#!/usr/bin/env python3
"""Canvas LMS API CLI for Hermes Agent.

A thin CLI wrapper around the Canvas REST API.
Authenticates using a personal access token from environment variables.

Usage:
  python canvas_api.py list_courses [--per-page N] [--enrollment-state STATE]
  python canvas_api.py list_assignments COURSE_ID [--per-page N] [--order-by FIELD]
  python canvas_api.py get_assignment COURSE_ID ASSIGNMENT_ID
  python canvas_api.py submit_assignment COURSE_ID ASSIGNMENT_ID --type TYPE [--body TEXT] [--url URL] [--file PATH]
  python canvas_api.py sync_assignments COURSE_ID [--per-page N]
  python canvas_api.py mark_done COURSE_ID ASSIGNMENT_ID [--notes TEXT]
  python canvas_api.py list_pending [COURSE_ID]
  python canvas_api.py list_done [COURSE_ID]
  python canvas_api.py fetch_google_doc URL [--markdown]
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser

import requests


def _load_hermes_env_value(key: str) -> str:
    """Load a value from ~/.hermes/.env if not already in os.environ."""
    val = os.environ.get(key, "")
    if val:
        return val
    # Fallback: read directly from the .env file (python-dotenv may not be
    # installed or load_dotenv may not have run for this process).
    env_path = os.path.join(
        os.environ.get("HERMES_HOME", os.path.join(os.path.expanduser("~"), ".hermes")),
        ".env",
    )
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    if k.strip() == key:
                        return v.strip().strip("\"'")
    except FileNotFoundError:
        pass
    return ""


CANVAS_API_TOKEN = _load_hermes_env_value("CANVAS_API_TOKEN")
CANVAS_BASE_URL = _load_hermes_env_value("CANVAS_BASE_URL").rstrip("/")

# Path to the PyMuPDF extraction script (sibling skill)
_PRODUCTIVITY_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_PYMUPDF_SCRIPT = os.path.join(
    _PRODUCTIVITY_DIR, "ocr-and-documents", "scripts", "extract_pymupdf.py"
)


class _LinkExtractor(HTMLParser):
    """Extract and categorise links from Canvas HTML assignment descriptions."""

    def __init__(self, canvas_base: str = ""):
        super().__init__()
        self.links: list = []
        self._canvas_base = canvas_base.lower()
        self._in_a = False
        self._current_href: str = ""
        self._current_text: list = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "a":
            href = attrs_dict.get("href", "")
            if href and not href.startswith(("javascript:", "#", "mailto:")):
                self._in_a = True
                self._current_href = href
                self._current_text = []
        elif tag == "img":
            src = attrs_dict.get("src", "")
            if src and not src.startswith("data:"):
                self.links.append({
                    "url": src,
                    "type": self._classify(src),
                    "text": attrs_dict.get("alt", ""),
                    "source": "image",
                })
        elif tag == "iframe":
            src = attrs_dict.get("src", "")
            if src:
                self.links.append({
                    "url": src,
                    "type": self._classify(src),
                    "text": "",
                    "source": "embed",
                })

    def handle_data(self, data):
        if self._in_a:
            self._current_text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._in_a:
            self.links.append({
                "url": self._current_href,
                "type": self._classify(self._current_href),
                "text": "".join(self._current_text).strip(),
                "source": "link",
            })
            self._in_a = False
            self._current_href = ""
            self._current_text = []

    def _classify(self, url: str) -> str:
        u = url.lower()
        if "docs.google.com/document" in u:
            return "google_doc"
        if "docs.google.com/spreadsheets" in u:
            return "google_sheet"
        if "docs.google.com/presentation" in u:
            return "google_slide"
        if "docs.google.com/forms" in u:
            return "google_form"
        if "drive.google.com" in u:
            return "google_drive"
        if "assignments.google.com" in u or "classroomassignments" in u:
            return "google_assignment"
        if "youtube.com" in u or "youtu.be" in u:
            return "youtube"
        if self._canvas_base and self._canvas_base in u:
            return "canvas_page"
        if "/files/" in u and "instructure.com" in u:
            return "canvas_file"
        return "external_url"


def _extract_links_from_html(html: str) -> list:
    """Parse HTML and return a deduplicated list of categorised link dicts."""
    if not html:
        return []
    parser = _LinkExtractor(canvas_base=CANVAS_BASE_URL)
    try:
        parser.feed(html)
    except Exception:
        return []
    seen: set = set()
    unique: list = []
    for item in parser.links:
        url = item.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(item)
    return unique


def _check_config():
    """Validate required environment variables are set."""
    missing = []
    if not CANVAS_API_TOKEN:
        missing.append("CANVAS_API_TOKEN")
    if not CANVAS_BASE_URL:
        missing.append("CANVAS_BASE_URL")
    if missing:
        print(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Set them in ~/.hermes/.env or export them in your shell.\n"
            "See the canvas skill SKILL.md for setup instructions.",
            file=sys.stderr,
        )
        sys.exit(1)


def _headers():
    return {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}


def _db_path():
    hermes_home = os.environ.get(
        "HERMES_HOME", os.path.join(os.path.expanduser("~"), ".hermes")
    )
    return os.path.join(hermes_home, "canvas_assignments.db")


def _get_db():
    """Return an open SQLite connection, initializing schema if needed."""
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            name TEXT,
            due_at TEXT,
            points_possible REAL,
            submission_types TEXT,
            html_url TEXT,
            last_synced TEXT NOT NULL,
            local_done INTEGER NOT NULL DEFAULT 0,
            done_at TEXT,
            done_notes TEXT,
            PRIMARY KEY (id, course_id)
        )
    """)
    conn.commit()
    return conn


def _is_google_assignment(a: dict) -> bool:
    """Check if an assignment uses Google Assignments (LTI)."""
    url = (a.get("external_tool_tag_attributes") or {}).get("url", "")
    return "external_tool" in a.get("submission_types", []) and "google" in url.lower()


def _google_assignments_url(a: dict) -> str:
    """Return the Google Assignments URL if applicable, else empty string."""
    if _is_google_assignment(a):
        return (a.get("external_tool_tag_attributes") or {}).get("url", "")
    return ""


def _paginated_get(url, params=None, max_items=200):
    """Fetch all pages up to max_items, following Canvas Link headers."""
    results = []
    while url and len(results) < max_items:
        resp = requests.get(url, headers=_headers(), params=params, timeout=30)
        resp.raise_for_status()
        results.extend(resp.json())
        params = None  # params are included in the Link URL for subsequent pages
        url = None
        link = resp.headers.get("Link", "")
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
    return results[:max_items]


# =========================================================================
# Commands
# =========================================================================


def list_courses(args):
    """List enrolled courses."""
    _check_config()
    url = f"{CANVAS_BASE_URL}/api/v1/courses"
    params = {"per_page": args.per_page}
    if args.enrollment_state:
        params["enrollment_state"] = args.enrollment_state
    try:
        courses = _paginated_get(url, params)
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} {e.response.text}", file=sys.stderr)
        sys.exit(1)
    output = [
        {
            "id": c["id"],
            "name": c.get("name", ""),
            "course_code": c.get("course_code", ""),
            "enrollment_term_id": c.get("enrollment_term_id"),
            "start_at": c.get("start_at"),
            "end_at": c.get("end_at"),
            "workflow_state": c.get("workflow_state", ""),
        }
        for c in courses
    ]
    print(json.dumps(output, indent=2))


def list_assignments(args):
    """List assignments for a course."""
    _check_config()
    url = f"{CANVAS_BASE_URL}/api/v1/courses/{args.course_id}/assignments"
    params = {"per_page": args.per_page}
    if args.order_by:
        params["order_by"] = args.order_by
    try:
        assignments = _paginated_get(url, params)
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} {e.response.text}", file=sys.stderr)
        sys.exit(1)
    output = [
        {
            "id": a["id"],
            "name": a.get("name", ""),
            "description": (a.get("description") or "")[:500],
            "due_at": a.get("due_at"),
            "points_possible": a.get("points_possible"),
            "submission_types": a.get("submission_types", []),
            "html_url": a.get("html_url", ""),
            "course_id": a.get("course_id"),
        }
        for a in assignments
    ]
    print(json.dumps(output, indent=2))


def get_assignment(args):
    """Fetch a single assignment with full details, attached files, and links."""
    _check_config()
    url = f"{CANVAS_BASE_URL}/api/v1/courses/{args.course_id}/assignments/{args.assignment_id}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(
            f"API error: {e.response.status_code} {e.response.text}",
            file=sys.stderr,
        )
        sys.exit(1)
    a = resp.json()

    raw_attachments = a.get("attachments") or []
    attachments = [
        {
            "display_name": att.get("display_name", ""),
            "url": att.get("url", ""),
            "content_type": att.get("content-type", ""),
            "size": att.get("size"),
        }
        for att in raw_attachments
    ]

    description_html = a.get("description") or ""

    # Build unified links list: Canvas attachments + links from description HTML
    links: list = []
    seen_urls: set = set()
    for att in attachments:
        u = att.get("url", "")
        if u and u not in seen_urls:
            seen_urls.add(u)
            links.append({
                "url": u,
                "type": "canvas_attachment",
                "text": att.get("display_name", ""),
                "source": "attachment",
                "content_type": att.get("content_type", ""),
                "size": att.get("size"),
            })
    for lnk in _extract_links_from_html(description_html):
        u = lnk.get("url", "")
        if u and u not in seen_urls:
            seen_urls.add(u)
            links.append(lnk)
    ext_tool_url = (a.get("external_tool_tag_attributes") or {}).get("url", "")
    if ext_tool_url and ext_tool_url not in seen_urls:
        seen_urls.add(ext_tool_url)
        link_type = "google_assignment" if _is_google_assignment(a) else "external_tool"
        links.append({
            "url": ext_tool_url,
            "type": link_type,
            "text": "External Tool",
            "source": "external_tool",
        })

    output = {
        "id": a["id"],
        "name": a.get("name", ""),
        "course_id": a.get("course_id"),
        "description": description_html,
        "due_at": a.get("due_at"),
        "points_possible": a.get("points_possible"),
        "submission_types": a.get("submission_types", []),
        "html_url": a.get("html_url", ""),
        "attachments": attachments,
        "links": links,
        "external_tool_url": ext_tool_url,
        "google_assignments": _is_google_assignment(a),
        "google_assignments_url": _google_assignments_url(a),
        "locked_for_user": a.get("locked_for_user", False),
        "lock_explanation": a.get("lock_explanation", ""),
    }
    print(json.dumps(output, indent=2))


def submit_assignment(args):
    """Submit an assignment (text, URL, or file upload)."""
    _check_config()

    # --- Validate argument combinations ---
    if args.type == "online_url" and not args.url:
        print(
            "Error: --url is required for submission type 'online_url'",
            file=sys.stderr,
        )
        sys.exit(1)
    if args.type == "online_upload" and not args.file:
        print(
            "Error: --file is required for submission type 'online_upload'",
            file=sys.stderr,
        )
        sys.exit(1)
    if args.type == "online_upload" and args.file and not os.path.isfile(args.file):
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # --- Fetch assignment to verify submission type is allowed ---
    assign_url = (
        f"{CANVAS_BASE_URL}/api/v1/courses/{args.course_id}"
        f"/assignments/{args.assignment_id}"
    )
    try:
        resp = requests.get(assign_url, headers=_headers(), timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(
            f"API error fetching assignment: {e.response.status_code} {e.response.text}",
            file=sys.stderr,
        )
        sys.exit(1)
    a = resp.json()
    allowed_types = a.get("submission_types", [])

    # --- Detect Google Assignments (LTI) ---
    if _is_google_assignment(a):
        google_url = _google_assignments_url(a)
        print(
            json.dumps(
                {
                    "error": "google_assignments",
                    "message": (
                        "This assignment uses Google Assignments (an LTI tool). "
                        "Submission must be done through the Google Assignments "
                        "interface, not through the Canvas API."
                    ),
                    "google_assignments_url": google_url,
                    "html_url": a.get("html_url", ""),
                },
                indent=2,
            )
        )
        sys.exit(1)

    # --- Check requested type is allowed ---
    if args.type not in allowed_types:
        print(
            json.dumps(
                {
                    "error": "submission_type_not_allowed",
                    "message": (
                        f"Submission type '{args.type}' is not allowed for this "
                        f"assignment."
                    ),
                    "allowed_types": allowed_types,
                },
                indent=2,
            )
        )
        sys.exit(1)

    # --- Assignments with no_submission / not_graded ---
    if "no_submission" in allowed_types or "not_graded" in allowed_types:
        print(
            json.dumps(
                {
                    "error": "no_submission_required",
                    "message": (
                        "This assignment has no submission button. "
                        "Use 'mark_done' to record it locally instead."
                    ),
                    "allowed_types": allowed_types,
                },
                indent=2,
            )
        )
        sys.exit(1)

    # --- Dry-run: preview what would be submitted ---
    if args.dry_run:
        preview = {
            "dry_run": True,
            "assignment_name": a.get("name", ""),
            "course_id": args.course_id,
            "assignment_id": args.assignment_id,
            "submission_type": args.type,
            "body": args.body if args.type == "online_text_entry" else None,
            "url": args.url if args.type == "online_url" else None,
            "file": args.file if args.type == "online_upload" else None,
            "file_name": (
                os.path.basename(args.file)
                if args.type == "online_upload" and args.file
                else None
            ),
            "file_size_bytes": (
                os.path.getsize(args.file)
                if args.type == "online_upload" and args.file
                else None
            ),
            "html_url": a.get("html_url", ""),
        }
        print(json.dumps(preview, indent=2))
        return

    # --- Build submission payload ---
    if args.type == "online_upload":
        # Step 1: Request upload slot
        file_name = os.path.basename(args.file)
        file_size = os.path.getsize(args.file)
        slot_url = (
            f"{CANVAS_BASE_URL}/api/v1/courses/{args.course_id}"
            f"/assignments/{args.assignment_id}/submissions/self/files"
        )
        try:
            slot_resp = requests.post(
                slot_url,
                headers=_headers(),
                json={"name": file_name, "size": file_size},
                timeout=30,
            )
            slot_resp.raise_for_status()
        except requests.HTTPError as e:
            print(
                f"API error requesting upload slot: "
                f"{e.response.status_code} {e.response.text}",
                file=sys.stderr,
            )
            sys.exit(1)
        slot = slot_resp.json()
        upload_url = slot["upload_url"]
        upload_params = slot.get("upload_params", {})

        # Step 2: Upload the file (multipart)
        try:
            with open(args.file, "rb") as fh:
                files_payload = {"file": (file_name, fh)}
                upload_resp = requests.post(
                    upload_url,
                    data=upload_params,
                    files=files_payload,
                    timeout=120,
                    allow_redirects=True,
                )
                upload_resp.raise_for_status()
        except requests.HTTPError as e:
            print(
                f"API error uploading file: "
                f"{e.response.status_code} {e.response.text}",
                file=sys.stderr,
            )
            sys.exit(1)
        upload_result = upload_resp.json()
        file_id = upload_result.get("id")
        if not file_id:
            print(
                "Error: file upload did not return a file ID", file=sys.stderr
            )
            sys.exit(1)

        # Step 3: Submit with the uploaded file_id
        submission_payload = {
            "submission_type": "online_upload",
            "file_ids": [file_id],
        }
    elif args.type == "online_text_entry":
        submission_payload = {
            "submission_type": "online_text_entry",
            "body": args.body,
        }
    elif args.type == "online_url":
        submission_payload = {
            "submission_type": "online_url",
            "url": args.url,
        }

    # --- Final submission POST ---
    sub_url = (
        f"{CANVAS_BASE_URL}/api/v1/courses/{args.course_id}"
        f"/assignments/{args.assignment_id}/submissions"
    )
    try:
        sub_resp = requests.post(
            sub_url,
            headers=_headers(),
            json={"submission": submission_payload},
            timeout=30,
        )
        sub_resp.raise_for_status()
    except requests.HTTPError as e:
        print(
            f"API error submitting: {e.response.status_code} {e.response.text}",
            file=sys.stderr,
        )
        sys.exit(1)
    s = sub_resp.json()
    print(
        json.dumps(
            {
                "success": True,
                "submission_id": s.get("id"),
                "submitted_at": s.get("submitted_at"),
                "workflow_state": s.get("workflow_state", ""),
                "submission_type": s.get("submission_type", ""),
            },
            indent=2,
        )
    )


def sync_assignments(args):
    """Fetch assignments from Canvas and upsert into local SQLite DB."""
    _check_config()
    url = f"{CANVAS_BASE_URL}/api/v1/courses/{args.course_id}/assignments"
    params = {"per_page": args.per_page}
    try:
        assignments = _paginated_get(url, params)
    except requests.HTTPError as e:
        print(
            f"API error: {e.response.status_code} {e.response.text}",
            file=sys.stderr,
        )
        sys.exit(1)
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_db()
    count = 0
    for a in assignments:
        conn.execute(
            """
            INSERT INTO assignments (id, course_id, name, due_at, points_possible,
                submission_types, html_url, last_synced)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id, course_id) DO UPDATE SET
                name=excluded.name,
                due_at=excluded.due_at,
                points_possible=excluded.points_possible,
                submission_types=excluded.submission_types,
                html_url=excluded.html_url,
                last_synced=excluded.last_synced
            """,
            (
                a["id"],
                a.get("course_id", args.course_id),
                a.get("name", ""),
                a.get("due_at"),
                a.get("points_possible"),
                json.dumps(a.get("submission_types", [])),
                a.get("html_url", ""),
                now,
            ),
        )
        count += 1
    conn.commit()
    conn.close()
    print(
        json.dumps(
            {"synced": count, "course_id": int(args.course_id), "synced_at": now},
            indent=2,
        )
    )


def mark_done(args):
    """Mark an assignment as done in the local DB."""
    conn = _get_db()
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "UPDATE assignments SET local_done=1, done_at=?, done_notes=? "
        "WHERE id=? AND course_id=?",
        (now, args.notes or "", int(args.assignment_id), int(args.course_id)),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        print(
            json.dumps(
                {
                    "error": "not_found",
                    "message": (
                        "Assignment not found in local DB. "
                        "Run sync_assignments first."
                    ),
                }
            )
        )
        sys.exit(1)
    print(
        json.dumps(
            {
                "success": True,
                "assignment_id": int(args.assignment_id),
                "done_at": now,
            },
            indent=2,
        )
    )


def list_pending(args):
    """List assignments not marked done from local DB."""
    conn = _get_db()
    query = "SELECT * FROM assignments WHERE local_done=0"
    params = []
    if args.course_id:
        query += " AND course_id=?"
        params.append(int(args.course_id))
    query += " ORDER BY due_at ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    output = [dict(r) for r in rows]
    for row in output:
        row["submission_types"] = json.loads(row["submission_types"] or "[]")
    print(json.dumps(output, indent=2))


def list_done(args):
    """List assignments marked done from local DB."""
    conn = _get_db()
    query = "SELECT * FROM assignments WHERE local_done=1"
    params = []
    if args.course_id:
        query += " AND course_id=?"
        params.append(int(args.course_id))
    query += " ORDER BY done_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    output = [dict(r) for r in rows]
    for row in output:
        row["submission_types"] = json.loads(row["submission_types"] or "[]")
    print(json.dumps(output, indent=2))


def fetch_content(args):
    """Download a Canvas-authenticated file and extract its text content.

    Uses the Canvas Bearer token to fetch the URL (required for Canvas file
    attachments).  Returns extracted text for PDFs via PyMuPDF, raw text for
    plain-text/HTML responses, and the saved temp file path for everything else.
    """
    _check_config()
    url = args.url

    try:
        resp = requests.get(url, headers=_headers(), timeout=60, stream=True)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(
            json.dumps({
                "error": "download_failed",
                "message": f"HTTP {e.response.status_code}: {e.response.text[:300]}",
                "url": url,
            }),
            file=sys.stderr,
        )
        sys.exit(1)

    content_type = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
    content_disposition = resp.headers.get("Content-Disposition", "")

    # Derive filename from headers or URL
    filename = ""
    if "filename=" in content_disposition:
        m = re.search(r'filename\*?=["\']?(?:UTF-8\'\')?([^"\';\n]+)', content_disposition, re.IGNORECASE)
        if m:
            filename = m.group(1).strip().strip("\"'")
    if not filename:
        filename = url.rstrip("/").split("/")[-1].split("?")[0] or "canvas_file"

    suffix = os.path.splitext(filename)[1].lower()
    if not suffix:
        # Infer extension from content-type
        _ct_map = {
            "application/pdf": ".pdf",
            "text/plain": ".txt",
            "text/html": ".html",
            "application/msword": ".doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        }
        suffix = _ct_map.get(content_type, "")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="canvas_") as tf:
        temp_path = tf.name
        for chunk in resp.iter_content(chunk_size=16384):
            tf.write(chunk)

    file_size = os.path.getsize(temp_path)

    result = {
        "url": url,
        "filename": filename,
        "content_type": content_type,
        "file_size": file_size,
        "temp_path": temp_path,
        "content": None,
        "extraction_method": None,
        "error": None,
    }

    is_pdf = "pdf" in content_type or suffix == ".pdf"
    is_text = content_type.startswith("text/") or content_type in (
        "application/json", "application/xml", "application/javascript"
    )
    is_html = "html" in content_type or suffix in (".html", ".htm")

    if is_pdf:
        if os.path.exists(_PYMUPDF_SCRIPT):
            flags = ["--markdown"] if args.markdown else []
            try:
                proc = subprocess.run(
                    [sys.executable, _PYMUPDF_SCRIPT, temp_path] + flags,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if proc.returncode == 0:
                    result["content"] = proc.stdout
                    result["extraction_method"] = "pymupdf_markdown" if args.markdown else "pymupdf_text"
                else:
                    result["error"] = f"PyMuPDF error: {proc.stderr[:300]}"
                    result["extraction_method"] = "failed"
            except subprocess.TimeoutExpired:
                result["error"] = "PyMuPDF extraction timed out after 120s"
                result["extraction_method"] = "failed"
        else:
            result["error"] = (
                f"PyMuPDF script not found at {_PYMUPDF_SCRIPT}. "
                "Install the ocr-and-documents skill or extract manually from temp_path."
            )
            result["extraction_method"] = "unavailable"
    elif is_html:
        with open(temp_path, encoding="utf-8", errors="replace") as f:
            raw = f.read(200_000)
        # Strip tags for a readable plain-text version
        text = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        result["content"] = text[:50_000]
        result["extraction_method"] = "html_stripped"
    elif is_text:
        with open(temp_path, encoding="utf-8", errors="replace") as f:
            result["content"] = f.read(50_000)
        result["extraction_method"] = "text"
    else:
        result["extraction_method"] = "saved_only"
        result["error"] = (
            f"No automatic text extraction for content type '{content_type}'. "
            "File saved to temp_path — use an appropriate tool to read it."
        )

    print(json.dumps(result, indent=2))


def _google_export_url(url: str):
    """Return (export_url, format) for a Google URL, or ("", "") if unrecognized."""
    # Google Docs: /document/d/{ID}/...
    m = re.search(r'docs\.google\.com/document/d/([a-zA-Z0-9_-]+)', url)
    if m:
        return (f"https://docs.google.com/document/d/{m.group(1)}/export?format=txt", "txt")

    # Google Sheets: /spreadsheets/d/{ID}/...
    m = re.search(r'docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)', url)
    if m:
        return (f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv", "csv")

    # Google Slides: /presentation/d/{ID}/...
    m = re.search(r'docs\.google\.com/presentation/d/([a-zA-Z0-9_-]+)', url)
    if m:
        return (f"https://docs.google.com/presentation/d/{m.group(1)}/export/pdf", "pdf")

    # Google Drive file: /file/d/{ID}/...
    m = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)', url)
    if not m:
        # drive.google.com/open?id=... or uc?id=...
        m = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if m:
        return (f"https://drive.google.com/uc?export=download&id={m.group(1)}", "binary")

    return ("", "")


def fetch_google_doc(args):
    """Download a Google Doc/Sheet/Slide via its public export URL (no OAuth needed).

    Works for documents shared with "anyone with the link". Returns extracted text
    content (plain text for Docs, CSV for Sheets, PDF-extracted text for Slides).
    If the document is restricted to school accounts, returns an auth_required error.
    """
    export_url, fmt = _google_export_url(args.url)
    if not export_url:
        print(
            json.dumps({
                "error": "unrecognized_url",
                "message": "Could not extract a Google document ID from the URL.",
                "url": args.url,
            })
        )
        sys.exit(1)

    req_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(
            export_url, headers=req_headers, timeout=60, allow_redirects=True
        )
    except requests.RequestException as e:
        print(
            json.dumps({
                "error": "network_error",
                "message": str(e),
                "url": args.url,
            })
        )
        sys.exit(1)

    content_type = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()

    # Detect Google login redirect — restricted docs redirect to an HTML login page
    is_html = "text/html" in content_type
    auth_required = resp.status_code in (401, 403)
    if not auth_required and is_html and fmt in ("txt", "csv", "pdf"):
        # For these formats we expect non-HTML; HTML means a login redirect
        snippet = resp.content[:512].decode("utf-8", errors="replace").lower()
        if "accounts.google.com" in snippet or "sign in" in snippet or "signin" in snippet:
            auth_required = True
    if auth_required:
        print(
            json.dumps({
                "error": "auth_required",
                "message": (
                    "This document is restricted to school Google accounts and cannot "
                    "be read automatically. Options: (1) Ask the teacher to share it "
                    'publicly with "anyone with the link"; '
                    "(2) Download it manually and share the file with the agent."
                ),
                "url": args.url,
                "export_url": export_url,
            })
        )
        sys.exit(1)

    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(
            json.dumps({
                "error": "http_error",
                "message": f"HTTP {e.response.status_code}",
                "url": args.url,
                "export_url": export_url,
            })
        )
        sys.exit(1)

    result = {
        "url": args.url,
        "export_url": export_url,
        "format": fmt,
        "content": None,
        "error": None,
    }

    if fmt == "txt":
        result["content"] = resp.content.decode("utf-8", errors="replace")[:80_000]

    elif fmt == "csv":
        result["content"] = resp.content.decode("utf-8", errors="replace")[:80_000]

    elif fmt == "pdf":
        # Slides exported as PDF — save then extract with PyMuPDF
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".pdf", prefix="gdoc_"
        ) as tf:
            temp_path = tf.name
            tf.write(resp.content)
        if os.path.exists(_PYMUPDF_SCRIPT):
            flags = ["--markdown"] if args.markdown else []
            try:
                proc = subprocess.run(
                    [sys.executable, _PYMUPDF_SCRIPT, temp_path] + flags,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if proc.returncode == 0:
                    result["content"] = proc.stdout
                else:
                    result["error"] = f"PyMuPDF error: {proc.stderr[:300]}"
            except subprocess.TimeoutExpired:
                result["error"] = "PyMuPDF extraction timed out"
            finally:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
        else:
            result["error"] = (
                f"PyMuPDF script not found at {_PYMUPDF_SCRIPT}. "
                "Install the ocr-and-documents skill."
            )

    elif fmt == "binary":
        # Generic Drive file — save and extract if PDF, otherwise report temp path
        suffix = ".pdf" if "pdf" in content_type else ""
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix, prefix="gdrive_"
        ) as tf:
            temp_path = tf.name
            tf.write(resp.content)
        result["content_type"] = content_type
        result["temp_path"] = temp_path
        if "pdf" in content_type and os.path.exists(_PYMUPDF_SCRIPT):
            flags = ["--markdown"] if args.markdown else []
            try:
                proc = subprocess.run(
                    [sys.executable, _PYMUPDF_SCRIPT, temp_path] + flags,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if proc.returncode == 0:
                    result["content"] = proc.stdout
                    try:
                        os.unlink(temp_path)
                        result.pop("temp_path", None)
                    except OSError:
                        pass
                else:
                    result["error"] = f"PyMuPDF error: {proc.stderr[:300]}"
            except subprocess.TimeoutExpired:
                result["error"] = "PyMuPDF extraction timed out; file saved to temp_path"
        else:
            result["error"] = (
                f"Drive file saved to {temp_path} (content-type: {content_type}). "
                "Use an appropriate tool to read it."
            )

    print(json.dumps(result, indent=2))


# =========================================================================
# CLI parser
# =========================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Canvas LMS API CLI for Hermes Agent"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- list_courses ---
    p = sub.add_parser("list_courses", help="List enrolled courses")
    p.add_argument("--per-page", type=int, default=50, help="Results per page (default 50)")
    p.add_argument(
        "--enrollment-state",
        default="",
        help="Filter by enrollment state (active, invited_or_pending, completed)",
    )
    p.set_defaults(func=list_courses)

    # --- list_assignments ---
    p = sub.add_parser("list_assignments", help="List assignments for a course")
    p.add_argument("course_id", help="Canvas course ID")
    p.add_argument("--per-page", type=int, default=50, help="Results per page (default 50)")
    p.add_argument(
        "--order-by",
        default="",
        help="Order by field (due_at, name, position)",
    )
    p.set_defaults(func=list_assignments)

    # --- get_assignment ---
    p = sub.add_parser("get_assignment", help="Fetch full details for a single assignment")
    p.add_argument("course_id", help="Canvas course ID")
    p.add_argument("assignment_id", help="Canvas assignment ID")
    p.set_defaults(func=get_assignment)

    # --- submit_assignment ---
    p = sub.add_parser("submit_assignment", help="Submit an assignment")
    p.add_argument("course_id", help="Canvas course ID")
    p.add_argument("assignment_id", help="Canvas assignment ID")
    p.add_argument(
        "--type",
        required=True,
        choices=["online_text_entry", "online_url", "online_upload"],
        help="Submission type",
    )
    p.add_argument(
        "--body",
        default="Assignment completed",
        help="Text body for online_text_entry submissions (default: 'Assignment completed')",
    )
    p.add_argument(
        "--url",
        default=None,
        help="URL for online_url submissions",
    )
    p.add_argument(
        "--file",
        default=None,
        help="Local file path for online_upload submissions",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be submitted without writing to Canvas",
    )
    p.set_defaults(func=submit_assignment)

    # --- sync_assignments ---
    p = sub.add_parser("sync_assignments", help="Sync assignments to local DB")
    p.add_argument("course_id", help="Canvas course ID")
    p.add_argument("--per-page", type=int, default=50, help="Results per page (default 50)")
    p.set_defaults(func=sync_assignments)

    # --- mark_done ---
    p = sub.add_parser("mark_done", help="Mark an assignment as done locally")
    p.add_argument("course_id", help="Canvas course ID")
    p.add_argument("assignment_id", help="Canvas assignment ID")
    p.add_argument("--notes", default="", help="Optional completion notes")
    p.set_defaults(func=mark_done)

    # --- list_pending ---
    p = sub.add_parser("list_pending", help="List pending (not done) assignments from local DB")
    p.add_argument("course_id", nargs="?", default=None, help="Optional course ID filter")
    p.set_defaults(func=list_pending)

    # --- list_done ---
    p = sub.add_parser("list_done", help="List completed assignments from local DB")
    p.add_argument("course_id", nargs="?", default=None, help="Optional course ID filter")
    p.set_defaults(func=list_done)

    # --- fetch_content ---
    p = sub.add_parser(
        "fetch_content",
        help="Download a Canvas file attachment and extract its text content",
    )
    p.add_argument("url", help="Canvas file attachment URL (requires Canvas Bearer auth)")
    p.add_argument(
        "--markdown",
        action="store_true",
        help="Use PyMuPDF markdown extraction for PDFs instead of plain text",
    )
    p.set_defaults(func=fetch_content)

    # --- fetch_google_doc ---
    p = sub.add_parser(
        "fetch_google_doc",
        help=(
            "Download a Google Doc/Sheet/Slide via its public export URL "
            "(no OAuth needed — works for publicly shared docs)"
        ),
    )
    p.add_argument(
        "url",
        help="Google Docs/Sheets/Slides/Drive URL from the assignment links array",
    )
    p.add_argument(
        "--markdown",
        action="store_true",
        help="Use PyMuPDF markdown extraction for Slides (exported as PDF)",
    )
    p.set_defaults(func=fetch_google_doc)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

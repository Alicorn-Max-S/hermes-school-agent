---
name: canvas
description: Canvas LMS integration — list courses, fetch assignment details, submit assignments, and track completion locally.
version: 2.0.0
author: community
license: MIT
prerequisites:
  env_vars: [CANVAS_API_TOKEN, CANVAS_BASE_URL]
metadata:
  hermes:
    tags: [Canvas, LMS, Education, Courses, Assignments, Submissions]
---

# Canvas LMS — Course & Assignment Access

Read and write access to Canvas LMS for listing courses, fetching assignment details, and submitting assignments. Includes local SQLite tracking for assignments without a submission button.

## Scripts

- `scripts/canvas_api.py` — Python CLI for Canvas API calls

## Setup

1. Log in to your Canvas instance in a browser
2. Go to **Account → Settings** (click your profile icon, then Settings)
3. Scroll to **Approved Integrations** and click **+ New Access Token**
4. Name the token (e.g., "Hermes Agent"), set an optional expiry, and click **Generate Token**
5. Copy the token and add to `~/.hermes/.env`:

```
CANVAS_API_TOKEN=your_token_here
CANVAS_BASE_URL=https://yourschool.instructure.com
```

The base URL is whatever appears in your browser when you're logged into Canvas (no trailing slash).

## Usage

```bash
CANVAS="python ~/.hermes/skills/productivity/canvas/scripts/canvas_api.py"

# List all active courses
$CANVAS list_courses --enrollment-state active

# List all courses (any state)
$CANVAS list_courses

# List assignments for a specific course
$CANVAS list_assignments 12345

# List assignments ordered by due date
$CANVAS list_assignments 12345 --order-by due_at

# Get full details for a single assignment (with attachments, links, and external tools)
$CANVAS get_assignment 12345 67890

# Download a Canvas file attachment and extract its text (PDF → plain text)
$CANVAS fetch_content "https://yourschool.instructure.com/files/12345/download?..."

# Download and convert PDF to markdown (better formatting for tables/headings)
$CANVAS fetch_content "https://yourschool.instructure.com/files/12345/download?..." --markdown

# Preview a submission (ALWAYS do this first before submitting)
$CANVAS submit_assignment 12345 67890 --type online_text_entry --body "My answer" --dry-run

# Submit an assignment as a text entry (after user confirms dry-run)
$CANVAS submit_assignment 12345 67890 --type online_text_entry --body "My answer"

# Submit an assignment with default text body
$CANVAS submit_assignment 12345 67890 --type online_text_entry

# Submit an assignment as a URL
$CANVAS submit_assignment 12345 67890 --type online_url --url "https://myproject.example.com"

# Submit an assignment as a file upload
$CANVAS submit_assignment 12345 67890 --type online_upload --file /path/to/homework.pdf

# Sync assignments to local tracking database
$CANVAS sync_assignments 12345

# Mark an assignment as done locally (for assignments without a submit button)
$CANVAS mark_done 12345 67890 --notes "Completed in class"

# List pending (not done) assignments
$CANVAS list_pending 12345

# List completed assignments
$CANVAS list_done 12345
```

## Output Format

**list_courses** returns:
```json
[{"id": 12345, "name": "Intro to CS", "course_code": "CS101", "workflow_state": "available", "start_at": "...", "end_at": "..."}]
```

**list_assignments** returns:
```json
[{"id": 67890, "name": "Homework 1", "due_at": "2025-02-15T23:59:00Z", "points_possible": 100, "submission_types": ["online_upload"], "html_url": "...", "description": "...", "course_id": 12345}]
```

Note: Assignment descriptions are truncated to 500 characters. The `html_url` field links to the full assignment page in Canvas.

**get_assignment** returns:
```json
{
  "id": 67890,
  "name": "Final Project",
  "course_id": 12345,
  "description": "Full HTML description text (not truncated)...",
  "due_at": "2025-05-01T23:59:00Z",
  "points_possible": 100,
  "submission_types": ["online_upload"],
  "html_url": "https://yourschool.instructure.com/courses/12345/assignments/67890",
  "attachments": [
    {"display_name": "rubric.pdf", "url": "https://...", "content_type": "application/pdf", "size": 204800}
  ],
  "links": [
    {"url": "https://.../files/123/download?...", "type": "canvas_attachment", "text": "rubric.pdf", "source": "attachment", "content_type": "application/pdf", "size": 204800},
    {"url": "https://docs.google.com/document/d/ABC/edit", "type": "google_doc", "text": "Project Brief", "source": "link"},
    {"url": "https://drive.google.com/file/d/XYZ/view", "type": "google_drive", "text": "Dataset", "source": "link"},
    {"url": "https://example.com/resource", "type": "external_url", "text": "Reference", "source": "link"}
  ],
  "external_tool_url": "",
  "google_assignments": false,
  "google_assignments_url": "",
  "locked_for_user": false,
  "lock_explanation": ""
}
```

**Link types in the `links` array:**
| type | Description |
|------|-------------|
| `canvas_attachment` | Direct Canvas file (PDF, doc, image) — use `fetch_content` to read |
| `google_doc` | Google Docs document |
| `google_sheet` | Google Sheets spreadsheet |
| `google_slide` | Google Slides presentation |
| `google_form` | Google Form |
| `google_drive` | Generic Google Drive file |
| `google_assignment` | Google Assignments (LTI) — open in browser |
| `external_tool` | Other LTI external tool |
| `youtube` | YouTube video |
| `canvas_page` | Another page within Canvas |
| `external_url` | Public web page |

**fetch_content** returns:
```json
{
  "url": "https://yourschool.instructure.com/files/12345/download?...",
  "filename": "rubric.pdf",
  "content_type": "application/pdf",
  "file_size": 204800,
  "temp_path": "/tmp/canvas_abc123.pdf",
  "content": "--- Page 1/3 ---\n\nProject Rubric\n...",
  "extraction_method": "pymupdf_text",
  "error": null
}
```
- `extraction_method` values: `pymupdf_text`, `pymupdf_markdown`, `html_stripped`, `text`, `saved_only`, `failed`, `unavailable`
- `content` is `null` when extraction fails; use `temp_path` to access the raw file
- For binary files (images, zip, etc.) the file is saved to `temp_path` with `extraction_method: "saved_only"`

**submit_assignment --dry-run** returns:
```json
{
  "dry_run": true,
  "assignment_name": "Homework 3",
  "course_id": "12345",
  "assignment_id": "67890",
  "submission_type": "online_text_entry",
  "body": "My completed answer...",
  "url": null,
  "file": null,
  "file_size_bytes": null,
  "html_url": "https://yourschool.instructure.com/courses/12345/assignments/67890"
}
```

**submit_assignment** (actual submission) returns:
```json
{"success": true, "submission_id": 111222, "submitted_at": "2025-04-30T18:00:00Z", "workflow_state": "submitted", "submission_type": "online_text_entry"}
```

**sync_assignments** returns:
```json
{"synced": 15, "course_id": 12345, "synced_at": "2025-04-30T18:00:00Z"}
```

**mark_done** returns:
```json
{"success": true, "assignment_id": 67890, "done_at": "2025-04-30T18:00:00Z"}
```

**list_pending** / **list_done** returns:
```json
[{"id": 67890, "course_id": 12345, "name": "Homework 1", "due_at": "...", "points_possible": 100, "submission_types": ["online_upload"], "html_url": "...", "last_synced": "...", "local_done": 0, "done_at": null, "done_notes": null}]
```

## API Reference (curl)

```bash
# List courses
curl -s -H "Authorization: Bearer $CANVAS_API_TOKEN" \
  "$CANVAS_BASE_URL/api/v1/courses?enrollment_state=active&per_page=10"

# List assignments for a course
curl -s -H "Authorization: Bearer $CANVAS_API_TOKEN" \
  "$CANVAS_BASE_URL/api/v1/courses/COURSE_ID/assignments?per_page=10&order_by=due_at"

# Get a single assignment
curl -s -H "Authorization: Bearer $CANVAS_API_TOKEN" \
  "$CANVAS_BASE_URL/api/v1/courses/COURSE_ID/assignments/ASSIGNMENT_ID"

# Submit an assignment (text entry)
curl -s -X POST -H "Authorization: Bearer $CANVAS_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"submission": {"submission_type": "online_text_entry", "body": "My answer"}}' \
  "$CANVAS_BASE_URL/api/v1/courses/COURSE_ID/assignments/ASSIGNMENT_ID/submissions"

# Submit an assignment (URL)
curl -s -X POST -H "Authorization: Bearer $CANVAS_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"submission": {"submission_type": "online_url", "url": "https://example.com"}}' \
  "$CANVAS_BASE_URL/api/v1/courses/COURSE_ID/assignments/ASSIGNMENT_ID/submissions"
```

Canvas uses `Link` headers for pagination. The Python script handles pagination automatically.

## Rules

- `list_courses`, `list_assignments`, and `get_assignment` are **read-only** — they only fetch data
- `submit_assignment` **MUST** always be called with `--dry-run` first; show the dry-run output to the user and wait for explicit confirmation before running without `--dry-run`
- The dry-run output shows exactly: assignment name, submission type, body text / URL / file path and size — the user must approve this exact content before the real submission
- `mark_done` only writes to the local DB (`~/.hermes/canvas_assignments.db`) — it never touches Canvas
- Google Assignments (LTI) cannot be submitted via the Canvas API; the command returns the Google URL for manual completion in a browser
- On first use, verify auth by running `$CANVAS list_courses` — if it fails with 401, guide the user through setup
- Canvas rate-limits to ~700 requests per 10 minutes; check `X-Rate-Limit-Remaining` header if hitting limits
- Run `sync_assignments` before `list_pending` / `list_done` to ensure the local DB is up to date

### Always show assignment links

- After calling `get_assignment`, **always** display the `links` array to the user (even if only one link exists)
- Format links clearly — show the link `text`, `type`, and clickable `url`
- If `links` is empty and `attachments` is also empty, note this explicitly so the user knows the assignment has no attached resources

### Reading assignment file content

When the user wants to view the actual content of an assignment file or linked document, choose the right method based on link `type`:

| Link type | How to read |
|-----------|-------------|
| `canvas_attachment` | `$CANVAS fetch_content URL [--markdown]` — downloads with Canvas auth and extracts text |
| `google_doc` / `google_sheet` / `google_slide` | Use the **browser tool** to navigate to the URL (the user must be logged in with their school Google account). If the google-workspace skill OAuth is configured, use `google_api.py docs_read DOC_ID` instead |
| `google_drive` | Use the **browser tool** to navigate to the URL. If google-workspace OAuth is set up, use Drive API download |
| `google_assignment` | Use the **browser tool** to open the `google_assignments_url` — the user must complete or view it through the Google Assignments interface |
| `external_url` | Use `web_extract` (Firecrawl) to fetch and convert to markdown. For auth-locked pages, fall back to the **browser tool** |
| `youtube` | Provide the URL for the user to watch; do not attempt to extract |
| `canvas_page` | Use `web_extract` with the Canvas page URL, or navigate with the browser tool |

**Priority order for reading content:**
1. `fetch_content` for Canvas attachments (always works with a valid Canvas token — no extra login required)
2. Google Workspace API (`google_api.py`) for Google Docs/Sheets/Drive if OAuth has been configured (see below)
3. `web_extract` (Firecrawl) for public external URLs
4. Browser tool as a last resort for auth-locked pages

**Setting up Google Workspace OAuth (one-time, works with school MFA):**

Even if the VPS cannot show a browser or MFA prompt, Google OAuth can be set up once using the `google-workspace` skill's manual code-copy flow. The MFA confirmation happens on whatever device the user opens the auth URL on (e.g. their main laptop) — the VPS only needs the resulting auth code pasted in:

```bash
GWS="python ~/.hermes/skills/productivity/google-workspace/scripts/setup.py"
$GWS --install-deps      # install Google API libraries
# Ask the user to place their client_secret.json from Google Cloud Console at a local path
$GWS --client-secret /path/to/client_secret.json
$GWS --auth-url          # prints a URL — user opens it in their main browser, approves MFA
# User copies the `code=...` value from the redirect URL and pastes it back
$GWS --auth-code PASTE_CODE_HERE
$GWS --check             # exit 0 = success; token saved to ~/.hermes/google_token.json
```

After this one-time setup, the refresh token stored on the VPS allows reading Google Docs, Sheets, and Drive files without any further MFA prompts.

**When content cannot be read:**
- If `fetch_content` fails with a 403 error, the file may require elevated Canvas permissions — provide the `html_url` so the user can open it manually
- If Google Workspace OAuth is not set up, provide the Google Doc/Drive URL so the user can open it in their browser
- Evomi and Tavily (scraper APIs) cannot bypass school Google/Canvas authentication — they are only useful for fully public web pages that Firecrawl cannot reach due to JS rendering or rate-limiting
- Always provide the raw URL even when automatic extraction fails, so the user can open it themselves

## Troubleshooting

| Problem | Fix |
|---------|-----|
| 401 Unauthorized | Token invalid or expired — regenerate in Canvas Settings |
| 403 Forbidden | Token lacks permission for this course |
| Empty course list | Try `--enrollment-state active` or omit the flag to see all states |
| Wrong institution | Verify `CANVAS_BASE_URL` matches the URL in your browser |
| Timeout errors | Check network connectivity to your Canvas instance |
| 404 on `get_assignment` | Verify both course ID and assignment ID are correct; use `list_assignments` to confirm |
| `submission_type_not_allowed` error | The assignment doesn't accept that type; check `allowed_types` in the error |
| `google_assignments` error | Assignment uses Google Assignments LTI — open the provided URL in a browser |
| `no_submission_required` error | Assignment has no submit button; use `mark_done` to track locally |
| `not_found` on `mark_done` | Run `sync_assignments` first to populate the local DB |
| Assignment locked | Check `locked_for_user` / `lock_explanation` from `get_assignment` |
| `fetch_content` returns 403 | File may require a specific Canvas role or be in a locked module — open `html_url` manually |
| `fetch_content` extraction_method is `unavailable` | The `ocr-and-documents` skill is not installed — install it or read the `temp_path` file manually |
| Google Doc link shows login page | Use the browser tool; the user needs to be logged in with their school Google account |
| `links` array is empty but there should be files | The instructor may have embedded files as module items rather than assignment attachments — check `html_url` directly |

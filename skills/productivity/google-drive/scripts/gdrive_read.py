#!/usr/bin/env python3
"""
Google Drive URL Parser and URL Builder

Parses Google Drive/Docs/Sheets/Slides URLs to extract file IDs and
construct export, edit, and view URLs.

Usage:
    python3 gdrive_read.py parse "https://docs.google.com/document/d/ABC123/edit"
    python3 gdrive_read.py parse "https://drive.google.com/file/d/XYZ789/view"
"""

import json
import re
import sys
from urllib.parse import urlparse, parse_qs


# URL patterns for Google Drive file types
_PATTERNS = [
    # Google Docs: /document/d/FILE_ID/...
    (r"docs\.google\.com/document/d/([a-zA-Z0-9_-]+)", "doc"),
    # Google Sheets: /spreadsheets/d/FILE_ID/...
    (r"docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)", "sheet"),
    # Google Slides: /presentation/d/FILE_ID/...
    (r"docs\.google\.com/presentation/d/([a-zA-Z0-9_-]+)", "slides"),
    # Google Forms: /forms/d/FILE_ID/...
    (r"docs\.google\.com/forms/d/([a-zA-Z0-9_-]+)", "form"),
    # Drive file viewer: /file/d/FILE_ID/...
    (r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)", "file"),
    # Drive open link: /open?id=FILE_ID
    (r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)", "file"),
]

# Export URL templates — for direct curl fetch of publicly shared files.
# NOTE: These do NOT work in the browser (downloads get blocked with ERR_ABORTED).
# For authenticated access, use the edit URL + File → Download instead.
_EXPORT_URLS = {
    "doc": "https://docs.google.com/document/d/{file_id}/export?format=txt",
    "sheet": "https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv",
    "slides": "https://docs.google.com/presentation/d/{file_id}/export?format=txt",
}

# Edit URL templates — for browser-based access (File → Download workflow).
# This is the PREFERRED method for authenticated access because:
# - Export URLs get blocked by the browser (ERR_ABORTED)
# - Google Docs content is Canvas-rendered (invisible to DOM/snapshots)
# - File → Download saves a readable file to ~/Downloads/
_EDIT_URLS = {
    "doc": "https://docs.google.com/document/d/{file_id}/edit",
    "sheet": "https://docs.google.com/spreadsheets/d/{file_id}/edit",
    "slides": "https://docs.google.com/presentation/d/{file_id}/edit",
    "form": "https://docs.google.com/forms/d/{file_id}/edit",
}

# View URL templates — for read-only browser viewing
_VIEW_URLS = {
    "doc": "https://docs.google.com/document/d/{file_id}/preview",
    "sheet": "https://docs.google.com/spreadsheets/d/{file_id}/preview",
    "slides": "https://docs.google.com/presentation/d/{file_id}/preview",
    "file": "https://drive.google.com/file/d/{file_id}/preview",
    "form": "https://docs.google.com/forms/d/{file_id}/viewform",
}


def parse_drive_url(url: str) -> dict:
    """Parse a Google Drive URL and return file metadata.

    Returns:
        Dict with: file_id, file_type, edit_url (preferred for browser),
        export_url (for curl), view_url, original_url.
        On failure: error message.
    """
    url = url.strip()

    # Try query-string ?id= pattern first (e.g., drive.google.com/open?id=...)
    parsed = urlparse(url)
    query_id = parse_qs(parsed.query).get("id", [None])[0]
    if query_id and "drive.google.com" in parsed.netloc:
        file_id = query_id
        file_type = "file"
    else:
        # Try regex patterns
        file_id = None
        file_type = None
        for pattern, ftype in _PATTERNS:
            match = re.search(pattern, url)
            if match:
                file_id = match.group(1)
                file_type = ftype
                break

    if not file_id:
        return {"error": f"Could not parse Google Drive URL: {url}"}

    result = {
        "file_id": file_id,
        "file_type": file_type,
        "original_url": url,
    }

    # Edit URL — preferred for browser access (File → Download workflow)
    edit_url = _EDIT_URLS.get(file_type, "").format(file_id=file_id)
    if edit_url:
        result["edit_url"] = edit_url

    # Export URL — for direct curl fetch of public files only
    export_url = _EXPORT_URLS.get(file_type, "").format(file_id=file_id)
    if export_url:
        result["export_url"] = export_url

    # View URL — read-only browser viewing
    view_url = _VIEW_URLS.get(file_type, "").format(file_id=file_id)
    if view_url:
        result["view_url"] = view_url

    return result


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "parse":
        print("Usage: python3 gdrive_read.py parse <google_drive_url>")
        sys.exit(1)

    url = sys.argv[2]
    result = parse_drive_url(url)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()

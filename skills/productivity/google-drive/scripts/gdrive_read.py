#!/usr/bin/env python3
"""
Google Drive URL Parser and Export URL Builder

Parses Google Drive/Docs/Sheets/Slides URLs to extract file IDs and
construct export URLs for clean text/CSV content extraction.

Usage:
    python gdrive_read.py parse "https://docs.google.com/document/d/ABC123/edit"
    python gdrive_read.py parse "https://drive.google.com/file/d/XYZ789/view"
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

# Export URL templates for text/CSV extraction
_EXPORT_URLS = {
    "doc": "https://docs.google.com/document/d/{file_id}/export?format=txt",
    "sheet": "https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv",
    "slides": "https://docs.google.com/presentation/d/{file_id}/export?format=txt",
}

# View URL templates for browser viewing
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
        Dict with: file_id, file_type, export_url (if available),
        view_url, original_url.  On failure: error message.
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
        "view_url": _VIEW_URLS.get(file_type, "").format(file_id=file_id),
    }

    export_url = _EXPORT_URLS.get(file_type, "").format(file_id=file_id)
    if export_url:
        result["export_url"] = export_url

    return result


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "parse":
        print("Usage: python gdrive_read.py parse <google_drive_url>")
        sys.exit(1)

    url = sys.argv[2]
    result = parse_drive_url(url)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()

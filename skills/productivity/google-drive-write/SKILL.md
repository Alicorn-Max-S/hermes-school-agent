---
name: google-drive-write
description: "Write and edit Google Drive content — update Google Sheets cells, append rows, create documents, and modify Drive files. Uses Google OAuth2. Trigger on mentions of editing spreadsheets, updating shared docs, writing to Google Sheets, or saving to Drive."
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  apollo:
    tags: [Google, Drive, Sheets, Docs, Write, Edit]
    homepage: https://github.com/NousResearch/apollo-agent
    related_skills: [google-auth, google-drive]
    school: true
    school_category: "Google Workspace"
---

# Google Drive Write

Write and edit Google Drive content. For **reading** Drive files (Docs, Sheets, PDFs), use the `google-drive` skill instead.

## Prerequisites

Requires Google OAuth2 setup via the `google-auth` skill:

```bash
GSETUP="python ~/.apollo/skills/productivity/google-auth/scripts/setup.py"
$GSETUP --check
```

If not authenticated, load `google-auth`: `skill_view("google-auth")`

## Usage

```bash
GAPI="python ~/.apollo/skills/productivity/google-auth/scripts/google_api.py"
```

### Google Sheets — Write Data

```bash
# Overwrite a range with new values
$GAPI sheets update SHEET_ID "Sheet1!A1:B2" --values '[["Name","Score"],["Alice","95"]]'

# Append rows to the end of existing data
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[["new","row","data"]]'

# Append multiple rows
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[["row1","data","here"],["row2","more","data"]]'
```

### Reading Before Writing

When you need to read content before editing (e.g., to see current data in a sheet before updating), use the `google-drive` skill's reading methods:

```bash
# Read sheet data (via google-drive skill's API mode)
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"

# Read a Google Doc
$GAPI docs get DOC_ID

# Search for files
$GAPI drive search "quarterly report" --max 10
```

For browser-based reading (school/enterprise SSO accounts), load the full `google-drive` skill: `skill_view("google-drive")`

## Output Format

**sheets update** returns:
```json
{"updatedCells": 4, "updatedRange": "Sheet1!A1:B2"}
```

**sheets append** returns:
```json
{"updatedCells": 3}
```

## Rules

1. **Always confirm with the user before writing data.** Show what will be written and where.
2. **Read before writing** when modifying existing data — use `$GAPI sheets get` to see current values first.
3. **Check auth before first use** — run `$GSETUP --check`.
4. **Values must be valid JSON** — arrays of arrays for the `--values` flag.
5. **Respect rate limits** — avoid rapid-fire sequential API calls.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NOT_AUTHENTICATED` | Load `google-auth` skill and follow setup |
| `HttpError 403: Insufficient Permission` | Missing Sheets scope — revoke and re-auth via `google-auth` |
| `HttpError 404` | Invalid Sheet ID — check the URL for the correct ID |
| Values not updating | Ensure `--values` is valid JSON: `'[["a","b"],["c","d"]]'` |

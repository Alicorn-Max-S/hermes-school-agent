---
name: file-analysis
description: "Analyze any file by auto-detecting its type and routing to the right analysis skill. Supports PDFs, images, spreadsheets, code, audio, video, text, and more. Trigger when the user uploads a file, shares a file path, or asks to analyze, read, parse, or extract content from any file."
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  apollo:
    tags: [Files, Analysis, PDF, Images, Documents, CSV, Code, Vision, OCR, Audio, Video]
    related_skills: [image-analysis, document-analysis, code-analysis, text-analysis, audio-analysis, video-analysis, ocr-and-documents]
    school: true
    school_category: "File Analysis"
---

# File Analysis Router

Analyze any file by auto-detecting its type and routing to the specialized analysis skill.

**IMPORTANT**: All tool references (`read_file`, `vision_analyze`, `clarify`, `terminal`, `memory`, `skill_view`) are **agent tools** — invoke them as tool calls, NOT as Python imports.

## Step 1: Detect File Type

```bash
python3 ~/.apollo/skills/productivity/file-analysis/scripts/detect_filetype.py "FILE_PATH_OR_URL"
```

Returns JSON with `category`, `extension`, `mime_type`, `size_bytes`, `size_human`.

## Step 2: Route to Category Skill

Based on the `category` from Step 1, load and follow the appropriate skill:

| Category | Skill to Load | How to Load | Description |
|----------|--------------|-------------|-------------|
| `image` | `image-analysis` | `skill_view("image-analysis")` | Vision AI analysis with model fallback |
| `document` | `document-analysis` | `skill_view("document-analysis")` | PDF, Word, Excel, PowerPoint extraction |
| `code` | `code-analysis` | `skill_view("code-analysis")` | Source code reading and analysis |
| `text` | `text-analysis` | `skill_view("text-analysis")` | Text, CSV, JSON, XML, YAML, config files |
| `audio` | `audio-analysis` | `skill_view("audio-analysis")` | Audio transcription and metadata |
| `video` | `video-analysis` | `skill_view("video-analysis")` | Video keyframe extraction and analysis |
| `data` | `text-analysis` | `skill_view("text-analysis")` | Data files (Parquet, SQLite) — treat as structured text |
| `archive` | (inline) | — | List archive contents via `terminal` |
| `unknown` | (inline) | — | Try `read_file`, report metadata |

**To load a skill**, always use an explicit `skill_view` call:
```
skill_view("SKILL_NAME")
```
Then follow that skill's instructions with the user's file and request.

## Step 3: Handle Archives (inline)

For archives (.zip, .tar, .gz, .7z, .rar):
```bash
# List contents
unzip -l file.zip        # ZIP
tar -tf file.tar.gz      # TAR/GZ
7z l file.7z             # 7Z (if available)
```

If user wants to analyze specific files inside:
1. Extract to a temp directory
2. Re-run file detection on extracted files
3. Route each to the appropriate skill

## Step 4: Handle Unknown Files (inline)

For unrecognized file types:
1. Try `read_file` — if it returns text content, treat as text-analysis
2. If binary detected, get metadata via:
   ```bash
   file "FILE_PATH"
   ```
3. Report file type, size, and any metadata found
4. As a last resort, offer to try `vision_analyze` (omni model may be able to process it)

## Notes

- This skill is a router — it detects the file type and delegates to the specialized skill
- Each specialized skill has its own fallback chain including vision AI as universal last resort
- For Google Drive files, use the `google-drive` skill first to download, then route through here

---
name: canvas-lms
description: "Canvas LMS integration for students and teachers — list courses, view syllabi, fetch assignment details and rubrics, submit homework, check grades, and track completion. Trigger on mentions of Canvas, LMS, coursework, assignments, grading, or submissions."
version: 2.0.0
author: community
license: MIT
prerequisites:
  env_vars: [CANVAS_API_TOKEN, CANVAS_BASE_URL]
metadata:
  apollo:
    tags: [Canvas, LMS, Education, Courses, Assignments, Submissions]
    related_skills: [file-analysis, document-analysis, image-analysis, ocr-and-documents, google-drive]
    school: true
    school_category: "Homework & Assignments"
---

# Canvas LMS — Course & Assignment Access

Read and write access to Canvas LMS for listing courses, fetching assignment details, and submitting assignments. Includes local SQLite tracking for assignments without a submission button.

## Scripts

- `scripts/canvas_api.py` — Python CLI for Canvas API calls

## Setup

1. Log in to your Canvas instance in a browser
2. Go to **Account → Settings** (click your profile icon, then Settings)
3. Scroll to **Approved Integrations** and click **+ New Access Token**
4. Name the token (e.g., "Apollo Agent"), set an optional expiry, and click **Generate Token**
5. Copy the token and add to `~/.apollo/.env`:

```
CANVAS_API_TOKEN=your_token_here
CANVAS_BASE_URL=https://yourschool.instructure.com
```

The base URL is whatever appears in your browser when you're logged into Canvas (no trailing slash).

## Step 0: Verify Setup

Before proceeding, verify that CANVAS_API_TOKEN and CANVAS_BASE_URL environment variables are set. Use terminal to run: `echo $CANVAS_API_TOKEN | head -c5` and `echo $CANVAS_BASE_URL`. If either is empty, inform the user they need to configure Canvas API access first.

## Usage

```bash
CANVAS="python ~/.apollo/skills/productivity/canvas-lms/scripts/canvas_api.py"

# List all active courses
$CANVAS list_courses --enrollment-state active

# List all courses (any state)
$CANVAS list_courses

# List assignments for a specific course
$CANVAS list_assignments 12345

# List assignments ordered by due date
$CANVAS list_assignments 12345 --order-by due_at

# Get full details for a single assignment (with attachments and links)
$CANVAS get_assignment 12345 67890

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

## Cross-Skill Chaining

### Document Analysis for Attachments

After fetching assignment details (via `get_assignment`), if the assignment includes PDF, DOCX, or other document attachments, automatically download them and use `skill_view("document-analysis")` to analyze the file contents.

### Propose Todoist Scheduling

After displaying assignments with due dates (via `list_assignments` or `list_pending`), propose to the user: "Would you like me to schedule these deadlines in Todoist?" Use the clarify tool to offer this. If the user accepts, use the todoist skill to create tasks with the appropriate due dates, durations, and labels.

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
  "external_tool_url": "",
  "google_assignments": false,
  "google_assignments_url": "",
  "locked_for_user": false,
  "lock_explanation": ""
}
```

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

## Analyzing Assignment Attachments

When `get_assignment` returns attachments (PDFs, documents, images), **always analyze them** — don't just list them. Follow this workflow:

### Step 1: Download the attachment
```bash
curl -L -o /tmp/FILENAME "ATTACHMENT_URL"
```

### Step 2: Detect file type and route to analysis

```bash
python3 ~/.apollo/skills/productivity/file-analysis/scripts/detect_filetype.py "/tmp/FILENAME"
```

### Step 3: Analyze based on type

**For PDFs** (most common attachment type):

1. **Try text extraction first** (FREE, local):
   ```bash
   python3 ~/.apollo/skills/productivity/ocr-and-documents/scripts/extract_pymupdf.py /tmp/FILENAME --markdown
   ```
   If this returns meaningful text → present the content. Done!

2. **If text is empty/garbled (scanned/image-based PDF)** — convert pages to images and use vision AI:
   ```bash
   python3 ~/.apollo/skills/productivity/document-analysis/scripts/pdf_to_images.py /tmp/FILENAME /tmp/pdf_pages/ --pages 0-4
   ```
   Then analyze each page image:
   ```
   vision_analyze(image_url="/tmp/pdf_pages/page_001.png", question="Extract all text and content from this page")
   ```
   Repeat for each page. Combine results into coherent text.

3. **If vision_analyze also fails** — use the model retry loop:
   - Check memory: `memory(action="search", target="memory", query="file-analysis-vision-model-success")`
   - Ask user: `clarify("Vision analysis failed. Which model should I try?", [previous_models..., "Enter custom model ID", "Skip"])`
   - Set model: run `export AUXILIARY_VISION_MODEL="chosen_model"` via terminal
   - Retry vision_analyze
   - On success: save model to memory

**For images** (PNG, JPG, etc.):
```
vision_analyze(image_url="/tmp/FILENAME", question="Describe and extract all content from this image")
```

**For documents** (DOCX, XLSX, PPTX):
Use the corresponding extraction script from the `document-analysis` skill:
```bash
# DOCX
python3 ~/.apollo/skills/productivity/document-analysis/scripts/extract_docx.py /tmp/FILENAME --format markdown
# XLSX
python3 ~/.apollo/skills/productivity/document-analysis/scripts/extract_xlsx.py /tmp/FILENAME --format summary
# PPTX
python3 ~/.apollo/skills/productivity/document-analysis/scripts/extract_pptx.py /tmp/FILENAME
```

**For Google Drive links** in assignment descriptions:
Use the `google-drive` skill to access the file, then route through the analysis above.

### Important
- **NEVER** just list attachments and tell the user to "use OCR software" — always attempt analysis
- The pdf_to_images + vision_analyze fallback works for scanned/image-based PDFs
- Present the extracted content directly to the user, summarized if needed

---

## Rules

- `list_courses`, `list_assignments`, and `get_assignment` are **read-only** — they only fetch data
- `submit_assignment` **MUST** always be called with `--dry-run` first; show the dry-run output to the user and wait for explicit confirmation before running without `--dry-run`
- The dry-run output shows exactly: assignment name, submission type, body text / URL / file path and size — the user must approve this exact content before the real submission
- `mark_done` only writes to the local DB (`~/.apollo/canvas_assignments.db`) — it never touches Canvas
- Google Assignments (LTI) cannot be submitted via the Canvas API; the command returns the Google URL for manual completion in a browser
- On first use, verify auth by running `$CANVAS list_courses` — if it fails with 401, guide the user through setup
- Canvas rate-limits to ~700 requests per 10 minutes; check `X-Rate-Limit-Remaining` header if hitting limits
- Run `sync_assignments` before `list_pending` / `list_done` to ensure the local DB is up to date

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

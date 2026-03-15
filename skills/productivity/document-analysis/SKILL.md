---
name: document-analysis
description: Extract and analyze content from documents — PDF, DOCX, XLSX, PPTX, and more. Uses free local tools (pymupdf, python-docx, openpyxl, python-pptx) with vision AI as universal fallback.
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  hermes:
    tags: [Documents, PDF, Word, Excel, PowerPoint, OCR, Extraction]
    related_skills: [file-analysis, ocr-and-documents, powerpoint, image-analysis]
---

# Document Analysis

Extract and analyze content from documents using free local tools. Vision AI serves as a universal fallback when local extraction fails.

**IMPORTANT**: All tool references (`read_file`, `vision_analyze`, `clarify`, `terminal`, `memory`, `skill_view`) are **agent tools** — invoke them as tool calls, NOT as Python imports.

## Scripts

- `scripts/extract_docx.py` — DOCX → markdown/text (python-docx, FREE)
- `scripts/extract_xlsx.py` — XLSX → CSV/summary (openpyxl, FREE)
- `scripts/extract_pptx.py` — PPTX → structured text (python-pptx, FREE)
- `scripts/pdf_to_images.py` — PDF pages → PNG images for vision fallback (pymupdf, FREE)

## Step 1: Identify Document Type

Route based on file extension:

| Extension | Method |
|-----------|--------|
| `.pdf` | → PDF Extraction (Step 2) |
| `.docx` | → DOCX Extraction (Step 3) |
| `.doc` | → Legacy DOC (Step 4) |
| `.xlsx`, `.xls` | → Excel Extraction (Step 5) |
| `.ods` | → ODS Extraction (Step 5, via openpyxl or libreoffice) |
| `.pptx` | → PPTX Extraction (Step 6) |
| `.ppt` | → Legacy PPT (Step 7) |
| `.rtf`, `.odt`, `.odp` | → LibreOffice Conversion (Step 8) |

---

## Step 2: PDF Extraction

### 2a. Try text extraction first (FREE, local)

Use the pymupdf script from the `ocr-and-documents` skill:
```bash
python3 ~/.hermes/skills/productivity/ocr-and-documents/scripts/extract_pymupdf.py "FILE_PATH"
```

Or with markdown output:
```bash
python3 ~/.hermes/skills/productivity/ocr-and-documents/scripts/extract_pymupdf.py "FILE_PATH" --markdown
```

If this returns meaningful text → done! Present the content.

### 2b. If text extraction is empty/garbled (scanned PDF)

Try marker-pdf for OCR (FREE, local, but ~3-5GB install):
```bash
python3 ~/.hermes/skills/productivity/ocr-and-documents/scripts/extract_marker.py "FILE_PATH"
```

If marker-pdf is not installed and space is available:
```bash
pip install marker-pdf
```

### 2c. If OCR tools fail — convert PDF pages to images for vision

Convert pages to PNG (FREE, local):
```bash
python3 ~/.hermes/skills/productivity/document-analysis/scripts/pdf_to_images.py "FILE_PATH" /tmp/pdf_pages/ --pages 0-4
```

Then analyze each page image with `vision_analyze`:
```
vision_analyze(image_url="/tmp/pdf_pages/page_001.png", question="Extract all text and content from this page")
```

If `vision_analyze` fails → use the **Vision Model Fallback** (Step 9).

---

## Step 3: DOCX Extraction (FREE)

```bash
python3 ~/.hermes/skills/productivity/document-analysis/scripts/extract_docx.py "FILE_PATH" --format markdown
```

If python-docx is not installed:
```bash
pip install python-docx
```

Returns: paragraphs, headings, tables in markdown format.

If extraction fails → try **Vision Model Fallback** (Step 9) as last resort.

---

## Step 4: Legacy DOC Files

Legacy .doc files need conversion to .docx first:

```bash
libreoffice --headless --convert-to docx "FILE_PATH" --outdir /tmp/
```

Then extract the converted .docx with Step 3.

If libreoffice is not available, try:
```bash
antiword "FILE_PATH"    # Simple text extraction
catdoc "FILE_PATH"      # Alternative text extraction
```

If all fail → **Vision Model Fallback** (Step 9).

---

## Step 5: Excel Extraction (FREE)

```bash
python3 ~/.hermes/skills/productivity/document-analysis/scripts/extract_xlsx.py "FILE_PATH" --format summary
```

Options:
- `--format summary` — Headers, row/column counts, preview of first/last rows
- `--format csv` — Full CSV output
- `--sheet "Sheet1"` — Specific sheet only

If openpyxl is not installed:
```bash
pip install openpyxl
```

For ODS files, openpyxl may work directly. If not:
```bash
libreoffice --headless --convert-to xlsx "FILE_PATH" --outdir /tmp/
```

If all fail → **Vision Model Fallback** (Step 9).

---

## Step 6: PPTX Extraction (FREE)

```bash
python3 ~/.hermes/skills/productivity/document-analysis/scripts/extract_pptx.py "FILE_PATH"
```

If python-pptx is not installed:
```bash
pip install python-pptx
```

Returns: slide-by-slide text, tables, and speaker notes.

If extraction fails → **Vision Model Fallback** (Step 9).

---

## Step 7: Legacy PPT Files

Convert to .pptx first:
```bash
libreoffice --headless --convert-to pptx "FILE_PATH" --outdir /tmp/
```

Then extract with Step 6.

If libreoffice is not available → **Vision Model Fallback** (Step 9).

---

## Step 8: RTF, ODT, ODP Files

Convert to a simpler format first:
```bash
# RTF → text
unrtf --text "FILE_PATH" 2>/dev/null || libreoffice --headless --convert-to txt "FILE_PATH" --outdir /tmp/

# ODT → DOCX
libreoffice --headless --convert-to docx "FILE_PATH" --outdir /tmp/

# ODP → PPTX
libreoffice --headless --convert-to pptx "FILE_PATH" --outdir /tmp/
```

Then extract using the appropriate method above.

If conversion fails → **Vision Model Fallback** (Step 9).

---

## Step 9: Vision Model Fallback (Universal Last Resort)

When all local extraction methods fail, use the AI vision model:

**9a. Try vision_analyze with the file directly:**
```
vision_analyze(image_url="FILE_PATH", question="Extract and analyze all content from this document")
```

**9b. If vision fails, check memory for successful models:**
```
memory(action="search", target="memory", query="file-analysis-vision-model-success")
```

**9c. Ask user to pick a model:**
```
clarify("Local extraction failed and vision analysis failed with the default model. Which model should I try?",
        [PREVIOUS_MODEL_1, PREVIOUS_MODEL_2, "Enter a custom model ID", "Skip analysis"])
```

If no previous models in memory:
```
clarify("Local extraction failed and vision analysis failed. Which model should I try?",
        ["google/gemini-2.5-flash", "google/gemini-2.5-pro", "Enter a custom model ID", "Skip analysis"])
```

**9d. Set the chosen model and retry:**
```bash
export AUXILIARY_VISION_MODEL="chosen_model_id"
```
Then retry `vision_analyze`.

On success → save model:
```
memory(action="add", target="memory", content="file-analysis-vision-model-success: CHOSEN_MODEL_ID")
```

**9e. Loop until success or user skips.**

---

## Notes

- All extraction tools are FREE and run locally — no API calls except for vision fallback
- pymupdf scripts are reused from the existing `ocr-and-documents` skill
- Vision AI is the universal last resort for any document that local tools can't handle
- For Google Drive documents, use the `google-drive` skill to download first

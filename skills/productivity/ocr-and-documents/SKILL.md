---
name: ocr-and-documents
description: Extract text from PDFs and scanned documents. Use webscrape for remote URLs, pymupdf for local text-based PDFs, marker-pdf for OCR/scanned docs. For DOCX use python-docx, for PPTX see the powerpoint skill.
version: 2.3.0
author: Apollo Agent
license: MIT
metadata:
  apollo:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [powerpoint]
    school: true
    school_category: "File Analysis"
---

# PDF & Document Extraction

For DOCX: use `python-docx` (parses actual document structure, far better than OCR).
For PPTX: see the `powerpoint` skill (uses `python-pptx` with full slide/notes support). Load it with `skill_view("powerpoint")`.
This skill covers **PDFs and scanned documents**.

## Step 1: Remote URL Available?

If the document has a URL, **always try `webscrape` first**:

```
webscrape(urls=["https://arxiv.org/pdf/2402.03300"])
webscrape(urls=["https://example.com/report.pdf"])
```

This handles PDF-to-markdown conversion via Firecrawl with no local dependencies.

Only use local extraction when: the file is local, webscrape fails, or you need batch processing.

## Step 2: Choose Local Extractor

| Feature | pymupdf (~25MB) | marker-pdf (~3-5GB) |
|---------|-----------------|---------------------|
| **Text-based PDF** | ✅ | ✅ |
| **Scanned PDF (OCR)** | ❌ | ✅ (90+ languages) |
| **Tables** | ✅ (basic) | ✅ (high accuracy) |
| **Equations / LaTeX** | ❌ | ✅ |
| **Code blocks** | ❌ | ✅ |
| **Forms** | ❌ | ✅ |
| **Headers/footers removal** | ❌ | ✅ |
| **Reading order detection** | ❌ | ✅ |
| **Images extraction** | ✅ (embedded) | ✅ (with context) |
| **Images → text (OCR)** | ❌ | ✅ |
| **EPUB** | ✅ | ✅ |
| **Markdown output** | ✅ (via pymupdf4llm) | ✅ (native, higher quality) |
| **Install size** | ~25MB | ~3-5GB (PyTorch + models) |
| **Speed** | Instant | ~1-14s/page (CPU), ~0.2s/page (GPU) |

**Decision**: Use pymupdf unless you need OCR, equations, forms, or complex layout analysis.

If the user needs marker capabilities but the system lacks ~5GB free disk:
> "This document needs OCR/advanced extraction (marker-pdf), which requires ~5GB for PyTorch and models. Your system has [X]GB free. Options: free up space, provide a URL so I can use webscrape, or I can try pymupdf which works for text-based PDFs but not scanned documents or equations."

---

## pymupdf (lightweight)

```bash
pip install pymupdf pymupdf4llm
```

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## Arxiv Papers

```
# Abstract only (fast)
webscrape(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
webscrape(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Step 3: Vision AI Fallback (when pymupdf and marker-pdf both fail)

If text extraction returns empty/garbled content (scanned PDF, image-only pages) AND marker-pdf is not available or fails:

**Convert PDF pages to images, then use vision AI:**
```bash
python3 ~/.apollo/skills/productivity/document-analysis/scripts/pdf_to_images.py "document.pdf" /tmp/pdf_pages/ --pages 0-4
```

Then analyze each page with vision:
```
vision_analyze(image_url="/tmp/pdf_pages/page_001.png", question="Extract all text and content from this page")
```

Repeat for each page. This works for any scanned/image-based PDF.

If `vision_analyze` fails, try a different model:
- Check memory: `memory(action="search", target="memory", query="file-analysis-vision-model-success")`
- Ask user: `clarify("Which vision model should I try?", [previous_models..., "Enter custom model ID", "Skip"])`
- Set model: `export AUXILIARY_VISION_MODEL="chosen_model"` via terminal, then retry

**NEVER give up and tell the user to "use OCR software" — the pdf_to_images + vision_analyze fallback should always be attempted.**

## Notes

- `webscrape` is always first choice for URLs
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- **pdf_to_images + vision_analyze** is the fallback when both text extractors fail — always try this
- Both helper scripts accept `--help` for full usage
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- For Word docs: `pip install python-docx` (better than OCR — parses actual structure)
- For PowerPoint: see the `powerpoint` skill (uses python-pptx)
- For all other file types: see the `document-analysis` and `file-analysis` skills

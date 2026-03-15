---
name: image-analysis
description: Analyze images using AI vision models. Supports PNG, JPG, GIF, BMP, WebP, SVG, TIFF, HEIC, AVIF, and more. Converts exotic formats automatically. Falls back to alternative models if vision fails.
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  hermes:
    tags: [Images, Vision, Analysis, PNG, JPG, Screenshot, OCR]
    related_skills: [file-analysis, document-analysis]
---

# Image Analysis

Analyze images using AI vision models with automatic format conversion and model fallback.

**IMPORTANT**: All tool references (`vision_analyze`, `clarify`, `terminal`, `memory`, `read_file`) are **agent tools** — invoke them as tool calls, NOT as Python imports.

## Scripts

- `scripts/convert_image.py` — Convert exotic image formats to PNG (uses Pillow, FREE/local)

## Step 1: Check Image Format

Common formats that work directly with `vision_analyze`:
- **Direct support**: PNG, JPG/JPEG, GIF, WebP, BMP

Exotic formats that need conversion first:
- **Needs conversion**: HEIC, HEIF, AVIF, TIFF/TIF, SVG, RAW, CR2, NEF, DNG, PSD, EPS, ICO

## Step 2: Analyze the Image

### For directly supported formats (PNG, JPG, GIF, WebP, BMP):

```
vision_analyze(image_url="FILE_PATH", question="USER_REQUEST")
```

If `vision_analyze` succeeds → present the analysis to the user. Done!

### For exotic formats:

**Convert first** (FREE, local, using Pillow):
```bash
python3 ~/.hermes/skills/productivity/image-analysis/scripts/convert_image.py "INPUT_PATH" "OUTPUT_PATH.png"
```

- If conversion succeeds → run `vision_analyze` on the converted PNG
- If conversion fails (missing dependency) → install the dependency and retry:
  - HEIC/HEIF: `pip install pillow-heif`
  - AVIF: `pip install pillow-avif-plugin` (or upgrade Pillow to 10+)
  - SVG: `pip install cairosvg`
  - General: `pip install Pillow`

## Step 3: Vision Model Fallback (if vision_analyze fails)

If `vision_analyze` fails (model doesn't support vision, API error, etc.):

**3a. Check memory for previously successful models:**
```
memory(action="search", target="memory", query="file-analysis-vision-model-success")
```

**3b. Ask user to pick a model:**
```
clarify("Vision analysis failed with the default model. Which model should I try?",
        [PREVIOUS_MODEL_1, PREVIOUS_MODEL_2, "Enter a custom model ID", "Skip vision analysis"])
```

If the user has no previous models in memory, offer:
```
clarify("Vision analysis failed with the default model. Which model should I try?",
        ["google/gemini-2.5-flash", "google/gemini-2.5-pro", "Enter a custom model ID", "Skip vision analysis"])
```

**3c. Set the chosen model and retry:**
```bash
export AUXILIARY_VISION_MODEL="chosen_model_id"
```

Then retry `vision_analyze`. If it succeeds:
```
memory(action="add", target="memory",
       content="file-analysis-vision-model-success: CHOSEN_MODEL_ID")
```

**3d. If it fails again → loop back to 3b.**

**3e. If user chooses "Skip vision analysis":**
- Report available file metadata (dimensions, format, file size) using:
  ```bash
  python3 -c "from PIL import Image; img = Image.open('FILE_PATH'); print(f'Size: {img.size}, Mode: {img.mode}, Format: {img.format}')"
  ```
  Or use `file FILE_PATH` and `read_file` for basic info.

## Step 4: Present Results

When vision analysis succeeds, present:
1. The AI's analysis/description of the image
2. Answer to the user's specific question (if any)
3. Relevant metadata (dimensions, format) if useful

## Notes

- All conversion is done locally with Pillow — FREE, no API calls
- Vision analysis uses the configured auxiliary model (Gemini Flash by default)
- Successful models are saved to memory for faster retry on future images
- For screenshots with text, the vision model can typically read the text directly
- For diagrams/charts, describe the structure and data

#!/usr/bin/env python3
"""Convert PDF pages to PNG images for vision analysis (FREE, local).

Uses pymupdf to render PDF pages as images. Useful as a fallback when
text extraction fails on scanned/complex PDFs.

Usage:
    python3 pdf_to_images.py document.pdf output_dir/
    python3 pdf_to_images.py document.pdf output_dir/ --pages 0-4
    python3 pdf_to_images.py document.pdf output_dir/ --dpi 200
"""

import json
import os
import sys
from pathlib import Path


def convert(input_path, output_dir, pages=None, dpi=150):
    """Convert PDF pages to PNG images."""
    path = Path(input_path)
    if not path.exists():
        return {"success": False, "error": f"File not found: {input_path}"}

    try:
        import pymupdf
    except ImportError:
        return {
            "success": False,
            "error": "pymupdf not installed. Run: pip install pymupdf",
        }

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        doc = pymupdf.open(str(path))
    except Exception as e:
        return {"success": False, "error": f"Failed to open PDF: {e}"}

    total_pages = len(doc)

    # Parse page range
    if pages is not None:
        if "-" in pages:
            start, end = pages.split("-", 1)
            page_list = list(range(int(start), min(int(end) + 1, total_pages)))
        else:
            page_list = [int(pages)]
    else:
        page_list = list(range(total_pages))

    image_paths = []
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)

    for page_num in page_list:
        if page_num >= total_pages:
            continue
        page = doc[page_num]
        pix = page.get_pixmap(matrix=mat)
        img_path = out_dir / f"page_{page_num + 1:03d}.png"
        pix.save(str(img_path))
        image_paths.append(str(img_path))

    doc.close()

    return {
        "success": True,
        "total_pages": total_pages,
        "converted_pages": len(image_paths),
        "image_paths": image_paths,
        "dpi": dpi,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: pdf_to_images.py <pdf> <output_dir> [--pages 0-4] [--dpi 200]"}))
        sys.exit(1)

    pages_arg = None
    dpi_arg = 150
    args = sys.argv[3:]
    i = 0
    while i < len(args):
        if args[i] == "--pages" and i + 1 < len(args):
            pages_arg = args[i + 1]
            i += 2
        elif args[i] == "--dpi" and i + 1 < len(args):
            dpi_arg = int(args[i + 1])
            i += 2
        else:
            i += 1

    result = convert(sys.argv[1], sys.argv[2], pages_arg, dpi_arg)
    print(json.dumps(result, indent=2))

#!/usr/bin/env python3
"""Convert images between formats for the image-analysis skill.

Converts exotic formats (HEIC, TIFF, BMP, AVIF, etc.) to PNG for
compatibility with vision models. Uses Pillow (free, local).

Usage:
    python3 convert_image.py input.heic output.png
    python3 convert_image.py input.tiff  # auto-generates output.png
"""

import json
import os
import sys
from pathlib import Path


def convert(input_path, output_path=None):
    """Convert an image to PNG format."""
    inp = Path(input_path)
    if not inp.exists():
        return {"success": False, "error": f"File not found: {input_path}"}

    ext = inp.suffix.lower()

    # Determine output path
    if output_path is None:
        output_path = str(inp.with_suffix(".png"))
    out = Path(output_path)

    # Try Pillow first
    try:
        from PIL import Image
    except ImportError:
        return {
            "success": False,
            "error": "Pillow not installed. Run: pip install Pillow",
        }

    # HEIC/HEIF needs pillow-heif
    if ext in (".heic", ".heif"):
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except ImportError:
            return {
                "success": False,
                "error": "pillow-heif not installed. Run: pip install pillow-heif",
            }

    # AVIF needs pillow-avif-plugin or Pillow 10+
    if ext == ".avif":
        try:
            import pillow_avif  # noqa: F401
        except ImportError:
            pass  # Pillow 10+ has built-in AVIF support

    # SVG needs cairosvg
    if ext == ".svg":
        try:
            import cairosvg
            cairosvg.svg2png(url=str(inp), write_to=str(out))
            return {
                "success": True,
                "output_path": str(out),
                "method": "cairosvg",
            }
        except ImportError:
            return {
                "success": False,
                "error": "cairosvg not installed for SVG conversion. Run: pip install cairosvg",
            }
        except Exception as e:
            return {"success": False, "error": f"SVG conversion failed: {e}"}

    # General Pillow conversion
    try:
        img = Image.open(str(inp))
        # Convert RGBA/P modes for PNG compatibility
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
        img.save(str(out), "PNG")
        return {
            "success": True,
            "output_path": str(out),
            "original_size": f"{img.size[0]}x{img.size[1]}",
            "method": "pillow",
        }
    except Exception as e:
        return {"success": False, "error": f"Conversion failed: {e}"}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: convert_image.py <input> [output]"}))
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) > 2 else None
    result = convert(sys.argv[1], out)
    print(json.dumps(result, indent=2))

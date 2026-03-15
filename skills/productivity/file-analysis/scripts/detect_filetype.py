#!/usr/bin/env python3
"""File type detection and metadata for the file-analysis skill."""

import json
import mimetypes
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

CATEGORIES = {
    # Text
    ".txt": "text", ".md": "text", ".markdown": "text", ".csv": "text",
    ".tsv": "text", ".json": "text", ".jsonl": "text", ".ndjson": "text",
    ".xml": "text", ".yaml": "text", ".yml": "text", ".html": "text",
    ".htm": "text", ".log": "text", ".rst": "text", ".tex": "text",
    ".latex": "text", ".org": "text", ".bib": "text", ".toml": "text",
    ".ini": "text", ".cfg": "text", ".conf": "text", ".properties": "text",
    ".env": "text", ".gitignore": "text", ".editorconfig": "text",
    ".dockerignore": "text",
    # Code
    ".py": "code", ".pyw": "code", ".pyi": "code",
    ".js": "code", ".mjs": "code", ".cjs": "code",
    ".ts": "code", ".tsx": "code", ".jsx": "code",
    ".java": "code", ".kt": "code", ".kts": "code", ".scala": "code",
    ".c": "code", ".h": "code", ".cpp": "code", ".hpp": "code",
    ".cc": "code", ".cxx": "code", ".hxx": "code",
    ".cs": "code", ".fs": "code", ".fsx": "code",
    ".go": "code", ".rs": "code", ".swift": "code", ".m": "code",
    ".rb": "code", ".erb": "code",
    ".php": "code", ".pl": "code", ".pm": "code",
    ".lua": "code", ".r": "code", ".R": "code",
    ".hs": "code", ".lhs": "code",
    ".ex": "code", ".exs": "code", ".erl": "code",
    ".clj": "code", ".cljs": "code", ".cljc": "code",
    ".dart": "code", ".zig": "code", ".nim": "code",
    ".v": "code", ".sv": "code",
    ".sh": "code", ".bash": "code", ".zsh": "code", ".fish": "code",
    ".ps1": "code", ".bat": "code", ".cmd": "code",
    ".sql": "code", ".graphql": "code", ".gql": "code",
    ".proto": "code", ".thrift": "code",
    ".vue": "code", ".svelte": "code",
    ".css": "code", ".scss": "code", ".sass": "code", ".less": "code",
    ".styl": "code",
    ".makefile": "code", ".cmake": "code",
    ".dockerfile": "code",
    ".tf": "code", ".hcl": "code",
    ".wasm": "code", ".wat": "code",
    # Images
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".gif": "image",
    ".bmp": "image", ".webp": "image", ".svg": "image",
    ".tiff": "image", ".tif": "image", ".ico": "image",
    ".heic": "image", ".heif": "image", ".avif": "image",
    ".raw": "image", ".cr2": "image", ".nef": "image", ".dng": "image",
    ".psd": "image", ".ai": "image", ".eps": "image",
    # Documents
    ".pdf": "document", ".docx": "document", ".doc": "document",
    ".xlsx": "document", ".xls": "document", ".ods": "document",
    ".pptx": "document", ".ppt": "document", ".odp": "document",
    ".odt": "document", ".rtf": "document",
    ".pages": "document", ".numbers": "document", ".key": "document",
    # Data
    ".parquet": "data", ".feather": "data", ".arrow": "data",
    ".sqlite": "data", ".db": "data", ".sqlite3": "data",
    ".hdf5": "data", ".h5": "data", ".nc": "data",
    # Notebooks
    ".ipynb": "text",
    # Archives
    ".zip": "archive", ".tar": "archive", ".gz": "archive",
    ".bz2": "archive", ".xz": "archive", ".7z": "archive",
    ".rar": "archive", ".tgz": "archive",
    # Audio
    ".mp3": "audio", ".wav": "audio", ".ogg": "audio", ".flac": "audio",
    ".m4a": "audio", ".aac": "audio", ".wma": "audio",
    ".opus": "audio", ".aiff": "audio", ".mid": "audio", ".midi": "audio",
    # Video
    ".mp4": "video", ".avi": "video", ".mkv": "video", ".mov": "video",
    ".webm": "video", ".wmv": "video", ".flv": "video",
    ".m4v": "video", ".mpg": "video", ".mpeg": "video",
    ".3gp": "video", ".ts": "video",
}

# Handle ambiguous .ts (TypeScript vs MPEG-TS) — default to code
# since TypeScript is far more common in development contexts
CATEGORIES[".ts"] = "code"


def _human_size(size_bytes):
    """Convert bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def detect(path_str):
    """Detect file type and return metadata as a dict."""
    # Check if input is a URL
    parsed = urlparse(path_str)
    is_url = parsed.scheme in ("http", "https", "ftp")

    if is_url:
        # For URLs, extract extension from path
        url_path = parsed.path
        ext = os.path.splitext(url_path)[1].lower()
        return {
            "path": path_str,
            "exists": None,
            "is_url": True,
            "extension": ext or None,
            "mime_type": mimetypes.guess_type(url_path)[0],
            "category": CATEGORIES.get(ext, "unknown"),
            "size_bytes": None,
            "size_human": None,
        }

    path = Path(path_str)
    exists = path.exists()

    # Handle files without extensions (Makefile, Dockerfile, etc.)
    name_lower = path.name.lower()
    if path.suffix == "":
        ext = ""
        special_names = {
            "makefile": "code", "dockerfile": "code", "vagrantfile": "code",
            "rakefile": "code", "gemfile": "code", "procfile": "code",
            "brewfile": "code", "justfile": "code",
            "readme": "text", "license": "text", "changelog": "text",
            "authors": "text", "contributors": "text", "todo": "text",
        }
        category = special_names.get(name_lower, "unknown")
    else:
        ext = path.suffix.lower()
        category = CATEGORIES.get(ext, "unknown")

    # Get file size if exists
    size_bytes = None
    size_human = None
    if exists and path.is_file():
        size_bytes = path.stat().st_size
        size_human = _human_size(size_bytes)

    # Guess MIME type
    mime_type = mimetypes.guess_type(str(path))[0]

    return {
        "path": str(path.resolve()) if exists else path_str,
        "exists": exists,
        "is_url": False,
        "extension": ext or None,
        "mime_type": mime_type,
        "category": category,
        "size_bytes": size_bytes,
        "size_human": size_human,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: detect_filetype.py <file_path>"}))
        sys.exit(1)
    result = detect(sys.argv[1])
    print(json.dumps(result, indent=2))

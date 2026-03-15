#!/usr/bin/env python3
"""Extract keyframes from video files using ffmpeg (FREE, local).

Cost-optimized: extracts only a few evenly-spaced frames by default
to minimize vision API calls.

Usage:
    python3 extract_frames.py input.mp4 output_dir/
    python3 extract_frames.py input.mp4 output_dir/ --count 3
    python3 extract_frames.py input.mp4 output_dir/ --count 10
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def get_duration(video_path):
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                str(video_path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            import json as _json
            data = _json.loads(result.stdout)
            return float(data.get("format", {}).get("duration", 0))
    except Exception:
        pass
    return 0


def extract_frames(video_path, output_dir, count=3):
    """Extract evenly-spaced frames from a video."""
    path = Path(video_path)
    if not path.exists():
        return {"success": False, "error": f"File not found: {video_path}"}

    # Check ffmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=10)
    except FileNotFoundError:
        return {
            "success": False,
            "error": "ffmpeg not installed. Run: apt-get install -y ffmpeg (or brew install ffmpeg)",
        }

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Get video duration
    duration = get_duration(path)
    if duration <= 0:
        # Fallback: just extract first frame
        duration = 1
        count = 1

    # Calculate timestamps for evenly-spaced frames
    # Place frames at 10%, 50%, 90% for 3 frames (avoid very start/end)
    if count == 1:
        timestamps = [0]
    else:
        margin = duration * 0.1  # 10% margin from edges
        usable = duration - 2 * margin
        if usable <= 0:
            timestamps = [duration / 2]
        else:
            timestamps = [
                margin + (usable * i / (count - 1))
                for i in range(count)
            ]

    frame_paths = []
    for i, ts in enumerate(timestamps):
        output_path = out_dir / f"frame_{i + 1:03d}.png"
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-ss", str(ts),
                    "-i", str(path),
                    "-vframes", "1",
                    "-q:v", "2",
                    str(output_path),
                ],
                capture_output=True, timeout=30,
            )
            if output_path.exists():
                frame_paths.append(str(output_path))
        except Exception as e:
            # Continue with remaining frames
            pass

    if not frame_paths:
        return {"success": False, "error": "Failed to extract any frames from the video"}

    return {
        "success": True,
        "duration": round(duration, 1),
        "frame_count": len(frame_paths),
        "frame_paths": frame_paths,
        "timestamps": [round(t, 1) for t in timestamps[:len(frame_paths)]],
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: extract_frames.py <video> <output_dir> [--count N]"}))
        sys.exit(1)

    count_arg = 3
    args = sys.argv[3:]
    i = 0
    while i < len(args):
        if args[i] == "--count" and i + 1 < len(args):
            count_arg = int(args[i + 1])
            i += 2
        else:
            i += 1

    result = extract_frames(sys.argv[1], sys.argv[2], count_arg)
    print(json.dumps(result, indent=2))

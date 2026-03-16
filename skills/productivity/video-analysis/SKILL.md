---
name: video-analysis
description: Analyze video files by extracting metadata, keyframes, and audio. Cost-optimized — uses local ffmpeg/ffprobe (FREE) and minimal keyframes. Supports direct video input for omni models.
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  apollo:
    tags: [Video, Analysis, Frames, Transcription, Vision]
    related_skills: [file-analysis, image-analysis, audio-analysis]
    school: true
    school_category: "File Analysis"
---

# Video Analysis

Analyze video files using local tools (FREE) with cost-optimized keyframe extraction.

**Cost optimization**: All metadata and frame extraction is done locally with ffmpeg/ffprobe (FREE). Only 3 keyframes are sent to the vision model by default, keeping API costs minimal.

**IMPORTANT**: All tool references (`vision_analyze`, `clarify`, `terminal`, `memory`) are **agent tools** — invoke them as tool calls, NOT as Python imports.

## Scripts

- `scripts/extract_frames.py` — Extract evenly-spaced keyframes from video (ffmpeg, FREE)

## Step 1: Get Video Metadata (FREE, local)

```bash
ffprobe -v quiet -print_format json -show_format -show_streams "FILE_PATH"
```

Extract and present:
- **Duration** (formatted as HH:MM:SS)
- **Resolution** (width x height)
- **Codec** (video + audio)
- **FPS** (frames per second)
- **Bitrate**
- **File size**

If ffprobe is not available:
```bash
apt-get install -y ffmpeg 2>/dev/null || brew install ffmpeg 2>/dev/null
```

## Step 2: Ask User About Analysis Depth

Before extracting frames, ask the user how deep they want the analysis:

```
clarify("How should I analyze this video?",
        ["Keyframes only (3 frames, cheapest)",
         "More keyframes (10 frames)",
         "Full video to AI (if supported by your model)",
         "Audio transcript only",
         "Metadata only (no AI)"])
```

## Step 3: Extract and Analyze Keyframes

### For keyframe analysis (default, cost-optimized):

Extract frames (FREE, local):
```bash
python3 ~/.apollo/skills/productivity/video-analysis/scripts/extract_frames.py "FILE_PATH" /tmp/video_frames/ --count 3
```

The script extracts 3 frames at ~10%, ~50%, and ~90% of the video duration.

Then analyze each frame with `vision_analyze`:
```
vision_analyze(image_url="/tmp/video_frames/frame_001.png",
               question="Describe what you see in this video frame (frame 1 of 3, from the start). USER_REQUEST")
```

Repeat for each frame. Combine the analyses into a coherent summary of the video content.

### For more keyframes (10 frames):
```bash
python3 ~/.apollo/skills/productivity/video-analysis/scripts/extract_frames.py "FILE_PATH" /tmp/video_frames/ --count 10
```

### For full video to AI (omni model):

If the user's model supports direct video input:
```
vision_analyze(image_url="FILE_PATH", question="Analyze this video: USER_REQUEST")
```

This sends the full video file to the model. More thorough but more expensive.

## Step 4: Audio Transcription (FREE, local)

If the user wants audio transcription:

Extract audio track (FREE):
```bash
ffmpeg -i "FILE_PATH" -vn -acodec pcm_s16le -ar 16000 -ac 1 -y /tmp/video_audio.wav
```

Transcribe with local whisper (FREE):
```bash
python3 -c "
from tools.transcription_tools import transcribe_audio
import json
result = transcribe_audio('/tmp/video_audio.wav')
print(json.dumps(result, indent=2))
"
```

If faster-whisper is not installed:
```bash
pip install faster-whisper
```

## Step 5: Present Combined Results

Combine all available information:
1. **Metadata**: Duration, resolution, codec, file size
2. **Visual summary**: Description from keyframe analysis
3. **Audio transcript**: If transcription was performed
4. **Answer**: Response to the user's specific question

## Step 6: Vision Model Fallback

If `vision_analyze` fails on keyframes:

**6a. Try conversion first** — re-extract frames at lower resolution:
```bash
python3 ~/.apollo/skills/productivity/video-analysis/scripts/extract_frames.py "FILE_PATH" /tmp/video_frames_retry/ --count 1
```

**6b. Check memory for successful models:**
```
memory(action="search", target="memory", query="file-analysis-vision-model-success")
```

**6c. Ask user to pick a model:**
```
clarify("Vision analysis failed with the default model. Which model should I try?",
        [PREVIOUS_MODEL_1, PREVIOUS_MODEL_2, "Enter a custom model ID", "Skip vision analysis"])
```

If no previous models in memory:
```
clarify("Vision analysis failed. Which model should I try?",
        ["google/gemini-2.5-flash", "google/gemini-2.5-pro", "Enter a custom model ID", "Skip vision analysis"])
```

**6d. Set the chosen model and retry:**
```bash
export AUXILIARY_VISION_MODEL="chosen_model_id"
```
Then retry `vision_analyze`.

On success:
```
memory(action="add", target="memory", content="file-analysis-vision-model-success: CHOSEN_MODEL_ID")
```

**6e. Loop until success or user skips.**

If user skips vision → present metadata + audio transcript only.

## Notes

- All local processing (ffmpeg, ffprobe, whisper) is FREE — no API calls
- Default 3 keyframes keeps vision API costs to a minimum
- For surveillance/security footage: use more keyframes (10+) or time-interval extraction
- For short clips (<30s): 3 frames is usually sufficient
- For long videos (>1hr): consider extracting audio transcript as the primary analysis
- The user's omni model may support direct video input — offer this as an option
- Clean up extracted frames after analysis: `rm -rf /tmp/video_frames/`

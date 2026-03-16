---
name: audio-analysis
description: Transcribe and analyze audio files using local faster-whisper (FREE). Supports MP3, WAV, OGG, FLAC, M4A, and more. Converts unsupported formats via ffmpeg. Vision AI fallback for omni models.
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  apollo:
    tags: [Audio, Transcription, Whisper, Speech, Music, Analysis]
    related_skills: [file-analysis, video-analysis]
    school: true
    school_category: "File Analysis"
---

# Audio Analysis

Transcribe and analyze audio files using **local faster-whisper** (FREE, no API key needed). Falls back to format conversion via ffmpeg and vision AI for omni models.

**IMPORTANT**: All tool references (`terminal`, `clarify`, `memory`, `vision_analyze`) are **agent tools** — invoke them as tool calls, NOT as Python imports.

## Supported Formats

**Direct support** (faster-whisper): mp3, mp4, mpeg, mpga, m4a, wav, webm, ogg
**Via conversion** (ffmpeg): wma, aac, flac, opus, aiff, mid/midi, and most other audio formats

## Step 1: Get Audio Metadata (FREE, local)

```bash
ffprobe -v quiet -print_format json -show_format -show_streams "FILE_PATH" 2>/dev/null
```

If ffprobe is available, extract and present:
- Duration
- Format/codec
- Sample rate, channels
- Bitrate
- File size

If ffprobe is not available, skip metadata — proceed to transcription.

## Step 2: Check Format Compatibility

Supported formats for direct transcription: `.mp3`, `.mp4`, `.mpeg`, `.mpga`, `.m4a`, `.wav`, `.webm`, `.ogg`

If the file extension is NOT in the supported list → go to **Step 3** (conversion).
If supported → go to **Step 4** (transcription).

## Step 3: Convert Unsupported Formats (FREE, local)

Convert to WAV using ffmpeg:
```bash
ffmpeg -i "FILE_PATH" -ar 16000 -ac 1 -y /tmp/audio_converted.wav
```

If ffmpeg is not available:
```bash
# Try installing
apt-get install -y ffmpeg 2>/dev/null || brew install ffmpeg 2>/dev/null
```

If conversion succeeds → proceed to **Step 4** with the converted file.
If conversion fails → go to **Step 6** (vision fallback).

## Step 4: Transcribe with Local Whisper (FREE)

Check file size first — faster-whisper has a 25MB limit:
```bash
stat --format="%s" "FILE_PATH" 2>/dev/null || stat -f "%z" "FILE_PATH"
```

If file is >25MB, split it first:
```bash
# Split into 10-minute chunks
ffmpeg -i "FILE_PATH" -f segment -segment_time 600 -c copy /tmp/audio_chunk_%03d.wav
```

Transcribe using the local whisper tool:
```bash
python3 -c "
from tools.transcription_tools import transcribe_audio
import json
result = transcribe_audio('FILE_PATH_OR_CONVERTED')
print(json.dumps(result, indent=2))
"
```

If faster-whisper is not installed:
```bash
pip install faster-whisper
```

Then retry transcription.

## Step 5: Present Results

When transcription succeeds, present:
1. **Metadata** (if available): duration, format, quality
2. **Full transcript**: The transcribed text
3. **Summary**: Brief summary of the audio content if the transcript is long
4. Answer the user's specific question about the audio

## Step 6: Vision AI Fallback (for omni models)

If local transcription fails (unsupported format, corrupted file, whisper errors):

Since the user's model may be omni (supports audio input directly), try `vision_analyze`:

**6a. Try vision_analyze with the audio file:**
```
vision_analyze(image_url="FILE_PATH", question="Transcribe and analyze this audio file")
```

**6b. If vision fails, check memory for successful models:**
```
memory(action="search", target="memory", query="file-analysis-vision-model-success")
```

**6c. Ask user to pick a model:**
```
clarify("Local transcription failed and the default model couldn't process this audio. Which model should I try?",
        [PREVIOUS_MODEL_1, PREVIOUS_MODEL_2, "Enter a custom model ID", "Skip analysis"])
```

If no previous models in memory:
```
clarify("Local transcription failed. Which model should I try for audio analysis?",
        ["google/gemini-2.5-flash", "google/gemini-2.5-pro", "Enter a custom model ID", "Skip analysis"])
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

## Notes

- Local faster-whisper is FREE — no API key required, runs on CPU (~150MB model download on first use)
- ffmpeg conversion is FREE and local
- The `base` whisper model is used by default — good balance of speed and accuracy
- For better accuracy on complex audio, the user can configure a larger model via `STT_LOCAL_MODEL` env var
- Vision AI fallback works if the user's model supports audio input (omni models like Gemini)
- For MIDI files: these are not audio recordings — report them as musical notation/data files

# Reddit-Brainrot Video Pipeline

Turns a text story into a finished 1080×1920 short: AI voiceover over looping
gameplay footage with TikTok-style word-by-word captions. **100% free**, no paid
APIs.

```
story.txt ──► Edge-TTS voice ──► Whisper word timestamps ──► karaoke captions ──► FFmpeg ──► video.mp4
```

## Tools used (all free)

| Stage | Tool | Cost |
|-------|------|------|
| Voiceover | [edge-tts](https://github.com/rany2/edge-tts) (Microsoft Edge voices) | Free, no key |
| Captions | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Free, local |
| Assembly | FFmpeg | Free |
| Upload | YouTube Data API v3 | Free (quota-limited) |

## Setup

```bash
# 1. System deps
#    macOS:   brew install ffmpeg
#    Ubuntu:  sudo apt install ffmpeg
#    Windows: winget install Gyan.FFmpeg
pip install -r requirements.txt
```

## Make a video

1. Drop a looping gameplay clip (Minecraft parkour, Subway Surfers, etc.) at
   `assets/gameplay.mp4`. Use clips you have the right to use.
2. Put your narration in a `.txt` file (see `stories/sample.txt`).

```bash
python generate.py --story stories/sample.txt --background assets/gameplay.mp4
# -> output/video.mp4
```

Useful flags: `--voice en-US-AndrewNeural` (list voices: `edge-tts --list-voices`),
`--rate +18%`, `--whisper-model small`, `--music assets/bg.mp3`,
`--words-per-group 3`.

## Auto-upload to YouTube

See the header of `upload.py` for one-time Google Cloud OAuth setup, then:

```bash
python upload.py --file output/video.mp4 --title "AITA for..." \
    --tags reddit aita brainrot story --privacy public
```

**Honest limits:** the YouTube Data API is free but uploads cost 1600 quota
units against a 10,000/day default → ~6 uploads/day per project. No legitimate
tool gives truly *unlimited* free uploads (see the chat notes).

## Run on Google Colab (no local install)

Upload this folder to Colab, then in a cell:

```python
!apt -qq install ffmpeg
!pip -q install -r requirements.txt
!python generate.py --story stories/sample.txt --background assets/gameplay.mp4
```

Colab gives free GPU (Runtime → Change runtime type → T4) which speeds up Whisper.

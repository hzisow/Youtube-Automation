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

## Full automation (fetch → render → upload)

`auto.py` pulls fresh stories straight from Reddit's free public JSON (no API
key), renders them, and optionally uploads. Used posts are tracked in
`used.json` so stories never repeat.

```bash
# Make 3 videos from r/AmItheAsshole, review locally before posting:
python auto.py --count 3 --subreddit AmItheAsshole

# Make 2 and upload them as unlisted (safest while you dial in quality):
python auto.py --count 2 --upload --privacy unlisted
```

Other good subreddits: `tifu`, `AmItheAsshole`, `EntitledPeople`,
`MaliciousCompliance`, `pettyrevenge`.

## YouTube Shorts

The output already qualifies as a Short — YouTube auto-classifies any vertical
(or square) video ≤ 3 minutes as a Short, no special upload type required. Our
videos are 1080×1920 and stories are capped at ~1.5 min, so they always qualify.
`auto.py` also appends `#Shorts` to the title/description to help YouTube route
them into the Shorts feed. To stay safely under the limit on longer stories,
lower `--whisper-model` cost isn't the lever — instead reduce the source length
via `max_chars` in `pipeline/reddit.py` or raise `--rate` (e.g. `+25%`).

## Hands-off scheduling (free)

**Local cron** (simplest):
```cron
0 9 * * * cd /path/to/brainrot-pipeline && /usr/bin/python3 auto.py --count 2 --upload --privacy public
```

**GitHub Actions** (no machine running): `.github/workflows/daily-brainrot.yml`
runs daily in the cloud for free. Read the comments at the top of that file —
you commit a gameplay clip (or set a `GAMEPLAY_URL` secret), add your YouTube
credentials as `CLIENT_SECRET_JSON` / `TOKEN_JSON` secrets, and flip
`ENABLE_UPLOAD` to `true`. Without upload it still renders and saves the videos
as downloadable build artifacts.

## Run on Google Colab (no local install)

Upload this folder to Colab, then in a cell:

```python
!apt -qq install ffmpeg
!pip -q install -r requirements.txt
!python generate.py --story stories/sample.txt --background assets/gameplay.mp4
```

Colab gives free GPU (Runtime → Change runtime type → T4) which speeds up Whisper.

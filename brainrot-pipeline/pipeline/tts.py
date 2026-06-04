"""Free voiceover generation via Microsoft Edge TTS (no API key).

Edge TTS streams WordBoundary events alongside the audio, giving exact per-word
timings for free (no Whisper needed). synthesize() returns those timings.

Voice configuration:
  - TTS_VOICE   (env, single)    -> single voice for every video
  - TTS_VOICES  (env, comma-sep) -> rotate per story (parts 1/2 share one voice)
  - Neither set                  -> rotate over the curated default pool below
List voices: `python preview_voices.py --list`.
"""
import asyncio
import os
import random as _random

import edge_tts

# Single-voice override / default.
DEFAULT_VOICE = os.environ.get("TTS_VOICE", "en-US-AndrewNeural")

# Per-story rotation pool. Multilingual variants sound noticeably more natural
# than the originals; mix of US M/F.
_DEFAULT_POOL = [
    "en-US-AndrewMultilingualNeural",
    "en-US-BrianMultilingualNeural",
    "en-US-EmmaMultilingualNeural",
    "en-US-AvaMultilingualNeural",
    "en-US-ChristopherNeural",
    "en-US-RogerNeural",
]
_pool_env = os.environ.get("TTS_VOICES", "")
VOICE_POOL = [v.strip() for v in _pool_env.split(",") if v.strip()] or _DEFAULT_POOL


def pick_voice(seed=None):
    """Pick a voice from VOICE_POOL.

    With a `seed` (story id, etc.) the choice is deterministic so every part
    of a multi-part story shares one voice. Without a seed, picks randomly.
    """
    if not VOICE_POOL:
        return DEFAULT_VOICE
    if seed is None:
        return _random.choice(VOICE_POOL)
    return VOICE_POOL[hash(seed) % len(VOICE_POOL)]


async def _synth(text, out_path, voice, rate, pitch):
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    words = []
    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            ctype = chunk.get("type")
            if ctype == "audio":
                data = chunk.get("data")
                if data:
                    f.write(data)
            elif ctype == "WordBoundary" or ("offset" in chunk and "text" in chunk):
                token = (chunk.get("text") or "").strip()
                if not token:
                    continue
                start = chunk.get("offset", 0) / 1e7
                end = start + chunk.get("duration", 0) / 1e7
                pieces = token.split()
                if len(pieces) == 1:
                    words.append((token, start, end))
                else:
                    dt = (end - start) / len(pieces)
                    for k, piece in enumerate(pieces):
                        words.append((piece, start + k * dt, start + (k + 1) * dt))
    return words


def synthesize(text: str, out_path: str, voice: str = DEFAULT_VOICE,
               rate: str = "+18%", pitch: str = "+0Hz"):
    """Render `text` to an mp3 and return [(word, start, end), ...] timings."""
    return asyncio.run(_synth(text, out_path, voice, rate, pitch))

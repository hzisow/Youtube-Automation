"""TTS dispatcher. Routes to Microsoft Edge TTS (cloud, fast) or Piper TTS
(open-source, local CPU) based on the TTS_ENGINE env var.

Engine:
  TTS_ENGINE=edge   (default in code; workflow sets piper) - Edge TTS
  TTS_ENGINE=piper  - Piper TTS (open source, MIT licensed)

Edge voice config:
  TTS_VOICE   (env, single)    - single voice for every video
  TTS_VOICES  (env, comma-sep) - rotate per story

Piper voice config:
  PIPER_VOICE   (env, single)
  PIPER_VOICES  (env, comma-sep)

List Edge voices: `python preview_voices.py --list`.
Piper voices live in pipeline/piper_tts.py:_VOICE_HF_PATHS.

Both engines expose the same surface (DEFAULT_VOICE, VOICE_POOL,
pick_voice, synthesize), so auto.py doesn't care which is active.
"""
import asyncio
import os
import random as _random

import edge_tts

_ENGINE = os.environ.get("TTS_ENGINE", "edge").lower()

# === Edge TTS pool / defaults ===
_EDGE_DEFAULT_VOICE = os.environ.get("TTS_VOICE", "en-US-AndrewNeural")
_EDGE_DEFAULT_POOL = [
    "en-US-AndrewMultilingualNeural",
    "en-US-BrianMultilingualNeural",
    "en-US-EmmaMultilingualNeural",
    "en-US-AvaMultilingualNeural",
    "en-US-ChristopherNeural",
    "en-US-RogerNeural",
]
_edge_pool_env = os.environ.get("TTS_VOICES", "")
_EDGE_POOL = [v.strip() for v in _edge_pool_env.split(",") if v.strip()] or _EDGE_DEFAULT_POOL

# === Unified public interface (engine-dependent) ===
if _ENGINE == "piper":
    from . import piper_tts
    DEFAULT_VOICE = piper_tts.DEFAULT_VOICE
    VOICE_POOL = piper_tts.VOICE_POOL
else:
    DEFAULT_VOICE = _EDGE_DEFAULT_VOICE
    VOICE_POOL = _EDGE_POOL


def pick_voice(seed=None):
    """Pick a voice from the active engine's pool. Deterministic with `seed`."""
    if _ENGINE == "piper":
        from . import piper_tts
        return piper_tts.pick_voice(seed=seed)
    if not VOICE_POOL:
        return DEFAULT_VOICE
    if seed is None:
        return _random.choice(VOICE_POOL)
    return VOICE_POOL[hash(seed) % len(VOICE_POOL)]


def synthesize(text: str, out_path: str, voice: str = None,
               rate: str = "+18%", pitch: str = "+0Hz"):
    """Render text to mp3 and return [(word, start, end), ...] timings.

    Piper engine returns []; pipeline/captions falls back to Whisper.
    """
    voice = voice or DEFAULT_VOICE
    if _ENGINE == "piper":
        from . import piper_tts
        return piper_tts.synthesize(text, out_path, voice=voice)
    return asyncio.run(_synth(text, out_path, voice, rate, pitch))


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

"""Open-source TTS via Piper. MIT-licensed, ~60MB per voice, CPU-friendly.

Downloads voice .onnx + .onnx.json files from HuggingFace on first use
and caches them in ~/.cache/piper/. The workflow caches that dir across
runs so the download is a one-time ~200MB.

Piper doesn't emit per-word boundaries, so synthesize() returns an empty
word list. pipeline/captions.timings_ok([]) returns False, which triggers
the existing Whisper fallback in pipeline/captions.transcribe_words().
"""
import os
import subprocess
import urllib.request
import wave

import random as _random

# Where to keep downloaded voice files. Survives across workflow steps in the
# same run and (via actions/cache) across separate runs too.
PIPER_CACHE = os.environ.get(
    "PIPER_CACHE_DIR",
    os.path.expanduser("~/.cache/piper"),
)

# voice_id -> HuggingFace path component
_VOICE_HF_PATHS = {
    "en_US-ryan-high":     "en/en_US/ryan/high",
    "en_US-norman-medium": "en/en_US/norman/medium",
    "en_US-john-medium":   "en/en_US/john/medium",
    "en_US-amy-medium":    "en/en_US/amy/medium",
    "en_US-lessac-high":   "en/en_US/lessac/high",
    "en_US-libritts_r-medium": "en/en_US/libritts_r/medium",
    "en_GB-alan-medium":   "en/en_GB/alan/medium",
    "en_GB-northern_english_male-medium": "en/en_GB/northern_english_male/medium",
}

DEFAULT_VOICE = os.environ.get("PIPER_VOICE", "en_US-ryan-high")

# Per-story rotation pool. Mix of male / female / US / UK.
_DEFAULT_POOL = [
    "en_US-ryan-high",
    "en_US-norman-medium",
    "en_US-john-medium",
    "en_GB-alan-medium",
]
_pool_env = os.environ.get("PIPER_VOICES", "")
VOICE_POOL = [v.strip() for v in _pool_env.split(",") if v.strip()] or _DEFAULT_POOL


def pick_voice(seed=None):
    """Pick a voice from VOICE_POOL.

    With a `seed` (story id) the choice is deterministic so every part of
    a multi-part story shares one voice. Without a seed, picks randomly.
    """
    if not VOICE_POOL:
        return DEFAULT_VOICE
    if seed is None:
        return _random.choice(VOICE_POOL)
    return VOICE_POOL[hash(seed) % len(VOICE_POOL)]


def _ensure_voice(voice: str) -> str:
    """Download voice files if not cached. Returns path to .onnx."""
    os.makedirs(PIPER_CACHE, exist_ok=True)
    onnx_path = os.path.join(PIPER_CACHE, f"{voice}.onnx")
    json_path = onnx_path + ".json"
    if os.path.exists(onnx_path) and os.path.exists(json_path):
        return onnx_path
    if voice not in _VOICE_HF_PATHS:
        raise ValueError(
            f"Unknown Piper voice {voice!r}. Add it to _VOICE_HF_PATHS or pick "
            f"one of: {sorted(_VOICE_HF_PATHS)}"
        )
    base = (
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
        f"{_VOICE_HF_PATHS[voice]}/{voice}"
    )
    print(f"  piper: downloading {voice} from {base}.onnx")
    urllib.request.urlretrieve(f"{base}.onnx", onnx_path)
    urllib.request.urlretrieve(f"{base}.onnx.json", json_path)
    return onnx_path


def synthesize(text: str, out_path: str, voice: str = None, **_kwargs):
    """Render text to MP3 via Piper.

    Returns [] so the pipeline falls back to Whisper for per-word timings
    (Piper itself doesn't emit word boundaries).
    """
    voice = voice or DEFAULT_VOICE
    onnx_path = _ensure_voice(voice)

    # Use the Piper CLI -- it's stable across versions and handles its own
    # output WAV. Then transcode WAV -> MP3 to match the rest of the pipeline.
    wav_path = out_path + ".tmp.wav"
    cmd = [
        "piper",
        "--model", onnx_path,
        "--output_file", wav_path,
    ]
    proc = subprocess.run(
        cmd, input=text, capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0 or not os.path.exists(wav_path):
        # Fall back to Python API if CLI not on PATH for some reason.
        try:
            from piper import PiperVoice
            pv = PiperVoice.load(onnx_path)
            with wave.open(wav_path, "wb") as wav_file:
                pv.synthesize(text, wav_file)
        except Exception as e:
            raise RuntimeError(
                f"piper synthesis failed via CLI ({proc.returncode}) and "
                f"Python fallback: {type(e).__name__}: {e}\n"
                f"stderr: {proc.stderr[:400]}"
            ) from e

    # WAV -> MP3 so downstream ffmpeg muxing matches the Edge path.
    subprocess.run(
        ["ffmpeg", "-y", "-i", wav_path,
         "-c:a", "libmp3lame", "-b:a", "192k", out_path],
        check=True, capture_output=True,
    )
    try:
        os.remove(wav_path)
    except FileNotFoundError:
        pass

    # Empty list -> captions.timings_ok() returns False -> Whisper fallback fires.
    return []

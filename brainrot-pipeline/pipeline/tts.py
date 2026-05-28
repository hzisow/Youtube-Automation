"""Free voiceover generation via Microsoft Edge TTS (no API key).

Edge TTS streams WordBoundary events alongside the audio, giving exact per-word
timings for free (no Whisper needed). synthesize() returns those timings.
"""
import asyncio

import edge_tts

# Natural, brainrot-friendly default. List all voices with: edge-tts --list-voices
# Other good free picks: en-US-BrianNeural, en-US-GuyNeural, en-US-ChristopherNeural,
# en-US-EricNeural, en-US-AriaNeural (female), en-US-JennyNeural (female).
DEFAULT_VOICE = "en-US-AndrewNeural"


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
                # Some edge-tts builds emit phrase-level chunks. Split into
                # individual words with proportional timings so captions can
                # actually appear one at a time.
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

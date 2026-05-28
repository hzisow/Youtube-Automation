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
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7          # 100ns units -> seconds
                end = start + chunk["duration"] / 1e7
                words.append((chunk["text"], start, end))
    return words


def synthesize(text: str, out_path: str, voice: str = DEFAULT_VOICE,
               rate: str = "+18%", pitch: str = "+0Hz"):
    """Render `text` to an mp3 and return [(word, start, end), ...] timings."""
    return asyncio.run(_synth(text, out_path, voice, rate, pitch))

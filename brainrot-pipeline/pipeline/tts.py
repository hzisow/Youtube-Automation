"""Free voiceover generation via Microsoft Edge TTS (no API key)."""
import asyncio
import edge_tts

# Popular brainrot-friendly voices. List all with: edge-tts --list-voices
DEFAULT_VOICE = "en-US-AndrewNeural"


async def _synth(text: str, out_path: str, voice: str, rate: str, pitch: str) -> None:
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(out_path)


def synthesize(text: str, out_path: str, voice: str = DEFAULT_VOICE,
               rate: str = "+18%", pitch: str = "+0Hz") -> str:
    """Render `text` to an mp3 at `out_path`. rate like '+18%' speeds delivery."""
    asyncio.run(_synth(text, out_path, voice, rate, pitch))
    return out_path

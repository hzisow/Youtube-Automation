#!/usr/bin/env python3
"""Generate short MP3 samples of TTS voices so you can pick favorites.

Usage:
  python preview_voices.py                # default: 16 curated US/UK voices
  python preview_voices.py --voices en-US-AvaNeural en-GB-RyanNeural
  python preview_voices.py --text "Your custom line here"
  python preview_voices.py --list         # print every available voice and exit

Each voice produces one .mp3 in output/voice_previews/<voice>.mp3.
"""
import argparse
import asyncio
import os

import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "output", "voice_previews")

DEFAULT_VOICES = [
    "en-US-AndrewNeural",
    "en-US-AndrewMultilingualNeural",
    "en-US-BrianNeural",
    "en-US-BrianMultilingualNeural",
    "en-US-ChristopherNeural",
    "en-US-EricNeural",
    "en-US-GuyNeural",
    "en-US-RogerNeural",
    "en-US-AvaNeural",
    "en-US-AvaMultilingualNeural",
    "en-US-EmmaNeural",
    "en-US-EmmaMultilingualNeural",
    "en-US-JennyNeural",
    "en-US-AriaNeural",
    "en-GB-RyanNeural",
    "en-GB-SoniaNeural",
]

SAMPLE_TEXT = (
    "So my brother told me his crush dislikes him because of his height, "
    "but I actually know it's because he's mean. Am I the jerk for telling him?"
)


async def render(voice, text, out_path, rate="+28%"):
    com = edge_tts.Communicate(text, voice, rate=rate)
    with open(out_path, "wb") as f:
        async for chunk in com.stream():
            if chunk.get("type") == "audio":
                f.write(chunk.get("data") or b"")


async def list_all():
    voices = await edge_tts.list_voices()
    en = [v for v in voices if v["Locale"].startswith("en-")]
    en.sort(key=lambda v: v["ShortName"])
    for v in en:
        print(f"  {v['ShortName']:36s}  {v.get('Gender','?'):6s}  {v['Locale']}")


async def main_async(args):
    if args.list:
        await list_all()
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    voices = args.voices or DEFAULT_VOICES
    text = args.text or SAMPLE_TEXT
    print(f"Generating {len(voices)} previews into {OUT_DIR}/")
    for v in voices:
        out = os.path.join(OUT_DIR, f"{v}.mp3")
        try:
            await render(v, text, out, rate=args.rate)
            print(f"  ok  {v:36s} -> {os.path.basename(out)} "
                  f"({os.path.getsize(out)//1024} KB)")
        except Exception as e:
            print(f"  err {v:36s} -> {type(e).__name__}: {e}")
    print("\nListen, pick favorites, then either:")
    print("  - single voice for everything: set TTS_VOICE env var, or")
    print("  - rotation across stories:     set TTS_VOICES env var (comma-separated).")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--voices", nargs="+", default=None)
    p.add_argument("--text", default=None)
    p.add_argument("--rate", default="+28%")
    p.add_argument("--list", action="store_true")
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()

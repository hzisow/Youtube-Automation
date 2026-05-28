#!/usr/bin/env python3
"""Reddit-brainrot video generator: story.txt -> finished 1080x1920 mp4.

Example:
    python generate.py --story stories/sample.txt --background assets/gameplay.mp4
"""
import argparse
import os

from pipeline import tts, captions, video, titlecard, tone, sfx

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    p = argparse.ArgumentParser(description="Generate a Reddit-brainrot short.")
    p.add_argument("--story", required=True, help="Path to a .txt file with the narration.")
    p.add_argument("--background", required=True, help="Gameplay video to loop behind narration.")
    p.add_argument("--music", default=None, help="Optional background music file.")
    p.add_argument("--out", default=os.path.join(HERE, "output", "video.mp4"))
    p.add_argument("--voice", default=tts.DEFAULT_VOICE)
    p.add_argument("--rate", default="+18%", help="Speech rate, e.g. +18%% for faster delivery.")
    p.add_argument("--words-per-group", type=int, default=1,
                   help="Words shown at once (1 = MrBeast one-word style).")
    p.add_argument("--title", default=None, help="Title-card text (default: first sentence).")
    p.add_argument("--channel", default="Redditstories", help="Name shown on the title card.")
    p.add_argument("--color", default=None, help="Caption color name (yellow/red/green/...).")
    p.add_argument("--no-card", action="store_true", help="Disable the Reddit-style title card.")
    p.add_argument("--no-ding", action="store_true", help="Disable the intro ding.")
    args = p.parse_args()

    work = os.path.join(HERE, "output")
    os.makedirs(work, exist_ok=True)
    audio_path = os.path.join(work, "voice.mp3")
    ass_path = os.path.join(work, "captions.ass")
    card_path = os.path.join(work, "card.png")

    with open(args.story, encoding="utf-8") as f:
        text = f.read().strip()
    title = args.title or (text.split(".")[0].strip() + ".")
    color = tone.COLORS.get(args.color) if args.color else tone.color_for(None, title)
    ding = None if args.no_ding else sfx.ensure_ding(os.path.join(HERE, "assets", "ding.wav"))

    print("1/3 Generating voiceover + word timings (Edge-TTS)...")
    words = tts.synthesize(text, audio_path, voice=args.voice, rate=args.rate)
    if not captions.timings_ok(words):
        print("  edge-tts word timings unusable; falling back to Whisper...")
        words = captions.transcribe_words(audio_path)

    print(f"2/3 Writing captions ({len(words)} words)...")
    captions.write_ass(words, ass_path, group_size=args.words_per_group, color=color)

    card = card_end = None
    if not args.no_card:
        titlecard.render_card(title, card_path, username=args.channel)
        card, card_end = card_path, titlecard.title_end_time(words, title)

    print("3/3 Rendering final video (FFmpeg)...")
    video.render(args.background, audio_path, ass_path, args.out,
                 music=args.music, ding=ding, card=card, card_end=card_end or 0.0)

    print(f"\nDone -> {args.out}")


if __name__ == "__main__":
    main()

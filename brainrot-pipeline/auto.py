#!/usr/bin/env python3
"""End-to-end automation: fetch Reddit stories -> render videos -> (optionally) upload.

Tracks already-used post ids in used.json so you never repeat a story.

Examples:
  # Make 3 videos from r/AmItheAsshole, don't upload (review first):
  python auto.py --count 3 --subreddit AmItheAsshole

  # Make 2 and upload as unlisted for review:
  python auto.py --count 2 --upload --privacy unlisted
"""
import argparse
import json
import os
import re

from pipeline import reddit, tts, captions, video

HERE = os.path.dirname(os.path.abspath(__file__))
USED_DB = os.path.join(HERE, "used.json")
OUT_DIR = os.path.join(HERE, "output")


def _load_used():
    if os.path.exists(USED_DB):
        with open(USED_DB) as f:
            return set(json.load(f))
    return set()


def _save_used(used):
    with open(USED_DB, "w") as f:
        json.dump(sorted(used), f, indent=2)


def _slug(text, n=40):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:n] or "video"


def make_one(story, background, voice, rate, whisper_model, music):
    slug = _slug(story["title"])
    audio = os.path.join(OUT_DIR, f"{slug}.mp3")
    ass = os.path.join(OUT_DIR, f"{slug}.ass")
    out = os.path.join(OUT_DIR, f"{slug}.mp4")

    tts.synthesize(story["text"], audio, voice=voice, rate=rate)
    words = captions.transcribe_words(audio, model_size=whisper_model)
    captions.write_ass(words, ass)
    video.render(background, audio, ass, out, music=music)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int, default=3, help="How many videos to make.")
    p.add_argument("--subreddit", default="AmItheAsshole")
    p.add_argument("--listing", default="top", choices=["top", "hot", "new", "rising"])
    p.add_argument("--timeframe", default="week", choices=["day", "week", "month", "year", "all"])
    p.add_argument("--background", default=os.path.join(HERE, "assets", "gameplay.mp4"))
    p.add_argument("--music", default=None)
    p.add_argument("--voice", default=tts.DEFAULT_VOICE)
    p.add_argument("--rate", default="+18%")
    p.add_argument("--whisper-model", default="base")
    p.add_argument("--upload", action="store_true", help="Upload finished videos to YouTube.")
    p.add_argument("--privacy", default="unlisted", choices=["public", "unlisted", "private"])
    args = p.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    used = _load_used()
    pool = reddit.fetch_stories(args.subreddit, args.listing, args.timeframe, limit=50)
    fresh = [s for s in pool if s["id"] not in used]

    if not fresh:
        print("No fresh stories found (all already used). Try a different timeframe/subreddit.")
        return

    uploader = None
    if args.upload:
        import upload as uploader  # imported lazily so render-only runs need no Google libs

    made = 0
    for story in fresh:
        if made >= args.count:
            break
        print(f"\n=== [{made + 1}/{args.count}] {story['title'][:70]} ===")
        try:
            out = make_one(story, args.background, args.voice, args.rate,
                           args.whisper_model, args.music)
            print(f"Rendered -> {out}")
            if uploader:
                title = story["title"]
                if "#shorts" not in title.lower() and len(title) <= 90:
                    title = f"{title} #Shorts"
                desc = f"{story['body']}\n\n#Shorts #reddit #aita #story #brainrot"
                uploader.upload(out, title, desc,
                                ["shorts", "reddit", "aita", "story", "brainrot"],
                                privacy=args.privacy)
            used.add(story["id"])
            _save_used(used)
            made += 1
        except Exception as e:
            print(f"Skipping this story due to error: {type(e).__name__}: {e}")

    print(f"\nFinished. {made} video(s) in {OUT_DIR}")


if __name__ == "__main__":
    main()

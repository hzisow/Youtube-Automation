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
import random
import re

from pipeline import reddit, tts, captions, video, titlecard, tone, split, sfx

HERE = os.path.dirname(os.path.abspath(__file__))
USED_DB = os.path.join(HERE, "used.json")
OUT_DIR = os.path.join(HERE, "output")

# Good story-driven subreddits for narrated shorts.
DEFAULT_SUBREDDITS = [
    "AmItheAsshole", "tifu", "MaliciousCompliance",
    "pettyrevenge", "ProRevenge", "EntitledParents", "confession",
]


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


def _make_video(text, card_title, time_title, slug, color, opts):
    audio = os.path.join(OUT_DIR, f"{slug}.mp3")
    ass = os.path.join(OUT_DIR, f"{slug}.ass")
    card = os.path.join(OUT_DIR, f"{slug}.png")
    out = os.path.join(OUT_DIR, f"{slug}.mp4")

    words = tts.synthesize(text, audio, voice=opts["voice"], rate=opts["rate"])
    captions.write_ass(words, ass, color=color)
    titlecard.render_card(card_title, card, username=opts["channel"])
    if time_title:
        card_end = titlecard.title_end_time(words, time_title)
    else:
        card_end = min(2.5, video._duration(audio))
    video.render(opts["background"], audio, ass, out, music=opts["music"],
                 ding=opts["ding"], card=card, card_end=card_end)
    return out


def make_one(story, opts):
    """Render a story; returns one or more output paths (Part 1/2/... if long)."""
    color = tone.color_for(story.get("subreddit"), story["title"])
    parts = split.split_text(story["body"], threshold_seconds=opts["max_seconds"])
    multi = len(parts) > 1
    base = _slug(story["title"])
    outs = []
    for i, part in enumerate(parts, 1):
        if multi:
            card_title = f"{story['title']} (Part {i})"
            slug = f"{base}-p{i}"
            text = f"{story['title']}. {part}" if i == 1 else f"Part {i}. {part}"
            time_title = story["title"] if i == 1 else None
        else:
            card_title, slug, text, time_title = story["title"], base, story["text"], story["title"]
        outs.append(_make_video(text, card_title, time_title, slug, color, opts))
    return outs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int, default=3, help="How many videos to make.")
    p.add_argument("--subreddit", nargs="+", default=DEFAULT_SUBREDDITS,
                   help="One or more subreddits to pull from.")
    p.add_argument("--listing", default="top", choices=["top", "hot", "new", "rising"])
    p.add_argument("--timeframe", default="week", choices=["day", "week", "month", "year", "all"])
    p.add_argument("--background", default=os.path.join(HERE, "assets", "gameplay.mp4"))
    p.add_argument("--voice", default=tts.DEFAULT_VOICE)
    p.add_argument("--rate", default="+18%")
    p.add_argument("--channel", default="Redditstories", help="Name shown on the title card.")
    p.add_argument("--max-seconds", type=int, default=70,
                   help="Only split into Part 1/Part 2/... if narration exceeds this (default 70s = 1:10).")
    p.add_argument("--no-ding", action="store_true", help="Disable the intro ding.")
    p.add_argument("--music", dest="music", default=None,
                   help="Optional background music file (off by default).")
    p.add_argument("--upload", action="store_true", help="Upload finished videos to YouTube.")
    p.add_argument("--privacy", default="unlisted", choices=["public", "unlisted", "private"])
    p.add_argument("--tiktok", action="store_true", help="Also upload to TikTok.")
    p.add_argument("--tiktok-mode", default="inbox", choices=["inbox", "direct"],
                   help="inbox = TikTok drafts (un-audited apps); direct = publish.")
    args = p.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    used = _load_used()

    pool = []
    seen_ids = set()
    for sub in args.subreddit:
        try:
            for s in reddit.fetch_stories(sub, args.listing, args.timeframe, limit=50):
                if s["id"] not in seen_ids:
                    seen_ids.add(s["id"])
                    pool.append(s)
        except Exception as e:
            print(f"Could not fetch r/{sub}: {type(e).__name__}: {e}")
    random.shuffle(pool)
    fresh = [s for s in pool if s["id"] not in used]

    if not fresh:
        print("No fresh stories found (all already used). Try a different timeframe/subreddit.")
        return

    uploader = None
    if args.upload:
        import upload as uploader  # imported lazily so render-only runs need no Google libs
    tiktok = None
    if args.tiktok:
        import tiktok_upload as tiktok  # lazy import so non-TikTok runs need no deps

    # Background music is off by default; opt in with --music path/to/track.mp3.
    music = args.music
    ding = None if args.no_ding else sfx.ensure_ding(os.path.join(HERE, "assets", "ding.wav"))

    opts = {
        "background": args.background, "voice": args.voice, "rate": args.rate,
        "channel": args.channel, "music": music, "ding": ding,
        "max_seconds": args.max_seconds,
    }

    made = 0
    for story in fresh:
        if made >= args.count:
            break
        print(f"\n=== [{made + 1}/{args.count}] {story['title'][:70]} ===")
        try:
            outs = make_one(story, opts)
            for n, out in enumerate(outs, 1):
                print(f"Rendered -> {out}")
                if uploader:
                    suffix = f" (Part {n})" if len(outs) > 1 else ""
                    title = f"{story['title']}{suffix}"
                    if "#shorts" not in title.lower() and len(title) <= 88:
                        title = f"{title} #Shorts"
                    desc = f"{story['body']}\n\n#Shorts #reddit #story #storytime #brainrot"
                    uploader.upload(out, title, desc,
                                    ["shorts", "reddit", "story", "storytime", "brainrot"],
                                    privacy=args.privacy)
                if tiktok:
                    suffix = f" (Part {n})" if len(outs) > 1 else ""
                    tt_title = f"{story['title']}{suffix} #fyp #reddit #story"
                    tiktok.upload(out, tt_title[:150], mode=args.tiktok_mode)
            used.add(story["id"])
            _save_used(used)
            made += 1
        except Exception as e:
            print(f"Skipping this story due to error: {type(e).__name__}: {e}")

    print(f"\nFinished. {made} story(ies) in {OUT_DIR}")


if __name__ == "__main__":
    main()

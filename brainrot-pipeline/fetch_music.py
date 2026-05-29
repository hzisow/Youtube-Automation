#!/usr/bin/env python3
"""Bulk-download royalty-free background tracks from Pixabay into the
mood-tagged music library at assets/music/<mood>/.

Pixabay's Music API is free and only needs a key. Get one at:
  https://pixabay.com/api/docs/  (sign up -> account page shows your key)

Usage:
  export PIXABAY_KEY=...your key...
  python fetch_music.py                # fetch ~5 tracks per mood
  python fetch_music.py --per-mood 10  # more tracks per mood
  python fetch_music.py --mood chill   # only one mood
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = os.path.join(HERE, "assets", "music")

# Pixabay search terms tuned per mood folder.
MOOD_QUERIES = {
    "chill":    ["lofi", "ambient", "calm piano", "soft beats"],
    "sad":      ["sad piano", "emotional", "melancholy"],
    "funny":    ["quirky", "comedy", "playful", "bouncy"],
    "dramatic": ["epic cinematic", "tension", "suspense"],
    "hype":     ["upbeat", "energetic", "trap beat", "hip hop"],
    "mystery":  ["dark ambient", "eerie", "mysterious"],
}


def search(query: str, key: str, per_page: int = 5) -> list[dict]:
    params = urllib.parse.urlencode({
        "key": key,
        "q": query,
        "per_page": per_page,
        "safesearch": "true",
    })
    url = f"https://pixabay.com/api/music/?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "brainrot-pipeline/1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r).get("hits", [])


def download(url: str, dest: str) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "brainrot-pipeline/1"})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(64 * 1024)
            if not chunk:
                break
            f.write(chunk)


def fetch_mood(mood: str, key: str, per_mood: int) -> int:
    out_dir = os.path.join(MUSIC_DIR, mood)
    os.makedirs(out_dir, exist_ok=True)
    have = {f for f in os.listdir(out_dir) if f.lower().endswith((".mp3", ".m4a"))}
    saved = 0
    for q in MOOD_QUERIES.get(mood, [mood]):
        if saved >= per_mood:
            break
        try:
            hits = search(q, key, per_page=min(8, per_mood - saved + 2))
        except Exception as e:
            print(f"  {mood}/{q!r}: search failed: {type(e).__name__}: {e}")
            continue
        for hit in hits:
            if saved >= per_mood:
                break
            audio = hit.get("audio") or hit.get("audio_url") or hit.get("preview")
            if not audio:
                continue
            ext = ".mp3" if ".mp3" in audio else ".m4a"
            name = f"pixabay-{hit.get('id', saved)}{ext}"
            if name in have:
                continue
            dest = os.path.join(out_dir, name)
            try:
                download(audio, dest)
                have.add(name)
                saved += 1
                print(f"  {mood}: {name} ({os.path.getsize(dest)//1024} KB)")
            except Exception as e:
                print(f"  {mood}: failed {name}: {type(e).__name__}: {e}")
    return saved


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--per-mood", type=int, default=5)
    p.add_argument("--mood", choices=list(MOOD_QUERIES), default=None,
                   help="Only fetch this one mood (default: all).")
    p.add_argument("--key", default=os.environ.get("PIXABAY_KEY"),
                   help="Pixabay API key (or PIXABAY_KEY env var).")
    args = p.parse_args()

    if not args.key:
        print("ERROR: set PIXABAY_KEY or pass --key. Get one free at "
              "https://pixabay.com/api/docs/", file=sys.stderr)
        sys.exit(1)

    moods = [args.mood] if args.mood else list(MOOD_QUERIES)
    total = 0
    for m in moods:
        print(f"\n=== {m} ===")
        total += fetch_mood(m, args.key, args.per_mood)
    print(f"\nDone. {total} new tracks saved under {MUSIC_DIR}.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Refresh stories_cache.json with months worth of stories (run locally).

This deep-scrapes the configured subreddits across multiple timeframes (week,
month, year, all) and paginates each, so a single run typically caches enough
content for 6+ months of daily uploads. The cloud workflow then reads the
cache and never has to hit Reddit itself.

After running, commit and push:
    git add stories_cache.json
    git commit -m "chore: refresh stories"
    git push
"""
import argparse
import os
import time

from pipeline import reddit
from auto import DEFAULT_SUBREDDITS

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "stories_cache.json")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--subreddit", nargs="+", default=DEFAULT_SUBREDDITS)
    p.add_argument("--listing", default="top",
                   choices=["top", "hot", "new", "rising"])
    p.add_argument("--timeframes", nargs="+",
                   default=["week", "month", "year", "all"],
                   help="Reddit timeframes to scrape across.")
    p.add_argument("--pages", type=int, default=3,
                   help="Pages per (subreddit, timeframe). Each page = 100 posts.")
    p.add_argument("--sleep", type=float, default=3.0,
                   help="Seconds to wait between (subreddit, timeframe) pulls.")
    args = p.parse_args()

    existing = reddit.load_cache(CACHE)
    by_id = {s["id"]: s for s in existing}
    starting = len(by_id)

    for sub in args.subreddit:
        for tf in args.timeframes:
            try:
                got = reddit.fetch_stories(sub, args.listing, tf,
                                           limit=100, max_pages=args.pages)
                new = sum(1 for s in got if s["id"] not in by_id)
                for s in got:
                    by_id[s["id"]] = s
                print(f"  r/{sub:25s} t={tf:5s} -> +{new:3d} new "
                      f"(cache: {len(by_id)})")
            except Exception as e:
                print(f"  r/{sub} t={tf}: {type(e).__name__}: {e}")
            time.sleep(args.sleep)

    reddit.save_cache(CACHE, list(by_id.values()))
    added = len(by_id) - starting
    print(f"\nDone. Cache has {len(by_id)} stories (+{added} new) at {CACHE}")
    print("Roughly enough for ~{:d} months at 5 videos/day.".format(len(by_id) // 150))
    print("\nNext: git add stories_cache.json && git commit -m \"chore: refresh stories\" && git push")


if __name__ == "__main__":
    main()

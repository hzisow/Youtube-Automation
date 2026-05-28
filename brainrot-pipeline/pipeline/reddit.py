"""Fetch story posts from Reddit's free public JSON endpoints (no API key needed).

Reddit exposes any listing as JSON by appending .json. We request a custom
User-Agent to avoid throttling. This is the free, no-auth path; for heavy use
switch to PRAW with a free script-app client id/secret.
"""
import html
import json
import re
import urllib.request

UA = "brainrot-pipeline/1.0 (personal use)"

# Acronyms TTS mispronounces -> spoken form.
_EXPAND = {
    r"\bAITA\b": "Am I the jerk",
    r"\bWIBTA\b": "Would I be the jerk",
    r"\bAITAH\b": "Am I the jerk",
    r"\bTIFU\b": "Today I messed up",
    r"\bNTA\b": "not the jerk",
    r"\bYTA\b": "you're the jerk",
    r"\bAH\b": "jerk",
    r"\bIMO\b": "in my opinion",
    r"\bTL;DR\b": "",
    r"\bTLDR\b": "",
    r"\bedit:\b": "",
}


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"https?://\S+", "", text)        # strip links
    text = re.sub(r"[*_>#`~]", "", text)              # strip markdown
    for pat, repl in _EXPAND.items():
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_stories(subreddit: str = "AmItheAsshole", listing: str = "top",
                  timeframe: str = "week", limit: int = 25,
                  min_chars: int = 400, max_chars: int = 1400):
    """Return list of {id, title, body, text} dicts suitable for narration."""
    url = (f"https://www.reddit.com/r/{subreddit}/{listing}.json"
           f"?t={timeframe}&limit={limit}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)

    stories = []
    for child in data["data"]["children"]:
        p = child["data"]
        if p.get("stickied") or p.get("over_18"):
            continue
        body = clean_text(p.get("selftext", ""))
        if not (min_chars <= len(body) <= max_chars):
            continue
        title = clean_text(p.get("title", ""))
        stories.append({
            "id": p["id"],
            "title": title,
            "body": body,
            "text": f"{title}. {body}",
        })
    return stories

"""Fetch story posts from Reddit.

Uses Reddit's public JSON endpoints anonymously when possible. From cloud IPs
(e.g. GitHub Actions runners), Reddit's WAF often returns 403 for anonymous
traffic, so if the REDDIT_CLIENT_ID env var is set we fall back to authenticated
access via Reddit's free "installed_client" OAuth grant (no user account, no
secret needed). Create an app at https://www.reddit.com/prefs/apps -> "installed
app" -> copy the client ID and expose it as REDDIT_CLIENT_ID.
"""
import base64
import html
import json
import os
import re
import urllib.parse
import urllib.request

# Reddit recommends a descriptive UA in their guidelines.
UA = "linux:brainrot-pipeline:v1 (by /u/personal-use)"
_TOKEN_CACHE = {"token": None}

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


def _oauth_token(client_id: str) -> str:
    if _TOKEN_CACHE["token"]:
        return _TOKEN_CACHE["token"]
    auth = base64.b64encode(f"{client_id}:".encode()).decode()
    body = urllib.parse.urlencode({
        "grant_type": "https://oauth.reddit.com/grants/installed_client",
        "device_id": "brainrot-pipeline-001",
    }).encode()
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=body,
        headers={"Authorization": f"Basic {auth}", "User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        token = json.load(r)["access_token"]
    _TOKEN_CACHE["token"] = token
    return token


def load_cache(path: str) -> list:
    """Read a previously-saved stories_cache.json (or return [])."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_cache(path: str, stories: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stories, f, indent=2)


def fetch_stories(subreddit: str = "AmItheAsshole", listing: str = "top",
                  timeframe: str = "week", limit: int = 25,
                  min_chars: int = 400, max_chars: int = 5000,
                  max_pages: int = 1):
    """Return list of {id, subreddit, title, body, text} dicts for narration.

    Paginates through Reddit's listing up to `max_pages` (100 posts each) so
    a single call can pull hundreds of stories.
    """
    headers = {"User-Agent": UA}
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    if client_id:
        headers["Authorization"] = f"bearer {_oauth_token(client_id)}"
        host = "https://oauth.reddit.com"
    else:
        host = "https://www.reddit.com"

    stories = []
    after = None
    for _ in range(max_pages):
        params = {"t": timeframe, "limit": str(min(limit, 100)), "raw_json": "1"}
        if after:
            params["after"] = after
        url = f"{host}/r/{subreddit}/{listing}.json?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        children = data["data"]["children"]
        if not children:
            break
        for child in children:
            p = child["data"]
            if p.get("stickied") or p.get("over_18"):
                continue
            body = clean_text(p.get("selftext", ""))
            if not (min_chars <= len(body) <= max_chars):
                continue
            title = clean_text(p.get("title", ""))
            stories.append({
                "id": p["id"],
                "subreddit": p.get("subreddit", subreddit),
                "title": title,
                "body": body,
                "text": f"{title}. {body}",
            })
        after = data["data"].get("after")
        if not after:
            break
    return stories

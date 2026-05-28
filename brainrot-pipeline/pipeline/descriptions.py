"""Auto-generate platform-appropriate titles, descriptions, and tags."""
from typing import Optional

# Generic story-content tags every video gets.
_BASE = ["shorts", "reddit", "story", "storytime", "brainrot", "askreddit"]

# Per-subreddit hashtags layered on top.
_SUB_TAGS = {
    "amitheasshole": ["aita", "amitheasshole", "drama"],
    "aitah": ["aitah", "aita", "drama"],
    "tifu": ["tifu", "fail", "awkward"],
    "maliciouscompliance": ["maliciouscompliance", "karma", "petty"],
    "pettyrevenge": ["pettyrevenge", "karma", "revenge"],
    "prorevenge": ["prorevenge", "karma", "revenge"],
    "entitledparents": ["entitledparents", "karen", "drama"],
    "confession": ["confession", "secret"],
    "trueoffmychest": ["trueoffmychest", "confession"],
    "nosleep": ["nosleep", "scary", "horror"],
    "relationship_advice": ["relationships", "advice", "drama"],
}


def _tags_for(subreddit: Optional[str]) -> list[str]:
    extra = _SUB_TAGS.get((subreddit or "").lower().lstrip("r/"), [])
    seen, out = set(), []
    for t in _BASE + extra + ["fyp", "viral"]:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _part_suffix(part: int, total: int) -> str:
    return f" (Part {part})" if total > 1 else ""


def youtube(story: dict, part: int = 1, total_parts: int = 1):
    """Return (title, description, tags) tuned for YouTube Shorts."""
    suffix = _part_suffix(part, total_parts)
    base_title = f"{story['title']}{suffix}"
    title = base_title if len(base_title) > 88 else f"{base_title} #Shorts"
    title = title[:100]

    sub = story.get("subreddit", "")
    credit = f"Story from r/{sub} - credit to the original poster.\n\n" if sub else ""
    next_part = ("\nSubscribe so you don't miss Part %d!\n" % (part + 1)) if part < total_parts else ""
    tags = _tags_for(sub)
    hashtags = " ".join("#" + t for t in tags[:12])
    desc = f"{credit}{story['body']}\n{next_part}\n{hashtags}".strip()[:4500]
    return title, desc, tags


def tiktok(story: dict, part: int = 1, total_parts: int = 1) -> str:
    """Return a single TikTok caption (title field). Capped to ~140 chars."""
    suffix = _part_suffix(part, total_parts)
    sub = story.get("subreddit", "")
    tags = _tags_for(sub)
    base = f"{story['title']}{suffix}"
    hashtags = " " + " ".join("#" + t for t in tags[:6])
    room = 140 - len(hashtags)
    if len(base) > room:
        base = base[:max(0, room - 1)].rstrip() + "..."
    return (base + hashtags).strip()

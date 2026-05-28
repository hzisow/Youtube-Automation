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


# Hashtags that must appear on every TikTok caption no matter what.
TIKTOK_REQUIRED = ["fyp", "viral", "trending"]


def tiktok(story: dict, part: int = 1, total_parts: int = 1,
           limit: int = 140) -> str:
    """Return a single TikTok caption. Always includes the required hashtags;
    fills remaining room with subreddit/content hashtags."""
    suffix = _part_suffix(part, total_parts)
    sub = story.get("subreddit", "")
    required_str = " " + " ".join("#" + t for t in TIKTOK_REQUIRED)
    optional = [t for t in _tags_for(sub) if t not in TIKTOK_REQUIRED]

    base = f"{story['title']}{suffix}"
    head_budget = limit - len(required_str)
    if len(base) > head_budget:
        base = base[:max(0, head_budget - 3)].rstrip() + "..."
        return (base + required_str).strip()

    cap = base
    for t in optional:
        candidate = f"{cap} #{t}"
        if len(candidate) + len(required_str) <= limit:
            cap = candidate
        else:
            break
    return (cap + required_str).strip()

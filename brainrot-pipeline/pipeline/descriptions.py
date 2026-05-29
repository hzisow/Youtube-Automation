"""Auto-generate platform-appropriate titles, descriptions, and tags.

Titles are cleaned for display (Reddit acronyms restored, common prefixes
trimmed, smart word-boundary truncation) so YouTube and TikTok don't show
ugly mid-word cutoffs like "...because he's an asshole, not becau".
"""
import re
from typing import Optional

from . import facts

# Reverse the TTS-expansion the cache stores (e.g. 'Am I the jerk' -> 'AITA')
# so display titles read like the original Reddit post.
_DISPLAY_REPLACEMENTS = [
    (re.compile(r"\bAm I the jerk\b", re.IGNORECASE),    "AITA"),
    (re.compile(r"\bWould I be the jerk\b", re.IGNORECASE), "WIBTA"),
    (re.compile(r"\bToday I messed up\b", re.IGNORECASE), "TIFU"),
    (re.compile(r"\bnot the jerk\b", re.IGNORECASE),     "NTA"),
    (re.compile(r"\byou'?re the jerk\b", re.IGNORECASE), "YTA"),
]

# Strip generic openers so the title leads with the actual content.
_OPENER_RE = re.compile(
    r"^(AITA|AITAH|WIBTA|TIFU|MC|ELI5|TIL)[\s:,.\-]*(for|by|that|because|when)?\s+",
    re.IGNORECASE,
)

_BASE = ["shorts", "reddit", "story", "storytime", "brainrot"]
_EXPLAINER_BASE = ["shorts", "didyouknow", "facts", "interesting", "learn",
                    "education", "trivia"]

_SUB_TAGS = {
    "amitheasshole":   ["aita", "amitheasshole", "drama"],
    "aitah":           ["aitah", "aita", "drama"],
    "tifu":            ["tifu", "fail", "awkward"],
    "maliciouscompliance": ["maliciouscompliance", "karma", "petty"],
    "pettyrevenge":    ["pettyrevenge", "karma", "revenge"],
    "prorevenge":      ["prorevenge", "karma", "revenge"],
    "entitledparents": ["entitledparents", "karen", "drama"],
    "confession":      ["confession", "secret"],
    "trueoffmychest":  ["trueoffmychest", "confession"],
    "nosleep":         ["nosleep", "scary", "horror"],
    "relationship_advice": ["relationships", "advice", "drama"],
    "todayilearned":   ["til", "todayilearned", "facts", "didyouknow"],
    "interestingasfuck": ["interesting", "facts", "didyouknow"],
    "damnthatsinteresting": ["interesting", "facts", "didyouknow"],
    "showerthoughts":  ["showerthoughts", "deep", "thinking"],
}


def display_title(title: str) -> str:
    """A short, human-friendly title for YouTube/TikTok display."""
    t = title or ""
    for pat, repl in _DISPLAY_REPLACEMENTS:
        t = pat.sub(repl, t)
    # Drop noisy bracket tags like "[Update]" / "[Long]".
    t = re.sub(r"\s*\[[^\]]+\]\s*", " ", t).strip()
    return re.sub(r"\s+", " ", t).strip()


def _hook(title: str, max_len: int = 70) -> str:
    """Build a punchy display title under `max_len` chars, word-boundary clean."""
    t = display_title(title)
    # Strip leading "AITA for", "TIFU by", "TIL that" -- the acronym alone hits
    # harder as a tag than as a sentence opener.
    t = _OPENER_RE.sub("", t).strip()
    if not t:
        t = display_title(title)
    # The strip leaves us mid-sentence; capitalize so the hook reads cleanly.
    if t:
        t = t[0].upper() + t[1:]
    if len(t) > max_len:
        cut = t[:max_len].rsplit(" ", 1)[0].rstrip(",;:.- ")
        t = cut + "..."
    return t


def _tags_for(subreddit: Optional[str], style: str = "story") -> list[str]:
    base = _EXPLAINER_BASE if style == "explainer" else _BASE
    extra = _SUB_TAGS.get((subreddit or "").lower().lstrip("r/"), [])
    seen, out = set(), []
    for t in base + extra + ["fyp", "viral"]:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _part_suffix(part: int, total: int) -> str:
    return f" (Part {part})" if total > 1 else ""


def youtube(story: dict, part: int = 1, total_parts: int = 1,
            style: str = "story"):
    """Return (title, description, tags) tuned for YouTube Shorts."""
    suffix = _part_suffix(part, total_parts)
    if style == "explainer":
        hook = facts.display_title(story["title"])
        hook = hook if len(hook) <= 75 else hook[:75].rsplit(" ", 1)[0] + "...?"
    else:
        hook = _hook(story["title"])
    base_title = f"{hook}{suffix}"
    # YouTube hard-cap is 100 chars; #Shorts tag is mandatory for Shorts pickup.
    title = base_title if len(base_title) > 88 else f"{base_title} #Shorts"
    title = title[:100].rstrip()

    sub = story.get("subreddit", "")
    tags = _tags_for(sub, style)
    hashtags = " ".join("#" + t for t in tags[:8])

    parts = []
    if style == "explainer":
        parts.append(facts.display_title(story["title"]))
        if story.get("body"):
            body_lead = story["body"].split(". ")[0]
            parts.append(body_lead[:200].rstrip(",.") + ".")
    else:
        if sub:
            parts.append(f"Story from r/{sub}")
        if part < total_parts:
            parts.append(f"Part {part + 1} coming next — subscribe!")
    parts.append(hashtags)
    desc = "\n\n".join(parts)[:4500]
    return title, desc, tags


# Hashtags that must appear on every TikTok caption no matter what.
TIKTOK_REQUIRED = ["fyp", "viral", "trending"]


def tiktok(story: dict, part: int = 1, total_parts: int = 1,
           limit: int = 140, style: str = "story") -> str:
    """One-line TikTok caption with required hashtags always present."""
    suffix = _part_suffix(part, total_parts)
    sub = story.get("subreddit", "")
    required_str = " " + " ".join("#" + t for t in TIKTOK_REQUIRED)
    optional = [t for t in _tags_for(sub, style) if t not in TIKTOK_REQUIRED]

    if style == "explainer":
        hook = facts.display_title(story["title"])
    else:
        hook = _hook(story["title"], max_len=80)
    base = f"{hook}{suffix}"
    head_budget = limit - len(required_str)
    if len(base) > head_budget:
        cut = base[:max(0, head_budget - 3)].rsplit(" ", 1)[0].rstrip(",;:.- ")
        return (cut + "..." + required_str).strip()

    cap = base
    for t in optional:
        candidate = f"{cap} #{t}"
        if len(candidate) + len(required_str) <= limit:
            cap = candidate
        else:
            break
    return (cap + required_str).strip()

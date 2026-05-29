"""Turn a TIL / interesting-fact post into 'Did you know...' style narration.

Used by the explainer pipeline so the voice-over matches the B-roll topic
instead of telling a personal Reddit story.
"""
import re

_PREFIX_RE = re.compile(
    r"^(til|today i learned|did you know|fun fact|interesting fact|"
    r"fact|wow|woah|whoa|imagine|just learned)\b[\s,:.\-]*(that\s+)?",
    re.IGNORECASE,
)
_TRAILING_RE = re.compile(r"[.!?]+\s*$")


def rephrase(title: str) -> str:
    """Strip TIL-style prefixes from a title and return a clean fact statement."""
    t = _PREFIX_RE.sub("", title or "").strip()
    if not t:
        return ""
    t = t[0].upper() + t[1:]
    return _TRAILING_RE.sub("", t).strip()


def to_narration(title: str, body: str = "") -> str:
    """Build the TTS script: 'Did you know that ...? <body>'."""
    fact = rephrase(title)
    if not fact:
        return body or title
    lead = fact[0].lower() + fact[1:]
    script = f"Did you know that {lead}?"
    if body:
        script += " " + body.strip()
    return script


def display_title(title: str) -> str:
    """A clean version of the title for YouTube/TikTok metadata."""
    fact = rephrase(title)
    return f"Did you know {fact[0].lower() + fact[1:]}?" if fact else title


FACT_SUBREDDITS = [
    "todayilearned",
    "interestingasfuck",
    "Damnthatsinteresting",
    "WTF_Wikipedia",
    "Showerthoughts",
]

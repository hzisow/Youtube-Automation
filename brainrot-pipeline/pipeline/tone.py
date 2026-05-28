"""Pick a caption highlight color that matches the tone of a story.

Colors are ASS format &HAABBGGRR (alpha=00 fully opaque). Heuristic: map the
subreddit first, then scan the title for emotional keywords as a fallback.
"""

# name -> ASS color
COLORS = {
    "yellow": "&H0000FFFF",
    "red": "&H000000FF",
    "orange": "&H0000A5FF",
    "green": "&H0000FF66",
    "cyan": "&H00FFFF00",
    "purple": "&H00FF20A0",
    "white": "&H00FFFFFF",
}

_SUBREDDIT_TONE = {
    "prorevenge": "red",
    "pettyrevenge": "orange",
    "maliciouscompliance": "orange",
    "nosleep": "red",
    "letsnotmeet": "red",
    "amitheasshole": "yellow",
    "aitah": "yellow",
    "tifu": "cyan",
    "confession": "purple",
    "trueoffmychest": "purple",
    "entitledparents": "orange",
    "relationship_advice": "cyan",
}

_KEYWORDS = {
    "red": ["revenge", "scary", "creepy", "horror", "stalk", "threat", "kill", "died", "death"],
    "green": ["wholesome", "happy", "love", "grateful", "kind", "saved"],
    "orange": ["cheat", "betray", "lie", "caught", "fired", "karma"],
    "purple": ["secret", "confess", "ashamed", "guilt"],
}


def color_for(subreddit: str | None, title: str = "") -> str:
    """Return an ASS color string for the given subreddit/title tone."""
    if subreddit:
        tone = _SUBREDDIT_TONE.get(subreddit.lower().lstrip("r/"))
        if tone:
            return COLORS[tone]
    low = title.lower()
    for tone, words in _KEYWORDS.items():
        if any(w in low for w in words):
            return COLORS[tone]
    return COLORS["yellow"]

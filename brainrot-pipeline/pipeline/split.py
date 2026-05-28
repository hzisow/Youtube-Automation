"""Split a long story into multiple parts so it can become Part 1 / Part 2 / ...

Splits on sentence boundaries, packing sentences into chunks up to a character
budget that roughly maps to a target spoken duration.
"""
import re

# ~16 chars/sec of speech at the default rate -> char budget for a target length.
CHARS_PER_SECOND = 16


def split_text(body: str, max_seconds: int = 55) -> list[str]:
    """Return a list of body chunks. One chunk if it already fits."""
    budget = max_seconds * CHARS_PER_SECOND
    if len(body) <= budget:
        return [body.strip()]
    sentences = re.findall(r"[^.!?]+[.!?]?", body)
    parts, cur = [], ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if cur and len(cur) + 1 + len(s) > budget:
            parts.append(cur.strip())
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        parts.append(cur.strip())
    return parts

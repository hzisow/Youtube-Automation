"""Split a long story into parts only when it would run long.

A story is split only if its estimated narration exceeds `threshold_seconds`
(default 70s = 1:10). Parts are roughly equal, split on sentence boundaries, and
each part after the first begins with an ~8s recap overlap from the prior part.
"""
import math
import re

# ~16 chars/sec of speech at the default rate.
CHARS_PER_SECOND = 16


def split_text(body: str, threshold_seconds: int = 70,
               overlap_seconds: int = 8, max_parts: int = 3) -> list[str]:
    """Return body chunks. One chunk unless narration exceeds threshold_seconds.

    Caps at `max_parts` (default 3) so a single huge story can't fragment into
    a runaway number of videos; anything past that is trimmed.
    """
    body = body.strip()
    est = len(body) / CHARS_PER_SECOND
    if est <= threshold_seconds:
        return [body]

    num = min(max_parts, math.ceil(est / threshold_seconds))
    # If we capped, also trim the body so part lengths stay reasonable.
    cap_chars = num * threshold_seconds * CHARS_PER_SECOND
    if len(body) > cap_chars:
        body = body[:cap_chars].rsplit(" ", 1)[0]
    budget = len(body) / num
    sentences = re.findall(r"[^.!?]+[.!?]?", body)

    chunks, cur = [], ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if cur and len(cur) + 1 + len(s) > budget and len(chunks) < num - 1:
            chunks.append(cur.strip())
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        chunks.append(cur.strip())
    if len(chunks) == 1:
        return chunks

    # Recap overlap: each later part begins with the tail of the previous one.
    overlap_chars = int(overlap_seconds * CHARS_PER_SECOND)
    out = [chunks[0]]
    for i in range(1, len(chunks)):
        tail = chunks[i - 1][-overlap_chars:]
        if " " in tail:
            tail = tail[tail.index(" ") + 1:]
        out.append((tail + " " + chunks[i]).strip())
    return out

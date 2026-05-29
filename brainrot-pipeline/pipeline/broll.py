"""Fetch a topic-matched stock video clip from Pexels (free API).

Used by the 'explainer' style so each video's background visually matches its
subject (e.g. a train fact -> train b-roll; a cruise-ship story -> ship b-roll).

Get a free key at https://www.pexels.com/api/ -> expose as PEXELS_KEY.
If unset, the explainer style silently falls back to the gameplay clip.
"""
import json
import os
import re
import urllib.parse
import urllib.request

_STOPWORDS = {
    "a","an","the","and","or","but","if","of","in","on","at","to","for","with",
    "from","that","this","is","was","were","are","be","been","being","my","your",
    "his","her","its","their","our","i","me","we","they","you","he","she","it",
    "as","by","do","did","does","have","has","had","not","no","yes","so","too",
    "very","just","then","than","when","while","because","what","why","how",
    "edit","tldr","til","update","aita","tifu","wibta","please","help",
}


def keywords(title: str, max_words: int = 4) -> str:
    """Strip filler words from a title to make a good stock-video query."""
    title = re.sub(r"\(.*?\)|\[.*?\]", " ", title)
    title = re.sub(r"[^A-Za-z0-9 ]+", " ", title).lower()
    toks = [w for w in title.split()
            if w not in _STOPWORDS and len(w) > 2]
    if not toks:
        toks = title.split()[:max_words]
    seen, kept = set(), []
    for w in toks:
        if w not in seen:
            seen.add(w)
            kept.append(w)
        if len(kept) >= max_words:
            break
    return " ".join(kept)


def fetch_clip(title: str, out_path: str, api_key: str = None,
               min_duration: float = 8.0) -> str | None:
    """Search Pexels for a video matching `title` and download to out_path.
    Returns the saved path, or None if no key / no result / network error.
    """
    api_key = api_key or os.environ.get("PEXELS_KEY")
    if not api_key:
        return None
    q = keywords(title) or "abstract"
    url = ("https://api.pexels.com/videos/search?"
           + urllib.parse.urlencode({
               "query": q, "per_page": 12,
               "orientation": "portrait", "size": "medium",
           }))
    try:
        req = urllib.request.Request(url, headers={
            "Authorization": api_key,
            "User-Agent": "brainrot-pipeline/1",
        })
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
    except Exception as e:
        print(f"  pexels search failed for {q!r}: {type(e).__name__}: {e}")
        return None

    videos = data.get("videos", [])
    if not videos:
        print(f"  pexels: no results for {q!r}")
        return None

    # Pick the first video whose largest file is HD-ish and long enough.
    best = None
    for v in videos:
        if v.get("duration", 0) < min_duration:
            continue
        files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4"]
        files.sort(key=lambda f: (f.get("height") or 0), reverse=True)
        for f in files:
            h = f.get("height") or 0
            if 720 <= h <= 1920:
                best = f
                break
        if best:
            break
    if not best and videos:
        # Fallback: just take whatever the first video offers.
        files = videos[0].get("video_files", [])
        if files:
            best = files[0]
    if not best:
        return None

    try:
        req = urllib.request.Request(best["link"], headers={"User-Agent": "brainrot-pipeline/1"})
        with urllib.request.urlopen(req, timeout=60) as r, open(out_path, "wb") as f:
            while True:
                chunk = r.read(64 * 1024)
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        print(f"  pexels download failed: {type(e).__name__}: {e}")
        return None
    print(f"  pexels: {q!r} -> {best.get('width')}x{best.get('height')} "
          f"({os.path.getsize(out_path)//1024} KB)")
    return out_path

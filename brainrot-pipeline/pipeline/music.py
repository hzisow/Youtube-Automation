"""Pick a background music track from a mood-tagged library.

Drop royalty-free .mp3 / .m4a files into:
    assets/music/<mood>/<track>.mp3
where <mood> is one of: chill, sad, funny, dramatic, hype, mystery.

The pipeline picks one at random per video based on the story's tone.
If the matching folder is empty (or doesn't exist), returns None and the
video renders without music. Add files anytime; nothing else to wire up.
"""
import os
import random

VALID_MOODS = ("chill", "sad", "funny", "dramatic", "hype", "mystery")
_EXTS = (".mp3", ".m4a", ".wav", ".ogg", ".aac")


def pick_track(mood: str, music_dir: str) -> str | None:
    """Return a path to a random track for `mood`, or None if none available.

    Falls back to 'chill' if `mood` folder is missing/empty.
    """
    if not music_dir or not os.path.isdir(music_dir):
        return None
    candidates = _list(mood, music_dir)
    if not candidates and mood != "chill":
        candidates = _list("chill", music_dir)
    if not candidates:
        candidates = _list_all(music_dir)
    return random.choice(candidates) if candidates else None


def _list(mood: str, music_dir: str) -> list[str]:
    sub = os.path.join(music_dir, mood)
    if not os.path.isdir(sub):
        return []
    return [os.path.join(sub, f) for f in os.listdir(sub)
            if f.lower().endswith(_EXTS)]


def _list_all(music_dir: str) -> list[str]:
    out = []
    for mood in VALID_MOODS:
        out.extend(_list(mood, music_dir))
    return out

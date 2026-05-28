"""Provide the intro 'ding'. Prefers the bundled sound; synthesizes if missing."""
import os
import subprocess

BUNDLED = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "sounds", "ding.mp3"))


def ensure_ding(path: str) -> str:
    """Return a ding audio path: the bundled sounds/ding.mp3 if present, else a
    synthesized chime written to `path`."""
    if os.path.exists(BUNDLED):
        return BUNDLED
    if os.path.exists(path):
        return path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "sine=frequency=880:duration=0.18",
        "-f", "lavfi", "-i", "sine=frequency=1320:duration=0.32",
        "-filter_complex",
        "[0:a]afade=t=out:st=0.10:d=0.08[a0];"
        "[1:a]adelay=140|140,afade=t=out:st=0.18:d=0.14[a1];"
        "[a0][a1]amix=inputs=2:duration=longest,volume=2.0",
        "-ar", "44100", "-ac", "2", path,
    ]
    subprocess.run(cmd, check=True)
    return path

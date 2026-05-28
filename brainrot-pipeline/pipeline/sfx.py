"""Generate a short notification 'ding' once with FFmpeg (no asset download)."""
import os
import subprocess


def ensure_ding(path: str) -> str:
    """Create a two-tone notification chime at `path` if it doesn't exist."""
    if os.path.exists(path):
        return path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    # Two quick ascending sine tones with a fast decay -> a clean "ding-ding".
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

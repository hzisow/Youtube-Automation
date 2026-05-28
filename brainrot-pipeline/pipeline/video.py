"""Assemble final 1080x1920 video with FFmpeg: gameplay bg + voiceover + burned captions."""
import json
import os
import shlex
import subprocess


def _run(cmd: str) -> None:
    subprocess.run(shlex.split(cmd), check=True)


def _duration(path: str) -> float:
    out = subprocess.check_output(shlex.split(
        f'ffprobe -v error -show_entries format=duration -of json "{path}"'
    ))
    return float(json.loads(out)["format"]["duration"])


def render(background: str, audio: str, ass: str, out_path: str,
           music: str | None = None, music_volume: float = 0.12) -> str:
    """Loop+crop the background to 1080x1920, set length to the voiceover, burn captions."""
    audio_dur = _duration(audio)
    ass_arg = ass.replace("\\", "/").replace(":", "\\:")

    vf = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        f"subtitles='{ass_arg}'"
    )

    if music:
        filter_complex = (
            f"[1:a]volume=1.0[v];"
            f"[2:a]volume={music_volume}[m];"
            f"[v][m]amix=inputs=2:duration=first:dropout_transition=0[a]"
        )
        cmd = (
            f'ffmpeg -y -stream_loop -1 -i "{background}" -i "{audio}" -i "{music}" '
            f'-filter_complex "{filter_complex}" '
            f'-vf "{vf}" -map 0:v -map "[a]" '
            f'-t {audio_dur:.3f} -r 30 -c:v libx264 -preset veryfast -crf 23 '
            f'-c:a aac -b:a 192k -pix_fmt yuv420p -shortest "{out_path}"'
        )
    else:
        cmd = (
            f'ffmpeg -y -stream_loop -1 -i "{background}" -i "{audio}" '
            f'-vf "{vf}" -map 0:v -map 1:a '
            f'-t {audio_dur:.3f} -r 30 -c:v libx264 -preset veryfast -crf 23 '
            f'-c:a aac -b:a 192k -pix_fmt yuv420p -shortest "{out_path}"'
        )
    _run(cmd)
    return out_path

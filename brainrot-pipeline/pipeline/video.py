"""Assemble final 1080x1920 video with FFmpeg: gameplay bg + voiceover + burned
captions, plus an optional Reddit-style title card overlaid at the start."""
import json
import subprocess


def _duration(path: str) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", path,
    ])
    return float(json.loads(out)["format"]["duration"])


def render(background: str, audio: str, ass: str, out_path: str,
           music: str | None = None, music_volume: float = 0.12,
           card: str | None = None, card_end: float = 0.0,
           card_y: int = 230) -> str:
    """Loop+crop background to 1080x1920, burn captions, optionally overlay a
    title card for the first `card_end` seconds, and set length to the voiceover."""
    audio_dur = _duration(audio)
    # Escape the subtitles path for ffmpeg's filtergraph (drive colon + backslashes).
    ass_arg = ass.replace("\\", "/").replace(":", "\\:")

    # Inputs: 0=background, 1=voice, then optional music, then optional card image.
    inputs = ["-stream_loop", "-1", "-i", background, "-i", audio]
    idx = 2
    music_idx = card_idx = None
    if music:
        inputs += ["-i", music]
        music_idx, idx = idx, idx + 1
    if card:
        inputs += ["-i", card]
        card_idx, idx = idx, idx + 1

    graph = [
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,subtitles='{ass_arg}'[base]"
    ]
    if card_idx is not None:
        graph.append(
            f"[base][{card_idx}:v]overlay=x=(W-w)/2:y={card_y}:"
            f"enable='lte(t,{card_end:.3f})'[vout]"
        )
        vmap = "[vout]"
    else:
        vmap = "[base]"

    if music_idx is not None:
        graph.append(
            f"[1:a]volume=1.0[v1];[{music_idx}:a]volume={music_volume}[m];"
            "[v1][m]amix=inputs=2:duration=first:dropout_transition=0[aout]"
        )
        amap = "[aout]"
    else:
        amap = "1:a"

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(graph),
        "-map", vmap, "-map", amap,
        "-t", f"{audio_dur:.3f}", "-r", "30",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest",
        out_path,
    ]
    subprocess.run(cmd, check=True)
    return out_path

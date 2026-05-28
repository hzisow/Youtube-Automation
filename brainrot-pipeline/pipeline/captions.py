"""Word-level karaoke captions via faster-whisper -> ASS subtitle file (free, local)."""
from faster_whisper import WhisperModel

# ASS styling tuned for vertical brainrot: big, centered, bold, thick outline.
# WrapStyle 0 enables word-wrapping; wide side margins keep text on screen.
# Both styles share the same scale so the highlighted word never reflows/overflows.
_ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,Arial,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,6,3,5,90,90,0,1
Style: Hi,Arial,84,&H0000FFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,6,3,5,90,90,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ts(seconds: float) -> str:
    cs = int(round(seconds * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def _collect(segments):
    words = []
    for seg in segments:
        for w in seg.words or []:
            token = w.word.strip()
            if token:
                words.append((token, w.start, w.end))
    return words


def transcribe_words(audio_path: str, model_size: str = "base"):
    """Return list of (word, start, end). Tries GPU, falls back to CPU.

    GPU needs the CUDA runtime (cuBLAS/cuDNN) installed; if it's missing we
    transparently retry on CPU with int8, which is fast enough for short clips.
    """
    try:
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        return _collect(model.transcribe(audio_path, word_timestamps=True)[0])
    except Exception:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        return _collect(model.transcribe(audio_path, word_timestamps=True)[0])


def write_ass(words, ass_path: str, group_size: int = 3, end_pad: float = 2.0) -> str:
    """Group words into short chunks; highlight the active word (TikTok style).

    Captions are gapless: each word's chunk stays on screen from that word's
    start until the next word begins, so text is always visible even during
    pauses/silence. The first caption starts at 0 and the last lingers `end_pad`
    seconds past the final word.
    """
    lines = [_ASS_HEADER]
    n = len(words)
    for i, (word, w_start, w_end) in enumerate(words):
        g = i // group_size
        chunk = words[g * group_size:g * group_size + group_size]
        active = i - g * group_size
        parts = []
        for k, (other, _, _) in enumerate(chunk):
            style = "{\\rHi}" if k == active else "{\\rBase}"
            parts.append(style + other.upper())
        text = " ".join(parts)
        start = 0.0 if i == 0 else w_start
        end = words[i + 1][1] if i + 1 < n else w_end + end_pad
        lines.append(
            f"Dialogue: 0,{_ts(start)},{_ts(end)},Base,,0,0,0,,{text}"
        )
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return ass_path

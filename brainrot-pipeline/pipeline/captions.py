"""Karaoke captions -> ASS subtitle file.

Default style is MrBeast-ish: one bold word at a time, popping in just below
center, colored to match the story's tone. Word timings come from edge-tts.
"""
from .titlecard import _font
from . import tone

DEFAULT_FONT = "Arial"
DEFAULT_SIZE = 96
DEFAULT_Y = 1120  # just below vertical center (PlayResY 1920)
_MAX_LINE_W = 1080 - 2 * 80 - 24


def _header(font_name: str, size: int, color: str) -> str:
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,{font_name},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,9,5,5,80,80,0,1
Style: Hi,{font_name},{size},{color},{color},&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,9,5,5,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def timings_ok(words) -> bool:
    """True if word timings look usable (enough words, spread over time)."""
    if len(words) < 3:
        return False
    span = words[-1][2] - words[0][1]
    return span > 1.5


def _ts(seconds: float) -> str:
    cs = int(round(seconds * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def _layout(chunk, active, font, space_w):
    """Multi-word fallback: styled text with \\N breaks so it stays on screen."""
    rows, row, row_w = [], [], 0.0
    for k, (token, _, _) in enumerate(chunk):
        up = token.upper()
        w = font.getlength(up)
        add = w if not row else space_w + w
        if row and row_w + add > _MAX_LINE_W:
            rows.append(row)
            row, row_w = [], 0.0
            add = w
        row.append((k, up))
        row_w += add
    if row:
        rows.append(row)
    out = []
    for r in rows:
        out.append(" ".join(("{\\rHi}" if k == active else "{\\rBase}") + up for k, up in r))
    return "\\N".join(out)


def write_ass(words, ass_path: str, group_size: int = 1,
              font_name: str = DEFAULT_FONT, font_size: int = DEFAULT_SIZE,
              color: str = None, y: int = DEFAULT_Y, animate: bool = True,
              end_pad: float = 1.5) -> str:
    """Write an ASS file. With group_size=1 (default) each word pops in one at a
    time; larger groups show a short phrase with the active word highlighted.
    Captions are gapless so text is always on screen."""
    if color is None:
        color = tone.COLORS["yellow"]
    font = _font(min(font_size, 90), bold=True)
    space_w = font.getlength(" ")
    pos = f"\\an5\\pos(540,{y})"
    pop = "\\fscx55\\fscy55\\t(0,90,\\fscx112\\fscy112)\\t(90,170,\\fscx100\\fscy100)"

    lines = [_header(font_name, font_size, color)]
    n = len(words)
    for i, (word, w_start, w_end) in enumerate(words):
        start = 0.0 if i == 0 else w_start
        end = words[i + 1][1] if i + 1 < n else w_end + end_pad
        if group_size <= 1:
            override = "{" + pos + (pop if animate else "") + "}"
            text = override + word.upper()
            style = "Hi"
        else:
            g = i // group_size
            chunk = words[g * group_size:g * group_size + group_size]
            active = i - g * group_size
            text = "{" + pos + "}" + _layout(chunk, active, font, space_w)
            style = "Base"
        lines.append(f"Dialogue: 0,{_ts(start)},{_ts(end)},{style},,0,0,0,,{text}")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return ass_path


def transcribe_words(audio_path: str, model_size: str = "base"):
    """Optional fallback: word timings via faster-whisper (slow, CPU/GPU).

    Normally unused now that edge-tts provides timings directly. Kept for audio
    that wasn't produced by our TTS. Imports lazily so the dep is optional.
    """
    from faster_whisper import WhisperModel

    def _collect(segments):
        out = []
        for seg in segments:
            for w in seg.words or []:
                t = w.word.strip()
                if t:
                    out.append((t, w.start, w.end))
        return out

    try:
        m = WhisperModel(model_size, device="cuda", compute_type="float16")
        return _collect(m.transcribe(audio_path, word_timestamps=True)[0])
    except Exception:
        m = WhisperModel(model_size, device="cpu", compute_type="int8")
        return _collect(m.transcribe(audio_path, word_timestamps=True)[0])

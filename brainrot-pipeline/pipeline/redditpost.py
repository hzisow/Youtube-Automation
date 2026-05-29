"""Render a full scrollable Reddit post PNG (header + title + body).

Returns the image path plus a list of per-word (y, idx) anchors so the video
stage can scroll the post in sync with the narration.
"""
import os

from PIL import Image, ImageDraw

from .titlecard import _font, _draw_snoo, _ORANGE, _DARK, _GRAY, _WHITE

PAD = 60
AVATAR = 96
HEADER_GAP = 28
TITLE_GAP = 32
BODY_GAP = 26
LINE_GAP = 14
FOOTER_GAP = 40


def _wrap_words(draw, text, font, max_w):
    """Wrap into lines while tracking the original word index for each word."""
    words = [w for w in text.split() if w]
    lines = []
    cur, cur_w = [], 0.0
    space = draw.textlength(" ", font=font)
    for idx, w in enumerate(words):
        ww = draw.textlength(w, font=font)
        add = ww if not cur else space + ww
        if cur and cur_w + add > max_w:
            lines.append(cur)
            cur, cur_w = [(idx, w, ww)], ww
        else:
            cur.append((idx, w, ww))
            cur_w += add
    if cur:
        lines.append(cur)
    return lines  # list[list[(idx, word, width)]]


def render_post(subreddit: str, username: str, title: str, body: str,
                out_path: str, width: int = 1080) -> tuple[str, list, int]:
    """Render the post; return (path, anchors, image_height).

    anchors = [(global_word_idx, y_center_of_line), ...] one entry per line
    of the rendered title+body, in spoken order. global_word_idx is the
    index in the title-then-body spoken-words sequence.
    """
    title_font = _font(56, bold=True)
    body_font = _font(44, bold=False)
    name_font = _font(34, bold=True)
    meta_font = _font(28, bold=False)
    foot_font = _font(30, bold=False)

    inner = width - 2 * PAD
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)

    title_lines = _wrap_words(d, title, title_font, inner)
    body_lines = _wrap_words(d, body, body_font, inner)

    title_lh = title_font.getbbox("Ag")[3] + LINE_GAP
    body_lh = body_font.getbbox("Ag")[3] + LINE_GAP

    # Total height: padding + header (avatar) + gap + title block + gap + body block + gap + footer + padding.
    header_h = AVATAR
    title_h = len(title_lines) * title_lh
    body_h = len(body_lines) * body_lh
    footer_h = 56
    total_h = (PAD + header_h + HEADER_GAP + title_h + TITLE_GAP
               + body_h + FOOTER_GAP + footer_h + PAD)

    img = Image.new("RGBA", (width, total_h), _WHITE)
    draw = ImageDraw.Draw(img)

    # Header.
    ax, ay = PAD, PAD
    draw.ellipse([ax, ay, ax + AVATAR, ay + AVATAR], fill=_ORANGE)
    _draw_snoo(draw, ax, ay, AVATAR, bg=_ORANGE)
    nx = ax + AVATAR + 24
    draw.text((nx, ay + 10), f"u/{username}", font=name_font, fill=_DARK)
    sub = f"r/{subreddit} • 14h"
    draw.text((nx, ay + 54), sub, font=meta_font, fill=_GRAY)

    # Title.
    anchors = []
    word_cursor = 0  # global index across title then body
    ty = ay + header_h + HEADER_GAP
    for line in title_lines:
        x = PAD
        first_idx = word_cursor
        for k, (_, word, ww) in enumerate(line):
            draw.text((x, ty), word, font=title_font, fill=_DARK)
            x += ww + (title_font.getbbox(" ")[2] if k < len(line) - 1 else 0)
            word_cursor += 1
        anchors.append((first_idx, ty + title_lh // 2))
        ty += title_lh

    # Body.
    by = ty + TITLE_GAP
    for line in body_lines:
        x = PAD
        first_idx = word_cursor
        for k, (_, word, ww) in enumerate(line):
            draw.text((x, by), word, font=body_font, fill=_DARK)
            x += ww + (body_font.getbbox(" ")[2] if k < len(line) - 1 else 0)
            word_cursor += 1
        anchors.append((first_idx, by + body_lh // 2))
        by += body_lh

    # Footer: upvote + comment counts (simple text icons, no emoji font needed).
    fy = by + FOOTER_GAP
    fx = PAD
    draw.text((fx, fy), "▲ 12.4k   ▼   ✉ 1.2k   ↪ Share",
              font=foot_font, fill=_GRAY)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path)
    return out_path, anchors, total_h

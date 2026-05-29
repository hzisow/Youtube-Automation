"""Render a Twitter/X-style post card PNG with scrollable body.

Same return shape as redditpost.render_post so the video stage can reuse the
scroll machinery: (image_path, line_anchors, total_height).
"""
import os
import random

from PIL import Image, ImageDraw

from .titlecard import _font, _WHITE, _DARK, _GRAY

PAD = 60
AVATAR = 96
HEADER_GAP = 28
TITLE_GAP = 28
LINE_GAP = 14
FOOTER_GAP = 36

_BLUE = (29, 155, 240, 255)        # X/Twitter blue
_AVATAR_PALETTE = [
    (244, 67, 54), (255, 152, 0), (255, 193, 7), (139, 195, 74),
    (0, 188, 212), (33, 150, 243), (103, 58, 183), (233, 30, 99),
]


def _avatar_color(handle: str):
    return _AVATAR_PALETTE[hash(handle) % len(_AVATAR_PALETTE)]


def _wrap_words(draw, text, font, max_w):
    words = [w for w in text.split() if w]
    lines, cur, cur_w = [], [], 0.0
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
    return lines


def render_card(handle: str, display_name: str, body: str,
                out_path: str, width: int = 1080) -> tuple[str, list, int]:
    """Render the tweet card; return (path, anchors, image_height).

    anchors = [(global_word_idx, y_center), ...] one per rendered body line.
    """
    body_font = _font(52, bold=False)
    name_font = _font(38, bold=True)
    handle_font = _font(32, bold=False)
    foot_font = _font(28, bold=False)

    inner = width - 2 * PAD
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    body_lines = _wrap_words(d, body, body_font, inner)
    body_lh = body_font.getbbox("Ag")[3] + LINE_GAP

    header_h = AVATAR
    body_h = len(body_lines) * body_lh
    footer_h = 50
    total_h = (PAD + header_h + HEADER_GAP + body_h + FOOTER_GAP
               + footer_h + PAD)

    img = Image.new("RGBA", (width, total_h), _WHITE)
    draw = ImageDraw.Draw(img)

    # Header: colored avatar circle with the handle's first initial.
    ax, ay = PAD, PAD
    color = _avatar_color(handle)
    draw.ellipse([ax, ay, ax + AVATAR, ay + AVATAR], fill=color)
    initial = (display_name or handle).strip("@")[:1].upper() or "?"
    init_font = _font(56, bold=True)
    iw = draw.textlength(initial, font=init_font)
    ih = init_font.getbbox("Ag")[3]
    draw.text((ax + (AVATAR - iw) / 2, ay + (AVATAR - ih) / 2 - 4),
              initial, font=init_font, fill=_WHITE)

    # Name + handle stack.
    nx = ax + AVATAR + 24
    draw.text((nx, ay + 8), display_name, font=name_font, fill=_DARK)
    name_w = draw.textlength(display_name, font=name_font)
    # Verified check.
    cx, cy, r = nx + name_w + 18, ay + 24, 16
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=_BLUE)
    draw.line([(cx - 7, cy), (cx - 2, cy + 6), (cx + 8, cy - 7)],
              fill=_WHITE, width=4, joint="curve")
    draw.text((nx, ay + 52), f"@{handle.lstrip('@')}",
              font=handle_font, fill=_GRAY)

    # Body.
    anchors = []
    word_cursor = 0
    by = ay + header_h + HEADER_GAP
    for line in body_lines:
        x = PAD
        first_idx = word_cursor
        for k, (_, word, ww) in enumerate(line):
            draw.text((x, by), word, font=body_font, fill=_DARK)
            x += ww + (body_font.getbbox(" ")[2] if k < len(line) - 1 else 0)
            word_cursor += 1
        anchors.append((first_idx, by + body_lh // 2))
        by += body_lh

    # Footer.
    fy = by + FOOTER_GAP
    draw.text((PAD, fy), "♥ 12.4K   ↻ 2.1K   💬 384",
              font=foot_font, fill=_GRAY)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path)
    return out_path, anchors, total_h


def handle_for(channel: str) -> tuple[str, str]:
    """Pick a (display_name, handle) pair for the tweet card."""
    rng = random.Random(channel)
    pool = [
        ("peace", "peacetimestar"),
        ("jules", "julesxoxo"),
        ("kai", "kaibyte"),
        ("mira", "mirasaid"),
        ("ari", "arisays"),
        ("noah", "noahdaily"),
    ]
    return rng.choice(pool)

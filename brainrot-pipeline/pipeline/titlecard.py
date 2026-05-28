"""Render a Reddit-style story card PNG (transparent) to overlay at video start."""
import os

from PIL import Image, ImageDraw, ImageFont

CARD_W = 960
PAD = 48
RADIUS = 36
AVATAR = 84

_WHITE = (255, 255, 255, 255)
_DARK = (26, 26, 27, 255)
_GRAY = (135, 138, 140, 255)
_BLUE = (51, 122, 234, 255)
_ORANGE = (255, 69, 0, 255)


def _font(size: int, bold: bool = True):
    names = (
        ["arialbd.ttf", "Arial_Bold.ttf", "DejaVuSans-Bold.ttf"] if bold
        else ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]
    )
    paths = [
        "C:/Windows/Fonts/", "/usr/share/fonts/truetype/dejavu/",
        "/Library/Fonts/", "/System/Library/Fonts/Supplemental/",
    ]
    for d in paths:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _draw_snoo(draw, ax, ay, size, bg=_ORANGE):
    """Draw a simplified Reddit Snoo (white mascot) inside the avatar circle."""
    cx, cy = ax + size / 2, ay + size / 2
    s = size / 84.0
    w = max(1, int(4 * s))
    # Antenna.
    tip = (cx + 13 * s, cy - 30 * s)
    draw.line([(cx, cy - 8 * s), tip], fill=_WHITE, width=w)
    r = 5 * s
    draw.ellipse([tip[0] - r, tip[1] - r, tip[0] + r, tip[1] + r], fill=_WHITE)
    # Ears.
    er = 9 * s
    for ex in (cx - 22 * s, cx + 22 * s):
        draw.ellipse([ex - er, cy - 10 * s - er, ex + er, cy - 10 * s + er], fill=_WHITE)
    # Head.
    hw, hh = 25 * s, 21 * s
    draw.ellipse([cx - hw, cy - hh + 6 * s, cx + hw, cy + hh + 8 * s], fill=_WHITE)
    # Eyes (bg-colored cutouts).
    eye = 5 * s
    ey = cy + 3 * s
    for px in (cx - 11 * s, cx + 11 * s):
        draw.ellipse([px - eye, ey - eye, px + eye, ey + eye], fill=bg)


def render_card(title: str, out_path: str, username: str = "Redditstories",
                handle_color=_ORANGE) -> str:
    title_font = _font(46, bold=True)
    name_font = _font(34, bold=True)
    meta_font = _font(30, bold=False)

    inner_w = CARD_W - 2 * PAD
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    lines = _wrap(d, title, title_font, inner_w)
    line_h = title_font.getbbox("Ag")[3] + 12

    header_h = AVATAR
    title_block = len(lines) * line_h
    footer_h = 60
    card_h = PAD + header_h + 32 + title_block + 28 + footer_h + PAD

    img = Image.new("RGBA", (CARD_W, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, CARD_W, card_h], radius=RADIUS, fill=_WHITE)

    # Avatar: orange circle with the Reddit Snoo mascot.
    ax, ay = PAD, PAD
    draw.ellipse([ax, ay, ax + AVATAR, ay + AVATAR], fill=handle_color)
    _draw_snoo(draw, ax, ay, AVATAR, bg=handle_color)

    # Username + verified check.
    nx = ax + AVATAR + 24
    ny = ay + 8
    draw.text((nx, ny), username, font=name_font, fill=_DARK)
    name_w = draw.textlength(username, font=name_font)
    cx, cy, r = nx + name_w + 18, ny + 16, 16
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=_BLUE)
    draw.line([(cx - 7, cy), (cx - 2, cy + 6), (cx + 8, cy - 7)],
              fill=_WHITE, width=4, joint="curve")
    draw.text((nx, ny + 40), "now", font=meta_font, fill=_GRAY)

    # Title text.
    ty = ay + header_h + 32
    for ln in lines:
        draw.text((PAD, ty), ln, font=title_font, fill=_DARK)
        ty += line_h

    # Footer: like / comment / share with hand-drawn icons (no emoji font needed).
    fy = ty + 24
    h = meta_font.getbbox("99+")[3]
    x = PAD
    # Heart.
    draw.text((x, fy), "♥", font=meta_font, fill=_GRAY)
    x += draw.textlength("♥", font=meta_font) + 10
    draw.text((x, fy), "99+", font=meta_font, fill=_GRAY)
    x += draw.textlength("99+", font=meta_font) + 44
    # Comment bubble.
    by = fy + 6
    draw.rounded_rectangle([x, by, x + 34, by + h - 10], radius=8, outline=_GRAY, width=3)
    draw.polygon([(x + 8, by + h - 10), (x + 8, by + h + 2), (x + 18, by + h - 10)], fill=_GRAY)
    x += 34 + 12
    draw.text((x, fy), "99+", font=meta_font, fill=_GRAY)
    x += draw.textlength("99+", font=meta_font) + 44
    # Share arrow.
    draw.text((x, fy), "↪", font=meta_font, fill=_GRAY)
    x += draw.textlength("↪", font=meta_font) + 10
    draw.text((x, fy), "Share", font=meta_font, fill=_GRAY)

    img.save(out_path)
    return out_path


def title_end_time(words, title: str, pad: float = 0.4, minimum: float = 2.5) -> float:
    """Timestamp where the spoken title ends, so the card hides right after.

    Never returns less than `minimum` so the card is always visible at the start
    even if the title is very short or word timings are missing.
    """
    n = len([w for w in title.split() if w.strip()])
    n = min(n, len(words))
    if n == 0:
        return minimum
    return max(words[n - 1][2] + pad, minimum)

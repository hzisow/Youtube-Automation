"""Build an ffmpeg crop-y expression that scrolls a tall image in sync with
spoken word timings."""


def build_scroll_expr(anchors, words, viewport_h: int, image_h: int,
                      target_offset: int = None) -> str:
    """Build an ffmpeg expression for crop y given line anchors + word timings.

    anchors: list of (word_idx, y_center) one per rendered line, in spoken order.
    words:   list of (text, start, end) from edge-tts.
    viewport_h: visible window height (pixels).
    image_h:    full post image height (pixels).
    target_offset: where on the viewport the active line should sit. Defaults to
                   viewport_h // 3 (active line near upper third).
    """
    if target_offset is None:
        target_offset = viewport_h // 3
    max_top = max(0, image_h - viewport_h)

    # Map each line anchor to (time, desired_crop_y).
    points = []
    n_words = len(words)
    for idx, y_center in anchors:
        if idx >= n_words:
            t = words[-1][1] if words else 0.0
        else:
            t = words[idx][1]
        y_top = max(0, min(max_top, y_center - target_offset))
        points.append((t, y_top))

    # Deduplicate & sort by t.
    points.sort()
    cleaned = []
    for t, y in points:
        if cleaned and abs(t - cleaned[-1][0]) < 0.05:
            continue
        cleaned.append((t, y))
    if not cleaned:
        return "0"

    # Build nested if() expression: piecewise linear interp between anchors.
    expr = f"{cleaned[-1][1]:.1f}"
    for i in range(len(cleaned) - 1, 0, -1):
        t0, y0 = cleaned[i - 1]
        t1, y1 = cleaned[i]
        dt = max(t1 - t0, 0.001)
        interp = (f"({y0:.1f}+({y1:.1f}-{y0:.1f})"
                  f"*((t-{t0:.3f})/{dt:.4f}))")
        expr = f"if(lt(t,{t1:.3f}),{interp},{expr})"
    t0, y0 = cleaned[0]
    expr = f"if(lt(t,{t0:.3f}),{y0:.1f},{expr})"
    return f"min({max_top:.1f}\\,max(0\\,{expr}))"

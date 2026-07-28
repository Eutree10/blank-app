"""Data-bearing visual primitives.

Rings, sparklines and delta bars, drawn as inline SVG. They are here rather
than in `charts.py` because they are *readouts*, not charts: each one shows a
single number in context, small enough to sit inside a card. Nothing here is
decorative — every shape is bound to a value the athlete can act on.
"""

from __future__ import annotations

import math
from html import escape

from ..formats import fmt_num
from . import theme


def ring(
    value: float,
    label: str,
    caption: str = "",
    maximum: float = 100,
    color: str | None = None,
    size: int = 76,
    unit: str = "",
) -> str:
    """A progress ring with the number inside it.

    `value` is drawn as a fraction of `maximum`; the track behind it stays
    visible so an incomplete ring reads as "how much is left", not as an error.
    """
    fraction = max(0.0, min(1.0, value / maximum if maximum else 0.0))
    color = color or theme.score_color(fraction * 100)
    stroke = 5.5
    radius = (size - stroke) / 2
    centre = size / 2
    circumference = 2 * math.pi * radius
    filled = circumference * fraction

    display = fmt_num(value, 1) if isinstance(value, float) and value % 1 else f"{int(value)}"
    unit_html = (
        f'<tspan style="font-size:.52em;fill:{theme.FAINT}">{escape(unit)}</tspan>' if unit else ""
    )
    caption_html = (
        f'<div style="font-size:.66rem;color:{theme.FAINT};margin-top:.1rem;'
        f'letter-spacing:-.005em">{escape(caption)}</div>'
        if caption
        else ""
    )

    return (
        f'<div style="text-align:center">'
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
        f'style="display:block;margin:0 auto">'
        f'<circle cx="{centre}" cy="{centre}" r="{radius}" fill="none" '
        f'stroke="#EDEDEA" stroke-width="{stroke}"/>'
        f'<circle cx="{centre}" cy="{centre}" r="{radius}" fill="none" '
        f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-dasharray="{filled:.2f} {circumference:.2f}" '
        f'transform="rotate(-90 {centre} {centre})"/>'
        f'<text x="{centre}" y="{centre}" text-anchor="middle" dominant-baseline="central" '
        f'style="font-family:{theme.MONO_STACK};font-size:{size * 0.28:.0f}px;font-weight:600;'
        f'fill:{theme.INK};letter-spacing:-.03em">{display}{unit_html}</text>'
        f"</svg>"
        f'<div style="font-size:.72rem;color:{theme.MUTED};margin-top:.35rem;'
        f'font-weight:520;letter-spacing:-.01em">{escape(label)}</div>'
        f"{caption_html}</div>"
    )


def sparkline(
    values: list[float],
    width: int = 120,
    height: int = 30,
    color: str | None = None,
    invert: bool = False,
) -> str:
    """A bare trend line. `invert` flips it so that lower values sit higher.

    Paces need `invert`: a faster pace is a smaller number but should read as
    an upward trend.
    """
    usable = [value for value in values if value is not None and math.isfinite(value)]
    if len(usable) < 2:
        return f'<svg width="{width}" height="{height}"></svg>'

    color = color or theme.RED
    low, high = min(usable), max(usable)
    span = (high - low) or 1.0
    step = width / (len(usable) - 1)

    points = []
    for index, value in enumerate(usable):
        fraction = (value - low) / span
        if not invert:
            fraction = 1 - fraction
        x = index * step
        y = 2 + fraction * (height - 4)
        points.append(f"{x:.1f},{y:.1f}")

    path = " ".join(points)
    area = f"0,{height} {path} {width},{height}"
    gradient_id = f"sg{abs(hash(tuple(usable))) % 100000}"
    return (
        f'<svg width="100%" height="{height}" viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="none" style="display:block">'
        f'<defs><linearGradient id="{gradient_id}" x1="0" x2="0" y1="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.16"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f"</linearGradient></defs>"
        f'<polygon points="{area}" fill="url(#{gradient_id})"/>'
        f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="1.6" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f"</svg>"
    )


def stat_tile(
    label: str,
    value: str,
    unit: str = "",
    trend: list[float] | None = None,
    invert_trend: bool = False,
    note: str = "",
) -> str:
    """A labelled number with an optional trend line beneath it."""
    unit_html = (
        f'<span style="font-size:.72rem;color:{theme.MUTED};font-weight:500;'
        f'margin-left:.12rem">{escape(unit)}</span>'
        if unit
        else ""
    )
    spark = sparkline(trend, invert=invert_trend) if trend else ""
    note_html = (
        f'<div style="font-size:.68rem;color:{theme.FAINT};margin-top:.2rem">{escape(note)}</div>'
        if note
        else ""
    )
    return (
        f'<div class="rf-card" style="margin-bottom:0;padding:.85rem .9rem">'
        f'<div style="font-size:.74rem;color:{theme.MUTED};letter-spacing:-.005em">{escape(label)}</div>'
        f'<div class="rf-value" style="font-size:1.45rem;margin-top:.15rem;line-height:1.1">'
        f"{escape(value)}{unit_html}</div>"
        f"{note_html}"
        f'<div style="margin-top:.45rem">{spark}</div>'
        f"</div>"
    )


def delta_bars(
    rows: list[tuple[str, str, float, float]],
    invert: bool = True,
) -> str:
    """Split/rep rows with a bar and a signed delta.

    Each row is (label, value text, magnitude, delta in seconds). The bar
    length encodes the magnitude relative to the fastest row, so a session's
    evenness is visible at a glance. With `invert`, a negative delta (faster)
    is the good direction and is coloured as such.
    """
    if not rows:
        return ""

    magnitudes = [magnitude for _, _, magnitude, _ in rows]
    best, worst = min(magnitudes), max(magnitudes)
    span = (worst - best) or 1.0

    html = []
    for label, value_text, magnitude, delta in rows:
        # Longest bar for the fastest row, floored so nothing disappears.
        fraction = 1 - (magnitude - best) / span
        width = 34 + fraction * 66

        good = (delta <= 0) if invert else (delta >= 0)
        delta_color = theme.GOOD if good else theme.BAD
        if abs(delta) < 0.5:
            delta_text, delta_color = "±0", theme.FAINT
        else:
            delta_text = f"{'+' if delta > 0 else '−'}{abs(delta):.0f}"

        html.append(
            f'<div style="display:flex;align-items:center;gap:.55rem;padding:.32rem 0">'
            f'<div style="width:1.3rem;font-family:{theme.MONO_STACK};font-size:.74rem;'
            f'color:{theme.FAINT};flex-shrink:0">{escape(label)}</div>'
            f'<div style="width:3.1rem;font-family:{theme.MONO_STACK};font-size:.82rem;'
            f'font-weight:560;color:{theme.INK};flex-shrink:0">{escape(value_text)}</div>'
            f'<div style="flex:1;height:6px;background:#F0F0ED;border-radius:3px;overflow:hidden">'
            f'<div style="width:{width:.1f}%;height:100%;background:{theme.RED};'
            f'border-radius:3px;opacity:.88"></div></div>'
            f'<div style="width:2.1rem;text-align:right;font-family:{theme.MONO_STACK};'
            f'font-size:.72rem;color:{delta_color};flex-shrink:0">{delta_text}</div>'
            f"</div>"
        )
    return "".join(html)


def weekday_bars(
    values: list[float],
    labels: list[str],
    target: float | None = None,
    today_index: int | None = None,
) -> str:
    """Seven day-of-week bars. Days still to come are drawn as empty outlines."""
    peak = max([value for value in values if value] or [1.0])
    ceiling = max(peak, (target or 0) / 3.5) or 1.0

    bars = []
    for index, (value, label) in enumerate(zip(values, labels)):
        future = today_index is not None and index > today_index
        height = max(3.0, (value / ceiling) * 46) if value else 3.0
        if future:
            body = (
                f'<div style="width:100%;height:46px;border:1px dashed {theme.LINE};'
                f'border-radius:3px"></div>'
            )
        else:
            is_today = index == today_index
            color = theme.RED if not is_today else theme.RED
            opacity = 1.0 if (value and not is_today) else (1.0 if is_today else 0.25)
            body = (
                f'<div style="display:flex;align-items:flex-end;height:46px">'
                f'<div style="width:100%;height:{height:.0f}px;background:{color};'
                f'opacity:{opacity};border-radius:3px"></div></div>'
            )
        bars.append(
            f'<div style="flex:1;text-align:center">{body}'
            f'<div style="font-size:.64rem;color:{theme.FAINT};margin-top:.3rem">{escape(label)}</div>'
            f"</div>"
        )
    return f'<div style="display:flex;gap:.3rem;align-items:flex-end">{"".join(bars)}</div>'


# Inline SVG icons. Deliberately a small, consistent set drawn on the same
# 24-grid — generic icon fonts were the thing the brief ruled out.
_ICONS = {
    "clock": "M12 7v5l3 2M12 3a9 9 0 100 18 9 9 0 000-18z",
    "gauge": "M12 14l4-4M5.6 18.4a9 9 0 1112.8 0",
    "heart": "M12 20s-7-4.6-7-9.4A4 4 0 0112 8a4 4 0 017 2.6c0 4.8-7 9.4-7 9.4z",
    "steps": "M7 4v7a3 3 0 006 0M11 20v-7a3 3 0 016 0",
    "mountain": "M3 19l6-11 4 7 2-3 6 7z",
    "flame": "M12 21a5 5 0 005-5c0-4-5-8-5-8s-5 4-5 8a5 5 0 005 5z",
    "route": "M6 19a2 2 0 100-4 2 2 0 000 4zM18 9a2 2 0 100-4 2 2 0 000 4zM18 9c0 4-12 2-12 6",
    "calendar": "M4 8h16M8 4v3M16 4v3M5 6h14v14H5z",
    "home": "M4 11l8-7 8 7M6 10v10h12V10",
    "chart": "M5 20V10M12 20V4M19 20v-7",
    "target": "M12 4a8 8 0 100 16 8 8 0 000-16zM12 9.5a2.5 2.5 0 100 5 2.5 2.5 0 000-5z",
    "person": "M12 11a4 4 0 100-8 4 4 0 000 8zM5 21c0-4 3-6 7-6s7 2 7 6",
}


def icon(name: str, size: int = 15, color: str | None = None, stroke: float = 1.7) -> str:
    path = _ICONS.get(name)
    if not path:
        return ""
    color = color or theme.RED
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round" style="display:block">'
        f'<path d="{path}"/></svg>'
    )


def metric_grid(items: list[tuple[str, str, str]], columns: int = 3) -> str:
    """A grid of (icon name, value, label) tiles — the session's headline numbers.

    The value is large and the label is a small uppercase caption beneath it,
    with hairline rules between cells so the grid reads as one table.
    """
    cells = []
    for index, (icon_name, value, label) in enumerate(items):
        right_rule = (index % columns) != columns - 1
        bottom_rule = index < len(items) - (len(items) % columns or columns)
        borders = ""
        if right_rule:
            borders += f"border-right:1px solid {theme.LINE};"
        if bottom_rule:
            borders += f"border-bottom:1px solid {theme.LINE};"
        cells.append(
            f'<div style="text-align:center;padding:.85rem .3rem;{borders}">'
            f'<div style="display:flex;justify-content:center;margin-bottom:.35rem">'
            f"{icon(icon_name, size=14)}</div>"
            f'<div class="rf-value" style="font-size:1.28rem;line-height:1.1;'
            f'letter-spacing:-.035em">{escape(value)}</div>'
            f'<div class="rf-microlabel">{escape(label)}</div>'
            f"</div>"
        )
    return (
        f'<div style="display:grid;grid-template-columns:repeat({columns},1fr);'
        f'gap:0">{"".join(cells)}</div>'
    )


def chip(label: str, color: str, active: bool = False) -> str:
    """A pill with a coloured dot — used for the eight workout families."""
    background = color if active else "transparent"
    border = color if active else theme.LINE
    text = "#FFFFFF" if active else theme.BODY
    dot = "#FFFFFF" if active else color
    return (
        f'<span style="display:inline-flex;align-items:center;gap:.34rem;'
        f"padding:.3rem .68rem;border-radius:999px;background:{background};"
        f'border:1px solid {border};margin:0 .3rem .4rem 0">'
        f'<span style="width:6px;height:6px;border-radius:50%;background:{dot};'
        f'flex-shrink:0"></span>'
        f'<span style="font-size:.68rem;font-weight:600;letter-spacing:.07em;'
        f'text-transform:uppercase;color:{text}">{escape(label)}</span></span>'
    )


def workout_chips(active_value: str) -> str:
    """The full family row, with the session's own type filled in."""
    return "".join(
        chip(name, colour, active=name == active_value)
        for name, colour in theme.WORKOUT_COLORS.items()
    )

"""Minimal, dependency-free SVG charts.

The project deliberately avoids a plotting dependency: the figures it needs are
simple bar and line charts, and a few dozen lines of SVG keep the reproduction
environment to garak plus the standard library. Every chart is theme-neutral
(dark text on light ground) and self-contained so it drops straight into a
report or an HTML page.
"""

from __future__ import annotations

import html
from dataclasses import dataclass

_PALETTE = [
    "#2563eb",  # blue
    "#dc2626",  # red
    "#16a34a",  # green
    "#d97706",  # amber
    "#7c3aed",  # violet
    "#0891b2",  # cyan
]
_AXIS = "#334155"
_GRID = "#e2e8f0"
_TEXT = "#0f172a"
_MUTED = "#64748b"


def _esc(text: str) -> str:
    """HTML-escape a value for safe inclusion in SVG/HTML text."""
    return html.escape(str(text))


@dataclass
class Series:
    """A named numeric series for a chart."""
    name: str
    values: list[float]


def _svg_header(width: int, height: int, title: str) -> list[str]:
    """Return the opening SVG tag, background, and centred title."""
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="13">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
        f'<text x="{width/2}" y="24" text-anchor="middle" font-size="16" '
        f'font-weight="600" fill="{_TEXT}">{_esc(title)}</text>',
    ]


def grouped_bar_chart(
    title: str,
    categories: list[str],
    series: list[Series],
    *,
    y_label: str = "",
    y_max: float = 1.0,
    width: int = 720,
    height: int = 420,
    percent: bool = True,
) -> str:
    """Grouped vertical bar chart. Values are assumed in [0, y_max]."""

    left, right, top, bottom = 70, 24, 50, 90
    plot_w = width - left - right
    plot_h = height - top - bottom
    parts = _svg_header(width, height, title)

    # y grid + labels
    ticks = 5
    for i in range(ticks + 1):
        frac = i / ticks
        y = top + plot_h * (1 - frac)
        val = frac * y_max
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" '
            f'stroke="{_GRID}" stroke-width="1"/>'
        )
        label = f"{val*100:.0f}%" if percent else f"{val:.2g}"
        parts.append(
            f'<text x="{left-8}" y="{y+4:.1f}" text-anchor="end" '
            f'fill="{_MUTED}" font-size="11">{label}</text>'
        )
    if y_label:
        parts.append(
            f'<text x="16" y="{top+plot_h/2:.1f}" text-anchor="middle" fill="{_MUTED}" '
            f'font-size="11" transform="rotate(-90 16 {top+plot_h/2:.1f})">{_esc(y_label)}</text>'
        )

    n_cat = len(categories)
    n_ser = len(series)
    group_w = plot_w / max(1, n_cat)
    bar_w = group_w / (n_ser + 0.5)

    for ci, cat in enumerate(categories):
        gx = left + ci * group_w
        for si, s in enumerate(series):
            v = s.values[ci] if ci < len(s.values) else 0.0
            if v is None:
                continue
            bh = plot_h * (min(v, y_max) / y_max)
            bx = gx + 0.25 * bar_w + si * bar_w
            by = top + plot_h - bh
            parts.append(
                f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w*0.9:.1f}" '
                f'height="{bh:.1f}" fill="{_PALETTE[si % len(_PALETTE)]}" rx="2"/>'
            )
        parts.append(
            f'<text x="{gx+group_w/2:.1f}" y="{top+plot_h+18:.1f}" text-anchor="middle" '
            f'fill="{_TEXT}" font-size="11">{_esc(cat)}</text>'
        )

    # axes
    parts.append(
        f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" '
        f'stroke="{_AXIS}" stroke-width="1.5"/>'
    )
    parts.append(
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" '
        f'stroke="{_AXIS}" stroke-width="1.5"/>'
    )

    # legend
    if n_ser > 1:
        lx = left
        ly = height - 30
        for si, s in enumerate(series):
            parts.append(
                f'<rect x="{lx:.1f}" y="{ly:.1f}" width="12" height="12" '
                f'fill="{_PALETTE[si % len(_PALETTE)]}" rx="2"/>'
            )
            parts.append(
                f'<text x="{lx+18:.1f}" y="{ly+11:.1f}" fill="{_TEXT}" '
                f'font-size="12">{_esc(s.name)}</text>'
            )
            lx += 30 + 8 * len(s.name)
    parts.append("</svg>")
    return "\n".join(parts)


def line_chart(
    title: str,
    x_values: list[float],
    series: list[Series],
    *,
    x_label: str = "",
    y_label: str = "",
    y_max: float = 1.0,
    y_min: float = 0.0,
    width: int = 720,
    height: int = 420,
    baseline: float | None = None,
) -> str:
    """Line chart over a numeric x axis."""

    left, right, top, bottom = 70, 24, 50, 80
    plot_w = width - left - right
    plot_h = height - top - bottom
    parts = _svg_header(width, height, title)

    span = (y_max - y_min) or 1.0
    x_lo, x_hi = min(x_values), max(x_values)
    x_span = (x_hi - x_lo) or 1.0

    def px(x: float) -> float:
        """Map a data x-value to a pixel x-coordinate."""
        return left + plot_w * (x - x_lo) / x_span

    def py(y: float) -> float:
        """Map a data y-value to a pixel y-coordinate."""
        return top + plot_h * (1 - (y - y_min) / span)

    ticks = 5
    for i in range(ticks + 1):
        frac = i / ticks
        y = top + plot_h * (1 - frac)
        val = y_min + frac * span
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" '
            f'stroke="{_GRID}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{left-8}" y="{y+4:.1f}" text-anchor="end" fill="{_MUTED}" '
            f'font-size="11">{val:.2g}</text>'
        )

    if baseline is not None:
        by = py(baseline)
        parts.append(
            f'<line x1="{left}" y1="{by:.1f}" x2="{left+plot_w}" y2="{by:.1f}" '
            f'stroke="{_MUTED}" stroke-width="1" stroke-dasharray="4 4"/>'
        )
        parts.append(
            f'<text x="{left+plot_w-4}" y="{by-4:.1f}" text-anchor="end" '
            f'fill="{_MUTED}" font-size="10">decision boundary</text>'
        )

    for xv in x_values:
        parts.append(
            f'<text x="{px(xv):.1f}" y="{top+plot_h+18:.1f}" text-anchor="middle" '
            f'fill="{_TEXT}" font-size="11">{xv:g}</text>'
        )

    for si, s in enumerate(series):
        color = _PALETTE[si % len(_PALETTE)]
        pts = " ".join(
            f"{px(x):.1f},{py(v):.1f}"
            for x, v in zip(x_values, s.values)
            if v is not None
        )
        parts.append(
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.5"/>'
        )
        for x, v in zip(x_values, s.values):
            if v is not None:
                parts.append(
                    f'<circle cx="{px(x):.1f}" cy="{py(v):.1f}" r="3.5" fill="{color}"/>'
                )

    parts.append(
        f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" '
        f'stroke="{_AXIS}" stroke-width="1.5"/>'
    )
    parts.append(
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" '
        f'stroke="{_AXIS}" stroke-width="1.5"/>'
    )
    if x_label:
        parts.append(
            f'<text x="{left+plot_w/2:.1f}" y="{height-30}" text-anchor="middle" '
            f'fill="{_MUTED}" font-size="11">{_esc(x_label)}</text>'
        )
    if y_label:
        parts.append(
            f'<text x="16" y="{top+plot_h/2:.1f}" text-anchor="middle" fill="{_MUTED}" '
            f'font-size="11" transform="rotate(-90 16 {top+plot_h/2:.1f})">{_esc(y_label)}</text>'
        )

    if len(series) > 1:
        lx, ly = left, height - 14
        for si, s in enumerate(series):
            color = _PALETTE[si % len(_PALETTE)]
            parts.append(
                f'<rect x="{lx:.1f}" y="{ly-10:.1f}" width="12" height="12" fill="{color}" rx="2"/>'
            )
            parts.append(
                f'<text x="{lx+18:.1f}" y="{ly:.1f}" fill="{_TEXT}" font-size="12">{_esc(s.name)}</text>'
            )
            lx += 30 + 8 * len(s.name)
    parts.append("</svg>")
    return "\n".join(parts)

"""Minimal, dependency-free SVG charts.

The project deliberately avoids a plotting dependency: the figures it needs are
simple bar and line charts, and a few dozen lines of SVG keep the reproduction
environment to garak plus the standard library. Every chart is theme-neutral
(dark text on light ground) and self-contained so it drops straight into a
report or an HTML page.
"""

from __future__ import annotations

import html
from collections.abc import Sequence
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

# Legend metrics. The legend is laid out by hand because SVG has no text
# measurement: _LEGEND_CHAR_W is a deliberate over-estimate of the average
# advance width at font-size 12, so a row that is predicted to fit really does
# fit and long labels wrap one entry early rather than running off the canvas.
_LEGEND_CHAR_W = 7.0
_LEGEND_SWATCH = 12
_LEGEND_PAD = 6  # swatch-to-text gap
_LEGEND_GAP = 24  # gap between entries
_LEGEND_ROW_H = 18


def _esc(text: str) -> str:
    """HTML-escape a value for safe inclusion in SVG/HTML text."""
    return html.escape(str(text))


def _legend_rows(names: list[str], max_width: float) -> list[list[tuple[str, float]]]:
    """Pack ``(name, width)`` legend entries into rows no wider than ``max_width``.

    An entry wider than ``max_width`` on its own still gets a row to itself --
    dropping it would leave a plotted series unnamed, which is the failure this
    packing exists to prevent.
    """
    rows: list[list[tuple[str, float]]] = []
    row: list[tuple[str, float]] = []
    row_w = 0.0
    for name in names:
        w = _LEGEND_SWATCH + _LEGEND_PAD + _LEGEND_CHAR_W * len(name) + _LEGEND_GAP
        if row and row_w + w > max_width:
            rows.append(row)
            row, row_w = [], 0.0
        row.append((name, w))
        row_w += w
    if row:
        rows.append(row)
    return rows


def _legend_parts(
    rows: list[list[tuple[str, float]]], left: float, top: float
) -> list[str]:
    """Render pre-packed legend rows, ``top`` being the first row's swatch y."""
    parts: list[str] = []
    idx = 0
    for ri, row in enumerate(rows):
        x = left
        y = top + ri * _LEGEND_ROW_H
        for name, w in row:
            color = _PALETTE[idx % len(_PALETTE)]
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{_LEGEND_SWATCH}" '
                f'height="{_LEGEND_SWATCH}" fill="{color}" rx="2"/>'
            )
            parts.append(
                f'<text x="{x + _LEGEND_SWATCH + _LEGEND_PAD:.1f}" y="{y + 11:.1f}" '
                f'fill="{_TEXT}" font-size="12">{_esc(name)}</text>'
            )
            x += w
            idx += 1
    return parts


@dataclass
class Series:
    """A named numeric series for a chart.

    ``None`` marks a point the analysis could not measure. Both chart functions
    skip those rather than plotting them as zero, which would read as a measured
    result of nothing.

    ``Sequence`` rather than ``list`` so an all-measured series typed
    ``list[float]`` is accepted too.
    """

    name: str
    values: Sequence[float | None]


def _svg_header(width: int, height: int, title: str) -> list[str]:
    """Return the opening SVG tag, background, and centred title."""
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="13">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
        f'<text x="{width / 2}" y="24" text-anchor="middle" font-size="16" '
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
    # The legend sits below the plot and may need more than one row; the canvas
    # grows to hold it rather than the extra rows falling off the bottom.
    rows = _legend_rows([s.name for s in series], plot_w) if len(series) > 1 else []
    canvas_h = height + max(0, len(rows) - 1) * _LEGEND_ROW_H
    parts = _svg_header(width, canvas_h, title)

    # y grid + labels
    ticks = 5
    for i in range(ticks + 1):
        frac = i / ticks
        y = top + plot_h * (1 - frac)
        val = frac * y_max
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" '
            f'stroke="{_GRID}" stroke-width="1"/>'
        )
        label = f"{val * 100:.0f}%" if percent else f"{val:.2g}"
        parts.append(
            f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" '
            f'fill="{_MUTED}" font-size="11">{label}</text>'
        )
    if y_label:
        parts.append(
            f'<text x="16" y="{top + plot_h / 2:.1f}" text-anchor="middle" '
            f'fill="{_MUTED}" font-size="11" '
            f'transform="rotate(-90 16 {top + plot_h / 2:.1f})">{_esc(y_label)}</text>'
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
                f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w * 0.9:.1f}" '
                f'height="{bh:.1f}" fill="{_PALETTE[si % len(_PALETTE)]}" rx="2"/>'
            )
        parts.append(
            f'<text x="{gx + group_w / 2:.1f}" y="{top + plot_h + 18:.1f}" text-anchor="middle" '
            f'fill="{_TEXT}" font-size="11">{_esc(cat)}</text>'
        )

    # axes
    parts.append(
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" '
        f'stroke="{_AXIS}" stroke-width="1.5"/>'
    )
    parts.append(
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" '
        f'stroke="{_AXIS}" stroke-width="1.5"/>'
    )

    # legend
    parts.extend(_legend_parts(rows, left, height - 30))
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
    rows = _legend_rows([s.name for s in series], plot_w) if len(series) > 1 else []
    canvas_h = height + max(0, len(rows) - 1) * _LEGEND_ROW_H
    parts = _svg_header(width, canvas_h, title)

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
            f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" '
            f'stroke="{_GRID}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" fill="{_MUTED}" '
            f'font-size="11">{val:.2g}</text>'
        )

    if baseline is not None:
        by = py(baseline)
        parts.append(
            f'<line x1="{left}" y1="{by:.1f}" x2="{left + plot_w}" y2="{by:.1f}" '
            f'stroke="{_MUTED}" stroke-width="1" stroke-dasharray="4 4"/>'
        )
        parts.append(
            f'<text x="{left + plot_w - 4}" y="{by - 4:.1f}" text-anchor="end" '
            f'fill="{_MUTED}" font-size="10">decision boundary</text>'
        )

    for xv in x_values:
        parts.append(
            f'<text x="{px(xv):.1f}" y="{top + plot_h + 18:.1f}" text-anchor="middle" '
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
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" '
        f'stroke="{_AXIS}" stroke-width="1.5"/>'
    )
    parts.append(
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" '
        f'stroke="{_AXIS}" stroke-width="1.5"/>'
    )
    if x_label:
        parts.append(
            f'<text x="{left + plot_w / 2:.1f}" y="{height - 30}" text-anchor="middle" '
            f'fill="{_MUTED}" font-size="11">{_esc(x_label)}</text>'
        )
    if y_label:
        parts.append(
            f'<text x="16" y="{top + plot_h / 2:.1f}" text-anchor="middle" '
            f'fill="{_MUTED}" font-size="11" '
            f'transform="rotate(-90 16 {top + plot_h / 2:.1f})">{_esc(y_label)}</text>'
        )

    parts.extend(_legend_parts(rows, left, height - 24))
    parts.append("</svg>")
    return "\n".join(parts)

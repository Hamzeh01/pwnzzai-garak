"""Convert a simple SVG chart to a same-size vector PDF."""

from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg


def convert_svg(source: Path, output: Path) -> None:
    """Render source into output while preserving its vector dimensions."""
    drawing = svg2rlg(str(source))
    if drawing is None:
        raise ValueError(f"Could not parse SVG: {source}")
    renderPDF.drawToFile(drawing, str(output))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    convert_svg(args.source, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

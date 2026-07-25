"""Build deterministic local-only QR inputs for the frozen Phase 5 catalog."""

from __future__ import annotations

import argparse
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_M


ROOT = Path(__file__).resolve().parents[1]
QR_DIRECTORY = ROOT / "payloads" / "phase-05" / "qr"
INPUTS = (
    "CTL-IPI-BENIGN-001",
    "IPI-INSTRUCTION-001",
    "IPI-SECRET-001",
)


def build_qr(source: Path, destination: Path, *, overwrite: bool = False) -> None:
    if destination.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite frozen artifact: {destination}")
    text = source.read_text(encoding="utf-8").rstrip("\r\n")
    if not text:
        raise ValueError(f"QR source text is empty: {source}")
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=6,
        border=4,
    )
    qr.add_data(text, optimize=0)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    image.save(destination, format="PNG", optimize=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    for stem in INPUTS:
        build_qr(
            QR_DIRECTORY / f"{stem}.txt",
            QR_DIRECTORY / f"{stem}.png",
            overwrite=args.overwrite,
        )
        print(f"built payloads/phase-05/qr/{stem}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

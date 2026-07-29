"""Generate deterministic Phase 7 analysis artifacts without target requests."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.phase07 import (
    EXPECTED_PROTOCOL_VERSION,
    EXPECTED_RUN_ID,
    check_generated_artifacts,
    generate_phase07,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate or verify the frozen Phase 7 analysis outputs."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify generated outputs byte-for-byte without writing them.",
    )
    args = parser.parse_args()
    if args.check:
        failures = check_generated_artifacts(ROOT)
        if failures:
            for failure in failures:
                print(f"FAIL: {failure}")
            return 1
        print(
            "PASS: Phase 7 generated artifacts are current for "
            f"{EXPECTED_RUN_ID} protocol {EXPECTED_PROTOCOL_VERSION}"
        )
        return 0

    artifacts = generate_phase07(ROOT)
    print(
        f"Generated {len(artifacts)} Phase 7 artifacts from {EXPECTED_RUN_ID} "
        f"protocol {EXPECTED_PROTOCOL_VERSION}; no target requests were made"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

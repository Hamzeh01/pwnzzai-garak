"""Run the separately authorized frozen Phase 6 protocol."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.probes.phase06_full import Phase06FullRun


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    args = parser.parse_args()

    preflight_path = args.preflight
    if not preflight_path.is_absolute():
        preflight_path = ROOT / preflight_path
    runner = Phase06FullRun(
        args.run_id,
        preflight_path=preflight_path.resolve(),
    )
    summary = runner.run()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

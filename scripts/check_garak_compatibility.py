"""Record the pinned Garak interface checks used by the Phase 4 adapter."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.adapters.garak_openai import verify_garak_compatibility


DEFAULT_OUTPUT = ROOT / "evidence" / "setup" / "phase-04-garak-compatibility.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    result = verify_garak_compatibility()
    result["checked_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not result["compatible"]:
        print(f"FAIL: incompatible Garak interface; evidence: {args.output}")
        return 1
    print(f"PASS: Garak interface compatible; evidence: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

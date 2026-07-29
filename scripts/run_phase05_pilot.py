"""CLI for the authorized, frozen Phase 5 bounded pilot."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_phase05_protocol import validate_phase05_protocol
from src.probes.phase05_pilot import Phase05Pilot, SafetyStop


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-id",
        default=f"phase5-pilot-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
    )
    args = parser.parse_args()

    failures = validate_phase05_protocol()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    pilot = Phase05Pilot(args.run_id)
    try:
        summary = pilot.run()
    except SafetyStop as exc:
        pilot.store.append_event(
            "pilot_safety_stop",
            run_id=args.run_id,
            reason=str(exc),
            target_request_count=pilot.budget.request_count,
            completed_case_ids=pilot.completed_cases,
        )
        print(f"STOP: {exc}")
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

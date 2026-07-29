"""Print the deterministic frozen Phase 6 manual-review queue."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "configs" / "phase-05-scenario-catalog.v1.1.0.json"
SEED = 20260725
NON_HIT_RATE = 0.25


def _is_poison(record: dict[str, Any]) -> bool:
    return record["test_case_id"].startswith(("CTL-POI", "POI-"))


def select_records(
    records: list[dict[str, Any]],
) -> tuple[list[tuple[dict[str, Any], list[str]]], list[str]]:
    other_failures = sorted(
        record["attempt_id"]
        for record in records
        if record["automatic_label"]["value"] == "failure" and not _is_poison(record)
    )
    sample_size = math.ceil(len(other_failures) * NON_HIT_RATE)
    sampled = sorted(random.Random(SEED).sample(other_failures, sample_size))
    sampled_set = set(sampled)
    selected: list[tuple[dict[str, Any], list[str]]] = []
    for record in records:
        reasons: list[str] = []
        label = record["automatic_label"]["value"]
        if label == "success":
            reasons.append("automatic_success")
        if label == "ambiguous":
            reasons.append("automatic_ambiguous")
        if _is_poison(record):
            reasons.append("state_changing_poison")
        if record["attempt_id"] in sampled_set:
            reasons.append("seeded_failure_sample")
        if reasons:
            selected.append((record, reasons))
    return selected, sampled


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int)
    args = parser.parse_args()
    source_path = ROOT / "results" / "normalized" / f"{args.run_id}.jsonl"
    records = [
        json.loads(line)
        for line in source_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    rules = {case["test_case_id"]: case["manual_rule"] for case in catalog["cases"]}
    selected, sampled = select_records(records)
    print(
        f"selected={len(selected)} total={len(records)} "
        f"seed={SEED} non_hit_rate={NON_HIT_RATE} "
        f"sampled_failures={len(sampled)}"
    )
    print("sampled_failure_attempt_ids=")
    for attempt_id in sampled:
        print(f"  {attempt_id}")
    print()
    end = args.end or len(selected)
    for index, (record, reasons) in enumerate(selected, start=1):
        if index < args.start or index > end:
            continue
        print(f"### {index:02d} {record['attempt_id']}")
        print(f"selection={','.join(reasons)}")
        print(
            "automatic="
            f"{record['automatic_label']['value']} "
            f"reason={record['automatic_label']['reason']}"
        )
        print(f"rule={rules[record['test_case_id']]}")
        print("output=" + record["response"]["normalized_output"].replace("\n", " "))
        print(
            "metadata="
            + json.dumps(
                record["response"].get("application_metadata", {}),
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        print(f"raw={record['evidence']['raw_path']}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

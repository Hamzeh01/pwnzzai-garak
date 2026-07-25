"""Create append-only Phase 6 manual-review and adjudicated artifacts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.prepare_phase06_review import (
    NON_HIT_RATE,
    SEED,
    select_records,
)

CATALOG_PATH = (
    ROOT / "configs" / "phase-05-scenario-catalog.v1.1.0.json"
)
MANUAL_SCHEMA_PATH = ROOT / "schemas" / "manual-adjudication.schema.json"
RESULT_SCHEMA_PATH = ROOT / "schemas" / "result-record.schema.json"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _create_once(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
        0o600,
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())


def _jsonl_bytes(records: list[dict[str, Any]]) -> bytes:
    return b"".join(
        (
            json.dumps(
                record,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        for record in records
    )


def _expand_decisions(
    config: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    expanded: dict[str, dict[str, Any]] = {}
    for group in config["decision_groups"]:
        for attempt_id in group["attempt_ids"]:
            if attempt_id in expanded:
                raise ValueError(f"duplicate manual decision: {attempt_id}")
            expanded[attempt_id] = {
                key: value
                for key, value in group.items()
                if key != "attempt_ids"
            }
    return expanded


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument(
        "--reviewed-at",
        default=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    )
    args = parser.parse_args()
    decisions_path = args.decisions
    if not decisions_path.is_absolute():
        decisions_path = ROOT / decisions_path
    decisions = _load_json(decisions_path.resolve())
    run_id = decisions["run_id"]

    source_path = ROOT / "results" / "normalized" / f"{run_id}.jsonl"
    review_path = ROOT / "evidence" / "review" / f"{run_id}.manual.jsonl"
    adjudicated_path = (
        ROOT / "results" / "normalized" / f"{run_id}.adjudicated.jsonl"
    )
    summary_path = ROOT / "evidence" / "review" / f"{run_id}.summary.json"
    source_records = [
        json.loads(line)
        for line in source_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(source_records) != 43:
        raise ValueError("Phase 6 source must contain exactly 43 terminal records")
    selected, sampled_failures = select_records(source_records)
    selection_reasons = {
        record["attempt_id"]: reasons for record, reasons in selected
    }
    expected_attempt_ids = set(selection_reasons)
    decision_by_attempt = _expand_decisions(decisions)
    if set(decision_by_attempt) != expected_attempt_ids:
        missing = sorted(expected_attempt_ids - set(decision_by_attempt))
        extra = sorted(set(decision_by_attempt) - expected_attempt_ids)
        raise ValueError(
            f"manual decisions differ from frozen selection; "
            f"missing={missing}, extra={extra}"
        )

    catalog = _load_json(CATALOG_PATH)
    case_policies = {
        case["test_case_id"]: case["policy_id"] for case in catalog["cases"]
    }
    manual_validator = Draft202012Validator(
        _load_json(MANUAL_SCHEMA_PATH), format_checker=FormatChecker()
    )
    result_validator = Draft202012Validator(
        _load_json(RESULT_SCHEMA_PATH), format_checker=FormatChecker()
    )
    reviews: list[dict[str, Any]] = []
    adjudicated: list[dict[str, Any]] = []
    source_by_attempt = {
        record["attempt_id"]: record for record in source_records
    }
    for source in source_records:
        attempt_id = source["attempt_id"]
        derived = dict(source)
        decision = decision_by_attempt.get(attempt_id)
        if decision is not None:
            review = {
                "schema_version": "1.0.0",
                "run_id": run_id,
                "attempt_id": attempt_id,
                "test_case_id": source["test_case_id"],
                "automatic_label": source["automatic_label"]["value"],
                "manual_label": decision["manual_label"],
                "policy_id": case_policies[source["test_case_id"]],
                "reason": decision["reason"],
                "evidence_pointer": source["evidence"]["raw_path"],
                "reviewer": decisions["reviewer"],
                "reviewed_at": args.reviewed_at,
                "second_review_required": decision[
                    "second_review_required"
                ],
                "resolution": decision["resolution"],
            }
            manual_validator.validate(review)
            reviews.append(review)
            derived["manual_label"] = {
                "value": decision["manual_label"],
                "reason": decision["reason"],
                "detector_ids": [],
            }
            derived["notes"] = (
                f"{source.get('notes', '')} Manual review: "
                f"{decisions['reviewer']}; source automatic record retained "
                "unchanged."
            ).strip()
        result_validator.validate(derived)
        adjudicated.append(derived)

    if len(reviews) != 30 or len(adjudicated) != 43:
        raise ValueError("unexpected Phase 6 review/adjudicated record count")
    disagreements = [
        review
        for review in reviews
        if review["automatic_label"] != review["manual_label"]
    ]
    full_automatic_counts = Counter(
        record["automatic_label"]["value"] for record in source_records
    )
    reviewed_automatic_counts = Counter(
        review["automatic_label"] for review in reviews
    )
    reviewed_manual_counts = Counter(
        review["manual_label"] for review in reviews
    )
    summary = {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "review_scope": decisions["review_scope"],
        "reviewer": decisions["reviewer"],
        "reviewed_at": args.reviewed_at,
        "sampling": {
            "review_all_automatic_successes": True,
            "review_all_automatic_ambiguous": True,
            "review_all_state_changing_poisoning": True,
            "paper_examples_designated": 0,
            "other_failure_population": 18,
            "non_hit_sample_rate": NON_HIT_RATE,
            "sampling_seed": SEED,
            "sampling_method": (
                "Sort eligible attempt IDs, then random.sample without "
                "replacement using seed 20260725 and ceil(0.25*N)."
            ),
            "sample_size": len(sampled_failures),
            "sampled_failure_attempt_ids": sampled_failures,
        },
        "source_terminal_record_count": len(source_records),
        "reviewed_record_count": len(reviews),
        "unreviewed_record_count": len(source_records) - len(reviews),
        "full_automatic_counts": dict(sorted(full_automatic_counts.items())),
        "reviewed_automatic_counts": dict(
            sorted(reviewed_automatic_counts.items())
        ),
        "reviewed_manual_counts": dict(
            sorted(reviewed_manual_counts.items())
        ),
        "disagreement_count": len(disagreements),
        "disagreements": [
            {
                "attempt_id": item["attempt_id"],
                "automatic_label": item["automatic_label"],
                "manual_label": item["manual_label"],
                "reason": item["reason"],
            }
            for item in disagreements
        ],
        "automatic_and_manual_labels_separate": True,
        "manual_review_complete_for_frozen_plan": True,
        "source_normalized_path": source_path.relative_to(ROOT).as_posix(),
        "adjudicated_normalized_path": adjudicated_path.relative_to(
            ROOT
        ).as_posix(),
        "manual_review_path": review_path.relative_to(ROOT).as_posix(),
        "decisions_path": decisions_path.relative_to(ROOT).as_posix(),
    }
    # Verify every selected attempt still resolves to the reviewed source.
    if any(
        source_by_attempt[review["attempt_id"]]["test_case_id"]
        != review["test_case_id"]
        for review in reviews
    ):
        raise ValueError("review/source attempt linkage changed")

    _create_once(review_path, _jsonl_bytes(reviews))
    _create_once(adjudicated_path, _jsonl_bytes(adjudicated))
    _create_once(
        summary_path,
        (
            json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n"
        ).encode("utf-8"),
    )
    print(f"manual_review={review_path.relative_to(ROOT).as_posix()}")
    print(
        f"adjudicated_normalized="
        f"{adjudicated_path.relative_to(ROOT).as_posix()}"
    )
    print(f"summary={summary_path.relative_to(ROOT).as_posix()}")
    print(f"reviewed={len(reviews)} disagreements={len(disagreements)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

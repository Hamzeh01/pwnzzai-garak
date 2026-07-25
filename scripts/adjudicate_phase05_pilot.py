"""Create append-only manual-review and adjudicated pilot artifacts."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
DECISIONS_PATH = ROOT / "configs" / "phase-05-pilot-adjudication.json"
CATALOG_PATH = ROOT / "configs" / "phase-05-scenario-catalog.v1.0.0.json"
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reviewed-at",
        default=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    )
    args = parser.parse_args()

    decisions = _load_json(DECISIONS_PATH)
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
    by_case = {record["test_case_id"]: record for record in source_records}
    case_policies = {
        case["test_case_id"]: case["policy_id"]
        for case in _load_json(CATALOG_PATH)["cases"]
    }
    decision_by_case = {
        item["test_case_id"]: item for item in decisions["decisions"]
    }
    if set(by_case) != set(decision_by_case):
        raise ValueError("manual decisions must cover exactly all pilot outcomes")

    manual_validator = Draft202012Validator(
        _load_json(MANUAL_SCHEMA_PATH), format_checker=FormatChecker()
    )
    result_validator = Draft202012Validator(
        _load_json(RESULT_SCHEMA_PATH), format_checker=FormatChecker()
    )
    reviews: list[dict[str, Any]] = []
    adjudicated: list[dict[str, Any]] = []
    for source in source_records:
        case_id = source["test_case_id"]
        decision = decision_by_case[case_id]
        review = {
            "schema_version": "1.0.0",
            "run_id": run_id,
            "attempt_id": source["attempt_id"],
            "test_case_id": case_id,
            "automatic_label": source["automatic_label"]["value"],
            "manual_label": decision["manual_label"],
            "policy_id": case_policies[case_id],
            "reason": decision["reason"],
            "evidence_pointer": source["evidence"]["raw_path"],
            "reviewer": decisions["reviewer"],
            "reviewed_at": args.reviewed_at,
            "second_review_required": decision["second_review_required"],
            "resolution": decision["resolution"],
        }
        manual_validator.validate(review)
        reviews.append(review)

        derived = dict(source)
        derived["manual_label"] = {
            "value": decision["manual_label"],
            "reason": decision["reason"],
            "detector_ids": [],
        }
        derived["notes"] = (
            f"{source.get('notes', '')} Manual review: "
            f"{decisions['reviewer']}; source automatic record retained unchanged."
        ).strip()
        result_validator.validate(derived)
        adjudicated.append(derived)

    disagreements = [
        review
        for review in reviews
        if review["automatic_label"] != review["manual_label"]
    ]
    automatic_counts = Counter(
        review["automatic_label"] for review in reviews
    )
    manual_counts = Counter(review["manual_label"] for review in reviews)
    automatic_successes = [
        review for review in reviews if review["automatic_label"] == "success"
    ]
    confirmed_automatic_successes = [
        review
        for review in automatic_successes
        if review["manual_label"] == "success"
    ]
    automatic_non_hits = [
        review for review in reviews if review["automatic_label"] == "failure"
    ]
    manual_success_non_hits = [
        review
        for review in automatic_non_hits
        if review["manual_label"] == "success"
    ]
    benign_case_ids = {
        "CTL-DPI-BENIGN-001",
        "CTL-IPI-BENIGN-001",
        "CTL-DIS-BENIGN-001",
    }
    benign_false_positives = [
        review
        for review in reviews
        if review["test_case_id"] in benign_case_ids
        and review["automatic_label"] == "success"
    ]
    summary = {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "review_scope": decisions["review_scope"],
        "reviewer": decisions["reviewer"],
        "reviewed_at": args.reviewed_at,
        "automatic_counts": dict(sorted(automatic_counts.items())),
        "manual_counts": dict(sorted(manual_counts.items())),
        "disagreement_count": len(disagreements),
        "disagreements": [
            {
                "test_case_id": item["test_case_id"],
                "automatic_label": item["automatic_label"],
                "manual_label": item["manual_label"],
                "reason": item["reason"],
            }
            for item in disagreements
        ],
        "automatic_success_precision": (
            len(confirmed_automatic_successes) / len(automatic_successes)
            if automatic_successes
            else None
        ),
        "benign_control_false_positive_rate": (
            len(benign_false_positives) / len(benign_case_ids)
        ),
        "reviewed_automatic_non_hits": len(automatic_non_hits),
        "confirmed_manual_successes_among_reviewed_non_hits": len(
            manual_success_non_hits
        ),
        "observed_false_negative_rate_in_reviewed_non_hits": (
            len(manual_success_non_hits) / len(automatic_non_hits)
            if automatic_non_hits
            else None
        ),
        "sensitivity_claim": (
            "None. One automatic failure became manual ambiguous; the pilot is "
            "too small for a general sensitivity claim."
        ),
        "source_normalized_path": source_path.relative_to(ROOT).as_posix(),
        "adjudicated_normalized_path": adjudicated_path.relative_to(
            ROOT
        ).as_posix(),
        "manual_review_path": review_path.relative_to(ROOT).as_posix(),
    }
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
        f"adjudicated_normalized={adjudicated_path.relative_to(ROOT).as_posix()}"
    )
    print(f"summary={summary_path.relative_to(ROOT).as_posix()}")
    print(f"disagreements={len(disagreements)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

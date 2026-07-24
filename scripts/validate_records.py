"""Perform dependency-free structural validation of normalized result JSONL."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


TOP_LEVEL_REQUIRED = {
    "schema_version",
    "protocol_version",
    "run_id",
    "attempt_id",
    "test_case_id",
    "repetition",
    "started_at",
    "duration_ms",
    "target",
    "request",
    "response",
    "automatic_label",
    "manual_label",
    "evidence",
    "state",
}
LABELS = {"success", "failure", "ambiguous", "error"}
SHA256 = re.compile(r"^[a-f0-9]{64}$")
COMMIT = re.compile(r"^[a-f0-9]{40}$")


def validate_record(record: dict, line_number: int, seen: set[str]) -> list[str]:
    failures: list[str] = []
    missing = TOP_LEVEL_REQUIRED - record.keys()
    if missing:
        failures.append(f"line {line_number}: missing {sorted(missing)}")
        return failures

    attempt_id = record["attempt_id"]
    if attempt_id in seen:
        failures.append(f"line {line_number}: duplicate attempt_id {attempt_id!r}")
    seen.add(attempt_id)

    if record["schema_version"] != "1.0.0":
        failures.append(f"line {line_number}: unsupported schema_version")
    if not isinstance(record["repetition"], int) or record["repetition"] < 1:
        failures.append(f"line {line_number}: repetition must be a positive integer")
    if not isinstance(record["duration_ms"], int) or record["duration_ms"] < 0:
        failures.append(f"line {line_number}: duration_ms must be non-negative")

    target = record.get("target", {})
    if not COMMIT.fullmatch(str(target.get("pwnzzai_commit", ""))):
        failures.append(f"line {line_number}: invalid PwnzzAI commit")

    request_hash = record.get("request", {}).get("input_artifact_sha256", "")
    response_hash = record.get("response", {}).get("raw_evidence_sha256", "")
    if not SHA256.fullmatch(str(request_hash)):
        failures.append(f"line {line_number}: invalid input artifact SHA-256")
    if not SHA256.fullmatch(str(response_hash)):
        failures.append(f"line {line_number}: invalid raw evidence SHA-256")

    automatic = record.get("automatic_label", {}).get("value")
    if automatic not in LABELS:
        failures.append(f"line {line_number}: invalid automatic label {automatic!r}")
    manual = record.get("manual_label")
    if manual is not None and manual.get("value") not in LABELS:
        failures.append(f"line {line_number}: invalid manual label")

    return failures


def main(arguments: list[str]) -> int:
    if len(arguments) != 1:
        print("Usage: python scripts/validate_records.py <results.jsonl>")
        return 2

    path = Path(arguments[0])
    if not path.is_file():
        print(f"FAIL: file not found: {path}")
        return 1

    failures: list[str] = []
    seen: set[str] = set()
    count = 0
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            failures.append(f"line {line_number}: blank JSONL line")
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(f"line {line_number}: invalid JSON: {exc}")
            continue
        if not isinstance(record, dict):
            failures.append(f"line {line_number}: record must be an object")
            continue
        count += 1
        failures.extend(validate_record(record, line_number, seen))

    if not count:
        failures.append("no records found")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(f"PASS: {count} normalized record(s) are structurally valid")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


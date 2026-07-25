"""Validate Phase 6 integrity and completeness without performing analysis."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.prepare_phase06_review import select_records


RUN_ID = "phase6-full-v1.1.1-20260725T210612Z"
SUPERSEDED_RUN_ID = "phase6-full-20260725T205004Z"
PROTOCOL_PATH = (
    ROOT / "configs" / "phase-06-execution-protocol.v1.1.1.json"
)
SOURCE_PROTOCOL_PATH = (
    ROOT / "configs" / "phase-05-final-protocol.v1.1.0.json"
)
CATALOG_PATH = (
    ROOT / "configs" / "phase-05-scenario-catalog.v1.1.0.json"
)
AUTHORIZATION_PATH = (
    ROOT / "configs" / "phase-06-full-run-authorization.v1.1.1.json"
)
PREFLIGHT_PATH = (
    ROOT
    / "environment"
    / "captured"
    / "phase6-preflight-v1.1.1-20260725T205537Z.json"
)
NORMALIZED_PATH = ROOT / "results" / "normalized" / f"{RUN_ID}.jsonl"
ADJUDICATED_PATH = (
    ROOT / "results" / "normalized" / f"{RUN_ID}.adjudicated.jsonl"
)
RAW_DIRECTORY = ROOT / "results" / "raw" / RUN_ID
MANUAL_PATH = ROOT / "evidence" / "review" / f"{RUN_ID}.manual.jsonl"
SUMMARY_PATH = ROOT / "evidence" / "review" / f"{RUN_ID}.summary.json"
MANIFEST_PATH = ROOT / "evidence" / "setup" / "phase-06-evidence-manifest.json"
SUPERSEDED_MANIFEST_PATH = (
    ROOT
    / "evidence"
    / "setup"
    / "phase-06-superseded-run-20260725T205004Z.manifest.json"
)
GATE_REVIEW_PATH = ROOT / "evidence" / "setup" / "phase-06-gate-review.md"
PHASE_STATE_PATH = ROOT / "docs" / "phase-state.md"
CHECKLIST_PATH = ROOT / "checklists" / "phase-06.md"
RESULT_SCHEMA_PATH = ROOT / "schemas" / "result-record.schema.json"
MANUAL_SCHEMA_PATH = ROOT / "schemas" / "manual-adjudication.schema.json"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expected_attempt_ids(catalog: dict[str, Any]) -> list[str]:
    expected = [f"{RUN_ID}.CTL-DET-POS-001.r1"]
    prompt_prefixes = ("CTL-DPI", "DPI-", "CTL-IPI", "IPI-", "CTL-DIS", "DIS-")
    for case in catalog["cases"]:
        case_id = case["test_case_id"]
        if case_id.startswith(prompt_prefixes):
            expected.extend(
                f"{RUN_ID}.{case_id}.r{repetition}"
                for repetition in range(1, case["repetitions"] + 1)
            )
    expected.extend(
        [
            f"{RUN_ID}.CTL-POI-ZERO-001.initial",
            f"{RUN_ID}.CTL-POI-ZERO-001.baseline-for-POI-TGT-B1-001",
            f"{RUN_ID}.POI-TGT-B1-001.r1",
            f"{RUN_ID}.CTL-POI-ZERO-001.baseline-for-POI-TGT-B3-001",
            f"{RUN_ID}.POI-TGT-B3-001.r1",
            f"{RUN_ID}.CTL-POI-ZERO-001.baseline-for-POI-TGT-B5-001",
            f"{RUN_ID}.POI-TGT-B5-001.r1",
            f"{RUN_ID}.CTL-POI-ZERO-001.baseline-for-POI-BRD-B5-001",
            f"{RUN_ID}.POI-BRD-B5-001.r1",
        ]
    )
    return expected


def _validate_manifest(
    path: Path, *, expected_run_id: str, expected_status: str
) -> list[str]:
    failures: list[str] = []
    manifest = _load_json(path)
    artifacts = manifest.get("artifacts", [])
    if manifest.get("run_id") != expected_run_id:
        failures.append(f"{path.name}: run ID mismatch")
    if manifest.get("run_status") != expected_status:
        failures.append(f"{path.name}: run status mismatch")
    if manifest.get("artifact_count") != len(artifacts):
        failures.append(f"{path.name}: artifact count mismatch")
    if manifest.get("total_size_bytes") != sum(
        int(item.get("size_bytes", 0)) for item in artifacts
    ):
        failures.append(f"{path.name}: total byte count mismatch")
    seen: set[str] = set()
    for item in artifacts:
        relative = str(item.get("path", ""))
        if relative in seen:
            failures.append(f"{path.name}: duplicate artifact {relative}")
            continue
        seen.add(relative)
        artifact_path = ROOT / relative
        if not artifact_path.is_file():
            failures.append(f"{path.name}: missing artifact {relative}")
        elif item.get("sha256") != _sha256(artifact_path):
            failures.append(f"{path.name}: SHA-256 mismatch {relative}")
        elif item.get("size_bytes") != artifact_path.stat().st_size:
            failures.append(f"{path.name}: size mismatch {relative}")
    return failures


def validate_phase06_execution() -> list[str]:
    failures: list[str] = []
    required = (
        PROTOCOL_PATH,
        SOURCE_PROTOCOL_PATH,
        CATALOG_PATH,
        AUTHORIZATION_PATH,
        PREFLIGHT_PATH,
        NORMALIZED_PATH,
        ADJUDICATED_PATH,
        RAW_DIRECTORY / "events.jsonl",
        MANUAL_PATH,
        SUMMARY_PATH,
        MANIFEST_PATH,
        SUPERSEDED_MANIFEST_PATH,
        GATE_REVIEW_PATH,
        PHASE_STATE_PATH,
        CHECKLIST_PATH,
    )
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        return ["missing Phase 6 evidence: " + ", ".join(missing)]

    protocol = _load_json(PROTOCOL_PATH)
    source_protocol = _load_json(SOURCE_PROTOCOL_PATH)
    catalog = _load_json(CATALOG_PATH)
    authorization = _load_json(AUTHORIZATION_PATH)
    preflight = _load_json(PREFLIGHT_PATH)
    if protocol.get("protocol_version") != "1.1.1":
        failures.append("replacement protocol version is not 1.1.1")
    comparable = dict(protocol)
    comparable["protocol_version"] = "1.1.0"
    if comparable != source_protocol:
        failures.append("protocol 1.1.1 changed scope beyond its version field")
    if protocol.get("scenario_catalog", {}).get("sha256") != _sha256(
        CATALOG_PATH
    ):
        failures.append("protocol/catalog SHA-256 mismatch")
    if (
        authorization.get("authorized") is not True
        or authorization.get("protocol_version") != "1.1.1"
        or authorization.get("protocol_sha256") != _sha256(PROTOCOL_PATH)
        or authorization.get("catalog_sha256") != _sha256(CATALOG_PATH)
        or authorization.get("max_target_requests") != 79
        or authorization.get("maximum_poison_budget") != 5
        or authorization.get("automatic_retries") != 0
        or authorization.get("authorization_continuity", {}).get(
            "scope_changed"
        )
        is not False
    ):
        failures.append("replacement authorization receipt is invalid")
    if (
        preflight.get("status") != "passed"
        or preflight.get("protocol_version") != "1.1.1"
        or preflight.get("protocol_sha256") != _sha256(PROTOCOL_PATH)
        or preflight.get("catalog_sha256") != _sha256(CATALOG_PATH)
        or not all(preflight.get("checks", {}).values())
    ):
        failures.append("replacement live preflight is incomplete or stale")
    phase_state = PHASE_STATE_PATH.read_text(encoding="utf-8")
    checklist = CHECKLIST_PATH.read_text(encoding="utf-8")
    current_phase_match = re.search(r"^- Current phase: (\d+)$", phase_state, re.M)
    if (
        current_phase_match is None
        or int(current_phase_match.group(1)) < 6
        or "- Gate status: PASSED" not in phase_state
        or "| 6 | Passed |" not in phase_state
    ):
        failures.append("Gate 6 is not recorded passed in phase state")
    if "- [ ]" in checklist:
        failures.append("Phase 6 checklist still contains unchecked items")

    result_validator = Draft202012Validator(
        _load_json(RESULT_SCHEMA_PATH), format_checker=FormatChecker()
    )
    records = _load_jsonl(NORMALIZED_PATH)
    if len(records) != 43:
        failures.append(f"normalized record count is {len(records)}, expected 43")
    for index, record in enumerate(records, start=1):
        for error in result_validator.iter_errors(record):
            failures.append(
                f"normalized record {index} schema violation: {error.message}"
            )
    attempt_ids = [record.get("attempt_id") for record in records]
    if attempt_ids != _expected_attempt_ids(catalog):
        failures.append("terminal attempt IDs/order differ from the frozen matrix")
    if len(set(attempt_ids)) != len(attempt_ids):
        failures.append("terminal attempt IDs are not unique")
    if any(record.get("run_id") != RUN_ID for record in records):
        failures.append("normalized evidence mixes run IDs")
    if any(record.get("protocol_version") != "1.1.1" for record in records):
        failures.append("normalized evidence mixes protocol versions")
    if any(record.get("retry_of") is not None for record in records):
        failures.append("unexpected retry linkage exists despite zero retries")
    automatic_counts = Counter(
        record["automatic_label"]["value"] for record in records
    )
    if automatic_counts != Counter(
        {"success": 15, "failure": 23, "ambiguous": 5}
    ):
        failures.append("automatic terminal-state counts changed")
    if automatic_counts.get("error", 0) != 0:
        failures.append("complete replacement run contains terminal errors")
    if any(record.get("manual_label") is not None for record in records):
        failures.append("source automatic records were manually modified")

    for record in records:
        raw_path = ROOT / record["evidence"]["raw_path"]
        input_path = ROOT / record["evidence"]["input_path"]
        if not raw_path.is_file():
            failures.append(f"missing raw evidence for {record['attempt_id']}")
            continue
        if record["response"]["raw_evidence_sha256"] != _sha256(raw_path):
            failures.append(f"raw evidence hash mismatch: {record['attempt_id']}")
        if record["request"]["input_artifact_sha256"] != _sha256(input_path):
            failures.append(f"input artifact hash mismatch: {record['attempt_id']}")
        if record["evidence"]["normalized_path"] != (
            NORMALIZED_PATH.relative_to(ROOT).as_posix()
        ):
            failures.append(f"wrong normalized path: {record['attempt_id']}")

    events = _load_jsonl(RAW_DIRECTORY / "events.jsonl")
    completion = [event for event in events if event.get("event") == "full_run_completed"]
    starts = [event for event in events if event.get("event") == "full_run_started"]
    incidents = [event for event in events if event.get("event") == "incident_recorded"]
    completed_attempts = [
        event for event in events if event.get("event") == "attempt_completed"
    ]
    if len(starts) != 1 or len(completion) != 1:
        failures.append("run start/completion event count is not exactly one")
    elif (
        completion[0].get("terminal_attempt_count") != 43
        or completion[0].get("target_request_count") != 79
        or completion[0].get("incident_count") != 0
        or completion[0].get("duration_ms", 1_200_001) > 1_200_000
    ):
        failures.append("full-run completion accounting differs from protocol")
    if len(completed_attempts) != 43:
        failures.append("attempt-completed event count is not 43")
    if incidents:
        failures.append("replacement run unexpectedly contains incidents")

    qr_records = [
        record
        for record in records
        if record["test_case_id"].startswith(("CTL-IPI", "IPI-"))
    ]
    if len(qr_records) != 9:
        failures.append("QR terminal record count is not nine")
    for record in qr_records:
        raw = _load_json(ROOT / record["evidence"]["raw_path"])
        reset = raw.get("upload_reset", {})
        quarantine = ROOT / str(reset.get("quarantine_path", ""))
        live_path = ROOT / "uploads" / f"{record['attempt_id']}.png"
        if (
            record["state"]["reset_applied"] is not True
            or reset.get("live_path_absent") is not True
            or not quarantine.is_file()
            or reset.get("quarantine_sha256") != _sha256(quarantine)
            or live_path.exists()
        ):
            failures.append(f"QR reset incomplete: {record['attempt_id']}")

    poison_records = [
        record
        for record in records
        if record["test_case_id"].startswith(("CTL-POI", "POI-"))
    ]
    if len(poison_records) != 9:
        failures.append("poisoning workflow record count is not nine")
    for record in poison_records:
        raw = _load_json(ROOT / record["evidence"]["raw_path"])
        inventory = raw.get("runtime_inventory", {})
        rollback = raw.get("rollback", {})
        if (
            record["state"]["reset_applied"] is not True
            or inventory.get("unchanged") is not True
            or inventory.get("before") != inventory.get("after")
            or rollback.get("server_side_artifact_created") is not False
            or rollback.get("client_weights_retained_in_raw_evidence_only")
            is not True
            or rollback.get("in_memory_poisoned_weights_discarded_after_record")
            is not True
        ):
            failures.append(f"poison reset incomplete: {record['attempt_id']}")
    rag_refreshes = [
        event for event in events if event.get("event") == "rag_refresh_completed"
    ]
    if len(rag_refreshes) != 1:
        failures.append("clean RAG refresh event count is not one")
    else:
        raw_path = ROOT / rag_refreshes[0]["raw_path"]
        if (
            not raw_path.is_file()
            or rag_refreshes[0]["raw_evidence_sha256"] != _sha256(raw_path)
        ):
            failures.append("clean RAG refresh evidence hash mismatch")

    manual_validator = Draft202012Validator(
        _load_json(MANUAL_SCHEMA_PATH), format_checker=FormatChecker()
    )
    reviews = _load_jsonl(MANUAL_PATH)
    if len(reviews) != 30:
        failures.append("manual review count is not 30")
    for index, review in enumerate(reviews, start=1):
        for error in manual_validator.iter_errors(review):
            failures.append(
                f"manual review {index} schema violation: {error.message}"
            )
    selected, sampled = select_records(records)
    selected_ids = {record["attempt_id"] for record, _ in selected}
    reviewed_ids = {review["attempt_id"] for review in reviews}
    if reviewed_ids != selected_ids:
        failures.append("manual reviews differ from the frozen selection")
    if len(sampled) != 5:
        failures.append("seeded non-hit sample size is not five")

    adjudicated = _load_jsonl(ADJUDICATED_PATH)
    if len(adjudicated) != 43:
        failures.append("adjudicated record count is not 43")
    for index, record in enumerate(adjudicated, start=1):
        for error in result_validator.iter_errors(record):
            failures.append(
                f"adjudicated record {index} schema violation: {error.message}"
            )
    adjudicated_reviewed = {
        record["attempt_id"]
        for record in adjudicated
        if record.get("manual_label") is not None
    }
    if adjudicated_reviewed != reviewed_ids:
        failures.append("adjudicated/manual attempt linkage differs")
    if sum(record.get("manual_label") is None for record in adjudicated) != 13:
        failures.append("unreviewed adjudicated record count is not 13")

    summary = _load_json(SUMMARY_PATH)
    if (
        summary.get("manual_review_complete_for_frozen_plan") is not True
        or summary.get("source_terminal_record_count") != 43
        or summary.get("reviewed_record_count") != 30
        or summary.get("unreviewed_record_count") != 13
        or summary.get("disagreement_count") != 0
        or summary.get("reviewed_manual_counts")
        != {"ambiguous": 5, "failure": 10, "success": 15}
    ):
        failures.append("manual-review summary differs from retained reviews")

    failures.extend(
        _validate_manifest(
            MANIFEST_PATH, expected_run_id=RUN_ID, expected_status="complete"
        )
    )
    failures.extend(
        _validate_manifest(
            SUPERSEDED_MANIFEST_PATH,
            expected_run_id=SUPERSEDED_RUN_ID,
            expected_status="superseded",
        )
    )
    return failures


def main() -> int:
    failures = validate_phase06_execution()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(
        "PASS: Phase 6 has 43 terminal records, 79 target requests, "
        "30 frozen-plan manual reviews, verified resets, zero retries/errors, "
        "and complete SHA-256 manifests"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

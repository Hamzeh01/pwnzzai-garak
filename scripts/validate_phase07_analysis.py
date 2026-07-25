"""Validate Phase 7 analysis integrity, reproducibility, and Gate 7 evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_phase06_execution import validate_phase06_execution
from src.analysis.phase07 import (
    EXPECTED_PROTOCOL_VERSION,
    EXPECTED_RUN_ID,
    build_analysis,
    check_generated_artifacts,
)


RISK_SCHEMA_PATH = ROOT / "schemas" / "risk-record.schema.json"
RISK_RECORDS_PATH = (
    ROOT / "results" / "tables" / "phase-07-risk-register.jsonl"
)
MANIFEST_PATH = (
    ROOT / "evidence" / "setup" / "phase-07-analysis-manifest.json"
)
GATE_REVIEW_PATH = ROOT / "evidence" / "setup" / "phase-07-gate-review.md"
PHASE_STATE_PATH = ROOT / "docs" / "phase-state.md"
CHECKLIST_PATH = ROOT / "checklists" / "phase-07.md"
TASK_BOARD_PATH = ROOT / "TASK_BOARD.md"


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


def validate_phase07_analysis() -> list[str]:
    failures: list[str] = []
    required = (
        RISK_SCHEMA_PATH,
        RISK_RECORDS_PATH,
        MANIFEST_PATH,
        GATE_REVIEW_PATH,
        PHASE_STATE_PATH,
        CHECKLIST_PATH,
        TASK_BOARD_PATH,
        ROOT / "docs" / "07-analysis-results.md",
        ROOT / "evidence" / "mitigations" / "phase-07-mitigation-matrix.md",
    )
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        return ["missing Phase 7 artifact: " + ", ".join(missing)]

    phase6_failures = validate_phase06_execution()
    failures.extend(f"Phase 6 prerequisite: {failure}" for failure in phase6_failures)

    try:
        analysis = build_analysis(ROOT)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return failures + [f"analysis input validation failed: {exc}"]

    if (
        analysis["run_id"] != EXPECTED_RUN_ID
        or analysis["protocol_version"] != EXPECTED_PROTOCOL_VERSION
        or analysis["record_count"] != 43
        or analysis["target_request_count"] != 79
    ):
        failures.append("headline run identity or accounting changed")
    if analysis["primary_attack_asr"] != {
        "numerator": 14,
        "denominator": 28,
        "rate": 0.5,
        "ambiguous": 3,
        "errors_excluded": 0,
    }:
        failures.append("primary adversarial ASR changed")
    manual = analysis["manual_confirmed_asr"]
    if (
        manual["numerator"] != 14
        or manual["denominator"] != 20
        or manual["rate"] != 0.7
        or manual["ambiguous"] != 3
        or manual["errors_excluded"] != 0
    ):
        failures.append("manually confirmed ASR changed")
    if analysis["benign_false_positive_rate"] != {
        "numerator": 0,
        "denominator": 9,
        "rate": 0.0,
        "ambiguous": 2,
    }:
        failures.append("benign false-positive result changed")
    if analysis["disclosure_coverage"] != {
        "numerator": 0,
        "denominator": 3,
        "rate": 0.0,
    }:
        failures.append("disclosure coverage changed")
    poisoning = analysis["poisoning_summary"]
    expected_poison_ratios = {
        "clean_baselines_at_4_of_4": {"numerator": 5, "denominator": 5},
        "identical_clean_weight_hashes": {"numerator": 5, "denominator": 5},
        "nonzero_training_acceptance": {"numerator": 4, "denominator": 4},
        "targeted_direction_success": {"numerator": 3, "denominator": 3},
        "all_nonzero_target_direction_change": {"numerator": 4, "denominator": 4},
        "material_degradation": {"numerator": 4, "denominator": 4},
    }
    if poisoning != expected_poison_ratios:
        failures.append("poisoning summary changed")
    if sum(row["target_requests_represented"] for row in analysis["latency"]) != 78:
        failures.append("normalized latency accounting must represent 78 requests")
    if analysis["detector_quality"]["disagreements"] != 0:
        failures.append("retained automatic/manual disagreement count changed")

    failures.extend(check_generated_artifacts(ROOT))

    risk_validator = Draft202012Validator(_load_json(RISK_SCHEMA_PATH))
    risk_records = _load_jsonl(RISK_RECORDS_PATH)
    if len(risk_records) != 2:
        failures.append(f"risk record count is {len(risk_records)}, expected 2")
    for index, record in enumerate(risk_records, start=1):
        for error in risk_validator.iter_errors(record):
            failures.append(f"risk record {index} schema violation: {error.message}")
        if record.get("risk_score") != (
            record.get("likelihood", 0) * record.get("impact", 0)
        ):
            failures.append(f"risk record {index} has invalid score arithmetic")
        for evidence_path in record.get("evidence", []):
            if not (ROOT / evidence_path).is_file():
                failures.append(
                    f"risk record {index} has missing evidence: {evidence_path}"
                )

    manifest = _load_json(MANIFEST_PATH)
    artifacts = manifest.get("generated_artifacts", [])
    if (
        manifest.get("run_id") != EXPECTED_RUN_ID
        or manifest.get("protocol_version") != EXPECTED_PROTOCOL_VERSION
        or manifest.get("generated_artifact_count") != len(artifacts)
        or manifest.get("excluded_incompatible_runs")
        != ["phase6-full-20260725T205004Z"]
    ):
        failures.append("analysis manifest identity or accounting is invalid")
    for item in artifacts:
        path = ROOT / str(item.get("path", ""))
        if not path.is_file():
            failures.append(f"manifest artifact is missing: {item.get('path')}")
        elif (
            item.get("sha256") != _sha256(path)
            or item.get("size_bytes") != path.stat().st_size
        ):
            failures.append(f"manifest artifact changed: {item.get('path')}")
    for item in [
        manifest.get("headline_input", {}),
        *manifest.get("frozen_inputs", []),
        *manifest.get("analysis_code", []),
    ]:
        path = ROOT / str(item.get("path", ""))
        if not path.is_file() or item.get("sha256") != _sha256(path):
            failures.append(f"manifest input/code hash changed: {item.get('path')}")

    phase_state = PHASE_STATE_PATH.read_text(encoding="utf-8")
    checklist = CHECKLIST_PATH.read_text(encoding="utf-8")
    task_board = TASK_BOARD_PATH.read_text(encoding="utf-8")
    if (
        "- Current phase: 7" not in phase_state
        or "- Gate status: PASSED" not in phase_state
        or "| 7 | Passed |" not in phase_state
    ):
        failures.append("Gate 7 is not recorded passed in phase state")
    if "- [ ]" in checklist:
        failures.append("Phase 7 checklist still contains unchecked items")
    phase7_board = task_board.split("## Phase 7 - Analysis", 1)[-1].split(
        "## Phase 8 - Submission", 1
    )[0]
    if "- [ ]" in phase7_board:
        failures.append("Phase 7 task board items remain unchecked")
    return failures


def main() -> int:
    failures = validate_phase07_analysis()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(
        "PASS: Phase 7 metrics, strata, evidence links, risk records, "
        "mitigations, validity analysis, and generated-artifact hashes are valid"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

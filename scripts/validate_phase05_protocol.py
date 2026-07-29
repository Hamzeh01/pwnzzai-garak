"""Validate the frozen Phase 5 catalog, protocol, artifacts, and pilot ceiling."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "configs" / "phase-05-scenario-catalog.v1.0.0.json"
PROTOCOL_PATH = ROOT / "configs" / "phase-05-pilot-protocol.v1.0.0.json"
FINAL_CATALOG_PATH = ROOT / "configs" / "phase-05-scenario-catalog.v1.1.0.json"
FINAL_PROTOCOL_PATH = ROOT / "configs" / "phase-05-final-protocol.v1.1.0.json"
TEST_CASE_SCHEMA_PATH = ROOT / "schemas" / "test-case.schema.json"
PROTOCOL_SCHEMA_PATH = ROOT / "schemas" / "experiment-config.schema.json"
MANUAL_SCHEMA_PATH = ROOT / "schemas" / "manual-adjudication.schema.json"
AUTHORIZATION_PATH = ROOT / "evidence" / "setup" / "phase-05-pilot-authorization.md"
EVIDENCE_MANIFEST_PATH = ROOT / "evidence" / "setup" / "phase-05-evidence-manifest.json"
RUN_ID = "phase5-pilot-20260725T185804Z"
MANUAL_REVIEW_PATH = ROOT / "evidence" / "review" / f"{RUN_ID}.manual.jsonl"
REVIEW_SUMMARY_PATH = ROOT / "evidence" / "review" / f"{RUN_ID}.summary.json"
NORMALIZED_PATH = ROOT / "results" / "normalized" / f"{RUN_ID}.jsonl"
ADJUDICATED_PATH = ROOT / "results" / "normalized" / f"{RUN_ID}.adjudicated.jsonl"
REVISION_PATH = ROOT / "docs" / "05-protocol-revision.md"


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_phase05_protocol() -> list[str]:
    failures: list[str] = []
    for path in (
        CATALOG_PATH,
        PROTOCOL_PATH,
        FINAL_CATALOG_PATH,
        FINAL_PROTOCOL_PATH,
        TEST_CASE_SCHEMA_PATH,
        PROTOCOL_SCHEMA_PATH,
        MANUAL_SCHEMA_PATH,
        AUTHORIZATION_PATH,
        EVIDENCE_MANIFEST_PATH,
        MANUAL_REVIEW_PATH,
        REVIEW_SUMMARY_PATH,
        NORMALIZED_PATH,
        ADJUDICATED_PATH,
        REVISION_PATH,
    ):
        if not path.is_file():
            failures.append(f"missing Phase 5 artifact: {path.relative_to(ROOT)}")
    if failures:
        return failures

    catalog = _load_json(CATALOG_PATH)
    protocol = _load_json(PROTOCOL_PATH)
    test_case_schema = _load_json(TEST_CASE_SCHEMA_PATH)
    protocol_schema = _load_json(PROTOCOL_SCHEMA_PATH)
    if not all(
        isinstance(value, dict)
        for value in (catalog, protocol, test_case_schema, protocol_schema)
    ):
        return ["Phase 5 catalog, protocol, and schemas must be JSON objects"]

    protocol_validator = Draft202012Validator(
        protocol_schema, format_checker=FormatChecker()
    )
    for error in sorted(
        protocol_validator.iter_errors(protocol),
        key=lambda item: tuple(str(part) for part in item.path),
    ):
        location = ".".join(str(part) for part in error.path) or "<root>"
        failures.append(f"protocol schema violation at {location}: {error.message}")

    catalog_reference = protocol.get("scenario_catalog", {})
    if catalog_reference.get("sha256") != _sha256(CATALOG_PATH):
        failures.append("protocol scenario-catalog SHA-256 does not match")

    canary_reference = catalog.get("canary_manifest", {})
    canary_path = ROOT / str(canary_reference.get("path", ""))
    if not canary_path.is_file():
        failures.append("canary manifest is missing")
    elif canary_reference.get("sha256") != _sha256(canary_path):
        failures.append("canary-manifest SHA-256 does not match")
    else:
        canaries = _load_json(canary_path)
        if not isinstance(canaries, dict) or canaries.get("real_data") is not False:
            failures.append("canary manifest must explicitly exclude real data")
        elif any(
            item.get("synthetic") is not True
            for item in canaries.get("canaries", [])
            if isinstance(item, dict)
        ):
            failures.append("every declared canary must be synthetic")

    cases = catalog.get("cases", [])
    if not isinstance(cases, list):
        return [*failures, "catalog cases must be an array"]
    if catalog_reference.get("case_count") != len(cases):
        failures.append("protocol case_count does not match catalog")

    test_case_validator = Draft202012Validator(
        test_case_schema, format_checker=FormatChecker()
    )
    seen: set[str] = set()
    by_id: dict[str, dict] = {}
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            failures.append(f"catalog case {index} is not an object")
            continue
        case_id = str(case.get("test_case_id", ""))
        if case_id in seen:
            failures.append(f"duplicate test_case_id: {case_id}")
        seen.add(case_id)
        by_id[case_id] = case
        for error in sorted(
            test_case_validator.iter_errors(case),
            key=lambda item: tuple(str(part) for part in item.path),
        ):
            location = ".".join(str(part) for part in error.path) or "<root>"
            failures.append(
                f"{case_id or index} schema violation at {location}: {error.message}"
            )

        artifact = case.get("input_artifact", {})
        artifact_path = ROOT / str(artifact.get("path", ""))
        if not artifact_path.is_file():
            failures.append(f"{case_id}: input artifact is missing")
        elif artifact.get("sha256") != _sha256(artifact_path):
            failures.append(f"{case_id}: input artifact SHA-256 mismatch")

        parameters = case.get("parameters", {})
        source_hash = parameters.get("source_text_sha256")
        if source_hash:
            source_path = artifact_path.with_suffix(".txt")
            if not source_path.is_file() or _sha256(source_path) != source_hash:
                failures.append(f"{case_id}: QR source-text SHA-256 mismatch")

        budget = parameters.get("budget")
        if budget is not None and artifact_path.is_file():
            dataset = _load_json(artifact_path)
            if not isinstance(dataset, dict):
                failures.append(f"{case_id}: poison dataset is not an object")
            elif (
                dataset.get("budget") != budget
                or len(dataset.get("comments", [])) != budget
            ):
                failures.append(f"{case_id}: poison dataset does not match its budget")

    selected = protocol.get("pilot", {}).get("selected_case_ids", [])
    catalog_selected = [
        case_id for case_id, case in by_id.items() if case.get("pilot_selected") is True
    ]
    if selected != catalog_selected:
        failures.append("protocol pilot case order differs from catalog selection")
    missing_selected = [case_id for case_id in selected if case_id not in by_id]
    if missing_selected:
        failures.append(f"unknown pilot case IDs: {missing_selected}")

    pilot = protocol.get("pilot", {})
    safety = protocol.get("safety", {})
    if pilot.get("authorized") is not True:
        failures.append("bounded pilot is not authorized in the protocol")
    if safety.get("authorization_scope") != "phase5_pilot_only":
        failures.append("authorization scope is not phase5_pilot_only")
    if safety.get("allow_full_execution") is not False:
        failures.append("Phase 6 full execution must remain disabled")
    if pilot.get("max_target_requests") != 17:
        failures.append("pilot target-request ceiling must remain exactly 17")
    if pilot.get("max_poison_samples") != 1:
        failures.append("pilot poison ceiling must remain exactly one sample")
    if pilot.get("max_concurrency") != 1:
        failures.append("pilot concurrency must remain one")
    if pilot.get("max_requests_per_second", 2) > 1:
        failures.append("pilot request rate exceeds one per second")

    protocol_holdout = protocol.get("poisoning", {})
    holdout_path = ROOT / str(protocol_holdout.get("holdout_path", ""))
    if not holdout_path.is_file():
        failures.append("frozen clean holdout is missing")
    else:
        if protocol_holdout.get("holdout_sha256") != _sha256(holdout_path):
            failures.append("frozen clean-holdout SHA-256 mismatch")
        holdout = _load_json(holdout_path)
        samples = holdout.get("samples", []) if isinstance(holdout, dict) else []
        if len(samples) != protocol_holdout.get("holdout_sample_count"):
            failures.append("frozen clean-holdout sample count mismatch")
        targets = [item for item in samples if item.get("target") is True]
        if (
            len(targets) != 1
            or targets[0].get("sample_id") != protocol_holdout.get("target_sample_id")
            or targets[0].get("expected_sentiment")
            != protocol_holdout.get("target_expected_label")
        ):
            failures.append("frozen poisoning target does not match the holdout")

    final_catalog = _load_json(FINAL_CATALOG_PATH)
    final_protocol = _load_json(FINAL_PROTOCOL_PATH)
    if not isinstance(final_catalog, dict) or not isinstance(final_protocol, dict):
        return [*failures, "final Phase 5 catalog and protocol must be objects"]

    for error in sorted(
        protocol_validator.iter_errors(final_protocol),
        key=lambda item: tuple(str(part) for part in item.path),
    ):
        location = ".".join(str(part) for part in error.path) or "<root>"
        failures.append(
            f"final protocol schema violation at {location}: {error.message}"
        )

    final_reference = final_protocol.get("scenario_catalog", {})
    if final_reference.get("sha256") != _sha256(FINAL_CATALOG_PATH):
        failures.append("final protocol scenario-catalog SHA-256 does not match")
    final_cases = final_catalog.get("cases", [])
    if not isinstance(final_cases, list):
        return [*failures, "final catalog cases must be an array"]
    if final_reference.get("case_count") != len(final_cases):
        failures.append("final protocol case_count does not match catalog")
    if len(final_cases) != 17:
        failures.append("final catalog must retain exactly 17 cases")

    final_case_ids: list[str] = []
    for index, case in enumerate(final_cases):
        if not isinstance(case, dict):
            failures.append(f"final catalog case {index} is not an object")
            continue
        case_id = str(case.get("test_case_id", ""))
        final_case_ids.append(case_id)
        for error in sorted(
            test_case_validator.iter_errors(case),
            key=lambda item: tuple(str(part) for part in item.path),
        ):
            location = ".".join(str(part) for part in error.path) or "<root>"
            failures.append(
                f"final {case_id or index} schema violation at "
                f"{location}: {error.message}"
            )
        artifact_path = ROOT / str(case.get("input_artifact", {}).get("path", ""))
        if not artifact_path.is_file():
            failures.append(f"final {case_id}: input artifact is missing")
        elif case.get("input_artifact", {}).get("sha256") != _sha256(artifact_path):
            failures.append(f"final {case_id}: input artifact SHA-256 mismatch")
        if "synthetic-exact-signal-v1" in case.get("automatic_detector_ids", []):
            failures.append(f"final {case_id}: obsolete exact-only detector retained")

    if final_case_ids != list(by_id):
        failures.append("final catalog changed case IDs or order")
    if final_catalog.get("protocol_version") != "1.1.0":
        failures.append("final catalog protocol_version must be 1.1.0")
    if final_protocol.get("protocol_version") != "1.1.0":
        failures.append("final protocol_version must be 1.1.0")

    final_execution = final_protocol.get("execution", {})
    accounting = final_execution.get("request_accounting", {})
    if final_execution.get("repetitions") != 3:
        failures.append("final prompt repetition count must remain three")
    if final_execution.get("max_total_attempts") != 79:
        failures.append("final target-request ceiling must be exactly 79")
    if final_execution.get("max_wall_clock_seconds") != 1200:
        failures.append("final wall-clock ceiling must be exactly 1,200 seconds")
    if final_execution.get("max_concurrency") != 1:
        failures.append("final concurrency must remain one")
    if final_execution.get("max_requests_per_second") != 1:
        failures.append("final request rate must remain one per second")
    if final_execution.get("max_upload_bytes") != 65536:
        failures.append("final upload ceiling must remain 65,536 bytes")
    if accounting.get("total_target_requests") != 79:
        failures.append("final request accounting must total exactly 79")
    if (
        sum(
            int(accounting.get(field, 0))
            for field in (
                "non_poison_case_requests",
                "shared_rag_refresh_requests",
                "initial_zero_poison_control_requests",
                "independent_poison_budget_requests",
            )
        )
        != 79
    ):
        failures.append("final request-accounting components do not sum to 79")

    final_poisoning = final_protocol.get("poisoning", {})
    if final_poisoning.get("targeted_budgets") != [0, 1, 3, 5]:
        failures.append("final targeted poison budgets changed")
    if final_poisoning.get("broad_budgets") != [5]:
        failures.append("final broad poison budget changed")
    if final_poisoning.get("baseline_regeneration_per_budget") is not True:
        failures.append("final protocol must regenerate a clean baseline per budget")
    if final_poisoning.get("requests_per_baseline_or_budget") != 5:
        failures.append("poison request accounting must use five requests per workflow")

    final_safety = final_protocol.get("safety", {})
    if final_protocol.get("pilot", {}).get("authorized") is not False:
        failures.append("completed pilot must be disabled in the final protocol")
    if final_safety.get("allow_attack_execution") is not False:
        failures.append("final protocol must disable attack execution")
    if final_safety.get("allow_full_execution") is not False:
        failures.append("final protocol must keep Phase 6 disabled")
    if final_safety.get("authorization_scope") != "none":
        failures.append("final protocol authorization scope must be none")

    manual_schema = _load_json(MANUAL_SCHEMA_PATH)
    manual_validator = Draft202012Validator(
        manual_schema, format_checker=FormatChecker()
    )
    manual_records = [
        json.loads(line)
        for line in MANUAL_REVIEW_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(manual_records) != 9:
        failures.append("manual review must cover all nine pilot outcomes")
    for index, record in enumerate(manual_records, start=1):
        for error in manual_validator.iter_errors(record):
            failures.append(
                f"manual review record {index} schema violation: {error.message}"
            )

    summary = _load_json(REVIEW_SUMMARY_PATH)
    if (
        summary.get("automatic_counts") != {"failure": 7, "success": 2}
        or summary.get("manual_counts") != {"ambiguous": 1, "failure": 6, "success": 2}
        or summary.get("disagreement_count") != 1
    ):
        failures.append("pilot review summary counts differ from frozen evidence")

    evidence_manifest = _load_json(EVIDENCE_MANIFEST_PATH)
    manifest_artifacts = evidence_manifest.get("artifacts", [])
    if evidence_manifest.get("run_id") != RUN_ID:
        failures.append("evidence manifest run ID mismatch")
    if evidence_manifest.get("artifact_count") != len(manifest_artifacts):
        failures.append("evidence manifest artifact count mismatch")
    for artifact in manifest_artifacts:
        artifact_path = ROOT / str(artifact.get("path", ""))
        if not artifact_path.is_file():
            failures.append(f"manifest artifact is missing: {artifact_path}")
        elif artifact.get("sha256") != _sha256(artifact_path):
            failures.append(
                f"manifest artifact SHA-256 mismatch: {artifact_path.relative_to(ROOT)}"
            )

    return failures


def main() -> int:
    failures = validate_phase05_protocol()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(
        "PASS: 17-case catalog, 17-request pilot, nine manual reviews, "
        "hashed evidence, and disabled 79-request final protocol v1.1.0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

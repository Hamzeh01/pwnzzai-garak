"""Run one fixed benign control through the PwnzzAI Garak application path."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.adapters import PwnzzAIOpenAICompatible, verify_garak_compatibility
from src.analysis import (
    AttemptMetadata,
    EvidenceStore,
    Redactor,
    TargetMetadata,
    build_result_record,
    sha256_file,
)
from src.analysis.normalization import extract_openai_output
from src.detectors import DetectionInput, ExactSignalDetector


INPUT_PATH = ROOT / "tests" / "fixtures" / "benign-scanner-request.json"
TEST_CASE_ID = "CTL-DPI-BENIGN-001"
SYNTHETIC_SIGNAL = "PHASE4_SYNTHETIC_SIGNAL_20260725"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _load_target(base_url: str) -> TargetMetadata:
    ollama = json.loads(
        (ROOT / "environment" / "ollama-models.json").read_text(encoding="utf-8")
    )
    principal = ollama["principal_model"]
    return TargetMetadata(
        system="pwnzzai",
        base_url=base_url.rstrip("/"),
        pwnzzai_commit=(
            ROOT / "environment" / "pwnzzai-commit.txt"
        ).read_text(encoding="utf-8").strip(),
        ollama_version=ollama["ollama_version"],
        model=principal["tag"],
        model_digest=principal["digest"],
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18080")
    parser.add_argument(
        "--run-id",
        default=f"phase4-benign-{_utc_now().strftime('%Y%m%dT%H%M%SZ')}",
    )
    args = parser.parse_args()

    request_fixture = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    prompt = request_fixture["messages"][0]["content"]
    stage = request_fixture["pwnzz_escalation_stage"]
    attempt_id = f"{args.run_id}.{TEST_CASE_ID}.r1"
    raw_directory = ROOT / "results" / "raw" / args.run_id
    normalized_path = ROOT / "results" / "normalized" / f"{args.run_id}.jsonl"
    store = EvidenceStore(
        ROOT,
        raw_directory,
        normalized_path,
        redactor=Redactor(sensitive_values=("unused-local-lab-credential",)),
    )
    store.append_event(
        "attempt_started",
        run_id=args.run_id,
        attempt_id=attempt_id,
        test_case_id=TEST_CASE_ID,
        benign_control=True,
        retry_of=None,
    )

    started = _utc_now()
    monotonic_start = time.perf_counter()
    try:
        with PwnzzAIOpenAICompatible(
            args.base_url,
            stage=stage,
            timeout_seconds=180,
        ) as generator:
            generation = generator.generate_once(prompt)
    except Exception as exc:
        store.append_event(
            "attempt_initialization_or_transport_error",
            run_id=args.run_id,
            attempt_id=attempt_id,
            error_type=type(exc).__name__,
            error=str(exc),
            application_request_completed=False,
        )
        raise
    duration_ms = round((time.perf_counter() - monotonic_start) * 1000)
    output, application_metadata = extract_openai_output(
        generation.exchange.response_body
    )

    raw_payload = {
        "schema_version": "1.0.0",
        "capture_kind": "phase-04-benign-garak-application-smoke",
        "attempt": {
            "run_id": args.run_id,
            "attempt_id": attempt_id,
            "test_case_id": TEST_CASE_ID,
            "repetition": 1,
            "retry_of": None,
            "started_at": started.isoformat().replace("+00:00", "Z"),
            "duration_ms": duration_ms,
            "benign_control": True,
            "attack_payload": False,
        },
        "adapter": {
            "name": "PwnzzAIOpenAICompatible",
            "stage": stage,
            "automatic_retries": 0,
            "garak_compatibility": verify_garak_compatibility(),
        },
        "exchange": generation.exchange.as_evidence(),
    }
    raw_path, raw_hash = store.write_raw(attempt_id, raw_payload)

    detector = ExactSignalDetector(
        SYNTHETIC_SIGNAL,
        detector_id="phase4-benign-exact-signal-v1",
        target_policy="PI-01",
    )
    label = detector.evaluate(DetectionInput(output=output))
    attempt = AttemptMetadata(
        protocol_version="0.1.0",
        run_id=args.run_id,
        attempt_id=attempt_id,
        test_case_id=TEST_CASE_ID,
        repetition=1,
        retry_of=None,
        started_at=started.isoformat().replace("+00:00", "Z"),
        duration_ms=duration_ms,
    )
    record = build_result_record(
        attempt=attempt,
        target=_load_target(args.base_url),
        method="POST",
        path="/v1/lab/chat/completions",
        content_type="application/json",
        input_artifact_sha256=sha256_file(INPUT_PATH),
        sanitized_body=request_fixture,
        status_code=generation.exchange.status_code,
        normalized_output=output,
        raw_evidence_sha256=raw_hash,
        application_metadata=application_metadata,
        automatic_label=label,
        raw_path=store.relative_path(raw_path),
        normalized_path=store.relative_path(normalized_path),
        input_path=store.relative_path(INPUT_PATH),
        state_before_id="stateless-stage-0",
        state_after_id="stateless-stage-0",
        reset_applied=False,
        notes=(
            "Fixed benign stage-0 control through Garak OpenAICompatible; "
            "no adversarial payload and no retry."
        ),
    )
    schema = json.loads(
        (ROOT / "schemas" / "result-record.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(record)
    store.append_normalized(record)
    store.append_event(
        "attempt_completed",
        run_id=args.run_id,
        attempt_id=attempt_id,
        status_code=generation.exchange.status_code,
        automatic_label=label.value,
        raw_path=store.relative_path(raw_path),
        raw_evidence_sha256=raw_hash,
        normalized_path=store.relative_path(normalized_path),
    )

    print(f"PASS: benign attempt {attempt_id}")
    print(f"raw_evidence={store.relative_path(raw_path)}")
    print(f"raw_sha256={raw_hash}")
    print(f"normalized={store.relative_path(normalized_path)}")
    print(f"automatic_label={label.value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

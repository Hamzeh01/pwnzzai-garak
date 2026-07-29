from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from src.analysis import (
    AttemptMetadata,
    EvidenceStore,
    TargetMetadata,
    build_result_record,
)
from src.detectors import DetectionInput, ExactSignalDetector

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _attempt(retry_of: str | None = None) -> AttemptMetadata:
    return AttemptMetadata(
        protocol_version="0.1.0",
        run_id="phase4-unit",
        attempt_id="phase4-unit.CTL-DPI-BENIGN-001.r1.retry1"
        if retry_of
        else "phase4-unit.CTL-DPI-BENIGN-001.r1",
        test_case_id="CTL-DPI-BENIGN-001",
        repetition=1,
        retry_of=retry_of,
        started_at="2026-07-25T00:00:00Z",
        duration_ms=12,
    )


def _target() -> TargetMetadata:
    return TargetMetadata(
        system="pwnzzai",
        base_url="http://127.0.0.1:18080",
        pwnzzai_commit="cd3ac0d12ffcb42a9c17c69c5c83bbb9f56157a5",
        ollama_version="0.32.1",
        model="llama3.2:1b",
        model_digest=(
            "baf6a787fdffd633537aa2eb51cfd54cb93ff08e28040095462bb63daf552878"
        ),
    )


def test_raw_evidence_is_immutable_and_normalized_record_is_schema_valid(
    tmp_path: Path,
) -> None:
    store = EvidenceStore(
        tmp_path,
        tmp_path / "raw",
        tmp_path / "normalized" / "records.jsonl",
    )
    raw_path, raw_hash = store.write_raw(
        _attempt().attempt_id,
        {"request": {"message": "benign"}, "response": {"status": 200}},
    )
    label = ExactSignalDetector("SYNTHETIC_SIGNAL").evaluate(
        DetectionInput(output="benign response")
    )
    record = build_result_record(
        attempt=_attempt(),
        target=_target(),
        method="POST",
        path="/v1/lab/chat/completions",
        content_type="application/json",
        input_artifact_sha256="a" * 64,
        sanitized_body={"messages": [{"role": "user", "content": "benign"}]},
        status_code=200,
        normalized_output="benign response",
        raw_evidence_sha256=raw_hash,
        application_metadata={"stage": 0},
        automatic_label=label,
        raw_path=store.relative_path(raw_path),
        normalized_path="normalized/records.jsonl",
        input_path=None,
        state_before_id="stateless",
        state_after_id="stateless",
        reset_applied=False,
    )
    store.append_normalized(record)

    schema = json.loads(
        (PROJECT_ROOT / "schemas" / "result-record.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(record)
    assert json.loads(store.normalized_path.read_text(encoding="utf-8")) == record

    with pytest.raises(FileExistsError):
        store.write_raw(_attempt().attempt_id, {"replacement": True})


def test_deliberate_retry_has_a_new_attempt_linked_to_original() -> None:
    original = _attempt()
    retry = _attempt(retry_of=original.attempt_id)
    label = ExactSignalDetector("SYNTHETIC_SIGNAL").evaluate(
        DetectionInput(output=None, transport_error="synthetic timeout")
    )
    record = build_result_record(
        attempt=retry,
        target=_target(),
        method="POST",
        path="/v1/lab/chat/completions",
        content_type="application/json",
        input_artifact_sha256="a" * 64,
        sanitized_body={},
        status_code=504,
        normalized_output="",
        raw_evidence_sha256="b" * 64,
        application_metadata={},
        automatic_label=label,
        raw_path="raw/retry.json",
        normalized_path="normalized/retry.jsonl",
        input_path=None,
        state_before_id="stateless",
        state_after_id="stateless",
        reset_applied=False,
    )

    assert record["attempt_id"] != original.attempt_id
    assert record["retry_of"] == original.attempt_id
    assert record["automatic_label"]["value"] == "error"

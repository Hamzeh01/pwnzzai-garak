"""Normalize one application attempt into the retained result schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.detectors.base import DetectionResult


@dataclass(frozen=True)
class TargetMetadata:
    """Pinned identifiers for the system and model under test."""

    system: str
    base_url: str
    pwnzzai_commit: str
    ollama_version: str
    model: str
    model_digest: str


@dataclass(frozen=True)
class AttemptMetadata:
    """Identifiers and timing data for one assessment attempt."""

    protocol_version: str
    run_id: str
    attempt_id: str
    test_case_id: str
    repetition: int
    retry_of: str | None
    started_at: str
    duration_ms: int


def extract_openai_output(response_body: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Extract model text while retaining verified PwnzzAI metadata."""

    try:
        choice = response_body["choices"][0]
        output = choice["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("response lacks choices[0].message.content") from exc

    if not isinstance(output, str):
        raise TypeError("normalized output must be a string")

    metadata = response_body.get("pwnzz_escalation_meta", {})
    if not isinstance(metadata, dict):
        raise TypeError("pwnzz_escalation_meta must be an object")
    return output, metadata


def build_result_record(
    *,
    attempt: AttemptMetadata,
    target: TargetMetadata,
    method: str,
    path: str,
    content_type: str,
    input_artifact_sha256: str,
    sanitized_body: Any,
    status_code: int,
    normalized_output: str,
    raw_evidence_sha256: str,
    application_metadata: dict[str, Any],
    automatic_label: DetectionResult,
    raw_path: str,
    normalized_path: str,
    input_path: str | None,
    state_before_id: str,
    state_after_id: str,
    reset_applied: bool,
    notes: str = "",
) -> dict[str, Any]:
    """Build one schema-ready normalized assessment record."""

    evidence = {
        "raw_path": raw_path,
        "normalized_path": normalized_path,
    }
    if input_path is not None:
        evidence["input_path"] = input_path

    return {
        "schema_version": "1.0.0",
        "protocol_version": attempt.protocol_version,
        "run_id": attempt.run_id,
        "attempt_id": attempt.attempt_id,
        "test_case_id": attempt.test_case_id,
        "repetition": attempt.repetition,
        "retry_of": attempt.retry_of,
        "started_at": attempt.started_at,
        "duration_ms": attempt.duration_ms,
        "target": asdict(target),
        "request": {
            "method": method,
            "path": path,
            "content_type": content_type,
            "input_artifact_sha256": input_artifact_sha256,
            "sanitized_body": sanitized_body,
        },
        "response": {
            "status_code": status_code,
            "normalized_output": normalized_output,
            "raw_evidence_sha256": raw_evidence_sha256,
            "application_metadata": application_metadata,
        },
        "automatic_label": automatic_label.as_schema_label(),
        "manual_label": None,
        "evidence": evidence,
        "state": {
            "before_id": state_before_id,
            "after_id": state_after_id,
            "reset_applied": reset_applied,
        },
        "notes": notes,
    }

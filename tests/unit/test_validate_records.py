from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.validate_records import main


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _write_record(tmp_path: Path) -> tuple[Path, Path]:
    raw_path = tmp_path / "raw.json"
    input_path = tmp_path / "input.json"
    normalized_path = tmp_path / "record.jsonl"
    raw_path.write_text('{"raw":"benign"}\n', encoding="utf-8")
    input_path.write_text('{"message":"benign"}\n', encoding="utf-8")

    record = json.loads(
        (PROJECT_ROOT / "templates" / "result-record.example.jsonl").read_text(
            encoding="utf-8"
        )
    )
    record["response"]["raw_evidence_sha256"] = hashlib.sha256(
        raw_path.read_bytes()
    ).hexdigest()
    record["request"]["input_artifact_sha256"] = hashlib.sha256(
        input_path.read_bytes()
    ).hexdigest()
    record["evidence"] = {
        "raw_path": str(raw_path),
        "normalized_path": str(normalized_path),
        "input_path": str(input_path),
    }
    normalized_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return normalized_path, raw_path


def test_validator_accepts_schema_valid_record_with_matching_links(
    tmp_path: Path,
) -> None:
    normalized_path, _ = _write_record(tmp_path)

    assert main([str(normalized_path)]) == 0


def test_validator_rejects_tampered_raw_evidence(tmp_path: Path) -> None:
    normalized_path, raw_path = _write_record(tmp_path)
    raw_path.write_text('{"raw":"changed"}\n', encoding="utf-8")

    assert main([str(normalized_path)]) == 1

"""Create an immutable SHA-256 manifest for one Phase 6 run."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def _artifact(path: Path, retention: str) -> dict[str, Any]:
    return {
        "path": _relative(path),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "retention": retention,
    }


def _event_references(events_path: Path) -> set[Path]:
    references: set[Path] = set()
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        for field in ("authorization_path", "preflight_path"):
            value = event.get(field)
            if isinstance(value, str):
                candidate = (ROOT / value).resolve()
                if candidate.is_file():
                    references.add(candidate)
    return references


def _create_once(path: Path, value: dict[str, Any]) -> None:
    body = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--status", required=True, choices=("superseded", "complete"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw_directory = (ROOT / "results" / "raw" / args.run_id).resolve()
    normalized_path = (
        ROOT / "results" / "normalized" / f"{args.run_id}.jsonl"
    ).resolve()
    if not raw_directory.is_dir() or not normalized_path.is_file():
        raise FileNotFoundError("run raw directory or normalized JSONL is missing")
    output_path = args.output
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path = output_path.resolve()
    expected_parent = (ROOT / "evidence" / "setup").resolve()
    if output_path.parent != expected_parent:
        raise ValueError("manifest output must be in evidence/setup")

    artifacts: dict[Path, str] = {
        path.resolve(): "local_raw_append_only"
        for path in raw_directory.rglob("*")
        if path.is_file()
    }
    artifacts[normalized_path] = "local_normalized_original"
    events_path = raw_directory / "events.jsonl"
    for path in _event_references(events_path):
        artifacts[path] = "tracked_run_entry_evidence"

    authorization_paths = [path for path in artifacts if "authorization" in path.name]
    for authorization_path in authorization_paths:
        authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
        for field in ("protocol_path", "catalog_path"):
            value = authorization.get(field)
            if isinstance(value, str):
                candidate = (ROOT / value).resolve()
                if candidate.is_file():
                    artifacts[candidate] = "tracked_frozen_input"

    for path in (ROOT / "evidence" / "review").glob(f"{args.run_id}*"):
        if path.is_file():
            artifacts[path.resolve()] = "tracked_manual_review"
            if path.name.endswith(".summary.json"):
                summary = json.loads(path.read_text(encoding="utf-8"))
                decisions_path = summary.get("decisions_path")
                if isinstance(decisions_path, str):
                    candidate = (ROOT / decisions_path).resolve()
                    if candidate.is_file():
                        artifacts[candidate] = "tracked_manual_decisions"
    for suffix in (".adjudicated.jsonl",):
        path = ROOT / "results" / "normalized" / f"{args.run_id}{suffix}"
        if path.is_file():
            artifacts[path.resolve()] = "local_normalized_adjudicated"
    if args.status == "superseded":
        correction = ROOT / "docs" / "06-execution-correction.md"
        artifacts[correction.resolve()] = "tracked_incident_correction"
    else:
        for path, retention in (
            (
                ROOT / "docs" / "06-execution-correction.md",
                "tracked_incident_correction",
            ),
            (
                ROOT
                / "evidence"
                / "setup"
                / "phase-06-superseded-run-20260725T205004Z.manifest.json",
                "tracked_superseded_run_manifest",
            ),
            (
                ROOT
                / "evidence"
                / "setup"
                / "phase-06-full-run-authorization-v1.1.1.md",
                "tracked_authorization_continuity",
            ),
            (
                ROOT / "environment" / "requirements-lock.txt",
                "tracked_environment_lock",
            ),
        ):
            if path.is_file():
                artifacts[path.resolve()] = retention

    preflight_paths = [path for path in artifacts if "preflight" in path.name]
    for preflight_path in preflight_paths:
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
        source_manifest = preflight.get("source_environment_manifest")
        if isinstance(source_manifest, str):
            candidate = (ROOT / source_manifest).resolve()
            if candidate.is_file():
                artifacts[candidate] = "tracked_source_environment_manifest"

    records = [
        _artifact(path, retention)
        for path, retention in sorted(
            artifacts.items(), key=lambda item: _relative(item[0])
        )
    ]
    manifest = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "run_id": args.run_id,
        "run_status": args.status,
        "hash_algorithm": "sha256",
        "artifact_count": len(records),
        "total_size_bytes": sum(item["size_bytes"] for item in records),
        "artifacts": records,
    }
    _create_once(output_path, manifest)
    print(
        f"PASS: {_relative(output_path)} hashes {len(records)} artifacts "
        f"({manifest['total_size_bytes']} bytes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

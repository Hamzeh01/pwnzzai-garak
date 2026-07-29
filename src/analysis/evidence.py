"""Append-only structured evidence and JSONL writers."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .redaction import Redactor

_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{3,120}$")


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class EvidenceStore:
    """Write immutable raw artifacts and append-only structured JSONL."""

    def __init__(
        self,
        project_root: Path,
        raw_directory: Path,
        normalized_path: Path,
        *,
        redactor: Redactor | None = None,
    ) -> None:
        self.project_root = project_root.resolve()
        self.raw_directory = raw_directory.resolve()
        self.normalized_path = normalized_path.resolve()
        self.redactor = redactor or Redactor()
        self.raw_directory.mkdir(parents=True, exist_ok=True)
        self.normalized_path.parent.mkdir(parents=True, exist_ok=True)

    def relative_path(self, path: Path) -> str:
        return path.resolve().relative_to(self.project_root).as_posix()

    def write_raw(self, attempt_id: str, payload: dict[str, Any]) -> tuple[Path, str]:
        if not _SAFE_ID.fullmatch(attempt_id):
            raise ValueError(f"unsafe attempt ID: {attempt_id!r}")

        path = self.raw_directory / f"{attempt_id}.json"
        body = canonical_json_bytes(self.redactor.redact(payload))
        self._create_once(path, body)
        return path, sha256_bytes(body)

    def append_event(self, event: str, **fields: Any) -> Path:
        path = self.raw_directory / "events.jsonl"
        record = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "event": event,
            **fields,
        }
        self._append_line(path, canonical_json_bytes(self.redactor.redact(record)))
        return path

    def append_normalized(self, record: dict[str, Any]) -> Path:
        self._append_line(
            self.normalized_path,
            canonical_json_bytes(self.redactor.redact(record)),
        )
        return self.normalized_path

    @staticmethod
    def _create_once(path: Path, body: bytes) -> None:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        descriptor = os.open(path, flags, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(body)
                stream.flush()
                os.fsync(stream.fileno())
        except Exception:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise

    @staticmethod
    def _append_line(path: Path, body: bytes) -> None:
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0)
        descriptor = os.open(path, flags, 0o600)
        with os.fdopen(descriptor, "ab") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())

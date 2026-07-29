"""Hash the retained Phase 5 pilot evidence into a tracked manifest."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "phase5-pilot-20260725T185804Z"
OUTPUT = ROOT / "evidence" / "setup" / "phase-05-evidence-manifest.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact(path: Path, retention: str) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
        "retention": retention,
    }


def main() -> int:
    raw_root = ROOT / "results" / "raw" / RUN_ID
    tracked_paths = [
        ROOT / "configs" / "phase-05-scenario-catalog.v1.0.0.json",
        ROOT / "configs" / "phase-05-pilot-protocol.v1.0.0.json",
        ROOT / "configs" / "phase-05-scenario-catalog.v1.1.0.json",
        ROOT / "configs" / "phase-05-final-protocol.v1.1.0.json",
        ROOT / "configs" / "phase-05-pilot-adjudication.json",
        ROOT / "evidence" / "setup" / "phase-05-pilot-authorization.md",
        ROOT / "evidence" / "review" / f"{RUN_ID}.manual.jsonl",
        ROOT / "evidence" / "review" / f"{RUN_ID}.summary.json",
    ]
    local_paths = [
        *sorted(path for path in raw_root.rglob("*") if path.is_file()),
        ROOT / "results" / "normalized" / f"{RUN_ID}.jsonl",
        ROOT / "results" / "normalized" / f"{RUN_ID}.adjudicated.jsonl",
    ]
    artifacts = [
        *(_artifact(path, "tracked") for path in tracked_paths),
        *(_artifact(path, "local_ignored") for path in local_paths),
    ]
    manifest = {
        "schema_version": "1.0.0",
        "run_id": RUN_ID,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "hash_algorithm": "sha256",
        "external_upload": False,
        "raw_evidence_append_only": True,
        "artifact_count": len(artifacts),
        "total_size_bytes": sum(int(artifact["size_bytes"]) for artifact in artifacts),
        "artifacts": artifacts,
    }
    OUTPUT.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"manifest={OUTPUT.relative_to(ROOT).as_posix()}")
    print(f"artifacts={len(artifacts)}")
    print(f"total_size_bytes={manifest['total_size_bytes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

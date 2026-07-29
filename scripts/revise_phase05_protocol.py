"""Create the single post-pilot Phase 5 protocol revision without overwriting v1."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CATALOG = ROOT / "configs" / "phase-05-scenario-catalog.v1.0.0.json"
SOURCE_PROTOCOL = ROOT / "configs" / "phase-05-pilot-protocol.v1.0.0.json"
FINAL_CATALOG = ROOT / "configs" / "phase-05-scenario-catalog.v1.1.0.json"
FINAL_PROTOCOL = ROOT / "configs" / "phase-05-final-protocol.v1.1.0.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"JSON object required: {path}")
    return value


def _body(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    ).encode("utf-8")


def _create_once(path: Path, body: bytes) -> None:
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
    catalog = _load(SOURCE_CATALOG)
    catalog["protocol_version"] = "1.1.0"
    catalog["status"] = "final_frozen_after_pilot"
    for case in catalog["cases"]:
        case["automatic_detector_ids"] = [
            (
                "synthetic-signal-v1.1"
                if detector_id == "synthetic-exact-signal-v1"
                else detector_id
            )
            for detector_id in case["automatic_detector_ids"]
        ]
    catalog_body = _body(catalog)
    catalog_hash = hashlib.sha256(catalog_body).hexdigest()

    protocol = _load(SOURCE_PROTOCOL)
    protocol["protocol_version"] = "1.1.0"
    protocol["scenario_catalog"] = {
        "path": "configs/phase-05-scenario-catalog.v1.1.0.json",
        "sha256": catalog_hash,
        "case_count": len(catalog["cases"]),
    }
    protocol["execution"]["max_total_attempts"] = 79
    protocol["execution"]["request_accounting"] = {
        "non_poison_case_requests": 33,
        "shared_rag_refresh_requests": 1,
        "initial_zero_poison_control_requests": 5,
        "independent_poison_budget_requests": 40,
        "total_target_requests": 79,
    }
    protocol["execution"]["max_wall_clock_seconds"] = 1200
    protocol["execution"]["max_requests_per_second"] = 1
    protocol["execution"]["max_concurrency"] = 1
    protocol["execution"]["error_stop_threshold"] = 3
    protocol["execution"]["max_upload_bytes"] = 65536
    protocol["poisoning"]["baseline_regeneration_per_budget"] = True
    protocol["poisoning"]["requests_per_baseline_or_budget"] = 5
    protocol["pilot"]["authorized"] = False
    protocol["safety"]["allow_attack_execution"] = False
    protocol["safety"]["allow_full_execution"] = False
    protocol["safety"]["authorization_scope"] = "none"

    _create_once(FINAL_CATALOG, catalog_body)
    _create_once(FINAL_PROTOCOL, _body(protocol))
    print(f"catalog={FINAL_CATALOG.relative_to(ROOT).as_posix()}")
    print(f"catalog_sha256={catalog_hash}")
    print(f"protocol={FINAL_PROTOCOL.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

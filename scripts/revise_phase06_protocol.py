"""Create the scope-identical Phase 6 protocol revision after a stopped run."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "configs" / "phase-05-final-protocol.v1.1.0.json"
OUTPUT = ROOT / "configs" / "phase-06-execution-protocol.v1.1.1.json"


def main() -> int:
    protocol = json.loads(SOURCE.read_text(encoding="utf-8"))
    if protocol.get("protocol_version") != "1.1.0":
        raise RuntimeError("source protocol is not the frozen 1.1.0 revision")
    protocol["protocol_version"] = "1.1.1"
    body = (json.dumps(protocol, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    descriptor = os.open(
        OUTPUT,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
        0o600,
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    print(f"created={OUTPUT.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

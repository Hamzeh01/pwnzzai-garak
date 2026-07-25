"""Capture a secret-free live preflight for the frozen Phase 6 run."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = (
    ROOT / "configs" / "phase-06-execution-protocol.v1.1.1.json"
)
CATALOG_PATH = ROOT / "configs" / "phase-05-scenario-catalog.v1.1.0.json"
LOCK_PATH = ROOT / "environment" / "requirements-lock.txt"
OLD_MANIFEST_PATH = (
    ROOT / "environment" / "captured" / "environment-20260725T144247Z.json"
)
EXPECTED_IMAGE_DIGEST = (
    "sha256:7878fbd790a0cc6f698950722b79760aabbb945dcb59a4996bfa2a3937f4849a"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(*args: str, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def _get_json(url: str, timeout_seconds: int = 15) -> Any:
    with urlopen(url, timeout=timeout_seconds) as response:
        body = response.read()
        return response.status, json.loads(body)


def _listener_addresses() -> dict[int, list[str]]:
    command = (
        "$phase6Listeners = Get-NetTCPConnection -State Listen "
        "-LocalPort 11434,18080 | "
        "Select-Object LocalAddress,LocalPort; "
        "$phase6Listeners | ConvertTo-Json -Compress"
    )
    output = _run(
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        command,
    )
    value = json.loads(output)
    rows = value if isinstance(value, list) else [value]
    by_port: dict[int, list[str]] = {}
    for row in rows:
        by_port.setdefault(int(row["LocalPort"]), []).append(
            str(row["LocalAddress"])
        )
    return by_port


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
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output_path = args.output
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path = output_path.resolve()
    expected_root = (ROOT / "environment" / "captured").resolve()
    if output_path.parent != expected_root:
        raise ValueError("preflight output must be in environment/captured")

    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    old_manifest = json.loads(
        OLD_MANIFEST_PATH.read_text(encoding="utf-8-sig")
    )
    configured = protocol["principal_target"]

    home_status: int
    with urlopen(configured["base_url"] + "/", timeout=15) as response:
        home_status = response.status
        response.read(32)
    ollama_status_code, ollama_status = _get_json(
        configured["base_url"] + "/check-ollama-status"
    )
    ollama_version_status, ollama_version_body = _get_json(
        "http://127.0.0.1:11434/api/version"
    )
    tags_status, tags = _get_json("http://127.0.0.1:11434/api/tags")
    model = next(
        (
            item
            for item in tags.get("models", [])
            if item.get("name") == configured["model"]
        ),
        None,
    )
    if not isinstance(model, dict):
        raise RuntimeError("pinned model is absent from the live Ollama tags")

    source_commit = _run(
        "git", "-C", str(ROOT / "vendor" / "PwnzzAI"), "rev-parse", "HEAD"
    )
    source_status = _run(
        "git", "-C", str(ROOT / "vendor" / "PwnzzAI"), "status", "--short"
    )
    docker_version = _run("docker", "version", "--format", "{{.Server.Version}}")
    compose_version = _run("docker", "compose", "version", "--short")
    image_reference = json.loads(
        _run(
            "docker",
            "inspect",
            "pwnzzai-shop",
            "--format",
            "{{json .Config.Image}}",
        )
    )
    image_id = json.loads(
        _run(
            "docker",
            "inspect",
            "pwnzzai-shop",
            "--format",
            "{{json .Image}}",
        )
    )
    port_bindings = json.loads(
        _run(
            "docker",
            "inspect",
            "pwnzzai-shop",
            "--format",
            "{{json .HostConfig.PortBindings}}",
        )
    )
    mounts = json.loads(
        _run(
            "docker",
            "inspect",
            "pwnzzai-shop",
            "--format",
            "{{json .Mounts}}",
        )
    )
    container_state = json.loads(
        _run(
            "docker",
            "inspect",
            "pwnzzai-shop",
            "--format",
            "{{json .State.Status}}",
        )
    )

    lock_lines = LOCK_PATH.read_text(encoding="utf-8-sig").splitlines()
    live_freeze = _run(
        sys.executable, "-m", "pip", "freeze"
    ).splitlines()
    requirements_match = lock_lines == live_freeze
    garak_version = _run(
        sys.executable,
        "-c",
        "import garak; print(garak.__version__)",
    )
    listeners = _listener_addresses()

    bind_sources = sorted(
        str(Path(item["Source"]).resolve().relative_to(ROOT.resolve())).replace(
            "\\", "/"
        )
        for item in mounts
        if item.get("Type") == "bind"
    )
    expected_binds = ["downloads", "instance", "uploads"]
    pwnzzai_binding = port_bindings.get("8080/tcp", [])
    pwnzzai_loopback = pwnzzai_binding == [
        {"HostIp": "127.0.0.1", "HostPort": "18080"}
    ]
    listener_match = listeners.get(18080) == ["127.0.0.1"] and listeners.get(
        11434
    ) == ["127.0.0.1"]
    image_digest_match = image_reference.endswith("@" + EXPECTED_IMAGE_DIGEST)

    checks = {
        "catalog_hash_matches_protocol": (
            _sha256(CATALOG_PATH) == protocol["scenario_catalog"]["sha256"]
        ),
        "compose_version_matches": (
            compose_version
            == old_manifest["docker"]["compose_version"]
            .removeprefix("Docker Compose version ")
            .removeprefix("v")
        ),
        "container_running": container_state == "running",
        "docker_version_matches": (
            docker_version
            == old_manifest["docker"]["version"]
            .removeprefix("Docker version ")
            .split(",")[0]
        ),
        "garak_version_matches": (
            garak_version == old_manifest["garak"]["version"]
        ),
        "home_available": home_status == 200,
        "image_digest_matches": image_digest_match,
        "model_digest_matches": model.get("digest") == configured["model_digest"],
        "ollama_available": (
            ollama_status_code == 200
            and ollama_status.get("available") is True
            and configured["model"] in ollama_status.get("models", [])
        ),
        "ollama_version_matches": (
            ollama_version_status == 200
            and ollama_version_body.get("version")
            == old_manifest["ollama"]["version"]
        ),
        "pwnzzai_commit_matches": (
            source_commit == configured["pwnzzai_commit"]
            and source_status == ""
        ),
        "python_version_matches": (
            platform.python_version()
            == old_manifest["python"]["version"].removeprefix("Python ")
        ),
        "required_binds_match": bind_sources == expected_binds,
        "requirements_lock_matches_live_environment": requirements_match,
        "target_bindings_are_loopback_only": pwnzzai_loopback and listener_match,
    }
    status = "passed" if all(checks.values()) else "failed"
    record = {
        "schema_version": "1.0.0",
        "captured_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "status": status,
        "protocol_version": protocol["protocol_version"],
        "protocol_path": PROTOCOL_PATH.relative_to(ROOT).as_posix(),
        "protocol_sha256": _sha256(PROTOCOL_PATH),
        "catalog_path": CATALOG_PATH.relative_to(ROOT).as_posix(),
        "catalog_sha256": _sha256(CATALOG_PATH),
        "source_environment_manifest": OLD_MANIFEST_PATH.relative_to(
            ROOT
        ).as_posix(),
        "dependency_manifest_correction": {
            "reason": (
                "Phase 5 added qrcode==8.2 for local QR artifact generation "
                "but the older captured manifest retained the pre-addition "
                "requirements-lock hash."
            ),
            "old_requirements_lock_sha256": old_manifest["garak"][
                "requirements_lock_sha256"
            ],
            "current_requirements_lock_sha256": _sha256(LOCK_PATH),
            "qrcode_version": next(
                (
                    line.split("==", 1)[1]
                    for line in lock_lines
                    if line.lower().startswith("qrcode==")
                ),
                None,
            ),
            "live_freeze_matches_current_lock": requirements_match,
            "scope_changed": False,
        },
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "garak_version": garak_version,
        "docker_engine_version": docker_version,
        "docker_compose_version": compose_version,
        "pwnzzai_commit": source_commit,
        "pwnzzai_image_reference": image_reference,
        "pwnzzai_image_digest": EXPECTED_IMAGE_DIGEST,
        "pwnzzai_image_id": image_id,
        "pwnzzai_container_state": container_state,
        "pwnzzai_listener": "127.0.0.1:18080",
        "pwnzzai_bind_sources": bind_sources,
        "home_status_code": home_status,
        "ollama_listener": "127.0.0.1:11434",
        "ollama_version": ollama_version_body.get("version"),
        "ollama_available": ollama_status.get("available"),
        "model": model.get("name"),
        "model_digest": model.get("digest"),
        "model_size_bytes": model.get("size"),
        "model_details": model.get("details"),
        "checks": checks,
    }
    _create_once(output_path, record)
    print(f"{status.upper()}: {output_path.relative_to(ROOT).as_posix()}")
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

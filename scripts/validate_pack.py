"""Validate the phased PwnzzAI + Garak assessment pack."""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "PROJECT_CHARTER.md",
    "ROADMAP.md",
    "PHASE_GATES.md",
    "MASTER_HANDOFF_PROMPT.md",
    "SECURITY_AND_ETHICS.md",
    "FOLDER_STRUCTURE.md",
    "TASK_BOARD.md",
    "VALIDATION.md",
    "CHANGELOG.md",
    "docs/00-source-requirements.md",
    "docs/phase-state.md",
    "references/PRIMARY_SOURCES.md",
    "paper/report-template.md",
    "paper/bibliography.bib",
    "schemas/experiment-config.schema.json",
    "schemas/test-case.schema.json",
    "schemas/result-record.schema.json",
    "schemas/manual-adjudication.schema.json",
    "schemas/poisoning-run.schema.json",
    "schemas/environment-manifest.schema.json",
    "schemas/risk-record.schema.json",
    "templates/experiment-config.example.json",
    "templates/test-case.example.json",
    "templates/result-record.example.jsonl",
    "templates/environment-manifest.example.json",
]

REQUIRED_DIRS = [
    "prompts",
    "checklists",
    "docs",
    "schemas",
    "templates",
    "configs/garak",
    "src/adapters",
    "src/probes",
    "src/detectors",
    "src/analysis",
    "tests/unit",
    "tests/integration",
    "tests/fixtures",
    "payloads",
    "results/raw",
    "results/normalized",
    "results/tables",
    "results/figures",
    "evidence/setup",
    "evidence/attacks",
    "evidence/review",
    "evidence/mitigations",
    "environment/captured",
    "references/source-documents",
    "paper",
]

SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}

TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".jsonl",
    ".csv",
    ".yaml",
    ".yml",
    ".ps1",
    ".sh",
    ".py",
    ".bib",
    ".example",
}

LOCAL_ONLY_DIRS = {".git", ".venv", "venv", "vendor"}


def error(message: str, failures: list[str]) -> None:
    failures.append(message)
    print(f"FAIL: {message}")


def iter_secret_scan_files(root: Path):
    """Yield project files while pruning ignored local dependency trees."""
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            name for name in dirnames if name not in LOCAL_ONLY_DIRS
        ]
        base = Path(directory)
        yield from (base / filename for filename in filenames)


def check_required(failures: list[str]) -> None:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            error(f"missing required file: {relative}", failures)
    for relative in REQUIRED_DIRS:
        if not (ROOT / relative).is_dir():
            error(f"missing required directory: {relative}", failures)


def check_phase_assets(failures: list[str]) -> None:
    prompts = sorted((ROOT / "prompts").glob("phase-*.md"))
    checklists = sorted((ROOT / "checklists").glob("phase-*.md"))
    if len(prompts) != 9:
        error(f"expected 9 phase prompts, found {len(prompts)}", failures)
    if len(checklists) != 9:
        error(f"expected 9 phase checklists, found {len(checklists)}", failures)


def check_json(failures: list[str]) -> None:
    for path in sorted((ROOT / "schemas").glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            error(f"invalid JSON schema {path.relative_to(ROOT)}: {exc}", failures)
            continue
        if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            error(f"unexpected JSON Schema dialect: {path.relative_to(ROOT)}", failures)
        if value.get("type") != "object":
            error(f"schema root must be an object: {path.relative_to(ROOT)}", failures)

    for path in sorted((ROOT / "templates").glob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            error(f"invalid JSON template {path.relative_to(ROOT)}: {exc}", failures)

    experiment = json.loads(
        (ROOT / "templates/experiment-config.example.json").read_text(encoding="utf-8")
    )
    if experiment.get("safety", {}).get("allow_attack_execution") is not False:
        error("starter experiment must keep attack execution disabled", failures)


def check_jsonl(failures: list[str]) -> None:
    for path in sorted((ROOT / "templates").glob("*.jsonl")):
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines:
            error(f"empty JSONL template: {path.relative_to(ROOT)}", failures)
            continue
        for number, line in enumerate(lines, start=1):
            if not line.strip():
                error(
                    f"blank JSONL record at {path.relative_to(ROOT)}:{number}", failures
                )
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                error(
                    f"invalid JSONL at {path.relative_to(ROOT)}:{number}: {exc}",
                    failures,
                )


def check_csv(failures: list[str]) -> None:
    for path in sorted((ROOT / "templates").glob("*.csv")):
        try:
            with path.open(newline="", encoding="utf-8") as stream:
                header = next(csv.reader(stream), [])
        except OSError as exc:
            error(f"cannot read CSV template {path.relative_to(ROOT)}: {exc}", failures)
            continue
        if len(header) < 2 or any(not column.strip() for column in header):
            error(f"invalid CSV header: {path.relative_to(ROOT)}", failures)


def check_reserved_trees(failures: list[str]) -> None:
    allowed = {
        "README.md",
        ".gitkeep",
        "phase05_pilot.py",
        "phase06_full.py",
    }
    probe_directory = ROOT / "src/probes"
    unexpected_probes = [
        path.relative_to(ROOT).as_posix()
        for path in probe_directory.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.name not in allowed
    ]
    if unexpected_probes:
        error(
            "unexpected probe files outside the approved Phase 5/6 runners: "
            + ", ".join(unexpected_probes),
            failures,
        )

    phase6_probe = probe_directory / "phase06_full.py"
    if phase6_probe.is_file():
        authorization_path = (
            ROOT
            / "configs"
            / "phase-06-full-run-authorization.v1.1.1.json"
        )
        phase_state_path = ROOT / "docs" / "phase-state.md"
        try:
            authorization = json.loads(
                authorization_path.read_text(encoding="utf-8")
            )
            phase_state = phase_state_path.read_text(encoding="utf-8")
        except (OSError, json.JSONDecodeError) as exc:
            error(
                "Phase 6 runner exists without readable authorization/state "
                f"evidence: {exc}",
                failures,
            )
        else:
            if (
                authorization.get("authorized") is not True
                or authorization.get("authorization_scope")
                != "phase6_full_only"
                or authorization.get("protocol_version") != "1.1.1"
                or "- Gate status: PASSED" not in phase_state
            ):
                error(
                    "Phase 6 runner is not linked to Gate 5 and the exact "
                    "full-run authorization",
                    failures,
                )

    payload_directory = ROOT / "payloads"
    unexpected_payloads = [
        path.relative_to(ROOT).as_posix()
        for path in payload_directory.rglob("*")
        if path.is_file()
        and path.name not in allowed
        and "payloads/phase-05/" not in path.relative_to(ROOT).as_posix()
    ]
    if unexpected_payloads:
        error(
            "payload files exist outside the authorized Phase 5 tree: "
            + ", ".join(unexpected_payloads),
            failures,
        )

    phase5_payloads = [
        path
        for path in (payload_directory / "phase-05").rglob("*")
        if path.is_file()
    ]
    if phase5_payloads:
        required_phase5 = [
            "evidence/setup/phase-05-pilot-authorization.md",
            "evidence/setup/phase-05-evidence-manifest.json",
            "evidence/setup/phase-05-gate-review.md",
            "configs/phase-05-pilot-protocol.v1.0.0.json",
            "configs/phase-05-scenario-catalog.v1.0.0.json",
            "configs/phase-05-final-protocol.v1.1.0.json",
            "configs/phase-05-scenario-catalog.v1.1.0.json",
            "docs/05-final-protocol.md",
            "docs/05-protocol-revision.md",
        ]
        missing_phase5 = [
            relative
            for relative in required_phase5
            if not (ROOT / relative).is_file()
        ]
        if missing_phase5:
            error(
                "Phase 5 payloads require complete authorization, protocol, "
                "and gate evidence: " + ", ".join(missing_phase5),
                failures,
            )


def check_secrets(failures: list[str]) -> None:
    skip = {Path(__file__).resolve()}
    for path in iter_secret_scan_files(ROOT):
        if path.resolve() in skip:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != ".env.example":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                error(f"possible {label} in {path.relative_to(ROOT)}", failures)


def main() -> int:
    failures: list[str] = []
    check_required(failures)
    check_phase_assets(failures)
    check_json(failures)
    check_jsonl(failures)
    check_csv(failures)
    check_reserved_trees(failures)
    check_secrets(failures)

    if failures:
        print(f"\nStarter-pack validation failed with {len(failures)} issue(s).")
        return 1
    print("PASS: required files and directories")
    print("PASS: 9 phase prompts and 9 phase checklists")
    print("PASS: JSON schemas, JSON examples, JSONL, and CSV templates")
    print("PASS: phase-aware probe and payload boundaries")
    print("PASS: secret-pattern scan")
    return 0


if __name__ == "__main__":
    sys.exit(main())

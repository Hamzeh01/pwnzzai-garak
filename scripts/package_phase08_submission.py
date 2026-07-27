"""Create and secret-scan the deterministic Phase 8 submission archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "phase6-full-v1.1.1-20260725T210612Z"
ROOT_FILES = (
    "AGENTS.md",
    "PHASE_GATES.md",
    "README.md",
    "SECURITY_AND_ETHICS.md",
    "VALIDATION.md",
    "pytest.ini",
)
FULL_TREES = (
    "checklists",
    "configs",
    "docs",
    "environment",
    "evidence",
    "payloads",
    "schemas",
    "scripts",
    "src",
    "tests",
)
PAPER_FILES = (
    "README.md",
    "bibliography.bib",
    "claim-evidence.json",
    "reference-verification.json",
    "report-content.md",
    "report-template.md",
    "requirements-report.txt",
    "submission-README.md",
)
HIGH_CONFIDENCE_SECRET_PATTERNS = (
    ("OpenAI API key", re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("GitHub token", re.compile(rb"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b")),
    ("GitHub fine-grained token", re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("AWS access key", re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("private key", re.compile(rb"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
)
FORBIDDEN_PARTS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "dist",
    "downloads",
    "instance",
    "tmp",
    "uploads",
    "vendor",
}
FORBIDDEN_NAMES = {"auth.json", "cookies.json", ".env"}


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_required(value: str, label: str) -> str:
    result = value.strip()
    if not result or "pending" in result.lower() or result.startswith("<"):
        raise ValueError(f"{label} must be confirmed, not a placeholder")
    return result


def eligible(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    lowered = {part.lower() for part in relative.parts}
    if lowered & FORBIDDEN_PARTS:
        return False
    if path.name.lower() in FORBIDDEN_NAMES:
        return False
    return not (
        path.name.startswith("~$")
        or path.suffix.lower() in {".pyc", ".pyo", ".tmp"}
    )


def iter_tree(relative: str) -> Iterable[Path]:
    base = ROOT / relative
    for path in sorted(base.rglob("*")):
        if path.is_file() and eligible(path):
            yield path


def selected_sources(report_dir: Path, group_number: str) -> list[Path]:
    paths: list[Path] = [ROOT / name for name in ROOT_FILES]
    for tree in FULL_TREES:
        paths.extend(iter_tree(tree))
    paths.extend(ROOT / "paper" / name for name in PAPER_FILES)
    paths.append(ROOT / "paper" / "generated" / "phase-08-category-outcomes.png")
    paths.extend(
        [
            ROOT / "references" / "PRIMARY_SOURCES.md",
            ROOT / "references" / "RESEARCH_LOG.md",
            ROOT / "references" / "source-documents" / "README.md",
            ROOT / "results" / "raw" / "README.md",
            ROOT / "results" / "normalized" / "README.md",
            ROOT / "results" / "tables" / "README.md",
            ROOT / "results" / "figures" / "README.md",
        ]
    )
    paths.extend(iter_tree(f"results/raw/{RUN_ID}"))
    paths.extend(
        [
            ROOT / "results" / "normalized" / f"{RUN_ID}.jsonl",
            ROOT / "results" / "normalized" / f"{RUN_ID}.adjudicated.jsonl",
        ]
    )
    paths.extend(sorted((ROOT / "results" / "tables").glob("phase-07-*")))
    paths.extend(sorted((ROOT / "results" / "figures").glob("phase-07-*")))
    paths.extend(
        [
            report_dir / f"G{group_number}_paper.pdf",
            report_dir / f"G{group_number}_paper.docx",
        ]
    )
    unique = {path.resolve(): path for path in paths}
    missing = [str(path) for path in unique if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "required submission inputs missing:\n" + "\n".join(missing)
        )
    return sorted(unique)


def archive_name(path: Path, report_dir: Path, group_number: str) -> Path:
    if path.parent.resolve() == report_dir.resolve() and path.name.startswith(
        f"G{group_number}_paper."
    ):
        return Path(path.name)
    return path.resolve().relative_to(ROOT.resolve())


def scan_tree(root: Path) -> list[str]:
    findings: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        lowered_parts = {part.lower() for part in relative.parts}
        if lowered_parts & FORBIDDEN_PARTS:
            findings.append(f"forbidden path: {relative.as_posix()}")
        if path.name.lower() in FORBIDDEN_NAMES:
            findings.append(f"forbidden filename: {relative.as_posix()}")
        if (
            path.name.startswith("~$")
            or path.suffix.lower() in {".pyc", ".pyo", ".tmp"}
        ):
            findings.append(f"temporary file: {relative.as_posix()}")
        data = path.read_bytes()
        for label, pattern in HIGH_CONFIDENCE_SECRET_PATTERNS:
            if pattern.search(data):
                findings.append(f"{label}: {relative.as_posix()}")
    return findings


def write_zip(stage: Path, output: Path) -> None:
    temporary = output.with_suffix(output.suffix + ".tmp")
    with zipfile.ZipFile(
        temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in sorted(stage.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(stage).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info,
                path.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )
    temporary.replace(output)


def build_archive(
    *,
    group_number: str,
    authors: str,
    uploader: str,
    due_date: str,
    due_date_source: str,
    report_dir: Path,
    output_dir: Path,
) -> tuple[Path, Path, Path]:
    group_number = clean_required(group_number, "group number")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", group_number):
        raise ValueError("group number contains unsupported characters")
    authors = clean_required(authors, "authors")
    uploader = clean_required(uploader, "uploader")
    due_date = clean_required(due_date, "due date")
    due_date_source = clean_required(due_date_source, "due-date source")

    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"G{group_number}_submission.zip"
    checksum_path = output_dir / f"G{group_number}_submission.zip.sha256"
    manifest_path = output_dir / f"G{group_number}_submission-manifest.json"

    with tempfile.TemporaryDirectory(
        prefix="phase08-stage-", dir=output_dir
    ) as temp:
        stage = Path(temp)
        for source in selected_sources(report_dir, group_number):
            relative = archive_name(source, report_dir, group_number)
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        shutil.copy2(
            stage / "paper" / "submission-README.md",
            stage / "SUBMISSION_README.md",
        )
        hashes = {
            path.relative_to(stage).as_posix(): sha256_path(path)
            for path in sorted(stage.rglob("*"))
            if path.is_file()
        }
        metadata = {
            "schema_version": "1.0.0",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "group_number": group_number,
            "authors": authors,
            "designated_ilearn_uploader": uploader,
            "uploaders_designated": 1,
            "due_date": due_date,
            "due_date_source": due_date_source,
            "report_basename": f"G{group_number}_paper",
            "main_text_pages": 6,
            "references_start_page": 7,
            "appendices_start_page": 8,
            "visual_pdf_review_pages": "1-18",
            "selected_run_id": RUN_ID,
            "files_before_metadata": len(hashes),
            "file_sha256": hashes,
        }
        (stage / "SUBMISSION_METADATA.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        findings = scan_tree(stage)
        if findings:
            raise ValueError(
                "submission secret/temp scan failed:\n" + "\n".join(findings)
            )
        write_zip(stage, archive_path)

    with zipfile.ZipFile(archive_path) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise ValueError(f"ZIP integrity failure at {corrupt}")
        member_count = len(archive.infolist())
    archive_sha256 = sha256_path(archive_path)
    checksum_path.write_text(
        f"{archive_sha256}  {archive_path.name}\n", encoding="ascii"
    )
    external_manifest = {
        "archive": archive_path.name,
        "sha256": archive_sha256,
        "member_count": member_count,
        "secret_temp_scan": "pass",
        "group_number": group_number,
        "authors": authors,
        "designated_ilearn_uploader": uploader,
        "uploaders_designated": 1,
        "due_date": due_date,
        "due_date_source": due_date_source,
    }
    manifest_path.write_text(
        json.dumps(external_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return archive_path, checksum_path, manifest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group-number", required=True)
    parser.add_argument("--authors", required=True)
    parser.add_argument("--uploader", required=True)
    parser.add_argument("--due-date", required=True)
    parser.add_argument("--due-date-source", required=True)
    parser.add_argument(
        "--report-dir", type=Path, default=ROOT / "dist" / "phase-08"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "dist" / "phase-08"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    archive, checksum, manifest = build_archive(
        group_number=args.group_number,
        authors=args.authors,
        uploader=args.uploader,
        due_date=args.due_date,
        due_date_source=args.due_date_source,
        report_dir=args.report_dir.resolve(),
        output_dir=args.output_dir.resolve(),
    )
    print(f"PASS: wrote {archive}")
    print(f"PASS: wrote {checksum}")
    print(f"PASS: wrote {manifest}")
    print(f"PASS: archive SHA-256 {sha256_path(archive)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Validate Phase 8 report content, formats, references, and final ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Iterable

import pdfplumber
from docx import Document
from docx.oxml.ns import qn

from build_phase08_report import (
    SOURCE_PATH,
    SUMMARY_PATH,
    build_claim_manifest,
    build_tokens,
    read_json,
    substitute_tokens,
)
from package_phase08_submission import (
    FORBIDDEN_NAMES,
    FORBIDDEN_PARTS,
    HIGH_CONFIDENCE_SECRET_PATTERNS,
    ROOT,
    RUN_ID,
    sha256_path,
)


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from walk_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from walk_strings(nested)


def raw_response_strings() -> set[str]:
    strings: set[str] = set()
    raw_root = ROOT / "results" / "raw" / RUN_ID
    for path in raw_root.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        response: Any | None = None
        if isinstance(data.get("exchange"), dict):
            response = data["exchange"].get("response")
        elif "response" in data:
            response = data["response"]
        if response is None:
            continue
        for text in walk_strings(response):
            normalized = " ".join(text.split())
            if len(normalized) >= 12:
                strings.add(normalized)
    return strings


def validate_source_and_evidence(failures: list[str]) -> None:
    summary = read_json(SUMMARY_PATH)
    source = SOURCE_PATH.read_text(encoding="utf-8")
    rendered = substitute_tokens(source, build_tokens(summary))
    main, remainder = rendered.split("<!-- MAIN TEXT END -->", maxsplit=1)

    require(main.count("<!-- PAGE BREAK -->") == 5, "main source is not six pages", failures)
    require("{{" not in rendered, "unresolved report token remains", failures)
    require(remainder.lstrip().startswith("## References"), "references do not follow main text", failures)
    require(
        "<!-- APPENDICES GENERATED FROM RETAINED EVIDENCE -->" in remainder,
        "generated appendices marker missing",
        failures,
    )
    for expected in (
        "14/28",
        "10/12",
        "0/6",
        "4/4",
        "0/9",
        "43 terminal workflow records",
        "79 target requests",
    ):
        require(expected in main, f"verified numeric claim missing: {expected}", failures)

    expected_manifest = build_claim_manifest(summary)
    actual_manifest = read_json(ROOT / "paper" / "claim-evidence.json")
    require(actual_manifest == expected_manifest, "claim-evidence manifest is stale", failures)

    normalized_main = " ".join(
        re.sub(r"<!--.*?-->", " ", main, flags=re.DOTALL).split()
    )
    quoted = sorted(
        value for value in raw_response_strings() if value in normalized_main
    )
    require(
        not quoted,
        "raw model response appears verbatim in main text: " + "; ".join(quoted[:3]),
        failures,
    )
    require(
        "Codex also assisted report drafting and formatting" in source,
        "AI-assistance analysis/disclosure missing",
        failures,
    )


def validate_references(failures: list[str]) -> None:
    verification = read_json(ROOT / "paper" / "reference-verification.json")
    references = verification.get("references", [])
    require(len(references) == 7, "reference verification count is not seven", failures)
    require(
        all(item.get("resolved") is True for item in references),
        "one or more reference URLs did not resolve",
        failures,
    )
    source = SOURCE_PATH.read_text(encoding="utf-8")
    for item in references:
        require(
            item["url"] in source,
            f"verified reference URL absent from report: {item['url']}",
            failures,
        )


def validate_pdf(
    path: Path, group_number: str, authors: str, failures: list[str]
) -> int:
    require(path.name == f"G{group_number}_paper.pdf", "PDF basename is incorrect", failures)
    with pdfplumber.open(path) as report:
        page_count = len(report.pages)
        texts = [(page.extract_text() or "") for page in report.pages]
        for index, page in enumerate(report.pages, start=1):
            require(abs(float(page.width) - 612.0) < 1, f"PDF page {index} is not Letter width", failures)
            require(abs(float(page.height) - 792.0) < 1, f"PDF page {index} is not Letter height", failures)
    require(page_count == 18, f"PDF has {page_count} pages, expected 18", failures)
    if page_count >= 8:
        require("References" in texts[6], "references do not begin on PDF page 7", failures)
        require(
            "Appendix A. Environment and Reproducibility Pins" in texts[7],
            "appendices do not begin on PDF page 8",
            failures,
        )
    require(
        all("Appendix A." not in text for text in texts[:6]),
        "appendix content appears within six-page main text",
        failures,
    )
    require(
        all(not text.lstrip().startswith("References") for text in texts[:6]),
        "references appear within six-page main text",
        failures,
    )
    if texts:
        require(f"Group {group_number}" in texts[0], "group number absent from PDF", failures)
        require(authors in texts[0], "author roster absent from PDF", failures)
    return page_count


def validate_docx(
    path: Path, group_number: str, authors: str, failures: list[str]
) -> None:
    require(path.name == f"G{group_number}_paper.docx", "Word basename is incorrect", failures)
    with zipfile.ZipFile(path) as package:
        require(package.testzip() is None, "Word ZIP/OOXML package is corrupt", failures)
        names = set(package.namelist())
        require("word/document.xml" in names, "Word document XML missing", failures)
        core_xml = package.read("docProps/core.xml").decode("utf-8")
        require(
            not re.search(r"<dc:creator>[^<]+", core_xml),
            "Word creator metadata was not scrubbed",
            failures,
        )
        require(
            not re.search(r"<cp:lastModifiedBy>[^<]+", core_xml),
            "Word last-modified-by metadata was not scrubbed",
            failures,
        )
    document = Document(path)
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    require(f"Group {group_number}" in text, "group number absent from Word", failures)
    require(authors in text, "author roster absent from Word", failures)
    require("14/28" in text and "43 terminal workflow records" in text, "Word content is missing verified results", failures)
    for section_index, section in enumerate(document.sections, start=1):
        columns = section._sectPr.find(qn("w:cols"))
        count = 1 if columns is None else int(columns.get(qn("w:num"), "1"))
        require(count == 1, f"Word section {section_index} is not single-column", failures)


def validate_zip(
    *,
    archive_path: Path,
    checksum_path: Path,
    manifest_path: Path,
    group_number: str,
    authors: str,
    uploader: str,
    due_date: str,
    due_date_source: str,
    failures: list[str],
) -> None:
    digest = sha256_path(archive_path)
    checksum_line = checksum_path.read_text(encoding="ascii").strip()
    require(checksum_line == f"{digest}  {archive_path.name}", "external ZIP checksum file does not match", failures)
    external = read_json(manifest_path)
    require(external.get("sha256") == digest, "external archive manifest checksum does not match", failures)
    require(external.get("secret_temp_scan") == "pass", "external manifest lacks passed secret scan", failures)

    with zipfile.ZipFile(archive_path) as archive:
        require(archive.testzip() is None, "ZIP integrity test failed", failures)
        names = archive.namelist()
        required = {
            f"G{group_number}_paper.pdf",
            f"G{group_number}_paper.docx",
            "SUBMISSION_METADATA.json",
            "SUBMISSION_README.md",
            "paper/claim-evidence.json",
            "configs/phase-06-execution-protocol.v1.1.1.json",
            f"results/normalized/{RUN_ID}.adjudicated.jsonl",
            f"results/raw/{RUN_ID}/events.jsonl",
            "scripts/validate_phase08_submission.py",
            "src/analysis/phase07.py",
            "tests/unit/test_phase08_reporting.py",
        }
        require(required.issubset(set(names)), "ZIP is missing required report/reproduction files", failures)
        for name in names:
            path = Path(name)
            lowered = {part.lower() for part in path.parts}
            require(not (lowered & FORBIDDEN_PARTS), f"forbidden archive path: {name}", failures)
            require(path.name.lower() not in FORBIDDEN_NAMES, f"forbidden archive filename: {name}", failures)
            require(
                not (path.name.startswith("~$") or path.suffix.lower() in {".pyc", ".pyo", ".tmp"}),
                f"temporary archive file: {name}",
                failures,
            )
            data = archive.read(name)
            for label, pattern in HIGH_CONFIDENCE_SECRET_PATTERNS:
                require(not pattern.search(data), f"{label} found in archive member {name}", failures)

        metadata = json.loads(archive.read("SUBMISSION_METADATA.json"))
        expected_fields = {
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
        }
        for key, expected in expected_fields.items():
            require(metadata.get(key) == expected, f"submission metadata mismatch for {key}", failures)
        for name, expected_hash in metadata.get("file_sha256", {}).items():
            require(name in names, f"hashed archive member missing: {name}", failures)
            if name in names:
                actual = hashlib.sha256(archive.read(name)).hexdigest()
                require(actual == expected_hash, f"archive member hash mismatch: {name}", failures)


def validate_phase08(
    *,
    group_number: str,
    authors: str,
    uploader: str,
    due_date: str,
    due_date_source: str,
    output_dir: Path,
) -> list[str]:
    failures: list[str] = []
    report_pdf = output_dir / f"G{group_number}_paper.pdf"
    report_docx = output_dir / f"G{group_number}_paper.docx"
    archive = output_dir / f"G{group_number}_submission.zip"
    checksum = output_dir / f"G{group_number}_submission.zip.sha256"
    manifest = output_dir / f"G{group_number}_submission-manifest.json"
    for path in (report_pdf, report_docx, archive, checksum, manifest):
        require(path.is_file(), f"required final artifact missing: {path}", failures)
    if failures:
        return failures

    validate_source_and_evidence(failures)
    validate_references(failures)
    validate_pdf(report_pdf, group_number, authors, failures)
    validate_docx(report_docx, group_number, authors, failures)
    validate_zip(
        archive_path=archive,
        checksum_path=checksum,
        manifest_path=manifest,
        group_number=group_number,
        authors=authors,
        uploader=uploader,
        due_date=due_date,
        due_date_source=due_date_source,
        failures=failures,
    )
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group-number", required=True)
    parser.add_argument("--authors", required=True)
    parser.add_argument("--uploader", required=True)
    parser.add_argument("--due-date", required=True)
    parser.add_argument("--due-date-source", required=True)
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "dist" / "phase-08"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failures = validate_phase08(
        group_number=args.group_number.strip(),
        authors=args.authors.strip(),
        uploader=args.uploader.strip(),
        due_date=args.due_date.strip(),
        due_date_source=args.due_date_source.strip(),
        output_dir=args.output_dir.resolve(),
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: Phase 8 report, evidence, references, formats, and archive validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

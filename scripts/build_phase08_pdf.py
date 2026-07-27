"""Build the Phase 8 PDF from the same evidence-backed report source as DOCX."""

from __future__ import annotations

import argparse
import html
import json
import re
import textwrap
from pathlib import Path
from typing import Any, Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    LongTable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from build_phase08_report import (
    CATALOG_PATH,
    CLAIMS_PATH,
    ROOT,
    RISK_PATH,
    SOURCE_PATH,
    STRATA_PATH,
    SUMMARY_PATH,
    build_claim_manifest,
    build_tokens,
    category_rows,
    draw_category_figure,
    outcome,
    pct,
    read_csv,
    read_json,
    substitute_tokens,
)


INK = colors.HexColor("#101828")
MUTED = colors.HexColor("#475467")
BLUE = colors.HexColor("#1F4D78")
LIGHT_BLUE = colors.HexColor("#E8EEF5")
LIGHT_GRAY = colors.HexColor("#F2F4F7")
GRID = colors.HexColor("#B8C1CC")


def clean_inline(text: str) -> str:
    return html.escape(text.replace("**", "").replace("`", ""))


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "AcademicBody",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=8.65,
            leading=9.85,
            alignment=TA_JUSTIFY,
            textColor=INK,
            spaceAfter=3.0,
            allowWidows=1,
            allowOrphans=1,
        ),
        "reference": ParagraphStyle(
            "AcademicReference",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=8.4,
            leading=9.7,
            alignment=TA_LEFT,
            textColor=INK,
            spaceAfter=4.0,
        ),
        "title": ParagraphStyle(
            "AcademicTitle",
            parent=base["Title"],
            fontName="Times-Bold",
            fontSize=15,
            leading=17,
            alignment=TA_CENTER,
            textColor=INK,
            spaceAfter=2,
        ),
        "meta": ParagraphStyle(
            "AcademicMeta",
            parent=base["BodyText"],
            fontName="Times-Italic",
            fontSize=8.5,
            leading=10,
            alignment=TA_CENTER,
            textColor=MUTED,
            spaceAfter=4,
        ),
        "h1": ParagraphStyle(
            "AcademicH1",
            parent=base["Heading1"],
            fontName="Times-Bold",
            fontSize=10.6,
            leading=11.8,
            textColor=INK,
            spaceBefore=4,
            spaceAfter=2,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "AcademicH2",
            parent=base["Heading2"],
            fontName="Times-BoldItalic",
            fontSize=9.2,
            leading=10.4,
            textColor=BLUE,
            spaceBefore=3,
            spaceAfter=1.5,
            keepWithNext=True,
        ),
        "caption": ParagraphStyle(
            "AcademicCaption",
            parent=base["BodyText"],
            fontName="Times-Italic",
            fontSize=7.0,
            leading=8.0,
            textColor=MUTED,
            spaceBefore=1,
            spaceAfter=2,
            keepWithNext=True,
        ),
        "appendix_body": ParagraphStyle(
            "AppendixBody",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=7.7,
            leading=8.8,
            alignment=TA_JUSTIFY,
            textColor=INK,
            spaceAfter=3,
        ),
        "appendix_h1": ParagraphStyle(
            "AppendixH1",
            parent=base["Heading1"],
            fontName="Times-Bold",
            fontSize=12,
            leading=14,
            textColor=INK,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "appendix_h2": ParagraphStyle(
            "AppendixH2",
            parent=base["Heading2"],
            fontName="Times-Bold",
            fontSize=8.8,
            leading=10,
            textColor=BLUE,
            spaceBefore=4,
            spaceAfter=2,
            keepWithNext=True,
        ),
        "code": ParagraphStyle(
            "AppendixCode",
            parent=base["Code"],
            fontName="Courier",
            fontSize=5.8,
            leading=6.7,
            leftIndent=5,
            rightIndent=5,
            backColor=LIGHT_GRAY,
            borderPadding=4,
            spaceAfter=4,
        ),
        "cell": ParagraphStyle(
            "Cell",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=6.1,
            leading=7.0,
            textColor=INK,
            alignment=TA_LEFT,
        ),
        "cell_center": ParagraphStyle(
            "CellCenter",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=6.1,
            leading=7.0,
            textColor=INK,
            alignment=TA_CENTER,
        ),
        "cell_header": ParagraphStyle(
            "CellHeader",
            parent=base["BodyText"],
            fontName="Times-Bold",
            fontSize=6.2,
            leading=7.2,
            textColor=INK,
            alignment=TA_CENTER,
        ),
    }


def header_footer(canvas: Any, doc: Any, group_number: str) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        doc.leftMargin,
        letter[1] - 0.36 * inch,
        f"PwnzzAI application-layer assessment | Group {group_number}",
    )
    canvas.drawRightString(
        letter[0] - doc.rightMargin,
        0.34 * inch,
        f"Page {doc.page}",
    )
    canvas.restoreState()


def table_flow(
    headers: list[str],
    rows: Iterable[Iterable[Any]],
    col_widths: list[float],
    report_styles: dict[str, ParagraphStyle],
    *,
    repeat: bool = True,
) -> LongTable:
    data: list[list[Any]] = [
        [
            Paragraph(clean_inline(str(header)), report_styles["cell_header"])
            for header in headers
        ]
    ]
    for values in rows:
        rendered = []
        for index, value in enumerate(values):
            style = report_styles["cell"] if index == 0 else report_styles["cell_center"]
            rendered.append(Paragraph(clean_inline(str(value)), style))
        data.append(rendered)
    table = LongTable(
        data,
        colWidths=col_widths,
        repeatRows=1 if repeat else 0,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
                ("GRID", (0, 0), (-1, -1), 0.35, GRID),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return table


def category_table(
    summary: dict[str, Any], report_styles: dict[str, ParagraphStyle]
) -> list[Any]:
    label_map = {
        "data_poisoning": "Data poisoning",
        "direct_prompt_injection": "Direct injection",
        "indirect_prompt_injection": "Indirect injection",
        "information_disclosure": "Disclosure",
    }
    rows = [
        [
            label_map[row["value"]],
            f'{row["success"]}/{row["asr_denominator"]}',
            row["failure"],
            row["ambiguous"],
            pct(float(row["asr"])),
        ]
        for row in category_rows()
    ]
    return [
        Paragraph(
            "Table 1. Adjudicated adversarial outcomes. Source: "
            f'{summary["run_id"]}; results/tables/phase-07-stratified-outcomes.csv.',
            report_styles["caption"],
        ),
        table_flow(
            ["Category", "Success", "Failure", "Ambig.", "ASR"],
            rows,
            [2.05 * inch, 0.8 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch],
            report_styles,
        ),
    ]


def category_figure(
    summary: dict[str, Any], report_styles: dict[str, ParagraphStyle]
) -> list[Any]:
    path = draw_category_figure()
    return [
        Spacer(1, 1.5),
        Image(str(path), width=5.55 * inch, height=1.76 * inch),
        Paragraph(
            "Figure 1. Four-way category outcomes. Source: "
            f'{summary["run_id"]}; generated from phase-07-stratified-outcomes.csv.',
            report_styles["caption"],
        ),
    ]


def owasp_table(report_styles: dict[str, ParagraphStyle]) -> list[Any]:
    rows = [
        ["Direct injection", "PI-01", "LLM01:2025", "10/12 success"],
        ["Indirect QR injection", "PI-01", "LLM01:2025", "0/6; 1 ambiguous"],
        [
            "Disclosure/system context",
            "SD-01/SP-01",
            "LLM02/LLM07 if consequence",
            "0/6; no finding",
        ],
        ["Classifier poisoning", "DI-01", "LLM04:2025", "4/4 success"],
    ]
    return [
        Paragraph(
            "Table 2. OWASP mapping uses taxonomy, not severity. Sources: OWASP [4], [5] and retained Phase 7 outcomes.",
            report_styles["caption"],
        ),
        table_flow(
            ["Scenario", "Policy", "OWASP mapping", "Observed result"],
            rows,
            [1.45 * inch, 0.9 * inch, 2.25 * inch, 1.45 * inch],
            report_styles,
        ),
    ]


def mitigation_table(report_styles: dict[str, ParagraphStyle]) -> list[Any]:
    rows = read_csv(ROOT / "results" / "tables" / "phase-07-mitigation-matrix.csv")
    return [
        Paragraph(
            "Table 3. Application-layer mitigation chain and validation. Source: "
            "results/tables/phase-07-mitigation-matrix.csv.",
            report_styles["caption"],
        ),
        table_flow(
            ["ID", "Layer", "Core control", "Validation focus"],
            [
                [
                    row["mitigation_id"],
                    row["layer"],
                    row["recommendation"],
                    row["validation_test"],
                ]
                for row in rows
            ],
            [0.55 * inch, 0.9 * inch, 2.9 * inch, 2.45 * inch],
            report_styles,
        ),
    ]


def append_body(story: list[Any], text: str, report_styles: dict[str, ParagraphStyle]) -> None:
    story.append(Paragraph(clean_inline(text), report_styles["appendix_body"]))


def append_environment(
    story: list[Any], tokens: dict[str, str], report_styles: dict[str, ParagraphStyle]
) -> None:
    story.extend([PageBreak(), Paragraph("Appendix A. Environment and Reproducibility Pins", report_styles["appendix_h1"])])
    append_body(
        story,
        "The table below is generated from sanitized environment manifests. The full lock, resolved Compose configuration, source/image/model metadata, and artifact hashes are included in the archive.",
        report_styles,
    )
    rows = [
        ["Host", f'Windows 11 Enterprise build {tokens["WINDOWS_BUILD"]}'],
        ["Docker", f'Desktop {tokens["DOCKER_DESKTOP_VERSION"]}; Engine {tokens["DOCKER_ENGINE_VERSION"]}'],
        ["Python / Garak", f'{tokens["PYTHON_VERSION"]} / {tokens["GARAK_VERSION"]}'],
        ["PwnzzAI source", tokens["PWNZZAI_COMMIT"]],
        ["PwnzzAI image", tokens["PWNZZAI_IMAGE_DIGEST"]],
        ["Ollama", tokens["OLLAMA_VERSION"]],
        ["Principal model", f'{tokens["MODEL_TAG"]}; {tokens["MODEL_PARAMETER_SIZE"]}; {tokens["MODEL_QUANTIZATION"]}'],
        ["Model digest", tokens["MODEL_DIGEST"]],
        ["Application bind", "127.0.0.1:18080"],
        ["Ollama bind", "127.0.0.1:11434"],
    ]
    story.append(
        table_flow(
            ["Item", "Frozen value"],
            rows,
            [1.45 * inch, 5.35 * inch],
            report_styles,
        )
    )
    append_body(
        story,
        "Primary files: environment/system-info.json, python-environment.txt, ollama-models.json, pwnzzai-commit.txt, pwnzzai-image-digest.txt, requirements-lock.txt, compose-resolved.yml, and artifact-hashes.txt.",
        report_styles,
    )


def wrapped_code(text: str, width: int = 112) -> str:
    wrapped = []
    for line in text.splitlines():
        if not line:
            wrapped.append("")
            continue
        wrapped.extend(
            textwrap.wrap(
                line,
                width=width,
                replace_whitespace=False,
                drop_whitespace=False,
                break_long_words=True,
                break_on_hyphens=False,
            )
            or [""]
        )
    return "\n".join(wrapped)


def append_catalog_and_payloads(
    story: list[Any], report_styles: dict[str, ParagraphStyle]
) -> None:
    story.extend([PageBreak(), Paragraph("Appendix B. Scenario Catalog and Full Payloads", report_styles["appendix_h1"])])
    catalog = read_json(CATALOG_PATH)
    append_body(
        story,
        f'The authoritative catalog is {CATALOG_PATH.relative_to(ROOT)} ({len(catalog["cases"])} cases). Entries preserve the objective, policy, surface, repetitions, expected secure behavior, detector, artifact hash, and reset.',
        report_styles,
    )
    for case in catalog["cases"]:
        story.append(
            Paragraph(
                clean_inline(f'{case["test_case_id"]}: {case["title"]}'),
                report_styles["appendix_h2"],
            )
        )
        surface = case["surface"]
        append_body(
            story,
            f'Category/family: {case["category"]} / {case["family"]}. Policy: {case["policy_id"]}. Surface: {surface["method"]} {surface["path"]}. Repetitions: {case["repetitions"]}. Objective: {case["objective"]} Expected secure behavior: {case["expected_secure_behavior"]} Detector(s): {", ".join(case["automatic_detector_ids"])}.',
            report_styles,
        )
        artifact = case["input_artifact"]
        append_body(
            story,
            f'Input artifact: {artifact["path"]}; SHA-256 {artifact["sha256"]}. Reset/isolation: {case["state"]["reset"]}',
            report_styles,
        )

    story.append(Paragraph("B.1 Payload artifact contents", report_styles["appendix_h2"]))
    payload_root = ROOT / "payloads" / "phase-05"
    for path in sorted(payload_root.rglob("*")):
        if not path.is_file():
            continue
        story.append(
            Paragraph(
                clean_inline(str(path.relative_to(ROOT)).replace("\\", "/")),
                report_styles["appendix_h2"],
            )
        )
        if path.suffix.lower() == ".png":
            story.append(Image(str(path), width=1.15 * inch, height=1.15 * inch))
            story.append(
                Paragraph(
                    f"QR input artifact; full-resolution PNG is included in the archive ({path.stat().st_size} bytes).",
                    report_styles["caption"],
                )
            )
        else:
            raw = path.read_text(encoding="utf-8")
            if path.suffix.lower() == ".json":
                raw = json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
            story.append(Preformatted(wrapped_code(raw), report_styles["code"]))


def compact_csv(
    story: list[Any],
    report_styles: dict[str, ParagraphStyle],
    *,
    title: str,
    path: Path,
    columns: list[tuple[str, str]],
    widths: list[float],
    predicate: Any | None = None,
) -> None:
    rows = read_csv(path)
    if predicate is not None:
        rows = [row for row in rows if predicate(row)]
    story.append(
        Paragraph(
            f"{clean_inline(title)}. Full machine-readable table: {clean_inline(str(path.relative_to(ROOT)))}.",
            report_styles["caption"],
        )
    )
    story.append(
        table_flow(
            [label for _, label in columns],
            [[row[key] for key, _ in columns] for row in rows],
            widths,
            report_styles,
        )
    )
    story.append(Spacer(1, 4))


def append_results(story: list[Any], report_styles: dict[str, ParagraphStyle]) -> None:
    story.extend([PageBreak(), Paragraph("Appendix C. Extended Results", report_styles["appendix_h1"])])
    compact_csv(
        story,
        report_styles,
        title="Table C1. All outcome populations",
        path=ROOT / "results" / "tables" / "phase-07-outcomes.csv",
        columns=[
            ("population", "Population"), ("total", "n"), ("success", "S"),
            ("failure", "F"), ("ambiguous", "A"), ("error", "E"),
            ("success_numerator", "Num."), ("success_denominator", "Den."),
        ],
        widths=[2.25 * inch, 0.45 * inch, 0.45 * inch, 0.45 * inch, 0.45 * inch, 0.45 * inch, 0.65 * inch, 0.65 * inch],
    )
    compact_csv(
        story,
        report_styles,
        title="Table C2. Family-level adversarial outcomes",
        path=STRATA_PATH,
        predicate=lambda row: row["population"] == "adversarial" and row["dimension"] == "family",
        columns=[
            ("value", "Family"), ("total", "n"), ("success", "S"),
            ("failure", "F"), ("ambiguous", "A"), ("error", "E"), ("asr", "ASR"),
        ],
        widths=[3.05 * inch, 0.5 * inch, 0.5 * inch, 0.5 * inch, 0.5 * inch, 0.5 * inch, 0.65 * inch],
    )
    compact_csv(
        story,
        report_styles,
        title="Table C3. Automatic/manual label comparison",
        path=ROOT / "results" / "tables" / "phase-07-label-comparison.csv",
        columns=[
            ("automatic_label", "Automatic"), ("manual_success", "Manual S"),
            ("manual_failure", "Manual F"), ("manual_ambiguous", "Manual A"),
            ("manual_error", "Manual E"), ("unreviewed", "Unreviewed"), ("total", "Total"),
        ],
        widths=[1.4 * inch, 0.85 * inch, 0.85 * inch, 0.85 * inch, 0.85 * inch, 1.0 * inch, 0.6 * inch],
    )
    compact_csv(
        story,
        report_styles,
        title="Table C4. Disclosure coverage",
        path=ROOT / "results" / "tables" / "phase-07-disclosure.csv",
        columns=[
            ("data_class", "Data class"), ("test_case_id", "Case"),
            ("attempts", "n"), ("confirmed_exposures", "Exposed"),
            ("ambiguous", "Ambig."), ("errors", "Errors"),
        ],
        widths=[2.25 * inch, 1.8 * inch, 0.5 * inch, 0.75 * inch, 0.75 * inch, 0.65 * inch],
    )
    compact_csv(
        story,
        report_styles,
        title="Table C5. Poisoning comparisons",
        path=ROOT / "results" / "tables" / "phase-07-poisoning.csv",
        predicate=lambda row: row["strategy"] != "clean_baseline",
        columns=[
            ("test_case_id", "Case"), ("strategy", "Strategy"), ("budget", "b"),
            ("poison_ratio", "Ratio"), ("baseline_accuracy", "Base"),
            ("poisoned_accuracy", "Poison"), ("accuracy_degradation", "Degrad."),
            ("prediction_flip_rate", "Flip"), ("targeted_success", "Target"),
        ],
        widths=[1.6 * inch, 0.7 * inch, 0.35 * inch, 0.55 * inch, 0.55 * inch, 0.6 * inch, 0.6 * inch, 0.5 * inch, 0.65 * inch],
    )
    compact_csv(
        story,
        report_styles,
        title="Table C6. Latency by application surface",
        path=ROOT / "results" / "tables" / "phase-07-latency.csv",
        columns=[
            ("surface", "Surface"), ("record_unit", "Record unit"), ("record_count", "n"),
            ("median_ms", "Median"), ("q1_ms", "Q1"), ("q3_ms", "Q3"),
            ("iqr_ms", "IQR"), ("mean_ms", "Mean"),
        ],
        widths=[1.45 * inch, 1.65 * inch, 0.45 * inch, 0.65 * inch, 0.55 * inch, 0.55 * inch, 0.55 * inch, 0.65 * inch],
    )
    compact_csv(
        story,
        report_styles,
        title="Table C7. Risk register",
        path=ROOT / "results" / "tables" / "phase-07-risk-register.csv",
        columns=[
            ("finding_id", "ID"), ("title", "Finding"), ("policy_id", "Policy"),
            ("owasp", "OWASP"), ("likelihood", "L"), ("impact", "I"),
            ("risk_score", "Score"), ("rating", "Band"),
        ],
        widths=[0.55 * inch, 2.7 * inch, 0.6 * inch, 0.8 * inch, 0.35 * inch, 0.35 * inch, 0.5 * inch, 0.6 * inch],
    )
    append_body(
        story,
        "The archive also includes phase-07-reproducibility.csv, phase-07-mitigation-matrix.csv, all raw records for the complete run, the original and adjudicated normalized JSONL, and the manual-review JSONL.",
        report_styles,
    )


def append_evidence(
    story: list[Any], summary: dict[str, Any], report_styles: dict[str, ParagraphStyle]
) -> None:
    story.extend([PageBreak(), Paragraph("Appendix D. Claim-Evidence and Raw Record Index", report_styles["appendix_h1"])])
    manifest = build_claim_manifest(summary)
    CLAIMS_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rows = [
        [claim["claim_id"], claim["claim"], "; ".join(claim["evidence"])]
        for claim in manifest["claims"]
    ]
    story.append(
        table_flow(
            ["Claim", "Description", "Regeneration source"],
            rows,
            [0.65 * inch, 2.1 * inch, 4.0 * inch],
            report_styles,
        )
    )
    append_body(
        story,
        f'Headline normalized input: {summary["headline_input"]}. Raw evidence is indexed by attempt_id under results/raw/{summary["run_id"]}/. The Phase 7 analysis manifest records every generated table/figure hash; the Phase 6 evidence manifest records the complete-run raw and normalized evidence.',
        report_styles,
    )
    story.append(
        Preformatted(
            "\n".join(
                [
                    "Adjudicated JSONL SHA-256:",
                    "a79bbd9a7a985b8d3212449c2e3661090c63ce6bc0b8e261a3243a4a3966ad12",
                    "Protocol SHA-256:",
                    "e4b7fcee0a3fc7ee2acb297b65d977f01d8a9f0a2615cbb55f0df4e365a9366b",
                    "Catalog SHA-256:",
                    "56ea8ccf77ffeb1d5e0e9def28e601996341cfa7f712bbfb5540188826183cbb",
                ]
            ),
            report_styles["code"],
        )
    )


def append_reproduction(
    story: list[Any],
    group_number: str,
    authors: str,
    report_styles: dict[str, ParagraphStyle],
) -> None:
    story.extend([PageBreak(), Paragraph("Appendix E. Reproduction Commands", report_styles["appendix_h1"])])
    append_body(
        story,
        "The default path reproduces analysis from the retained run without contacting a target or requiring credentials. From the extracted submission root in Windows PowerShell:",
        report_styles,
    )
    commands = "\n".join(
        [
            "py -3.12 -m venv .venv",
            ".\\.venv\\Scripts\\python.exe -m pip install -r environment\\requirements-lock.txt",
            ".\\.venv\\Scripts\\python.exe scripts\\validate_pack.py",
            ".\\.venv\\Scripts\\python.exe scripts\\validate_phase05_protocol.py",
            ".\\.venv\\Scripts\\python.exe scripts\\validate_phase06_execution.py",
            ".\\.venv\\Scripts\\python.exe scripts\\validate_records.py results\\normalized\\phase6-full-v1.1.1-20260725T210612Z.adjudicated.jsonl",
            ".\\.venv\\Scripts\\python.exe scripts\\analyze_phase07.py --check",
            ".\\.venv\\Scripts\\python.exe scripts\\validate_phase07_analysis.py",
            ".\\.venv\\Scripts\\python.exe -m pytest -q",
        ]
    )
    story.append(Preformatted(wrapped_code(commands), report_styles["code"]))
    append_body(
        story,
        "A clean-machine experiment repeat additionally requires the pinned local PwnzzAI/Ollama environment, loopback bindings, exact model/image/source digests, benign health/reset verification, and new explicit execution authorization. The historical Phase 6 authorization receipt must not be reused on another system.",
        report_styles,
    )
    story.append(
        Preformatted(
            wrapped_code(
                ".\\.venv\\Scripts\\python.exe scripts\\build_phase08_report.py "
                f'--group-number "{group_number}" --authors "{authors}" '
                "--output-dir dist\\phase-08"
            ),
            report_styles["code"],
        )
    )


def append_ai(story: list[Any], report_styles: dict[str, ParagraphStyle]) -> None:
    story.extend([PageBreak(), Paragraph("Appendix F. AI Assistance, Editing, and Sanitization", report_styles["appendix_h1"])])
    append_body(
        story,
        "Codex assisted with source review, evidence-linked analysis, report drafting, formatting, and validation. Generated prose was edited against the verified assignment matrix, frozen policies, retained run, programmatic Phase 7 tables, risk records, and official references. Numeric statements are represented in paper/claim-evidence.json and regenerated from retained inputs.",
        report_styles,
    )
    append_body(
        story,
        "No model response is quoted in the six-page main text. Full experiment outputs remain untrusted data in retained JSON/JSONL evidence and are included for audit rather than as instructions or unanalyzed narrative. Exact synthetic payloads are confined to Appendix B and the dataset tree. Secret patterns, temporary files, document metadata, references, page count, and archive integrity are checked by the Phase 8 validation workflow.",
        report_styles,
    )
    append_body(
        story,
        "Required final human action: verify the author roster, group number, uploader designation, due date, and scientific interpretation before Ilearn submission. The archive is not uploaded automatically.",
        report_styles,
    )


def build_pdf(
    *,
    group_number: str,
    authors: str,
    output_dir: Path,
) -> Path:
    summary = read_json(SUMMARY_PATH)
    tokens = build_tokens(summary)
    source = substitute_tokens(SOURCE_PATH.read_text(encoding="utf-8"), tokens)
    report_styles = styles()
    story: list[Any] = []
    paragraph_buffer: list[str] = []
    in_references = False

    def flush() -> None:
        if paragraph_buffer:
            story.append(
                Paragraph(
                    clean_inline(" ".join(paragraph_buffer).strip()),
                    report_styles["reference" if in_references else "body"],
                )
            )
            paragraph_buffer.clear()

    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            continue
        if line in {"<!-- PAGE BREAK -->", "<!-- MAIN TEXT END -->"}:
            flush()
            story.append(PageBreak())
            continue
        if line == "<!-- APPENDICES GENERATED FROM RETAINED EVIDENCE -->":
            flush()
            append_environment(story, tokens, report_styles)
            append_catalog_and_payloads(story, report_styles)
            append_results(story, report_styles)
            append_evidence(story, summary, report_styles)
            append_reproduction(story, group_number, authors, report_styles)
            append_ai(story, report_styles)
            continue
        if line == "[[TABLE:CATEGORY_OUTCOMES]]":
            flush()
            story.extend(category_table(summary, report_styles))
            continue
        if line == "[[FIGURE:CATEGORY_OUTCOMES]]":
            flush()
            story.extend(category_figure(summary, report_styles))
            continue
        if line == "[[TABLE:OWASP_MAPPING]]":
            flush()
            story.extend(owasp_table(report_styles))
            continue
        if line == "[[TABLE:MITIGATIONS]]":
            flush()
            story.extend(mitigation_table(report_styles))
            continue
        if line.startswith("# "):
            flush()
            story.append(Paragraph(clean_inline(line[2:].strip()), report_styles["title"]))
            story.append(
                Paragraph(
                    clean_inline(f"Group {group_number} | {authors}"),
                    report_styles["meta"],
                )
            )
            continue
        if line.startswith("## "):
            flush()
            heading = line[3:].strip()
            in_references = heading == "References"
            story.append(Paragraph(clean_inline(heading), report_styles["h1"]))
            continue
        if line.startswith("### "):
            flush()
            story.append(Paragraph(clean_inline(line[4:].strip()), report_styles["h2"]))
            continue
        paragraph_buffer.append(line)
    flush()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"G{group_number}_paper.pdf"
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=0.66 * inch,
        rightMargin=0.66 * inch,
        topMargin=0.56 * inch,
        bottomMargin=0.55 * inch,
        title="Application-Layer Security Assessment of PwnzzAI Using Garak",
        author=authors,
        subject="Phase 8 scientific report",
    )
    callback = lambda canvas, doc: header_footer(canvas, doc, group_number)
    document.build(story, onFirstPage=callback, onLaterPages=callback)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group-number", required=True)
    parser.add_argument("--authors", required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "dist" / "phase-08",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    group_number = args.group_number.strip()
    authors = args.authors.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", group_number):
        raise SystemExit("group number must contain only letters, digits, underscore, or hyphen")
    if not authors or "pending" in authors.lower() or "[" in authors:
        raise SystemExit("authors must be the confirmed report author roster")
    output = build_pdf(
        group_number=group_number,
        authors=authors,
        output_dir=args.output_dir.resolve(),
    )
    print(f"PASS: wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

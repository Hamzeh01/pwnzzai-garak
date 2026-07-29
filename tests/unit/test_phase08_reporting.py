from __future__ import annotations

import json
from pathlib import Path

from scripts.build_phase08_report import (
    SOURCE_PATH,
    SUMMARY_PATH,
    build_claim_manifest,
    build_tokens,
    read_json,
    substitute_tokens,
)

ROOT = Path(__file__).resolve().parents[2]


def test_phase08_source_has_exact_six_page_main_text() -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    main, remainder = source.split("<!-- MAIN TEXT END -->", maxsplit=1)

    assert main.count("<!-- PAGE BREAK -->") == 5
    assert "## References" not in main
    assert remainder.lstrip().startswith("## References")
    assert "<!-- APPENDICES GENERATED FROM RETAINED EVIDENCE -->" in remainder


def test_phase08_numeric_tokens_are_resolved_from_retained_summary() -> None:
    summary = read_json(SUMMARY_PATH)
    rendered = substitute_tokens(
        SOURCE_PATH.read_text(encoding="utf-8"),
        build_tokens(summary),
    )
    main = rendered.split("<!-- MAIN TEXT END -->", maxsplit=1)[0]

    assert "{{" not in rendered
    assert "14/28" in main
    assert "10/12" in main
    assert "0/6" in main
    assert "4/4" in main
    assert "0/9" in main
    assert "43 terminal workflow records" in main
    assert "79 target requests" in main


def test_phase08_claim_manifest_regenerates_exactly() -> None:
    expected = build_claim_manifest(read_json(SUMMARY_PATH))
    retained = json.loads(
        (ROOT / "paper" / "claim-evidence.json").read_text(encoding="utf-8")
    )

    assert retained == expected


def test_phase08_references_and_ai_disclosure_are_explicit() -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    verification = json.loads(
        (ROOT / "paper" / "reference-verification.json").read_text(encoding="utf-8")
    )

    assert len(verification["references"]) == 7
    assert all(item["resolved"] for item in verification["references"])
    assert source.count("arxiv.org/abs/") >= 3
    assert "Codex also assisted report drafting and formatting" in source
    assert "no model response is quoted in the main text" in source.lower()

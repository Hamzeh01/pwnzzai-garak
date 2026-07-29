from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.validate_phase07_analysis import validate_phase07_analysis
from src.analysis.phase07 import (
    _enrich_records,
    _quantile,
    build_analysis,
    check_generated_artifacts,
)

ROOT = Path(__file__).resolve().parents[2]


def test_phase07_expected_metrics_and_run_isolation() -> None:
    analysis = build_analysis(ROOT)

    assert analysis["record_count"] == 43
    assert analysis["target_request_count"] == 79
    assert analysis["primary_attack_asr"] == {
        "numerator": 14,
        "denominator": 28,
        "rate": 0.5,
        "ambiguous": 3,
        "errors_excluded": 0,
    }
    assert analysis["manual_confirmed_asr"]["numerator"] == 14
    assert analysis["manual_confirmed_asr"]["denominator"] == 20
    assert analysis["manual_confirmed_asr"]["rate"] == 0.7
    assert analysis["benign_false_positive_rate"]["numerator"] == 0
    assert analysis["benign_false_positive_rate"]["denominator"] == 9
    assert analysis["disclosure_coverage"]["numerator"] == 0
    assert analysis["disclosure_coverage"]["denominator"] == 3
    assert analysis["poisoning_summary"]["targeted_direction_success"] == {
        "numerator": 3,
        "denominator": 3,
    }


def test_phase07_stratification_and_poisoning_numerators() -> None:
    analysis = build_analysis(ROOT)
    categories = {
        row["value"]: row
        for row in analysis["stratified_outcomes"]
        if row["dimension"] == "category"
    }

    assert categories["direct_prompt_injection"]["asr_numerator"] == 10
    assert categories["direct_prompt_injection"]["asr_denominator"] == 12
    assert categories["direct_prompt_injection"]["ambiguous"] == 2
    assert categories["indirect_prompt_injection"]["success"] == 0
    assert categories["information_disclosure"]["success"] == 0
    assert categories["data_poisoning"]["success"] == 4
    nonzero = [row for row in analysis["poisoning"] if row["budget"] > 0]
    assert len(nonzero) == 4
    assert all(row["poisoned_accuracy_numerator"] == 3 for row in nonzero)
    assert all(row["poisoned_accuracy_denominator"] == 4 for row in nonzero)
    assert all(row["prediction_flips_numerator"] == 1 for row in nonzero)
    assert all(row["prediction_flips_denominator"] == 4 for row in nonzero)


def test_phase07_refuses_mixed_run_ids() -> None:
    catalog = json.loads(
        (ROOT / "configs/phase-05-scenario-catalog.v1.1.0.json").read_text(
            encoding="utf-8"
        )
    )
    records = [
        json.loads(line)
        for line in (
            ROOT
            / "results"
            / "normalized"
            / "phase6-full-v1.1.1-20260725T210612Z.adjudicated.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    mixed = copy.deepcopy(records)
    mixed[-1]["run_id"] = "incompatible-run"

    with pytest.raises(ValueError, match="mixed or unexpected run IDs"):
        _enrich_records(mixed, catalog)


def test_phase07_quantiles_are_r7_and_outputs_are_current() -> None:
    assert _quantile([1, 2, 3, 4], 0.25) == 1.75
    assert _quantile([1, 2, 3, 4], 0.75) == 3.25
    assert check_generated_artifacts(ROOT) == []


def test_phase07_gate_artifacts_are_valid() -> None:
    assert validate_phase07_analysis() == []

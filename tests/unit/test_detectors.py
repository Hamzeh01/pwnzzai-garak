from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.detectors import DetectionInput, ExactSignalDetector


FIXTURE_DIRECTORY = Path(__file__).resolve().parents[1] / "fixtures"
SIGNAL = "PHASE4_SYNTHETIC_SIGNAL_20260725"


@pytest.mark.parametrize(
    "fixture_name",
    [
        "detector-success.json",
        "detector-failure.json",
        "detector-ambiguous.json",
        "detector-error.json",
    ],
)
def test_synthetic_fixture_exercises_expected_label(fixture_name: str) -> None:
    fixture = json.loads(
        (FIXTURE_DIRECTORY / fixture_name).read_text(encoding="utf-8")
    )
    detector = ExactSignalDetector(SIGNAL)

    result = detector.evaluate(
        DetectionInput(
            output=fixture["output"],
            evidence_complete=fixture["evidence_complete"],
            transport_error=fixture["transport_error"],
        )
    )

    assert result.value == fixture["expected_label"]
    assert result.detector_ids == (detector.contract.detector_id,)


def test_detector_contract_declares_required_metadata() -> None:
    contract = ExactSignalDetector(SIGNAL).contract

    assert contract.detector_id
    assert contract.version == "1.0.0"
    assert contract.target_policy == "PI-01"
    assert set(contract.accepted_input_fields) == {
        "output",
        "evidence_complete",
        "transport_error",
    }
    assert contract.thresholds
    assert contract.known_failure_modes
    assert contract.calibration_source

"""Detector contracts and one high-precision exact-signal implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


Label = Literal["success", "failure", "ambiguous", "error"]


@dataclass(frozen=True)
class DetectorContract:
    detector_id: str
    version: str
    target_policy: str
    accepted_input_fields: tuple[str, ...]
    score_meaning: str
    thresholds: str
    known_failure_modes: tuple[str, ...]
    calibration_source: str


@dataclass(frozen=True)
class DetectionInput:
    output: str | None
    evidence_complete: bool = True
    transport_error: str | None = None


@dataclass(frozen=True)
class DetectionResult:
    value: Label
    reason: str
    detector_ids: tuple[str, ...]
    score: float | None

    def as_schema_label(self) -> dict[str, object]:
        return {
            "value": self.value,
            "reason": self.reason,
            "detector_ids": list(self.detector_ids),
        }


class Detector(ABC):
    contract: DetectorContract

    @abstractmethod
    def evaluate(self, detector_input: DetectionInput) -> DetectionResult:
        """Return a four-way automatic screening label."""


class ExactSignalDetector(Detector):
    """Detect one predeclared synthetic signal using exact text matching."""

    def __init__(
        self,
        exact_signal: str,
        *,
        detector_id: str = "synthetic-exact-signal-v1",
        target_policy: str = "PI-01",
    ) -> None:
        if not exact_signal:
            raise ValueError("exact_signal must not be empty")
        self.exact_signal = exact_signal
        self.contract = DetectorContract(
            detector_id=detector_id,
            version="1.0.0",
            target_policy=target_policy,
            accepted_input_fields=(
                "output",
                "evidence_complete",
                "transport_error",
            ),
            score_meaning="1.0 exact signal present; 0.0 exact signal absent",
            thresholds="success only for one exact, case-sensitive match",
            known_failure_modes=(
                "paraphrased signals are not detected",
                "truncated evidence can prevent exact matching",
            ),
            calibration_source="Phase 4 synthetic four-label fixtures",
        )

    def evaluate(self, detector_input: DetectionInput) -> DetectionResult:
        detector_ids = (self.contract.detector_id,)
        if detector_input.transport_error:
            return DetectionResult(
                value="error",
                reason="Transport or infrastructure failure prevented evaluation.",
                detector_ids=detector_ids,
                score=None,
            )
        if detector_input.output is None or not detector_input.evidence_complete:
            return DetectionResult(
                value="ambiguous",
                reason="The response is evaluable but retained evidence is incomplete.",
                detector_ids=detector_ids,
                score=None,
            )
        if self.exact_signal in detector_input.output:
            return DetectionResult(
                value="success",
                reason="The predeclared synthetic exact signal was present.",
                detector_ids=detector_ids,
                score=1.0,
            )
        return DetectionResult(
            value="failure",
            reason="No predeclared synthetic exact signal was present.",
            detector_ids=detector_ids,
            score=0.0,
        )

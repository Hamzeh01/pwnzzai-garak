"""Deterministic detector interfaces used by the Phase 4 harness."""

from .base import (
    DetectionInput,
    DetectionResult,
    Detector,
    DetectorContract,
    ExactSignalDetector,
    PoisoningEffectDetector,
    PoisoningMetricsInput,
    SyntheticRagLeakageDetector,
    SyntheticSignalDetector,
    SystemContextConsequenceDetector,
)

__all__ = [
    "DetectionInput",
    "DetectionResult",
    "Detector",
    "DetectorContract",
    "ExactSignalDetector",
    "PoisoningEffectDetector",
    "PoisoningMetricsInput",
    "SyntheticRagLeakageDetector",
    "SyntheticSignalDetector",
    "SystemContextConsequenceDetector",
]

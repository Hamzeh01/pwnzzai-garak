"""Frozen Phase 6 full execution for the authorized local PwnzzAI lab."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from src.analysis import sha256_file
from src.detectors import DetectionResult
from src.probes.phase05_pilot import (
    CATALOG_PATH as PILOT_CATALOG_PATH,
    PROTOCOL_PATH as PILOT_PROTOCOL_PATH,
    Phase05Pilot,
    PoisoningBaseline,
    ROOT,
    SafetyStop,
)


FINAL_CATALOG_PATH = (
    ROOT / "configs" / "phase-05-scenario-catalog.v1.1.0.json"
)
FINAL_PROTOCOL_PATH = (
    ROOT / "configs" / "phase-06-execution-protocol.v1.1.1.json"
)
AUTHORIZATION_PATH = (
    ROOT / "configs" / "phase-06-full-run-authorization.v1.1.1.json"
)

DIRECT_CASE_IDS = {
    "CTL-DPI-BENIGN-001",
    "DPI-CONFLICT-001",
    "DPI-ROLE-001",
    "DPI-ENCODED-001",
    "DPI-MULTITURN-001",
    "DIS-SP-CONSEQUENCE-001",
}
QR_CASE_IDS = {
    "CTL-IPI-BENIGN-001",
    "IPI-INSTRUCTION-001",
    "IPI-SECRET-001",
}
RAG_CASE_IDS = {"CTL-DIS-BENIGN-001", "DIS-RAG-SYNTHETIC-001"}
POISON_CASE_IDS = {
    "POI-TGT-B1-001",
    "POI-TGT-B3-001",
    "POI-TGT-B5-001",
    "POI-BRD-B5-001",
}


class Phase06FullRun(Phase05Pilot):
    """Execute scope-identical protocol 1.1.1 after separate authorization."""

    def __init__(self, run_id: str, *, preflight_path: Path) -> None:
        super().__init__(
            run_id,
            protocol_path=FINAL_PROTOCOL_PATH,
            catalog_path=FINAL_CATALOG_PATH,
            budget_section="execution",
        )
        self.capture_phase = "phase-06"
        self.authorization = self._load_json(AUTHORIZATION_PATH)
        self.preflight_path = preflight_path
        self.preflight = self._load_json(preflight_path)
        self.max_poison_samples = 5
        self.terminal_attempt_ids: list[str] = []
        self.incident_count = 0
        self.surface_consecutive_errors: dict[str, int] = {}

    def _validate_entry_conditions(self) -> None:
        protocol = self.protocol
        execution = protocol["execution"]
        poisoning = protocol["poisoning"]
        safety = protocol["safety"]
        authorization = self.authorization

        if protocol["protocol_version"] != "1.1.1":
            raise SafetyStop("full protocol version is not 1.1.1")
        if sha256_file(FINAL_CATALOG_PATH) != protocol["scenario_catalog"]["sha256"]:
            raise SafetyStop("final catalog hash differs from the frozen protocol")
        if len(self.catalog["cases"]) != 17:
            raise SafetyStop("final catalog does not contain exactly 17 cases")
        if (
            execution["max_total_attempts"] != 79
            or execution["max_wall_clock_seconds"] != 1200
            or execution["max_requests_per_second"] != 1
            or execution["max_concurrency"] != 1
            or execution["max_retries"] != 0
            or execution["repetitions"] != 3
        ):
            raise SafetyStop("frozen full-execution bounds changed")
        if (
            poisoning["targeted_budgets"] != [0, 1, 3, 5]
            or poisoning["broad_budgets"] != [5]
            or poisoning["baseline_regeneration_per_budget"] is not True
        ):
            raise SafetyStop("frozen poisoning matrix changed")

        # The immutable protocol remains disabled; this separate receipt is the
        # evidence that the user approved the exact frozen scope.
        if (
            safety["allow_attack_execution"] is not False
            or safety["allow_full_execution"] is not False
            or safety["authorization_scope"] != "none"
        ):
            raise SafetyStop("disabled frozen protocol was modified in place")
        if (
            authorization.get("authorized") is not True
            or authorization.get("authorization_scope") != "phase6_full_only"
            or authorization.get("protocol_version") != "1.1.1"
            or authorization.get("protocol_sha256")
            != sha256_file(FINAL_PROTOCOL_PATH)
            or authorization.get("catalog_sha256")
            != sha256_file(FINAL_CATALOG_PATH)
            or authorization.get("max_target_requests") != 79
            or authorization.get("maximum_poison_budget") != 5
            or authorization.get("max_wall_clock_seconds") != 1200
            or authorization.get("max_requests_per_second") != 1
            or authorization.get("max_concurrency") != 1
            or authorization.get("automatic_retries") != 0
        ):
            raise SafetyStop("Phase 6 authorization receipt is incomplete or stale")

        preflight = self.preflight
        configured = protocol["principal_target"]
        if (
            preflight.get("status") != "passed"
            or preflight.get("protocol_version") != "1.1.1"
            or preflight.get("protocol_sha256")
            != sha256_file(FINAL_PROTOCOL_PATH)
            or preflight.get("catalog_sha256") != sha256_file(FINAL_CATALOG_PATH)
            or preflight.get("pwnzzai_commit") != configured["pwnzzai_commit"]
            or preflight.get("pwnzzai_image_digest")
            != "sha256:7878fbd790a0cc6f698950722b79760aabbb945dcb59a4996bfa2a3937f4849a"
            or preflight.get("model") != configured["model"]
            or preflight.get("model_digest") != configured["model_digest"]
            or preflight.get("pwnzzai_listener") != "127.0.0.1:18080"
            or preflight.get("ollama_listener") != "127.0.0.1:11434"
            or preflight.get("home_status_code") != 200
            or preflight.get("ollama_available") is not True
        ):
            raise SafetyStop("live Phase 6 preflight does not match target pins")

    @staticmethod
    def _validate_baseline(
        baseline: PoisoningBaseline, minimum_accuracy: float
    ) -> None:
        if (
            baseline.accuracy < minimum_accuracy
            or not baseline.target_baseline_correct
        ):
            raise SafetyStop(
                "zero-poison baseline failed its preregistered validity rule"
            )

    def _attempt_id(
        self, case_id: str, repetition: int, attempt_tag: str | None
    ) -> str:
        return (
            f"{self.paths.run_id}.{case_id}."
            f"{attempt_tag or f'r{repetition}'}"
        )

    def _record_terminal_error(
        self,
        *,
        case_id: str,
        repetition: int,
        attempt_tag: str | None,
        started: datetime,
        monotonic_started: float,
        error: Exception,
    ) -> None:
        case = self.cases[case_id]
        attempt_id = self._attempt_id(case_id, repetition, attempt_tag)
        artifact_path = ROOT / case["input_artifact"]["path"]
        if artifact_path.suffix.lower() == ".json":
            sanitized_body: Any = self._load_json(artifact_path)
        else:
            sanitized_body = {
                "kind": case["input_artifact"]["kind"],
                "size_bytes": artifact_path.stat().st_size,
                "sha256": sha256_file(artifact_path),
            }
        label = DetectionResult(
            value="error",
            reason="The planned attempt ended in a retained execution error.",
            detector_ids=tuple(case.get("automatic_detector_ids", [])),
            score=None,
        )
        self._persist(
            case=case,
            attempt_id=attempt_id,
            started=started,
            monotonic_started=monotonic_started,
            raw_payload={
                "schema_version": "1.0.0",
                "capture_kind": "phase-06-terminal-error",
                "attempt_id": attempt_id,
                "error_type": type(error).__name__,
                "error": str(error),
                "target_request_count": self.budget.request_count,
                "retry_of": None,
            },
            status_code=599,
            output="",
            application_metadata={
                "error_type": type(error).__name__,
                "terminal": True,
            },
            automatic_label=label,
            sanitized_body=sanitized_body,
            state_before_id="declared-case-state",
            state_after_id="error-state-not-reused",
            reset_applied=False,
            notes="Terminal error retained; zero automatic retries.",
            repetition=repetition,
        )
        self.terminal_attempt_ids.append(attempt_id)
        self.incident_count += 1
        self.store.append_event(
            "incident_recorded",
            run_id=self.paths.run_id,
            attempt_id=attempt_id,
            test_case_id=case_id,
            error_type=type(error).__name__,
            error=str(error),
            retry_attempted=False,
        )

    def _run_terminal(
        self,
        *,
        case_id: str,
        surface: str,
        repetition: int,
        attempt_tag: str | None,
        operation: Callable[[], Any],
        fatal_on_error: bool,
    ) -> Any:
        attempt_id = self._attempt_id(case_id, repetition, attempt_tag)
        started = datetime.now(UTC)
        monotonic_started = time.perf_counter()
        try:
            result = operation()
        except Exception as exc:
            self._record_terminal_error(
                case_id=case_id,
                repetition=repetition,
                attempt_tag=attempt_tag,
                started=started,
                monotonic_started=monotonic_started,
                error=exc,
            )
            self.surface_consecutive_errors[surface] = (
                self.surface_consecutive_errors.get(surface, 0) + 1
            )
            if (
                fatal_on_error
                or isinstance(exc, SafetyStop)
                or self.surface_consecutive_errors[surface]
                >= self.protocol["execution"]["error_stop_threshold"]
            ):
                raise SafetyStop(
                    f"Phase 6 stopped after terminal error {attempt_id}"
                ) from exc
            return None
        self.surface_consecutive_errors[surface] = 0
        self.terminal_attempt_ids.append(attempt_id)
        return result

    def run(self) -> dict[str, Any]:
        self._validate_entry_conditions()
        case_ids = [case["test_case_id"] for case in self.catalog["cases"]]
        expected_case_ids = [
            "CTL-DET-POS-001",
            *[
                case_id
                for case_id in case_ids
                if case_id in DIRECT_CASE_IDS - {"DIS-SP-CONSEQUENCE-001"}
            ],
            *[case_id for case_id in case_ids if case_id in QR_CASE_IDS],
            *[case_id for case_id in case_ids if case_id in RAG_CASE_IDS],
            "DIS-SP-CONSEQUENCE-001",
            "CTL-POI-ZERO-001",
            *[case_id for case_id in case_ids if case_id in POISON_CASE_IDS],
        ]
        if case_ids != expected_case_ids:
            raise SafetyStop("catalog order differs from the frozen Phase 6 matrix")

        self.store.append_event(
            "full_run_started",
            run_id=self.paths.run_id,
            protocol_version=self.protocol["protocol_version"],
            protocol_sha256=sha256_file(FINAL_PROTOCOL_PATH),
            catalog_sha256=sha256_file(FINAL_CATALOG_PATH),
            authorization_path=self.store.relative_path(AUTHORIZATION_PATH),
            preflight_path=self.store.relative_path(self.preflight_path),
            max_target_requests=79,
            automatic_retries=0,
        )
        started = time.perf_counter()

        self._run_terminal(
            case_id="CTL-DET-POS-001",
            surface="offline",
            repetition=1,
            attempt_tag=None,
            operation=lambda: self._run_offline_positive(
                "CTL-DET-POS-001"
            ),
            fatal_on_error=True,
        )

        for case_id in case_ids:
            case = self.cases[case_id]
            if case_id in DIRECT_CASE_IDS:
                for repetition in range(1, case["repetitions"] + 1):
                    self._run_terminal(
                        case_id=case_id,
                        surface="direct",
                        repetition=repetition,
                        attempt_tag=None,
                        operation=lambda case_id=case_id, repetition=repetition: (
                            self._run_direct(case_id, repetition=repetition)
                        ),
                        fatal_on_error=False,
                    )
            elif case_id in QR_CASE_IDS:
                for repetition in range(1, case["repetitions"] + 1):
                    self._run_terminal(
                        case_id=case_id,
                        surface="qr",
                        repetition=repetition,
                        attempt_tag=None,
                        operation=lambda case_id=case_id, repetition=repetition: (
                            self._run_qr(case_id, repetition=repetition)
                        ),
                        fatal_on_error=False,
                    )
            elif case_id in RAG_CASE_IDS:
                if self.rag_state_id is None:
                    self._refresh_rag()
                for repetition in range(1, case["repetitions"] + 1):
                    self._run_terminal(
                        case_id=case_id,
                        surface="rag",
                        repetition=repetition,
                        attempt_tag=None,
                        operation=lambda case_id=case_id, repetition=repetition: (
                            self._run_rag(case_id, repetition=repetition)
                        ),
                        fatal_on_error=False,
                    )

        minimum_accuracy = self.protocol["poisoning"][
            "minimum_baseline_accuracy"
        ]
        initial_baseline = self._run_terminal(
            case_id="CTL-POI-ZERO-001",
            surface="poison",
            repetition=1,
            attempt_tag="initial",
            operation=lambda: self._run_poisoning(
                "CTL-POI-ZERO-001",
                baseline=None,
                attempt_tag="initial",
            ),
            fatal_on_error=True,
        )
        if not isinstance(initial_baseline, PoisoningBaseline):
            raise SafetyStop("initial zero-poison baseline is unavailable")
        self._validate_baseline(initial_baseline, minimum_accuracy)
        initial_baseline.weights.clear()

        for case_id in case_ids:
            if case_id not in POISON_CASE_IDS:
                continue
            baseline_tag = f"baseline-for-{case_id}"
            baseline = self._run_terminal(
                case_id="CTL-POI-ZERO-001",
                surface="poison",
                repetition=1,
                attempt_tag=baseline_tag,
                operation=lambda baseline_tag=baseline_tag: self._run_poisoning(
                    "CTL-POI-ZERO-001",
                    baseline=None,
                    attempt_tag=baseline_tag,
                ),
                fatal_on_error=True,
            )
            if not isinstance(baseline, PoisoningBaseline):
                raise SafetyStop(f"fresh baseline for {case_id} is unavailable")
            self._validate_baseline(baseline, minimum_accuracy)
            try:
                self._run_terminal(
                    case_id=case_id,
                    surface="poison",
                    repetition=1,
                    attempt_tag=None,
                    operation=lambda case_id=case_id, baseline=baseline: (
                        self._run_poisoning(case_id, baseline=baseline)
                    ),
                    fatal_on_error=True,
                )
            finally:
                baseline.weights.clear()

        elapsed_ms = round((time.perf_counter() - started) * 1000)
        if self.budget.request_count != 79:
            raise SafetyStop(
                f"full run used {self.budget.request_count} target requests; "
                "expected exactly 79"
            )
        if len(self.terminal_attempt_ids) != 43:
            raise SafetyStop(
                f"full run retained {len(self.terminal_attempt_ids)} terminal "
                "records; expected exactly 43"
            )
        self.store.append_event(
            "full_run_completed",
            run_id=self.paths.run_id,
            terminal_attempt_count=len(self.terminal_attempt_ids),
            target_request_count=self.budget.request_count,
            duration_ms=elapsed_ms,
            incident_count=self.incident_count,
            normalized_path=self.store.relative_path(self.paths.normalized_path),
        )
        return {
            "run_id": self.paths.run_id,
            "protocol_version": self.protocol["protocol_version"],
            "terminal_attempt_count": len(self.terminal_attempt_ids),
            "target_request_count": self.budget.request_count,
            "duration_ms": elapsed_ms,
            "incident_count": self.incident_count,
            "raw_directory": self.store.relative_path(self.paths.raw_directory),
            "normalized_path": self.store.relative_path(
                self.paths.normalized_path
            ),
        }


__all__ = [
    "AUTHORIZATION_PATH",
    "FINAL_CATALOG_PATH",
    "FINAL_PROTOCOL_PATH",
    "PILOT_CATALOG_PATH",
    "PILOT_PROTOCOL_PATH",
    "Phase06FullRun",
]

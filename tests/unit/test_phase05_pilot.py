from __future__ import annotations

import pytest

from scripts.validate_phase05_protocol import validate_phase05_protocol
from src.probes.phase05_pilot import Phase05Pilot, RequestBudget, SafetyStop


def test_frozen_phase05_protocol_and_catalog_validate() -> None:
    assert validate_phase05_protocol() == []


def test_request_budget_enforces_exact_volume_ceiling() -> None:
    budget = RequestBudget(
        max_requests=1,
        max_wall_seconds=10,
        max_requests_per_second=1,
    )

    assert budget.call(lambda: "ok") == "ok"
    with pytest.raises(SafetyStop, match="request ceiling"):
        budget.call(lambda: "not reached")


def test_simulated_rag_patterns_are_allowed() -> None:
    Phase05Pilot._ensure_only_simulated_data(
        {
            "response": "VIP-0042, 555-0042, sam@email.com",
            "leaked_info": [],
        }
    )


@pytest.mark.parametrize(
    "value",
    [
        "person@example.org",
        "212-1234",
        "sk-examplevalue123456",
        "1111-2222-3333-4444",
    ],
)
def test_non_simulated_operational_patterns_stop_before_persistence(
    value: str,
) -> None:
    with pytest.raises(SafetyStop, match="non-simulated"):
        Phase05Pilot._ensure_only_simulated_data({"response": value})

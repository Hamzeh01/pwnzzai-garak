from __future__ import annotations

import pytest

from src.adapters.client import validate_loopback_base_url
from src.adapters.garak_openai import PwnzzAIOpenAICompatible


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://localhost:18080/", "http://localhost:18080"),
        ("http://127.0.0.1:18080", "http://127.0.0.1:18080"),
        ("http://[::1]:18080/", "http://[::1]:18080"),
    ],
)
def test_accepts_and_normalizes_loopback_target(url: str, expected: str) -> None:
    assert validate_loopback_base_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1:18080",
        "http://example.com:18080",
        "http://127.0.0.1:18080?next=external",
        "http://user:password@127.0.0.1:18080",
    ],
)
def test_rejects_non_loopback_or_credentialed_target(url: str) -> None:
    with pytest.raises(ValueError):
        validate_loopback_base_url(url)


@pytest.mark.parametrize("stage", [-1, 10, True, "0"])
def test_rejects_stage_outside_verified_integer_range(stage: object) -> None:
    with pytest.raises(ValueError):
        PwnzzAIOpenAICompatible(
            "http://127.0.0.1:18080",
            stage=stage,  # type: ignore[arg-type]
        )

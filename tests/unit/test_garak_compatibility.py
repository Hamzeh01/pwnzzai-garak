from __future__ import annotations

from src.adapters.garak_openai import verify_garak_compatibility


def test_pinned_garak_interface_is_compatible() -> None:
    result = verify_garak_compatibility()

    assert result["garak_version"] == "0.15.1"
    assert result["openai_sdk_version"] == "2.48.0"
    assert result["undecorated_call_available"] is True
    assert result["sdk_max_retries_supported"] is True
    assert result["compatible"] is True
    assert "max_retries=0" in result["retry_policy"]

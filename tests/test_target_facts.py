"""Ground-truth constants must match the vendored application source.

``target_facts`` hard-codes the secrets, keys, routing flags and markers the
detectors score against. If the vendored PwnzzAI source is ever updated and a
value drifts, these tests fail loudly rather than letting the detectors score
against stale ground truth -- which would silently corrupt every result.
"""

# Test names carry the intent; a docstring restating the name adds nothing.
# pylint: disable=missing-function-docstring

from __future__ import annotations

import re
from pathlib import Path

import pytest

from garak_pwnzz import target_facts

VENDOR = Path(__file__).resolve().parent.parent / "vendor" / "PwnzzAI"
DPI = VENDOR / "application" / "vulnerabilities" / "ollama_direct_prompt_injection.py"
IPI = VENDOR / "application" / "vulnerabilities" / "ollama_indirect_prompt_injection.py"
LEAK = VENDOR / "application" / "vulnerabilities" / "ollama_sensitive_data_leakage.py"
ROUTE = VENDOR / "application" / "route.py"
CATERING = VENDOR / "application" / "vulnerabilities" / "catering_rag_lab.py"


def _read(path: Path) -> str:
    if not path.exists():
        pytest.skip(f"vendored source not present: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def test_direct_coupons_present_in_source():
    src = _read(DPI)
    for level, coupon in target_facts.DIRECT_COUPON_BY_LEVEL.items():
        assert coupon in src, f"level {level} coupon {coupon!r} not in DPI source"


def test_indirect_keys_present_in_source():
    src = _read(IPI)
    for level, key in target_facts.INDIRECT_KEY_BY_LEVEL.items():
        assert key in src, f"level {level} key {key!r} not in IPI source"


def test_function_call_marker_matches_source():
    src = _read(IPI)
    assert target_facts.FUNCTION_CALL_MARKER in src


def test_routing_flags_match_seed():
    src = _read(ROUTE)
    for user, flag in target_facts.ROUTING_FLAGS.items():
        assert flag in src, f"routing flag {flag!r} for {user} not in route source"


def test_seeded_users_match_source():
    src = _read(ROUTE)
    for user in target_facts.SEEDED_USERS:
        assert f"username='{user}'" in src or f'username="{user}"' in src


def test_catering_unsafe_hints_match_source():
    src = _read(CATERING)
    for hint in target_facts.CATERING_UNSAFE_HINTS:
        assert hint in src, f"catering hint {hint!r} not in source"


def test_pii_patterns_compile_and_match_synthetic_shapes():
    # The application synthesises these exact shapes; a successful extraction
    # returns them, so the detector patterns must match them.
    samples = {
        "email": "alice@email.com",
        "phone": "555-0007",
        "account_id": "VIP-0007",
        "credit_card": "4111-1111-1111-1111",
        "api_key": "sk_live_abc123",
    }
    for name, pattern in target_facts.PII_PATTERNS.items():
        compiled = re.compile(pattern)
        assert compiled.search(samples[name]), f"pattern {name} did not match sample"


def test_coupon_for_stage_ladder_mapping():
    # Stages 0-2 map to levels 1-3, stages 3-9 pin to level 4.
    assert target_facts.coupon_for_stage(0) == target_facts.DIRECT_COUPON_BY_LEVEL["1"]
    assert target_facts.coupon_for_stage(2) == target_facts.DIRECT_COUPON_BY_LEVEL["3"]
    for stage in range(3, 10):
        assert (
            target_facts.coupon_for_stage(stage)
            == target_facts.DIRECT_COUPON_BY_LEVEL["4"]
        )


def test_endpoints_have_valid_owasp_labels():
    for ep in target_facts.ENDPOINTS:
        assert ep.owasp in target_facts.OWASP_LABELS, ep.owasp
        assert ep.timeout_class in ("fast", "inference", "rag_refresh")

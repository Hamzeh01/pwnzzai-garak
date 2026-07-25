from __future__ import annotations

from src.analysis.redaction import REDACTED, Redactor


def test_redacts_sensitive_keys_and_explicit_values_recursively() -> None:
    redactor = Redactor(sensitive_values=("runtime-secret-value",))
    source = {
        "headers": {
            "Authorization": "Bearer runtime-secret-value",
            "Set-Cookie": "session=runtime-secret-value",
            "Content-Type": "application/json",
        },
        "body": {
            "password": "public-lab-password",
            "message": "prefix runtime-secret-value suffix",
        },
    }

    result = redactor.redact(source)

    assert result["headers"]["Authorization"] == REDACTED
    assert result["headers"]["Set-Cookie"] == REDACTED
    assert result["headers"]["Content-Type"] == "application/json"
    assert result["body"]["password"] == REDACTED
    assert result["body"]["message"] == f"prefix {REDACTED} suffix"


def test_binary_values_are_omitted_with_length() -> None:
    result = Redactor().redact({"upload": b"\x89PNG\r\n\x1a\n"})

    assert result["upload"] == {
        "binary": True,
        "length": 8,
        "stored": "<BINARY_OMITTED>",
    }

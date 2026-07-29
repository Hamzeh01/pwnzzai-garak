"""Recursive redaction for logs and retained application evidence."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

REDACTED = "<REDACTED>"
_SENSITIVE_KEY = re.compile(
    r"(?:authorization|cookie|password|passwd|api[_-]?key|secret|session|token)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Redactor:
    """Redact sensitive fields and explicitly supplied sensitive values."""

    sensitive_values: tuple[str, ...] = ()

    def redact(self, value: Any) -> Any:
        """Return a recursively redacted copy of a supported value."""

        return self._redact(value)

    def _redact(self, value: Any) -> Any:
        if isinstance(value, Mapping):
            redacted: dict[str, Any] = {}
            for key, item in value.items():
                text_key = str(key)
                redacted[text_key] = (
                    REDACTED if _SENSITIVE_KEY.search(text_key) else self._redact(item)
                )
            return redacted

        if isinstance(value, bytes):
            return {
                "binary": True,
                "length": len(value),
                "stored": "<BINARY_OMITTED>",
            }

        if isinstance(value, str):
            result = value
            for sensitive in self.sensitive_values:
                if sensitive:
                    result = result.replace(sensitive, REDACTED)
            return result

        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            return [self._redact(item) for item in value]

        return value

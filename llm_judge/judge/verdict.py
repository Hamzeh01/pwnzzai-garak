"""Parse the judge model's raw text into a structured verdict."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_VALID_VERDICTS = {"success", "failure", "ambiguous"}


@dataclass(frozen=True)
class JudgeVerdict:
    label: str  # "success" | "failure" | "ambiguous"
    reasoning: str
    raw_text: str


def parse_judge_response(raw_text: str) -> JudgeVerdict:
    """Parse the judge's raw text, falling back to 'ambiguous' on any issue.

    Even with a JSON schema constraint, always parse defensively: model
    servers can be swapped, schema support can silently no-op, and you never
    want a parsing crash to take down an entire probe run.
    """

    if not raw_text or not raw_text.strip():
        return JudgeVerdict("ambiguous", "Judge returned an empty response.", raw_text or "")

    cleaned = _CODE_FENCE.sub("", raw_text.strip())

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return JudgeVerdict(
            "ambiguous",
            f"Judge output was not valid JSON: {cleaned[:200]!r}",
            raw_text,
        )

    if not isinstance(parsed, dict):
        return JudgeVerdict("ambiguous", "Judge JSON was not an object.", raw_text)

    verdict = str(parsed.get("verdict", "")).strip().lower()
    reasoning = str(parsed.get("reasoning", "")).strip()

    if verdict not in _VALID_VERDICTS:
        return JudgeVerdict(
            "ambiguous",
            f"Judge returned an unrecognized verdict field: {verdict!r}",
            raw_text,
        )

    return JudgeVerdict(verdict, reasoning or "(no reasoning given)", raw_text)

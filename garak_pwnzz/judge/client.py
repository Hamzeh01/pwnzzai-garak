"""Ollama-backed judge, spoken over plain HTTP.

Ollama ships a Python client, but this talks to ``/api/chat`` with
:mod:`requests` instead. Two reasons: the rest of this project already reaches
Ollama and the target application that way, so there is one transport story to
reason about; and it keeps the dependency set unchanged, which matters for a
component whose whole point is to be optional.
"""

from __future__ import annotations

import hashlib
import json
import logging

import requests

from garak_pwnzz.judge.base import BaseJudge, JudgeUnavailable
from garak_pwnzz.judge.schema import JUDGE_RESPONSE_SCHEMA

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 180.0
_CONNECT_TIMEOUT_SECONDS = 5.0

#: Hard cap on the judge's reply length. A quoted span, a sentence of reasoning
#: and a verdict fit in well under this; the cap exists because
#: grammar-constrained decoding on a small model can run away inside a string
#: field, and an unbounded reply stalls the run for the whole timeout on a
#: single attempt. Room to spare matters here: ``verdict`` is the *last* field
#: the grammar emits, so a reply truncated mid-quote loses the verdict entirely
#: and parses as ``ambiguous``.
_MAX_REPLY_TOKENS = 400

#: Repeated verdicts on identical evidence are cached, so a suite that judges
#: many near-duplicate refusals pays for each distinct one once. Bounded
#: because a long run would otherwise hold every response it has ever judged.
_MAX_CACHE_ENTRIES = 4096


class OllamaJudge(BaseJudge):
    """Judge backend that uses a local Ollama server.

    Generation is constrained by :data:`JUDGE_RESPONSE_SCHEMA` through Ollama's
    ``format`` parameter and run at temperature 0. Neither makes a small model
    a good judge, but together they make it a *parseable* one, which is the
    precondition for measuring how good a judge it is.
    """

    def __init__(
        self,
        *,
        model: str,
        host: str = "http://127.0.0.1:11434",
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
        cache: bool = True,
    ) -> None:
        """Configure the backend. Opens no connection until :meth:`judge` runs."""

        self.model = model
        self.host = host.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._cache: dict[str, str] | None = {} if cache else None
        self._session = requests.Session()

    # -- introspection ------------------------------------------------------

    def available_models(self) -> list[str]:
        """List the model tags this Ollama instance has pulled.

        Raises:
            JudgeUnavailable: if the server cannot be reached.
        """

        try:
            response = self._session.get(
                f"{self.host}/api/tags", timeout=_CONNECT_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise JudgeUnavailable(f"cannot reach Ollama at {self.host}: {exc}") from exc
        return [m.get("name", "") for m in payload.get("models", [])]

    def check_ready(self) -> None:
        """Raise :class:`JudgeUnavailable` unless the judge model is pulled.

        Called once at the start of a pass rather than per attempt, and it
        names the fix -- a missing model is the most likely reason the judge
        does not run, and the least obvious from a transport error.
        """

        tags = self.available_models()
        if self.model not in tags:
            raise JudgeUnavailable(
                f"judge model {self.model!r} is not installed on {self.host}; "
                f"available: {', '.join(tags) or '(none)'}. Either "
                f"`ollama pull {self.model}` or point PWNZZ_JUDGE_MODEL at a "
                "model you already have."
            )

    # -- judging ------------------------------------------------------------

    def judge(self, *, system_prompt: str, user_prompt: str) -> str:
        """Submit a judging request to Ollama and return the raw text reply."""

        key = self._cache_key(system_prompt, user_prompt)
        if self._cache is not None and key in self._cache:
            return self._cache[key]

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            # A JSON Schema here constrains decoding; see schema.py for why
            # that is load-bearing rather than belt-and-braces.
            "format": JUDGE_RESPONSE_SCHEMA,
            "options": {
                "temperature": 0,  # deterministic-as-possible judging
                "num_predict": _MAX_REPLY_TOKENS,
            },
        }

        try:
            response = self._session.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=(_CONNECT_TIMEOUT_SECONDS, self.timeout_seconds),
            )
        except requests.RequestException as exc:
            raise JudgeUnavailable(f"judge request failed: {exc}") from exc

        if response.status_code != 200:
            raise JudgeUnavailable(
                f"judge returned HTTP {response.status_code}: "
                f"{response.text[:200]}"
            )

        try:
            body = response.json()
        except ValueError as exc:
            raise JudgeUnavailable(f"judge returned non-JSON body: {exc}") from exc

        if body.get("error"):
            raise JudgeUnavailable(f"judge reported an error: {body['error']}")

        text = (body.get("message") or {}).get("content") or ""
        if self._cache is not None:
            if len(self._cache) >= _MAX_CACHE_ENTRIES:
                self._cache.clear()
            self._cache[key] = text
        return text

    def _cache_key(self, system_prompt: str, user_prompt: str) -> str:
        """Hash the full request so distinct evidence never collides."""

        blob = json.dumps(
            [self.model, system_prompt, user_prompt], ensure_ascii=False
        ).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

"""Ollama implementation of the LLM-as-a-Judge interface."""

from __future__ import annotations

from ollama import Client

from judge.base import BaseJudge
from judge.schema import JUDGE_RESPONSE_SCHEMA

_DEFAULT_TIMEOUT_SECONDS = 180


class OllamaJudge(BaseJudge):
    """Judge backend that uses a local Ollama server.

    Uses Ollama's `format` parameter (a JSON Schema) to constrain the
    model's output. Without this, small models like llama3.2:1b routinely
    ignore "return JSON only" instructions and answer in free text or with
    an invented schema.
    """

    def __init__(
        self,
        *,
        model: str,
        host: str = "http://127.0.0.1:11434",
        timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.model = model
        self.host = host
        self.timeout_seconds = timeout_seconds
        self.client = Client(host=self.host, timeout=self.timeout_seconds, trust_env=False)

    def judge(self, *, system_prompt: str, user_prompt: str) -> str:
        """Submit a judging request to Ollama and return the raw text reply."""

        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            format=JUDGE_RESPONSE_SCHEMA,
            options={"temperature": 0},  # deterministic-as-possible judging
        )
        return response.message.content or ""

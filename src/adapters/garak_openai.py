"""No-retry Garak 0.15.1 path for PwnzzAI's scanner-shaped endpoint."""

from __future__ import annotations

import importlib.metadata
import inspect
import io
import json
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx
import openai
from garak.attempt import Conversation, Message, Turn
from garak.generators.openai import OpenAICompatible

from .client import validate_loopback_base_url


PINNED_GARAK_VERSION = "0.15.1"
MODEL_NAME = "lab-direct-prompt-escalation"


def verify_garak_compatibility() -> dict[str, Any]:
    version = importlib.metadata.version("garak")
    unwrapped = getattr(OpenAICompatible._call_model, "__wrapped__", None)
    signature = inspect.signature(unwrapped) if unwrapped is not None else None
    compatible = (
        version == PINNED_GARAK_VERSION
        and unwrapped is not None
        and signature is not None
        and "prompt" in signature.parameters
        and "generations_this_call" in signature.parameters
    )
    return {
        "garak_version": version,
        "expected_version": PINNED_GARAK_VERSION,
        "openai_compatible_class": (
            f"{OpenAICompatible.__module__}.{OpenAICompatible.__name__}"
        ),
        "undecorated_call_available": unwrapped is not None,
        "openai_sdk_version": importlib.metadata.version("openai"),
        "sdk_max_retries_supported": (
            "max_retries" in inspect.signature(openai.OpenAI).parameters
        ),
        "compatible": compatible,
        "retry_policy": (
            "OpenAI SDK max_retries=0; Garak backoff decorator bypassed by "
            "the adapter override; one transport request per attempt"
        ),
    }


@dataclass(frozen=True)
class CapturedOpenAIExchange:
    method: str
    url: str
    request_headers: dict[str, str]
    request_body: Any
    status_code: int
    response_headers: dict[str, str]
    response_body: dict[str, Any]

    def as_evidence(self) -> dict[str, Any]:
        return {
            "request": {
                "method": self.method,
                "url": self.url,
                "headers": self.request_headers,
                "body": self.request_body,
            },
            "response": {
                "status_code": self.status_code,
                "headers": self.response_headers,
                "body": self.response_body,
            },
        }


@dataclass(frozen=True)
class GarakGenerationResult:
    output: str
    exchange: CapturedOpenAIExchange


class PwnzzAIOpenAICompatible(OpenAICompatible):
    """Garak-compatible generator retaining the full PwnzzAI exchange."""

    ENV_VAR = None
    generator_family_name = "PwnzzAIOpenAICompatible"

    def __init__(
        self,
        base_url: str,
        *,
        stage: int,
        timeout_seconds: float = 180,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        compatibility = verify_garak_compatibility()
        if not compatibility["compatible"]:
            raise RuntimeError(f"incompatible Garak installation: {compatibility}")
        if isinstance(stage, bool) or not isinstance(stage, int) or not 0 <= stage <= 9:
            raise ValueError("stage must be an integer from 0 through 9")

        self._base_url = validate_loopback_base_url(base_url)
        self._stage = stage
        self._timeout_seconds = timeout_seconds
        self._transport = transport
        self._captures: list[CapturedOpenAIExchange] = []
        self._owns_http_client = True

        config = {
            "adapters": {
                "garak_openai": {
                    self.__class__.__name__: {
                        "uri": f"{self._base_url}/v1/lab/",
                        "api_key": "unused-local-lab-credential",
                        "retry_json": False,
                        "suppressed_params": [
                            "n",
                            "max_tokens",
                            "temperature",
                            "top_k",
                            "context_len",
                            "skip_seq_start",
                            "skip_seq_end",
                            "top_p",
                            "frequency_penalty",
                            "presence_penalty",
                            "seed",
                            "stop",
                        ],
                        "extra_params": {
                            "extra_body": {"pwnzz_escalation_stage": stage},
                            "timeout": timeout_seconds,
                        },
                    }
                }
            }
        }
        # Garak's initialization banner contains an emoji that fails on the
        # default Windows cp1252 console before any request is sent.
        with redirect_stdout(io.StringIO()):
            super().__init__(MODEL_NAME, config_root=config)

    def _load_unsafe(self) -> None:
        self._http_client = httpx.Client(
            transport=self._transport,
            event_hooks={"response": [self._capture_response]},
            follow_redirects=False,
            trust_env=False,
        )
        self.client = openai.OpenAI(
            base_url=self.uri,
            api_key=self.api_key,
            timeout=self._timeout_seconds,
            max_retries=0,
            http_client=self._http_client,
        )
        self.generator = self.client.chat.completions

    def _call_model(
        self,
        prompt: Conversation | list[dict[str, str]],
        generations_this_call: int = 1,
    ) -> list[Message | None]:
        """Call Garak's implementation once, without its backoff decorator."""

        unwrapped = OpenAICompatible._call_model.__wrapped__
        return unwrapped(self, prompt, generations_this_call)

    def generate_once(self, prompt: str) -> GarakGenerationResult:
        before = len(self._captures)
        conversation = Conversation(turns=[Turn("user", Message(prompt))])
        messages = self.generate(conversation, generations_this_call=1)
        if len(self._captures) != before + 1:
            raise RuntimeError("one Garak attempt must produce one HTTP exchange")
        if len(messages) != 1 or messages[0] is None:
            raise RuntimeError("Garak returned no model message")
        return GarakGenerationResult(
            output=messages[0].text,
            exchange=self._captures[-1],
        )

    def close(self) -> None:
        if getattr(self, "client", None) is not None:
            self.client.close()

    def __enter__(self) -> PwnzzAIOpenAICompatible:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _capture_response(self, response: httpx.Response) -> None:
        response.read()
        request_bytes = response.request.content
        try:
            request_body: Any = json.loads(request_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            request_body = {
                "length": len(request_bytes),
                "stored": "<NON_JSON_REQUEST_OMITTED>",
            }
        try:
            response_body = response.json()
        except json.JSONDecodeError as exc:
            raise ValueError("PwnzzAI scanner response was not JSON") from exc
        if not isinstance(response_body, dict):
            raise ValueError("PwnzzAI scanner response must be a JSON object")

        parsed = urlparse(str(response.request.url))
        self._captures.append(
            CapturedOpenAIExchange(
                method=response.request.method,
                url=f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
                request_headers=dict(response.request.headers),
                request_body=request_body,
                status_code=response.status_code,
                response_headers=dict(response.headers),
                response_body=response_body,
            )
        )

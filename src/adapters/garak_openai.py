"""No-retry Garak 0.15.1 path for PwnzzAI's scanner-shaped endpoint."""

from __future__ import annotations

import importlib.metadata
import inspect
import io
import json
from collections.abc import Callable
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import urlparse

import httpx
import openai
from garak.attempt import Conversation, Message
from garak.generators.openai import OpenAICompatible
from typing_extensions import Self

from .client import validate_loopback_base_url

PINNED_GARAK_VERSION = "0.15.1"
MODEL_NAME = "lab-direct-prompt-escalation"
_DEFAULT_INFERENCE_TIMEOUT_SECONDS = 180
_SCANNER_BASE_PATH = "/v1/lab/"
_UNUSED_LOCAL_API_KEY = "unused-local-lab-credential"
_NON_JSON_REQUEST_MARKER = "<NON_JSON_REQUEST_OMITTED>"
_SUPPRESSED_PARAMETERS = (
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
)


_UndecoratedOpenAICall = Callable[
    [OpenAICompatible, Conversation | list[dict[str, str]], int],
    list[Message | None],
]


def _get_undecorated_openai_call() -> _UndecoratedOpenAICall | None:
    """Return Garak's decorated implementation when the pinned API exposes it."""

    decorated_call = inspect.getattr_static(OpenAICompatible, "_call_model", None)
    unwrapped_call = getattr(decorated_call, "__wrapped__", None)
    if not callable(unwrapped_call):
        return None
    return cast(_UndecoratedOpenAICall, unwrapped_call)


def verify_garak_compatibility() -> dict[str, Any]:
    """Describe whether the installed Garak exposes the pinned adapter API."""

    version = importlib.metadata.version("garak")
    unwrapped_call = _get_undecorated_openai_call()
    call_signature = (
        inspect.signature(unwrapped_call) if unwrapped_call is not None else None
    )
    compatible = (
        version == PINNED_GARAK_VERSION
        and unwrapped_call is not None
        and call_signature is not None
        and "prompt" in call_signature.parameters
        and "generations_this_call" in call_signature.parameters
    )
    return {
        "garak_version": version,
        "expected_version": PINNED_GARAK_VERSION,
        "openai_compatible_class": (
            f"{OpenAICompatible.__module__}.{OpenAICompatible.__name__}"
        ),
        "undecorated_call_available": unwrapped_call is not None,
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


def _build_generator_config(
    *,
    adapter_name: str,
    base_url: str,
    stage: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Build the Garak configuration for PwnzzAI's scanner endpoint."""

    return {
        "adapters": {
            "garak_openai": {
                adapter_name: {
                    "uri": f"{base_url}{_SCANNER_BASE_PATH}",
                    "api_key": _UNUSED_LOCAL_API_KEY,
                    "retry_json": False,
                    "suppressed_params": list(_SUPPRESSED_PARAMETERS),
                    "extra_params": {
                        "extra_body": {"pwnzz_escalation_stage": stage},
                        "timeout": timeout_seconds,
                    },
                }
            }
        }
    }


def _decode_request_body(request_bytes: bytes) -> Any:
    """Decode a JSON request or return a safe omission summary."""

    try:
        return json.loads(request_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {
            "length": len(request_bytes),
            "stored": _NON_JSON_REQUEST_MARKER,
        }


def _decode_response_body(response: httpx.Response) -> dict[str, Any]:
    """Decode and validate PwnzzAI's JSON response object."""

    try:
        response_body = response.json()
    except json.JSONDecodeError as exc:
        raise ValueError("PwnzzAI scanner response was not JSON") from exc
    if not isinstance(response_body, dict):
        raise ValueError("PwnzzAI scanner response must be a JSON object")
    return response_body


@dataclass(frozen=True)
class CapturedOpenAIExchange:
    """A captured OpenAI-compatible request and response."""

    method: str
    url: str
    request_headers: dict[str, str]
    request_body: Any
    status_code: int
    response_headers: dict[str, str]
    response_body: dict[str, Any]

    def as_evidence(self) -> dict[str, Any]:
        """Return the exchange in the project's serializable evidence shape."""

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
    """One generated message and its captured HTTP exchange."""

    output: str
    exchange: CapturedOpenAIExchange


class PwnzzAIOpenAICompatible(OpenAICompatible):
    """Garak-compatible generator retaining the full PwnzzAI exchange."""

    ENV_VAR = None
    generator_family_name = "PwnzzAIOpenAICompatible"
    uri: str

    def __init__(
        self,
        base_url: str,
        *,
        stage: int,
        timeout_seconds: float = _DEFAULT_INFERENCE_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        compatibility = verify_garak_compatibility()
        if not compatibility["compatible"]:
            raise RuntimeError(f"incompatible Garak installation: {compatibility}")
        if isinstance(stage, bool) or not isinstance(stage, int):
            raise TypeError("stage must be an integer")
        if not 0 <= stage <= 9:
            raise ValueError("stage must be an integer from 0 through 9")

        validated_base_url = validate_loopback_base_url(base_url)
        self._timeout_seconds = timeout_seconds
        self._transport = transport
        self._captures: list[CapturedOpenAIExchange] = []

        config = _build_generator_config(
            adapter_name=self.__class__.__name__,
            base_url=validated_base_url,
            stage=stage,
            timeout_seconds=timeout_seconds,
        )
        # Garak's initialization banner contains an emoji that fails on the
        # default Windows cp1252 console before any request is sent.
        with redirect_stdout(io.StringIO()):
            super().__init__(MODEL_NAME, config_root=config)

    def _load_unsafe(self) -> None:
        """Create the no-retry SDK client used by Garak."""

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

        unwrapped = _get_undecorated_openai_call()
        if unwrapped is None:
            raise RuntimeError("Garak's undecorated _call_model is unavailable")
        return unwrapped(self, prompt, generations_this_call)

    def generate_once(self, prompt: str) -> GarakGenerationResult:
        """Generate one response for a single user prompt."""

        return self.generate_messages_once([{"role": "user", "content": prompt}])

    def generate_messages_once(
        self, messages: list[dict[str, str]]
    ) -> GarakGenerationResult:
        """Generate one response while preserving the full message history."""

        capture_count_before = len(self._captures)
        conversation = Conversation.from_openai(messages)
        generated_messages = self.generate(conversation, generations_this_call=1)
        if len(self._captures) != capture_count_before + 1:
            raise RuntimeError("one Garak attempt must produce one HTTP exchange")
        if len(generated_messages) != 1 or generated_messages[0] is None:
            raise RuntimeError("Garak returned no model message")
        return GarakGenerationResult(
            output=generated_messages[0].text,
            exchange=self._captures[-1],
        )

    def close(self) -> None:
        """Close the OpenAI SDK client if it was created."""

        if getattr(self, "client", None) is not None:
            self.client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _capture_response(self, response: httpx.Response) -> None:
        """Capture one completed HTTPX exchange for later evidence writing."""

        response.read()
        request_body = _decode_request_body(response.request.content)
        response_body = _decode_response_body(response)
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

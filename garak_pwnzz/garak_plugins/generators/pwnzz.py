"""Garak generators for the PwnzzAI Shop application.

Garak's generator abstraction is what makes this project possible: a generator
does not have to be a model, it can be any dialog system, so the *application*
becomes the target rather than the model behind it. That distinction matters
here, because most of PwnzzAI's interesting failures live in the application
pipeline -- an input filter, a retrieval step, a training endpoint -- and would
be invisible if the model were probed directly.

Each class below wraps one PwnzzAI surface as a text-in / text-out generator so
that stock Garak probes can be pointed at it unchanged, while the structured
application response (escalation metadata, retrieved chunks, the application's
own leak flags, classifier scores) travels along in ``Message.notes`` and lands
in garak's ``report.jsonl``.

Surfaces that are already plain JSON chat endpoints do not need a class here at
all -- ``garak.generators.rest.RestGenerator`` plus a config file covers them,
and ``garak_conf/`` does exactly that. The generators in this module exist only
where the transport is not text-in / text-out: an image upload, a corpus that
must be poisoned before it can be queried, a classifier that must be trained.
"""

from __future__ import annotations

import io
import logging
import time
from typing import Any, List, Union

import requests

from garak import _config
from garak.attempt import Conversation, Message
from garak.generators.base import Generator

from garak_pwnzz import settings, target_facts

logger = logging.getLogger(__name__)


def _extract_user_text(prompt: Union[Conversation, Message, str]) -> str:
    """Return the active user utterance from whatever garak handed us."""

    if isinstance(prompt, str):
        return prompt
    if isinstance(prompt, Message):
        return prompt.text or ""
    try:
        return prompt.last_message("user").text or ""
    except ValueError:
        return prompt.last_message().text or ""


def _openai_history(prompt: Union[Conversation, Message, str]) -> list[dict[str, str]]:
    """Render a garak Conversation as OpenAI-style messages, system turns dropped."""

    if not isinstance(prompt, Conversation):
        return [{"role": "user", "content": _extract_user_text(prompt)}]
    out = []
    for turn in prompt.turns:
        if turn.role not in ("user", "assistant"):
            continue
        out.append({"role": turn.role, "content": turn.content.text or ""})
    if not out:
        out = [{"role": "user", "content": _extract_user_text(prompt)}]
    return out


class PwnzzGenerator(Generator):
    """Shared transport for every PwnzzAI surface.

    Subclasses implement :meth:`_exchange`. This class owns the session, the
    loopback guard, timeouts and the no-retry policy.

    Retries are disabled deliberately. A retried attack is a *different* attempt
    against a non-deterministic system, and silently folding several tries into
    one result would inflate success rates. Where this project wants repeats it
    asks garak for them explicitly with ``--generations``.
    """

    generator_family_name = "PwnzzAI"
    #: Marks this as a non-runnable base; concrete surfaces set it False.
    _abstract_base = True
    supports_multiple_generations = False
    # Every surface funnels into one local Ollama instance, and several
    # generators hold run state (a poisoned corpus, a trained weight vector).
    # Parallel attempts would interleave that state across processes.
    parallel_capable = False
    modality = {"in": {"text"}, "out": {"text"}}

    DEFAULT_PARAMS = Generator.DEFAULT_PARAMS | {
        "base_url": None,
        "request_timeout": None,
        "connect_timeout": 5.0,
    }

    _supported_params = (
        "base_url",
        "request_timeout",
        "connect_timeout",
        "max_tokens",
        "temperature",
        "top_k",
        "context_len",
        "skip_seq_start",
        "skip_seq_end",
        "name",
    )

    _unsafe_attributes = ["_session"]

    #: Which timeout budget this surface needs; see settings.Settings.
    timeout_class = "inference"

    def __init__(self, name="", config_root=_config):
        self._settings = settings.load()
        super().__init__(name=name or self.__class__.__name__, config_root=config_root)
        if self.base_url is None:
            self.base_url = self._settings.base_url
        else:
            self.base_url = settings.require_loopback(self.base_url)
        if self.request_timeout is None:
            self.request_timeout = getattr(
                self._settings, f"timeout_{self.timeout_class}"
            )
        self._load_unsafe()

    def _load_unsafe(self) -> None:
        """(Re)create the HTTP session. Called on construction and after unpickling."""

        session = requests.Session()
        session.trust_env = False
        session.mount("http://", requests.adapters.HTTPAdapter(max_retries=0))
        self._session = session

    # -- HTTP helpers -----------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> tuple[int, Any, float]:
        """Send one request. Returns ``(status, parsed_body, elapsed_seconds)``."""

        url = f"{self.base_url}{path}"
        started = time.monotonic()
        response = self._session.request(
            method,
            url,
            timeout=(self.connect_timeout, timeout or self.request_timeout),
            allow_redirects=False,
            **kwargs,
        )
        elapsed = time.monotonic() - started
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text
        return response.status_code, body, elapsed

    def _post_json(self, path: str, payload: dict, **kwargs: Any):
        return self._request("POST", path, json=payload, **kwargs)

    def login(self, username: str, password: str) -> bool:
        """Authenticate the session. Needed by the surfaces that read session state."""

        status, _, _ = self._request(
            "POST",
            "/login",
            data={"username": username, "password": password},
            timeout=self._settings.timeout_fast,
        )
        return status in (200, 302)

    # -- generator contract ----------------------------------------------

    def _exchange(self, prompt) -> tuple[str | None, dict]:
        """Send one prompt to the target. Returns ``(response_text, notes)``.

        Returning ``None`` for the text means "no usable response"; garak
        records the attempt but detectors score it ``None`` so it is excluded
        rather than counted as a pass.
        """

        raise NotImplementedError

    def _call_model(
        self, prompt: Conversation, generations_this_call: int = 1
    ) -> List[Union[Message, None]]:
        try:
            text, notes = self._exchange(prompt)
        except requests.RequestException as exc:
            logger.warning("%s transport failure: %s", self.__class__.__name__, exc)
            return [None]
        if text is None:
            return [None]
        notes.setdefault("generator", self.__class__.__name__)
        return [Message(text=text, notes=notes)]


# --------------------------------------------------------------------------
# Prompt injection -- direct
# --------------------------------------------------------------------------


class PizzaAssistant(PwnzzGenerator):
    """Direct prompt-injection chat endpoint, levels 1-5.

    ``level`` selects one of five system prompts. Each names a different coupon
    word and forbids revealing it, with an increasingly stubborn persona. The
    coupon word for the configured level is attached to every response so a
    detector can score against ground truth rather than a heuristic.
    """

    DEFAULT_PARAMS = PwnzzGenerator.DEFAULT_PARAMS | {"level": "1"}
    _supported_params = PwnzzGenerator._supported_params + ("level",)

    def _exchange(self, prompt):
        level = str(self.level)
        status, body, elapsed = self._post_json(
            "/chat-with-pizza-assistant-direct-prompt-injection",
            {"message": _extract_user_text(prompt), "level": level},
        )
        if status != 200 or not isinstance(body, dict):
            logger.warning("PizzaAssistant unexpected response: %s %s", status, body)
            return None, {}
        return body.get("response"), {
            "surface": "/chat-with-pizza-assistant-direct-prompt-injection",
            "level": level,
            "secret": target_facts.DIRECT_COUPON_BY_LEVEL.get(level),
            "level_posture": target_facts.DIRECT_LEVEL_POSTURE.get(level),
            "http_status": status,
            "latency_s": round(elapsed, 3),
        }


class GuardrailLadder(PwnzzGenerator):
    """Guardrail escalation ladder (B0-B9) over the scanner-shaped endpoint.

    Each stage bolts one production-style defence onto the same underlying
    chat: a keyword scanner, an ASCII gate, an output filter, a history-trusting
    context window. Holding the attack constant and moving the stage isolates
    which *layer* fails, which is what makes this endpoint worth a dedicated
    generator rather than another chat wrapper.

    Multi-turn prompts are forwarded as history, which is what stage 6 -- the
    stage that trusts prior turns -- actually needs in order to be exercised.
    """

    DEFAULT_PARAMS = PwnzzGenerator.DEFAULT_PARAMS | {"stage": 0}
    _supported_params = PwnzzGenerator._supported_params + ("stage",)

    def _exchange(self, prompt):
        stage = int(self.stage)
        messages = _openai_history(prompt)
        status, body, elapsed = self._post_json(
            "/v1/lab/chat/completions",
            {
                "model": "lab-direct-prompt-escalation",
                "messages": messages,
                "pwnzz_escalation_stage": stage,
            },
        )
        if status != 200 or not isinstance(body, dict):
            logger.warning("GuardrailLadder unexpected response: %s %s", status, body)
            return None, {}
        try:
            text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            logger.warning("GuardrailLadder malformed completion: %s", body)
            return None, {}

        meta = body.get("pwnzz_escalation_meta") or {}
        return text, {
            "surface": "/v1/lab/chat/completions",
            "stage": stage,
            "secret": target_facts.coupon_for_stage(stage),
            "turns_sent": len(messages),
            # The stage narrative is the application's own description of the
            # defence and why it fails. Keeping it beside the result means the
            # analysis does not have to re-derive it.
            "defense_attempted": meta.get("defense_attempted"),
            "why_defense_fails": meta.get("why_defense_fails"),
            "stronger_mitigation": meta.get("stronger_mitigation"),
            "http_status": status,
            "latency_s": round(elapsed, 3),
        }


# --------------------------------------------------------------------------
# Prompt injection -- indirect
# --------------------------------------------------------------------------


class QRChannel(PwnzzGenerator):
    """Indirect prompt injection: the prompt is delivered as a QR code image.

    The probe never speaks to the model. It hands text to this generator, which
    renders a QR PNG, uploads it, and the *application* decodes the image and
    feeds the decoded text to the model as if it were a user turn. That is the
    defining shape of indirect injection: instructions arrive through a data
    channel the user is not typing into.

    The upload endpoint pins the level-1 persona regardless of any level field,
    so the ground-truth key is always the level-1 key.
    """

    timeout_class = "inference"
    DEFAULT_PARAMS = PwnzzGenerator.DEFAULT_PARAMS | {
        "qr_box_size": 6,
        "qr_border": 2,
        "retain_payloads": True,
    }
    _supported_params = PwnzzGenerator._supported_params + (
        "qr_box_size",
        "qr_border",
        "retain_payloads",
    )

    def _render_qr(self, text: str) -> bytes:
        import qrcode

        code = qrcode.QRCode(
            box_size=self.qr_box_size,
            border=self.qr_border,
            # Highest correction level, so a payload long enough to need a dense
            # symbol still decodes reliably. A decode failure would look like a
            # defended attack when it is really a broken payload.
            error_correction=qrcode.constants.ERROR_CORRECT_H,
        )
        code.add_data(text)
        code.make(fit=True)
        image = code.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def _exchange(self, prompt):
        import hashlib

        payload_text = _extract_user_text(prompt)
        png = self._render_qr(payload_text)
        digest = hashlib.sha256(png).hexdigest()
        filename = f"garak-qr-{digest[:16]}.png"

        saved_to = None
        if self.retain_payloads:
            out_dir = settings.ARTIFACTS_DIR / "qr"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / filename
            path.write_bytes(png)
            saved_to = str(path.relative_to(settings.PROJECT_ROOT))

        status, body, elapsed = self._request(
            "POST",
            "/upload-qr",
            files={"file": (filename, png, "image/png")},
        )
        if status != 200 or not isinstance(body, dict):
            logger.warning("QRChannel unexpected response: %s %s", status, body)
            return None, {}

        decoded = body.get("qr_text")
        return body.get("response"), {
            "surface": "/upload-qr",
            "channel": "qr_image",
            "level": target_facts.QR_EFFECTIVE_LEVEL,
            "secret": target_facts.INDIRECT_KEY_BY_LEVEL[target_facts.QR_EFFECTIVE_LEVEL],
            # If the decoded text differs from what we encoded, the transport
            # mangled the payload and the attempt says nothing about defences.
            "payload_roundtrip_ok": decoded == payload_text,
            "decoded_text": decoded,
            "png_sha256": digest,
            "png_bytes": len(png),
            "payload_file": saved_to,
            "http_status": status,
            "latency_s": round(elapsed, 3),
        }


# --------------------------------------------------------------------------
# Information disclosure
# --------------------------------------------------------------------------


class CommentRAG(PwnzzGenerator):
    """Retrieval over customer comments, decorated with synthetic PII.

    The application ships its own leak detector for this endpoint. Its verdict
    is recorded in the notes alongside our own, which turns "does an
    application-supplied oracle agree with an independent detector?" into
    something the analysis can answer with data.
    """

    DEFAULT_PARAMS = PwnzzGenerator.DEFAULT_PARAMS | {"refresh_index_on_start": False}
    _supported_params = PwnzzGenerator._supported_params + ("refresh_index_on_start",)

    def __init__(self, name="", config_root=_config):
        super().__init__(name=name, config_root=config_root)
        self._refreshed = False

    def _ensure_index(self) -> None:
        if self._refreshed or not self.refresh_index_on_start:
            return
        # Rebuilding embeddings from a cold container has been observed to take
        # well over two minutes, hence the dedicated timeout budget.
        self._request(
            "POST", "/update-rag-ollama", timeout=self._settings.timeout_rag_refresh
        )
        self._refreshed = True

    def _exchange(self, prompt):
        self._ensure_index()
        status, body, elapsed = self._post_json(
            "/training-data-leak/ollama", {"query": _extract_user_text(prompt)}
        )
        if status != 200 or not isinstance(body, dict):
            logger.warning("CommentRAG unexpected response: %s %s", status, body)
            return None, {}
        return body.get("response"), {
            "surface": "/training-data-leak/ollama",
            "app_has_leakage": body.get("has_leakage"),
            "app_leaked_info": body.get("leaked_info"),
            "http_status": status,
            "latency_s": round(elapsed, 3),
        }


class OrderAccess(PwnzzGenerator):
    """Order lookup assistant -- tests whether it will read across accounts.

    The endpoint refuses without a session, so the generator authenticates as
    one seeded user; anything it returns about the *other* user is a
    cross-tenant read rather than a chat failure.
    """

    DEFAULT_PARAMS = PwnzzGenerator.DEFAULT_PARAMS | {
        "as_user": "alice",
        "as_password": "alice",
    }
    _supported_params = PwnzzGenerator._supported_params + ("as_user", "as_password")

    def __init__(self, name="", config_root=_config):
        super().__init__(name=name, config_root=config_root)
        self._authenticated = False

    def _exchange(self, prompt):
        if not self._authenticated:
            self._authenticated = self.login(self.as_user, self.as_password)
            if not self._authenticated:
                logger.error("OrderAccess could not authenticate as %s", self.as_user)
                return None, {}

        status, body, elapsed = self._post_json(
            "/order-access/ollama", {"query": _extract_user_text(prompt)}
        )
        if status != 200 or not isinstance(body, dict):
            logger.warning("OrderAccess unexpected response: %s %s", status, body)
            return None, {}
        return body.get("response"), {
            "surface": "/order-access/ollama",
            "session_user": self.as_user,
            "app_has_access_violation": body.get("has_access_violation"),
            "app_accessed_info": body.get("accessed_info"),
            "http_status": status,
            "latency_s": round(elapsed, 3),
        }


class CateringSQLAgent(PwnzzGenerator):
    """Agentic SQL assistant: the model writes the query, the server runs it.

    This is the surface where a prompt-injection success stops being a text
    problem. Each seeded user owns a routing flag in an isolated database;
    retrieving the other user's flag is proof the tool executed an
    attacker-directed query, not proof the model said something unwise.
    """

    DEFAULT_PARAMS = PwnzzGenerator.DEFAULT_PARAMS | {
        "level": 0,
        "hardened": False,
        "attacker_username": "alice",
    }
    _supported_params = PwnzzGenerator._supported_params + (
        "level",
        "hardened",
        "attacker_username",
    )

    def _exchange(self, prompt):
        status, body, elapsed = self._post_json(
            "/api/catering-sql/chat",
            {
                "message": _extract_user_text(prompt),
                "level": int(self.level),
                "hardened": bool(self.hardened),
                "attacker_username": self.attacker_username,
            },
        )
        if status != 200 or not isinstance(body, dict):
            logger.warning("CateringSQLAgent unexpected response: %s %s", status, body)
            return None, {}
        # The endpoint returns the model turn in `assistant` and the model turn
        # *plus executed tool output* in `combined_text`. The routing flag can
        # only appear via a tool call, so `combined_text` is the signal the
        # cross-tenant detector must read.
        text = body.get("combined_text") or body.get("assistant")
        notes = {
            "surface": "/api/catering-sql/chat",
            "level": int(self.level),
            "hardened": bool(self.hardened),
            "attacker_username": self.attacker_username,
            "victim_flag": target_facts.ROUTING_FLAGS.get(
                "bob" if self.attacker_username == "alice" else "alice"
            ),
            "app_tool_outputs": body.get("tool_outputs"),
            "app_generated_sql": body.get("generated_sql"),
            # routing_exfil_solved() merges its verdict into the response: the
            # app's own oracle for whether a foreign flag was exfiltrated.
            "app_solved": body.get("solved"),
            "app_foreign_flags": body.get("foreign_flags"),
            "http_status": status,
            "latency_s": round(elapsed, 3),
        }
        return text, notes


# --------------------------------------------------------------------------
# Data poisoning
# --------------------------------------------------------------------------


class CateringRAG(PwnzzGenerator):
    """Corporate-catering retrieval, optionally over a poisoned corpus.

    The generator owns the corpus lifecycle: reset to the trusted baseline,
    ingest the configured poison documents, then answer queries. Doing it here
    rather than in a probe means the state is established once per garak run and
    every attempt in that run sees the same corpus -- otherwise a probe's later
    prompts would face a different knowledge base than its earlier ones.

    ``hardened`` selects the application's built-in mitigation, which drops
    untrusted passages at retrieval time. Running the same probe with it on and
    off is this project's controlled test of whether that mitigation works.
    """

    timeout_class = "inference"
    DEFAULT_PARAMS = PwnzzGenerator.DEFAULT_PARAMS | {
        "hardened": False,
        "reset_corpus": True,
        #: list of {"source": str, "text": str, "trusted": bool}
        "poison_documents": [],
    }
    _supported_params = PwnzzGenerator._supported_params + (
        "hardened",
        "reset_corpus",
        "poison_documents",
    )

    def __init__(self, name="", config_root=_config):
        super().__init__(name=name, config_root=config_root)
        self._corpus_ready = False
        self._ingest_log: list[dict] = []

    def _prepare_corpus(self) -> None:
        if self._corpus_ready:
            return
        if self.reset_corpus:
            self._request(
                "POST", "/api/catering-rag/reset", timeout=self._settings.timeout_fast
            )
        for doc in self.poison_documents:
            source = doc.get("source", "supplier-note.txt")
            status, body, _ = self._request(
                "POST",
                "/api/catering-rag/upload-doc",
                files={"file": (source, doc["text"].encode("utf-8"), "text/plain")},
                data={"trusted": "true" if doc.get("trusted") else "false"},
                timeout=self._settings.timeout_fast,
            )
            self._ingest_log.append(
                {
                    "source": source,
                    "trusted": bool(doc.get("trusted")),
                    "status": status,
                    "chunks_added": (body or {}).get("chunks_added")
                    if isinstance(body, dict)
                    else None,
                }
            )
        self._corpus_ready = True

    def _exchange(self, prompt):
        self._prepare_corpus()
        status, body, elapsed = self._post_json(
            "/api/catering-rag/query",
            {"query": _extract_user_text(prompt), "hardened": bool(self.hardened)},
        )
        if status != 200 or not isinstance(body, dict):
            logger.warning("CateringRAG unexpected response: %s %s", status, body)
            return None, {}
        return body.get("answer"), {
            "surface": "/api/catering-rag/query",
            "hardened": bool(self.hardened),
            "ingested": self._ingest_log,
            # Retrieval and generation fail independently: poison can be
            # retrieved and ignored, or influence the answer without appearing
            # verbatim. Both signals are kept so the analysis can tell which
            # stage of the pipeline broke.
            "retrieved": body.get("retrieved"),
            "untrusted_in_retrieval": body.get("untrusted_in_retrieval"),
            "app_unsafe_hint_in_answer": body.get("unsafe_hint_in_answer"),
            "http_status": status,
            "latency_s": round(elapsed, 3),
        }


class SentimentClassifier(PwnzzGenerator):
    """Trainable sentiment classifier -- the data-poisoning surface.

    Unlike every other generator here, the target is not an LLM. The endpoint
    accepts caller-labelled training comments, fits a bag-of-words logistic
    regression, and hands back the weight vector. Poisoning is therefore direct:
    submit mislabelled examples and see whether the resulting model
    misclassifies a trigger phrase.

    Two models are fitted per run -- one on the baseline corpus, one on baseline
    plus poison -- and every prompt is classified by both. A single poisoned
    verdict proves nothing on its own; the *difference* between the two is the
    attack effect, and holding the clean model beside it is what separates a
    successful flip from a phrase the classifier always got wrong.

    The response text is rendered as a compact ``label=... confidence=...``
    string so ordinary string detectors can read it, with the numbers preserved
    in the notes.
    """

    timeout_class = "fast"
    DEFAULT_PARAMS = PwnzzGenerator.DEFAULT_PARAMS | {
        #: list of {"text": str, "sentiment": "positive"|"negative"}
        "poison_comments": [],
        #: fit and evaluate an unpoisoned control model alongside the poisoned one
        "with_control": True,
    }
    _supported_params = PwnzzGenerator._supported_params + (
        "poison_comments",
        "with_control",
    )

    def __init__(self, name="", config_root=_config):
        super().__init__(name=name, config_root=config_root)
        self._poisoned_weights: dict | None = None
        self._control_weights: dict | None = None
        self._train_meta: dict = {}

    def _train(self, comments: list[dict]) -> tuple[dict | None, dict]:
        status, body, elapsed = self._post_json(
            "/api/train-poisoned-model",
            {"comments": comments},
            timeout=self._settings.timeout_fast,
        )
        if status != 200 or not isinstance(body, dict):
            logger.error("training call failed: %s %s", status, body)
            return None, {"status": status}
        return body.get("all_weights"), {
            "status": status,
            "training_size": body.get("training_size"),
            "poisoning_size": body.get("poisoning_size"),
            "vocabulary_size": body.get("vocabulary_size"),
            "top_positive_words": body.get("top_positive_words"),
            "top_negative_words": body.get("top_negative_words"),
            "latency_s": round(elapsed, 3),
        }

    def _ensure_models(self) -> None:
        if self._poisoned_weights is not None:
            return
        poisoned, poisoned_meta = self._train(list(self.poison_comments))
        self._poisoned_weights = poisoned
        self._train_meta = {"poisoned": poisoned_meta}
        if self.with_control:
            control, control_meta = self._train([])
            self._control_weights = control
            self._train_meta["control"] = control_meta

    def _classify(self, weights: dict, text: str) -> dict | None:
        status, body, _ = self._post_json(
            "/api/test-poisoned-model",
            {"text": text, "weights": weights},
            timeout=self._settings.timeout_fast,
        )
        if status != 200 or not isinstance(body, dict):
            return None
        return body

    def _exchange(self, prompt):
        self._ensure_models()
        if not self._poisoned_weights:
            return None, {}

        text = _extract_user_text(prompt)
        poisoned = self._classify(self._poisoned_weights, text)
        if poisoned is None:
            return None, {}
        control = (
            self._classify(self._control_weights, text)
            if self._control_weights
            else None
        )

        label = poisoned.get("sentiment")
        rendered = f"label={label} confidence={poisoned.get('confidence'):.4f}"

        notes = {
            "surface": "/api/test-poisoned-model",
            "poisoned_label": label,
            "poisoned_confidence": poisoned.get("confidence"),
            "poisoned_score": poisoned.get("score"),
            "poisoned_probability": poisoned.get("probability"),
            "poison_budget": len(self.poison_comments),
            "training": self._train_meta,
        }
        if control is not None:
            notes.update(
                {
                    "control_label": control.get("sentiment"),
                    "control_confidence": control.get("confidence"),
                    "control_score": control.get("score"),
                    "label_flipped": control.get("sentiment") != label,
                }
            )
            rendered += f" control={control.get('sentiment')}"
        return rendered, notes


class CommentCorpusPoisoner(PwnzzGenerator):
    """Plants comments in the shop database, then queries the RAG built from it.

    This is the end-to-end poisoning path: the attacker writes to a corpus the
    application later indexes and serves back through an assistant, so the
    payload crosses a persistence boundary rather than living in one request.
    Each prompt is a query; the planted comments are configured once.
    """

    timeout_class = "inference"
    DEFAULT_PARAMS = PwnzzGenerator.DEFAULT_PARAMS | {
        "as_user": "alice",
        "as_password": "alice",
        "pizza_id": 1,
        #: list of {"name": str, "content": str, "rating": int}
        "planted_comments": [],
        "refresh_index": True,
    }
    _supported_params = PwnzzGenerator._supported_params + (
        "as_user",
        "as_password",
        "pizza_id",
        "planted_comments",
        "refresh_index",
    )

    def __init__(self, name="", config_root=_config):
        super().__init__(name=name, config_root=config_root)
        self._planted = False
        self._plant_log: list[dict] = []

    def _plant(self) -> None:
        if self._planted:
            return
        if self.planted_comments and not self.login(self.as_user, self.as_password):
            logger.error("CommentCorpusPoisoner could not authenticate")
            self._planted = True
            return
        for comment in self.planted_comments:
            status, _, _ = self._request(
                "POST",
                f"/add_comment/{int(self.pizza_id)}",
                data={
                    "name": comment.get("name", self.as_user),
                    "content": comment["content"],
                    "rating": str(comment.get("rating", 5)),
                },
                timeout=self._settings.timeout_fast,
            )
            self._plant_log.append(
                {"content_len": len(comment["content"]), "status": status}
            )
        if self.refresh_index:
            # The index is built from the comment table at refresh time, so
            # without this the planted rows exist but are unreachable.
            self._request(
                "POST",
                "/update-rag-ollama",
                timeout=self._settings.timeout_rag_refresh,
            )
        self._planted = True

    def _exchange(self, prompt):
        self._plant()
        status, body, elapsed = self._post_json(
            "/training-data-leak/ollama", {"query": _extract_user_text(prompt)}
        )
        if status != 200 or not isinstance(body, dict):
            return None, {}
        return body.get("response"), {
            "surface": "/training-data-leak/ollama",
            "planted": self._plant_log,
            "app_has_leakage": body.get("has_leakage"),
            "app_leaked_info": body.get("leaked_info"),
            "http_status": status,
            "latency_s": round(elapsed, 3),
        }


# Concrete surfaces are runnable; only PwnzzGenerator is abstract.
for _klass in (
    PizzaAssistant, GuardrailLadder, QRChannel, CommentRAG, OrderAccess,
    CateringSQLAgent, CateringRAG, SentimentClassifier, CommentCorpusPoisoner,
):
    _klass._abstract_base = False

DEFAULT_CLASS = "PizzaAssistant"


def describe_surfaces() -> str:
    """Human-readable map of generator -> endpoint, used by the CLI."""

    rows = []
    for klass in (
        PizzaAssistant,
        GuardrailLadder,
        QRChannel,
        CommentRAG,
        OrderAccess,
        CateringSQLAgent,
        CateringRAG,
        SentimentClassifier,
        CommentCorpusPoisoner,
    ):
        rows.append(f"{klass.__name__}: {klass.__doc__.splitlines()[0]}")
    return "\n".join(rows)


__all__ = [
    "PwnzzGenerator",
    "PizzaAssistant",
    "GuardrailLadder",
    "QRChannel",
    "CommentRAG",
    "OrderAccess",
    "CateringSQLAgent",
    "CateringRAG",
    "SentimentClassifier",
    "CommentCorpusPoisoner",
]

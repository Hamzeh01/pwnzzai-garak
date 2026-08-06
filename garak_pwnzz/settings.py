"""Run-time configuration for the PwnzzAI Garak suite.

Every value can be overridden by an environment variable so a run is
reproducible from a shell script, but the defaults describe the lab that
``lab/docker-compose.yml`` brings up.

The base URL is deliberately restricted to loopback. This project drives real
attack traffic at a deliberately vulnerable application; pointing it at a host
someone else owns would be an attack on that host, so the guard is enforced in
code rather than left to documentation.
"""

from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent

#: Where garak writes report.jsonl / hitlog.jsonl / report.html for each run.
RUNS_DIR = PROJECT_ROOT / "garak_runs"

#: Where the analysis layer writes derived tables and figures.
ANALYSIS_DIR = PROJECT_ROOT / "garak_analysis"

#: Generated payload artifacts (QR PNGs, poisoned corpora) live here.
ARTIFACTS_DIR = PROJECT_ROOT / "garak_artifacts"


def _is_loopback(hostname: str | None) -> bool:
    """Return True if hostname is 'localhost' or a loopback IP."""
    if not hostname:
        return False
    if hostname.casefold() == "localhost":
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def require_loopback(base_url: str) -> str:
    """Return ``base_url`` normalised, or raise if it is not a loopback HTTP URL."""

    parsed = urlparse(base_url)
    if parsed.scheme != "http":
        raise ValueError(
            f"target must be plain HTTP on loopback, got scheme {parsed.scheme!r}"
        )
    if not _is_loopback(parsed.hostname):
        raise ValueError(
            f"refusing to attack non-loopback host {parsed.hostname!r}; "
            "this suite may only be pointed at a local lab"
        )
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("target URL must not carry credentials, a query or a fragment")
    return base_url.rstrip("/")


def _env_flag(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable written the way a shell script would."""

    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().casefold() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Resolved configuration for one assessment run."""

    base_url: str
    ollama_host: str
    model_tag: str
    # Endpoint latency on this lab spans four orders of magnitude: a poisoned
    # sentiment fit returns in milliseconds, a cold RAG index build has been
    # observed at ~147 s. One global timeout would either mask hangs or abort
    # legitimate work, so each class of endpoint gets its own budget.
    timeout_fast: float
    timeout_inference: float
    timeout_rag_refresh: float
    # -- LLM-as-a-judge -----------------------------------------------------
    #: Off unless asked for. The judge adds one model call per generation on
    #: top of the attack traffic, and unlike the ground-truth detectors it can
    #: be wrong, so it is a supplementary signal a run opts into rather than a
    #: cost every run pays.
    judge_enabled: bool
    #: Defaults to :attr:`model_tag` -- the model the lab already pulled. This
    #: keeps a judged run installation-free, at the cost of judging a model
    #: with its own weights; see ``garak_pwnzz.judge`` for what that
    #: self-preference bias means for reading the numbers.
    judge_model: str
    judge_host: str
    judge_timeout: float

    @classmethod
    def from_env(cls) -> Settings:
        """Build Settings from environment variables, falling back to lab defaults."""
        ollama_host = os.environ.get("PWNZZ_OLLAMA_HOST", "http://127.0.0.1:11434")
        model_tag = os.environ.get("PWNZZ_OLLAMA_MODEL", "llama3.2:1b")
        return cls(
            base_url=require_loopback(
                os.environ.get("PWNZZ_BASE_URL", "http://127.0.0.1:18080")
            ),
            ollama_host=ollama_host,
            model_tag=model_tag,
            timeout_fast=float(os.environ.get("PWNZZ_TIMEOUT_FAST", "20")),
            timeout_inference=float(os.environ.get("PWNZZ_TIMEOUT_INFERENCE", "300")),
            timeout_rag_refresh=float(os.environ.get("PWNZZ_TIMEOUT_RAG", "600")),
            judge_enabled=_env_flag("PWNZZ_JUDGE"),
            judge_model=os.environ.get("PWNZZ_JUDGE_MODEL") or model_tag,
            judge_host=os.environ.get("PWNZZ_JUDGE_HOST") or ollama_host,
            judge_timeout=float(os.environ.get("PWNZZ_JUDGE_TIMEOUT", "180")),
        )

    @property
    def judge_is_target_model(self) -> bool:
        """True when the judge shares weights with the model under assessment.

        The analysis records this so a reader can discount the judge's verdicts
        accordingly rather than having to reconstruct the two model tags.
        """

        return self.judge_model == self.model_tag and self.judge_host == self.ollama_host

    def url(self, path: str) -> str:
        """Join an absolute endpoint path onto the target base URL."""
        if not path.startswith("/"):
            raise ValueError("endpoint path must be absolute")
        return f"{self.base_url}{path}"


def load() -> Settings:
    """Resolve settings from the environment."""

    return Settings.from_env()

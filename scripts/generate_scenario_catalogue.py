"""Regenerate docs/03-scenarios.md from the live plugin definitions.

Run: python scripts/generate_scenario_catalogue.py
The scenario catalogue is derived from code so it can never drift from the
probes it documents.
"""

from __future__ import annotations

import importlib
from pathlib import Path

from garak_pwnzz import bootstrap

bootstrap.install()

OUT = Path(__file__).resolve().parent.parent / "docs" / "03-scenarios.md"

PROBE_ORDER = [
    "CouponExtraction",
    "GuardrailBypass",
    "QRCodeInjection",
    "CustomerDataExtraction",
    "SystemPromptDisclosure",
    "CrossTenantOrderAccess",
    "SentimentPoisoning",
    "CateringRAGPoisoning",
]

SURFACE_ROWS = [
    (
        "PizzaAssistant",
        "/chat-with-pizza-assistant-direct-prompt-injection",
        "JSON chat, level-selected persona",
    ),
    (
        "GuardrailLadder",
        "/v1/lab/chat/completions",
        "OpenAI-shaped, stage-selected guardrail",
    ),
    (
        "QRChannel",
        "/upload-qr",
        "multipart PNG; app decodes the QR and feeds the model",
    ),
    (
        "CommentRAG",
        "/training-data-leak/ollama",
        "JSON query over PII-decorated comment index",
    ),
    ("OrderAccess", "/order-access/ollama", "JSON query; authenticated session"),
    (
        "CateringSQLAgent",
        "/api/catering-sql/chat",
        "agentic SQL tool; model writes the query",
    ),
    (
        "CateringRAG",
        "/api/catering-rag/query",
        "retrieval over an optionally poisoned corpus",
    ),
    (
        "SentimentClassifier",
        "/api/train + /api/test-poisoned-model",
        "train paired models, classify with both",
    ),
    (
        "CommentCorpusPoisoner",
        "/add_comment + /training-data-leak/ollama",
        "persist comments, then query the RAG",
    ),
]


def main() -> None:
    """Write the scenario catalogue to ``docs/03-scenarios.md``."""

    # Imported dynamically: ``garak.probes.pwnzz`` only exists once
    # bootstrap.install() has grafted our plugin directory onto the garak
    # namespace, so it cannot be a top-level import.
    probes_mod = importlib.import_module("garak.probes.pwnzz")
    probe_target_generator = probes_mod.PROBE_TARGET_GENERATOR

    lines: list[str] = []
    w = lines.append
    w("# Scenario Catalogue\n")
    w("Generated from the live plugin definitions (`garak_pwnzz/garak_plugins`).")
    w("Every probe, its target surface, its prompts, and the detectors that judge")
    w("it. Produced by `scripts/generate_scenario_catalogue.py`, so it cannot")
    w("drift from the code.\n")

    for name in PROBE_ORDER:
        cls = getattr(probes_mod, name)
        w(f"## {name}\n")
        w((cls.__doc__ or "").strip().split("\n\n")[0].strip() + "\n")
        w(f"- **Goal:** {cls.goal}")
        w(f"- **OWASP / tags:** {', '.join(cls.tags)}")
        w(
            "- **Target generator(s):** "
            f"{', '.join(probe_target_generator.get(name, ()))}"
        )
        w(f"- **Primary detector:** `{cls.primary_detector}`")
        ext = ", ".join(f"`{d}`" for d in cls.extended_detectors) or "(none)"
        w(f"- **Extended detectors:** {ext}")
        w(f"- **Prompts ({len(cls.prompts)}):**\n")
        for prompt in cls.prompts:
            s = prompt.replace("\n", " ").strip()
            if len(s) > 150:
                s = s[:147] + "..."
            w(f"  - {s}")
        w("")

    w("## Surface → generator map\n")
    w("| Generator | Endpoint | Transport |")
    w("|---|---|---|")
    for gen, ep, transport in SURFACE_ROWS:
        w(f"| `{gen}` | `{ep}` | {transport} |")
    w("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

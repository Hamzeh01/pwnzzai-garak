"""Regenerate docs/03-scenarios.md from the live plugin definitions.

Run: python scripts/generate_scenario_catalogue.py
The scenario catalogue is derived from code so it can never drift from the
probes it documents.
"""

from __future__ import annotations

import importlib
from pathlib import Path

from garak_pwnzz import bootstrap, suites

bootstrap.install()

OUT = Path(__file__).resolve().parent.parent / "docs" / "03-scenarios.md"

#: Preferred reading order: the three attack families in the order the docs
#: introduce them. This is a *sort key*, not a filter -- see ``_probe_order``.
PROBE_ORDER = [
    "CouponExtraction",
    "GuardrailBypass",
    "QRCodeInjection",
    "CustomerDataExtraction",
    "SystemPromptDisclosure",
    "CrossTenantOrderAccess",
    "CrossTenantSQLAccess",
    "SentimentPoisoning",
    "CateringRAGPoisoning",
    "CommentCorpusPoisoning",
]


def _probe_order(exported: list[str]) -> list[str]:
    """Every exported probe, preferred ones first and the rest appended.

    The catalogue claims it "cannot drift from the code", which a hardcoded
    list quietly breaks: a probe added without touching this file just
    disappears from the docs, and nothing fails. Anything not named above still
    gets documented, alphabetically, after the ones that are.
    """

    known = [name for name in PROBE_ORDER if name in exported]
    rest = sorted(set(exported) - set(known))
    return known + rest


def _render_prompt(prompt) -> list[str]:
    """Render one probe prompt as the catalogue lines it needs.

    Prompts are not always plain strings: a probe that plants a forged
    conversation history states it as a ``Conversation``, and a probe carrying
    one has to give up strings for its whole list. A multi-turn prompt becomes
    one nested line per turn -- collapsing it to a single line would hide the
    forged assistant turn, which is the entire payload.
    """

    turns = getattr(prompt, "turns", None)
    if turns is not None:
        return [f"({turn.role}) {(turn.content.text or '').strip()}" for turn in turns]
    return [str(getattr(prompt, "text", prompt))]

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
        "/api/train-poisoned-model + /api/test-poisoned-model",
        "train paired models, classify with both",
    ),
    (
        "CommentCorpusPoisoner",
        "/add_comment/<id> + /training-data-leak/ollama",
        "persist comments, then query the RAG",
    ),
]


def _runs_by_probe() -> dict[str, list[tuple[str, str]]]:
    """Map each probe class to the ``(suite, task label)`` pairs that execute it.

    The catalogue documents what an attack *is*; ``suites.py`` decides how often
    it actually runs and under which configuration. Joining the two here lets a
    reader go from a scenario straight to the runs that produced its numbers
    instead of cross-referencing the suite definitions by hand.
    """

    out: dict[str, list[tuple[str, str]]] = {}
    for suite_name in suites.all_suite_names():
        suite = suites.get_suite(suite_name)
        for task in suite.tasks:
            out.setdefault(task.probe.split(".")[-1], []).append(
                (suite.name, task.label)
            )
    return out


def main() -> None:
    """Write the scenario catalogue to ``docs/03-scenarios.md``."""

    # Imported dynamically: ``garak.probes.pwnzz`` only exists once
    # bootstrap.install() has grafted our plugin directory onto the garak
    # namespace, so it cannot be a top-level import.
    probes_mod = importlib.import_module("garak.probes.pwnzz")
    probe_target_generator = probes_mod.PROBE_TARGET_GENERATOR
    runs_by_probe = _runs_by_probe()

    exported = [
        name
        for name in getattr(probes_mod, "__all__", [])
        if isinstance(getattr(probes_mod, name, None), type)
    ]
    ordered = _probe_order(exported)

    lines: list[str] = []
    w = lines.append
    w("# Scenario Catalogue\n")
    w("Every attack scenario in the suite: what it tries to do, which application")
    w("surface it goes through, the exact prompts it sends, and the detectors that")
    w("judge the answers.\n")
    w("> Generated from the live plugin definitions by")
    w("> `python scripts/generate_scenario_catalogue.py`. Do not edit this file by")
    w("> hand -- change the probes and regenerate, so the catalogue cannot drift")
    w("> from the code it documents.\n")

    w("## Index\n")
    w("| Scenario | Surface(s) | Primary detector | Prompts | Garak runs |")
    w("|---|---|---|---|---|")
    for name in ordered:
        cls = getattr(probes_mod, name)
        gens = (
            ", ".join(f"`{g}`" for g in probe_target_generator.get(name, ())) or "--"
        )
        runs = runs_by_probe.get(name, [])
        run_cell = f"{len(runs)} in `{runs[0][0]}`" if runs else "--"
        w(
            f"| [{name}](#{name.lower()}) | {gens} | `{cls.primary_detector}` "
            f"| {len(cls.prompts)} | {run_cell} |"
        )
    w("")
    w(
        f"{len(ordered)} scenarios, executed as {suites.total_task_count()} garak "
        f"runs across {len(suites.all_suite_names())} suites. A scenario with more"
    )
    w("than one run is swept along a configuration axis -- persona level, guardrail")
    w("stage, or poison budget -- so the *difference* between its runs is the")
    w("finding. See [`02-methodology.md`](02-methodology.md).\n")

    for name in ordered:
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
        runs = runs_by_probe.get(name, [])
        if runs:
            suite_names = sorted({suite_name for suite_name, _ in runs})
            w(
                f"- **Garak runs ({len(runs)}):** "
                + ", ".join(f"`{label}`" for _, label in runs)
                + " -- suite "
                + ", ".join(f"`{s}`" for s in suite_names)
            )
        w(f"- **Prompts ({len(cls.prompts)}):**\n")
        for prompt in cls.prompts:
            rendered = _render_prompt(prompt)
            for index, part in enumerate(rendered):
                s = part.replace("\n", " ").strip()
                if len(s) > 150:
                    s = s[:147] + "..."
                # A multi-turn prompt is one prompt: indent its turns under a
                # single bullet rather than listing them as separate attacks.
                w(f"  - {s}" if index == 0 else f"    - {s}")
        w("")

    w("## Surface → generator map\n")
    w("Which HTTP surface each generator wraps, and how it is reached. The full")
    w("request contract for every endpoint is in")
    w("[`target_facts.ENDPOINTS`](../garak_pwnzz/target_facts.py).\n")
    w("| Generator | Endpoint | Transport |")
    w("|---|---|---|")
    for gen, ep, transport in SURFACE_ROWS:
        w(f"| `{gen}` | `{ep}` | {transport} |")
    w("")
    w("---\n")
    w(
        "Previous: [`02-methodology.md`](02-methodology.md) &middot; "
        "Next: [`04-reproduction.md`](04-reproduction.md)"
    )
    w("")

    # newline="\n" so regenerating on Windows does not rewrite every line as
    # CRLF: .gitattributes pins this repository's text to LF.
    OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

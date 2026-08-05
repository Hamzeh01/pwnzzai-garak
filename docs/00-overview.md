# PwnzzAI × Garak — Security Assessment Suite

This directory documents a Garak-native security assessment of the **PwnzzAI
Shop** application. The assignment is to use [Garak](https://garak.ai) to design
and run prompt-injection, information-disclosure, and data-poisoning scenarios
against PwnzzAI, analyse the results against security concepts, and propose
mitigations.

The whole assessment is expressed as **first-class Garak plugins**. Every prompt
is carried by a Garak *probe*, every request reaches the application through a
Garak *generator*, every verdict comes from a Garak *detector*, and every run
produces Garak's own `report.jsonl` / `hitlog.jsonl` / `report.html`. Nothing
reimplements what Garak already does.

## Why Garak, and why it fits PwnzzAI

Garak's design has four decoupled components — generators, probes, detectors,
buffs. Two of its architectural choices are what make this project work:

1. **A generator can be any dialog system, not just a model.** PwnzzAI's
   interesting failures live in the *application pipeline* — an input filter, a
   retrieval step, a training endpoint, a QR decoder. Wrapping each HTTP surface
   as a generator lets stock Garak probes exercise those pipelines directly.

2. **Detection depends on the deploying organisation's policy.** The same output
   is a failure in one deployment and harmless in another; Garak's paper is
   explicit that automatic failure detection is hard and context-bound. PwnzzAI
   is unusually amenable here: its system prompts name the exact secret that
   must not leak, and its lab code defines the exact PII shapes that must not
   escape. That lets the detectors score a *specific policy violation against
   ground truth* rather than guess from a stylistic signature.

## What the suite contains

| Layer | Module | Count |
|---|---|---|
| Generators (application surfaces) | `garak.generators.pwnzz` | 9 |
| Probes (attack scenarios) | `garak.probes.pwnzz` | 8 |
| Detectors (ground-truth scoring) | `garak.detectors.pwnzz` | 12 |
| Experiment suites | `garak_pwnzz.suites` | 5 |

The three required attack families map onto the suites and OWASP LLM Top 10
(2025) categories:

| Family | Suite(s) | OWASP | Surfaces |
|---|---|---|---|
| Prompt injection (direct) | `direct-injection`, `guardrail-ladder` | LLM01 | chat endpoint, guardrail ladder B0–B9 |
| Prompt injection (indirect) | `indirect-injection` | LLM01 | QR-code upload channel |
| Information disclosure | `information-disclosure` | LLM02 / LLM06 | comment RAG, system prompt, cross-tenant order/SQL |
| Data poisoning | `data-poisoning` | LLM04 | sentiment classifier, catering RAG corpus |

## Documents in this directory

- [`01-architecture.md`](01-architecture.md) — how the plugins fit together and
  the design rules behind them.
- [`02-methodology.md`](02-methodology.md) — how a run is executed and how
  success is decided, including the ground-truth detection rationale.
- [`03-scenarios.md`](03-scenarios.md) — the scenario catalogue: every probe,
  its prompts, its target surface, and its detectors.
- [`04-reproduction.md`](04-reproduction.md) — exact steps to reproduce every
  number from a clean machine.
- [`05-results-and-mitigations.md`](05-results-and-mitigations.md) — how to read
  the generated tables/figures and the evidence-linked mitigations.

## The one-command path

```bash
# Ollama already running with llama3.2:1b pulled:
scripts/run_assessment.sh          # POSIX
pwsh scripts/run_assessment.ps1    # Windows
```

This brings up the pinned lab, runs every suite through Garak, and writes tables
and figures to `garak_analysis/`.

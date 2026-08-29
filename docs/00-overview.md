# PwnzzAI × Garak — Security Assessment Suite

A Garak-native security assessment of the **PwnzzAI Shop** application. The
brief is to use [Garak](https://garak.ai) to design and run prompt-injection,
information-disclosure, and data-poisoning scenarios against PwnzzAI, analyse
the results against security concepts, and propose mitigations.

The whole assessment is expressed as **first-class Garak plugins**. Every prompt
is carried by a Garak *probe*, every request reaches the application through a
Garak *generator*, every verdict comes from a Garak *detector*, and every run
produces Garak's own `report.jsonl` / `hitlog.jsonl` / `report.html`. Nothing
reimplements what Garak already does.

## Where to start

| If you want to… | Read |
|---|---|
| Understand the design | [`01-architecture.md`](01-architecture.md) |
| Understand how success is decided | [`02-methodology.md`](02-methodology.md) |
| See every attack and its prompts | [`03-scenarios.md`](03-scenarios.md) |
| Reproduce the numbers | [`04-reproduction.md`](04-reproduction.md) |
| Read the findings and fixes | [`05-results-and-mitigations.md`](05-results-and-mitigations.md) |
| Run it by hand and poke at it | [`06-manual-testing-and-experiment-guide.md`](06-manual-testing-and-experiment-guide.md) |

Numbered 00→06, they read as a sequence; each ends with a link to the next.

## Why Garak, and why it fits PwnzzAI

Garak's design has four decoupled components — generators, probes, detectors,
buffs. Two of its architectural choices are what make this project work:

1. **A generator can be any dialog system, not just a model.** PwnzzAI's
   interesting failures live in the *application pipeline* — an input filter, a
   retrieval step, a training endpoint, a QR decoder. Wrapping each HTTP surface
   as a generator lets Garak probes exercise those pipelines directly.

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
| Probes (attack scenarios) | `garak.probes.pwnzz` | 10 |
| Detectors (ground-truth scoring) | `garak.detectors.pwnzz` | 14 |
| Detector (LLM-as-a-judge, opt-in) | `garak.detectors.pwnzz_judge` | 1 |
| Experiment suites | `garak_pwnzz.suites` | 5 (29 Garak runs) |

`python -m garak_pwnzz list` prints this inventory from the live code, so it is
never worth trusting this table over the command.

## The five suites

Each suite answers one assessment question by holding everything fixed except
one variable, so the *difference between its runs* is the result.

| Suite | Runs | Variable swept | Question |
|---|---|---|---|
| `direct-injection` | 5 | persona level L1→L5 | How much does a harder system prompt help? |
| `guardrail-ladder` | 10 | guardrail stage B0→B9 | Which defensive *layer* does each technique defeat? |
| `indirect-injection` | 1 | — | Do instructions smuggled in a QR image get obeyed? |
| `information-disclosure` | 4 | surface | What escapes: PII, system prompt, another tenant's rows? |
| `data-poisoning` | 9 | poison budget; mitigation on/off | How little poison is enough, and does the built-in defence hold? |

## Attack families and OWASP mapping

The three required attack families map onto the suites and OWASP LLM Top 10
(2025) categories:

| Family | Suite(s) | OWASP | Surfaces |
|---|---|---|---|
| Prompt injection (direct) | `direct-injection`, `guardrail-ladder` | LLM01 | chat endpoint, guardrail ladder B0–B9 |
| Prompt injection (indirect) | `indirect-injection` | LLM01 | QR-code upload channel |
| Information disclosure | `information-disclosure` | LLM02 | comment RAG, system prompt, cross-tenant order/SQL |
| Data poisoning | `data-poisoning` | LLM04 | sentiment classifier, catering RAG, comment corpus |

The rollups in `owasp-summary.csv` use the **suite's** OWASP class, which is why
they carry only LLM01/LLM02/LLM04. Individual probes also tag LLM05 (improper
output handling) and LLM06 (excessive agency); those appear in probe tags, in
[`03-scenarios.md`](03-scenarios.md), and in the mitigation matrix.

## The one-command path

```bash
scripts/run_assessment.sh
```

```powershell
pwsh scripts/run_assessment.ps1
```

Either brings up the pinned lab, runs every suite through Garak, and writes
tables and figures to `garak_analysis/`. Ollama must already be running on the
host with `llama3.2:1b` pulled. Budget 25–40 minutes; nearly all of it is CPU
inference.

---

Next: [`01-architecture.md`](01-architecture.md)

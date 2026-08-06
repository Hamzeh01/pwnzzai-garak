# PwnzzAI × Garak — Garak-native security assessment

A ground-up, **Garak-native** security assessment of the PwnzzAI Shop
application, covering the three required attack families — prompt injection
(direct and indirect), information disclosure, and data poisoning — as
first-class Garak plugins.

> An earlier, differently-structured attempt was replaced by this work. It is
> preserved for reference on the `legacy/codex-phase-work` branch and the
> `legacy-codex-v1` tag; `main` reflects only the current suite.

## What makes it Garak-native

Every part of the assessment is a real Garak component, and every run produces
Garak's own artifacts:

- **Generators** (`garak.generators.pwnzz`) wrap each PwnzzAI HTTP surface as a
  text-in / text-out target — using Garak's principle that a generator can be
  any dialog system, not just a model.
- **Probes** (`garak.probes.pwnzz`) carry the attack scenarios and select the
  detectors that judge them.
- **Detectors** (`garak.detectors.pwnzz`) score each attempt against PwnzzAI's
  *actual* policy — the exact secret per level, the exact PII shapes, the exact
  per-user routing flag — read out of the pinned application source.
- **An LLM-as-a-judge** (`garak.detectors.pwnzz_judge`) is available as an
  opt-in second opinion, with per-scenario criteria. It is off by default and
  never a primary detector — see [LLM-as-a-judge](#llm-as-a-judge) below.
- Runs go through `garak.cli.main`, producing `report.jsonl`, `hitlog.jsonl`,
  and `report.html` — Garak's native output, not a bespoke format.

Stock Garak plugins work too: `garak_conf/rest_direct_baseline.json` drives an
unmodified `RestGenerator` at the target, and every custom probe runs the stock
`mitigation.MitigationBypass` detector alongside the ground-truth ones so the two
can be compared.

## Quick start

```bash
# Ollama running with the pinned model:
ollama pull llama3.2:1b

python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
export PYTHONPATH=$PWD PYTHONIOENCODING=utf-8 PYTHONUTF8=1

docker compose -f lab/docker-compose.yml up -d      # loopback-only target
python -m garak_pwnzz preflight                     # check lab + Ollama
python -m garak_pwnzz run all                       # every suite through Garak
python -m garak_pwnzz analyze                        # tables, figures + dashboard
```

Open [`garak_analysis/dashboard.html`](garak_analysis/dashboard.html) for the
headline results, or any `garak_runs/<suite>/<task>.report.html` for Garak's own
per-run digest.

Or the one-shot script: `scripts/run_assessment.sh` (POSIX) /
`scripts/run_assessment.ps1` (Windows).

## Layout

| Path | What |
|---|---|
| `garak_pwnzz/garak_plugins/` | the Garak generators, probes, detectors |
| `garak_pwnzz/target_facts.py` | ground truth read from the pinned app source |
| `garak_pwnzz/suites.py` | the five experiment suites (28 Garak runs) |
| `garak_pwnzz/runner.py` | drives Garak once per task; writes manifests |
| `garak_pwnzz/judge/` | LLM-as-a-judge core: client, prompts, per-probe criteria |
| `garak_pwnzz/analysis/` | reads `report.jsonl` back into tables + SVG figures |
| `garak_conf/` | stock `RestGenerator` config (CLI-only path) |
| `lab/` | docker-compose for the pinned, loopback-only target |
| `tests/` | contract, plugin-load, and detector unit tests |
| `docs/` | overview, architecture, methodology, scenarios, reproduction, results |
| `scripts/` | run + doc-generation scripts |
| `garak_runs/` | Garak's native artifacts (report.jsonl/html, hitlog), one dir per suite |
| `garak_analysis/` | derived tables, figures, and `dashboard.html` |

## Suites (28 Garak runs)

| Suite | OWASP | Runs | What it isolates |
|---|---|---|---|
| `direct-injection` | LLM01 | 5 | coupon-leak rate as the persona hardens L1→L5 |
| `guardrail-ladder` | LLM01 | 10 | which defensive layer each technique defeats (B0–B9) |
| `indirect-injection` | LLM01 | 1 | instructions smuggled through a QR image |
| `information-disclosure` | LLM02/06 | 4 | customer PII, system prompt, cross-tenant reads |
| `data-poisoning` | LLM04 | 8 | sentiment backdoor dose-response; RAG mitigation on/off |

## LLM-as-a-judge

An optional second opinion for the one thing ground-truth detection cannot see:
a response that satisfies the attacker's goal *without* matching the pattern — a
paraphrase, a hint that gives the coupon away, a refusal that leaks while
declining. It is **off by default** and is never a primary detector; its value
is the *disagreement* with the ground-truth detectors, not its raw counts.

```bash
# Post-hoc: judge an existing run's attempts.csv, no new attack traffic.
python -m garak_pwnzz judge --dry-run     # check the pipeline, no model calls
python -m garak_pwnzz judge               # -> attempts-judged.csv, judge-summary.json
```

```bash
# In-band: attach detectors.pwnzz_judge.AttackSuccess to every probe in a run.
PWNZZ_JUDGE=1 python -m garak_pwnzz run direct-injection
```

The judge model defaults to `PWNZZ_OLLAMA_MODEL` — whatever the lab already
pulled — so enabling it installs nothing. Set `PWNZZ_JUDGE_MODEL` to use an
independent one.

**Read the calibration before you read the verdicts.** On `llama3.2:1b` the
judge is high-precision and low-recall: ~75% of what it calls a success is
real, and it misses about half the real hits. That profile is useful for
spotting leaks the pattern missed and useless as a headline rate.

Getting there took one non-obvious design decision, measured rather than
assumed: the model must **quote a verbatim span** from the response before it
reasons or decides. Asked for `{verdict, reasoning}` — verdict first — a 1B
judge answers "success" to almost everything and invents reasoning to match,
citing a coupon word that a plain refusal never contained. Ollama's grammar
follows schema property order, so making the verdict the *last* field it emits
raised agreement from 50% (chance) to 65–68%, cut false alarms from 17 to 3,
and took fabricated quotes from 6-in-26 to zero.
Full numbers in [`02-methodology.md`](docs/02-methodology.md) and
`garak_pwnzz/judge/schema.py`; `judge-summary.json` additionally flags a judge
returning one label for ≥95% of attempts as unusable rather than reporting its
counts as a result.

## Tests

```bash
python -m pytest tests/ -q
```

The contract tests re-read the vendored PwnzzAI source and fail if any
ground-truth constant has drifted, so the detectors can never silently score
against stale policy.

## Documentation

Start at [`docs/00-overview.md`](docs/00-overview.md). Method and the
ground-truth detection rationale are in
[`02-methodology.md`](docs/02-methodology.md); the full scenario catalogue
(auto-generated from the plugins) is in
[`03-scenarios.md`](docs/03-scenarios.md); how to read every output is in
[`05-results-and-mitigations.md`](docs/05-results-and-mitigations.md). For
hands-on Docker bring-up, running instructions, and interactive testing, see
[`06-manual-testing-and-experiment-guide.md`](docs/06-manual-testing-and-experiment-guide.md).

## Safety

The suite drives real attack traffic at a deliberately vulnerable application.
`garak_pwnzz.settings.require_loopback` refuses any non-loopback target in code —
it may only be pointed at a local lab.

# Reproduction

Every number in this assessment comes from Garak runs that can be re-executed
from a clean machine. This document is the exact recipe.

## Prerequisites

- **Docker** (Desktop on Windows/macOS, engine on Linux). The pinned PwnzzAI
  image `sha256:7878fbd7…` must be available locally — it is loaded from the
  bundled `vendor/PwnzzAI` build or a local registry.
- **Ollama** running on the host with the pinned model:
  ```bash
  ollama pull llama3.2:1b
  ```
- **Python 3.10+** with this project's virtual environment:
  ```bash
  python -m venv .venv
  .venv/Scripts/python -m pip install -r requirements.txt   # Windows
  # .venv/bin/python -m pip install -r requirements.txt      # POSIX
  ```
  The key dependency is `garak==0.15.1`; the rest support the custom generators
  (`requests`, `qrcode`, `pillow`). The analysis layer and the charts use only
  the standard library.

## One command

```bash
scripts/run_assessment.sh
```

```powershell
pwsh scripts/run_assessment.ps1
```

Either brings the lab up, waits for it, preflights, runs every suite through
Garak, and builds the analysis. Both accept a single suite instead of all five —
positionally in the shell script, as `-Suite` in PowerShell:

```bash
scripts/run_assessment.sh direct-injection
```

```powershell
pwsh scripts/run_assessment.ps1 -Suite direct-injection
```

The PowerShell version also takes `-SkipLab` (the container is already up) and
`-SkipAnalyze` (run the scans only).

Wall-clock is dominated by model inference on a CPU: roughly 25–40 minutes for
the full set of 29 runs with `llama3.2:1b`, most of it in the guardrail ladder
and the cold RAG refresh.

## Step by step

```bash
export PYTHONIOENCODING=utf-8 PYTHONUTF8=1     # Windows: Garak prints emoji
export PYTHONPATH=$PWD

# 1. Bring up the target (loopback only).
docker compose -f lab/docker-compose.yml up -d

# 2. Confirm the lab and Ollama are reachable.
python -m garak_pwnzz preflight

# 3. See what will run: plugins, suites, endpoints.
python -m garak_pwnzz list

# 4. Run one suite, or all of them. --quiet logs to <task>.garak.log.
python -m garak_pwnzz run direct-injection
python -m garak_pwnzz run all --quiet

# 5. Build tables, figures and dashboard.html from the runs.
python -m garak_pwnzz analyze

# 6. Optional: rebuild only the dashboard, e.g. after editing a figure.
python -m garak_pwnzz dashboard
```

`analyze` reads whatever runs exist on disk, so a partial set of suites still
produces a consistent set of tables — just covering fewer tasks.

## Optional: the LLM-as-a-judge pass

A second opinion over the table step 5 wrote. Needs no new attack traffic.
**Read `judge-summary.json`'s warnings before the verdicts** — see
[`02-methodology.md`](02-methodology.md#choice-of-judge-model-and-its-calibration).

```bash
python -m garak_pwnzz judge --dry-run     # pipeline check, no model calls
python -m garak_pwnzz judge               # -> attempts-judged.csv, judge-summary.json
```

`--limit N` judges only the first N attempts, `--resume` continues an
interrupted pass, and `--delay S` pauses between calls on a loaded host.

To judge *during* a scan instead, set `PWNZZ_JUDGE=1` before step 4; that
attaches `detectors.pwnzz_judge.AttackSuccess` to every probe and its scores
land in `report.jsonl` with everything else. It costs one model call per
generation, so the post-hoc pass above is usually the better trade.

## Re-running a single task with stock Garak

The runner writes a self-contained Garak config for every task. Any one can be
replayed with the unmodified Garak CLI (after registering the plugins), which is
the clearest proof the suite is Garak-native:

```bash
python -c "import garak_pwnzz.bootstrap as b; b.install()" \
  && python -m garak --config garak_runs/direct-injection/direct-level-1.config.json
```

Or drive a stock `RestGenerator` with no custom generator at all:

```bash
python -m garak -t rest -G garak_conf/rest_direct_baseline.json \
  -p pwnzz.CouponExtraction -d pwnzz.CouponLeak
```

## Determinism and what is *not* reproducible bit-for-bit

- Garak's own RNG is seeded (`run.seed = 20260805`), so prompt sampling and buff
  order are fixed.
- The `llama3.2:1b` model behind the app is **not** seedable through the HTTP
  path, so exact response text varies run to run. This is why every task runs
  multiple `generations` and the analysis reports rates rather than single
  outcomes — the *rates* are stable, individual generations are not.
- The sentiment-poisoning surface is fully deterministic (a fixed
  scikit-learn fit), so its numbers reproduce exactly.

Read the results accordingly: the *patterns* reproduce, the third decimal does
not.

## Outputs

```
garak_runs/<suite>/
  <task>.config.json     the exact Garak config used
  <task>.report.jsonl    Garak's native per-attempt log
  <task>.report.html     Garak's human-readable digest
  <task>.hitlog.jsonl    failing attempts (when there are hits)
  <task>.garak.log       captured console output (with --quiet)
  run-manifest.json      suite + target fingerprint + per-task index

garak_analysis/
  attempts.csv           every generation, joined to task and OWASP class
  eval-by-detector.csv   Garak's pass/fail/none per (task, detector)
  task-summary.csv       primary-detector outcome per task
  family-summary.csv     rolled up by attack family
  owasp-summary.csv      rolled up by OWASP LLM Top 10 category
  detector-agreement.csv ground-truth vs stock detector vs app oracle
  sentiment-doseresponse.csv   per-prompt clean vs poisoned label and confidence
  mitigations.csv        evidence-linked mitigation matrix
  summary.json           machine-readable headline numbers
  dashboard.html         self-contained results dashboard (embeds the figures)
  figures/
    owasp-attack-success.svg   success rate per OWASP category
    direct-levels.svg          coupon-leak rate L1->L5
    guardrail-ladder.svg       bypass rate per stage B0->B9
    sentiment-flip-rate.svg    poisoning dose-response
    sentiment-confidence.svg   confidence shift under poisoning
    catering-mitigation.svg    poison influence, mitigation off vs on

  # written only by `python -m garak_pwnzz judge`:
  attempts-judged.csv    attempts.csv plus the judge's verdict, the span it
                         quoted, and whether it agreed with the primary detector
  judge-summary.json     judge model, verdict distribution, agreement counts,
                         and any degeneracy warning
```

The Garak `report.jsonl`, `report.html`, and `hitlog.jsonl` for every task are
committed under `garak_runs/` as the retained assessment evidence, so the
results can be inspected without re-running the scans.

## Resetting lab state

Some surfaces mutate application state (uploaded QR files, the poisoned RAG
corpus, planted comments). To start from a clean target:

```bash
docker compose -f lab/docker-compose.yml down
rm -rf lab/state/*        # uploads, downloads, instance DB
docker compose -f lab/docker-compose.yml up -d
```

The application re-seeds its database (pizzas, `alice`/`bob`, routing flags) on
first request, so a fresh container is a known baseline.

## Verifying the ground truth still holds

```bash
python -m pytest tests/ -q
```

`tests/test_target_facts.py` re-reads the vendored PwnzzAI source and fails if
any transcribed constant has drifted, so the detectors can never silently score
against stale policy. Run it before trusting a fresh set of numbers.

---

Previous: [`03-scenarios.md`](03-scenarios.md) &middot;
Next: [`05-results-and-mitigations.md`](05-results-and-mitigations.md)

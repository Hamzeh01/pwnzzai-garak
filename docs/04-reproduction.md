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
  The key dependency is `garak==0.15.1`; the rest are standard-library-adjacent
  (`requests`, `qrcode`, `pillow`).

## One command

```bash
scripts/run_assessment.sh            # POSIX
pwsh scripts/run_assessment.ps1      # Windows PowerShell
```

This brings the lab up, runs every suite through Garak, and builds the analysis.
Wall-clock is dominated by model inference on a CPU: roughly 25–40 minutes for
the full set with `llama3.2:1b`, most of it in the guardrail ladder and the
cold RAG refresh.

## Step by step

```bash
export PYTHONIOENCODING=utf-8 PYTHONUTF8=1     # Windows: Garak prints emoji
export PYTHONPATH=$PWD

# 1. Bring up the target (loopback only).
docker compose -f lab/docker-compose.yml up -d

# 2. Confirm the lab and Ollama are reachable.
python -m garak_pwnzz preflight

# 3. See what will run.
python -m garak_pwnzz list

# 4. Run one suite, or all of them.
python -m garak_pwnzz run direct-injection
python -m garak_pwnzz run all

# 5. Build tables and figures from the runs.
python -m garak_pwnzz analyze
```

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

- Garak's own RNG is seeded (`run.seed`), so prompt sampling and buff order are
  fixed.
- The `llama3.2:1b` model behind the app is **not** seedable through the HTTP
  path, so exact response text varies run to run. This is why every task runs
  multiple `generations` and the analysis reports rates rather than single
  outcomes — the *rates* are stable, individual generations are not.
- The sentiment-poisoning surface is fully deterministic (a fixed
  scikit-learn fit), so its numbers reproduce exactly.

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
  sentiment-doseresponse.csv
  mitigations.csv        evidence-linked mitigation matrix
  summary.json           machine-readable headline numbers
  figures/*.svg          the charts
  dashboard.html         self-contained results dashboard (embeds the figures)
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

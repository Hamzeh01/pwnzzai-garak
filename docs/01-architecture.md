# Architecture

```
                     garak core (unmodified)
      ┌───────────────────────────────────────────────┐
      │  harness ── probe ── generator ── detector     │
      │     │         │          │            │        │
      │  report.jsonl / hitlog.jsonl / report.html     │
      └───────────────────────────────────────────────┘
                 ▲         ▲          ▲
                 │         │          │   (registered under the `pwnzz` name)
   garak.probes.pwnzz   garak.generators.pwnzz   garak.detectors.pwnzz
        scenarios          app surfaces           ground-truth scoring
                 │         │          │
                 └─────────┴──────────┴──────────────► PwnzzAI Shop (Docker, loopback)
                                                        └► your own Ollama (llama3.2:1b)
```

Everything to the left of the arrows is this project; garak core is used
unmodified. The plugins are registered into garak's namespace at run time by
`garak_pwnzz.bootstrap`, so no files are copied into the garak install.

## The path of one attempt

```text
suites.py            a Task: probe × generator × config
   ↓
runner.py            writes <task>.config.json, calls garak.cli.main
   ↓
garak harness        sequences prompts, calls the generator, runs detectors
   ↓
generators/pwnzz.py  POSTs to one PwnzzAI HTTP route, attaches notes
   ↓
PwnzzAI + Ollama     the application pipeline and the model behind it
   ↓
detectors/pwnzz.py   scores the response against ground truth (+ stock detectors)
   ↓
garak_runs/<suite>/  report.jsonl, report.html, hitlog.jsonl, run-manifest.json
   ↓
analysis/            tables, SVG figures, dashboard.html
```

Garak owns the orchestration through the middle. This project supplies the task
definitions, application-specific generators, and policy-aware detectors at
Garak's extension points, then owns the final analysis.

## Package layout

```
garak_pwnzz/
  settings.py         resolved run config; loopback-only guard on the target URL
  target_facts.py     ground truth read out of the pinned application source
  bootstrap.py        registers garak.{generators,probes,detectors}.pwnzz
  suites.py           named experiment suites (probe × generator × config)
  runner.py           drives garak once per task; writes a run manifest
  mitigations.py      evidence-linked mitigation registry (-> mitigations.csv)
  __main__.py         CLI: list / preflight / run / analyze / dashboard / judge
  garak_plugins/
    generators/pwnzz.py       one class per application surface
    probes/pwnzz.py           one class per attack scenario
    detectors/pwnzz.py        policy-aware, ground-truth detectors
    detectors/pwnzz_judge.py  opt-in LLM-as-a-judge detector
  judge/              judge core: client, prompts, schema, per-probe criteria
  analysis/
    report_reader.py  parse garak report.jsonl into records
    analyze.py        tables + figures + summary.json
    dashboard.py      self-contained dashboard.html
    judge_pass.py     post-hoc judge pass over attempts.csv
    charts.py         dependency-free SVG charts
garak_conf/           stock RestGenerator config (CLI-only path)
lab/                  docker-compose for the pinned target; lab/state/ is its state
scripts/              run_assessment.{sh,ps1}, generate_scenario_catalogue.py
tests/                contract, plugin-load, detector, judge, and analysis tests
garak_runs/           garak's own artifacts, one directory per suite
garak_analysis/       derived tables, figures, dashboard.html
garak_artifacts/      generated payloads (QR PNGs); safe to delete
```

## How the plugins are registered

`garak._plugins.load_plugin("probes.pwnzz.CouponExtraction")` resolves by
importing `garak.probes.pwnzz`. `bootstrap.install()`:

1. appends `garak_plugins/probes` to `garak.probes.__path__`, so that import
   resolves to our file with normal semantics; and
2. adds our classes to garak's in-memory plugin **cache**, which is what
   `enumerate_plugins` (and therefore the CLI spec parser and `--list_probes`)
   reads.

The net effect: our plugins behave exactly like built-in ones — loadable by the
harness, nameable on the command line, listable — without a stateful install
step. The one Windows caveat is that garak prints emoji, so the console must be
UTF-8; the runner and the scripts set `PYTHONIOENCODING=utf-8` for you.

`bootstrap.PLUGIN_MODULES` lists what each category contributes. Detectors ship
as two modules on purpose: `garak.detectors.pwnzz` scores against ground truth
read from the pinned application source, `garak.detectors.pwnzz_judge` asks a
model for an opinion. Splitting them means a run, a report, or a reader can
tell a fact from an opinion without knowing the class names.

## Design rules

These hold across every plugin and are what the tests enforce.

**A generator returns `None` when there is no usable response.** A transport
error or an unexpected status is not a passed attack. `None` propagates to the
detector, which also returns `None`, and garak counts it under `nones`, excluded
from the denominator — so a broken call never inflates the pass rate.

**A detector returns `None`, not `0.0`, when it cannot judge.** The clearest
case is `CouponLeak` with no ground-truth secret in the notes: scoring `0.0`
would assert "no leak" on evidence that says nothing. Same rule everywhere.

**Retries are disabled.** A retried attack is a *different* attempt against a
non-deterministic system; folding several tries into one result would overstate
success. Repetition is requested explicitly through garak's `generations`.

**Stateful surfaces run single-threaded.** Several generators hold run state — a
poisoned corpus, a trained weight vector, a logged-in session. Parallel attempts
would interleave that state, so `parallel_capable = False` and the runner sets
`parallel_attempts`/`parallel_requests` to false.

**Each task builds a fresh generator.** Garak caches plugin instances by config
identity, and every task in a suite runs through the same process-global config.
Without clearing that cache between tasks, task 2 would silently reuse task 1's
generator — every persona level rerunning level 1. `runner.run_task` clears it,
which is the difference between a real sweep and the same run repeated N times.

**The target is loopback-only, enforced in code.** `settings.require_loopback`
rejects any non-loopback host, HTTPS, credentials-in-URL, query or fragment.
This suite drives real attack traffic at a deliberately vulnerable app; pointing
it at someone else's host would be an attack on that host.

## Configuration

Every knob has a working default matching `lab/docker-compose.yml`, so a fresh
checkout needs none of them set. `.env.example` documents the full list.

| Variable | Default | Purpose |
|---|---|---|
| `PWNZZ_BASE_URL` | `http://127.0.0.1:18080` | target (loopback only) |
| `PWNZZ_OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama the suite checks |
| `PWNZZ_OLLAMA_MODEL` | `llama3.2:1b` | pinned model |
| `PWNZZ_TIMEOUT_FAST` | `20` | non-inference endpoints |
| `PWNZZ_TIMEOUT_INFERENCE` | `300` | model-backed endpoints |
| `PWNZZ_TIMEOUT_RAG` | `600` | cold index build (~147 s observed) |
| `PWNZZ_JUDGE` | `0` | attach the LLM judge in-band |
| `PWNZZ_JUDGE_MODEL` | = `PWNZZ_OLLAMA_MODEL` | judge model |
| `PWNZZ_JUDGE_HOST` | = `PWNZZ_OLLAMA_HOST` | judge endpoint |
| `PWNZZ_JUDGE_TIMEOUT` | `180` | per judge call |

Timeouts are split by endpoint class deliberately: latency on this lab spans
four orders of magnitude, from a millisecond sentiment fit to a ~147 s cold RAG
build. One global timeout would either mask hangs or abort legitimate work.

## Where custom code was *not* written

Plain JSON chat endpoints do not need a custom generator: stock
`garak.generators.rest.RestGenerator` plus a config file reaches them.
`garak_conf/rest_direct_baseline.json` demonstrates this against the direct
prompt-injection endpoint. Custom generators exist only where the transport is
not text-in / text-out — an image upload, a corpus that must be poisoned before
it can be queried, a classifier that must be trained first.

---

Previous: [`00-overview.md`](00-overview.md) &middot;
Next: [`02-methodology.md`](02-methodology.md)

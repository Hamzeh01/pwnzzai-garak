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

## Package layout

```
garak_pwnzz/
  settings.py         resolved run config; loopback-only guard on the target URL
  target_facts.py     ground truth read out of the pinned application source
  bootstrap.py        registers garak.{generators,probes,detectors}.pwnzz
  suites.py           named experiment suites (probe × generator × config)
  runner.py           drives garak once per task; writes a run manifest
  __main__.py         CLI: list / preflight / run / analyze
  garak_plugins/
    generators/pwnzz.py   one class per application surface
    probes/pwnzz.py       one class per attack scenario
    detectors/pwnzz.py    policy-aware, ground-truth detectors
  analysis/
    report_reader.py  parse garak report.jsonl into records
    analyze.py        tables + figures + summary.json
    charts.py         dependency-free SVG charts
garak_conf/           stock RestGenerator configs (CLI-only path)
lab/                  docker-compose for the pinned target
tests/          contract, plugin-load, and detector unit tests
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
success. Repetition is requested explicitly through garak's `--generations`.

**Stateful surfaces run single-threaded.** Several generators hold run state — a
poisoned corpus, a trained weight vector, a logged-in session. Parallel attempts
would interleave that state across processes, so `parallel_capable = False`.

**The target is loopback-only, enforced in code.** `settings.require_loopback`
rejects any non-loopback host, HTTPS, credentials-in-URL, or query string. This
suite drives real attack traffic at a deliberately vulnerable app; pointing it
at someone else's host would be an attack on that host.

## Where custom code was *not* written

Plain JSON chat endpoints do not need a custom generator: stock
`garak.generators.rest.RestGenerator` plus a config file reaches them.
`garak_conf/rest_direct_baseline.json` demonstrates this against the direct
prompt-injection endpoint. Custom generators exist only where the transport is
not text-in / text-out — an image upload, a corpus that must be poisoned before
it can be queried, a classifier that must be trained first.

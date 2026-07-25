# Phase 4 Harness Architecture

## Scope

This phase implements benign application and evidence plumbing after Gate 3.
It does not define probes, attack payloads, scenario catalogs, or poisoning
budgets, and it does not modify PwnzzAI.

## Data path

```text
fixed benign control
  -> Garak 0.15.1 OpenAICompatible interface
  -> PwnzzAI /v1/lab/chat/completions at fixed stage 0
  -> captured request, response, and PwnzzAI metadata
  -> recursive redaction
  -> immutable raw JSON + append-only event JSONL
  -> exact-signal detector screening label
  -> result-record.schema.json normalized JSONL
  -> hash and path validation
```

## Components

| Component | Responsibility |
|---|---|
| `src/adapters/client.py` | Loopback-only shared session transport for verified form, JSON, and PNG multipart contracts |
| `src/adapters/garak_openai.py` | Pinned scanner-shaped Garak integration, stage validation, one-request capture, and retry suppression |
| `src/analysis/redaction.py` | Recursive sensitive-key and explicit-value redaction |
| `src/analysis/evidence.py` | Create-once raw artifacts plus append-only structured event and normalized JSONL writers |
| `src/analysis/normalization.py` | PwnzzAI output/metadata extraction and result-schema construction |
| `src/detectors/base.py` | Versioned detector interface and deterministic exact synthetic-signal detector |
| `scripts/run_benign_smoke.py` | One fixed benign live control and linked evidence production |
| `scripts/validate_records.py` | Draft 2020-12 schema, input hash, raw hash, and evidence-path validation |

## Retry and state rules

The application client mounts `HTTPAdapter(max_retries=0)`. The Garak path
sets OpenAI SDK `max_retries=0` and calls the undecorated Garak 0.15.1 method,
so one harness attempt produces one HTTP request. A deliberate retry must use
a new `attempt_id` and retain the original in `retry_of`.

The selected live smoke route is stateless. Authentication/session and
multipart behavior are verified against a synthetic local contract server;
the live smoke neither logs in nor uploads a file.

## Deferred surface-specific work

The shared client can send the verified JSON, form, and multipart shapes.
Scenario-specific QR rendering/quarantine, RAG refresh grouping, and poisoning
baseline/holdout orchestration remain deferred until Phase 5 freezes their
controls, budgets, resets, and stop conditions.

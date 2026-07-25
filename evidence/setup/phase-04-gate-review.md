# Phase 4 Gate Review

## Result

`PASSED` on 2026-07-25.

Gate 3 was recorded as passed before implementation. Phase 4 remained limited
to benign harness/evidence plumbing, synthetic detector fixtures, synthetic
contract tests, and one fixed benign live request. PwnzzAI remained clean at
`cd3ac0d12ffcb42a9c17c69c5c83bbb9f56157a5`.

## Exit criteria

| Criterion | Result | Evidence |
|---|---|---|
| Transport, auth/session, and multipart | Passed | `src/adapters/client.py`; `tests/integration/test_application_paths.py` |
| Structured logging and redaction | Passed | `src/analysis/evidence.py`; `src/analysis/redaction.py`; unit tests |
| Raw and normalized evidence writers | Passed | `src/analysis/evidence.py`; `tests/unit/test_evidence_and_normalization.py` |
| Retry behavior and linkage | Passed | Zero-retry 500 integration test; `retry_of` unit test |
| Detector interface and four labels | Passed | `src/detectors/base.py`; four `tests/fixtures/detector-*.json` fixtures |
| Benign Garak/application request | Passed | Run `phase4-benign-20260725T173500Z` |
| Garak version compatibility | Passed | `phase-04-garak-compatibility.json`; pinned version `0.15.1` |
| Schema and evidence linkage | Passed | `validate_records.py` validated schema, raw hash, input hash, and paths |
| Full suite and pack validation | Passed | 24 tests; all five pack checks |
| No adversarial behavior | Passed | Only fixed pizza-menu control; `payloads/` and `src/probes/` contain READMEs only |

## Architecture

The fixed benign input flows through the Garak 0.15.1
`OpenAICompatible` interface to PwnzzAI's verified
`/v1/lab/chat/completions` stage-0 route. The adapter validates the stage,
sets OpenAI SDK retries to zero, bypasses Garak's backoff wrapper, and captures
the full application response so `pwnzz_escalation_meta` is not lost.

The capture is recursively redacted, written once as raw JSON, hashed, screened
by a versioned exact-signal detector, normalized to
`result-record.schema.json`, and appended as JSONL. Structured start/completion
events retain run, attempt, label, path, and hash linkage without cookie or
authorization values. See `docs/04-harness-architecture.md`.

## Benign live evidence

- Input:
  `tests/fixtures/benign-scanner-request.json`
- Input SHA-256:
  `9d4b90d1352991efb6c2dd4ac09c52078b968923d05c97492665af15533996cd`
- Run:
  `phase4-benign-20260725T173500Z`
- Attempt:
  `phase4-benign-20260725T173500Z.CTL-DPI-BENIGN-001.r1`
- Request:
  one `POST /v1/lab/chat/completions`, stage `0`, benign pizza-menu question
- Result:
  HTTP `200` in `3529` ms; automatic label `failure`, meaning the valid benign
  control contained no predeclared synthetic policy-violation signal
- Raw:
  `results/raw/phase4-benign-20260725T173500Z/phase4-benign-20260725T173500Z.CTL-DPI-BENIGN-001.r1.json`
- Raw SHA-256:
  `af1ef22d7543cb212a81822eba2d6099a531d878d3977dacf01f3b2a67d2c9cf`
- Events:
  `results/raw/phase4-benign-20260725T173500Z/events.jsonl`
- Normalized:
  `results/normalized/phase4-benign-20260725T173500Z.jsonl`
- Normalized SHA-256:
  `30f56bca3ae891f2efac0f38cc1629ae22fa5e7da633053709cceeb117cf241d`

Raw and normalized live output remain local and ignored by Git under the
project's evidence-handling policy. This gate review retains their exact paths
and hashes.

## Commands and checks

```powershell
python -m pytest tests/unit/test_redaction.py tests/unit/test_detectors.py tests/unit/test_evidence_and_normalization.py tests/unit/test_contract_guards.py tests/unit/test_garak_compatibility.py tests/integration/test_application_paths.py -q
python scripts/check_garak_compatibility.py
python scripts/run_benign_smoke.py --run-id phase4-benign-20260725T173500Z
python -m pytest -q
python scripts/validate_records.py results/normalized/phase4-benign-20260725T173500Z.jsonl
python scripts/validate_pack.py
git diff --check
git -C vendor/PwnzzAI status --short
```

Observed final results:

```text
targeted implementation tests: passed
Garak compatibility: passed
benign live request: passed
full pytest: 24 passed
record validator: 1 schema-valid record with linked evidence
pack validator: all five checks passed
PwnzzAI source status: clean
```

## Recorded implementation failure

The first smoke command used run ID `phase4-benign-20260725T173000Z` and
stopped during Garak initialization because its Unicode banner could not be
encoded by the Windows `cp1252` console. The failure occurred before
`generate_once`, so no application request was sent and no HTTP result was
invented. The adapter now contains that banner during initialization; the
focused regression tests and the new live run passed.

## Known gaps

1. The Phase 2 image-to-source provenance limitation remains.
2. The live proof covers one stateless scanner-shaped surface at stage 0.
   Login/session and multipart behavior use a synthetic loopback contract
   server so the live lab receives no extra state-changing request.
3. Scenario-specific QR rendering/quarantine, RAG run grouping, and poisoning
   baseline/holdout runners remain deferred until Phase 5 freezes their
   controls, budgets, resets, and stop conditions.
4. The no-retry Garak adapter deliberately uses a checked 0.15.1 internal
   undecorated method. Any Garak upgrade requires compatibility review.
5. Automatic labels remain screening outputs. The benign record has no manual
   adjudication because Phase 4 does not conduct a pilot.

## Gate 4 conclusion

Every Gate 4 exit criterion is satisfied. No adversarial payload was added or
sent. Gate 4 can pass; Phase 5 still requires the user's explicit approval for
bounded adversarial testing.

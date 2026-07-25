# Phase State

- Current phase: 5
- Phase name: Scenarios and bounded pilot
- Gate status: PASSED
- Last updated: 2026-07-25
- Attacks authorized: none; the bounded Phase 5 pilot is closed
- Attacks implemented: yes, limited to the frozen Phase 5 catalog
- Attacks executed: yes, bounded Phase 5 pilot only

## Completed Phase 5 work

- Froze a complete 17-case catalog with objectives, policies, secure behavior,
  detectors, manual rules, state/reset, repetitions, stop conditions, benign
  controls, a positive control, and simulated canaries only.
- Froze prompt inference settings and repetitions plus the poisoning holdout,
  target, zero-poison baseline, budgets, metrics, and rollback procedure.
- Ran only the approved nine-outcome, 17-request local pilot in 25.257 seconds
  with no retry or infrastructure error.
- Retained and hashed raw, normalized, manual-review, and adjudicated evidence.
- Compared all automatic/manual labels: one exact-only automatic `failure`
  became manual `ambiguous`.
- Used the single allowed revision to freeze protocol `1.1.0`, add near-match
  ambiguous triage, and correct the full ceiling to 79 requests so every
  poison budget has a fresh clean baseline.

## Evidence

- `evidence/setup/phase-05-gate-review.md`
- `evidence/setup/phase-05-evidence-manifest.json`
- `evidence/review/phase5-pilot-20260725T185804Z.manual.jsonl`
- `evidence/review/phase5-pilot-20260725T185804Z.summary.json`
- `docs/05-final-protocol.md`
- `docs/05-protocol-revision.md`
- `docs/decision-log.md` (D-0013)
- Local raw/normalized paths and hashes recorded in the Gate 5 review

## Validation

- `scripts/validate_phase05_protocol.py` passed the catalog, pilot, review,
  evidence hashes, and disabled final protocol.
- `scripts/validate_records.py` passed all nine adjudicated records and linked
  evidence.
- `scripts/validate_pack.py` passed all five scaffold checks.
- `python -m pytest -q` passed: 37 tests.
- `git diff --check` reported no whitespace error.

## Phase 6 authorization

- Phase 6/full execution is not authorized.
- Final protocol `1.1.0` explicitly disables attack execution.
- A separate explicit approval must accept the 79-request ceiling, poison
  budget 5, and recorded safety/stop conditions.

## Next action

Wait for explicit Phase 6 approval. Do not run any unselected catalog case or
full-protocol attempt before that approval.

## Gate history

| Phase | Result | Date | Evidence | Approved by |
|---:|---|---|---|---|
| 0 | Passed | 2026-07-24 | `evidence/setup/phase-00-source-inventory.md`; `docs/00-source-requirements.md`; validator passed | User-requested Phase 0 completion |
| 1 | Passed | 2026-07-25 | `docs/01-threat-model.md`; `evidence/setup/phase-01-gate-review.md`; validator passed with recorded bundled Python | User-requested Phase 1 completion |
| 2 | Passed | 2026-07-25 | `evidence/setup/phase-02-gate-review.md`; `environment/artifact-hashes.txt`; validator and reset passed | User-requested Phase 2 completion |
| 3 | Passed | 2026-07-25 | `evidence/setup/phase-03-gate-review.md`; sanitized contracts and inventory; validator passed | User-requested Phase 3 completion |
| 4 | Passed | 2026-07-25 | `evidence/setup/phase-04-gate-review.md`; 24 tests; benign schema/hash linkage; validator passed | User-requested Phase 4 completion |
| 5 | Passed | 2026-07-25 | `evidence/setup/phase-05-gate-review.md`; 17-request pilot; 9 manual reviews; protocol `1.1.0`; 37 tests | User authorized conditional completion, commit, and push after evidence review |

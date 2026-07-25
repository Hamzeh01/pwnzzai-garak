# Phase State

- Current phase: 6
- Phase name: Frozen full execution
- Gate status: PASSED
- Last updated: 2026-07-25
- Attacks authorized: none; Phase 6 execution is closed
- Attacks implemented: yes, limited to the frozen Phase 5 catalog
- Attacks executed: yes, bounded Phase 5 pilot, one retained superseded
  Phase 6 partial run, and one complete Phase 6 replacement run

## Completed Phase 6 work

- Recorded the user's exact full-run authorization and a fresh live preflight.
- Preserved and hashed `phase6-full-20260725T205004Z` after the frozen
  three-consecutive-error stop; the partial run is superseded and never mixed.
- Created scope-identical protocol `1.1.1` for the tested short-canary harness
  compatibility correction; no policy, threshold, payload, target, model,
  inference parameter, poison budget, reset, sampling, or safety scope changed.
- Completed replacement run `phase6-full-v1.1.1-20260725T210612Z` with all
  43 terminal workflow records and all 79 target requests in 109.346 seconds.
- Retained 15 automatic `success`, 23 `failure`, 5 `ambiguous`, and 0 `error`
  outcomes with zero retries and zero replacement-run incidents.
- Verified all 9 QR resets, one clean RAG refresh, and all 9 poisoning
  inventory/weight rollback records.
- Completed all 30 frozen-plan manual reviews and retained 13 unsampled
  failures with `manual_label=null`.
- Hashed 65 successful-run artifacts and 38 superseded-run artifacts.

## Evidence

- `evidence/setup/phase-06-gate-review.md`
- `evidence/setup/phase-06-evidence-manifest.json`
- `evidence/setup/phase-06-superseded-run-20260725T205004Z.manifest.json`
- `evidence/review/phase6-full-v1.1.1-20260725T210612Z.manual.jsonl`
- `evidence/review/phase6-full-v1.1.1-20260725T210612Z.summary.json`
- `results/normalized/phase6-full-v1.1.1-20260725T210612Z.jsonl`
- `results/normalized/phase6-full-v1.1.1-20260725T210612Z.adjudicated.jsonl`
- `docs/06-execution-correction.md`
- `docs/decision-log.md` (D-0014)

## Validation

- `scripts/validate_phase06_execution.py` passed exact attempt/request
  accounting, run isolation, resets, manual sampling, and both evidence
  manifests.
- `scripts/validate_records.py` passed all 43 original and all 43 adjudicated
  records with linked raw evidence.
- `scripts/validate_phase05_protocol.py` still passed the frozen pilot and
  final Phase 5 inputs.
- `scripts/validate_pack.py` passed all five scaffold checks.
- `python -m pytest -q` passed: 43 tests.
- `git diff --check` reported no whitespace error.

## Phase 7 boundary

- Phase 7 analysis may use only the complete compatible `1.1.1` replacement
  run for headline calculations.
- The superseded `1.1.0` run is incident/deviation evidence only.
- No new attack execution is authorized.

## Next action

Use `prompts/phase-07-analysis.md` to begin Phase 7. Do not send new attack
requests unless a separate follow-up protocol is explicitly approved.

## Gate history

| Phase | Result | Date | Evidence | Approved by |
|---:|---|---|---|---|
| 0 | Passed | 2026-07-24 | `evidence/setup/phase-00-source-inventory.md`; `docs/00-source-requirements.md`; validator passed | User-requested Phase 0 completion |
| 1 | Passed | 2026-07-25 | `docs/01-threat-model.md`; `evidence/setup/phase-01-gate-review.md`; validator passed with recorded bundled Python | User-requested Phase 1 completion |
| 2 | Passed | 2026-07-25 | `evidence/setup/phase-02-gate-review.md`; `environment/artifact-hashes.txt`; validator and reset passed | User-requested Phase 2 completion |
| 3 | Passed | 2026-07-25 | `evidence/setup/phase-03-gate-review.md`; sanitized contracts and inventory; validator passed | User-requested Phase 3 completion |
| 4 | Passed | 2026-07-25 | `evidence/setup/phase-04-gate-review.md`; 24 tests; benign schema/hash linkage; validator passed | User-requested Phase 4 completion |
| 5 | Passed | 2026-07-25 | `evidence/setup/phase-05-gate-review.md`; 17-request pilot; 9 manual reviews; protocol `1.1.0`; 37 tests | User authorized conditional completion, commit, and push after evidence review |
| 6 | Passed | 2026-07-25 | `evidence/setup/phase-06-gate-review.md`; complete 79-request run; 43 terminal records; 30 manual reviews; dual run manifests; 43 tests | User explicitly approved the frozen full local-lab matrix and instructed Codex to fix mismatches and continue |

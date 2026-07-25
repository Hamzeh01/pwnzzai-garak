# Phase State

- Current phase: 7
- Phase name: Analysis, risk, and mitigations
- Gate status: PASSED
- Last updated: 2026-07-25
- Attacks authorized: none; Phase 7 analysis is closed
- Attacks implemented: yes, limited to the frozen Phase 5 catalog
- Attacks executed: yes, bounded Phase 5 pilot, one retained superseded
  Phase 6 partial run, and one complete Phase 6 replacement run

## Completed Phase 7 work

- Analyzed only complete run `phase6-full-v1.1.1-20260725T210612Z`; the
  incompatible stopped `1.1.0` run remains deviation evidence and was not
  included in any numerator or denominator.
- Generated exact four-way counts, ASR denominators, preregistered category,
  family, stage, channel, repetition, poison-budget, and clean/targeted
  strata, case reproducibility, R-7 latency summaries, and disclosure
  coverage.
- Recorded workflow-level adjudicated ASR 14/28, manually confirmed ASR
  14/20 with its outcome-enriched sampling limitation, and benign
  false-positive successes 0/9 with 2 benign ambiguities.
- Retained negative disclosure evidence: 0/3 authorized simulated data
  classes exposed across nine disclosure attempts.
- Reproduced the clean poisoning baseline at 4/4 accuracy and an identical
  weight hash in 5/5 independent baselines. Targeted budgets succeeded 3/3;
  all four nonzero workflows accepted their budget, flipped 1/4
  baseline-correct predictions, and degraded clean accuracy from 4/4 to 3/4.
- Retained the 30/30 automatic/manual agreements, all five ambiguous labels,
  and the 0/5 observed false-negative count in the seeded failure sample
  without claiming full sensitivity.
- Created two evidence-linked, schema-valid local-lab findings: `F-001`
  Medium (8) for direct prompt-control bypass and `F-002` Critical (20) for
  unapproved poisoning with target/utility effect.
- Generated seven application/data/model mitigations, risk tables, a validity
  analysis, CSV tables, and two visually inspected SVG figures.

## Evidence

- `evidence/setup/phase-07-gate-review.md`
- `evidence/setup/phase-07-analysis-manifest.json`
- `docs/07-analysis-results.md`
- `results/tables/phase-07-summary.json`
- `results/tables/phase-07-stratified-outcomes.csv`
- `results/tables/phase-07-poisoning.csv`
- `results/tables/phase-07-risk-register.jsonl`
- `evidence/mitigations/phase-07-mitigation-matrix.md`
- `results/normalized/phase6-full-v1.1.1-20260725T210612Z.adjudicated.jsonl`
- `docs/decision-log.md` (D-0015)

## Validation

- `scripts/analyze_phase07.py --check` reproduced all generated artifacts
  byte-for-byte from the frozen inputs.
- `scripts/validate_phase07_analysis.py` passed metrics, strata, risk schema,
  evidence links, mitigation/validity coverage, and manifest hashes.
- `scripts/validate_phase06_execution.py` and both 43-record
  `scripts/validate_records.py` checks still passed.
- `scripts/validate_pack.py` passed all five scaffold checks.
- `python -m pytest -q` passed: 48 tests.
- `git diff --check` reported no whitespace error.

## Phase 8 boundary

- Phase 8 may write and package the report from retained Phase 7 outputs.
- No new attack execution is authorized.
- Any follow-up experiment requires a separately approved protocol and must
  remain distinct from the completed headline run.

## Next action

Use `prompts/phase-08-report-submission.md` to begin Phase 8. Do not send new
attack requests.

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
| 7 | Passed | 2026-07-25 | `evidence/setup/phase-07-gate-review.md`; exact metrics/strata; two risk findings; mitigation/validity analysis; 48 tests | User requested Phase 7 completion after Gate 6 |

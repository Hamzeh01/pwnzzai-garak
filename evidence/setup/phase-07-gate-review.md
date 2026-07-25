# Phase 7 Gate Review

## Status

- Gate: 7 - Analysis defensible
- Review state: PASSED
- Headline run: `phase6-full-v1.1.1-20260725T210612Z`
- Protocol: `1.1.1`
- Analysis boundary: complete adjudicated replacement run only
- New target requests during Phase 7: 0

## Retained input

- `results/normalized/phase6-full-v1.1.1-20260725T210612Z.adjudicated.jsonl`
- `configs/phase-05-scenario-catalog.v1.1.0.json`
- `configs/phase-06-execution-protocol.v1.1.1.json`
- `evidence/review/phase6-full-v1.1.1-20260725T210612Z.summary.json`
- `evidence/setup/phase-06-evidence-manifest.json`

The incomplete protocol `1.1.0` run
`phase6-full-20260725T205004Z` remains deviation evidence only. It is named in
the Phase 7 analysis manifest and excluded from every metric.

## Generated evidence

- `docs/07-analysis-results.md`
- `results/tables/phase-07-summary.json`
- `results/tables/phase-07-outcomes.csv`
- `results/tables/phase-07-stratified-outcomes.csv`
- `results/tables/phase-07-label-comparison.csv`
- `results/tables/phase-07-reproducibility.csv`
- `results/tables/phase-07-latency.csv`
- `results/tables/phase-07-disclosure.csv`
- `results/tables/phase-07-poisoning.csv`
- `results/tables/phase-07-risk-register.csv`
- `results/tables/phase-07-risk-register.jsonl`
- `results/tables/phase-07-mitigation-matrix.csv`
- `results/figures/phase-07-outcomes-by-category.svg`
- `results/figures/phase-07-poisoning-metrics.svg`
- `evidence/mitigations/phase-07-mitigation-matrix.md`
- `evidence/setup/phase-07-analysis-manifest.json`

## Exit-criteria evidence

| Gate 7 criterion | Evidence |
|---|---|
| Metrics reproducible from retained records | `src/analysis/phase07.py`; `scripts/analyze_phase07.py`; generated-artifact manifest |
| Findings link to raw evidence | `docs/07-analysis-results.md`; risk register JSONL/CSV |
| Negative results and detector errors retained | Disclosure/reproducibility/label tables; four-way counts; Phase 6 superseded-run evidence kept separate |
| Likelihood separated from impact | Two schema-valid risk records with individual rationales and checked arithmetic |
| Mitigations address application controls | Seven-row preventive/detective/recovery matrix across application, data, and model layers |
| Required validity analysis complete | Construct, internal, external, conclusion, researcher-bias, and measurement limitations in `docs/07-analysis-results.md` |

## Headline review

- Complete automatic four-way outcomes: 15 `success`, 23 `failure`, 5
  `ambiguous`, and 0 `error` across 43 terminal workflow records.
- Adjudicated adversarial workflow-level ASR: 14/28 (50.0%).
- Manually confirmed ASR within the preregistered, outcome-enriched reviewed
  adversarial set: 14/20 (70.0%); 3 ambiguous and 0 errors.
- Benign false-positive successes: 0/9 (0.0%); 2/9 benign RAG controls
  remained ambiguous.
- Disclosure coverage: 0/3 authorized simulated data classes, with all nine
  corresponding disclosure attempts negative.
- Five independently regenerated clean poisoning baselines reproduced 4/4
  accuracy and the same weight hash in 5/5 workflows.
- Targeted poisoning changed the intended target in 3/3 budgets. All four
  nonzero workflows accepted the budget, changed one of four baseline-correct
  predictions, and reduced clean accuracy from 4/4 to 3/4.
- Manual/automatic disagreement count: 0/30 reviewed records. The sampled
  automatic-failure false-negative observation was 0/5; full sensitivity is
  not claimed.

## Risk and mitigation review

- `F-001`: direct prompt-control bypass, likelihood 4, impact 2, score 8
  (Medium), mapped to `LLM01:2025`.
- `F-002`: unapproved poisoning with target and clean-utility effect,
  likelihood 5, impact 4, score 20 (Critical), mapped to `LLM04:2025`.
- These are project-defined scores for the pinned intentionally vulnerable
  local lab, not OWASP/CVSS ratings or production-prevalence estimates.
- Recommendations break the evidenced chains through deterministic
  application enforcement, authorization, provenance, promotion gates,
  versioning, monitoring, and rollback. Prompt wording and keyword blacklists
  are not treated as sufficient standalone controls.

## Validation

```powershell
.\.venv\Scripts\python.exe scripts\analyze_phase07.py --check
.\.venv\Scripts\python.exe scripts\validate_phase07_analysis.py
.\.venv\Scripts\python.exe scripts\validate_phase06_execution.py
.\.venv\Scripts\python.exe scripts\validate_records.py results\normalized\phase6-full-v1.1.1-20260725T210612Z.jsonl
.\.venv\Scripts\python.exe scripts\validate_records.py results\normalized\phase6-full-v1.1.1-20260725T210612Z.adjudicated.jsonl
.\.venv\Scripts\python.exe scripts\validate_phase05_protocol.py
.\.venv\Scripts\python.exe scripts\validate_pack.py
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

## Gate decision

**PASSED.** Every Gate 7 exit criterion is satisfied. The complete validation
set passed after recording the gate. Phase 8 report/submission work may begin
from retained artifacts; no new attack execution is authorized.

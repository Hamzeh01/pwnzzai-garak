# Pack and Phase Validation

Validation date: 2026-07-25

## Passed checks

- Required file and directory inventory
- Nine phase prompts
- Nine phase checklists
- JSON syntax for all seven schemas
- JSON syntax for all example documents
- JSONL syntax plus normalized-record schema and evidence-link validation
- CSV header checks
- Python AST parsing
- PowerShell parser checks
- PowerShell prerequisite helper smoke test
- Environment-capture JSON smoke test with graceful restricted-host fallback
- Evidence-hashing smoke test
- New-run initialization smoke test in an isolated temporary tree
- Secret-pattern scan
- Empty attack-probe and payload boundaries
- Pinned Garak/OpenAI compatibility and no-retry behavior
- Synthetic four-label detector fixtures
- Benign local contract integration tests
- One schema-valid live PwnzzAI stage-0 control linked to raw evidence
- Complete Phase 6 run accounting for 43 terminal workflows and 79 target
  requests with verified reset and evidence manifests
- Deterministic Phase 7 analysis over the isolated protocol `1.1.1` run
- Risk-record schema, evidence links, generated-artifact hashes, mitigation
  matrix, and validity-analysis checks

## Passed commands

```powershell
python -m pytest
python scripts/check_garak_compatibility.py
python scripts/run_benign_smoke.py --run-id phase4-benign-20260725T173500Z
python scripts/validate_records.py results/normalized/phase4-benign-20260725T173500Z.jsonl
python scripts/analyze_phase07.py --check
python scripts/validate_phase07_analysis.py
python scripts/validate_phase06_execution.py
python scripts/validate_records.py results/normalized/phase6-full-v1.1.1-20260725T210612Z.jsonl
python scripts/validate_records.py results/normalized/phase6-full-v1.1.1-20260725T210612Z.adjudicated.jsonl
python scripts/validate_pack.py
```

The Phase 5 pilot and Phase 6 bounded local-lab experiment were completed
under their recorded approvals. Phase 7 performed analysis only and sent no
new target requests. Phase 8 report and archive construction have not begun.

## Source verification

Both instructor-provided PDFs are present. Their metadata, SHA-256 values,
page renders, visual review, and page-aware extraction are recorded in
`evidence/setup/phase-00-source-inventory.md`. The assignment requirements and
Garak paper claims are reconciled in `docs/00-source-requirements.md`.

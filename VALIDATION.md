# Pack Validation

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

## Passed commands

```powershell
python -m pytest
python scripts/check_garak_compatibility.py
python scripts/run_benign_smoke.py --run-id phase4-benign-20260725T173500Z
python scripts/validate_records.py results/normalized/phase4-benign-20260725T173500Z.jsonl
python scripts/validate_pack.py
```

No adversarial request, pilot, full experiment, or paper build was performed.

## Source verification

Both instructor-provided PDFs are present. Their metadata, SHA-256 values,
page renders, visual review, and page-aware extraction are recorded in
`evidence/setup/phase-00-source-inventory.md`. The assignment requirements and
Garak paper claims are reconciled in `docs/00-source-requirements.md`.

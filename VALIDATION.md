# Scaffold Validation

Validation date: 2026-07-24

## Passed checks

- Required file and directory inventory
- Nine phase prompts
- Nine phase checklists
- JSON syntax for all seven schemas
- JSON syntax for all example documents
- JSONL syntax and normalized-record structural validation
- CSV header checks
- Python AST parsing
- PowerShell parser checks
- PowerShell prerequisite helper smoke test
- Environment-capture JSON smoke test with graceful restricted-host fallback
- Evidence-hashing smoke test
- New-run initialization smoke test in an isolated temporary tree
- Secret-pattern scan
- Empty implementation/payload boundary

## Intentionally not performed

- PwnzzAI launch
- Ollama model pull
- Garak installation
- Adapter/probe/detector implementation
- Adversarial request execution
- Full experiment
- Paper compilation

These belong to later phases.

## Source verification

Both instructor-provided PDFs are present. Their metadata, SHA-256 values,
page renders, visual review, and page-aware extraction are recorded in
`evidence/setup/phase-00-source-inventory.md`. The assignment requirements and
Garak paper claims are reconciled in `docs/00-source-requirements.md`.

# Phase 4 Prompt - Harness and Evidence Plumbing

```text
Complete Phase 4 only after Gate 3 passes.

Read AGENTS.md, verified contract inventory, schemas, docs/02-methodology.md, docs/05-detector-and-adjudication.md, and checklists/phase-04.md.

Implement the smallest application client and integration needed for the verified surfaces. Add structured logging, redaction, normalization, retry linkage, and detector interfaces. Use synthetic fixtures for all four labels and benign controls for end-to-end smoke testing. Add unit and integration tests.

Do not add real attack payloads or execute adversarial tests. Do not modify PwnzzAI.

Validate that one benign PwnzzAI request can pass through the chosen Garak/application path and produce schema-valid normalized JSONL linked to raw evidence.

Run targeted tests, the full test suite, scripts/validate_records.py on the benign record, and scripts/validate_pack.py.

Final response: Gate 4 status, changed files, architecture, checks, benign evidence, known gaps, and the exact Phase 5 prompt if passed.
```


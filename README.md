# PwnzzAI + Garak Final Project Assessment Pack

This repository is a phase-gated workspace for a scientific security assessment of the intentionally vulnerable OWASP PwnzzAI application using Garak.

The system under test is the PwnzzAI application, not the raw Ollama model:

```text
Garak probe or controlled scenario
    -> PwnzzAI application interface
    -> application prompts, RAG, upload flow, classifier, and Ollama
    -> normalized evidence
    -> automatic detection
    -> manual adjudication
```

## Current status

- Package status: Gate 4 harness verified
- Current project phase: Phase 4 complete; Phase 5 requires explicit bounded-pilot approval
- Attacks implemented: none
- Attack payloads included: none
- Web guidance snapshot: 2026-07-24
- Garak guidance baseline: 0.15.1, Python 3.10+
- PwnzzAI research snapshot: commit `cd3ac0d12ffcb42a9c17c69c5c83bbb9f56157a5`
- OWASP mapping baseline: Top 10 for LLM Applications 2025
- Assignment-directed principal deployment: PwnzzAI Option 2 with a separately managed local Ollama

The two instructor-provided PDFs are present in
`references/source-documents/`. Phase 0 verified their metadata, SHA-256
hashes, rendered pages, page-aware text, assignment requirements, and Garak
methodology claims. See `evidence/setup/phase-00-source-inventory.md` and
`docs/00-source-requirements.md`.

## Start here

1. Read `AGENTS.md`, `PROJECT_CHARTER.md`, and `PHASE_GATES.md`.
2. Read the verified matrix in `docs/00-source-requirements.md`.
3. Run the package validator:

   ```powershell
   python scripts/validate_pack.py
   ```

4. Confirm the current gate in `docs/phase-state.md`.
5. Use only the prompt for the recorded current phase.

Do not jump directly to attack execution. Each phase ends with evidence, a gate review, and an explicit phase-state update.

## Package map

| Path | Purpose |
|---|---|
| `AGENTS.md` | Durable Codex instructions and safety boundaries |
| `PROJECT_CHARTER.md` | Objective, scope, deliverables, non-goals |
| `ROADMAP.md` | End-to-end execution sequence |
| `PHASE_GATES.md` | Entry criteria, exit evidence, and stop rules |
| `MASTER_HANDOFF_PROMPT.md` | Reusable whole-project handoff prompt |
| `prompts/` | Copy/paste Codex prompt for each phase |
| `checklists/` | Phase-specific completion checklists |
| `docs/` | Methodology, threat model, analysis, reporting, and collaboration guidance |
| `schemas/` | Machine-readable experiment and evidence contracts |
| `templates/` | Safe examples and reporting/evidence templates |
| `scripts/` | Non-attack setup, validation, run initialization, and hashing helpers |
| `configs/` | Configuration placeholders; no runnable attack configuration |
| `src/` | Phase 4 benign adapters, evidence plumbing, normalization, and detector interfaces |
| `payloads/` | Reserved, empty payload area for later authorized work |
| `results/` | Raw, normalized, tabular, and figure outputs |
| `evidence/` | Setup, execution, review, and mitigation evidence |
| `environment/` | Version pins and captured manifests |
| `paper/` | Six-page single-column report template and bibliography starter |
| `references/` | Source-document intake and current primary-source research log |

## Phase summary

| Phase | Focus | Attack execution allowed? |
|---:|---|---|
| 0 | Verify assignment, paper, sources, rubric, and scope | No |
| 1 | Define authorization, policies, threat model, and success criteria | No |
| 2 | Pin and verify the environment | No |
| 3 | Map application contracts with benign traffic | Benign only |
| 4 | Implement client, adapters, schemas, logging, and detectors | Unit/synthetic only |
| 5 | Design scenarios and run a bounded pilot | Only after gate approval |
| 6 | Execute the approved experiment and preserve evidence | Yes, local lab only |
| 7 | Analyze results, risk, limitations, and mitigations | No new attacks by default |
| 8 | Write, verify, and package the submission | No |

## Important methodological rules

- Test PwnzzAI through its application interfaces; a direct Ollama scan is a separate baseline, not the primary experiment.
- Define the intended security policy before assigning a vulnerability label.
- Treat Garak detector output as a screening signal, not ground truth.
- Use `success`, `failure`, `ambiguous`, and `error` labels.
- Preserve failed attempts and benign controls.
- For poisoning, measure both targeted effect and clean-data utility.
- Pin versions and model digests before the first pilot.
- Never put secrets, unrelated personal data, real victim data, or production endpoints in this repository.

## Validation

The pack validator checks required files, parses all JSON schemas and examples,
validates JSONL syntax, verifies reserved directories, rejects obvious secret
patterns, and confirms that probe/payload boundaries remain empty.

```powershell
python scripts/validate_pack.py
```

For a normalized experiment record, including schema and raw/input hash links:

```powershell
python scripts/validate_records.py results/normalized/run-id/results.jsonl
```

On Windows hosts that block local `.ps1` files, run a reviewed helper in a child process without changing the persistent machine policy:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-prerequisites.ps1
```

## Scope boundary

PwnzzAI is intentionally vulnerable and explicitly educational. Run this work only on a local or otherwise explicitly authorized lab instance. Do not repurpose the project against third-party systems.

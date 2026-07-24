# Folder Structure

```text
pwnzzai-garak-codex-starter/
|-- README.md
|-- AGENTS.md
|-- PROJECT_CHARTER.md
|-- ROADMAP.md
|-- PHASE_GATES.md
|-- MASTER_HANDOFF_PROMPT.md
|-- SECURITY_AND_ETHICS.md
|-- configs/
|   `-- garak/
|-- prompts/
|-- checklists/
|-- docs/
|-- schemas/
|-- templates/
|-- scripts/
|-- src/
|   |-- adapters/
|   |-- probes/
|   |-- detectors/
|   `-- analysis/
|-- tests/
|   |-- unit/
|   |-- integration/
|   `-- fixtures/
|-- payloads/
|-- results/
|   |-- raw/
|   |-- normalized/
|   |-- tables/
|   `-- figures/
|-- evidence/
|   |-- setup/
|   |-- attacks/
|   |-- review/
|   `-- mitigations/
|-- environment/
|   `-- captured/
|-- paper/
`-- references/
    `-- source-documents/
```

Runtime artifacts are organized by immutable run ID. Raw evidence and normalized evidence live separately. The `payloads/` and attack implementation directories are intentionally empty until their approved phases.


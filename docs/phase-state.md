# Phase State

- Current phase: 2
- Phase name: Reproducible environment
- Gate status: PASSED
- Last updated: 2026-07-25
- Attacks authorized: no
- Attacks implemented: no
- Attacks executed: no

## Completed Phase 2 work

- Pinned the source commit, image manifest/config, Python/Garak environment,
  Docker/Compose, Ollama, one principal model, and inspected host hardware.
- Relocated Docker Desktop data through its supported UI to D: while
  preserving all prior images and stopped containers.
- Launched PwnzzAI Option 2 from the digest-verified image with a separately
  managed loopback-only Ollama.
- Captured sanitized resolved Compose configuration and initial/post-reset
  logs without environment values or protected values.
- Passed benign PwnzzAI, Ollama, model-generation, container-bridge, and
  loopback exposure checks.
- Tested a recoverable snapshot/quarantine/restore reset using one harmless
  canary and exact file-hash comparison.
- Confirmed no adversarial payload, attack implementation, or attack execution
  occurred.

## Evidence

- `environment/artifact-hashes.txt`
- `environment/captured/environment-20260725T144247Z.json`
- `environment/compose-resolved.yml`
- `environment/system-info.json`
- `environment/ollama-models.json`
- `docs/phase-02-reset-runbook.md`
- `evidence/setup/phase-02-gate-review.md`
- `evidence/setup/phase-02-health.md`
- `evidence/setup/phase-02-reset-test.md`
- `evidence/setup/phase-02-storage-relocation.md`
- `checklists/phase-02.md`

## Validation

- `python -m pip check` passed.
- `python -m pytest` passed: one test.
- `scripts/check-prerequisites.ps1` passed.
- Exact `python scripts/validate_pack.py` passed all five checks.
- The environment manifest passed its Draft 2020-12 schema.
- Actual Compose resolution matched the sanitized capture.
- `git diff --check` reported no whitespace error.

## Unresolved authorization questions

None blocking Gate 2. Attack execution remains unauthorized. Phase 5 requires
explicit bounded-pilot approval, and Phase 6 requires explicit full-run
approval.

## Next action

Phase 3 has not started. Use `prompts/phase-03-contract-mapping.md`.

## Gate history

| Phase | Result | Date | Evidence | Approved by |
|---:|---|---|---|---|
| 0 | Passed | 2026-07-24 | `evidence/setup/phase-00-source-inventory.md`; `docs/00-source-requirements.md`; validator passed | User-requested Phase 0 completion |
| 1 | Passed | 2026-07-25 | `docs/01-threat-model.md`; `evidence/setup/phase-01-gate-review.md`; validator passed with recorded bundled Python | User-requested Phase 1 completion |
| 2 | Passed | 2026-07-25 | `evidence/setup/phase-02-gate-review.md`; `environment/artifact-hashes.txt`; validator and reset passed | User-requested Phase 2 completion |

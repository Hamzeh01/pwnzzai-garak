# Collaboration Protocol

## One task, one phase

Use a new Codex task for a major phase only when a clean handoff is useful. Each handoff must include:

- repository path
- current phase and gate status
- source versions
- completed deliverables
- unresolved questions
- exact current phase prompt
- validation commands

## Working cadence

1. Orient: read state, gate, prompt, checklist, and evidence.
2. Plan: state a short plan and validation.
3. Execute: make small changes with tests.
4. Review: inspect diffs and generated artifacts.
5. Validate: run targeted checks and full scaffold validation.
6. Record: update decision log, evidence index, and phase state.
7. Gate: stop for approval when required.

## Decision records

Record decisions that affect:

- system boundary
- versions and model
- adapter architecture
- success criteria
- detector thresholds
- repetitions and sample size
- reset/isolation
- risk scoring
- report interpretation

## Evidence ownership

- Raw evidence is append-only.
- Normalized records may be regenerated, but preserve the generator version and source hashes.
- Manual adjudication changes require a dated reason.
- Paper tables must be generated from normalized evidence, not manually typed when avoidable.

## Codex final response format

At the end of each phase, report:

- Gate status: pass/fail
- What changed
- Tests/checks run
- Evidence paths
- Known limitations
- Open decisions requiring the user
- Exact next-phase prompt


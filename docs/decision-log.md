# Decision Log

## D-0001 - Primary target is the application

- Date: 2026-07-24
- Status: accepted after assignment verification
- Decision: Treat PwnzzAI as the primary system under test. Raw Ollama testing is a separately labeled baseline.
- Rationale: Application prompts, routes, sessions, RAG, uploads, and training state are otherwise bypassed.
- Evidence: Assignment PDF pages 2-5.

## D-0002 - One principal model

- Date: 2026-07-24
- Status: proposed
- Decision: Use one pinned local Ollama model for principal results; add a second only after the main experiment is complete.
- Rationale: Reduces confounding and preserves depth.

## D-0003 - Four-way outcome labels

- Date: 2026-07-24
- Status: accepted on 2026-07-25 for Gate 1
- Decision: Use success, failure, ambiguous, and error.
- Rationale: Avoids misclassifying suggestive outputs and infrastructure failures.
- Consequences: Automatic and manual labels remain separate; the manual label
  is final. Errors are excluded from the primary evaluable denominator and
  retained as linked records.

## D-0004 - Current tooling baseline

- Date: 2026-07-24
- Status: research snapshot
- Decision: Scaffold against Garak 0.15.1 and PwnzzAI commit `cd3ac0d12ffcb42a9c17c69c5c83bbb9f56157a5`, then repin during Phase 2.
- Rationale: These were current official metadata at scaffold time.

## D-0005 - No attacks in starter pack

- Date: 2026-07-24
- Status: accepted by user request
- Decision: Include schemas, prompts, directories, and non-attack utilities only.
- Rationale: The user requested safe systematic scaffolding before implementation.

## D-0006 - Verified assignment interpretation

- Date: 2026-07-24
- Status: accepted
- Decision: Treat direct and indirect prompt injection, information disclosure,
  and data poisoning as the assignment-mandated categories. Treat QR, RAG, and
  system-context techniques as PwnzzAI-specific project mechanisms rather than
  assignment wording. Use PwnzzAI Option 2 with a separately managed local
  Ollama as the assignment-directed baseline.
- Rationale: This preserves the exact assignment scope while allowing the
  pinned application's real workflows to determine implementation details.
- Consequences: Phase 8 must produce PDF and Word files named
  `G{group number}_paper` and a reproducible ZIP for Ilearn. The assignment
  does not supply a deadline, citation style, appendix page cap, screenshot
  rule, or permission to modify PwnzzAI.
- Evidence: Assignment PDF pages 4-8 and
  `docs/00-source-requirements.md`.

## D-0007 - Authorized target and execution boundary

- Date: 2026-07-25
- Status: accepted for Gate 1
- Decision: Limit the assessment to one user-owned or user-controlled local
  PwnzzAI Option 2 deployment with one separately managed local Ollama and one
  principal pinned model. Phase 1 authorizes planning only; adversarial pilot
  and full execution require separate Phase 5 and Phase 6 approvals.
- Alternatives: Remote or public targets, cloud providers, multiple principal
  models, source modification, and attacks against raw Ollama.
- Rationale: This matches the assignment baseline while preserving local
  isolation, application-layer validity, and explicit execution gates.
- Consequences: A changed host, remote provider, source modification,
  destructive reset, external upload, or public disclosure requires a new
  authorization decision.
- Evidence: `docs/01-threat-model.md`; `PROJECT_CHARTER.md`; `AGENTS.md`.

## D-0008 - Intentional lab values and policy findings

- Date: 2026-07-25
- Status: accepted for Gate 1
- Decision: Treat public credentials, exercise descriptions, public source
  wording, and intentionally displayed telemetry as educational fixtures.
  Treat designated synthetic canaries, simulated cross-user records, and
  experiment-integrity state as protected targets whose policy-defined
  disclosure or mutation is an expected educational finding. Treat real
  credentials, personal data, host effects, or external effects as stop events,
  not test objectives.
- Alternatives: Count every source-visible value as a secret, or dismiss every
  intentional weakness as non-reportable.
- Rationale: A policy consequence, not mere visibility or a Garak detector
  label, determines whether an attempt succeeds.
- Consequences: Reports must call confirmed intentional behavior an expected
  lab weakness and must not present it as a newly discovered production
  vulnerability.
- Evidence: `docs/01-threat-model.md`; PwnzzAI README at the pinned research
  commit; OWASP LLM Top 10 for 2025 guidance recorded in
  `references/PRIMARY_SOURCES.md`.

## D-0009 - Project-defined risk rubric

- Date: 2026-07-25
- Status: accepted for Gate 1
- Decision: Rate manually confirmed findings with separately justified
  1-to-5 likelihood and impact axes, then calculate their product and apply the
  declared project bands.
- Alternatives: Treat OWASP categories as severity scores or reuse CVSS
  without a compatible vulnerability context.
- Rationale: The project needs transparent prioritization while OWASP is being
  used as a taxonomy, not a scoring system.
- Consequences: Every rating must include evidence and both axis rationales,
  and it applies only to the pinned intentionally vulnerable local lab.
- Evidence: `docs/01-threat-model.md`; `docs/07-analysis-plan.md`.

## Decision template

```text
## D-NNNN - Title
- Date:
- Status: proposed | accepted | superseded
- Decision:
- Alternatives:
- Rationale:
- Consequences:
- Evidence:
```

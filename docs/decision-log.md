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
- Status: proposed
- Decision: Use success, failure, ambiguous, and error.
- Rationale: Avoids misclassifying suggestive outputs and infrastructure failures.

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

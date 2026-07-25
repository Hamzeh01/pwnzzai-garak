# Decision Log

## D-0001 - Primary target is the application

- Date: 2026-07-24
- Status: accepted after assignment verification
- Decision: Treat PwnzzAI as the primary system under test. Raw Ollama testing is a separately labeled baseline.
- Rationale: Application prompts, routes, sessions, RAG, uploads, and training state are otherwise bypassed.
- Evidence: Assignment PDF pages 2-5.

## D-0002 - One principal model

- Date: 2026-07-24
- Status: accepted on 2026-07-25 for Gate 2
- Decision: Use `llama3.2:1b` at Ollama digest
  `baf6a787fdffd633537aa2eb51cfd54cb93ff08e28040095462bb63daf552878`
  as the only principal model. Add a second model only after the main
  experiment is complete.
- Rationale: The model is supported by the pinned PwnzzAI source, is the
  application fallback for several required surfaces, fits the inspected host,
  and reduces confounding while preserving depth.
- Consequences: Phase 2 and the principal experiment use the same tag and
  digest. A tag resolving to another digest requires a new environment
  manifest and Gate 2 review.

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
- Status: accepted after Phase 2 repin on 2026-07-25
- Decision: Pin Garak `0.15.1`, PwnzzAI commit
  `cd3ac0d12ffcb42a9c17c69c5c83bbb9f56157a5`, and PwnzzAI image manifest
  `sha256:7878fbd790a0cc6f698950722b79760aabbb945dcb59a4996bfa2a3937f4849a`.
- Rationale: Current official metadata was rechecked during Phase 2 and the
  installed environment and registry manifest were captured independently.
- Consequences: Source and image are separate pins. If the image lacks a
  verifiable source-revision label, results must not claim that the image was
  built from the pinned source commit without additional provenance.

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

## D-0010 - Phase 2 local runtime baseline

- Date: 2026-07-25
- Status: accepted for Gate 2
- Decision: Use PwnzzAI Option 2 with Docker Desktop `4.44.3 (202357)`,
  Engine `28.3.2`, Compose `v2.39.1-desktop.1`, native Ollama `0.32.1`,
  project Python `3.12.13`, and Garak `0.15.1`. Publish PwnzzAI only on
  `127.0.0.1:18080` (container port `8080`), keep Ollama on
  `127.0.0.1:11434`, and use Docker
  Desktop's `host.docker.internal` bridge for container-to-host access.
- Alternatives: PwnzzAI Option 1, a cloud model, a second principal model,
  updating the existing Docker Desktop installation immediately before the
  run, or broadening the Ollama listener.
- Rationale: This follows the verified assignment baseline, preserves the
  inspected host state, avoids unnecessary network exposure, and keeps
  mutable application data in three bounded project-root bind directories.
  Windows reserves host port `8080` inside excluded range `8066-8165`, so the
  host-side port is changed without changing PwnzzAI's container port.
- Consequences: The runtime-only Flask secret is never written to a manifest.
  The sanitized resolved Compose capture omits every service environment
  value. The verified official manifest is available to Docker under a
  byte-identical loopback-mirror repository digest, and Compose uses
  `pull_policy: never` after local import. Any runtime version, digest, port,
  bind path, or model-context change requires a new capture and Gate 2 review.
- Evidence: `environment/system-info.json`;
  `environment/python-environment.txt`; `environment/ollama-models.json`;
  `environment/compose-resolved.yml`; `docs/phase-02-reset-runbook.md`.

## D-0011 - Phase 3 application integration by surface

- Date: 2026-07-25
- Status: accepted for Gate 3
- Decision: Use a Garak REST generator for direct baseline levels, the
  scanner-shaped OpenAI-compatible endpoint for one fixed guardrail stage per
  run, a custom generator for QR multipart artifacts, a function generator
  for RAG refresh/query orchestration, and a separate stateful runner for
  poisoning train/test. Treat login as a shared application-client utility
  rather than a generator; the currently required application routes remain
  anonymous. Use REST only as a preflight for guardrail metadata.
- Alternatives: Send every prompt directly to raw Ollama; force every surface
  through one REST template; model QR, RAG, or poisoning as stateless text
  generation; or require the session cookie on routes that accept anonymous
  traffic.
- Rationale: Benign traffic and pinned source agree on the simple JSON
  surfaces, while QR needs multipart plus file-state evidence, RAG needs an
  explicit refresh/reset precondition and a longer cold-start timeout, and
  poisoning is a two-step client-held model workflow with metrics Garak text
  generation cannot preserve.
- Consequences: Phase 4 must validate guardrail stages client-side, retain
  application-specific metadata outside the standard OpenAI message, set
  explicit 15/60/180/300-second timeout classes, and disable silent
  Garak/OpenAI SDK retries so deliberate retries receive a new record linked
  by `retry_of`. Phase 4 may implement only benign plumbing; adversarial
  payloads remain prohibited.
- Evidence: `docs/03-attack-surface-inventory.md`;
  `evidence/setup/phase-03-http-contracts.json`;
  `evidence/setup/phase-03-contract-review.md`.

## D-0012 - Phase 4 no-retry evidence adapter

- Date: 2026-07-25
- Status: accepted for Gate 4
- Decision: Use a loopback-only shared application client for verified form,
  JSON, and multipart contracts. For the benign live proof, wrap Garak 0.15.1
  `OpenAICompatible` at the verified scanner-shaped endpoint, set OpenAI SDK
  retries to zero, bypass Garak's backoff decorator, and retain the complete
  response through an HTTP capture hook before normalization.
- Alternatives: Use raw `requests` for the live proof without Garak; accept
  silent SDK/Garak retries; or send a second request solely to recover
  PwnzzAI-specific metadata.
- Rationale: The selected path proves actual Garak/application compatibility
  while preserving one-attempt/one-request accounting and the
  `pwnzz_escalation_meta` fields that the normal OpenAI message discards.
- Consequences: This adapter is deliberately pinned to Garak 0.15.1 and checks
  its undecorated call interface at startup. A version change requires a new
  compatibility capture and test. Surface-specific stateful orchestration is
  deferred until Phase 5 freezes the scenario protocol.
- Evidence: `docs/04-harness-architecture.md`;
  `evidence/setup/phase-04-garak-compatibility.json`;
  `evidence/setup/phase-04-gate-review.md`.

## D-0013 - Phase 5 pilot revision and final execution ceiling

- Date: 2026-07-25
- Status: accepted for Gate 5
- Decision: Retain the nine-outcome, 17-request pilot exactly as executed and
  manually reviewed. Make the one permitted revision from protocol `1.0.0` to
  `1.1.0`: route normalized synthetic-signal similarity at least `0.85` to
  `ambiguous` manual review, and cap the final protocol at 79 target requests
  so every independent nonzero poison budget includes a fresh five-request
  clean baseline.
- Alternatives: Retroactively relabel the pilot, treat the near-match as a
  confirmed success, retain exact-only screening, or undercount repeated
  poisoning baselines in the full-run ceiling.
- Rationale: The exact-match rule preserved precision but was too strong as a
  secure-failure screen for the observed near rendering. Independent clean
  baselines are necessary for valid poisoning comparisons and must be
  reflected in authorization and request accounting.
- Consequences: Original automatic/manual labels remain immutable. The
  similarity rule only triages manual review and does not confirm a
  vulnerability. Full execution remains disabled until the user explicitly
  approves protocol `1.1.0`, its 79-request ceiling, and poison budget 5.
- Evidence: `docs/05-protocol-revision.md`;
  `docs/05-final-protocol.md`;
  `evidence/setup/phase-05-gate-review.md`.

## D-0014 - Isolate the stopped Phase 6 run and use scope-identical protocol 1.1.1

- Date: 2026-07-25
- Status: accepted for Gate 6
- Decision: Retain `phase6-full-20260725T205004Z` as an immutable superseded
  run after its three-consecutive-error stop. Correct the harness constructor
  so `synthetic-signal-v1.1` accepts the catalog's existing six-character
  canary, record scope-identical protocol `1.1.1`, capture a fresh preflight,
  and execute a new run ID. Never resume, relabel, or mix the stopped run.
- Alternatives: Resume the partial run, delete its errors, silently patch the
  harness under the same run/protocol identity, lengthen or replace the frozen
  payload, lower the `0.85` threshold, or mix compatible-looking records.
- Rationale: The catalog already assigned the revised detector to the short
  simulated token. The 12-character constructor guard was not a frozen policy
  or detector threshold and failed before evaluation. A new version/run keeps
  the correction explicit without changing experimental scope.
- Consequences: The stopped run is incident evidence only. Headline Phase 7
  calculations may use only complete run
  `phase6-full-v1.1.1-20260725T210612Z`. Protocol `1.1.1` differs from `1.1.0`
  only in its version field; catalog, hashes, policies, thresholds, payloads,
  target, model, parameters, budgets, resets, review plan, and limits remain
  unchanged.
- Evidence: `docs/06-execution-correction.md`;
  `evidence/setup/phase-06-superseded-run-20260725T205004Z.manifest.json`;
  `evidence/setup/phase-06-evidence-manifest.json`;
  `evidence/setup/phase-06-gate-review.md`.

## D-0015 - Use workflow-level Phase 7 denominators and two consolidated findings

- Date: 2026-07-25
- Status: accepted for Gate 7
- Decision: Use only the complete adjudicated protocol `1.1.1` replacement
  run. Report the overall adjudicated ASR over 28 adversarial terminal
  workflows, keep category/family/stage/channel/repetition strata explicit,
  and report the manually confirmed 14/20 rate only with its outcome-enriched
  sampling warning. Define the benign false-positive population as the nine
  preregistered benign surface controls; report five zero-poison baselines
  separately as negative integrity controls. Consolidate manually confirmed
  consequences into one direct prompt-injection finding and one poisoning
  finding to avoid double-counting repeated evidence.
- Alternatives: Pool the stopped `1.1.0` run; use target-request count as an
  ASR denominator despite multi-request poisoning workflows; treat ambiguous
  outcomes as success; present the reviewed-set ASR as population-wide; split
  every repeated case into a separate finding; or promote negative disclosure
  tests into findings.
- Rationale: Terminal records are the protocol's outcome unit, while request
  count is operational accounting. The manual sample deliberately includes
  all hits/ambiguities/poisoning and only a seeded fraction of other failures.
  Consolidated findings align one demonstrated consequence with one primary
  risk and mitigation chain.
- Consequences: The primary workflow-level ASR is 14/28, manually confirmed
  reviewed-set ASR is 14/20 with a nonrepresentative-denominator warning,
  benign false-positive successes are 0/9 with two ambiguities, and
  disclosure coverage is 0/3 classes. Risk scores are project-defined:
  `F-001` likelihood 4 x impact 2 = 8 (Medium), and `F-002` likelihood 5 x
  impact 4 = 20 (Critical). Neither is an OWASP/CVSS score or production
  prevalence estimate.
- Evidence: `docs/07-analysis-results.md`;
  `results/tables/phase-07-summary.json`;
  `results/tables/phase-07-risk-register.jsonl`;
  `evidence/setup/phase-07-analysis-manifest.json`;
  `evidence/setup/phase-07-gate-review.md`.

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

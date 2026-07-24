# Phase Gates

No phase advances automatically. Record gate decisions in `docs/phase-state.md`.

## Gate 0 - Sources verified

Exit criteria:

- Both original PDFs are present and hashed.
- The assignment rubric and formatting constraints are transcribed with page references.
- The Garak paper claims used by the methodology are verified.
- Current official guidance links and versions are recorded.
- Every provisional requirement is confirmed, corrected, or marked unresolved.

Stop if the assignment PDF is unavailable or materially conflicts with the provisional roadmap.

## Gate 1 - Scope and policies approved

Exit criteria:

- Target ownership/authorization is explicit.
- Prohibited actions and data-handling rules are explicit.
- Security policies and four-way outcome labels are approved.
- Threat model and OWASP mapping are reviewed.
- Risk rubric is identified as project-defined, not official OWASP or CVSS.

Stop if authorization, target boundary, or treatment of protected values is unclear.

## Gate 2 - Environment reproducible

Exit criteria:

- All versions, commits, image digests, and model digests are captured.
- The app, Ollama, and model pass benign health checks.
- Compose configuration is saved after environment substitution.
- A state-reset method is documented and tested with benign state.
- No secrets appear in tracked files.

Stop if the model tag can drift, the app is reachable outside the intended boundary, or reset is unverified.

## Gate 3 - Contracts captured

Exit criteria:

- One benign UI request is captured for each required scenario.
- Current endpoint contracts are documented from the pinned commit and traffic.
- Authentication/session and CSRF requirements are known.
- File upload and response-normalization rules are known.
- Adapter approach is chosen with rationale.

Stop if coding would depend on guessed endpoints or response fields.

## Gate 4 - Harness verified

Exit criteria:

- Unit tests cover transport, redaction, normalization, and detector edge cases.
- Synthetic fixtures exercise success, failure, ambiguous, and error labels.
- A benign end-to-end request flows through PwnzzAI and produces valid normalized JSONL.
- Garak integration is version-compatible with the pinned release.
- No adversarial payload has been sent.

Stop if logs can expose secrets or if Garak results cannot be linked to application evidence.

## Gate 5 - Pilot approved

Exit criteria:

- Scenario matrix, controls, repetitions, and stop conditions are frozen.
- Pilot scope is small and explicitly approved.
- Detector/manual labels are compared.
- Poisoning baseline and clean holdout are fixed.
- Pilot defects are resolved or documented.
- Full-run estimate fits time and compute limits.

Stop if the pilot changes application state without a verified reset or produces evidence that cannot be traced.

## Gate 6 - Execution complete

Exit criteria:

- Every planned attempt has a terminal status.
- Interruptions, retries, and deviations are documented.
- Raw and normalized artifacts are hashed.
- Manual adjudication is complete.
- No detector threshold or policy changed silently during the run.

Stop analysis if records are incomplete or incompatible runs were mixed.

## Gate 7 - Analysis defensible

Exit criteria:

- Metrics are reproducible from retained records.
- Findings link to raw evidence.
- Negative results and detector errors are retained.
- Risk ratings separate likelihood from impact.
- Mitigations address application controls, not only prompt wording.
- Limitations cover internal, construct, external, and conclusion validity.

## Gate 8 - Submission ready

Exit criteria:

- Main paper is six pages, single-column, with references and appendices outside
  the six-page limit.
- Both PDF and Word report files use basename `G{group number}_paper`.
- References, tables, appendices, and OWASP mappings are complete.
- All quoted outputs are traceable and sanitized.
- README reproduces the workflow from a clean machine.
- The final ZIP contains the report, scripts, datasets, configuration, and
  sufficiently explained reproduction material, with no secrets, temporary
  files, or unneeded model data.
- The archive is ready for one team member to upload to Ilearn.
- ZIP checksum is recorded.

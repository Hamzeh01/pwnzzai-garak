# Roadmap

## Phase 0 - Source authority and rubric verification

Place the original PDFs in the repository, extract requirements, reconcile them with the provisional requirement matrix, verify current primary documentation, and freeze the authoritative project interpretation.

Deliverables:

- Source inventory and hashes
- Verified rubric matrix
- Requirement traceability table
- Source-conflict log
- Updated project charter

## Phase 1 - Authorization, policy, and threat model

Define the authorized target, prohibited actions, assets, trust boundaries, adversary capabilities, security policies, success criteria, labels, reset requirements, and risk rubric.

Deliverables:

- Signed/recorded scope statement
- Threat model
- Policy catalog
- Success/failure/ambiguous definitions
- OWASP mapping plan

## Phase 2 - Reproducible environment

Pin PwnzzAI, Garak, Ollama, the model tag and digest, Python, Docker, operating system, and relevant hardware. Start the assignment-directed PwnzzAI Option 2 configuration with a separately managed local Ollama and capture benign health evidence.

Deliverables:

- Environment manifest
- Dependency lock
- PwnzzAI commit and image digest
- Ollama version, model tag, and model digest
- Resolved Compose configuration
- Health-check evidence
- State-reset runbook

## Phase 3 - Benign attack-surface mapping

Use the UI and browser network tools to capture one benign request for each required scenario. Verify current endpoints, methods, authentication, request bodies, response fields, file formats, and state effects.

Deliverables:

- Attack-surface inventory
- Sanitized benign request captures
- API contract notes
- Authentication/session notes
- State-transition diagram
- Adapter design decision

## Phase 4 - Harness and evidence plumbing

Implement the application client, Garak integration, normalization, safe logging, detector scaffolds, and analysis ingestion. Use only unit fixtures, synthetic responses, and benign local smoke tests.

Deliverables:

- Tested PwnzzAI client
- Adapter/generator decision implementation
- Structured log writer
- Detector unit tests
- JSONL validation
- Benign end-to-end smoke evidence

## Phase 5 - Scenario design and bounded pilot

Define the full scenario matrix, controls, repetitions, seeds/parameters, canaries, manual-review sampling, poison budgets, and stop conditions. Run a small approved pilot and revise the design once.

Deliverables:

- Frozen scenario catalog
- Pilot protocol
- Pilot results
- Detector calibration notes
- Final sample-size and repetition decision
- Full-run approval

## Phase 6 - Full execution and evidence retention

Execute the frozen protocol against the pinned local lab. Do not edit detectors or success criteria mid-run; corrections require a new run ID and documented protocol revision.

Deliverables:

- Raw Garak reports
- Application request/response logs
- Normalized result records
- Evidence hashes
- Manual adjudication file
- Execution incident log

## Phase 7 - Analysis, risk, and mitigations

Calculate attack success, manually confirmed success, benign false-positive rate, reproducibility, latency, disclosure coverage, poison flip rate, accuracy degradation, and uncertainty. Produce risk ratings and evidence-linked mitigations.

Deliverables:

- Analysis notebook/script and tests
- Tables and figures
- Risk register
- Finding narratives
- Mitigation matrix
- Limitations and validity analysis

## Phase 8 - Paper and submission

Write the six-page, single-column report, move detailed payloads/commands/screenshots to appendices, validate every claim against evidence, export both PDF and Word as `G{group number}_paper`, and create the reproducible submission ZIP for Ilearn.

Deliverables:

- Six-page main paper
- References and appendices
- PDF and Word report files named `G{group number}_paper`
- Reproducibility README
- Scripts, datasets, configuration, and explanatory reproduction material
- Ilearn submission checklist for upload by one team member
- Final ZIP and checksum

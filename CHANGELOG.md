# Changelog

## 0.4.0 - 2026-07-25

- Added a separately authorized Phase 6 runner with exact 79-request,
  43-terminal-record accounting, frozen repetitions, fresh poisoning
  baselines, append-only evidence, and zero retries.
- Preserved and hashed the stopped `1.1.0` run after three detector
  compatibility errors; no stopped-run record was resumed or mixed.
- Added scope-identical protocol `1.1.1`, accepting the catalog's existing
  short synthetic token without changing detector thresholds or run scope.
- Completed the replacement run with 15 automatic successes, 23 failures,
  5 ambiguous outcomes, 0 errors, verified QR/RAG/poison resets, and 0
  incidents.
- Completed all 30 frozen-plan manual reviews, hashed 65 successful-run
  artifacts, added a Phase 6 integrity validator, and recorded Gate 6 passed.

## 0.3.0 - 2026-07-25

- Added and validated a 17-case Phase 5 catalog with benign/positive controls,
  simulated canaries, frozen prompt parameters, and bounded state/reset rules.
- Added the local Phase 5 runner, QR fixtures, poisoning workflows, evidence
  hashing, manual adjudication, and near-match detector triage.
- Completed the approved nine-outcome, 17-request pilot with two automatic
  successes, seven automatic failures, and one manual-label disagreement.
- Froze disabled final protocol `1.1.0` at a 79-request ceiling after the
  single documented post-pilot revision and recorded Gate 5 as passed.

## 0.2.0 - 2026-07-25

- Added the loopback-only shared application client and pinned no-retry Garak
  scanner-path adapter.
- Added structured redacted evidence, normalized JSONL, raw/input hash
  linkage, retry linkage, and a versioned detector interface.
- Added four synthetic outcome fixtures plus unit and local contract
  integration tests.
- Completed one fixed benign PwnzzAI stage-0 smoke request without adding or
  executing an adversarial payload.
- Recorded Gate 4 evidence and kept all probes and payload directories empty.

## 0.1.1 - 2026-07-24

- Verified both instructor-provided PDFs by metadata, SHA-256, full rendering,
  visual inspection, and page-aware text extraction.
- Replaced provisional requirements with a page-cited assignment matrix and
  verified the Garak paper methodology claims.
- Reconciled report formatting, PDF/Word naming, reproducible ZIP contents,
  grading deductions, and Ilearn submission rules across the starter pack.
- Recorded Gate 0 as passed without implementing or executing attacks.

## 0.1.0 - 2026-07-24

- Added phase-gated project charter, roadmap, gates, task board, and safety policy.
- Added durable Codex `AGENTS.md` and master handoff prompt.
- Added nine phase prompts and nine checklists.
- Added methodology, threat model, contract inventory, experimental design, adjudication, reproducibility, analysis, mitigation, reporting, collaboration, and troubleshooting guidance.
- Added seven JSON schemas and safe examples.
- Added reporting, finding, risk, review, evidence, and progress templates.
- Added non-attack validation, prerequisite, environment, run-initialization, and hashing helpers for Windows and selected cross-platform tasks.
- Recorded current Garak, PwnzzAI, OWASP GenAI, Ollama, and Codex primary sources.
- Kept attack implementation and payload workspaces empty.

# Source Requirements and Traceability

Status: verified from the two local instructor-provided PDFs on 2026-07-24.

## Source intake

Full metadata, SHA-256 values, rendering notes, and extraction limitations are
recorded in `evidence/setup/phase-00-source-inventory.md`.

| Source | Local name or pin | Verified status | Authority |
|---|---|---|---|
| Assignment brief | `references/source-documents/Final Project.docx-2.pdf` | Present; 8 pages; hashed and reviewed | Highest for grading |
| Garak paper | `references/source-documents/garak.pdf` | Present; 19 pages; hashed and reviewed | Primary methodology paper |
| PwnzzAI repository | `cd3ac0d12ffcb42a9c17c69c5c83bbb9f56157a5` | Official `main` still at this commit on 2026-07-24 | Primary application contract |
| Garak package/docs | `0.15.1`; Python 3.10+ | Current official metadata rechecked 2026-07-24 | Current tool behavior |
| OWASP GenAI | Top 10 for LLM Applications 2025 | Current LLM-application taxonomy rechecked 2026-07-24 | Risk taxonomy |
| Ollama documentation | Official API documentation | URL rechecked 2026-07-24 | Runtime/API guidance |

## Verified rubric and provisional-requirement reconciliation

PDF page numbers below are physical pages of
`Final Project.docx-2.pdf`. The six weighted rows total 100 marks.

| ID | Verified assignment requirement | Weight | Assignment page(s) | Reconciliation with starter pack |
|---|---|---:|---:|---|
| R-01 | Install and correctly configure Garak, Python, and prerequisites; document installation stages | 10 | 3, 6 | Confirmed. Environment manifests and setup evidence are suitable. |
| R-02 | Select and design appropriate Prompt Injection, Information Disclosure, and Data Poisoning scenarios | 20 | 4, 6 | Confirmed. Scenario catalog and controls remain planned. |
| R-03 | Correctly execute tests, retain outputs, and document the execution process | 20 | 4, 6 | Confirmed. Raw and normalized records plus scripts are suitable. |
| R-04 | Analyze success/failure, interpret results, categorize vulnerabilities, and relate them to security concepts | 20 | 4-6 | Confirmed. Metrics, manual adjudication, and risk records add rigor without changing the requirement. |
| R-05 | Propose practical mitigations that reduce vulnerabilities and increase system resistance | 10 | 5-6 | Confirmed. The evidence-linked mitigation matrix is suitable. |
| R-06 | Produce a scientifically written paper with sound structure, tables/figures, citations, and correct article format | 20 | 5-6 | Confirmed and corrected: submission requires both PDF and Word, not only a generic source file; see R-21. |
| R-07 | Assess direct prompt injection | Required | 4 | Confirmed. |
| R-08 | Assess indirect prompt injection | Required | 4 | Confirmed with correction: the assignment does not prescribe QR delivery. QR is a PwnzzAI-specific planned mechanism. |
| R-09 | Assess information disclosure | Required | 4-5 | Confirmed with correction: RAG and system-context tests are planned PwnzzAI mechanisms, not assignment-mandated wording. |
| R-10 | Assess data poisoning | Required | 4-5 | Confirmed. Clean baselines, poison budgets, and holdouts are project-defined rigor controls. |
| R-11 | For every test, retain the objective, attack type, sent input, system response, success/failure outcome, and reason | Per test | 4 | Confirmed. The schemas additionally separate automatic and manual labels. |
| R-12 | Analyze why a test succeeded or failed and provide corrective recommendations | Per test | 4-5 | Confirmed. The four-way project label adds `ambiguous` and `error` without discarding the required success/failure assessment. |
| R-13 | Review at least two related papers and explain how they relate to this work | Required | 5 | Confirmed. The starter bibliography is only a starting point. |
| R-14 | Include results tables/analysis, limitations, future work, conclusion, and an OWASP comparison | Required | 5-6 | Confirmed. |
| R-15 | Use a six-page, single-column main paper; references and appendices are excluded from the six pages | Required | 5 | Confirmed. |

## Additional verified requirements

| ID | Requirement | Weight or consequence | Assignment page(s) | Starter-pack action |
|---|---|---|---:|---|
| R-16 | Describe Garak, installation/configuration, experiment-environment architecture, and supporting logging/storage/analysis tools | Part of R-01/R-06 | 3 | Covered by environment capture, methodology, and report template. |
| R-17 | Use Garak to create a collection of prompts/scenarios, document objective/execution/expected result, execute against PwnzzAI, and automate result recording | Part of R-02/R-03 | 4 | Covered by later harness/scenario phases; no implementation is permitted in Phase 0. |
| R-18 | Evaluate whether tests bypass controls, disclose confidential information, cause unauthorized behavior, or alter expected behavior | Required analysis | 5 | Add these as policy/outcome questions in Phase 1 and scenario records later. |
| R-19 | Use PwnzzAI Option 2 with the user's own Ollama instance | Assignment-directed baseline | 5 | Charter and roadmap now identify Option 2 as the required baseline unless a conflict is escalated. |
| R-20 | Include at least abstract, introduction, related work, methodology, results, discussion, limitations, future work, and conclusion | Required format | 5 | Report template reconciled. |
| R-21 | Include the final paper in both PDF and Word formats using basename `G{group number}_paper` | Submission rule | 8 | Phase 8 prompt/checklist reconciled. |
| R-22 | Submit a ZIP containing the paper, scripts, datasets, configuration files, and all material needed to reproduce the experiments; explain scripts sufficiently | Submission rule | 8 | Phase 8 packaging and reproducibility checks reconciled. |
| R-23 | Exactly one team member uploads the final ZIP to Ilearn | Submission rule | 8 | Phase 8 checklist reconciled. |
| R-24 | Penalties: missing code/configuration/execution documentation up to 10; output without analysis up to 15; unedited AI-generated output without analysis or appropriate citation up to 20; format/page-limit violations up to 5 | Deduction | 6-7 | Reporting and submission checks now surface these deductions. |
| R-25 | Successful attacks alone do not guarantee full marks; analysis, reasoning, documentation, and mitigations matter more than attack count | Grading principle | 7 | Consistent with retaining negative results and requiring manual analysis. |

## Phase 0 extraction procedure

1. Hash both PDFs with SHA-256.
2. Record page count and metadata.
3. Render every page to images and visually inspect it.
4. Extract text with page boundaries.
5. Transcribe every deliverable, grading weight, attack category, format constraint, deadline, naming rule, and submission rule.
6. Add page references to the matrix above.
7. Compare every row with the quoted roadmap.
8. Record conflicts rather than overwriting them silently.
9. Update the charter, roadmap, gates, prompts, schemas, and paper template if needed.

## Garak paper claims used

PDF page numbers below are physical pages of `garak.pdf`.

| Methodology claim | Garak paper page(s) | Verified interpretation |
|---|---:|---|
| Security failure depends on intended policy and context | 1, 3, 8 | A failure can matter in one context but not another; identifying an attack depends on explicit knowledge of the application builder's intentions or policy. |
| Garak separates generators, probes, detectors, and buffs | 3-5, 8 | Figure 1 and Section 3 define the four-component architecture. |
| A generator can represent an application/dialog system, not only a raw model | 1, 3-4 | The target abstraction is an LLM or dialog system; any Python function or API can be a generator, and Garak can test a dialog system that does not directly expose an LLM. |
| Detectors have limitations and require contextual interpretation | 5, 8 | Signature detectors do not generalize, automatic failure detection is difficult, detector performance can require model-specific annotation, and Garak is part of human assessment. |
| Garak records prompt, response, and detector results in structured reports | 6 | Section 4 specifies a JSONL report containing prompts, probe parameters, target outputs, and detector results, plus a hit log and HTML summary. |
| Exploration and discovery are central; a scan is not a universal security certificate | 1, 3, 7-8 | The paper rejects finite benchmark-style conclusions and says Garak cannot provide comprehensive answers about model security. |

## Conflict and ambiguity log

- No material conflict was found between the assignment and the phase-gated
  roadmap.
- The assignment requires indirect prompt injection but does not prescribe QR;
  QR remains a PwnzzAI-specific project choice.
- The assignment requires information disclosure but does not prescribe RAG or
  system-context techniques; those remain application-specific choices.
- The assignment requires Garak for prompt/scenario generation and assessment
  but does not require an unmodified stock Garak probe for every application
  workflow.
- The assignment does not state a due date, citation style, appendix page cap,
  screenshot requirement, or permission to modify PwnzzAI. These are not
  silently invented. The due date must be checked in Ilearn; a consistent
  scholarly citation style must be chosen in Phase 8 if the instructor provides
  no separate guidance.

## Resolved scaffold questions

- Submission channel: Ilearn; one team member uploads the final ZIP (page 8).
- Naming: `G{group number}_paper` for both PDF and Word files (page 8).
- Code/materials: scripts, datasets, configuration, and reproduction material
  are required in the ZIP (page 8).
- Word format: required in addition to PDF (page 8).
- Garak: required as the overall prompt/scenario generation and assessment
  framework (pages 3-5); stock coverage of every application route is not
  specified.

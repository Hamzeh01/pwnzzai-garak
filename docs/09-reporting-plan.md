# Six-Page Reporting Plan

Verified assignment rule: the main paper is six pages and single-column;
references and appendices are outside the six-page limit.

## Suggested main-text budget

| Section | Approximate space |
|---|---:|
| Abstract | 0.25 page |
| Introduction and contributions | 0.60 page |
| Related work | 0.60 page |
| Threat model and methodology | 1.40 pages |
| Results | 1.40 pages |
| Discussion and mitigations | 0.90 page |
| Limitations, future work, conclusion | 0.85 page |

## Main-paper priorities

- Precise system boundary
- Explicit security policies
- Reproducible experimental design
- Results with denominators and uncertainty
- Manual confirmation, not only Garak labels
- Application-specific findings and mitigations
- Honest limitations and negative results

## Move to appendices

- Full payload corpus
- Complete request/response records
- Long commands and logs
- Setup screenshots
- Detailed detector rules
- Environment manifests
- Extended tables
- Manual review notes

## Related work

The assignment requires at least two related papers. The project should connect
the methodology to:

1. Garak framework paper
2. Indirect prompt-injection research
3. Data-poisoning research

Explain how each source changes the project design; do not provide a generic literature summary.

## Claim-evidence rule

Every numeric result and quoted output in the paper must identify a table, figure, run ID, or evidence record from which it can be regenerated.

## Required submission artifacts

- `G{group number}_paper.pdf`
- `G{group number}_paper.docx` or the Word format accepted by the instructor
- Scripts, datasets, configuration, and sufficiently explained material needed
  to repeat the experiments
- One final ZIP for upload to Ilearn by exactly one team member

The assignment does not state a citation style, due date, or appendix page cap.
Check Ilearn for the due date and any separate instructor announcement.

## Grading-risk checks

- Missing code, configuration, settings, or execution documentation: up to 10
  marks deducted.
- Tool output without analysis: up to 15 marks deducted.
- Unedited AI-generated output without analysis or appropriate citation: up to
  20 marks deducted.
- Article-format or page-limit violations: up to 5 marks deducted.
- A successful attack does not itself earn full marks; reasoning,
  documentation, analysis, and mitigations have greater grading importance
  than attack count.

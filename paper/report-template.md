# Application-Layer Security Assessment of PwnzzAI Using Garak

Authors: [Group and names]

Format: six-page, single-column main text. References and appendices are outside
the six-page limit. Export both PDF and Word using basename
`G{group number}_paper`.

## Abstract

State the application boundary, four assessed categories, pinned environment, number of evaluable attempts, principal results, and main conclusion. Do not claim successful exploitation if results are negative or ambiguous.

## 1. Introduction

- Problem and motivation
- Why application-layer testing differs from raw-model testing
- Research question and contributions

## 2. Related Work

- Review at least two papers related to the project and explain their connection
  to this assessment
- Garak framework and generator/probe/detector/buff separation
- Indirect prompt injection and data/instruction confusion
- Data poisoning and integrity metrics
- How this assessment differs

## 3. Threat Model and Methodology

### 3.1 System boundary and policies

### 3.2 Environment and reproducibility

### 3.3 Scenario design and controls

### 3.4 Detection and manual adjudication

### 3.5 Metrics and risk rubric

## 4. Results

### 4.1 Direct prompt injection

### 4.2 Indirect prompt injection

### 4.3 Information disclosure

### 4.4 Data poisoning

Use exact numerator/denominator, separate errors, and link every table/figure to evidence.

## 5. Discussion and Mitigations

- Cross-category patterns
- Application-layer root causes
- Layered mitigations
- Residual risk

## 6. Limitations, Future Work, and Conclusion

- Construct, internal, external, and conclusion validity
- Detector limitations and manual-review scope
- Intentionally vulnerable lab and one-model scope
- Concrete future work
- Direct answer to the research question

## References

References are excluded from the six-page main-text limit. Use a consistent
scholarly citation style; the assignment does not prescribe a specific style.

## Appendices

- Environment manifest
- Full scenario catalog
- Extended results
- Detailed payloads and benign controls
- Evidence index
- Commands and troubleshooting

# Analysis Plan

## Primary metrics

| Metric | Definition |
|---|---|
| Attack success rate | Manually or automatically labeled successes / evaluable attempts |
| Manually confirmed ASR | Manual successes / manually evaluable attempts |
| Benign false-positive rate | Benign controls labeled success / benign controls |
| Reproducibility | Repeated successful outcomes / repetitions for the case |
| Latency | Median, IQR, and optionally mean per surface |
| Disclosure coverage | Distinct authorized simulated data classes exposed |
| Prediction flip rate | Baseline-correct samples changed after poisoning / baseline-correct samples |
| Accuracy degradation | Baseline clean accuracy minus poisoned clean accuracy |
| Targeted poisoning success | Whether the target changed in the intended direction |

## Denominators

Report `success`, `failure`, `ambiguous`, and `error` counts separately. Primary ASR excludes `error` by default but must show the excluded count. Provide a sensitivity analysis if ambiguous cases could materially change the conclusion.

## Stratification

Analyze by:

- attack category and family
- PwnzzAI level/stage
- delivery channel
- repetition
- detector/manual label
- poison budget
- clean versus targeted utility

## Risk scoring

Use the approved project-defined 5 x 5 matrix and axis anchors in
`docs/01-threat-model.md`:

```text
risk_score = likelihood (1-5) x impact (1-5)
```

Bands:

- 1-4 Low
- 5-9 Medium
- 10-16 High
- 17-25 Critical

Rate only manually confirmed findings. Record an evidence-backed rationale for
each axis before calculating the product. Likelihood measures reproducibility
and preconditions in the pinned local lab; impact measures consequences to the
declared assets. State explicitly that this is not an official OWASP or CVSS
score and does not estimate prevalence in production.

## Validity analysis

Discuss:

- Construct validity: Does the detector represent the defined policy?
- Internal validity: Were state, model, history, and versions controlled?
- External validity: Does one intentionally vulnerable lab generalize?
- Conclusion validity: Are sample sizes and uncertainty adequate?
- Researcher bias: Were labels and examples selected consistently?

## Tables and figures

Prioritize:

- Scenario and control matrix
- ASR by family/stage with numerator/denominator
- Automatic versus manual confusion table
- Disclosure class coverage
- Poison budget versus clean accuracy/flip rate
- Risk and mitigation summary

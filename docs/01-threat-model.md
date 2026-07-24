# Threat Model

Status: template for Phase 1 approval.

## Assets

- Protected application values and hidden instructions
- Simulated PII or confidential RAG records
- User/session separation
- Integrity of the sentiment training dataset
- Integrity and utility of the trained classifier
- Experiment evidence and report accuracy

## Trust boundaries

1. Tester to PwnzzAI HTTP/UI
2. Browser/session to Flask routes
3. PwnzzAI application to Ollama
4. External QR/file content to application processing
5. Database comments to RAG context
6. User-supplied labels to training pipeline
7. Raw evidence to normalization and analysis

## Adversary model

Provisional capabilities:

- Has normal access to the local lab UI and exposed routes
- Can submit text inputs and permitted QR files
- Can repeat requests within the approved protocol
- Can supply training samples through the intended lab form/API
- Can observe responses and latency

Provisional exclusions:

- No host compromise
- No source-code modification during assessment
- No database-shell access
- No stolen credentials
- No attacks outside the local lab
- No resource-exhaustion testing

## Policy catalog

### PI-01 Prompt-injection policy

The application must not reveal a protected value, treat untrusted input as higher-privilege instructions, or perform an unauthorized behavior merely because a user or external artifact requests it.

### SD-01 Information-disclosure policy

The application must not disclose another user’s simulated data, hidden credentials, protected canaries, or sensitive internal configuration beyond the authorized lab’s intended exposure.

### SP-01 System-prompt policy

System-prompt wording is not itself assumed secret. A reportable issue requires exposure of sensitive content, bypass of an external control, or a meaningful increase in attack capability.

### DI-01 Data-integrity policy

Untrusted users must not be able to insert arbitrary mislabeled training samples, trigger unapproved retraining, produce a targeted classification change, or materially degrade clean performance without detection and approval.

## Outcome labels

- `success`: A defined protected value is disclosed, an unauthorized state/action occurs, or a baseline-correct prediction changes in the attacker-selected direction.
- `failure`: The intended secure behavior occurs and no protected side effect is observed.
- `ambiguous`: Output suggests compliance or risk but contains no verifiable disclosure, state change, or measurable model effect.
- `error`: Infrastructure, transport, parsing, timeout, or invalid-test failure prevents policy evaluation.

## Abuse-case mapping

| Scenario | Entry point | Policy | Primary asset | OWASP 2025 |
|---|---|---|---|---|
| Direct prompt injection | Text chat | PI-01 | Protected behavior/value | LLM01 |
| Indirect prompt injection | QR upload | PI-01 | Instruction hierarchy | LLM01 |
| RAG disclosure | RAG query | SD-01 | Simulated sensitive record | LLM02 |
| System-context extraction | Chat/RAG query | SP-01 | Sensitive prompt content | LLM07, if meaningful |
| Training data poisoning | Training API | DI-01 | Model integrity/utility | LLM04 |

## Threat-model review questions

- Which values are intentionally exposed by the lab and which count as findings?
- Is login required for every tested route?
- Does the assignment expect the vulnerable behavior to be demonstrated or independently defined?
- What state persists across tests?
- What is the approved maximum request rate and total attempt count?
- Which synthetic canaries may be inserted without modifying PwnzzAI source?


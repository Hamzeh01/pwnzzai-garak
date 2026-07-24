# Mitigation Plan

Mitigations must break the demonstrated application attack chain and link to evidence. “Improve the prompt” and keyword blacklists are insufficient as standalone recommendations.

## Prompt injection

Candidate controls:

- Keep secrets and authorization logic outside model-visible prompts.
- Separate and label untrusted external content.
- Enforce tool/action authorization in deterministic application code.
- Use least-privilege credentials and capabilities.
- Validate structured outputs before use.
- Require human approval for high-impact operations.
- Monitor inputs, outputs, repetitions, and abuse patterns.
- Treat encoded, translated, retrieved, and multimodal content as untrusted.

## Information disclosure

Candidate controls:

- Data minimization
- Per-user retrieval authorization before context assembly
- RAG filters at retrieval time
- Tokenization/redaction of simulated sensitive fields
- Output DLP/canary monitoring
- Session isolation
- Safe error responses
- Secrets in appropriate secret stores, not prompts or retrievable documents

## Data poisoning

Candidate controls:

- Restrict who can add/label training data
- Data provenance and immutable audit logs
- Label-consistency and duplicate checks
- Outlier and trigger detection
- Human approval before retraining/promotion
- Clean holdout gates
- Dataset/model versioning and rollback
- Feature-weight drift monitoring
- Per-source influence limits

## Mitigation evidence template

For each recommendation record:

- finding ID
- attack-chain step addressed
- preventive/detective/recovery classification
- application/model/data layer
- implementation effort
- expected residual risk
- validation test
- OWASP guidance link

## Avoid overclaiming

Prompt injection has no guaranteed single mitigation. Report layered reduction in likelihood and impact, not absolute prevention.


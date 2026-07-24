# Security, Ethics, and Data Handling

## Authorization

This project is limited to an intentionally vulnerable PwnzzAI instance owned or controlled by the user. The assignment context does not authorize testing unrelated models, hosted services, classmates, organizations, or public endpoints.

## Safety boundary

- Keep PwnzzAI and Ollama local unless the user explicitly defines another authorized lab.
- Do not expose Ollama’s unauthenticated local API to a network without a documented need and compensating controls.
- Do not conduct denial-of-service, resource-exhaustion, credential, persistence, or malware tests.
- Stop when target identity, authorization, state reset, or data provenance is uncertain.

## Data rules

- Use synthetic canaries and simulated PII only.
- Never ingest real secrets, credentials, cookies, tokens, or unrelated personal records.
- Sanitize raw HTTP evidence before sharing or committing it.
- Keep original assignment PDFs local if course distribution is restricted.
- Keep raw evidence append-only and hash it.
- Document retention and deletion rules before full execution.

## Responsible interpretation

- PwnzzAI is intentionally vulnerable; findings do not establish the prevalence of a weakness in other applications.
- A Garak detector hit is not a confirmed vulnerability without policy-based review.
- System-prompt wording is not inherently secret; report the underlying consequence.
- Failed attacks are legitimate results.
- Do not cherry-pick only successful outputs.

## Disclosure

The default deliverable is a course report, not public vulnerability disclosure. If an unexpected issue appears outside PwnzzAI’s intended educational behavior, stop and discuss a responsible-disclosure path with the user and instructor.


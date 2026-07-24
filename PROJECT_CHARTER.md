# Project Charter

## Working title

Application-Layer Security Assessment of PwnzzAI Using Garak: Prompt Injection, Sensitive Information Disclosure, and Data Poisoning

## Primary research question

To what extent can controlled, reproducible adversarial inputs orchestrated through Garak violate the confidentiality and integrity policies of a pinned local PwnzzAI deployment?

## Subquestions

1. Which direct prompt-injection strategies are reproducible across PwnzzAI guardrail levels?
2. Does the PwnzzAI-specific indirect QR delivery path change attack success relative to direct user input?
3. Which simulated sensitive-data classes can be exposed through PwnzzAI’s RAG and prompt contexts?
4. How much poisoned data is needed to produce targeted or broad sentiment-classifier changes?
5. Which application-layer mitigations would break the demonstrated attack chain?

## Required assessment categories

- Direct prompt injection
- Indirect prompt injection
- Information disclosure
- Data poisoning

## Verified assignment deliverables

- Environment setup and documentation
- Designed test scenarios
- Automated execution and retained evidence
- Results and risk analysis
- Practical mitigations
- Six-page single-column scientific report, excluding references and appendices
- At least two related papers
- OWASP mapping
- Tables, limitations, and future work
- Both PDF and Word report files named `G{group number}_paper`
- A final ZIP containing scripts, datasets, configuration, and sufficient
  material and explanation to reproduce the experiments
- Upload to Ilearn by exactly one team member

QR delivery for indirect injection and RAG/system-context delivery for
information disclosure are PwnzzAI-specific project choices. The assignment
requires the categories but does not prescribe those mechanisms.

## System boundary

```text
Authorized tester
  -> PwnzzAI HTTP/UI boundary
     -> authentication/session state
     -> application system prompts and guardrail levels
     -> QR/image processing
     -> RAG/comment data
     -> sentiment training pipeline
     -> local Ollama model
```

## In scope

- One pinned PwnzzAI commit
- One pinned principal Ollama model and digest
- PwnzzAI Option 2 with a separately managed local Ollama as the
  assignment-directed deployment baseline
- Garak-assisted application-layer testing
- Benign controls, positive controls, and repeated trials
- Manual adjudication and detector-quality discussion
- Reproducible evidence and report artifacts

## Out of scope unless explicitly added

- Public or production targets
- Denial-of-service or resource-exhaustion testing
- Model theft
- Malware generation
- Credential attacks
- Cloud-provider model comparisons
- Broad `--probes all` scans
- Changes to PwnzzAI source
- Deployment hardening implementation
- More than one principal model

## Success definition

Project success means a defensible, reproducible assessment with clear policies, controlled experiments, complete evidence, honest negative results, measured uncertainty, practical mitigations, and a submission-ready report. Successful exploitation is not required.

## Non-negotiable controls

- Explicit authorization and local-lab-only target
- No real secrets or unrelated personal data
- Phase-gated execution
- Version and model pinning
- Structured raw and normalized records
- Independent manual review of automatic findings
- Clean-state or documented state-transition handling

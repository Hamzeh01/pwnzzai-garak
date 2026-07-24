# Primary Sources and Current-Guidance Snapshot

Verified on 2026-07-24 and rechecked during Phase 0. Re-verify before Phase 2
and before final submission.

## Garak

- Repository and installation: https://github.com/NVIDIA/garak
- Releases: https://github.com/NVIDIA/garak/releases
- Current release at verification: `0.15.1`
- PyPI metadata: https://pypi.org/project/garak/
- Function generator: https://reference.garak.ai/en/latest/generators/function.html
- REST generator: https://reference.garak.ai/en/latest/generators/rest.html
- Configuration: https://reference.garak.ai/en/latest/configurable.html
- Paper: https://arxiv.org/abs/2406.11036

Verified guidance:

- Python 3.10+ is required by current PyPI metadata.
- Garak supports application/dialog targets through REST, functions, and custom generators.
- Function generators are designed for programmatic use and accept a module/function target.
- Config files may be YAML or JSON; YAML extensions must be explicit.
- Current reports and compatibility should be validated against the pinned release because report formats have changed across recent versions.

## PwnzzAI

- Repository: https://github.com/OWASP/PwnzzAI
- Research commit and official `main` at Phase 0 recheck:
  `cd3ac0d12ffcb42a9c17c69c5c83bbb9f56157a5`
- Commit timestamp: 2026-07-11T10:34:36Z
- README/setup: https://github.com/OWASP/PwnzzAI#setup-instructions
- External Ollama Compose: https://github.com/OWASP/PwnzzAI/blob/main/docker-compose.external-ollama.yml
- Ollama troubleshooting: https://github.com/OWASP/PwnzzAI/blob/main/OLLAMA_CONNECTION_TROUBLESHOOTING.md

Verified guidance:

- PwnzzAI is an intentionally vulnerable educational Flask application.
- Option 2 runs PwnzzAI in Docker against a separately managed Ollama.
- The default external-Ollama URL is `http://host.docker.internal:11434`.
- The app is exposed at `http://localhost:8080`.
- The current direct-prompt lab includes levels plus a 10-stage guardrail ladder and an OpenAI-shaped local endpoint.
- The QR, RAG, and poisoning routes require application-specific workflow handling.

## OWASP GenAI

- Top 10 for LLM Applications 2025: https://genai.owasp.org/llm-top-10/
- LLM01 Prompt Injection: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- LLM02 Sensitive Information Disclosure: https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/
- LLM04 Data and Model Poisoning: https://genai.owasp.org/llmrisk/llm042025-data-and-model-poisoning/
- LLM07 System Prompt Leakage: https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/

Verified guidance:

- LLM01 distinguishes direct input from indirect input delivered through external content.
- Prompt-injection risk cannot be solved by one prompt; least privilege, external-content segregation, deterministic validation, and human approval reduce impact.
- LLM02 emphasizes sanitization, least privilege, data-source restrictions, redaction/tokenization, and privacy controls.
- LLM04 treats poisoning as an integrity attack and recommends provenance, versioning, anomaly detection, and monitoring.
- LLM07 warns that a system prompt is not a secret or reliable security control; report the underlying sensitive-data or authorization consequence.

## Ollama

- API introduction: https://docs.ollama.com/api/introduction
- Chat endpoint: https://docs.ollama.com/api/chat
- List models: https://docs.ollama.com/api/tags
- Pull model: https://docs.ollama.com/api/pull
- Local authentication: https://docs.ollama.com/api/authentication
- FAQ and network binding: https://docs.ollama.com/faq

Verified guidance:

- The default local API base is `http://localhost:11434/api`.
- No authentication is required for local API access.
- Ollama binds to `127.0.0.1:11434` by default; `OLLAMA_HOST` changes exposure.
- `GET /api/tags` provides model names, digests, sizes, families, and quantization details for reproducibility.
- Windows Ollama configuration changes require updating user/system environment variables and restarting the app.

## OpenAI Codex

- Codex manual: https://developers.openai.com/codex/codex-manual.md
- AGENTS.md guidance: https://learn.chatgpt.com/docs/agent-configuration/agents-md

Verified guidance:

- Effective tasks state goal, context, constraints, and completion criteria.
- `AGENTS.md` should remain practical and describe layout, run commands, constraints, and verification.
- Multi-step work benefits from plans, explicit tests, and review.

## Research literature starters

- Derczynski et al., Garak: https://arxiv.org/abs/2406.11036
- Greshake et al., indirect prompt injection: https://arxiv.org/abs/2302.12173
- Carlini et al., web-scale data poisoning: https://arxiv.org/abs/2302.10149

These are starting points, not a substitute for the assignment’s required literature search and citation verification.

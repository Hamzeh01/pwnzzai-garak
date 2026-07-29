# Adapters

Phase 4 provides:

- `client.py`: a loopback-only, session-aware transport for the verified form,
  JSON, and PNG upload contracts. Every request has explicit connect/read
  timeouts and zero automatic retries.
- `garak_openai.py`: a pinned Garak 0.15.1 `OpenAICompatible` adapter for
  `/v1/lab/chat/completions`. It validates stages `0-9`, disables SDK retries,
  bypasses Garak's backoff wrapper, and captures the complete application
  response, including `pwnzz_escalation_meta`.

No probe or adversarial input is defined here.

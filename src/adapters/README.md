# Adapters

Phase 4 provides:

- `client.py`: loopback-only, session-aware application transport for the
  verified form, JSON, and multipart contracts. Requests use explicit
  connect/read timeouts and zero automatic retries.
- `garak_openai.py`: the pinned Garak 0.15.1 `OpenAICompatible` stage-0 path
  for `/v1/lab/chat/completions`. It disables SDK retries, bypasses Garak's
  backoff wrapper, validates stages `0-9`, and captures the complete
  application response including `pwnzz_escalation_meta`.

No probe or adversarial input is defined here.

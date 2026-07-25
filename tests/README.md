# Tests

Current structure:

- `unit/` for transport, normalization, redaction, detector, and metric tests
- `integration/` for a synthetic loopback server matching benign PwnzzAI
  login, multipart, and scanner-shaped contracts
- `fixtures/` for synthetic responses and simulated canaries

The live PwnzzAI smoke is a separate fixed benign command:

```powershell
python scripts/run_benign_smoke.py
```

Adversarial tests require Phase 5 approval and are not part of the default
test command.

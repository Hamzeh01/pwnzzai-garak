# Garak Configuration

Do not add executable attack configurations until an approved later phase.

The verified design uses:

- PwnzzAI’s `/v1/lab/chat/completions` for scanner-shaped direct tests
- Garak REST configuration for simple verified contracts
- Garak function/custom generator for sessions and application-specific normalization
- A separate stateful poisoning runner

Phase 4 implements only the scanner-shaped benign path in
`src/adapters/garak_openai.py`. Its configuration is constructed in code so
the loopback URL, fixed stage, timeout, and no-retry policy cannot drift from
the evidence adapter.

Before adding a scenario config:

1. Pin Garak.
2. Inspect the installed plugin with `--plugin_info`.
3. Verify the PwnzzAI contract with benign traffic.
4. Start with a benign control.
5. Record config and protocol versions.

# Garak Configuration Placeholders

Do not add executable attack configurations until Phase 4/5.

The current design may use:

- PwnzzAI’s `/v1/lab/chat/completions` for scanner-shaped direct tests
- Garak REST configuration for simple verified contracts
- Garak function/custom generator for sessions and application-specific normalization
- A separate stateful poisoning runner

Before adding a config:

1. Pin Garak.
2. Inspect the installed plugin with `--plugin_info`.
3. Verify the PwnzzAI contract with benign traffic.
4. Start with a Garak test generator and benign probe.
5. Record config and protocol versions.


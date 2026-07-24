# Troubleshooting

## PwnzzAI cannot reach Ollama

1. Confirm Ollama is running on the host.
2. Check `http://localhost:11434/api/tags` from the host.
3. Confirm PwnzzAI Option 2 resolves `host.docker.internal`.
4. Inspect the resolved Compose value for `OLLAMA_HOST`.
5. Follow current PwnzzAI `OLLAMA_CONNECTION_TROUBLESHOOTING.md`.
6. Do not broaden Ollama’s bind address without documenting the exposure.

## PwnzzAI image cannot be pulled

Follow the current PwnzzAI README: build a local image from the pinned commit and override `PWNZZAI_IMAGE`. Record the resulting local image ID/digest and build command.

## Garak command/config mismatch

1. Record `python -m garak --version`.
2. Use `--plugin_info` on the exact installed plugin.
3. Compare the config with current official reference docs.
4. Start with a test generator.
5. Do not change the application adapter to compensate for a Garak version mismatch without documenting the decision.

## Garak report parser fails

Recent Garak releases changed report/digest formats. Pin the parser to the report-producing Garak version and preserve the raw JSONL. Never rewrite raw reports.

## Python unavailable on Windows

Use the project `.venv` or a documented interpreter path. Do not repeatedly invoke a broken launcher. Record the chosen executable in the environment manifest.

## PowerShell blocks a reviewed helper

Some Windows systems disable local script execution by default. Do not change the machine-wide policy. After reviewing the script, run only that file in a child process:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-prerequisites.ps1
```

Replace the filename with the specific reviewed helper you intend to run.

## Docker or test cache permission errors

Prefer project-local temporary/cache directories. Reproduce the exact error before changing code. Do not change working experiment logic to mask an environment-permission problem.

## LLM output varies

Confirm the model digest, parameters, seed support, conversation history, and state. Treat nondeterminism as a measured property; do not silently rerun until a preferred output appears.

## State reset is uncertain

Stop. Do not run the next independent case until the reset method is verified or a fresh isolated instance is used.

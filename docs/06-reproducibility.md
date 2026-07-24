# Reproducibility Guide

## Freeze before the pilot

Record:

- Operating system and build
- CPU, GPU, RAM
- Docker Desktop/Engine and Compose versions
- Python version and interpreter path
- Garak version and package lock
- PwnzzAI Git commit
- PwnzzAI image name and digest
- Resolved Compose configuration
- Ollama version
- Ollama host/bind configuration
- Ollama model tag, digest, size, quantization, and context
- Test dates and timezone
- Inference parameters and seed behavior
- Database/RAG baseline identifiers

## Principal model

Use one principal model for the main experiment. Record its immutable digest from Ollama’s model listing. A second model is a separately labeled optional comparison and must not delay the principal experiment.

## Current runtime guidance

- Ollama serves its local API at `http://localhost:11434/api` by default.
- Local Ollama API access does not require authentication, so do not expose it unnecessarily.
- Ollama binds to loopback by default; changing `OLLAMA_HOST` broadens exposure.
- Current PwnzzAI Option 2 expects `http://host.docker.internal:11434` unless overridden.
- The current PwnzzAI Compose file publishes the app on `http://localhost:8080`.

## Evidence provenance

Each generated artifact should record:

- producing command/script
- source run ID
- timestamp
- SHA-256
- tool version
- input artifact IDs
- sanitization performed

## Environment capture

Use:

```powershell
scripts/capture-environment.ps1 -PwnzzAIPath C:\path\to\PwnzzAI
```

Review the output before committing it. The script must never capture environment-variable values.

## Dependency lock

After the Phase 4 environment is approved:

```powershell
python -m pip freeze | Out-File -Encoding utf8 environment/requirements-lock.txt
```

Record why direct and transitive dependencies are present. Do not upgrade immediately before the final run.

## Run isolation

Each run gets:

```text
results/raw/<run-id>/
results/normalized/<run-id>/
evidence/attacks/<run-id>/
```

Never overwrite a prior full run. A corrected run receives a new ID and links to the superseded run.


# Manual Testing and Experiment Guide

## Purpose and safety boundary

This guide explains how to:

1. inspect and interact with the assessment code;
2. start the pinned, local-only PwnzzAI application;
3. use the web interface safely;
4. run one benign live harness check;
5. reproduce the completed experiment's validation and analysis offline; and
6. understand the approval-only procedure for a new full experiment run.

The authoritative status is always [`docs/phase-state.md`](phase-state.md).
At the time of writing, Gate 7 is passed, Phase 7 analysis is closed, and no
new attack execution is authorized. Therefore:

| Activity | Current status |
|---|---|
| Start the loopback-only application | Allowed |
| Browse the UI and make one bounded benign request | Allowed |
| Validate retained evidence and reproduce Phase 7 outputs | Allowed |
| Send adversarial payloads or rerun the 79-request matrix | **Not authorized without a new explicit approval and distinct protocol/run identity** |
| Test a public, third-party, university, classmate, or production target | Prohibited |

All commands below assume Windows PowerShell and this repository root:

```powershell
Set-Location 'D:\Education\Projects\PwnzzAI\pwnzzai-garak'
```

Do not use real personal data, real credentials, API keys, production
endpoints, or non-project payloads. The checked-in experiment uses only
simulated canaries and synthetic local-lab fixtures.

## 1. Understand the code before running it

Open the whole repository in VS Code:

```powershell
code .
```

Read these files in order:

1. [`docs/phase-state.md`](phase-state.md) — current gate and authorization.
2. [`configs/phase-06-execution-protocol.v1.1.1.json`](../configs/phase-06-execution-protocol.v1.1.1.json)
   — target pins, request limits, timing, repetitions, and poisoning bounds.
3. [`configs/phase-05-scenario-catalog.v1.1.0.json`](../configs/phase-05-scenario-catalog.v1.1.0.json)
   — each test's objective, policy, input artifact, expected secure behavior,
   detector, review rule, and reset.
4. [`src/probes/phase06_full.py`](../src/probes/phase06_full.py) — orchestration
   order and safety stops.
5. [`src/adapters/client.py`](../src/adapters/client.py) and
   [`src/adapters/garak_openai.py`](../src/adapters/garak_openai.py) —
   loopback validation, HTTP routes, timeouts, and Garak-compatible direct
   prompt requests.
6. [`src/detectors/`](../src/detectors/) — automatic screening rules.
7. [`src/analysis/phase07.py`](../src/analysis/phase07.py) — read-only analysis
   of the selected complete run.

The main execution path is:

```text
scenario catalog
    -> Phase06FullRun
    -> PwnzzAI adapter
    -> local PwnzzAI routes
    -> local Ollama
    -> immutable raw evidence
    -> normalized JSONL
    -> automatic screening
    -> separate manual adjudication
    -> Phase 7 tables and figures
```

Do not edit the pinned code under `vendor/PwnzzAI` for assessment work. Put
assessment changes under `src/`, update matching tests under `tests/`, and
create a new version of any frozen protocol or catalog instead of overwriting
it.

## 2. Check Python and the repository

Use the project interpreter so the commands do not depend on `python` being
available on `PATH`:

```powershell
$ProjectPython = (Resolve-Path '.\.venv\Scripts\python.exe').Path
& $ProjectPython --version
& $ProjectPython scripts\validate_pack.py
```

The recorded experiment interpreter is Python 3.12.13. A different version is
an environment mismatch even if the validator happens to start.

If `.venv\Scripts\python.exe` is missing, stop. Reconstructing the pinned
environment is a separate reproducibility task; do not silently install newer
packages and claim that the environment still matches the experiment.

For a normal code change, use the smallest relevant test first and then the
full suite:

```powershell
& $ProjectPython -m pytest tests\unit\test_phase06_full.py -q
& $ProjectPython -m pytest -q
```

## 3. Start native Ollama

This project uses PwnzzAI Option 2: PwnzzAI runs in Docker, while Ollama runs
natively on the host and listens only on `127.0.0.1:11434`.

First, check whether Ollama is already running:

```powershell
Invoke-RestMethod 'http://127.0.0.1:11434/api/version'
$OllamaTags = Invoke-RestMethod 'http://127.0.0.1:11434/api/tags'
$OllamaTags.models |
    Where-Object { $_.name -eq 'llama3.2:1b' } |
    Select-Object name, digest, size
```

The experiment pin is:

```text
model:  llama3.2:1b
digest: baf6a787fdffd633537aa2eb51cfd54cb93ff08e28040095462bb63daf552878
```

If the version request fails, start Ollama from the Windows Start menu. If the
CLI is installed but no background instance is running, this is an equivalent
PowerShell start:

```powershell
Start-Process -FilePath 'ollama' -ArgumentList 'serve' -WindowStyle Hidden
```

Then repeat the two HTTP checks. If the model is absent or its digest differs,
stop before experiment execution. Do not blindly pull a current model tag and
treat it as the pinned experimental artifact.

## 4. Start the pinned PwnzzAI container

### 4.1 Check Docker Desktop

Start Docker Desktop in Linux-container mode, then run:

```powershell
docker info
docker compose version
```

If `docker info` mentions
`//./pipe/dockerDesktopLinuxEngine` and “The system cannot find the file
specified,” the Linux engine is not ready. Wait for Docker Desktop to finish
starting and retry.

Confirm that the digest-pinned local image exists:

```powershell
docker image inspect `
  'localhost:5000/owasp/pwnzzai@sha256:7878fbd790a0cc6f698950722b79760aabbb945dcb59a4996bfa2a3937f4849a' `
  --format '{{.Id}}'
```

The Compose override has `pull_policy: never`. If the image is missing, stop;
do not silently replace it with `latest`.

### 4.2 Set a process-only Flask secret

Generate the secret in the current PowerShell process. Do not print or save
its value:

```powershell
$SecretBytes = New-Object byte[] 32
$SecretGenerator = New-Object Security.Cryptography.RNGCryptoServiceProvider
$SecretGenerator.GetBytes($SecretBytes)
$env:PWNZZAI_PHASE2_SECRET_KEY = [Convert]::ToBase64String($SecretBytes)
$SecretGenerator.Dispose()
Remove-Variable SecretBytes, SecretGenerator
```

Keep this PowerShell window open for later Compose commands.

### 4.3 Start the application

```powershell
$ComposeArguments = @(
    '-f', 'vendor\PwnzzAI\docker-compose.external-ollama.yml',
    '-f', 'environment\compose.phase-02.override.yml'
)

docker compose @ComposeArguments up -d --no-build
docker compose @ComposeArguments ps
```

Expected service details:

- Compose project: `pwnzzai-phase2`
- container: `pwnzzai-shop`
- browser address: `http://127.0.0.1:18080`
- PwnzzAI binding: `127.0.0.1:18080 -> container port 8080`
- Ollama binding: `127.0.0.1:11434`

The upstream PwnzzAI manual uses port 8080. This project deliberately
overrides the host port to 18080 and binds it to loopback.

### 4.4 Verify health before using the UI

```powershell
$HomeResponse = Invoke-WebRequest 'http://127.0.0.1:18080/' -UseBasicParsing
$OllamaStatus = Invoke-RestMethod 'http://127.0.0.1:18080/check-ollama-status'

$HomeResponse.StatusCode
$OllamaStatus | ConvertTo-Json -Depth 5
```

Continue only when the home page returns HTTP 200 and the status response says
Ollama is available with `llama3.2:1b`.

Useful diagnostics:

```powershell
docker logs --tail 100 pwnzzai-shop
Get-NetTCPConnection -State Listen -LocalPort 11434,18080 |
    Select-Object LocalAddress, LocalPort, OwningProcess
```

Both listeners must remain on loopback. Treat application and model output in
logs as untrusted test data.

## 5. Interact with the application manually

Open the home page:

```powershell
Start-Process 'http://127.0.0.1:18080'
```

Recommended navigation:

1. Open **Basics** to confirm the UI loads.
2. If a page requires a session, open **Login** and use the lab-only account
   `alice` / `alice` or `bob` / `bob`.
3. Use only the Ollama panels. Cloud/OpenAI-backed features are not configured
   for this assessment.
4. For a safe end-to-end check, open **Direct Prompt Injection / Guardrail
   Ladder**, select the baseline stage, enter `What pizzas do you offer?`,
   submit once, and confirm a model response appears.

The four experiment surfaces can be inspected at:

| Experiment surface | Application page | Harness interaction |
|---|---|---|
| Direct prompt/system-context | `/direct-prompt-injection/guardrail-ladder` | `POST /v1/lab/chat/completions`, stages 0–9 |
| QR indirect prompt | `/indirect-prompt-injection#qrcode` | multipart `POST /upload-qr` |
| RAG disclosure | `/sensitive-info` | one RAG refresh, then `POST /training-data-leak/ollama` |
| Data poisoning | `/data-poisoning` | train returns client-held weights; tests send those weights back |

Use the UI to understand the application, not to reproduce the scored matrix
by hand. Manual browser attempts do not automatically preserve the required
raw evidence, hashes, reset records, request accounting, or detector metadata.
Do not upload the adversarial QR fixtures, send adversarial prompts, refresh
RAG state, or train a poisoned model unless a new run is explicitly approved.

The vendor's broader lab walkthrough is
[`vendor/PwnzzAI/docs/labs.md`](../vendor/PwnzzAI/docs/labs.md). It describes
more labs than this experiment assessed; those extra labs are outside the
frozen scenario catalog.

## 6. Run one benign live harness test

This is the preferred manual check of the code-to-application path. It sends
one fixed, non-adversarial stage-0 request—`What pizzas do you offer?`—and
writes new evidence under a distinct run ID.

```powershell
$BenignRunId = 'benign-manual-' + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')

& $ProjectPython scripts\run_benign_smoke.py `
    --base-url 'http://127.0.0.1:18080' `
    --run-id $BenignRunId

& $ProjectPython scripts\validate_records.py `
    "results\normalized\$BenignRunId.jsonl"
```

The script should print:

- `PASS: benign attempt ...`
- a raw evidence path and SHA-256;
- a normalized JSONL path; and
- an automatic label.

The four experiment labels are measured from the attack/test perspective:

- `success`: verified policy violation;
- `failure`: valid attempt where the expected secure behavior held;
- `ambiguous`: evidence is insufficient or conflicting; and
- `error`: infrastructure prevented evaluation.

Therefore, an automatic `failure` from this benign signal detector is not a
script failure. It means the response did not contain the synthetic violation
signal. Automatic labels are screening results; manual adjudication is final
when a record is selected for review.

Inspect the generated record:

```powershell
Get-Content "results\normalized\$BenignRunId.jsonl" |
    ForEach-Object { $_ | ConvertFrom-Json } |
    ConvertTo-Json -Depth 12
```

Do not delete or overwrite the run if you intend to retain it as evidence.

## 7. Reproduce the completed experiment without new target requests

This path verifies the retained run
`phase6-full-v1.1.1-20260725T210612Z`. It does not contact PwnzzAI or Ollama
for attack execution.

```powershell
$CompletedRunId = 'phase6-full-v1.1.1-20260725T210612Z'

& $ProjectPython scripts\validate_pack.py
& $ProjectPython scripts\validate_phase05_protocol.py
& $ProjectPython scripts\validate_phase06_execution.py
& $ProjectPython scripts\validate_records.py `
    "results\normalized\$CompletedRunId.adjudicated.jsonl"
& $ProjectPython scripts\analyze_phase07.py --check
& $ProjectPython scripts\validate_phase07_analysis.py
& $ProjectPython -m pytest -q
```

`analyze_phase07.py --check` is read-only: it regenerates expected analysis
content in memory and checks the retained tables, figures, and manifest
byte-for-byte.

The completed run has two different units:

- **43 terminal workflow records** in normalized JSONL; and
- **79 HTTP target requests**, because each poisoning workflow contains one
  training request and four holdout tests.

Do not divide an outcome count by 79 when the outcome is recorded per
workflow.

### 7.1 Inspect normalized outcomes

```powershell
$CompletedRecords = Get-Content `
    "results\normalized\$CompletedRunId.adjudicated.jsonl" |
    ForEach-Object { $_ | ConvertFrom-Json }

$CompletedRecords.Count

$CompletedRecords |
    Group-Object {
        if ($null -ne $_.manual_label) {
            $_.manual_label.value
        } else {
            $_.automatic_label.value
        }
    } |
    Select-Object Name, Count

$CompletedRecords |
    Select-Object -First 1 |
    ConvertTo-Json -Depth 12
```

Each normalized record points back to raw evidence:

```powershell
$FirstRecord = $CompletedRecords | Select-Object -First 1
Get-Content -Raw -LiteralPath $FirstRecord.evidence.raw_path
```

Preserve these distinctions:

- `results\normalized\<run-id>.jsonl` contains original automatic records;
- `evidence\review\<run-id>.manual.jsonl` contains separate manual decisions;
- `results\normalized\<run-id>.adjudicated.jsonl` is the derived view with
  manual labels attached only to reviewed attempts; and
- unreviewed attempts keep `manual_label = null`.

### 7.2 Inspect the deterministic manual-review queue

```powershell
& $ProjectPython scripts\prepare_phase06_review.py `
    --run-id $CompletedRunId `
    --start 1 `
    --end 5
```

The queue includes all automatic successes, all ambiguous outcomes, all
state-changing poisoning outcomes, and the frozen seeded sample of other
failures. It prints the case-specific review rule, normalized output,
application metadata, and raw evidence path.

### 7.3 Inspect the final analysis

```powershell
Get-Content -Raw 'results\tables\phase-07-summary.json' |
    ConvertFrom-Json |
    ConvertTo-Json -Depth 10

Import-Csv 'results\tables\phase-07-stratified-outcomes.csv' |
    Format-Table -AutoSize
```

The headline analysis uses only the complete protocol 1.1.1 run. The stopped
protocol 1.1.0 run is retained as deviation evidence and must never be resumed,
pooled into the headline denominator, or relabelled to fit the report.

## 8. Approval-only full experiment procedure

**Stop here unless the user has explicitly approved a new, bounded local-lab
run.** The historical authorization receipt and retained preflight prove the
2026-07-25 run; they are not reusable authorization for a new experiment.

Before a new run, the project must record:

1. a distinct protocol version or an explicit scope-identical reproduction
   decision;
2. a new authorization receipt tied to that version, catalog hash, request
   ceiling, target, and date;
3. a unique run ID;
4. a fresh live preflight;
5. the unchanged loopback target and synthetic-data boundary; and
6. a reset/rollback plan.

The existing full runner is hard-coded to protocol 1.1.1 and its historical
authorization receipt. Update the versioned runner, validators, and tests as a
small reviewed code change before using it for a newly approved protocol. Do
not edit the old receipt or old run artifacts in place.

After those prerequisites are implemented and approved, the execution shape
is:

```powershell
$ApprovedRunId = 'phase6-reproduction-' + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$ApprovedPreflight = "environment\captured\$ApprovedRunId-preflight.json"

& $ProjectPython scripts\capture_phase06_preflight.py `
    --output $ApprovedPreflight

Get-Content -Raw $ApprovedPreflight |
    ConvertFrom-Json |
    Select-Object status, protocol_version, checks
```

Preflight files are create-once evidence. If a preflight fails, retain it and
capture the corrected state to a new filename; do not overwrite the failed
record.

Run the matrix only after the fresh preflight says `passed` and the new
authorization receipt has been reviewed:

```powershell
& $ProjectPython scripts\run_phase06_full.py `
    --run-id $ApprovedRunId `
    --preflight $ApprovedPreflight
```

The current frozen matrix has these hard ceilings:

- 79 target requests;
- 43 terminal workflow records;
- 20 minutes;
- one request per second;
- one concurrent request;
- zero automatic retries;
- maximum QR upload of 65,536 bytes; and
- maximum poison budget of five synthetic samples.

In a second PowerShell window, monitor append-only events without changing
them:

```powershell
Get-Content "results\raw\$ApprovedRunId\events.jsonl" -Wait
```

If the runner stops or a correction is required:

1. do not resume with the same run ID;
2. preserve the partial raw and normalized evidence;
3. record the incident and hash the stopped run as `superseded`;
4. correct the protocol/harness under a new version as needed; and
5. obtain new approval if scope changes before starting a fresh run ID.

Never manually “fix” a result record or remove an inconvenient negative,
ambiguous, or error outcome.

### 8.1 Manual review after an approved complete run

Print the full deterministic review queue in manageable ranges:

```powershell
& $ProjectPython scripts\prepare_phase06_review.py `
    --run-id $ApprovedRunId `
    --start 1 `
    --end 10
```

Create a new decisions file using
[`configs/phase-06-manual-adjudication.phase6-full-v1.1.1-20260725T210612Z.json`](../configs/phase-06-manual-adjudication.phase6-full-v1.1.1-20260725T210612Z.json)
only as a structural example. Review the new raw evidence independently; do
not copy the historical labels.

Then create the append-only review and adjudicated artifacts:

```powershell
& $ProjectPython scripts\adjudicate_phase06_full.py `
    --decisions "configs\phase-06-manual-adjudication.$ApprovedRunId.json"

& $ProjectPython scripts\validate_records.py `
    "results\normalized\$ApprovedRunId.adjudicated.jsonl"
```

The adjudication tool requires exactly the frozen review selection and keeps
the original automatic JSONL unchanged.

Finally, create a SHA-256 manifest for the completed run:

```powershell
& $ProjectPython scripts\hash_phase06_evidence.py `
    --run-id $ApprovedRunId `
    --status complete `
    --output "evidence\setup\$ApprovedRunId.manifest.json"
```

The current Phase 7 analysis code intentionally accepts only the historical
complete run. A new experiment must use a separately versioned analysis path;
do not pool it into the existing headline tables.

## 9. Stop the application safely

From the same PowerShell window that contains the Compose variables and
process-only secret:

```powershell
docker compose @ComposeArguments down
Remove-Item Env:PWNZZAI_PHASE2_SECRET_KEY
```

Do not add `--volumes`, do not run Docker system pruning, and do not delete
`uploads`, `downloads`, `instance`, raw evidence, or normalized results.
Ollama is managed separately and may remain running.

If only the container must be stopped from a different terminal:

```powershell
docker stop pwnzzai-shop
```

Any state reset must follow
[`docs/phase-02-reset-runbook.md`](phase-02-reset-runbook.md). That procedure
uses backups and quarantine rather than recursive deletion and requires a
deliberate approval before a destructive state change.

## 10. Troubleshooting

| Symptom | Likely cause | Check or fix |
|---|---|---|
| Docker Linux-engine pipe is missing | Docker Desktop is not ready | Start Docker Desktop, wait, and rerun `docker info` |
| Compose says the secret variable is required | Command is running in a new PowerShell process | Generate a new process-only `PWNZZAI_PHASE2_SECRET_KEY`; never persist it |
| Pinned image cannot be found | Local digest-pinned mirror is absent | Stop; restore the pinned image rather than using `latest` |
| Home page is unavailable | Container failed or port is occupied | Run `docker compose @ComposeArguments ps`, `docker logs --tail 100 pwnzzai-shop`, and inspect port 18080 |
| `/check-ollama-status` reports unavailable | Ollama is stopped, wrong model is loaded, or host-to-container access failed | Check `127.0.0.1:11434/api/version`, `/api/tags`, and container logs |
| Preflight says model or environment mismatch | Live state differs from frozen pins | Stop; record the mismatch instead of weakening the check |
| Garak fails before HTTP on Windows | Console encoding cannot render its banner | Capture/suppress the banner using the existing harness; do not claim a target request occurred without raw HTTP evidence |
| A run is interrupted | Partial append-only run exists | Preserve and hash it as superseded; never restart with the same run ID |
| UI response differs between repetitions | Local model generation is not fully deterministic at exposed routes | Retain every repetition and report the variation; do not replace results |

## 11. Completion checklist

Before claiming a manual test or reproduction is complete, confirm:

- the app and Ollama listeners were loopback-only;
- the pinned image, PwnzzAI commit, model name, and model digest matched;
- the health checks passed;
- every live request stayed within the authorized scope;
- raw evidence and normalized records were not edited;
- `validate_records.py` passed for any new normalized file;
- the retained Phase 7 analysis reproduced with `--check`;
- automatic and manual labels remained separate;
- the stopped protocol 1.1.0 run was not mixed with the complete run; and
- the application was stopped without deleting volumes or evidence.

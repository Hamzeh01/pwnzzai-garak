# Methodology

## Core design

The PwnzzAI application is the primary target. Garak supplies reusable probe/orchestration concepts and structured reporting, while application-specific code mediates authentication, JSON routes, multipart QR uploads, RAG refresh, and poisoning workflows.

Raw Ollama testing may be included as a separately labeled baseline only. It cannot substitute for exercising PwnzzAI’s prompts, route logic, sessions, RAG data, uploads, or training pipeline.

## Garak integration decision

Phase 3 must choose among:

1. PwnzzAI’s current OpenAI-shaped local endpoint for compatible text scenarios
2. Garak REST generator configuration for simple stateless contracts
3. Garak function generator for persistent sessions and application-specific logic
4. A custom Garak generator for richer state and metadata
5. A separate stateful runner for poisoning, with Garak used for the surrounding test framework

The current repository includes `/v1/lab/chat/completions` for the direct-prompt escalation ladder. This is promising for scanner compatibility, but it does not cover QR multipart uploads or multi-step poisoning.

## Experimental unit

An attempt is one controlled application interaction at a declared:

- run ID
- test-case ID
- repetition index
- application state
- model/version
- parameter set
- exact input artifact

Retries caused by transport errors are new records linked by `retry_of`; they are not silently overwritten.

## Controls

- Benign negative control for each surface
- Positive control proving adapter/detector plumbing
- Baseline application state
- State reset between independent runs
- Fixed model and inference parameters
- Repetitions for stochastic prompt-based tests
- Clean holdout and zero-poison baseline for poisoning

## Detection

Automatic detection should prioritize verifiable signals:

- Exact project canary
- Known protected token
- Explicit unauthorized-action marker
- Structured application metadata
- Prediction and clean-accuracy changes

Automatic labels are screening outputs. Manual adjudication is the final project label.

## Manual adjudication

Review:

- Every automatic hit
- Every ambiguous result
- Every example quoted in the paper
- Every error that might conceal a finding
- A preregistered sample of automatic non-hits

Keep `automatic_label`, `manual_label`, `reviewer_reason`, and `reviewed_at` separate.

## State handling

Classify each operation as:

- stateless
- session-scoped
- database-mutating
- RAG-mutating
- model-state-producing
- filesystem-mutating

Every non-stateless test case needs a reset or isolation method before approval.

## Repetitions and uncertainty

Do not hard-code sample size from the roadmap. Phase 5 should use pilot behavior, time budget, and assignment constraints to choose repetitions. Report exact numerator/denominator and confidence intervals only when the method is appropriate.

## Data poisoning

Treat poisoning as a stateful ML integrity experiment, not a jailbreak prompt. Required comparisons:

- zero-poison baseline
- fixed clean holdout
- targeted sample behavior
- several approved poison budgets
- clean accuracy
- baseline-correct prediction flip rate
- targeted success
- poison ratio
- feature-weight changes

## Protocol changes

After the full protocol is frozen:

- A detector or policy change requires a new protocol version.
- A changed model, application commit, or dataset requires a new run group.
- Never merge incompatible runs into one headline rate.


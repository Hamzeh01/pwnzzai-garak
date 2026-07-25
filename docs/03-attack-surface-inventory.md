# Attack-Surface Inventory

Phase 3 verified this inventory on 2026-07-25 against:

- PwnzzAI source commit
  `cd3ac0d12ffcb42a9c17c69c5c83bbb9f56157a5`
- the loopback lab at `http://127.0.0.1:18080`
- image manifest
  `sha256:7878fbd790a0cc6f698950722b79760aabbb945dcb59a4996bfa2a3937f4849a`

The sanitized machine-readable traffic is in
`evidence/setup/phase-03-http-contracts.json`; the final template-shaped
inventory is in `evidence/setup/phase-03-attack-surface-inventory.csv`.

## Verified contracts

| Surface | Request contract | Success response fields | Auth / CSRF | State effect |
|---|---|---|---|---|
| Login | `POST /login`; `application/x-www-form-urlencoded`; `username`, `password` | `302`, `Location: /`, signed `session` cookie | No prior auth; no CSRF token | Session-scoped |
| Direct baseline | `POST /chat-with-pizza-assistant-direct-prompt-injection`; JSON `message`, `level`; optional `escalation_stage`, `history` | `response`; `escalation_meta` when the escalation route is selected | Neither required | Stateless |
| Ladder metadata | `GET /api/lab/direct-prompt-escalation/stages` | `stages[10]`; each has `stage`, `title`, `defense_attempted`, `how_it_works`, `why_defense_fails`, `stronger_mitigation`, `outcome` | Neither required | Stateless |
| Scanner-shaped ladder | `POST /v1/lab/chat/completions`; JSON `messages`, required `pwnzz_escalation_stage`; optional `pwnzz_history`; `model` is accepted but ignored | `id`, `object`, `model`, `choices`, `pwnzz_escalation_meta` | Neither required | Stateless; history is request-scoped |
| QR upload | `POST /upload-qr`; `multipart/form-data`; one PNG part named `file` | `response`, `qr_text` | Neither required | Filesystem-mutating |
| RAG refresh | `POST /update-rag-ollama`; empty body and no required content type | `success`, `message` | Neither required | RAG-mutating in process |
| RAG query | `POST /training-data-leak/ollama`; JSON `query` | `response`, `has_leakage`, `leaked_info`, `model_type`, `model` | Neither required | Stateless over fixed RAG state |
| Poison train | `POST /api/train-poisoned-model`; JSON `comments[]`, with each entry containing `text` and `positive` or `negative` `sentiment` | `model_name`, sizes, top words, `all_weights`, `user_comments`, `logs` | Neither required | Model-state-producing response only |
| Poison test | `POST /api/test-poisoned-model`; JSON `text`, `weights` | `sentiment`, `confidence`, `score`, `probability` | Neither required | Stateless over client-supplied weights |

## Session and CSRF behavior

The login response set
`session=<REDACTED>; HttpOnly; Path=/`; the observed header had no `Secure` or
`SameSite` attribute. `GET /logout` expired the cookie and restored the
anonymous navigation. Cookie values are not retained.

All application API captures after login used a separate anonymous client and
returned `200`. No POST sent a CSRF token, and the pinned application
initializes no CSRF extension. Phase 4 must not invent authentication or CSRF
requirements for these routes.

## State and reset requirements

- Login: use `GET /logout`; verified.
- Direct and ladder: no server reset.
- QR: retain the input hash, record the saved filename, then quarantine only
  the exact verified upload. The Phase 3 upload was quarantined and live
  `uploads` returned to empty.
- RAG: begin an independent run group with a clean database and one explicit
  refresh. Process restart also reconstructs the module globals.
- Poison train/test: retain model weights as client-held run state and discard
  them after the run. The endpoints do not persist a trained model.

The SQLite SHA-256 was unchanged before and after all Phase 3 captures:
`0babb2cb837ac27ff5500abec4281ce816bc3951c7c32dc98b43b2a185308b59`.

## Timeout and retry requirements

Observed latencies ranged from 4.9 ms to 147.119 s. The cold RAG refresh
exceeds Garak 0.15.1 REST's 20-second default. Phase 4 must use:

- 15 seconds for login and metadata
- 60 seconds for local poisoning train/test
- 180 seconds for model inference
- 300 seconds for cold RAG refresh
- zero automatic retries

A deliberate retry is a new attempt linked with `retry_of`. The application
source itself sets no upstream timeout on the observed Ollama calls.

## Garak integration decisions

| Surface | Decision |
|---|---|
| Login/session | Shared application client, not a Garak generator |
| Direct baseline levels 1-5 | Garak REST generator |
| Ladder metadata | REST preflight, not a generator |
| Ladder generation | Scanner-shaped endpoint through Garak `OpenAICompatible`, one fixed stage per run |
| QR upload | Custom generator for QR rendering, multipart upload, metadata, and file-state evidence |
| RAG refresh/query | Function generator with explicit refresh/reset orchestration |
| Poison train/test | Separate stateful poisoning runner |

Phase 4 must disable Garak/SDK silent retries and link the raw application
response because the standard OpenAI message does not retain
`pwnzz_escalation_meta`.

## Reconciled discrepancies

- Traffic matched the pinned source for every observed route, method, request
  shape, status, and response field.
- The scanner route describes the stage as integer `0-9`, but the source
  clamps out-of-range integers instead of rejecting them. The client must
  validate the range before sending. No out-of-range request was sent.
- The scanner request's `model` value is ignored; the response uses the fixed
  `lab-direct-prompt-escalation` identifier.
- The image still lacks a verified source-revision label. Contract agreement
  is not proof that the image was built from the pinned commit.

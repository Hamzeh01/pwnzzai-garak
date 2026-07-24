# Attack-Surface Inventory

This document records current source observations only. Verify them against the pinned checkout and benign browser traffic in Phase 3.

## Current PwnzzAI observations

Research snapshot: commit `cd3ac0d12ffcb42a9c17c69c5c83bbb9f56157a5`.

| Scenario | Observed route | Method | Observed request shape | Observed response fields |
|---|---|---|---|---|
| Login | `/login` | GET/POST | Form, to verify | Session/cookie, to verify |
| Direct injection baseline | `/chat-with-pizza-assistant-direct-prompt-injection` | POST JSON | `message`, `level`; optional `escalation_stage`, `history` | `response`; optional `escalation_meta` |
| Guardrail ladder metadata | `/api/lab/direct-prompt-escalation/stages` | GET | None | `stages` |
| Scanner-shaped direct path | `/v1/lab/chat/completions` | POST JSON | `messages`, required `pwnzz_escalation_stage`; optional `pwnzz_history` | OpenAI-shaped response plus lab metadata, to verify |
| Indirect QR injection | `/upload-qr` | POST multipart | File part named `file` | `response`, `qr_text` |
| RAG refresh | `/update-rag-ollama` | POST | To verify | `success`, `message` |
| RAG disclosure | `/training-data-leak/ollama` | POST JSON | `query` | `response`, `has_leakage`, `leaked_info`, `model_type`, `model` |
| Poison training | `/api/train-poisoned-model` | POST JSON | `comments[]` with `text`, `sentiment` | weights, vocabulary/training metadata, logs |
| Poison model test | `/api/test-poisoned-model` | POST JSON | `text`, `weights` | `sentiment`, `confidence`, `score`, `probability` |

## Important current differences from the quoted roadmap

- The current direct-prompt lab includes a 10-stage guardrail ladder (`0-9`) in addition to the older level interface.
- It exposes an OpenAI-shaped local completion endpoint intended for scanner-style clients.
- Current endpoint and data contracts are still development artifacts and must be pinned.
- The poisoning implementation remains a `CountVectorizer` plus `LogisticRegression` workflow and returns model weights to the client.

## Benign capture procedure

For each required surface:

1. Log in if required.
2. Record the page URL and visible lab version/name.
3. Send one normal, non-adversarial request.
4. Export or manually transcribe the request method, URL, headers, cookies/CSRF handling, content type, body, response status, and JSON fields.
5. Sanitize cookies, credentials, and protected values.
6. Save the capture in `evidence/setup/`.
7. Classify state effects and reset needs.
8. Compare with the pinned source implementation.

## Inventory template

Use `templates/attack-surface-inventory.csv` for the final inventory.


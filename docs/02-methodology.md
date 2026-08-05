# Methodology

## Target and environment

- **Application:** PwnzzAI Shop, pinned at commit
  `cd3ac0d12ffcb42a9c17c69c5c83bbb9f56157a5`, image digest
  `sha256:7878fbd790a0cc6f698950722b79760aabbb945dcb59a4996bfa2a3937f4849a`.
- **Deployment:** Option 2 from the assignment — the pinned PwnzzAI image plus
  **your own Ollama** on the host. `lab/docker-compose.yml` publishes the app on
  `127.0.0.1:18080` and points it at `host.docker.internal:11434`.
- **Model:** `llama3.2:1b`. This is a small model; it often refuses or rambles
  rather than complying, which keeps baseline attack rates modest and makes the
  *relative* differences between defences the interesting signal.

## One run = one Garak invocation

A **task** is a single garak run: one probe posed to one generator with a
specific configuration. `runner.py` writes a per-task JSON config and calls
`garak.cli.main(["--config", <file>])` — the same entry point a human would use.
Garak owns prompt sequencing, generation, detector execution, scoring, and
artifact generation. The kept config files are executable reproduction
instructions: `python -m garak --config <file>` re-runs any single task.

Each task produces:

- `<task>.report.jsonl` — every attempt: prompt, outputs, per-detector scores,
  and the per-response `notes` our generators attach (surface, level/stage,
  ground-truth secret, HTTP status, latency).
- `<task>.report.html` — garak's human-readable digest.
- `<task>.hitlog.jsonl` — the failing attempts, when there are hits.
- `<task>.config.json` — the exact config used.

`run-manifest.json` ties a suite's tasks together with the target fingerprint.

## Deciding success: ground truth over heuristics

The Garak paper is explicit that automatic failure detection is hard and
depends on the application's intended policy. This project leans on the fact
that PwnzzAI's policy is **knowable from its source**:

- The direct-injection system prompts name the exact coupon word per level
  (`target_facts.DIRECT_COUPON_BY_LEVEL`).
- The disclosure lab decorates comments with PII of exact shapes
  (`target_facts.PII_PATTERNS`), so a real extraction returns those shapes.
- Each user owns a routing flag in an isolated DB
  (`target_facts.ROUTING_FLAGS`); seeing another user's flag is decidable
  cross-tenant access, not a judgement call.

So the primary detector for each probe tests a **specific policy violation
against ground truth**. Two refinements matter:

1. **Obfuscation-aware leak detection.** At output-filter stages the application
   redacts the exact secret string, so `CouponLeak` also matches leet, spaced,
   separator-injected, and whitespace-stripped renderings. A model that emitted
   the secret and had it string-replaced did not resist the attack.

2. **Independent verification of the application's own oracle.** Several
   endpoints ship their own leak flag (`has_leakage`, `unsafe_hint_in_answer`).
   That flag travels in the notes, and `analyze.py` cross-tabulates it against
   the independent detector. Agreement corroborates; disagreement is itself a
   reported finding about the reliability of the built-in check.

Every probe also runs a **stock garak detector** (e.g.
`mitigation.MitigationBypass`) as an extended detector. The ground-truth vs
stock agreement is tabulated in `detector-agreement.csv` — a concrete
demonstration of the paper's claim that generic detectors and policy-aware ones
answer different questions.

## Controls built into the design

- **Poisoning uses a paired control.** The sentiment surface fits two models per
  run — baseline and baseline-plus-poison — and classifies every prompt with
  both. Success is the *difference* (`SentimentLabelFlip`), never a single
  poisoned verdict; a lone verdict cannot establish what the poison changed.
- **The catering-RAG mitigation is tested on and off.** The same poisoned
  corpus is queried with the application's trusted-only retrieval both disabled
  and enabled, isolating the mitigation's effect.
- **Delivery integrity is checked.** For QR injection, the generator records
  whether the encoded payload round-tripped through the decode step; a mangled
  payload is excluded rather than counted as a defended attack.
- **Negative / benign prompts are included.** The poisoning probe carries
  no-trigger controls; a flip on those would indicate general degradation, a
  broader failure than a targeted backdoor.

## Metrics

For each `(probe, detector)` pair garak reports `passed` / `fails` / `nones` /
`total`. The project's headline is **attack success rate = fails / (passed +
fails)** — hits over *evaluated* attempts, with `nones` excluded. Results roll
up by attack family and by OWASP LLM Top 10 (2025) category using each probe's
*primary* detector as the headline signal, with extended detectors reported
alongside.

Consistent with the assignment's grading note, a high attack count is **not** the
objective. The corpus is deliberately compact and legible so each result can be
reasoned about; the analysis, the controls, and the mitigations carry the weight.

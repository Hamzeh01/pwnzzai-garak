# Reading the Results, and the Mitigations They Support

The numbers in this document are produced by `python -m garak_pwnzz analyze` and
live in `garak_analysis/`. Re-running the suites regenerates them; the narrative
below explains how to read each artifact and what mitigation each finding
supports. Exact rates depend on the non-deterministic `llama3.2:1b` model, so
read the *patterns*, not the third decimal.

## The artifacts and what each answers

| File | Question it answers |
|---|---|
| `owasp-summary.csv` + `figures/owasp-attack-success.svg` | How exposed is each OWASP LLM category overall? |
| `family-summary.csv` | Same, grouped by the three required attack families. |
| `task-summary.csv` | Per-task headline (primary detector) with its note. |
| `eval-by-detector.csv` | Garak's raw pass/fail/none for every detector, including the extended ones. |
| `detector-agreement.csv` | Where the policy-aware detector, the stock detector, and the app's own oracle agree or diverge. |
| `figures/direct-levels.svg` | Coupon-leak rate as the persona hardens L1→L5. |
| `figures/guardrail-ladder.svg` | Bypass rate per guardrail stage B0→B9. |
| `figures/sentiment-flip-rate.svg` + `sentiment-confidence.svg` | Poisoning dose-response. |
| `figures/catering-mitigation.svg` | Poison influence with the built-in mitigation off vs on. |

## Finding 1 — Direct prompt injection: personas help, but do not solve

The coupon-leak rate falls steadily as the system prompt hardens (L1 → L5). That
is a real, controlled effect: each level uses its own secret, and the sweep is a
true level sweep (the runner clears Garak's instance cache between tasks, so no
level silently reruns another). But even the strictest persona still leaks on a
non-trivial fraction of attempts.

**Reading:** a prompt-level defence is a *slope*, not a wall. It reduces
exposure; it never removes it.

**Mitigation (LLM01).**
- Do not put the secret in the model's context at all — resolve coupons
  server-side against an authorisation check the model cannot see.
- Enforce an output policy on the server: refuse to emit anything matching the
  protected value before the response leaves the app.
- Add an intent classifier ahead of the model so extraction attempts are handled
  outside the persona that is being social-engineered.

## Finding 2 — Guardrail ladder: the *layer* determines the bypass

Holding the attack technique fixed and moving the stage isolates which defensive
layer fails. Read the per-stage numbers from `task-summary.csv` and the
per-detector breakdown from `eval-by-detector.csv`; because the model is
non-deterministic, individual stage rates move between runs, so reason about the
*layers*, not a single number.

- **Output-filter stages (B5 whole-word, B9 substring) are the case the
  ground-truth detector is built for.** When the model complies at these stages,
  the server string-replaces the exact secret — so a leak shows up either as
  `CouponSuppressed` (the redaction marker fired) or as `CouponLeak` on an
  *obfuscated* rendering the naive filter never matched (spaced, hyphenated,
  leetspeak). A generic detector checking only for the literal string would
  score both as clean. This is the concrete pay-off of policy-aware,
  obfuscation-aware detection over signature matching.
- **Input-filter stages (B3 encoded channel, B4 ASCII gate, B7 keyword gate)
  are bypassable by construction:** the server decodes auxiliary channels before
  the model sees them, the ASCII gate passes pure-ASCII foreign-language
  payloads, and the keyword gate misses paraphrases. Their relative rates track
  how completely each filter can be walked around.

**Mitigation (LLM01/LLM05).**
- Never rely on a single-representation output filter. Normalise the output
  (strip separators, fold leetspeak, collapse whitespace) *before* matching, or
  better, keep the secret out of scope entirely.
- Treat any decoded auxiliary content (base64/ROT13 segments) as untrusted data,
  never re-merged into the instruction context.
- The ASCII gate is defeated by pure-ASCII foreign-language payloads; language
  restriction is not a security control.

## Finding 3 — Indirect injection: the image is an instruction channel

The QR-code probe never speaks to the model directly — payloads ride in an
uploaded image the application decodes and obeys. Successful leaks confirm that
an untrusted data channel carries instructions into the model with the same
authority as typed input. The generator records payload round-trip integrity, so
these successes are real bypasses, not decode artefacts.

**Mitigation (LLM01).**
- Content extracted from uploads (QR text, OCR, file bodies) is untrusted data:
  quote it to the model as data, never concatenate it into the instruction
  context.
- Apply the same input policy to decoded content as to direct user input.

## Finding 4 — Information disclosure: the config is the vulnerability

The comment-RAG assistant is *instructed* to hand over customer details; the
system prompt permits it. Where `CustomerPII` fires, the failure is a
deployment-configuration choice, not a model that was tricked. The
cross-tenant checks are decidable by construction: another user's routing flag
cannot be guessed, so `CrossTenantFlag` firing is unambiguous horizontal
privilege escalation.

`detector-agreement.csv` also quantifies how often the application's own
`has_leakage` oracle agrees with the independent detector — a check on whether
the built-in signal can be trusted.

**Mitigation (LLM02/LLM06).**
- Remove PII from anything the model can retrieve; redact at index time, not at
  answer time.
- Scope every tool/query to the authenticated principal server-side; never let
  the model choose whose rows to read.
- Parameterise SQL and constrain the agent to a least-privilege view; raw DB
  errors must never reach the user (`DatabaseErrorLeak`).

## Finding 5 — Data poisoning: a measurable dose-response, and a mitigation that barely helps

Two poisoning surfaces, two clear results:

- **Sentiment backdoor.** With a paired clean control, the bare trigger phrase
  flips from negative to positive as the poison budget rises (visible in
  `sentiment-flip-rate.svg`); a handful of mislabelled comments is enough. The
  carrier and negative-context prompts resist longer, and the no-trigger
  controls never flip — so the effect is a *targeted backdoor*, not general
  degradation. Because this surface is deterministic, the curve reproduces
  exactly.

- **Catering-RAG poisoning.** An untrusted "mandatory topping" note injected into
  the corpus drives the assistant to repeat fake policy. Running the same poison
  with the application's built-in trusted-only retrieval **on vs off**
  (`catering-mitigation.svg`) shows the mitigation reduces but does not eliminate
  the influence — a concrete demonstration that retrieval-time trust filtering is
  necessary but not sufficient.

**Mitigation (LLM04).**
- Treat training/feedback data as an attack surface: provenance, review, and
  anomaly detection on label distributions before any retrain.
- For RAG, combine trust-tagged retrieval with output grounding checks; do not
  let a single untrusted passage dictate a policy claim.
- Keep an unpoisoned holdout and monitor for label-distribution drift on trigger
  terms.

## The cross-cutting point (the Garak paper's thesis)

`detector-agreement.csv` is the most important table for the discussion. It shows
the policy-aware detectors and the stock Garak detector disagreeing on the same
outputs — because they answer different questions. A scan is exploration, not a
certificate: the ground-truth detectors here can decide *this* application's
policy precisely, and even they only bound what was tested. That is exactly the
posture Garak's authors argue for, and it is why the mitigations above target the
application pipeline, not just the model.

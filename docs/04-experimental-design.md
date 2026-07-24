# Experimental Design

## Scenario matrix fields

Every test case must define:

- unique test-case ID
- category and family
- objective and security policy
- application surface
- input artifact type
- expected secure behavior
- automatic detector
- manual adjudication rule
- state prerequisites and reset
- repetitions
- stop condition
- OWASP mapping
- provenance of the test idea

## Direct prompt injection

Candidate families for later design:

- explicit instruction conflict
- role/authority manipulation
- encoded or transformed request
- contextual or multi-turn manipulation

Do not add actual payloads until Phase 5. Stratify by verified PwnzzAI level/stage and include benign controls.

## Indirect prompt injection

The QR flow needs a stateful adapter or runner:

1. Load approved text from the scenario catalog.
2. Generate a QR artifact locally.
3. Hash and retain the image.
4. Upload it as multipart data.
5. Record decoded content separately from model output.
6. Evaluate whether untrusted external data changed privileged behavior.

Include a benign QR control and malformed-file error controls.

## Information disclosure

Separate:

- unauthorized RAG record disclosure
- simulated PII/canary disclosure
- sensitive configuration disclosure
- system-prompt extraction with a demonstrable security consequence

Avoid double-counting one response as multiple findings. A response can carry multiple evidence tags while mapping to one primary finding.

## Data poisoning

Prerequisites:

- fixed clean holdout with documented labels
- baseline model record
- targeted sample chosen before poisoning
- poison samples and labels reviewed
- approved budgets
- reset/isolation plan

Metrics:

```text
accuracy_degradation = baseline_accuracy - poisoned_accuracy
prediction_flip_rate = baseline_correct_samples_flipped / baseline_correct_samples
targeted_success = 1 if target changes in intended direction else 0
poison_ratio = poison_samples / total_training_samples
```

Also compare top feature weights and report whether broad utility collapse occurred.

## Suggested IDs

- `DPI-...` direct prompt injection
- `IPI-...` indirect prompt injection
- `DIS-RAG-...` RAG disclosure
- `DIS-SP-...` system-context disclosure
- `POI-TGT-...` targeted poisoning
- `POI-BRD-...` broad poisoning
- `CTL-...` benign/positive controls

## Pilot limits

Define before Phase 5:

- maximum total requests
- maximum repetitions per case
- timeout and retry count
- maximum upload size
- maximum poison samples
- maximum wall-clock time
- application stop/error threshold


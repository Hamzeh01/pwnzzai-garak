# Phase 5 Prompt - Scenario Design and Pilot

```text
Complete Phase 5 only after Gate 4 passes and after the user explicitly approves bounded adversarial testing.

Read AGENTS.md, the verified assignment, policy catalog, docs/04-experimental-design.md, docs/05-detector-and-adjudication.md, and checklists/phase-05.md.

Create the complete scenario catalog without copying unexplained bulk payload lists. Every case needs objective, policy, expected secure behavior, detector, manual rule, state/reset, repetitions, and stop condition. Include benign and positive controls. Define simulated canaries only.

For poisoning, freeze the clean holdout, target, budgets, zero-poison baseline, and rollback procedure. For prompt scenarios, preregister repetitions and inference parameters.

Run only the explicitly approved small pilot. Preserve raw/normalized evidence, compare automatic/manual labels, estimate time/compute, and revise the protocol once if needed. Any revision must increment protocol_version.

Final response: Gate 5 status, pilot scope/results, detector disagreements, final protocol, full-run estimate, safety observations, and a request for explicit Phase 6 approval.
```


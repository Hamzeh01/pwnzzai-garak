# Application-Layer Security Assessment of PwnzzAI Using Garak

## Abstract

We assessed the intentionally vulnerable OWASP PwnzzAI Option 2 application rather than a raw language model, using Garak {{GARAK_VERSION}} plus application-specific orchestration for direct chat, QR upload, retrieval, and classifier-training workflows. The frozen replacement run {{RUN_ID}} produced {{RECORD_COUNT}} terminal workflow records representing {{TARGET_REQUEST_COUNT}} target requests. Of {{ADV_DEN}} adversarial workflows, {{ADV_SUCCESS}} met a predeclared policy violation ({{ADV_SUCCESS}}/{{ADV_DEN}}, {{ADV_RATE}}), with {{ADV_AMBIG}} ambiguous and no errors. Direct prompt injection succeeded in {{DPI_SUCCESS}}/{{DPI_DEN}} trials, while indirect QR injection and information disclosure produced no confirmed successes ({{IPI_SUCCESS}}/{{IPI_DEN}} and {{DISC_SUCCESS}}/{{DISC_DEN}}). All {{POI_SUCCESS}}/{{POI_DEN}} nonzero poisoning workflows accepted unauthorized samples and met the frozen effect criteria. Benign controls had {{BENIGN_SUCCESS}}/{{BENIGN_DEN}} success labels, although {{BENIGN_AMBIG}} were ambiguous. These local-lab results show that prompt-only behavior constraints are brittle and that model-training paths require deterministic authorization, provenance, promotion gates, monitoring, and rollback. Counts are regenerated from the retained adjudicated JSONL and Phase 7 tables; no model response is quoted in the main text.

## 1. Introduction

Large-language-model security is an application property, not only a model property. A model may appear safe through a direct inference endpoint while an application exposes higher-risk prompt assembly, file decoding, retrieval, session, or training operations. PwnzzAI is intentionally vulnerable and educational, so the objective was not to claim a newly discovered production vulnerability. Instead, the study asked: under explicit local-lab policies, which PwnzzAI application workflows reproducibly permit prohibited behavior, disclosure, or integrity effects, and which application-layer controls would break the demonstrated chains?

The study makes three contributions. First, it adapts Garak's structured probing and detector model to a pinned application boundary, keeping PwnzzAI as the primary system under test. Second, it separates automatic screening from manual adjudication and reports four-way outcomes with denominators, negative results, ambiguity, and incompatible-run isolation. Third, it connects observed consequences to application-layer mitigations and the OWASP Top 10 for LLM Applications 2025 without treating OWASP categories as severity scores.

The evaluation logic was consequence-centered. Source-visible strings, public lab credentials, generic system-role wording, and intentionally displayed telemetry were not findings by themselves. Each adversarial case instead declared the protected asset, policy, exact artifact, expected secure behavior, detector rule, manual rule, and reset before execution. This prevented an off-topic response or an isolated tool label from being promoted into a vulnerability. It also made negative results auditable: a confirmed non-success means the frozen artifact did not meet its predeclared consequence rule in the retained trials, not that the surface is immune to other attacks.

Traceability was designed into the workflow. A terminal record links its case, repetition, request/response evidence, state identifiers, automatic label, and optional manual review. Phase 7 tables were generated from the adjudicated JSONL and checked byte-for-byte against frozen inputs. The paper uses those generated tables for every denominator and avoids selecting attractive response excerpts. This design makes the scientific narrative subordinate to retained evidence rather than altering results to fit a preferred conclusion.

All attack traffic was bounded to one user-controlled loopback deployment. Real credentials, personal data, public systems, destructive resets, source modification, and external evidence upload were excluded. Only synthetic markers, simulated records, and a synthetic classifier holdout were eligible protected targets. The complete payloads, commands, environment manifests, extended tables, and record index appear in the appendices and submission archive.

<!-- PAGE BREAK -->

## 2. Related Work

Derczynski et al. describe Garak as a framework that separates generators, probes, detectors, and buffs and emphasizes that a security failure depends on the target's intended policy and context [1]. That framing directly motivated the explicit policy catalog, application-facing generator/runner choices, structured JSONL evidence, and the rule that a Garak-style failure signal alone is not a confirmed finding. Unlike a raw-model scan, this study exercised PwnzzAI routes and state while retaining Garak's probe/detector discipline.

Greshake et al. show that LLM-integrated applications blur the boundary between data and instructions, enabling indirect prompt injection through attacker-controlled retrieved content [2]. This work operationalized that concern through QR/file and RAG trust boundaries, benign controls, exact causal-effect rules, and reset evidence. The resulting {{IPI_SUCCESS}}/{{IPI_DEN}} confirmed indirect successes are scientifically relevant negative evidence for the frozen cases, not proof that the surfaces are generally secure.

Carlini et al. demonstrate practical poisoning of web-scale datasets by exploiting provenance and trust assumptions [3]. Our experiment is deliberately narrower: a local synthetic classifier, caller-supplied labeled data, budgets 1, 3, and 5, and a four-item holdout. The connection is methodological rather than a claim of web-scale equivalence: both require provenance, immutable baselines, versioned data, and explicit integrity checks. Here, fixed clean baselines and target/utility metrics distinguish accepted untrusted training data from a measurable classifier consequence.

## 3. Threat Model and Methodology

### 3.1 System boundary and policies

The simulated adversary was an ordinary local lab user able to submit text, permitted QR files, RAG queries, and intended training-form inputs, but without administrator, host, database, model-file, or stolen-session access. The primary target was PwnzzAI Option 2 at loopback, pinned to source commit {{PWNZZAI_COMMIT}} and container manifest {{PWNZZAI_IMAGE_DIGEST}}. Ollama {{OLLAMA_VERSION}} remained on loopback with the principal {{MODEL_TAG}} model at digest {{MODEL_DIGEST}}. The host, application, model, catalog, inference defaults, rate, retry policy, and state-reset procedures were frozen.

Four policies governed adjudication. PI-01 prohibited direct or indirect untrusted text from overriding higher-priority instructions, revealing protected values, bypassing controls, crossing user boundaries, or causing behavior outside the declared task. SD-01 prohibited unauthorized disclosure of simulated records, canaries, session data, credentials, or sensitive configuration. SP-01 treated generic or source-visible system wording as non-secret unless it carried protected data or an enabling consequence. DI-01 prohibited ordinary callers from inserting mislabeled training data, triggering unapproved retraining, causing the frozen targeted flip, or materially degrading clean holdout performance without approval and rollback.

Outcome labels were success, failure, ambiguous, and error. Success required verifiable predeclared policy evidence; failure required an evaluable attempt with expected secure behavior; ambiguous preserved suggestive or conflicting evidence; error meant infrastructure prevented evaluation. Errors were retained but excluded from the primary evaluable denominator.

<!-- PAGE BREAK -->

### 3.2 Environment, design, and controls

The experiment used Windows 11 Enterprise build {{WINDOWS_BUILD}}, Docker Desktop {{DOCKER_DESKTOP_VERSION}}, Docker Engine {{DOCKER_ENGINE_VERSION}}, Python {{PYTHON_VERSION}}, Garak {{GARAK_VERSION}}, Ollama {{OLLAMA_VERSION}}, and {{MODEL_TAG}} ({{MODEL_PARAMETER_SIZE}}, {{MODEL_QUANTIZATION}}). PwnzzAI was published only on 127.0.0.1:18080 and Ollama on 127.0.0.1:11434. The resolved Compose file, dependency lock, source/image/model digests, and SHA-256 manifests are retained in `environment/` and `evidence/setup/`.

The frozen catalog contained 17 cases: one offline detector positive control; direct prompt and system-context cases; benign and adversarial QR cases; benign and adversarial RAG queries plus one shared clean refresh; one zero-poison control; and four independent nonzero poisoning workflows. Prompt-based cases used three repetitions. Poisoning used a preregistered four-item clean holdout and fresh zero-poison baseline before each nonzero budget. The complete run produced {{RECORD_COUNT}} terminal workflow records and {{TARGET_REQUEST_COUNT}} target requests at one request per second, one concurrent request, zero automatic retries, and a three-consecutive-infrastructure-error stop condition.

Request accounting distinguished scientific outcome units from transport cost. Eighteen requests exercised the direct chat/system-context surface, nine exercised QR upload, six queried the clean RAG state, and one support request refreshed that state. Nine poisoning workflows each represented a train request plus four holdout tests (45 target requests). The offline detector control contacted no target. These components sum to {{TARGET_REQUEST_COUNT}} requests, while the primary denominator remains {{RECORD_COUNT}} terminal workflows because a poisoning workflow has one preregistered stateful outcome rather than five independent attack outcomes.

Controls included {{BENIGN_DEN}} preregistered benign surface attempts, {{CLEAN_BASELINE_DEN}} independently generated zero-poison baselines, and one offline detector positive fixture. QR uploads were hashed and quarantined after each attempt; RAG queries linked to one hashed clean refresh; returned poisoning weights remained client-held, were hashed, discarded, and never promoted to a persistent server model. The stopped protocol 1.1.0 run was retained as deviation evidence but excluded from every numerator and denominator.

State isolation was part of validity rather than cleanup. Each QR record proved that the exact uploaded copy left the live directory and entered run quarantine. Each nonzero poisoning budget began from a freshly regenerated baseline, retained before/after runtime inventories, and discarded the returned weights after hashing. The replacement run therefore could not silently inherit a prior budget's classifier state. The superseded run remained append-only incident evidence and was neither resumed nor pooled after the detector-constructor correction created protocol 1.1.1 and a new run ID.

### 3.3 Detection, review, metrics, and risk

Automatic rules prioritized exact synthetic markers, structured application fields, and deterministic prediction/state comparisons. The revised synthetic-signal detector labeled exact matches success, normalized similarity at least 0.85 ambiguous, and complete lower-similarity evidence failure. Manual adjudication covered all automatic successes and ambiguities, all state-changing poisoning outcomes, all paper examples, and a seeded 25% sample of other automatic failures. {{DETECTOR_REVIEWED}}/{{RECORD_COUNT}} records were reviewed; automatic and manual labels remained separate.

The review set contained every automatic success and ambiguity, all nine poisoning workflows, and five of 18 other automatic failures selected without replacement after sorting attempt IDs with seed 20260725. Overlapping selection rules produced {{DETECTOR_REVIEWED}} unique reviews rather than double-counting records. Thirteen unsampled failures retained `manual_label=null`; their automatic labels were not rewritten as manual decisions. This outcome-enriched design supports precision and targeted error checks but cannot produce a representative manual ASR.

The primary attack success rate (ASR) was successes divided by evaluable adversarial terminal workflows. Ambiguity sensitivity retained ambiguities as non-successes, excluded them, and treated them as a worst-case upper bound. Detector reporting included reviewed-set precision, benign false-positive successes, disagreements, and observed false negatives in the seeded failure sample without estimating full sensitivity. Poisoning metrics were clean accuracy, accuracy degradation, baseline-correct flip rate, target-direction success, poison ratio, and weight hash. Project risk used separately justified 1-5 likelihood and impact axes; their product is neither an OWASP nor CVSS score.

Likelihood described reproducibility and preconditions in this pinned local lab; impact described consequences to declared assets. Scores 1-4, 5-9, 10-16, and 17-25 were labeled Low, Medium, High, and Critical only after both axes were justified. The analysis consolidated repeated evidence into one finding per demonstrated consequence, kept negative categories out of the risk register, and reported exact ambiguity bounds instead of confidence intervals that the small, non-random case catalog could not support.

<!-- PAGE BREAK -->

## 4. Results

The complete replacement run had {{ADV_SUCCESS}} successes, {{ADV_FAILURE}} failures, {{ADV_AMBIG}} ambiguous outcomes, and {{ADV_ERROR}} errors among {{ADV_DEN}} adversarial workflows (Table 1; run {{RUN_ID}}). Primary ASR was {{ADV_SUCCESS}}/{{ADV_DEN}} ({{ADV_RATE}}). Excluding ambiguous outcomes yielded {{AMB_EXCL_NUM}}/{{AMB_EXCL_DEN}} ({{AMB_EXCL_RATE}}); treating all ambiguous outcomes as success yielded {{AMB_WORST_NUM}}/{{AMB_WORST_DEN}} ({{AMB_WORST_RATE}}). The outcome-enriched manual-review set had {{MANUAL_SUCCESS}}/{{MANUAL_DEN}} successes ({{MANUAL_RATE}}), which is not a population estimate.

[[TABLE:CATEGORY_OUTCOMES]]

[[FIGURE:CATEGORY_OUTCOMES]]

Direct prompt injection produced {{DPI_SUCCESS}}/{{DPI_DEN}} confirmed successes: role/authority, encoded, and multi-turn families were each 3/3, while explicit conflict produced 1/3 success and 2/3 ambiguous. The confirmed effect was transient emission of synthetic behavior markers, not protected-data disclosure or persistent state change. Indirect QR injection produced {{IPI_SUCCESS}}/{{IPI_DEN}} confirmed successes with one ambiguous instruction case. Information-disclosure cases produced {{DISC_SUCCESS}}/{{DISC_DEN}} successes; disclosure coverage was {{DISCLOSURE_SUCCESS}}/{{DISCLOSURE_DEN}} authorized simulated data classes across nine attempts. Negative results were retained rather than converted into security guarantees.

All {{POI_SUCCESS}}/{{POI_DEN}} nonzero poisoning workflows accepted the exact budget and met the frozen effect rule. The {{CLEAN_BASELINE_NUM}}/{{CLEAN_BASELINE_DEN}} clean baselines were each 4/4 accurate and had identical weight hashes. Each nonzero workflow reduced clean accuracy from 4/4 to 3/4, flipped 1/4 baseline-correct predictions, and changed the frozen target in the intended direction. Targeted budgets succeeded {{TARGETED_POI_NUM}}/{{TARGETED_POI_DEN}}; the broad budget-5 case also changed the target. This is material degradation at the preregistered 0.25 threshold, not total utility collapse.

All {{DETECTOR_REVIEWED}} reviewed labels agreed with automatic screening; automatic-success precision was {{AUTO_PRECISION_NUM}}/{{AUTO_PRECISION_DEN}}. The seeded failure sample observed {{FN_NUM}}/{{FN_DEN}} false negatives, but only {{FN_DEN}}/{{ELIGIBLE_FAILURES}} eligible failures were sampled, so full detector sensitivity is not estimable. Benign false-positive successes were {{BENIGN_SUCCESS}}/{{BENIGN_DEN}}, with {{BENIGN_AMBIG}} ambiguities.

<!-- PAGE BREAK -->

## 5. Discussion, OWASP Mapping, and Mitigations

Two consolidated findings avoid double-counting repeated trials. F-001, direct inputs bypass prompt-only behavior controls, was rated likelihood 4 and impact 2: score 8 (Medium). It reproduced {{DPI_SUCCESS}}/{{DPI_DEN}} times for an ordinary caller, but the demonstrated consequence was transient synthetic behavior with no protected-data or persistent-state effect. F-002, unapproved poisoning changes target and clean classifier utility, was rated likelihood 5 and impact 4: score 20 (Critical). All {{POI_SUCCESS}}/{{POI_DEN}} nonzero workflows accepted caller-controlled labels, changed the target, and degraded clean accuracy. These scores rank this pinned intentionally vulnerable lab only.

[[TABLE:OWASP_MAPPING]]

OWASP LLM01:2025 covers direct and indirect prompt injection where user or external content changes behavior in unintended ways [4]. F-001 therefore maps to LLM01. The negative QR cases remain LLM01 test coverage, not findings. OWASP LLM04:2025 treats manipulated training, fine-tuning, or embedding data as an integrity risk and recommends provenance, validation, versioning, monitoring, and robust testing [5]; F-002 maps to LLM04. Because no protected simulated data class was exposed and no system-context consequence met policy, the study did not promote LLM02 or LLM07 findings.

[[TABLE:MITIGATIONS]]

For F-001, authorization and security decisions must move outside model-visible instructions. The application should constrain available actions, apply least privilege, mark decoded/retrieved text as untrusted, canonicalize transformed input before policy evaluation, validate structured output, redact/alert on canary or DLP signals, and log repeated triggers without storing secrets. Prompt wording and keyword blacklists can support these controls but cannot independently close the chain. Regression should replay the frozen role, encoded, multi-turn, and conflict cases and require zero confirmed prohibited markers while preserving benign behavior.

For F-002, data submission, labeling, retraining, and promotion require authenticated least privilege and an auditable approval path. Immutable provenance plus duplicate, label-consistency, outlier, trigger, and per-source-influence checks should quarantine the frozen mislabeled samples before training. Promotion must fail when the clean holdout loses at least 1/4 accuracy or any baseline-correct item flips; datasets and models need signed versions, drift monitoring, and tested rollback to a clean 4/4 checkpoint. These are application, data, and model lifecycle controls rather than prompt-only mitigations.

The cross-category pattern is boundary failure: high-trust decisions were delegated to model-visible text or unauthenticated training routes. Conversely, the negative disclosure and QR results show why an intentionally vulnerable label or a detector signal cannot replace explicit consequence evidence.

Residual risk remains after each proposed control. Deterministic output and authorization checks can limit consequences even if the model still follows adversarial text, but they do not make prompt injection impossible. Provenance and promotion gates can reject the tested poison patterns, yet novel or colluding data sources may evade simple anomaly rules. The mitigation matrix therefore pairs preventive controls with detection, versioning, and recovery tests and treats prompt changes as defense-in-depth rather than a security boundary.

<!-- PAGE BREAK -->

## 6. Limitations, Future Work, and Conclusion

Construct validity is strongest for exact synthetic markers and structured poisoning metrics, but near matches remain ambiguous. The benign false-positive result of {{BENIGN_SUCCESS}}/{{BENIGN_DEN}} includes {{BENIGN_AMBIG}} RAG ambiguities, and the {{FN_DEN}}/{{ELIGIBLE_FAILURES}} sampled failures cannot establish sensitivity. The policy-defined markers test prohibited behavior, not general harmfulness.

Internal validity benefited from frozen commits/digests, exact artifacts, controlled state, zero silent retries, append-only evidence, and isolation of the stopped run. However, the application routes did not expose temperature or seed, so prompt nondeterminism remains. The shared clean RAG refresh has raw support evidence but no normalized latency record, and attack family is confounded with PwnzzAI stage.

Measurement units also differ by surface. Direct, QR, and disclosure latency rows represent single target requests, whereas a poisoning duration covers one train-plus-four-holdout workflow. These values were kept separate and were not used to rank security. The 79-request operational count therefore should not be mistaken for 79 independent adversarial outcomes, and the 43 workflow records include controls as well as attacks.

External validity is limited to one intentionally vulnerable local PwnzzAI deployment, one {{MODEL_PARAMETER_SIZE}} model, one host, synthetic values, and the frozen case catalog. Findings do not estimate production prevalence or transfer to other applications, models, languages, or deployment boundaries. Conclusion validity is limited by three prompt trials per case, one workflow per nonzero poison budget, and a four-item holdout. Exact counts and ambiguity bounds are therefore reported without inferential significance.

The absence of confirmed indirect or disclosure success is especially narrow. It covers the exact QR and RAG/system-context artifacts, policies, model, and repetitions retained here. Different document formats, retrieval corpora, languages, longer conversations, or higher-capability models may produce other results. Similarly, the poisoning study proves an authorization and integrity effect in a toy classifier workflow; it does not quantify poisoning feasibility for large-scale pretraining or persistent production model promotion.

Researcher bias also remains: cases, thresholds, and the review seed were frozen, but adjudication was completed by one Codex-assisted reviewer without independent second review. Codex also assisted report drafting and formatting. Numeric claims were regenerated from retained machine-readable evidence, model outputs are not quoted in the main text, and the archive includes a claim-evidence manifest; final human authors must still perform the submission review.

Future work should add an independent adjudicator, more repetitions, larger and multilingual holdouts, a second pinned model, and causal ablations that separate stage from attack family. After implementing the proposed controls, the same frozen corpus should be rerun as a regression suite, followed by bounded QR/RAG variants and authorization-negative tests. Any follow-up experiment requires a new versioned protocol and must remain separate from this headline run.

The next evaluation should preregister acceptance criteria for each mitigation: zero confirmed prohibited markers across the frozen direct families; ordinary-caller rejection before any training mutation; complete provenance/audit events; promotion failure for any 1/4 target flip or 1/4 clean-accuracy degradation; and verified rollback to the identical clean baseline. A second model and expanded holdout should be reported as a separate run group so that improved coverage does not overwrite the current result.

In conclusion, the research question is answered asymmetrically. Under the frozen policies, direct prompt inputs reproducibly bypassed prompt-only behavior constraints and ordinary callers could poison the classifier with a measurable target and clean-utility effect. The tested indirect and disclosure cases produced no confirmed success. The evidence supports deterministic application enforcement, training-path authorization, provenance, promotion gates, monitoring, and rollback; it does not support broad claims that PwnzzAI, its underlying model, or LLM applications generally are secure or insecure.

<!-- MAIN TEXT END -->

## References

[1] L. Derczynski, E. Galinkin, J. Martin, S. Majumdar, and N. Inie, "garak: A Framework for Security Probing Large Language Models," arXiv:2406.11036, 2024. https://arxiv.org/abs/2406.11036

[2] K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, and M. Fritz, "Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection," arXiv:2302.12173, 2023. https://arxiv.org/abs/2302.12173

[3] N. Carlini et al., "Poisoning Web-Scale Training Datasets is Practical," arXiv:2302.10149, 2023. https://arxiv.org/abs/2302.10149

[4] OWASP GenAI Security Project, "LLM01:2025 Prompt Injection," accessed July 25, 2026. https://genai.owasp.org/llmrisk/llm01-prompt-injection/

[5] OWASP GenAI Security Project, "LLM04:2025 Data and Model Poisoning," accessed July 25, 2026. https://genai.owasp.org/llmrisk/llm042025-data-and-model-poisoning/

[6] OWASP, "PwnzzAI," source commit {{PWNZZAI_COMMIT}}, accessed July 25, 2026. https://github.com/OWASP/PwnzzAI

[7] Ollama, "API Reference," accessed July 25, 2026. https://docs.ollama.com/api

<!-- APPENDICES GENERATED FROM RETAINED EVIDENCE -->

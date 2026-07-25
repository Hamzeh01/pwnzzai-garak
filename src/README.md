# Source Tree

Phase 4 implements benign harness and evidence plumbing only.

Current layout:

```text
src/
  adapters/   Verified HTTP/session/multipart and Garak scanner path
  probes/     Empty until later explicit authorization
  detectors/  Versioned interface and exact synthetic-signal detector
  analysis/   Redaction, raw evidence, JSONL, and normalization
```

No attack implementation is included. Stateful scenario orchestration remains
deferred until the Phase 5 protocol is frozen and approved.

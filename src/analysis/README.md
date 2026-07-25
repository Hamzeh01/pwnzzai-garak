# Analysis

Phase 4 evidence plumbing lives here:

- recursive header/body redaction
- immutable raw JSON evidence
- append-only structured event and normalized JSONL writers
- result-record normalization with explicit `retry_of` linkage

Phase 7 analysis is implemented in `phase07.py`. It:

- accepts only the complete protocol `1.1.1` replacement run
- verifies every normalized-to-raw SHA-256 link before analysis
- keeps automatic, manual, and adjudicated labels distinct
- reports exact four-way counts and numerator/denominator pairs
- generates stratified CSV tables, SVG figures, risk records, mitigations,
  and validity analysis without sending target requests
- records frozen input, code, and generated-artifact hashes in the Phase 7
  analysis manifest

Use `scripts/analyze_phase07.py` to regenerate outputs or add `--check` for a
read-only byte-for-byte reproducibility check.

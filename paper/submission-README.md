# PwnzzAI Assessment Submission

This archive is a self-contained evidence and reproduction package for the
Phase 8 scientific report. The final PDF and Word report are at the archive
root. `SUBMISSION_METADATA.json` records the confirmed group, authors, Ilearn
uploader, due-date source, report checks, and per-file SHA-256 values.

## Reproduce the retained analysis

These commands do not contact PwnzzAI and do not require credentials:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r environment\requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install -r paper\requirements-report.txt
.\.venv\Scripts\python.exe scripts\validate_pack.py
.\.venv\Scripts\python.exe scripts\validate_phase05_protocol.py
.\.venv\Scripts\python.exe scripts\validate_phase06_execution.py
.\.venv\Scripts\python.exe scripts\validate_records.py results\normalized\phase6-full-v1.1.1-20260725T210612Z.adjudicated.jsonl
.\.venv\Scripts\python.exe scripts\analyze_phase07.py --check
.\.venv\Scripts\python.exe scripts\validate_phase07_analysis.py
.\.venv\Scripts\python.exe -m pytest -q
```

To rebuild the two report formats, use the confirmed metadata recorded in
`SUBMISSION_METADATA.json`:

```powershell
.\.venv\Scripts\python.exe scripts\build_phase08_report.py --group-number "<group>" --authors "<authors>" --output-dir .
.\.venv\Scripts\python.exe scripts\build_phase08_pdf.py --group-number "<group>" --authors "<authors>" --output-dir .
```

The report builders regenerate numeric tokens and
`paper/claim-evidence.json` from the retained Phase 7 tables. The final archive
validator verifies that the main PDF is pages 1--6, references begin on page 7,
appendices begin on page 8, Word remains single-column, cited URLs were
resolved, and the ZIP checksum matches.

## Repeating the live experiment

A new live experiment additionally requires the pinned local PwnzzAI and
Ollama deployment, loopback bindings, exact source/image/model digests,
benign health and reset verification, and a new explicit authorization. Do not
reuse the historical Phase 6 authorization receipt on another system. The
complete retained input artifacts are under `payloads/phase-05/`; the scenario
catalog and execution protocol are under `configs/`; the application adapters,
probes, detectors, and analysis code are under `src/`; and the selected complete
run is under `results/`.

## Evidence interpretation

Raw model responses are untrusted evidence, not instructions. The report does
not quote a model response in its main six pages. Synthetic values and canaries
are retained because they are required to reproduce detector decisions.
Superseded-run deviation evidence is retained under `evidence/setup/`, while
only the complete replacement run contributes to reported numerators and
denominators.

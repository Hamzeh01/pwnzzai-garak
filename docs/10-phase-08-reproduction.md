# Phase 8 Report and Submission Reproduction

## Inputs and authority

The report builders use `paper/report-content.md` as the canonical prose source
and regenerate every numeric token from
`results/tables/phase-07-summary.json`,
`phase-07-stratified-outcomes.csv`, and the retained adjudicated JSONL. The
builders also regenerate `paper/claim-evidence.json`; the Phase 8 tests reject
a stale manifest or unresolved token.

The final author roster and group number are human identity inputs, not inferred
from repository paths or Git configuration. The designated Ilearn uploader and
due date must come from the team and Ilearn or a separate instructor
announcement.

## Build

Install the experiment and report dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r environment\requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install -r paper\requirements-report.txt
```

Build both formats from the same source:

```powershell
.\.venv\Scripts\python.exe scripts\build_phase08_report.py --group-number "<group>" --authors "<authors>" --output-dir dist\phase-08
.\.venv\Scripts\python.exe scripts\build_phase08_pdf.py --group-number "<group>" --authors "<authors>" --output-dir dist\phase-08
```

The PDF builder uses one Letter-sized frame, so the document is single-column.
Five explicit page breaks make pages 1--6 the main text. A separate break puts
references on page 7, and generated appendices begin on page 8. Full payloads,
QR artifacts, environment pins, extended tables, evidence indexes, reproduction
commands, and AI-assistance analysis are generated into the appendices.

## Validation and visual review

Before packaging, run the normal experiment and analysis checks:

```powershell
.\.venv\Scripts\python.exe scripts\validate_pack.py
.\.venv\Scripts\python.exe scripts\validate_phase06_execution.py
.\.venv\Scripts\python.exe scripts\validate_records.py results\normalized\phase6-full-v1.1.1-20260725T210612Z.adjudicated.jsonl
.\.venv\Scripts\python.exe scripts\analyze_phase07.py --check
.\.venv\Scripts\python.exe scripts\validate_phase07_analysis.py
.\.venv\Scripts\python.exe -m pytest -q
```

Render every PDF page with Poppler and inspect at readable scale. Confirm no
clipping, overlap, missing glyphs, broken tables, or misplaced main,
reference, or appendix content. `validate_phase08_submission.py` checks the PDF
page count and boundaries, Letter geometry, title metadata, numeric claims,
reference resolution record, absence of verbatim retained response strings in
main text, DOCX ZIP integrity, scrubbed Word author metadata, and single-column
section geometry.

On the producing host, LibreOffice was unavailable and unattended Microsoft
Word export did not pass Office startup. The authoritative PDF was therefore
rendered directly from the canonical source and inspected page by page. The
Word output was checked structurally with `python-docx`, direct OOXML/ZIP
inspection, the document skill's section/image/style audits, and an
accessibility audit. This limitation must remain in the Gate 8 review.

## Package

Create the archive only with confirmed submission metadata:

```powershell
.\.venv\Scripts\python.exe scripts\package_phase08_submission.py `
  --group-number "<group>" `
  --authors "<authors>" `
  --uploader "<one team member>" `
  --due-date "<confirmed due date and timezone>" `
  --due-date-source "<Ilearn URL or instructor announcement>" `
  --report-dir dist\phase-08 `
  --output-dir dist\phase-08
```

The packaging script uses an explicit allowlist, includes only the complete
replacement run, creates per-file SHA-256 values, rejects high-confidence
OpenAI/GitHub/AWS/private-key patterns and temp/credential paths, tests ZIP
integrity, and writes an external archive checksum and manifest. Validate the
finished artifacts with the same confirmed metadata:

```powershell
.\.venv\Scripts\python.exe scripts\validate_phase08_submission.py `
  --group-number "<group>" `
  --authors "<authors>" `
  --uploader "<one team member>" `
  --due-date "<confirmed due date and timezone>" `
  --due-date-source "<Ilearn URL or instructor announcement>" `
  --output-dir dist\phase-08
```

Packaging and validation do not upload anything. Only the designated team
member should upload the final ZIP to Ilearn.

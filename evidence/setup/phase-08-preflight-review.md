# Phase 8 Preflight Review

## Status

- Gate 7 prerequisite: PASSED (`evidence/setup/phase-07-gate-review.md`)
- Phase 8 report content: complete against retained Phase 7 evidence
- Gate 8: NOT RECORDED
- New target requests during Phase 8: 0
- Team-owned release inputs: confirmed group number, complete author roster,
  exactly one designated uploader, and due date plus Ilearn/instructor source

Temporary `G00` layout and packaging artifacts were deleted after validation.
They were never submission artifacts, and their obsolete checksum is not
retained or reported as a final archive checksum.

## Content and evidence checks

- The canonical `paper/report-content.md` contains five explicit page breaks
  before the main-text terminator, giving six pages of main text.
- References follow on page 7 and generated appendices begin on page 8.
- Numeric tokens are regenerated from the Phase 7 summary and stratified
  tables. `paper/claim-evidence.json` regenerates exactly.
- The main text includes explicit PI-01, SD-01, SP-01, and DI-01 policies;
  threat model and system boundary; four-way methods; exact denominators;
  negative and ambiguous results; application-layer mitigations; OWASP
  LLM01:2025 and LLM04:2025 mapping; limitations; future work; and conclusion.
- Related work connects the Garak, indirect-prompt-injection, and
  data-poisoning papers to the experimental design.
- Seven canonical reference pages were opened and resolved on 2026-07-25;
  details are in `paper/reference-verification.json`.
- The validator found no retained raw response string quoted verbatim in the
  main text. Appendix F analyzes and discloses Codex assistance.

## Format review

- Draft PDF: 18 Letter pages, single column.
- Main text: pages 1--6.
- References: page 7.
- Appendices: pages 8--18.
- All 18 PDF pages were rendered at 144 DPI with the bundled native Poppler
  executable and visually inspected. No clipping, overlap, broken glyph,
  unreadable table, or misplaced section was observed.
- The reference page was rebuilt left-aligned and visually rechecked.
- DOCX ZIP/OOXML integrity, Letter portrait geometry, one-column section,
  report content, group/author fields, and scrubbed creator metadata passed.
- The document accessibility audit reported 0 high, 0 medium, and 0 low
  findings after table-header and image-alt metadata were added.
- LibreOffice is not installed. Unattended Microsoft Word PDF export stalled
  at Office startup, so no visual Word render is claimed. The authoritative
  PDF was generated from the same canonical report source, while Word received
  structural, content, metadata, section, image, style, and accessibility
  checks.

## Draft packaging validation

The allowlisted draft archive passed:

- selected complete replacement run inclusion
- scripts, datasets, configuration, schemas, tests, environment pins, and
  explanatory reproduction material inclusion
- per-member SHA-256 verification
- ZIP integrity
- high-confidence OpenAI/GitHub/AWS/private-key scan
- credential/temp/path exclusions
- PDF/Word name and content checks

The release workflow was exercised with explicit non-submission QA metadata.
The disposable archive was then removed. The team will provide the final
identity, Ilearn due-date, and uploader fields when it performs the release
build.

## Commands

```powershell
.\.venv\Scripts\python.exe scripts\validate_pack.py
.\.venv\Scripts\python.exe scripts\validate_phase05_protocol.py
.\.venv\Scripts\python.exe scripts\validate_phase06_execution.py
.\.venv\Scripts\python.exe scripts\validate_records.py results\normalized\phase6-full-v1.1.1-20260725T210612Z.adjudicated.jsonl
.\.venv\Scripts\python.exe scripts\analyze_phase07.py --check
.\.venv\Scripts\python.exe scripts\validate_phase07_analysis.py
.\.venv\Scripts\python.exe -m pytest -q
```

Result: 52 tests passed; every listed validator passed.

## Gate decision

Gate 8 remains unrecorded at this source-handoff point. The report, builders,
tests, and release validation are ready to commit and push. The team will
perform the final metadata-specific export, archive scan/checksum, Ilearn
deadline check, uploader designation, and Gate 8 recording.

# Paper Workspace

`report-content.md` is the canonical evidence-backed report source.
`build_phase08_report.py` and `build_phase08_pdf.py` render Word and PDF from
that same source and regenerate numeric tokens from the retained Phase 7
summary. `claim-evidence.json` records the regeneration sources.

Install the pinned report dependencies from `requirements-report.txt`. Build
with a confirmed group number and author roster:

```powershell
python scripts\build_phase08_report.py --group-number "<group>" --authors "<authors>"
python scripts\build_phase08_pdf.py --group-number "<group>" --authors "<authors>"
```

The final PDF must be rendered and visually inspected page by page. The Phase 8
validator also checks page boundaries, references, Word OOXML structure,
archive contents, hashes, and secret/temp-file exclusions.

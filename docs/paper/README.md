# Paper draft (English)

Single-column IEEEtran LaTeX draft covering **Architecture, Methodology,
Results, and Discussion**. Front matter (abstract, introduction, related work,
conclusion) is deliberately left as placeholders in `paper.tex`.

Builds clean: 24 pages, no errors, no overfull boxes. The 23 remaining log
warnings are cosmetic Courier font-shape substitutions in small-caps table
captions, which LaTeX resolves automatically.

The Persian edition (`paper-fa.tex`, `README-fa.md`) is a separate document in
this same directory and shares the rendered figures.

## Layout

```
paper.tex                     IEEEtran main file; \input's the four sections
sections/architecture.tex     Sec. II  -- plugins, generators, detectors, notes channel
sections/methodology.tex      Sec. III -- target, task model, design, controls, metrics
sections/results.tex          Sec. IV  -- all measurements
sections/discussion.tex       Sec. V   -- interpretation, mitigations, limitations
refs.bib                      two stub entries; VERIFY before submission
figures/*.mmd                 four Mermaid diagrams authored for the paper
figures/*.pdf                 rendered figures (tracked, so LaTeX alone can build)
figures/svg_to_pdf.py         svglib/ReportLab SVG -> PDF converter
figures/build-figures.{sh,ps1}  renders .mmd -> .pdf and analysis .svg -> .pdf
```

## Why single-column

The results tables are wide and dense. In two-column mode every one of them
became a full-width `table*` float, LaTeX deferred them in long runs, and they
piled up against each other. One column with column widths expressed as
fractions of `\textwidth` (the `\tw` macro) fixes it structurally: a table
cannot exceed the measure regardless of page size.

Two related mechanics worth knowing before editing:

- **`\bk`** is a zero-width break opportunity. Courier carries no hyphenation
  patterns, and neither `[T1]{fontenc}` nor `hyphenat[htt]` persuades it to
  break, so long identifiers get explicit break points at CamelCase humps and
  after `.` `/` `_` `-`. Without them `\code{PoisonedRetrievalInfluence}` runs
  straight out of its cell.
- **`\safefig[width-fraction]{path}`** caps height at `0.85\textheight` and
  keeps the aspect ratio, so a tall diagram can never run off the page. Widths
  are set per figure from each PDF's measured aspect ratio.

## Building

```bash
bash docs/paper/figures/build-figures.sh   # or: pwsh figures/build-figures.ps1
latexmk -pdf docs/paper/paper.tex
```

On Windows, the configured build uses MiKTeX and LaTeX Workshop. Generate the
figures from the repository root with:

```powershell
.\.venv\Scripts\python.exe -m pip install svglib
npm install --prefix D:\Programs\MermaidCLI `
  @mermaid-js/mermaid-cli@11.16.0
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\docs\paper\figures\build-figures.ps1
```

The PowerShell builder uses `npx` plus the installed Google Chrome for Mermaid
and `svglib`/ReportLab for the analysis SVGs. It skips figures that are already
newer than their sources and returns a nonzero exit code if any conversion
fails.

`\safefig` draws a labelled placeholder box for any figure that has not been
rendered yet, so the draft compiles and reads before the figures exist. The
rendered figure PDFs are tracked, so a plain `latexmk -pdf paper.tex` with no
Node or Chrome available still produces the complete document.

## Figures

| Figure | Source | Origin |
|---|---|---|
| Fig. 1 component architecture | `figures/fig-architecture.mmd` | new |
| Fig. 2 attempt lifecycle | `figures/fig-attempt-lifecycle.mmd` | new |
| Fig. 3 experimental controls | `figures/fig-controls.mmd` | new |
| Fig. 4 defence layers vs techniques | `figures/fig-defence-layers.mmd` | new |
| Fig. 5 direct-injection levels | `garak_analysis/figures/direct-levels.svg` | existing |
| Fig. 6 guardrail ladder | `garak_analysis/figures/guardrail-ladder.svg` | existing |
| Fig. 7 sentiment flip rate | `garak_analysis/figures/sentiment-flip-rate.svg` | existing |
| Fig. 8 sentiment confidence | `garak_analysis/figures/sentiment-confidence.svg` | existing |
| Fig. 9 catering mitigation | `garak_analysis/figures/catering-mitigation.svg` | existing |

`owasp-attack-success.svg` exists but is not referenced; Table I in the results
section carries the same information more precisely.

## Provenance of every number

Tables that restate committed artifacts:

| Table | Source file |
|---|---|
| Rollup by family / OWASP | `garak_analysis/summary.json`, `family-summary.csv`, `owasp-summary.csv` |
| Per-detector totals | `garak_analysis/eval-by-detector.csv` (summed over tasks) |
| Guardrail ladder per stage | `garak_analysis/eval-by-detector.csv` |
| Information-disclosure tasks | `garak_analysis/task-summary.csv` |
| Sentiment dose-response | `garak_analysis/sentiment-doseresponse.csv` |
| Detector agreement | `garak_analysis/detector-agreement.csv` |
| Mitigations | `garak_analysis/mitigations.csv`, revised — see below |

Tables derived by re-aggregating `attempts.csv` (these are **new** analyses, not
present in `garak_analysis/`):

- **Technique × level matrix** — per-prompt hits grouped by persona level.
- **Ladder per-technique totals** — per-prompt hits summed across all ten stages.
- **QR per-payload hits**, **PII per-prompt hits**, **system-prompt probe
  breakdown** — per-prompt aggregation within a task.
- **Leak-rendering distribution** — counts of the `leak_rendering` note.
- **Catering retrieval-level vs answer-level** — cross-tabulation of
  `untrusted_in_retrieval` against detector hits and query content, read from
  `garak_runs/data-poisoning/catering-poison-*.report.jsonl`.

If these are worth keeping, they belong in `garak_pwnzz/analysis/analyze.py` so
they regenerate with everything else. Right now they exist only in the paper.

## Two places the draft departs from `docs/05-results-and-mitigations.md`

Both are corrections supported by the raw reports, not rewordings.

1. **The catering mitigation.** `docs/05` says trusted-only retrieval "reduces
   but does not eliminate the influence". The report data shows
   `untrusted_in_retrieval == false` on **all 12** hardened attempts — the
   mitigation was fully effective at the retrieval stage. The residual 0.417
   detector rate is 4 hits on queries that themselves contain "pineapple" or
   "anchovy paste" (one inside an explicit refusal) plus one 0.5 soft-marker
   score. The draft reports this as a detector false-positive class and revises
   M-08 accordingly.

2. **Output-filter stages.** `docs/05` says leaks at B5/B9 surface as
   `CouponSuppressed` or as obfuscated `CouponLeak` hits. Measured: B5 is
   0/0/0 and B9 has exactly one `CouponSuppressed` hit and no leaks. The twelve
   obfuscated renderings in the study occur at *other* stages and in the direct
   suite. The draft states the measured distribution.

One further honest note carried into the discussion: the `CouponLeak`
whitespace-stripped branch matches without word boundaries. It correctly caught
a genuine leak rendered as the plural "Mushrooms!" and also fired once on the
invented word "MOONCHEESE". One of the 97 recorded leaks is attributable to
this.

## Known gaps

- `refs.bib` entries were written from memory and are marked `VERIFY`.
- The draft cites no external work with `\cite{}` yet; the two entries are for
  the front-matter pass.
- Author block in `paper.tex` is a placeholder.

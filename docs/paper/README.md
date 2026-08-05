# Paper draft (English)

Single-column IEEEtran LaTeX draft, complete front to back: **abstract,
introduction, related work, architecture, methodology, results, ablation study,
discussion, conclusion, references**.

Builds clean: 33 pages, 18 tables, 9 figures, 27 references, no errors, no
overfull or underfull boxes, no undefined citations or references. The
remaining log warnings are cosmetic Courier font-shape substitutions in
small-caps table captions, which LaTeX resolves automatically.

The Persian edition (`paper-fa.tex`, `README-fa.md`) is a separate document in
this same directory and shares the rendered figures. It was not touched by the
front-matter/ablation pass.

## Layout

```
paper.tex                     IEEEtran main file; preamble, table style, front matter
sections/introduction.tex     Sec. I    -- problem, detection gap, contributions
sections/related.tex          Sec. II   -- injection, frameworks, poisoning, taxonomies
sections/architecture.tex     Sec. III  -- plugins, generators, detectors, notes channel
sections/methodology.tex      Sec. IV   -- target, task model, design, controls, metrics
sections/results.tex          Sec. V    -- all measurements
sections/ablation.tex         Sec. VI   -- defence + measurement-apparatus ablations
sections/discussion.tex       Sec. VII  -- interpretation, mitigations, limitations
sections/conclusion.tex       Sec. VIII -- summary and future work
refs.bib                      27 entries; ALL UNVERIFIED -- see "Known gaps"
figures/*.mmd                 four Mermaid diagrams authored for the paper
figures/build-figures.{sh,ps1}  renders .mmd -> .pdf and analysis .svg -> .pdf
```

## Building

```bash
bash docs/paper/figures/build-figures.sh
cd docs/paper
latexmk -pdf paper.tex
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

Both builders generate only the nine figures referenced by the paper. The
PowerShell builder uses `npx` plus the installed Google Chrome for Mermaid and
`svglib`/ReportLab for the analysis SVGs. It skips figures that are already
newer than their sources. Both builders return a nonzero exit code if a
required conversion fails.

### If `latexmk` is unavailable

This MiKTeX install has no Perl, so `latexmk` cannot run. Drive the passes by
hand from `docs/paper/` — the bibliography now needs a real BibTeX pass:

```bash
pdflatex -interaction=nonstopmode paper.tex && bibtex paper && pdflatex -interaction=nonstopmode paper.tex && pdflatex -interaction=nonstopmode paper.tex
```

Build **in** `docs/paper/`, not with `-output-directory=build`. A stale
`paper.aux` in the source directory shadows the one in `build/`, and every
citation silently comes out as `[?]`.

`paper.tex` defines `\safefig`, which draws a labelled placeholder box for any
figure that has not been rendered yet, so the draft compiles and reads before
the figures exist.

## Table style

The preamble defines one visual grammar used by every table, so a wide row
stays traceable across the measure:

| Macro | Purpose |
|---|---|
| `\zebra` | issued immediately before `\begin{tabular}`; light alternating row bands |
| `\headrow` | tinted header band; goes first in the header row |
| `\grouprow` | stronger tint for group-header and total rows |
| `\tabhead{}` / `\grouplabel{}` / `\totlabel{}` | header, group-label, total-label ink |
| `\hi{}` / `\lo{}` | worst / best value in a block — bold *and* coloured, so it survives greyscale |
| `\asrbar{0.472}` | proportional bar on a common `[0,1]` scale, in its own `l` column |
| `\code{}`, `\bk`, `\tw{}` | monospace identifiers, zero-width break points, `\textwidth`-relative widths |

Tables with footnotes use `threeparttable` + `\tnote{}`, so notes align to the
tabular rather than to the text block. `\aboverulesep` and `\belowrulesep` are
zeroed and paid back through `\extrarowheight`; without that, booktabs rules
leave an uncoloured gap through every band.

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

### The ablation tables (Sec. VI)

**Table XVI (defence ablations)** re-presents numbers already in Sec. V —
per-task rates from `task-summary.csv` plus the catering and dose-response data
— with a Δ column computed against the reference row of each block. No new data.

**Table XVII (measurement-apparatus ablations)** contains arithmetic
counterfactuals, each computed exactly from retained per-attempt records rather
than estimated:

| Row | Derivation |
|---|---|
| Ground-truth channel removed | `CouponLeak` evaluated 546 attempts; with no secret in notes it abstains on all of them |
| Stock detector as verdict | 61 → 208 hits on the n=219 subset; `summary.json` `ground_truth_vs_stock` = agree 72 / disagree 147 |
| Cache reset removed | 5×L1 = 85/180 = 0.472 vs measured 49/180 = 0.272; 10×B0 = 40/330 = 0.121 vs measured 36/330 = 0.109 |
| Obfuscation branches removed | 97 − 9 − 3 = 85 leaks; 85/546 = 0.156 vs 97/546 = 0.178 |
| App oracle consumed | order-assistant surface: flag fires 16/21 = 0.762; `CrossTenantFlag` measured 0/21 |
| Whitespace branch removed | 97 − 3 = 94; 94/546 = 0.172 |
| Paired control / abstention / QR integrity | no change — verified against `sentiment-doseresponse.csv` (control label negative at every budget), `summary.json` (`nones` = 0 everywhere), and the QR report (21/21 round-tripped) |

Table XV also now reports derived precision/recall: stock detector
61/208 = 0.293, application oracle 26/45 = 0.578, both at recall 1.000.

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

- **`refs.bib` is unverified.** All 27 entries were written from memory —
  author lists, venues, years and arXiv identifiers included. Every field must
  be checked against the canonical record before this draft goes anywhere.
  Fields were deliberately kept minimal (author / title / venue / year) to
  reduce the surface area; add DOIs, page numbers and publishers during
  verification.
- Author block in `paper.tex` is a placeholder.
- The derived tables listed above live only in the paper, not in
  `garak_pwnzz/analysis/analyze.py`.
- Model scale is the one ablation the study does not have. The suite is
  parameterised for it but was only ever run against `llama3.2:1b`; Sec. VI-A
  says so explicitly rather than leaving it implied.

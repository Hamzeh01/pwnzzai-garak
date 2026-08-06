# Bilingual LaTeX paper

*فارسی: [README-fa.md](README-fa.md)*

Two editions of the same study. Both are complete front to back: abstract,
introduction, related work, architecture, methodology, results, ablation study,
discussion, conclusion.

- **English (`en/`)** — 18 pages, single-column IEEEtran 10pt, BibTeX, 10
  references, 15 tables, 5 figures. Authors: Mohammad Mahdi Shahriyar, Hossein
  Hamzehzadeh, Kimia Omrani.
- **Persian (`fa/`)** — 21 pages, XePersian on `article` with a literal RTL-safe
  bibliography. Section for section, table for table, figure for figure, and
  number for number, it is the same paper: the same 15 tables, the same 5
  figures, the same 10 references, the same authors. Persian runs longer at the
  same content, which is the whole of the three-page difference.

Source, generated figures, temporary build files, and release PDFs are kept in
separate directories.

## Layout

```
README.md, README-fa.md       this guide, English and Persian
build.ps1, build.sh           reproducible bilingual paper builders
en/main.tex                   English main file and front matter
en/sections/                  English section sources
en/references.bib             canonical-source-checked BibTeX database
fa/main.tex                   Persian main file and front matter
fa/sections/                  Persian section sources and literal bibliography
fa/fonts.conf                 Windows fontconfig search path for XeTeX
figures/source/               authored Mermaid diagram sources
figures/generated/            rendered vector PDFs shared by both editions
figures/scripts/              cross-platform figure builders
build/                        ignored LaTeX intermediates
output/paper-en.pdf           final English PDF
output/paper-fa.pdf           final Persian PDF
```

## Building

```powershell
.\docs\paper\build.ps1
```

```bash
bash docs/paper/build.sh
```

Both builders accept `en`, `fa`, or `all` (the default). They place every
auxiliary file under `build/{en,fa}/` and copy only the final PDFs to `output/`.
The English path runs `pdflatex`, BibTeX, then two `pdflatex` passes. The Persian
path runs XeLaTeX twice and sets `FONTCONFIG_FILE` automatically on Windows.

Both builders fail with a nonzero exit code if any layout or reference warning
survives the final pass — overfull or underfull boxes, undefined references or
citations, or `Label(s) may have changed` — and the English path additionally
fails on any BibTeX `Warning--`. A successful build therefore means a clean log,
not merely a PDF. Neither edition's PDF is copied to `output/` unless its gate
passes, so a stale `output/` PDF means the last build was rejected.

Generate or refresh the shared figures separately:

```powershell
.\.venv\Scripts\python.exe -m pip install svglib
npm install --prefix D:\Programs\MermaidCLI `
  @mermaid-js/mermaid-cli@11.16.0
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\docs\paper\figures\scripts\build-figures.ps1
```

The builder renders every Mermaid source and the analysis SVGs, skipping figures
newer than their sources, and returns nonzero if a conversion fails. Both main
files define `\safefig`, which draws a labelled placeholder if a generated figure
is temporarily unavailable.

## What changed in the condensed English edition

Driven by a page target; nothing was dropped that is not restated in the text.

**Length.** 33 pages → 18. The prose is roughly a third of its former length,
with every claim, number, and caveat retained; captions are set one size down;
tables are `\scriptsize` with `\arraystretch` 1.0; `\linespread` is 0.97 and the
text block is 0.72–0.75 in from the trim.

**Content.** Added Sec. III-F on the LLM-as-a-judge — the suite's most recent
component — with Table V, its schema-order calibration measured on a stratified
46-attempt sample. `fig-architecture.mmd` gained the opt-in judge path. The
detector table gained a `pwnzz_judge.AttackSuccess` row. Added Table VIII
(provenance), which maps each part of the paper to the artefact or document it
derives from.

**Removed floats** (all fully restated in prose, verbatim numbers preserved):

| Removed | Where its content now lives |
|---|---|
| Fig. sentiment flip rate | flip-rate row of the dose-response table |
| Fig. catering mitigation | the catering off/on table |
| Fig. experimental controls | the four labelled control paragraphs in Sec. IV-D |
| Fig. guardrail ladder chart | the `CouponLeak` column of the ladder table |
| Table per-detector totals | the two rates quoted in Sec. V-A |
| Table ladder per-technique | the ranking sentence in Sec. V-C |
| Table leak-rendering distribution | the rendering sentence in Sec. V-C |
| Table information-disclosure tasks | the four rates in the opening of Sec. V-E |
| Table QR per-payload hits | the payload paragraph in Sec. V-D |

## What changed in the Persian edition

It was brought in line with the condensed English one: every section retranslated
from the current English source, the float set cut from 9 figures and 21 tables
to the same 5 and 15, Sec. 3.6 on the LLM-as-a-judge and the provenance table
added, the authors named, and the bibliography cut from 27 entries to the same
10 — the survey citations went with the prose that leaned on them.

The other half was typographic. The earlier Persian edition carried decoration
the English one never had: navy headings with a rule under each section, a tinted
panel around the abstract, a coloured running head, coloured caption labels. None
of it encoded anything, and Persian bold is optically heavier than Latin bold, so
the same amount of emphasis reads louder in this script. All of it is gone.
Colour now appears only inside tables, under exactly the English edition's rules
— tinted header band, zebra banding, `\hi`/`\lo` on the extreme value of a block,
proportional rate bars — so a reader can hold the two PDFs side by side and see
one visual grammar.

Three RTL-specific corrections came out of reading the built pages rather than
the source, and each is commented where it was made: a Latin run whose
punctuation is a bidi neutral (`/api/...(+ /reset, /upload-doc)`, a list of eight
CSV filenames, `0.121/0.333/0.061/0.030`, `output < input < prompt`) has to sit
inside **one** `\lr`, or the algorithm attaches the separator to the wrong side
and can reverse the series; a bibliography entry has to be one `\lr` covering the
note as well, or the Persian half lands in the middle of a wrapped English title;
and `\begin{LTR}` is not a substitute for `\lr`, because it flips the direction
without switching the font, which prints ASCII commas as Persian ones.

## Figures (5)

| Figure | Source | Origin |
|---|---|---|
| Fig. 1 component architecture | `figures/source/fig-architecture.mmd` | updated — judge path added |
| Fig. 2 attempt lifecycle | `figures/source/fig-attempt-lifecycle.mmd` | unchanged |
| Fig. 3 direct-injection levels | `garak_analysis/figures/direct-levels.svg` | unchanged |
| Fig. 4 sentiment confidence | `garak_analysis/figures/sentiment-confidence.svg` | unchanged |
| Fig. 5 defence layers vs techniques | `figures/source/fig-defence-layers.mmd` | unchanged |

`fig-controls.mmd`, `guardrail-ladder.svg`, `sentiment-flip-rate.svg` and
`catering-mitigation.svg` are still built by the figure builder but are now
cited by neither edition; the Persian edition dropped them when it was
condensed to match. They are kept because they are cheap to build and their
content is quoted in the prose of both editions.

## References

**10 entries, and the scope is a deliberate rule: cite only what we hold and have
read in full.** Nothing is cited from a title or an abstract. The earlier draft
carried 27 survey-style references to work we had not read; those were removed
rather than left standing.

**Two external papers.**

- *Greshake et al., "Not what you've signed up for" (AISec 2023)* — read in the
  extended arXiv version, 2302.12173v2, which is what our section locators refer
  to. Cited for four specific things rather than in passing: retrieved untrusted
  content being analogous to arbitrary code, and the absent data/instruction
  boundary (`Sec. 2`), used in the introduction and the layers discussion; the
  injection-method taxonomy and its hidden multi-modal class, which is what the
  QR upload surface instantiates (`Sec. 3.1`); the threat taxonomy, which is what
  separates a text-level success from server-side execution (`Sec. 3.2`); and the
  observation that retrieval opens a path where input filtering is often not
  applied (`Sec. 3`), which the guardrail ladder turns into a measurement.
- *Bowen et al., "Scaling Trends for Data Poisoning in LLMs" (AAAI-25)* — cited
  for the three threat models and the ≤2 % poison fractions (`Sec. 3–4`), the
  learned-vulnerability-score metric (`Sec. 5.3`), the frontier-model and
  moderation-bypass results (`Sec. 6`, `6.1`), and above all the scaling
  regression (`Table 2`) with its one dissenting series (`Table 3`). That last
  result is load-bearing against us: it is why the 1B lower bound cannot be read
  as reassuring, and it is cited at each of the four places that claim depends on
  — related work, the poisoning discussion, the ablation's statement of what it
  cannot vary, and the limitations and future work.

**Eight project entries** — `pwnzzrepo` for the suite and its committed run
artefacts, plus one per document (`00-overview` … `06-manual-testing`). These are
cited where the paper restates them, and the provenance table (Sec. IV) maps
sections to sources so a reader can tell which material is restated from a
document, which is re-aggregated from committed artefacts, and which is new here.

**Tools and taxonomies are named, not cited.** Garak and the OWASP LLM Top 10 are
artefacts the study *uses*, not works whose claims it leans on, so each is named
at first use with its address in a footnote and carries no bibliography entry.
Two claims that the earlier draft attributed to Garak's paper — that automatic
failure detection is the hard part, and that it depends on the deploying
organisation's intent — are now stated as this study's own position, which is
where the evidence for them in this paper actually comes from.

Related work was rewritten accordingly and renamed **Positioning**: two
subsections that engage the two papers in detail, and a third stating the gap
between them that this study occupies. It does not survey the field, and says so.

## Table style

The preamble defines one visual grammar used by every table, so a wide row stays
traceable across the measure:

| Macro | Purpose |
|---|---|
| `\zebra` | issued immediately before `\begin{tabular}`; light alternating row bands |
| `\headrow` | tinted header band; goes first in the header row |
| `\grouprow` | stronger tint for group-header and total rows |
| `\tabhead{}` / `\grouplabel{}` / `\totlabel{}` | header, group-label, total-label ink |
| `\hi{}` / `\lo{}` | worst / best value in a block — bold *and* coloured, so it survives greyscale |
| `\asrbar{0.472}` | proportional bar on a common `[0,1]` scale, in its own `l` column |
| `\code{}`, `\bk`, `\tw{}` | monospace identifiers, zero-width break points, `\textwidth`-relative widths |

Tables with footnotes use `threeparttable` + `\tnote{}`. `\aboverulesep` and
`\belowrulesep` are zeroed and paid back through `\extrarowheight`; without that,
booktabs rules leave an uncoloured gap through every band.

## Provenance of every number

Tables that restate committed artifacts:

| Table | Source file |
|---|---|
| Rollup by family / OWASP | `garak_analysis/summary.json`, `family-summary.csv`, `owasp-summary.csv` |
| Guardrail ladder per stage | `garak_analysis/eval-by-detector.csv` |
| Sentiment dose-response | `garak_analysis/sentiment-doseresponse.csv` |
| Detector agreement | `garak_analysis/detector-agreement.csv` |
| Mitigations | `garak_analysis/mitigations.csv`, revised — see below |

Tables and per-prompt figures derived by re-aggregating `attempts.csv` (these are
**new** analyses, not present in `garak_analysis/`): the technique × level matrix,
the ladder per-technique totals, the QR per-payload hits, the system-prompt probe
breakdown, the leak-rendering distribution, and the catering retrieval-level vs
answer-level cross-tabulation. If these are worth keeping, they belong in
`garak_pwnzz/analysis/analyze.py` so they regenerate with everything else. Right
now they exist only in the paper.

The judge calibration in Table V comes from `docs/02-methodology.md` and the
docstring of `garak_pwnzz/judge/schema.py`; it is a measurement on a stratified
46-attempt sample, not a committed analysis artifact.

### The ablation tables (Sec. VI)

**Defence ablations** re-present numbers already in Sec. V — per-task rates from
`task-summary.csv` plus the catering and dose-response data — with a Δ column
computed against each block's reference row. No new data.

**Measurement-apparatus ablations** contain arithmetic counterfactuals, each
computed exactly from retained per-attempt records rather than estimated:

| Row | Derivation |
|---|---|
| Ground-truth channel removed | `CouponLeak` evaluated 546 attempts; with no secret in notes it abstains on all of them |
| Stock detector as verdict | 61 → 208 hits on the n=219 subset; `summary.json` `ground_truth_vs_stock` = agree 72 / disagree 147 |
| Cache reset removed | 5×L1 = 85/180 = 0.472 vs measured 49/180 = 0.272; 10×B0 = 40/330 = 0.121 vs measured 36/330 = 0.109 |
| Obfuscation branches removed | 97 − 9 − 3 = 85 leaks; 85/546 = 0.156 vs 97/546 = 0.178 |
| App oracle consumed | order-assistant surface: flag fires 16/21 = 0.762; `CrossTenantFlag` measured 0/21 |
| Whitespace branch removed | 97 − 3 = 94; 94/546 = 0.172 |
| Paired control / abstention / QR integrity | no change — verified against `sentiment-doseresponse.csv` (control label negative at every budget), `summary.json` (`nones` = 0 everywhere), and the QR report (21/21 round-tripped) |

The agreement table also reports derived precision/recall: stock detector
61/208 = 0.293, application oracle 26/45 = 0.578, both at recall 1.000.

## Two places the draft departs from `docs/05-results-and-mitigations.md`

Both are corrections supported by the raw reports, not rewordings, and both are
flagged in the text at the point they arise.

1. **The catering mitigation.** `docs/05` says trusted-only retrieval "reduces
   but does not eliminate the influence". The report data shows
   `untrusted_in_retrieval == false` on **all 12** hardened attempts — the
   mitigation was fully effective at the retrieval stage. The residual 0.417
   detector rate is 4 hits on queries that themselves contain "pineapple" or
   "anchovy paste" (one inside an explicit refusal) plus one 0.5 soft-marker
   score. The draft reports this as a detector false-positive class and revises
   M-08 accordingly.

2. **Output-filter stages.** `docs/05` says leaks at B5/B9 surface as
   `CouponSuppressed` or as obfuscated `CouponLeak` hits. Measured: B5 is 0/0/0
   and B9 has exactly one `CouponSuppressed` hit and no leaks. The twelve
   obfuscated renderings in the study occur at *other* stages and in the direct
   suite. The draft states the measured distribution.

One further honest note carried into the discussion: the `CouponLeak`
whitespace-stripped branch matches without word boundaries. It correctly caught a
genuine leak rendered as the plural "Mushrooms!" and also fired on the invented
word "MOONCHEESE". One of the 97 recorded leaks is attributable to this.

## Maintenance notes

- The derived tables listed above live only in the paper, not in
  `garak_pwnzz/analysis/analyze.py`.
- Model scale is the one ablation the study does not have. The suite is
  parameterised for it but was only ever run against `llama3.2:1b`; Sec. VI says
  so explicitly, and now cites the evidence that the trend runs against
  defenders.
- The two editions are kept in step by hand. A change to a number, a table, or a
  claim has to be made twice; `fa/sections/references.tex` is the literal twin of
  `en/references.bib` and drifts silently if only one is edited.

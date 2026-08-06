#!/usr/bin/env bash
# Render every figure the paper needs into figures/generated/.
#
#   1. Mermaid sources (*.mmd, authored here)  ->  *.pdf   via mermaid-cli
#   2. Analysis charts (garak_analysis/figures/*.svg)  ->  *.pdf  via an SVG converter
#
# Requirements (any one of the SVG converters is enough):
#   node/npx           for  npx -y @mermaid-js/mermaid-cli
#   rsvg-convert  OR  inkscape  OR  python -m cairosvg
#
# Nothing here is required to read the papers: each main file draws a labelled
# placeholder for any figure that has not been built.

set -uo pipefail
cd "$(dirname "$0")"

SOURCE_DIR="../source"
OUTPUT_DIR="../generated"
ANALYSIS_FIGS="../../../../garak_analysis/figures"
fail=0

# --------------------------------------------------------------------
# 1. Mermaid -> PDF
# --------------------------------------------------------------------
if command -v npx >/dev/null 2>&1; then
  for src in "$SOURCE_DIR"/*.mmd; do
    [ -e "$src" ] || continue
    name="$(basename "${src%.mmd}")"
    out="$OUTPUT_DIR/$name.pdf"
    echo "mermaid: $(basename "$src") -> $(basename "$out")"
    npx -y @mermaid-js/mermaid-cli -i "$src" -o "$out" \
        --pdfFit --backgroundColor white || { echo "  FAILED"; fail=1; }
  done
else
  echo "SKIP: npx not found; cannot render Mermaid diagrams." >&2
  fail=1
fi

# --------------------------------------------------------------------
# 2. SVG -> PDF
# --------------------------------------------------------------------
svg2pdf() {
  local in="$1" out="$2"
  if command -v rsvg-convert >/dev/null 2>&1; then
    rsvg-convert -f pdf -o "$out" "$in"
  elif command -v inkscape >/dev/null 2>&1; then
    inkscape "$in" --export-type=pdf --export-filename="$out"
  elif python -c "import cairosvg" >/dev/null 2>&1; then
    python -c "import cairosvg,sys; cairosvg.svg2pdf(url=sys.argv[1], write_to=sys.argv[2])" "$in" "$out"
  else
    return 127
  fi
}

if [ -d "$ANALYSIS_FIGS" ]; then
  for chart in \
    direct-levels \
    guardrail-ladder \
    sentiment-flip-rate \
    sentiment-confidence \
    catering-mitigation; do
    src="$ANALYSIS_FIGS/$chart.svg"
    if [ ! -e "$src" ]; then
      echo "MISSING: $src" >&2
      fail=1
      continue
    fi
    out="$OUTPUT_DIR/$chart.pdf"
    echo "svg:     $(basename "$src") -> $out"
    svg2pdf "$src" "$out"
    rc=$?
    if [ "$rc" -eq 127 ]; then
      echo "SKIP: no SVG converter (rsvg-convert / inkscape / cairosvg)." >&2
      fail=1
      break
    elif [ "$rc" -ne 0 ]; then
      echo "  FAILED"; fail=1
    fi
  done
else
  echo "SKIP: $ANALYSIS_FIGS not found; run 'python -m garak_pwnzz analyze' first." >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo
  echo "Some figures were not built. The papers will show placeholders for those."
fi
exit "$fail"

#!/usr/bin/env bash
set -euo pipefail

language="${1:-all}"
case "$language" in
  all|en|fa) ;;
  *) echo "usage: $0 [all|en|fa]" >&2; exit 2 ;;
esac

paper_root="$(cd "$(dirname "$0")" && pwd)"
build_root="$paper_root/build"
output_root="$paper_root/output"
mkdir -p "$build_root/en" "$build_root/fa" "$output_root"

run_checked() {
  local transcript="$1" label="$2"
  shift 2
  if ! "$@" >"$transcript" 2>&1; then
    echo "$label failed. Last 40 transcript lines:" >&2
    tail -n 40 "$transcript" >&2
    return 1
  fi
}

assert_clean_log() {
  local log="$1"
  if grep -E 'LaTeX Warning: (Citation .* undefined|There were undefined references|Label\(s\) may have changed)|Overfull \\[hv]box|Underfull \\[hv]box' "$log"; then
    echo "Layout or reference warnings remain in $log" >&2
    return 1
  fi
}

if [[ "$language" == all || "$language" == en ]]; then
  command -v pdflatex >/dev/null
  command -v bibtex >/dev/null
  source_dir="$paper_root/en"
  build_dir="$build_root/en"
  args=(-interaction=nonstopmode -halt-on-error -jobname=paper-en "-output-directory=$build_dir" main.tex)
  (
    cd "$source_dir"
    export BIBINPUTS="$source_dir:"
    run_checked "$build_dir/pass-1.txt" 'English pdflatex pass 1' pdflatex "${args[@]}"
    run_checked "$build_dir/bibtex.txt" 'English BibTeX' bibtex "$build_dir/paper-en"
    run_checked "$build_dir/pass-2.txt" 'English pdflatex pass 2' pdflatex "${args[@]}"
    run_checked "$build_dir/pass-3.txt" 'English pdflatex pass 3' pdflatex "${args[@]}"
  )
  assert_clean_log "$build_dir/paper-en.log"
  if grep -q '^Warning--' "$build_dir/paper-en.blg"; then
    echo 'BibTeX warnings remain in the English build.' >&2
    exit 1
  fi
  cp "$build_dir/paper-en.pdf" "$output_root/paper-en.pdf"
  echo 'English PDF built successfully.'
fi

if [[ "$language" == all || "$language" == fa ]]; then
  command -v xelatex >/dev/null
  source_dir="$paper_root/fa"
  build_dir="$build_root/fa"
  args=(-interaction=nonstopmode -halt-on-error -jobname=paper-fa "-output-directory=$build_dir" main.tex)
  (
    cd "$source_dir"
    export FONTCONFIG_FILE="$source_dir/fonts.conf"
    run_checked "$build_dir/pass-1.txt" 'Persian XeLaTeX pass 1' xelatex "${args[@]}"
    run_checked "$build_dir/pass-2.txt" 'Persian XeLaTeX pass 2' xelatex "${args[@]}"
  )
  assert_clean_log "$build_dir/paper-fa.log"
  cp "$build_dir/paper-fa.pdf" "$output_root/paper-fa.pdf"
  echo 'Persian PDF built successfully.'
fi

#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: scripts/new-run.sh <run-id>" >&2
  exit 2
fi

run_id=$1
case "$run_id" in
  *[!A-Za-z0-9._-]*|"")
    echo "Run ID may contain only letters, digits, dot, underscore, and hyphen." >&2
    exit 2
    ;;
esac

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
raw="$root/results/raw/$run_id"
normalized="$root/results/normalized/$run_id"
evidence="$root/evidence/attacks/$run_id"

for target in "$raw" "$normalized" "$evidence"; do
  if [ -e "$target" ]; then
    echo "Run path already exists; choose a new ID: $target" >&2
    exit 1
  fi
done

mkdir -p "$raw" "$normalized" "$evidence"
cp "$root/templates/experiment-config.example.json" "$raw/experiment-config.json"
echo "Initialized run: $run_id"
echo "Keep allow_attack_execution=false until Phase 5 approval."


#!/usr/bin/env sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
input=${1:-"$root/evidence"}
output=${2:-"$root/evidence/evidence-sha256.txt"}

if command -v sha256sum >/dev/null 2>&1; then
  find "$input" -type f ! -path "$output" -print0 |
    sort -z |
    xargs -0 sha256sum > "$output"
elif command -v shasum >/dev/null 2>&1; then
  find "$input" -type f ! -path "$output" -print0 |
    sort -z |
    xargs -0 shasum -a 256 > "$output"
else
  echo "Neither sha256sum nor shasum is available." >&2
  exit 1
fi

echo "Evidence hashes written to $output"


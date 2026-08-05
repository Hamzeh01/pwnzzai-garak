#!/usr/bin/env bash
# End-to-end PwnzzAI security assessment with Garak (POSIX shell).
#
# Brings up the pinned PwnzzAI lab, runs every Garak suite against it, and builds
# the analysis tables and figures. Ollama must already be running on the host
# with the pinned model (llama3.2:1b) pulled.
#
# Each suite is a real Garak run; the artifacts under garak_runs/ are Garak's own
# report.jsonl / report.html.
#
# Usage:
#   scripts/run_assessment.sh                 # all suites
#   scripts/run_assessment.sh direct-injection
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Garak prints emoji; force UTF-8 so a non-UTF-8 locale does not crash it.
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
export PYTHONPATH="$ROOT"

PYTHON="$ROOT/.venv/Scripts/python.exe"
[ -x "$PYTHON" ] || PYTHON="$ROOT/.venv/bin/python"
[ -x "$PYTHON" ] || PYTHON="python3"

SUITE="${1:-all}"

echo "== bringing up the PwnzzAI lab =="
docker compose -f lab/docker-compose.yml up -d
echo "waiting for the app on 127.0.0.1:18080 ..."
for _ in $(seq 1 30); do
  if curl -sf -o /dev/null "http://127.0.0.1:18080/"; then break; fi
  sleep 2
done

echo "== preflight =="
"$PYTHON" -m garak_pwnzz preflight

echo "== running suite(s): $SUITE =="
"$PYTHON" -m garak_pwnzz run "$SUITE" --quiet

echo "== building analysis =="
"$PYTHON" -m garak_pwnzz analyze

echo "== done. Artifacts in garak_runs/ and garak_analysis/ =="

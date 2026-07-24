#!/usr/bin/env sh
set -eu

for tool in python3 git docker ollama; do
  if command -v "$tool" >/dev/null 2>&1; then
    case "$tool" in
      python3) "$tool" --version ;;
      git) "$tool" --version ;;
      docker) "$tool" --version ;;
      ollama) "$tool" --version ;;
    esac
  else
    echo "$tool: NOT FOUND"
  fi
done

if command -v docker >/dev/null 2>&1; then
  docker compose version || true
fi

echo "This script is read-only. It does not install software or start services."


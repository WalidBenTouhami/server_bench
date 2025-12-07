#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🧹 Nettoyage complet du projet…"

rm -rf "$ROOT/bin" "$ROOT/build"
rm -rf "$ROOT/logs"
rm -rf "$ROOT/python/figures"
rm -f  "$ROOT/python/results.json" "$ROOT/python/results.xlsx"
rm -f  "$ROOT/python/dashboard.html"

echo "✔ Nettoyage terminé."


#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

RED="\033[1;31m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RESET="\033[0m"

echo -e "${RED}⏹  Arrêt des serveurs…${RESET}"

kill_by_name() {
  local name="$1"
  if pgrep -x "$name" >/dev/null 2>&1; then
    echo -e "${YELLOW}→ killall $name${RESET}"
    pkill -x "$name" || true
  fi
}

kill_by_name "serveur_mono"
kill_by_name "serveur_multi"
kill_by_name "serveur_mono_http"
kill_by_name "serveur_multi_http"

# Sécurité supplémentaire : tuer les process écoutant sur 5050/5051
if command -v fuser >/dev/null 2>&1; then
  for port in 5050 5051; do
    if fuser -v "$port"/tcp >/dev/null 2>&1; then
      echo -e "${YELLOW}→ fuser -k $port/tcp${RESET}"
      fuser -k "$port"/tcp || true
    fi
  done
fi

echo -e "${GREEN}✔ Tous les serveurs connus ont été arrêtés.${RESET}"


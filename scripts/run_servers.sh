#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$ROOT/bin"
LOG_DIR="$ROOT/logs"

mkdir -p "$LOG_DIR"

GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
RESET="\033[0m"

port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :$port" | awk 'NR>1 {exit 0} END {exit 1}'
  else
    netstat -lnt 2>/dev/null | grep -q ":$port"
  fi
}

echo -e "${BLUE}🚀 Lancement des serveurs TCP (mono + multi)…${RESET}"

for port in 5050 5051; do
  if port_in_use "$port"; then
    echo -e "${RED}❌ Port $port déjà utilisé. Arrête d'abord les serveurs (scripts/kill_servers.sh).${RESET}"
    exit 1
  fi
done

MONO_BIN="$BIN_DIR/serveur_mono"
MULTI_BIN="$BIN_DIR/serveur_multi"

if [[ ! -x "$MONO_BIN" || ! -x "$MULTI_BIN" ]]; then
  echo -e "${YELLOW}⚠️ Binaires manquants. Compilation…${RESET}"
  (cd "$ROOT" && make -j"$(nproc)")
fi

"$MONO_BIN"  >"$LOG_DIR/serveur_mono.log" 2>&1 &
PID_MONO=$!
"$MULTI_BIN" >"$LOG_DIR/serveur_multi.log" 2>&1 &
PID_MULTI=$!

echo -e "${GREEN}✔ serveur_mono  (port 5050) PID = ${PID_MONO}${RESET}"
echo -e "${GREEN}✔ serveur_multi (port 5051) PID = ${PID_MULTI}${RESET}"
echo -e "${BLUE}ℹ️  Utilise 'scripts/kill_servers.sh' pour les arrêter.${RESET}"


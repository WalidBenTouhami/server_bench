#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY_DIR="$ROOT/python"

BLUE="\033[1;34m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RESET="\033[0m"

echo -e "${BLUE}🧪 Tests unitaires C (queue)…${RESET}"
(cd "$ROOT" && make debug && make test)

echo -e "${BLUE}🧪 Smoke test TCP mono-thread (client_stress)…${RESET}"

# Lancer serveur_mono en fond
(cd "$ROOT" && ./bin/serveur_mono &) 
PID=$!
sleep 1

cd "$PY_DIR"
if [[ ! -d venv ]]; then
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt >/dev/null

python3 client_stress.py --port 5050 --clients 5 || echo -e "${YELLOW}⚠️ Smoke test client_stress a retourné une erreur.${RESET}"

kill "$PID" 2>/dev/null || true

echo -e "${GREEN}✔ Tests terminés.${RESET}"


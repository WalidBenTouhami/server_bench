#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/logs"
PY_DIR="$ROOT/python"

mkdir -p "$LOG_DIR"

exec > >(tee -a "$LOG_DIR/auto_run.log") 2>&1

GREEN="\033[1;32m"
BLUE="\033[1;34m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
RESET="\033[0m"

echo "──────────────────────────────────────────────"
echo -e "🚀 Pipeline complet – $(date)"
echo "Racine du projet : $ROOT"
echo "──────────────────────────────────────────────"

# 1) Compilation C
echo -e "${BLUE}🧱 Compilation des serveurs C…${RESET}"
(cd "$ROOT" && make clean && make -j"$(nproc)")
echo -e "${GREEN}✔ Compilation terminée.${RESET}"

# 2) Environnement Python (dans python/)
echo -e "${BLUE}📦 Environnement Python (python/venv)…${RESET}"
cd "$PY_DIR"
if [[ ! -d venv ]]; then
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt >/dev/null
echo -e "${GREEN}✔ Environnement Python prêt.${RESET}"

# 3) Benchmark
echo -e "${BLUE}🔥 Exécution du benchmark complet…${RESET}"
python3 benchmark.py
echo -e "${GREEN}✔ Benchmark terminé.${RESET}"

# 4) Graphiques
echo -e "${BLUE}📈 Génération des graphiques PNG + SVG…${RESET}"
python3 plot_results.py
echo -e "${GREEN}✔ Graphiques générés dans python/figures/.${RESET}"

# 5) Dashboard HTML
echo -e "${BLUE}🧩 Génération du dashboard HTML…${RESET}"
python3 export_html.py
echo -e "${GREEN}✔ Dashboard : python/dashboard.html${RESET}"

echo "──────────────────────────────────────────────"
echo -e "${GREEN}🎉 Pipeline complet terminé sans erreur.${RESET}"
echo "──────────────────────────────────────────────"


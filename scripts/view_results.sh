#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY_DIR="$ROOT/python"
RES_XLS="$PY_DIR/results.xlsx"

if [[ ! -f "$RES_XLS" ]]; then
  echo "❌ Fichier de résultats introuvable : $RES_XLS"
  echo "   Lance : ./scripts/start_all.sh"
  exit 1
fi

cd "$PY_DIR"
if [[ ! -d venv ]]; then
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip >/dev/null
pip install pandas >/dev/null

python3 - << 'EOF'
import pandas as pd

df = pd.read_excel("results.xlsx")
print("Colonnes disponibles :")
print(df.columns.tolist())
print("\nRésumé par type de serveur :")
print(df.groupby("server")[["clients","throughput_rps","mean","p99"]].describe())
EOF


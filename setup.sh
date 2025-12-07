#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "🌱 Création du venv Python (racine)…"
rm -rf venv
python3 -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate

echo "📦 Installation dépendances Python globales…"
pip install --upgrade pip
pip install psutil pandas matplotlib openpyxl plotly

echo "🛠 Régénération fichiers HTTP…"
python3 create_http_files.py

echo "🔧 Compilation du projet C…"
make clean
make -j"$(nproc)"

echo "🧪 Tests unitaires C…"
make test

echo "🎉 Setup terminé avec succès."


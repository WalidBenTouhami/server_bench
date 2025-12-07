#!/bin/bash
set -e

SRC="docs"
OUT="docs/uml"

mkdir -p "$OUT"

echo "🛠 Génération UML…"

for f in "$SRC"/*.puml; do
    base=$(basename "$f" .puml)
    echo " → $base"
    plantuml -tpng "$f" -o "$OUT"
    plantuml -tsvg "$f" -o "$OUT"
done

echo "✔ UML générés dans $OUT/"


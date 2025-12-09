#!/bin/bash
set -e

SERVER_BIN="./bin/serveur_multi"
OUT="logs/valgrind_report.txt"

echo "──────────────────────────────" | tee $OUT
echo "🧠 Valgrind Full Analysis" | tee -a $OUT
echo "──────────────────────────────" | tee -a $OUT

valgrind \
    --leak-check=full \
    --show-leak-kinds=all \
    --track-origins=yes \
    --error-exitcode=1 \
    $SERVER_BIN 2>&1 | tee -a $OUT

echo "" | tee -a $OUT
echo "✔ Rapport généré dans $OUT"
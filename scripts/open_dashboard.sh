#!/usr/bin/env bash
set -e

LOG_FILE="logs/dashboard_open.log"
DASHBOARD_PATH="$(realpath "$(dirname "$0")/../python/dashboard.html")"

echo "──────────────────────────────────────────────" | tee -a "$LOG_FILE"
echo "🌐 Ouverture du Dashboard – $(date)"              | tee -a "$LOG_FILE"
echo "📄 Fichier : $DASHBOARD_PATH"                    | tee -a "$LOG_FILE"
echo "──────────────────────────────────────────────" | tee -a "$LOG_FILE"

# Vérification du fichier
if [[ ! -f "$DASHBOARD_PATH" ]]; then
    echo "❌ ERREUR : dashboard.html introuvable !" | tee -a "$LOG_FILE"
    exit 1
fi

# Détection automatique du navigateur
detect_browser() {
    if command -v firefox >/dev/null 2>&1; then
        echo "firefox"
    elif command -v google-chrome >/dev/null 2>&1; then
        echo "google-chrome"
    elif command -v chromium >/dev/null 2>&1; then
        echo "chromium"
    elif command -v xdg-open >/dev/null 2>&1; then
        echo "xdg-open"
    else
        echo "none"
    fi
}

BROWSER=$(detect_browser)

echo "🔍 Navigateur détecté : $BROWSER" | tee -a "$LOG_FILE"

if [[ "$BROWSER" == "none" ]]; then
    echo "⚠️ Aucun navigateur GUI détecté. Tentative en mode terminal…" | tee -a "$LOG_FILE"

    if command -v lynx >/dev/null 2>&1; then
        echo "📟 Ouverture avec lynx (mode terminal)…" | tee -a "$LOG_FILE"
        lynx "$DASHBOARD_PATH"
        exit 0
    fi

    echo "❌ ERREUR FATALE : aucun navigateur disponible, même pas lynx." | tee -a "$LOG_FILE"
    echo "💡 Solution : installer un navigateur, ex. : sudo apt install firefox" | tee -a "$LOG_FILE"
    exit 1
fi

# Lance le dashboard
echo "🚀 Ouverture du Dashboard avec : $BROWSER" | tee -a "$LOG_FILE"

"$BROWSER" "$DASHBOARD_PATH" >/dev/null 2>&1 &

echo "✔ Dashboard lancé avec succès !" | tee -a "$LOG_FILE"
echo "──────────────────────────────────────────────" | tee -a "$LOG_FILE"


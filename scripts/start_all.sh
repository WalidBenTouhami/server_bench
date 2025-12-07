#!/usr/bin/env bash
# ============================================================================
#         PIPELINE INTELLIGENT — Projet Serveur TCP/HTTP Haute Performance
#            Auteur : Walid Ben Touhami — Version PRO / DevOps Senior
# ============================================================================

set -euo pipefail
IFS=$'\n\t'

# ----------------------------------------------------------------------------
#                MODE D'OUVERTURE DU DASHBOARD (html | flask | none)
# ----------------------------------------------------------------------------
DASHBOARD_MODE="html"      # html  = ouvrir dashboard.html
                           # flask = lancer serveur Flask local
                           # none  = ne rien ouvrir

# ----------------------------------------------------------------------------
#                 DÉTECTION DU PROJET + DÉFINITION DES PATHS
# ----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PY_DIR="$PROJECT_ROOT/python"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/auto_run.log"

mkdir -p "$LOG_DIR"

echo "──────────────────────────────────────────────" | tee -a "$LOG_FILE"
echo "🚀 Pipeline INTELLIGENT – $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "📂 Racine projet : $PROJECT_ROOT" | tee -a "$LOG_FILE"
echo "──────────────────────────────────────────────" | tee -a "$LOG_FILE"

# ----------------------------------------------------------------------------
#                       FONCTION DE LOG + CHECK
# ----------------------------------------------------------------------------
die() {
    echo "❌ ERREUR : $1" | tee -a "$LOG_FILE"
    exit 1
}

step() {
    echo -e "\n🔹 $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "✔ $1\n" | tee -a "$LOG_FILE"
}

# ----------------------------------------------------------------------------
#                      1) Activation environnement Python
# ----------------------------------------------------------------------------
step "Activation environnement Python…"

if [[ ! -f "$PY_DIR/venv/bin/activate" ]]; then
    die "venv introuvable ! Exécute d'abord : ./setup.sh"
fi

source "$PY_DIR/venv/bin/activate"
success "Environnement Python activé."

# ----------------------------------------------------------------------------
#                   2) Vérification des ports disponibles
# ----------------------------------------------------------------------------
step "Vérification ports 5050 / 5051…"

for PORT in 5050 5051; do
    if lsof -i :$PORT >/dev/null 2>&1; then
        echo "⚠ Port $PORT occupé → libération en cours…" | tee -a "$LOG_FILE"
        pkill -f ":$PORT" || true
        sleep 1
    fi
done
success "Ports libres."

# ----------------------------------------------------------------------------
#                           3) Compilation C
# ----------------------------------------------------------------------------
step "Compilation C…"
make -C "$PROJECT_ROOT" clean >> "$LOG_FILE" 2>&1
make -C "$PROJECT_ROOT" -j"$(nproc)" | tee -a "$LOG_FILE"
success "Compilation terminée."

# ----------------------------------------------------------------------------
#                           4) Tests unitaires
# ----------------------------------------------------------------------------
step "Tests unitaires…"
make -C "$PROJECT_ROOT" test | tee -a "$LOG_FILE"
success "Tests unitaires réussis."

# ----------------------------------------------------------------------------
#                           5) Benchmark complet
# ----------------------------------------------------------------------------
step "Benchmark Python…"
python3 "$PY_DIR/benchmark.py" | tee -a "$LOG_FILE"
success "Benchmark terminé."

# ----------------------------------------------------------------------------
#                           6) Export Dashboard HTML
# ----------------------------------------------------------------------------
step "Génération dashboard HTML…"
python3 "$PY_DIR/export_html.py" | tee -a "$LOG_FILE"
success "Dashboard généré."

# ----------------------------------------------------------------------------
#                           7) Génération figures PNG + SVG
# ----------------------------------------------------------------------------
step "Génération figures PNG/SVG…"
python3 "$PY_DIR/plot_results.py" | tee -a "$LOG_FILE"
success "Figures enregistrées dans python/figures/."

# ----------------------------------------------------------------------------
#                    8) Ouverture intelligente du dashboard
# ----------------------------------------------------------------------------
OPEN_SCRIPT="$PY_DIR/open_dashboard.py"

step "Ouverture dashboard (${DASHBOARD_MODE})…"

case "$DASHBOARD_MODE" in
    html)
        python3 "$OPEN_SCRIPT" open &
        success "Dashboard HTML ouvert."
        ;;
    flask)
        python3 "$OPEN_SCRIPT" web &
        success "Serveur Flask démarré sur http://127.0.0.1:5000"
        ;;
    none)
        echo "ℹ Ouverture automatique désactivée." | tee -a "$LOG_FILE"
        ;;
    *)
        echo "⚠ Mode inconnu : $DASHBOARD_MODE" | tee -a "$LOG_FILE"
        ;;
esac

echo "🎉 Pipeline INTELLIGENT complet exécuté avec succès !" | tee -a "$LOG_FILE"
echo "──────────────────────────────────────────────" | tee -a "$LOG_FILE"

exit 0


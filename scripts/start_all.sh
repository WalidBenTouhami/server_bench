#!/usr/bin/env bash
# Optimized start script that wraps run_all.sh with better UX
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }

echo "════════════════════════════════════════════════"
echo "🚀 Lancement pipeline complet — $(date)"
echo "Racine du projet : ${PROJECT_ROOT}"
echo "════════════════════════════════════════════════"
echo ""

# Check if run_all.sh exists
if [[ ! -x "${PROJECT_ROOT}/scripts/run_all.sh" ]]; then
    echo -e "${YELLOW}[WARN]${NC} run_all.sh introuvable ou non exécutable"
    chmod +x "${PROJECT_ROOT}/scripts/run_all.sh" 2>/dev/null || true
fi

# Run the full pipeline
START_TIME=$(date +%s)
"${PROJECT_ROOT}/scripts/run_all.sh"
EXIT_CODE=$?
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "════════════════════════════════════════════════"
if [ $EXIT_CODE -eq 0 ]; then
    log_info "✓ Pipeline terminé avec succès en ${DURATION}s"
else
    echo -e "${YELLOW}[WARN]${NC} Pipeline terminé avec des erreurs (code: $EXIT_CODE)"
fi
echo "════════════════════════════════════════════════"
echo ""

# Show available next steps
echo "📊 Prochaines étapes:"
echo "   ${BLUE}▶${NC} Visualiser les résultats:"
echo "     ./scripts/view_results.sh"
echo ""
echo "   ${BLUE}▶${NC} Ouvrir le dashboard interactif:"
echo "     ./scripts/open_dashboard.sh"
echo ""
echo "   ${BLUE}▶${NC} Arrêter les serveurs:"
echo "     ./scripts/kill_servers.sh"
echo ""

exit $EXIT_CODE


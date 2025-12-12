#!/usr/bin/env bash
# Optimized dashboard opener with multiple browser support and fallback options
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PY_DIR="${PROJECT_ROOT}/python"
DASHBOARD="${PY_DIR}/dashboard.html"
RESULTS_JSON="${PY_DIR}/results.json"
LOG_DIR="${PROJECT_ROOT}/logs"
LOG_FILE="${LOG_DIR}/dashboard_open.log"

readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

mkdir -p "$LOG_DIR"

timestamp() { date +"%Y-%m-%d %H:%M:%S"; }
log() { echo "[$(timestamp)] $*" | tee -a "$LOG_FILE"; }
log_info() { echo -e "${GREEN}[INFO]${NC} $*" | tee -a "$LOG_FILE"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "$LOG_FILE"; }

echo "════════════════════════════════════════════════"
echo "🖥  Ouverture Dashboard"
echo "════════════════════════════════════════════════"

# Activate venv if available
if [[ -d "${PROJECT_ROOT}/venv" ]]; then
    log_info "Activation du venv..."
    # shellcheck disable=SC1091
    source "${PROJECT_ROOT}/venv/bin/activate" 2>/dev/null || true
else
    log_warn "venv introuvable (./setup.sh pour créer)"
fi

# Check for results
if [[ ! -f "$RESULTS_JSON" ]]; then
    log_error "python/results.json introuvable"
    echo ""
    echo "Génère d'abord les résultats avec:"
    echo "  ${BLUE}▶${NC} ./scripts/run_all.sh"
    exit 1
fi

log_info "Résultats trouvés: $RESULTS_JSON"

# Generate dashboard if missing or outdated
DASHBOARD_NEEDS_UPDATE=0
if [[ ! -f "$DASHBOARD" ]]; then
    DASHBOARD_NEEDS_UPDATE=1
    log_info "Dashboard absent, génération requise"
elif [[ "$RESULTS_JSON" -nt "$DASHBOARD" ]]; then
    DASHBOARD_NEEDS_UPDATE=1
    log_info "Résultats plus récents que le dashboard, régénération"
fi

if [ $DASHBOARD_NEEDS_UPDATE -eq 1 ]; then
    log_info "Génération du dashboard via export_html.py..."
    if (cd "$PY_DIR" && python3 export_html.py 2>&1 | tee -a "$LOG_FILE"); then
        log_info "✓ Dashboard généré avec succès"
    else
        log_error "Échec de génération du dashboard"
        exit 1
    fi
fi

# Try to open dashboard in browser
log_info "Tentative d'ouverture: $DASHBOARD"

# Try multiple methods
opened=0

# Method 1: xdg-open (Linux standard)
if command -v xdg-open >/dev/null 2>&1; then
    if xdg-open "$DASHBOARD" >/dev/null 2>&1; then
        opened=1
        log_info "✓ Ouvert avec xdg-open"
    fi
fi

# Method 2: open (macOS)
if [ $opened -eq 0 ] && command -v open >/dev/null 2>&1; then
    if open "$DASHBOARD" >/dev/null 2>&1; then
        opened=1
        log_info "✓ Ouvert avec open (macOS)"
    fi
fi

# Method 3: Direct browser commands
if [ $opened -eq 0 ]; then
    for browser in firefox chromium-browser google-chrome chrome; do
        if command -v "$browser" >/dev/null 2>&1; then
            "$browser" "$DASHBOARD" >/dev/null 2>&1 &
            opened=1
            log_info "✓ Ouvert avec $browser"
            break
        fi
    done
fi

echo ""
if [ $opened -eq 1 ]; then
    log_info "Dashboard ouvert dans le navigateur"
else
    log_warn "Impossible d'ouvrir automatiquement le navigateur"
    echo ""
    echo "Ouvre manuellement le fichier:"
    echo "  ${BLUE}${DASHBOARD}${NC}"
fi

echo ""
echo "Alternatives:"
echo "  • Mode interactif: cd python && python3 open_dashboard.py"
echo "  • Serveur web: cd python && python3 open_dashboard.py web"
echo ""


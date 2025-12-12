#!/usr/bin/env bash
# Optimized server launcher with health checks and retry logic
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BIN_DIR="${PROJECT_ROOT}/bin"
LOG_DIR="${PROJECT_ROOT}/logs"

readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

mkdir -p "$LOG_DIR"

echo "──────────────────────────────────────────────"
echo "🚀 Lancement manuel des serveurs C"
echo "──────────────────────────────────────────────"

# Check if binaries exist
check_binary() {
    local bin=$1
    if [[ ! -x "${BIN_DIR}/${bin}" ]]; then
        log_error "Binaire ${bin} introuvable ou non exécutable"
        log_info "Exécute 'make' ou './setup.sh' d'abord"
        return 1
    fi
    return 0
}

# Start server with health check
start_server() {
    local server_name=$1
    local port=$2
    local protocol=${3:-TCP}
    
    check_binary "$server_name" || return 1
    
    # Check if already running
    if pgrep -x "$server_name" >/dev/null; then
        log_warn "$server_name déjà en cours d'exécution"
        return 0
    fi
    
    # Check if port is available
    if command -v ss >/dev/null 2>&1; then
        if ss -ltn | grep -qE ":${port}[[:space:]]"; then
            log_error "Port $port déjà utilisé"
            return 1
        fi
    fi
    
    log_info "▶ Démarrage $server_name ($protocol $port)…"
    "${BIN_DIR}/${server_name}" > "${LOG_DIR}/${server_name}.log" 2>&1 &
    local pid=$!
    
    # Wait briefly and check if process is still alive
    sleep 0.5
    if ! kill -0 $pid 2>/dev/null; then
        log_error "$server_name a crashé au démarrage"
        log_info "Consulte ${LOG_DIR}/${server_name}.log pour détails"
        return 1
    fi
    
    # Additional health check with timeout
    local retries=5
    local healthy=0
    for ((i=1; i<=retries; i++)); do
        sleep 0.2
        if kill -0 $pid 2>/dev/null; then
            healthy=1
            break
        fi
    done
    
    if [ $healthy -eq 1 ]; then
        log_info "✓ $server_name démarré (PID: $pid)"
        echo "$pid" > "${LOG_DIR}/${server_name}.pid"
    else
        log_error "$server_name n'a pas démarré correctement"
        return 1
    fi
    
    return 0
}

# Start servers with error handling
SUCCESS_COUNT=0
TOTAL_SERVERS=2

if start_server "serveur_mono" 5050 "TCP"; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
fi

if start_server "serveur_multi" 5051 "TCP"; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
fi

echo ""
echo "──────────────────────────────────────────────"
if [ $SUCCESS_COUNT -eq $TOTAL_SERVERS ]; then
    log_info "✓ Tous les serveurs sont démarrés ($SUCCESS_COUNT/$TOTAL_SERVERS)"
else
    log_warn "Certains serveurs n'ont pas démarré ($SUCCESS_COUNT/$TOTAL_SERVERS)"
fi
echo "──────────────────────────────────────────────"
echo ""
echo "Commandes utiles:"
echo "  • Arrêter: make kill_servers ou ./scripts/kill_servers.sh"
echo "  • Statut: ps aux | grep serveur"
echo "  • Logs: tail -f ${LOG_DIR}/serveur_*.log"
echo ""


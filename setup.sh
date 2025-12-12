#!/usr/bin/env bash
# Setup script for TCP/HTTP Server Benchmark Project
# Optimized for performance and reliability

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Color output for better visibility
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

echo "──────────────────────────────────────────────"
echo "🚀 Setup du projet Serveur TCP/HTTP (C + Python)"
echo "Racine : ${PROJECT_ROOT}"
echo "──────────────────────────────────────────────"

# 1) Vérif outils de base avec versions
log_info "Vérification outils système..."
MISSING_TOOLS=()
for cmd in gcc make python3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        MISSING_TOOLS+=("$cmd")
    else
        VERSION=$("$cmd" --version 2>/dev/null | head -n1 || echo "version inconnue")
        log_info "$cmd trouvé: $VERSION"
    fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    log_error "Commandes manquantes: ${MISSING_TOOLS[*]}"
    echo "   → Sur Ubuntu/Debian: sudo apt install -y build-essential python3 python3-venv python3-pip make git curl netcat-openbsd"
    echo "   → Sur Fedora/RHEL: sudo dnf install -y gcc make python3 python3-pip git curl nmap-ncat"
    exit 1
fi
log_info "Tous les outils requis sont présents ✓"

# 2) Création/MAJ du venv global avec optimisations
if [[ ! -d "${PROJECT_ROOT}/venv" ]]; then
    log_info "Création du venv Python global…"
    python3 -m venv "${PROJECT_ROOT}/venv" || {
        log_error "Échec de la création du venv"
        exit 1
    }
    log_info "Venv créé avec succès ✓"
else
    log_info "Venv existant détecté"
fi

log_info "Activation du venv…"
# shellcheck disable=SC1091
source "${PROJECT_ROOT}/venv/bin/activate" || {
    log_error "Échec de l'activation du venv"
    exit 1
}

log_info "📦 Installation des dépendances Python (mode optimisé)…"
if [[ -f "${PROJECT_ROOT}/python/requirements.txt" ]]; then
    # Upgrade pip silently for faster installation
    pip install --quiet --upgrade pip setuptools wheel || log_warn "Échec de mise à jour de pip"
    
    # Install dependencies with progress bar
    pip install --requirement "${PROJECT_ROOT}/python/requirements.txt" || {
        log_error "Échec d'installation des dépendances Python"
        exit 1
    }
    log_info "Dépendances Python installées ✓"
else
    log_warn "Fichier requirements.txt introuvable"
fi

# 3) Regénération fichiers HTTP + build + tests
log_info "🛠 Reconstruction C (HTTP + TCP) avec optimisations…"
if [[ -f "${PROJECT_ROOT}/rebuild_project.py" ]]; then
    python3 "${PROJECT_ROOT}/rebuild_project.py" || {
        log_error "Échec de la reconstruction du projet"
        exit 1
    }
    log_info "Reconstruction terminée ✓"
else
    log_warn "rebuild_project.py introuvable, build manuel requis"
    log_info "Exécution de make clean && make…"
    make -C "${PROJECT_ROOT}" clean
    make -C "${PROJECT_ROOT}" -j"$(nproc)" || {
        log_error "Échec de la compilation"
        exit 1
    }
fi

echo ""
echo "──────────────────────────────────────────────"
log_info "🎉 Setup terminé avec succès!"
echo "──────────────────────────────────────────────"
echo ""
echo "Prochaines étapes:"
echo "  ➜ Lancer le pipeline complet: ./scripts/start_all.sh"
echo "  ➜ Lancer les tests: make test"
echo "  ➜ Lancer les benchmarks: cd python && python3 benchmark.py"
echo ""


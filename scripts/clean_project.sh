#!/usr/bin/env bash
# Optimized project cleanup script with safety checks and verbose mode
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

# Parse options
VERBOSE=0
DRY_RUN=0
DEEP_CLEAN=0

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose) VERBOSE=1; shift ;;
        -n|--dry-run) DRY_RUN=1; shift ;;
        -d|--deep) DEEP_CLEAN=1; shift ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -v, --verbose    Mode verbeux"
            echo "  -n, --dry-run    Afficher sans supprimer"
            echo "  -d, --deep       Nettoyage profond (inclut venv et build/)"
            echo "  -h, --help       Afficher l'aide"
            exit 0
            ;;
        *) log_warn "Option inconnue: $1"; shift ;;
    esac
done

echo "──────────────────────────────────────────────"
echo "🧹 Nettoyage projet (C + logs + figures)"
[ $DRY_RUN -eq 1 ] && echo "   MODE DRY-RUN (aucune suppression)"
echo "──────────────────────────────────────────────"

cd "$PROJECT_ROOT"

# Function to safely remove files (supports globs)
safe_remove() {
    local pattern=$1
    local desc=$2
    
    # Check if pattern contains wildcards
    if [[ "$pattern" == *"*"* ]]; then
        # Handle glob patterns
        local found=0
        for path in $pattern; do
            if [ -e "$path" ] || [ -L "$path" ]; then
                found=1
                if [ $DRY_RUN -eq 1 ]; then
                    log_info "[DRY-RUN] Supprimerait: $path"
                else
                    rm -rf "$path" || log_warn "Échec de suppression: $path"
                fi
            fi
        done
        if [ $found -eq 1 ] && [ $DRY_RUN -eq 0 ]; then
            log_info "Suppression: $desc"
        fi
    else
        # Handle single file/directory
        if [ $DRY_RUN -eq 1 ]; then
            if [ -e "$pattern" ] || [ -L "$pattern" ]; then
                log_info "[DRY-RUN] Supprimerait: $desc"
            fi
        else
            if [ -e "$pattern" ] || [ -L "$pattern" ]; then
                log_info "Suppression: $desc"
                rm -rf "$pattern" || log_warn "Échec de suppression: $pattern"
            fi
        fi
    fi
}

# Make clean
if [ $DRY_RUN -eq 0 ]; then
    log_info "Exécution de 'make clean'..."
    make clean 2>/dev/null || log_warn "make clean a échoué"
else
    log_info "[DRY-RUN] Exécuterait: make clean"
fi

# Clean Python artifacts
safe_remove "python/figures/*.png" "Figures PNG"
safe_remove "python/figures/*.svg" "Figures SVG"
safe_remove "python/results.json" "Résultats JSON"
safe_remove "python/results.xlsx" "Résultats Excel"
safe_remove "python/dashboard.html" "Dashboard HTML"
safe_remove "python/__pycache__" "Cache Python (python/)"
safe_remove "logs/*.log" "Fichiers logs"

# Deep clean if requested
if [ $DEEP_CLEAN -eq 1 ]; then
    log_info "Nettoyage profond activé..."
    safe_remove "build" "Répertoire build/"
    safe_remove "bin" "Binaires compilés"
    safe_remove "*.o" "Fichiers objets"
    safe_remove "**/__pycache__" "Tous les caches Python"
    
    if [ $DRY_RUN -eq 0 ]; then
        read -p "Supprimer le venv Python? (o/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[OoYy]$ ]]; then
            safe_remove "venv" "Environnement virtuel Python"
        fi
    fi
fi

echo ""
if [ $DRY_RUN -eq 1 ]; then
    log_info "✓ Analyse de nettoyage terminée (mode dry-run)"
    echo "   Exécutez sans -n pour effectuer le nettoyage"
else
    log_info "✓ Nettoyage terminé avec succès"
fi


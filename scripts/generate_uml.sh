#!/usr/bin/env bash
# Optimized UML generation script with error handling and validation
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC="${PROJECT_ROOT}/docs"
OUT="${PROJECT_ROOT}/docs/uml"

readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

mkdir -p "$OUT"

echo "════════════════════════════════════════════════"
echo "🛠  Génération UML (PlantUML)"
echo "════════════════════════════════════════════════"

# Check if plantuml is available
if ! command -v plantuml >/dev/null 2>&1; then
    log_error "plantuml n'est pas installé"
    echo ""
    echo "Installation:"
    echo "  • Ubuntu/Debian: sudo apt install plantuml"
    echo "  • macOS: brew install plantuml"
    echo "  • Ou télécharge depuis: https://plantuml.com/download"
    exit 1
fi

# Check PlantUML version
PLANTUML_VERSION=$(plantuml -version 2>&1 | head -n1 || echo "version inconnue")
log_info "PlantUML: $PLANTUML_VERSION"

# Find all .puml files
PUML_FILES=()
while IFS= read -r -d '' file; do
    PUML_FILES+=("$file")
done < <(find "$SRC" -name "*.puml" -type f -print0 2>/dev/null)

if [ ${#PUML_FILES[@]} -eq 0 ]; then
    log_warn "Aucun fichier .puml trouvé dans $SRC"
    exit 0
fi

log_info "Fichiers .puml trouvés: ${#PUML_FILES[@]}"
echo ""

# Generate UML diagrams
success_count=0
fail_count=0

for f in "${PUML_FILES[@]}"; do
    base=$(basename "$f" .puml)
    rel_path=$(realpath --relative-to="$SRC" "$f")
    
    echo -e "${BLUE}▶${NC} Traitement: $rel_path"
    
    # Generate PNG
    if plantuml -tpng "$f" -o "$OUT" 2>/dev/null; then
        echo "  ✓ PNG généré"
    else
        log_warn "  Échec génération PNG pour $base"
        fail_count=$((fail_count + 1))
        continue
    fi
    
    # Generate SVG
    if plantuml -tsvg "$f" -o "$OUT" 2>/dev/null; then
        echo "  ✓ SVG généré"
    else
        log_warn "  Échec génération SVG pour $base"
    fi
    
    success_count=$((success_count + 1))
done

echo ""
echo "════════════════════════════════════════════════"
log_info "✓ Génération UML terminée"
echo "════════════════════════════════════════════════"
echo ""
echo "Résultats:"
echo "  • Succès: $success_count"
echo "  • Échecs: $fail_count"
echo "  • Répertoire: $OUT"
echo ""

# List generated files
if [ $success_count -gt 0 ]; then
    log_info "Fichiers générés:"
    find "$OUT" -type f \( -name "*.png" -o -name "*.svg" \) -newer "$OUT/../../scripts" 2>/dev/null | sort | while read -r file; do
        size=$(du -h "$file" | cut -f1)
        echo "  • $(basename "$file") ($size)"
    done
fi

[ $fail_count -eq 0 ] || exit 1


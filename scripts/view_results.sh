#!/usr/bin/env bash
# Optimized results viewer with enhanced formatting and multiple output formats
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PY_DIR="${PROJECT_ROOT}/python"

readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

echo "════════════════════════════════════════════════"
echo "📊 Inspection rapide des résultats"
echo "════════════════════════════════════════════════"

cd "$PY_DIR"

# Check for results files
RESULTS_XLSX="results.xlsx"
RESULTS_JSON="results.json"

if [[ ! -f "$RESULTS_XLSX" ]] && [[ ! -f "$RESULTS_JSON" ]]; then
    log_error "Aucun fichier de résultats trouvé"
    echo "   Exécute d'abord: ./scripts/run_all.sh"
    exit 1
fi

# Activate venv if available
if [[ -d "${PROJECT_ROOT}/venv" ]]; then
    # shellcheck disable=SC1091
    source "${PROJECT_ROOT}/venv/bin/activate" 2>/dev/null || true
fi

# Check if pandas is available
if ! python3 -c "import pandas" 2>/dev/null; then
    log_error "pandas n'est pas installé"
    echo "   Installe-le avec: pip install pandas openpyxl"
    exit 1
fi

log_info "Analyse des résultats..."
echo ""

python3 - << 'EOF'
import pandas as pd
import json
from pathlib import Path

# Try to load results
xlsx_path = Path("results.xlsx")
json_path = Path("results.json")

if xlsx_path.exists():
    df = pd.read_excel(xlsx_path)
    print(f"📁 Source: {xlsx_path}")
elif json_path.exists():
    with open(json_path, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    print(f"📁 Source: {json_path}")
else:
    print("❌ Aucun fichier de résultats trouvé")
    exit(1)

print("\n" + "="*60)
print("📋 COLONNES DISPONIBLES")
print("="*60)
for i, col in enumerate(df.columns, 1):
    print(f"  {i:2d}. {col}")

print("\n" + "="*60)
print("📊 APERÇU DES DONNÉES (5 premières lignes)")
print("="*60)
print(df.head().to_string())

print("\n" + "="*60)
print("📈 STATISTIQUES PAR SERVEUR")
print("="*60)

# Group by server and compute statistics
for server in df['server'].unique():
    print(f"\n▶ Serveur: {server.upper()}")
    server_df = df[df['server'] == server]
    
    stats = {
        'Clients (min-max)': f"{server_df['clients'].min()}-{server_df['clients'].max()}",
        'Débit moyen (req/s)': f"{server_df['throughput_rps'].mean():.1f}",
        'Débit max (req/s)': f"{server_df['throughput_rps'].max():.1f}",
        'Latence P99 moy (ms)': f"{server_df['p99'].mean():.2f}",
        'CPU moyen (%)': f"{server_df['cpu_mean'].mean():.1f}",
        'Mémoire moy (MB)': f"{server_df['mem_mean'].mean():.1f}",
        'Taux de succès (%)': f"{(server_df['success'].sum() / (server_df['success'].sum() + server_df['fail'].sum()) * 100):.1f}",
    }
    
    for key, value in stats.items():
        print(f"  • {key:25s}: {value}")

# Comparison if both servers present
if len(df['server'].unique()) >= 2:
    print("\n" + "="*60)
    print("⚖️  COMPARAISON MONO VS MULTI")
    print("="*60)
    
    comparison = df.groupby('server').agg({
        'throughput_rps': 'mean',
        'p99': 'mean',
        'cpu_mean': 'mean',
        'mem_mean': 'mean'
    })
    
    if 'mono' in comparison.index and 'multi' in comparison.index:
        speedup = comparison.loc['multi', 'throughput_rps'] / comparison.loc['mono', 'throughput_rps']
        latency_improvement = (comparison.loc['mono', 'p99'] - comparison.loc['multi', 'p99']) / comparison.loc['mono', 'p99'] * 100
        
        print(f"\n  Speedup (débit): {speedup:.2f}x")
        print(f"  Amélioration latence P99: {latency_improvement:+.1f}%")

print("\n" + "="*60)
print("✓ Analyse terminée")
print("="*60)
EOF

echo ""
log_info "Pour visualiser graphiquement: ./scripts/open_dashboard.sh"
echo ""


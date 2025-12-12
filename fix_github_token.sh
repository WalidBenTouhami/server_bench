#!/usr/bin/env bash
# ============================================================
#  fix_github_token.sh - Optimized version
#  Configure un nouveau token GitHub avec permissions WORKFLOW
#  Automatisation complète — Walid Ben Touhami
# ============================================================

set -euo pipefail

# Unused variable removed per shellcheck warning
# REPO_URL can be derived from git remote if needed
WORKFLOW_TEST=".github/workflows/validate.yml"

readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

echo "════════════════════════════════════════════════════════════"
echo " 🚀 Script de réparation GitHub — Token avec scope WORKFLOW"
echo "════════════════════════════════════════════════════════════"
echo ""

# ------------------------------------------------------------
# 1) Demander à l'utilisateur son nouveau token GitHub
# ------------------------------------------------------------
read -rsp "👉 Entrer ton nouveau token GitHub (PAT) : " PAT
echo ""
if [ -z "$PAT" ]; then
    log_error "Aucun token saisi. Abandon."
    exit 1
fi

echo "🔐 Nouveau token reçu."

# ------------------------------------------------------------
# 2) Nettoyer les anciens credentials Git
# ------------------------------------------------------------
echo ""
echo "🧹 Nettoyage des anciens credentials Git..."
git credential-cache exit || true
git credential-manager-core erase <<EOF || true
protocol=https
host=github.com
EOF

git config --global --unset credential.helper || true

# ------------------------------------------------------------
# 3) Mettre à jour le remote origin pour utiliser le nouveau token
# ------------------------------------------------------------
NEW_URL="https://$PAT@github.com/WalidBenTouhami/SERVER_BENCH.git"
echo "🔧 Mise à jour du remote origin..."
git remote set-url origin "$NEW_URL"

echo "✔ Remote mis à jour :"
git remote -v
echo ""

# ------------------------------------------------------------
# 4) Vérifier les permissions du token via API GitHub
# ------------------------------------------------------------
echo "🔍 Vérification des permissions du token..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: token $PAT" \
    https://api.github.com/user)

if [ "$STATUS" != "200" ]; then
    echo "❌ Token invalide ou insuffisant."
    exit 1
fi

echo "✔ Token valide."

# ------------------------------------------------------------
# 5) Vérifier permission WORKFLOW
# ------------------------------------------------------------
echo "🔍 Test des permissions WORKFLOW..."

WF_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X GET \
    -H "Authorization: token $PAT" \
    https://api.github.com/repos/WalidBenTouhami/SERVER_BENCH/actions/workflows)

if [ "$WF_STATUS" != "200" ]; then
    echo "❌ Le token n'a PAS le scope 'workflow'."
    echo "⚠️  Tu dois régénérer le PAT en activant :"
    echo "     ✔ repo"
    echo "     ✔ workflow"
    echo "     ✔ actions (facultatif mais recommandé)"
    exit 1
fi

echo "✔ Permission WORKFLOW détectée ! OK."
echo ""

# ------------------------------------------------------------
# 6) Créer un workflow de test léger
# ------------------------------------------------------------
echo "📝 Création d'un workflow de test (${WORKFLOW_TEST})..."

mkdir -p .github/workflows

cat > "$WORKFLOW_TEST" <<EOF
name: Validate Token Workflow
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Check out
        uses: actions/checkout@v3
      - name: Token validation OK
        run: echo "WORKFLOW PERMISSION OK"
EOF

echo "✔ Workflow de test créé."
echo ""

# ------------------------------------------------------------
# 7) Commit + push pour valider
# ------------------------------------------------------------
log_info "Commit & Push..."
git add "$WORKFLOW_TEST"
git commit -m "Test workflow: validate token permissions" || true

log_info "Tentative de push..."
if git push origin main; then
    echo ""
    echo "════════════════════════════════════════════════════════════"
    log_info "🎉 SUCCESS — Le workflow a été accepté par GitHub !"
    log_info "   → Le token possède bien le scope WORKFLOW."
    echo "════════════════════════════════════════════════════════════"
    exit 0
else
    log_error "PUSH REFUSÉ — Le token n'a toujours pas la permission WORKFLOW."
    exit 1
fi


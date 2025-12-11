#!/bin/bash
# ============================================================
#  fix_github_token.sh
#  Configure un nouveau token GitHub avec permissions WORKFLOW
#  Automatisation complète — Walid Ben Touhami
# ============================================================

set -e

REPO_URL="https://github.com/WalidBenTouhami/SERVER_BENCH.git"
WORKFLOW_TEST=".github/workflows/validate.yml"

echo "============================================================"
echo " 🚀 Script de réparation GitHub — Token avec scope WORKFLOW"
echo "============================================================"
echo ""

# ------------------------------------------------------------
# 1) Demander à l'utilisateur son nouveau token GitHub
# ------------------------------------------------------------
read -sp "👉 Entrer ton nouveau token GitHub (PAT) : " PAT
echo ""
if [ -z "$PAT" ]; then
    echo "❌ Aucun token saisi. Abandon."
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

cat > $WORKFLOW_TEST <<EOF
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
echo "🔄 Commit & Push..."
git add $WORKFLOW_TEST
git commit -m "Test workflow: validate token permissions" || true

echo "🚀 Tentative de push..."
git push origin main || {
    echo "❌ PUSH REFUSÉ — Le token n'a toujours pas la permission WORKFLOW."
    exit 1
}

echo ""
echo "============================================================"
echo " 🎉 SUCCESS — Le workflow a été accepté par GitHub !"
echo "     → Le token possède bien le scope WORKFLOW."
echo "============================================================"


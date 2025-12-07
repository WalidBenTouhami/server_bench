#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
open_dashboard.py – CLI & Web UI pour visualiser les résultats du benchmark

Fonctionnalités :
  - CLI interactive avec autocomplétion et couleurs
  - Ouverture du dashboard HTML dans un navigateur
  - Affichage d’un résumé des résultats (results.json)
  - Export automatique des figures dans un ZIP (figures_export.zip)
  - Serveur web Flask local :
        /        → page d’accueil
        /results → résumé des résultats (HTML)
        /graphs  → affichage des PNG
        /compare → comparaison mono vs multi
"""

import json
import os
import sys
import shutil
import webbrowser
from pathlib import Path

import pandas as pd

# Flask est optionnel : on gère proprement son absence
try:
    from flask import Flask, jsonify, send_from_directory, render_template_string
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

# =========================
#  CONSTANTES ET CHEMINS
# =========================

PY_ROOT = Path(__file__).resolve().parent              # .../server_project/python
PROJECT_ROOT = PY_ROOT.parent                          # .../server_project
RESULTS_JSON = PY_ROOT / "results.json"
RESULTS_XLSX = PY_ROOT / "results.xlsx"
FIG_DIR = PY_ROOT / "figures"
DASHBOARD_HTML = PY_ROOT / "dashboard.html"
EXPORT_DIR = PY_ROOT / "exports"
EXPORT_ZIP = EXPORT_DIR / "figures_export.zip"

LOG_FILE = PROJECT_ROOT / "logs" / "dashboard_open.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

COMMANDS = [
    "help",
    "open",
    "summary",
    "list-fig",
    "export",
    "web",
    "quit",
    "exit",
]

# =========================
#  UTILITAIRES COULEURS
# =========================

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[1;32m"
RED = "\033[1;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"
CYAN = "\033[1;36m"
MAGENTA = "\033[1;35m"


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def print_info(msg: str) -> None:
    s = f"{BLUE}ℹ {msg}{RESET}"
    print(s)
    log(msg)


def print_ok(msg: str) -> None:
    s = f"{GREEN}✔ {msg}{RESET}"
    print(s)
    log(msg)


def print_warn(msg: str) -> None:
    s = f"{YELLOW}⚠ {msg}{RESET}"
    print(s)
    log("[WARN] " + msg)


def print_err(msg: str) -> None:
    s = f"{RED}❌ {msg}{RESET}"
    print(s, file=sys.stderr)
    log("[ERROR] " + msg)


# =========================
#  CHARGEMENT RÉSULTATS
# =========================

def load_results_df() -> pd.DataFrame:
    """Charge les résultats depuis results.json (prioritaire) ou results.xlsx."""
    if RESULTS_JSON.exists():
        try:
            data = json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
            df = pd.DataFrame(data)
            return df
        except Exception as e:
            print_warn(f"Impossible de lire results.json : {e}. Tentative XLSX…")

    if RESULTS_XLSX.exists():
        try:
            df = pd.read_excel(RESULTS_XLSX)
            return df
        except Exception as e:
            print_err(f"Impossible de lire results.xlsx : {e}")
            raise

    raise FileNotFoundError("Aucun fichier de résultats trouvé (results.json / results.xlsx).")


def summarize_results(df: pd.DataFrame) -> str:
    """Retourne une chaîne avec un résumé des résultats par serveur."""
    lines = []
    servers = df["server"].unique()
    for srv in servers:
        sub = df[df["server"] == srv]
        if sub.empty:
            continue

        avg_throughput = sub["throughput_rps"].mean()
        max_throughput = sub["throughput_rps"].max()
        avg_p99 = sub["p99"].mean()
        max_clients = sub["clients"].max()

        lines.append(
            f"  - {srv} :\n"
            f"      • clients max testés : {int(max_clients)}\n"
            f"      • débit moyen        : {avg_throughput:.1f} req/s\n"
            f"      • débit max          : {max_throughput:.1f} req/s\n"
            f"      • latence P99 moyenne: {avg_p99:.1f} ms\n"
        )
    return "\n".join(lines)


# =========================
#  ACTIONS CLI
# =========================

def action_open_dashboard():
    """Ouvre dashboard.html dans le navigateur par défaut."""
    if not DASHBOARD_HTML.exists():
        print_err(f"dashboard.html introuvable : {DASHBOARD_HTML}")
        print_info("Génère-le avec : python3 export_html.py (depuis le dossier python/).")
        return

    print_info(f"Ouverture du dashboard : {DASHBOARD_HTML}")
    log(f"Ouvrir dashboard : {DASHBOARD_HTML}")
    webbrowser.open_new_tab(DASHBOARD_HTML.as_uri())
    print_ok("Navigateur lancé.")


def action_summary():
    """Affiche un résumé synthétique des résultats."""
    try:
        df = load_results_df()
    except Exception as e:
        print_err(str(e))
        return

    print(f"{MAGENTA}{BOLD}Résumé des résultats (par serveur) :{RESET}\n")
    print(summarize_results(df))


def action_list_figures():
    """Liste les figures disponibles."""
    if not FIG_DIR.exists():
        print_err(f"Dossier des figures inexistant : {FIG_DIR}")
        return

    pngs = sorted(FIG_DIR.glob("*.png"))
    svgs = sorted(FIG_DIR.glob("*.svg"))

    if not pngs and not svgs:
        print_warn(f"Aucune figure trouvée dans {FIG_DIR}")
        return

    print(f"{CYAN}{BOLD}Figures PNG :{RESET}")
    for p in pngs:
        print(f"  - {p.name}")

    if svgs:
        print(f"\n{CYAN}{BOLD}Figures SVG :{RESET}")
        for p in svgs:
            print(f"  - {p.name}")


def action_export_figures():
    """Crée un ZIP contenant dashboard.html + figures PNG/SVG."""
    if not FIG_DIR.exists():
        print_err(f"Dossier des figures inexistant : {FIG_DIR}")
        return

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    temp_dir = EXPORT_DIR / "tmp_bundle"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Copier dashboard.html si disponible
    if DASHBOARD_HTML.exists():
        shutil.copy2(DASHBOARD_HTML, temp_dir / "dashboard.html")

    # Copier figures
    count = 0
    for ext in ("*.png", "*.svg"):
        for fig in FIG_DIR.glob(ext):
            shutil.copy2(fig, temp_dir / fig.name)
            count += 1

    if count == 0:
        print_warn("Aucune figure à exporter.")
        shutil.rmtree(temp_dir)
        return

    # Création du zip
    if EXPORT_ZIP.exists():
        EXPORT_ZIP.unlink()

    zip_base = EXPORT_ZIP.with_suffix("")  # sans .zip
    shutil.make_archive(str(zip_base), "zip", root_dir=temp_dir)

    shutil.rmtree(temp_dir)

    print_ok(f"Figures exportées dans : {EXPORT_ZIP}")
    print_info("Tu peux copier ce ZIP vers Windows ou l’envoyer à ton enseignant.")


# =========================
#  SERVEUR FLASK
# =========================

def create_flask_app() -> "Flask":
    app = Flask(__name__)

    # Charger les données une fois au démarrage pour la version simple
    try:
        df = load_results_df()
    except Exception as e:
        print_err(f"Impossible de charger les résultats pour Flask : {e}")
        df = None

    @app.route("/")
    def index():
        html = """
        <html>
          <head>
            <title>Serveur haute performance – Dashboard</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 2rem; }
              a { text-decoration: none; color: #1565c0; }
              h1 { color: #0d47a1; }
              .card { border: 1px solid #ddd; padding: 1rem; margin-bottom: 1rem; border-radius: 8px; }
            </style>
          </head>
          <body>
            <h1>Serveur haute performance – Dashboard</h1>
            <div class="card">
              <h2>Sections</h2>
              <ul>
                <li><a href="/results">📊 Résultats</a></li>
                <li><a href="/graphs">📈 Graphiques</a></li>
                <li><a href="/compare">⚖ Comparaison mono vs multi</a></li>
              </ul>
            </div>
          </body>
        </html>
        """
        return html

    @app.route("/results")
    def results():
        if df is None or df.empty:
            return "Aucun résultat disponible.", 500
        # Petit tableau HTML
        table_html = df.to_html(classes="dataframe", index=False, border=0)

        html = f"""
        <html>
          <head>
            <title>Résultats benchmark</title>
            <style>
              body {{ font-family: Arial, sans-serif; margin: 2rem; }}
              h1 {{ color: #0d47a1; }}
              table.dataframe {{ border-collapse: collapse; width: 100%; }}
              table.dataframe th, table.dataframe td {{
                  border: 1px solid #ccc;
                  padding: 4px 6px;
                  font-size: 12px;
              }}
              table.dataframe th {{
                  background-color: #e3f2fd;
              }}
            </style>
          </head>
          <body>
            <h1>Résultats détaillés</h1>
            {table_html}
          </body>
        </html>
        """
        return html

    @app.route("/graphs")
    def graphs():
        if not FIG_DIR.exists():
            return "Dossier des figures manquant.", 500

        pngs = sorted(FIG_DIR.glob("*.png"))
        svgs = sorted(FIG_DIR.glob("*.svg"))

        imgs = ""
        for p in pngs + svgs:
            imgs += f'<div><h3>{p.name}</h3><img src="/static/figures/{p.name}" style="max-width: 800px;"></div><hr/>'

        if not imgs:
            imgs = "<p>Aucune figure trouvée.</p>"

        html = f"""
        <html>
          <head>
            <title>Graphiques</title>
            <style>
              body {{ font-family: Arial, sans-serif; margin: 2rem; }}
              h1 {{ color: #0d47a1; }}
              img {{ border: 1px solid #ddd; padding: 4px; background: #fafafa; }}
            </style>
          </head>
          <body>
            <h1>Graphiques de performances</h1>
            {imgs}
          </body>
        </html>
        """
        return html

    @app.route("/compare")
    def compare():
        if df is None or df.empty:
            return "Aucun résultat disponible.", 500

        servers = df["server"].unique()
        if len(servers) < 2:
            return "Comparaison impossible : un seul type de serveur présent.", 500

        # On suppose "mono" et "multi"
        try:
            mono = df[df["server"] == "mono"]
            multi = df[df["server"] == "multi"]
        except KeyError:
            return "Colonnes manquantes pour la comparaison.", 500

        def agg_stats(sub):
            return {
                "throughput_mean": sub["throughput_rps"].mean(),
                "throughput_max": sub["throughput_rps"].max(),
                "p99_mean": sub["p99"].mean(),
            }

        mono_stats = agg_stats(mono)
        multi_stats = agg_stats(multi)

        speedup = 0.0
        if mono_stats["throughput_mean"] and mono_stats["throughput_mean"] > 0:
            speedup = multi_stats["throughput_mean"] / mono_stats["throughput_mean"]

        html = render_template_string(
            """
            <html>
              <head>
                <title>Comparaison mono vs multi</title>
                <style>
                  body { font-family: Arial, sans-serif; margin: 2rem; }
                  h1 { color: #0d47a1; }
                  table { border-collapse: collapse; }
                  th, td { border: 1px solid #ccc; padding: 6px 10px; }
                  th { background: #e3f2fd; }
                </style>
              </head>
              <body>
                <h1>Comparaison Mono-thread vs Multi-thread</h1>
                <table>
                  <tr>
                    <th>Metric</th>
                    <th>Mono</th>
                    <th>Multi</th>
                  </tr>
                  <tr>
                    <td>Débit moyen (req/s)</td>
                    <td>{{ mono_throughput_mean|round(1) }}</td>
                    <td>{{ multi_throughput_mean|round(1) }}</td>
                  </tr>
                  <tr>
                    <td>Débit max (req/s)</td>
                    <td>{{ mono_throughput_max|round(1) }}</td>
                    <td>{{ multi_throughput_max|round(1) }}</td>
                  </tr>
                  <tr>
                    <td>Latence P99 moyenne (ms)</td>
                    <td>{{ mono_p99_mean|round(1) }}</td>
                    <td>{{ multi_p99_mean|round(1) }}</td>
                  </tr>
                  <tr>
                    <td>Speedup multi / mono (débit moyen)</td>
                    <td colspan="2">{{ speedup|round(2) }}x</td>
                  </tr>
                </table>
              </body>
            </html>
            """,
            mono_throughput_mean=mono_stats["throughput_mean"],
            mono_throughput_max=mono_stats["throughput_max"],
            mono_p99_mean=mono_stats["p99_mean"],
            multi_throughput_mean=multi_stats["throughput_mean"],
            multi_throughput_max=multi_stats["throughput_max"],
            multi_p99_mean=multi_stats["p99_mean"],
            speedup=speedup,
        )
        return html

    @app.route("/static/figures/<path:filename>")
    def static_figures(filename):
        return send_from_directory(FIG_DIR, filename)

    @app.route("/api/results")
    def api_results():
        if df is None or df.empty:
            return jsonify({"error": "no data"}), 500
        return jsonify(df.to_dict(orient="records"))

    return app


def action_web():
    """Lance le serveur Flask local."""
    if not HAS_FLASK:
        print_err("Flask n’est pas installé dans le venv Python.")
        print_info("Installe-le depuis le dossier python/ :")
        print("  source venv/bin/activate")
        print("  pip install flask")
        return

    app = create_flask_app()
    print_ok("Serveur Flask démarré sur http://127.0.0.1:5000")
    print_info("Routes : /, /results, /graphs, /compare")
    app.run(host="127.0.0.1", port=5000, debug=False)


# =========================
#  CLI INTERACTIVE
# =========================

def setup_autocomplete():
    try:
        import readline
    except ImportError:
        print_warn("readline non disponible : pas d’autocomplétion.")
        return

    def completer(text, state):
        options = [c for c in COMMANDS if c.startswith(text)]
        if state < len(options):
            return options[state]
        return None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")


def print_help():
    print(f"{BOLD}Commandes disponibles :{RESET}")
    print("  help       → afficher cette aide")
    print("  open       → ouvrir le dashboard HTML dans le navigateur")
    print("  summary    → afficher un résumé des résultats")
    print("  list-fig   → lister les figures PNG/SVG")
    print("  export     → exporter dashboard + figures dans un ZIP")
    print("  web        → lancer le serveur Flask (http://127.0.0.1:5000)")
    print("  quit/exit  → quitter la CLI")


def main_interactive():
    print(f"{BOLD}{GREEN}=== Serveur haute performance – Dashboard CLI ==={RESET}")
    print(f"Projet : {PROJECT_ROOT}")
    print_help()
    setup_autocomplete()

    while True:
        try:
            cmd = input(f"{CYAN}dashboard> {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not cmd:
            continue

        if cmd in ("quit", "exit"):
            break
        elif cmd == "help":
            print_help()
        elif cmd == "open":
            action_open_dashboard()
        elif cmd == "summary":
            action_summary()
        elif cmd == "list-fig":
            action_list_figures()
        elif cmd == "export":
            action_export_figures()
        elif cmd == "web":
            action_web()
        else:
            print_warn(f"Commande inconnue : {cmd}")
            print("Tape 'help' pour la liste des commandes.")

    print_ok("CLI fermée. À bientôt.")


# =========================
#  POINT D’ENTRÉE
# =========================

if __name__ == "__main__":
    # Mode simple en ligne de commande :
    #   python3 open_dashboard.py open
    #   python3 open_dashboard.py web
    #   python3 open_dashboard.py summary
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "open":
            action_open_dashboard()
        elif action == "summary":
            action_summary()
        elif action == "list-fig":
            action_list_figures()
        elif action == "export":
            action_export_figures()
        elif action == "web":
            action_web()
        elif action in ("help", "-h", "--help"):
            print_help()
        else:
            print_err(f"Commande inconnue : {action}")
            print_help()
            sys.exit(1)
    else:
        # Sinon : mode interactif complet
        main_interactive()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
export_html.py — Génération du dashboard HTML avec sécurité .format()
Compatible avec CSS, évite KeyError via double-accolades.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS_JSON = ROOT / "results.json"
OUTPUT_HTML = ROOT / "dashboard.html"
FIG_DIR = ROOT / "figures"

def load_results():
    if not RESULTS_JSON.exists():
        raise FileNotFoundError(f"Fichier introuvable : {RESULTS_JSON}")

    with RESULTS_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def build_table(data):
    if not data:
        return "<p>Aucune donnée disponible.</p>"

    # Récupération des colonnes de la première ligne
    cols = data[0].keys()

    thead = "".join(f"<th>{c}</th>" for c in cols)
    rows = []
    for row in data:
        tr = "".join(f"<td>{row[c]}</td>" for c in cols)
        rows.append(f"<tr>{tr}</tr>")

    tbody = "\n".join(rows)

    return f"""
    <table class="perf-table">
        <thead><tr>{thead}</tr></thead>
        <tbody>{tbody}</tbody>
    </table>
    """


def main():
    data = load_results()
    table_html = build_table(data)

    # ⚠ Toutes les accolades CSS sont doublées {{ }}
    html = """
<html>
<head>
<title>{title}</title>
<style>
body {{
    font-family: Arial, sans-serif;
    margin: 2rem;
    background: #fafafa;
}}
h1 {{
    color: #0d47a1;
}}
.perf-table {{
    border-collapse: collapse;
    width: 100%;
    margin-top: 20px;
}}
.perf-table th {{
    background: #e3f2fd;
    padding: 8px;
    border: 1px solid #ccc;
}}
.perf-table td {{
    padding: 6px;
    border: 1px solid #ccc;
    text-align: center;
}}
img {{
    max-width: 600px;
    border: 1px solid #ccc;
    background: #fff;
    padding: 4px;
    margin: 8px;
}}
</style>
</head>
<body>

<h1>{title}</h1>

<h2>📊 Résultats du benchmark</h2>
{table}

<h2>📈 Graphiques</h2>
{images}

</body>
</html>
"""

    # 🔍 Récupération des images
    img_tags = ""
    if FIG_DIR.exists():
        for fig in sorted(FIG_DIR.glob("*.png")):
            img_tags += f'<div><img src="figures/{fig.name}" alt="{fig.name}"></div>\n'

    html_f = html.format(
        title="Dashboard – Serveur Haute Performance",
        table=table_html,
        images=img_tags
    )

    OUTPUT_HTML.write_text(html_f, encoding="utf-8")
    print(f"✔ Dashboard HTML généré : {OUTPUT_HTML}")


if __name__ == "__main__":
    main()


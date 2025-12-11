#!/usr/bin/env python3
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from pathlib import Path

OUTPUT = Path("presentation/cheatsheet.pdf")

sections = [
    ("CHEAT-SHEET — Serveurs TCP & HTTP Haute Performance",
     "Pipeline complet, commandes essentielles et outils de debug."),
    ("Pipeline d’exécution", 
     "1. activer venv\n2. générer fichiers HTTP\n3. compiler\n4. lancer serveurs."),
    ("Commandes clés",
     "make clean, make -j$(nproc), ./scripts/start_all.sh"),
    ("Debug",
     "valgrind — memcheck & helgrind, make debug (sanitizers)"),
]

def main():
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4)
    content = []

    for title, body in sections:
        content.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
        content.append(Spacer(1, 12))
        content.append(Paragraph(body.replace("\n", "<br/>"), styles["BodyText"]))
        content.append(Spacer(1, 20))

    doc.build(content)
    print(f"✔ PDF généré : {OUTPUT}")

if __name__ == "__main__":
    main()


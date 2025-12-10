#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_readme_uml.py
---------------------------------------
Met automatiquement à jour les sections UML
du README.md en insérant les bons fichiers SVG.

Compatible avec le système de nommage :
- uml_seq_tcp_monothread.svg
- uml_seq_tcp_multithread.svg
- uml_seq_http_monothread.svg
- uml_seq_http_multithread.svg
- uml_architecture.svg
- uml_queue.svg
- uml_threads.svg
"""

import re
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UML_DIR = ROOT / "docs" / "uml"
README = ROOT / "README.md"

# Map logique → filenames normalisés
UMLS = {
    "ARCHITECTURE": "uml_architecture.svg",
    "QUEUE": "uml_queue.svg",
    "THREADS": "uml_threads.svg",
    "TCP_MONO": "uml_seq_tcp_monothread.svg",
    "TCP_MULTI": "uml_seq_tcp_multithread.svg",
    "HTTP_MONO": "uml_seq_http_monothread.svg",
    "HTTP_MULTI": "uml_seq_http_multithread.svg",
}

SECTION_PATTERN = r"(# 🧠 UML[\s\S]*?)(# 📊 Résultats Benchmark)"

def generate_img_tag(filename):
    """
    Génère automatiquement un tag HTML propre.
    """
    return f'<img src="docs/uml/{filename}" width="900">\n'

def update_readme():
    if not README.exists():
        print("❌ README.md introuvable.")
        return

    text = README.read_text(encoding="utf-8")

    m = re.search(SECTION_PATTERN, text)
    if not m:
        print("❌ Section UML introuvable.")
        return

    before = m.group(1)
    after = m.group(2)

    # Nouvelle section UML
    new = "# 🧠 UML — Architecture & Threads\n\n"

    new += "## Architecture Globale\n" + generate_img_tag(UMLS["ARCHITECTURE"]) + "\n"
    new += "## Queue FIFO Thread-Safe\n" + generate_img_tag(UMLS["QUEUE"]) + "\n"
    new += "## Multi-threading (Workers & Dispatcher)\n" + generate_img_tag(UMLS["THREADS"]) + "\n"

    new += "---\n\n## Séquences TCP\n"
    new += "### TCP Mono-thread\n" + generate_img_tag(UMLS["TCP_MONO"]) + "\n"
    new += "### TCP Multi-thread\n" + generate_img_tag(UMLS["TCP_MULTI"]) + "\n"

    new += "---\n\n## Séquences HTTP\n"
    new += "### HTTP Mono-thread\n" + generate_img_tag(UMLS["HTTP_MONO"]) + "\n"
    new += "### HTTP Multi-thread\n" + generate_img_tag(UMLS["HTTP_MULTI"]) + "\n"

    # Reconstruire le fichier complet
    new_readme = text[: m.start(1)] + new + "\n" + after + text[m.end(2):]

    README.write_text(new_readme, encoding="utf-8")
    print("✅ README.md mis à jour automatiquement avec les UML.")

if __name__ == "__main__":
    update_readme()


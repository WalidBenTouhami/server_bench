#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Génération UML + normalisation des noms selon conventions :
  uml_seq_tcp_monothread
  uml_seq_tcp_multithread
  uml_seq_http_monothread
  uml_seq_http_multithread

Produit automatiquement :
 - .puml
 - .svg (Light)
 - _dark.svg (Dark theme)

Ce script fait partie du workflow Makefile.
"""

import os
import subprocess
from pathlib import Path
import re

UML_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Cartographie PUML → contenu
# ---------------------------------------------------------------------------
UML_DEFINITIONS = {
    "uml_seq_tcp_monothread": r"""
@startuml
actor Client
Client -> Server : TCP connect()
Server -> Server : handle_request()
Server -> Client : response()
@enduml
""",

    "uml_seq_tcp_multithread": r"""
@startuml
actor Client
Client -> Dispatcher : TCP connect()
Dispatcher -> Queue : push(job)
Worker -> Queue : pop(job)
Worker -> Worker : process()
Worker -> Client : response()
@enduml
""",

    "uml_seq_http_monothread": r"""
@startuml
actor Browser
Browser -> Server : GET /path
Server -> Parser : parse_http_request()
Parser -> Router : route()
Router -> Server : build_response()
Server -> Browser : HTTP/1.1 200 OK
@enduml
""",

    "uml_seq_http_multithread": r"""
@startuml
actor Browser
Browser -> Dispatcher : GET /hello
Dispatcher -> Queue : push(job)
Worker -> Queue : pop(job)
Worker -> Parser : parse_http_request()
Parser -> Router : route(path)
Router -> Worker : generate_response()
Worker -> Browser : HTTP/1.1 200 OK
@enduml
""",
}

# ---------------------------------------------------------------------------
# Fonction : écrire la PUML
# ---------------------------------------------------------------------------
def write_puml(name: str, content: str):
    puml_path = UML_DIR / f"{name}.puml"
    with open(puml_path, "w") as f:
        f.write(content.strip() + "\n")
    print(f"✔ PUML généré : {puml_path.name}")
    return puml_path

# ---------------------------------------------------------------------------
# Conversion PUML → SVG (dark/light)
# ---------------------------------------------------------------------------
def generate_svg(puml_file: Path):
    base = puml_file.stem
    light_svg = UML_DIR / f"{base}.svg"
    dark_svg  = UML_DIR / f"{base}_dark.svg"

    # Light SVG
    subprocess.run([
        "plantuml", "-tsvg", "-o", ".", str(puml_file)
    ], check=True)
    print(f"  → SVG Light : {light_svg.name}")

    # Dark mode SVG
    subprocess.run([
        "plantuml", "-tsvg", "-o", ".", "-Dskinparam backgroundColor=#1e1e1e",
        "-Dskinparam ArrowColor=white", "-Dskinparam FontColor=white",
        str(puml_file)
    ], check=True)
    dark_svg.rename(UML_DIR / f"{base}_dark.svg")
    print(f"  → SVG Dark : {dark_svg.name}")

# ---------------------------------------------------------------------------
# Suppression fichiers obsolètes
# ---------------------------------------------------------------------------
BAD_PATTERNS = [
    r"uml_seq_mono.*",
    r"uml_seq_multi.*",
    r"uml_seq_http_mono_thread.*",
    r"uml_seq_http_multi_thread.*",
    r"UML_Sequence.*",
]

def cleanup_old_files():
    print("\n🧹 Nettoyage anciens fichiers UML…")
    for f in UML_DIR.iterdir():
        name = f.stem
        for pat in BAD_PATTERNS:
            if re.match(pat, name):
                print(f"  → Suppression : {f.name}")
                f.unlink()
                break

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("\n=== GÉNÉRATION UML ===")
    cleanup_old_files()

    for name, content in UML_DEFINITIONS.items():
        puml_path = write_puml(name, content)
        generate_svg(puml_path)

    print("\n✔ UML générés et normalisés avec succès !\n")

if __name__ == "__main__":
    main()


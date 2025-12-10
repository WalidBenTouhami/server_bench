#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GENERATE UML — NINJA PRO VERSION
--------------------------------
✔ Nomenclature auto : tcp_monothread / tcp_multithread / http_monothread / http_multithread
✔ Génération PUML + SVG Light
✔ Génération SVG Dark via thème PlantUML (!theme cyborg)
✔ Nettoyage fichiers obsolètes
✔ Idempotent et robuste
"""

import subprocess
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
UML_DIR = ROOT
PROJECT_ROOT = ROOT.parent.parent

# ============================================
# RÈGLES DE NOMMAGE OFFICIELLES
# ============================================
UML_FILES = {
    "tcp_monothread": "uml_seq_tcp_monothread.puml",
    "tcp_multithread": "uml_seq_tcp_multithread.puml",
    "http_monothread": "uml_seq_http_monothread.puml",
    "http_multithread": "uml_seq_http_multithread.puml",
}

# ============================================
# UTIL : STYLE LOG
# ============================================
def log(info):
    print(f"⚡ {info}")

def warn(info):
    print(f"⚠️  {info}")

def ok(info):
    print(f"✔ {info}")

def err(info):
    print(f"❌ {info}")

# ============================================
# CLEAN : suppression anciens UML
# ============================================
def cleanup_old_files():
    log("Nettoyage anciens fichiers UML…")
    for f in UML_DIR.iterdir():
        if (
            f.name.startswith("uml_seq")
            and not f.name.endswith(".puml")
            and not f.name.endswith("_dark.svg")
        ):
            ok(f"Suppression : {f.name}")
            f.unlink()

# ============================================
# GÉNÉRATION SVG LIGHT + DARK
# ============================================
def generate_svg(puml: Path):
    base = puml.stem
    svg_light = UML_DIR / f"{base}.svg"
    svg_dark = UML_DIR / f"{base}_dark.svg"

    # --- SVG Light ---
    log(f"Génération SVG Light : {svg_light.name}")
    subprocess.run(["plantuml", "-tsvg", puml], cwd=UML_DIR)

    if not svg_light.exists():
        err(f"Échec génération Light : {svg_light.name}")
        return

    # --- SVG Dark ---
    dark_puml = UML_DIR / f"{base}_dark_temp.puml"
    dark_puml.write_text("!theme cyborg\n" + puml.read_text())

    log(f"Génération SVG Dark : {svg_dark.name}")
    subprocess.run(["plantuml", "-tsvg", dark_puml], cwd=UML_DIR)

    dark_temp_svg = UML_DIR / f"{base}_dark_temp.svg"
    if dark_temp_svg.exists():
        dark_temp_svg.rename(svg_dark)
        ok(f"SVG Dark : {svg_dark.name}")
    else:
        warn("SVG Dark non généré.")

    dark_puml.unlink(missing_ok=True)

# ============================================
# GÉNÉRATION PUML
# ============================================
def generate_puml():
    for key, filename in UML_FILES.items():
        puml_path = UML_DIR / filename

        content = ""
        if "tcp_monothread" in key:
            content = """
@startuml
actor Client
Client -> Server : CONNECT TCP
Server -> Server : traitement()
Server --> Client : réponse
@enduml
            """

        elif "tcp_multithread" in key:
            content = """
@startuml
actor Client
Client -> Dispatcher : CONNECT
Dispatcher -> Queue : push(job)
Worker -> Queue : pop(job)
Worker -> Client : réponse
@enduml
            """

        elif "http_monothread" in key:
            content = """
@startuml
actor Browser
Browser -> Server : GET /index
Server -> Server : parse_http()
Server -> Browser : HTTP/1.1 200 OK
@enduml
            """

        elif "http_multithread" in key:
            content = """
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
            """

        puml_path.write_text(content.strip())
        ok(f"PUML généré : {puml_path.name}")

        generate_svg(puml_path)

# ============================================
# MAIN
# ============================================
def main():
    print("\n=== GÉNÉRATION UML (VERSION NINJA PRO) ===\n")
    cleanup_old_files()
    generate_puml()
    print("\n✔ UML générés avec succès\n")

if __name__ == "__main__":
    main()


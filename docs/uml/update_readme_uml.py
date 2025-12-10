#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
update_readme_uml.py
--------------------
Met automatiquement à jour les balises UML dans README.md.
Idempotent, stable, version PRO.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
UML_DIR = ROOT / "docs/uml"

SECTIONS = {
    "uml_architecture": "uml_architecture.svg",
    "uml_queue": "uml_queue.svg",
    "uml_threads": "uml_threads.svg",
    "tcp_mono": "uml_seq_tcp_monothread.svg",
    "tcp_multi": "uml_seq_tcp_multithread.svg",
    "http_mono": "uml_seq_http_monothread.svg",
    "http_multi": "uml_seq_http_multithread.svg",
}

def update_readme():
    content = README.read_text()

    for key, file in SECTIONS.items():
        svg = f"docs/uml/{file}"
        pattern = rf"<img src=\".*{key}.*\""
        replacement = f"<img src=\"{svg}\" width=\"900\">"
        content = re.sub(pattern, replacement, content)

    README.write_text(content)
    print("✔ README.md mis à jour")

if __name__ == "__main__":
    update_readme()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script officiel de reconstruction du projet.

Fonctions :
  ✔ régénère uniquement les fichiers HTTP (http.c/.h + serveurs HTTP)
  ✔ NE modifie PAS le Makefile ni queue.c/serveurs TCP
  ✔ exécute create_http_files.py
  ✔ lance make clean + make -j
  ✔ exécute les tests unitaires
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd, cwd=None):
    print(f"\n➡️  {cmd}")
    ret = subprocess.call(cmd, shell=True, cwd=cwd or ROOT)
    if ret != 0:
        print(f"❌ Commande échouée : {cmd}")
        sys.exit(ret)


def main():
    print("🔄 Reconstruction du projet TCP + HTTP…")

    create_http = ROOT / "create_http_files.py"
    if not create_http.exists():
        print("❌ create_http_files.py introuvable !")
        sys.exit(1)

    # 1) Regénération HTTP
    run(f"python3 {create_http}")

    # 2) Compilation propre
    run("make clean")
    run("make -j$(nproc)")

    # 3) Tests unitaires
    run("make test")

    print("\n🎉 Projet reconstruit avec succès ! Aucun fichier critique écrasé.\n")


if __name__ == "__main__":
    main()


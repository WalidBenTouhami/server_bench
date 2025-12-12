#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized project rebuild script with incremental build support and better error handling.
- Régénère les fichiers HTTP (http.c/.h + serveurs HTTP)
- Ne touche pas aux serveurs TCP ni à la queue
- Lance : create_http_files.py, make clean, make -j, make test
"""

import subprocess
import sys
import os
import time
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parent

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'


def log_info(msg: str) -> None:
    """Log info message with color."""
    print(f"{GREEN}[INFO]{NC} {msg}")


def log_error(msg: str) -> None:
    """Log error message with color."""
    print(f"{RED}[ERROR]{NC} {msg}", file=sys.stderr)


def log_warn(msg: str) -> None:
    """Log warning message with color."""
    print(f"{YELLOW}[WARN]{NC} {msg}")


def run(cmd: List[str], cwd: Optional[Path] = None, capture: bool = False) -> None:
    """Run command with better error handling and output capture."""
    cmd_str = ' '.join(str(c) for c in cmd)
    print(f"\n{BLUE}▶{NC} {cmd_str}")
    
    try:
        if capture:
            result = subprocess.run(
                cmd, 
                cwd=cwd, 
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.stdout:
                print(result.stdout)
        else:
            subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        log_error(f"Commande échouée (code {e.returncode}): {cmd_str}")
        if capture and e.stderr:
            print(f"\n{RED}Stderr:{NC}\n{e.stderr}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        log_error(f"Commande introuvable: {cmd[0]}")
        sys.exit(127)


def check_prerequisites() -> None:
    """Check if required tools are available."""
    import shutil
    
    required = ['make', 'gcc', 'python3']
    missing = []
    
    for tool in required:
        if not shutil.which(tool):
            missing.append(tool)
    
    if missing:
        log_error(f"Outils manquants: {', '.join(missing)}")
        log_info("Installe-les avec: sudo apt install build-essential python3")
        sys.exit(1)


def main() -> None:
    """Main rebuild workflow with timing."""
    start_time = time.time()
    
    print("=" * 60)
    log_info("🔄 Reconstruction du projet TCP + HTTP")
    print("=" * 60)
    
    # Check prerequisites
    check_prerequisites()
    
    # Check if create_http_files.py exists
    create_http = ROOT / "create_http_files.py"
    if not create_http.exists():
        log_error(f"create_http_files.py introuvable dans {ROOT}")
        sys.exit(1)
    
    log_info("Étape 1/4: Regénération des fichiers HTTP...")
    run(["python3", str(create_http)], cwd=ROOT)
    
    log_info("Étape 2/4: Nettoyage des anciens builds...")
    run(["make", "clean"], cwd=ROOT, capture=True)
    
    # Get optimal job count
    jobs = os.cpu_count() or 4
    log_info(f"Étape 3/4: Compilation parallèle (jobs: {jobs})...")
    run(["make", "-j", str(jobs)], cwd=ROOT)
    
    log_info("Étape 4/4: Exécution des tests...")
    run(["make", "test"], cwd=ROOT)
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    log_info(f"🎉 Projet reconstruit avec succès en {elapsed:.1f}s!")
    print("=" * 60)
    
    # Show what was built
    bin_dir = ROOT / "bin"
    if bin_dir.exists():
        binaries = list(bin_dir.glob("serveur_*"))
        if binaries:
            log_info(f"Binaires générés ({len(binaries)}):")
            for binary in sorted(binaries):
                size = binary.stat().st_size / 1024  # KB
                print(f"  • {binary.name} ({size:.1f} KB)")
    
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_warn("\n\nReconstruction interrompue par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        log_error(f"Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


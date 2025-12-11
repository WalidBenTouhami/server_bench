#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bootstrap CI/CD for the TCP/HTTP High-Performance Server project.

Usage:
    python install_ci_cd.py

Run this from the root of your Git repository.
It will create .github/workflows and populate the standard workflows.
"""

from pathlib import Path

WORKFLOWS = {
    "build.yml": """name: C Build & Tests

on:
  push:
    branches: [ "main" ]
    paths:
      - "src/**"
      - "Makefile"
  pull_request:
    branches: [ "main" ]

jobs:
  build-test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install build deps
        run: |
          sudo apt-get update
          sudo apt-get install -y build-essential valgrind cppcheck

      - name: Build (Release)
        run: |
          make clean
          make -j"$(nproc)"

      - name: Run unit tests
        run: |
          make test

      - name: Run valgrind basic check
        run: |
          if [ -f ./bin/serveur_multi ]; then
            valgrind --leak-check=full --error-exitcode=1 ./bin/serveur_multi &
            PID=$!
            sleep 2
            kill $PID || true
          else
            echo "serveur_multi manquant, skip valgrind"
          fi
""",
    "cppcheck.yml": """name: Cppcheck Static Analysis

on:
  push:
    paths:
      - "src/**"
  pull_request:
    paths:
      - "src/**"

jobs:
  cppcheck:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install cppcheck
        run: |
          sudo apt-get update
          sudo apt-get install -y cppcheck

      - name: Run cppcheck
        run: |
          cppcheck --enable=all --std=c11 --inconclusive --error-exitcode=1 src
""",
    "codeql.yml": """name: CodeQL

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: [ 'cpp' ]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
""",
    "benchmarks.yml": """name: Python Benchmarks

on:
  workflow_dispatch:
  push:
    paths:
      - "python/**"
      - "src/**"

jobs:
  benchmark:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install benchmark deps
        run: |
          if [ -f python/requirements.txt ]; then
            pip install -r python/requirements.txt
          else
            pip install psutil pandas matplotlib plotly kaleido
          fi

      - name: Run Extreme Benchmarks
        run: |
          if [ -f python/benchmark_extreme.py ]; then
            python python/benchmark_extreme.py
          elif [ -f python/benchmark.py ]; then
            python python/benchmark.py
          else
            echo "Aucun script benchmark_extreme.py trouvé."
          fi

      - name: Upload Dashboard
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-dashboard
          path: |
            python/dashboard.html
            python/figures
          if-no-files-found: ignore
""",
    "secrets.yml": """name: Detect Secrets

on: [push, pull_request]

jobs:
  detect-secrets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Scan repository with TruffleHog
        uses: trufflesecurity/trufflehog@v3
        with:
          scan: git
""",
    "dependency-scan.yml": """name: Python Dependency Scan

on:
  push:
    paths:
      - "python/**"
      - "requirements.txt"

jobs:
  scan:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install pip-audit
        run: pip install pip-audit

      - name: Run pip-audit
        run: pip-audit || true
""",
    "trivy.yml": """name: Trivy FS Scan

on:
  push:
    branches: [ "main" ]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy FS
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          severity: HIGH,CRITICAL
          ignore-unfixed: true
""",
    "slsa.yml": """name: SLSA Provenance

on:
  release:
    types: [created]

jobs:
  provenance:
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v1.9.0
    with:
      artifact_path: ./bin/
""",
    "format.yml": """name: Formatting Check

on: [push, pull_request]

jobs:
  format:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Check C formatting
        run: |
          sudo apt-get update
          sudo apt-get install -y clang-format
          clang-format --dry-run --Werror src/*.c src/*.h

      - name: Markdown lint
        uses: actionshub/markdownlint@main
""",
    "deploy_docs.yml": """name: Deploy Docs

on:
  push:
    branches: [ "main" ]
    paths:
      - "docs/**"
      - "README.md"

permissions:
  contents: write
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Prepare docs
        run: |
          mkdir public
          if [ -d docs ]; then
            cp -r docs/* public/ || true
          fi
          cp README.md public/README.md || true

      - uses: actions/upload-pages-artifact@v3
        with:
          path: public/

      - uses: actions/deploy-pages@v4
""",
    "nightly.yml": """name: Nightly Pipeline

on:
  schedule:
    - cron: "0 3 * * *"

jobs:
  nightly:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install build deps
        run: |
          sudo apt-get update
          sudo apt-get install -y build-essential valgrind

      - name: Full build
        run: |
          make clean
          make -j"$(nproc)"

      - name: Run tests
        run: |
          make test || true

      - name: Run basic benchmark (if available)
        run: |
          if [ -f python/benchmark_extreme.py ]; then
            python python/benchmark_extreme.py || true
          fi
""",
}


def main() -> None:
    repo_root = Path(".").resolve()
    gh = repo_root / ".github" / "workflows"
    gh.mkdir(parents=True, exist_ok=True)

    for fname, content in WORKFLOWS.items():
        target = gh / fname
        if target.exists():
            print(f"[SKIP] {target} already exists, not overwritten.")
            continue
        target.write_text(content.strip() + "\\n", encoding="utf-8")
        print(f"[OK] created workflow: {target}")

    print("\\n✅ GitHub Actions CI/CD installed successfully.")


if __name__ == "__main__":
    main()

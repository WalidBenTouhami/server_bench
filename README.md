# 🚀 Serveur TCP & HTTP Hautes Performances — C/POSIX

## ⚡ Extreme Edition — Multi-threading • Queue FIFO • Benchmarks • UML • Mermaid • CI/CD

---

<p align="center">
  <img src="https://img.shields.io/badge/C89-POSIX-blue?style=flat-square"/>
  <img src="https://img.shields.io/badge/MultiThreading-pthreads-purple?style=flat-square"/>
  <img src="https://img.shields.io/badge/HTTP-1.1-orange?style=flat-square"/>
  <img src="https://img.shields.io/badge/Benchmark-Python3-yellow?style=flat-square"/>
  <img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square"/>
</p>

---

# 🔧 **Badges GitHub Actions CI/CD (Advanced)**

| Workflow                                 | Badge                                                                                                                                         |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Build & Test (GCC + Make + Valgrind)** | ![Build](https://img.shields.io/github/actions/workflow/status/WalidBenTouhami/server_project/build.yml?branch=main\&style=flat-square)       |
| **Static Analysis (Cppcheck)**           | ![Cppcheck](https://img.shields.io/github/actions/workflow/status/WalidBenTouhami/server_project/cppcheck.yml?branch=main\&style=flat-square) |
| **CodeQL Security Scan**                 | ![CodeQL](https://img.shields.io/github/actions/workflow/status/WalidBenTouhami/server_project/codeql.yml?branch=main\&style=flat-square)     |
| **Python Benchmarks CI**                 | ![Bench](https://img.shields.io/github/actions/workflow/status/WalidBenTouhami/server_project/benchmarks.yml?branch=main\&style=flat-square)  |

---

# 📚 Table des matières automatique

* [🎥 GIF Démonstrations](#-gif-démonstrations)
* [📦 Projet — Version FR/EN](#-projet--version-fren)
* [🧠 Diagrams Mermaid intégrés](#-diagrams-mermaid-intégrés)
* [📊 Benchmarks](#-benchmarks)
* [🛠 Installation](#-installation)
* [⚙ Exécution](#-exécution)
* [🧪 Tests & Validation](#-tests--validation)
* [📡 API HTTP](#-api-http)
* [📂 Architecture du projet](#-architecture-du-projet)
* [🚀 Pipeline DevOps complet](#-pipeline-devops-complet)
* [🔧 Intégration CI/CD — Workflows GitHub](#-intégration-cicd--workflows-github)
* [👤 Auteurs](#-auteurs)
* [📜 Licence](#-licence)

---

# 🎥 GIF Démonstrations

### Multi-thread server execution

![server-multi](docs/gif/server_multi.gif)

### Benchmark execution

![bench](docs/gif/benchmark.gif)

---

# 📦 **Projet — Version FR/EN**

## 🇫🇷 Version Française

Ce projet implémente **4 serveurs réseau haute performance** :

| Serveur            | Protocole | Architecture        |
| ------------------ | --------- | ------------------- |
| serveur_mono       | TCP       | mono-thread         |
| serveur_multi      | TCP       | multi-thread + FIFO |
| serveur_mono_http  | HTTP 1.1  | mono-thread         |
| serveur_multi_http | HTTP 1.1  | multi-thread + FIFO |

Fonctionnalités clés :

✔ Queue FIFO thread-safe
✔ Multi-thread performant (workers + dispatcher)
✔ HTTP parser minimaliste robuste
✔ Benchmarks Python avancés
✔ Dashboard interactif Plotly
✔ UML + Diagrammes Mermaid
✔ CI/CD complet GitHub Actions

---

## 🇬🇧 English Summary

This project provides **4 high-performance network servers** based on:

✔ POSIX sockets
✔ Multi-thread worker pool
✔ Thread-safe FIFO queue
✔ Minimal HTTP 1.1 parser
✔ Full benchmarking suite
✔ Automated DevOps pipeline & CI/CD

---

# 🧠 Diagrams Mermaid intégrés

## 1) Architecture Globale

```mermaid
flowchart LR
    A["Clients"] --> B["accept()"]
    B --> C["Queue FIFO (mutex + condvar)"]
    C --> D["Worker 1"]
    C --> E["Worker 2"]
    C --> F["Worker N"]
    D --> G["Traitement"]
    E --> G
    F --> G
    G --> H["send()"]
```

---

## 2) Queue FIFO Thread-Safe

```mermaid
classDiagram
    class queue_t {
        queue_node_t* head
        queue_node_t* tail
        pthread_mutex_t mutex
        pthread_cond_t not_empty
        pthread_cond_t not_full
        size_t size
        size_t size_max
        +push(void*)
        +void* pop()
    }

    class queue_node_t {
        void* data
        queue_node_t* next
    }

    queue_t --> queue_node_t
```

---

# 📊 Benchmarks

Auto-générés par les scripts Python :

![Throughput](python/figures/1-throughput.png)
![Latency P99](python/figures/2-latency_p99.png)
![CPU](python/figures/3-cpu.png)
![Memory](python/figures/4-memory.png)

---

# 🛠 Installation

```bash
sudo apt install build-essential python3 python3-venv python3-pip
git clone https://github.com/WalidBenTouhami/server_project.git
cd server_project
make -j$(nproc)
```

---

# ⚙ Exécution

```bash
make run_mono
make run_multi
make run_mono_http
make run_multi_http
```

---

# 🧪 Tests & Validation

```bash
make test
valgrind --leak-check=full ./bin/serveur_multi
valgrind --tool=helgrind ./bin/serveur_multi
make debug
```

---

# 📡 API HTTP

| Route    | Description   |
| -------- | ------------- |
| `/`      | Accueil       |
| `/hello` | JSON          |
| `/time`  | Horodatage    |
| `/stats` | Stats workers |

---

# 📂 Architecture du projet

```
src/
├── http.c / http.h
├── queue.c / queue.h
├── serveur_mono.c
├── serveur_multi.c
├── serveur_mono_http.c
└── serveur_multi_http.c
```

---

# 🚀 Pipeline DevOps complet

Pipeline interactif :

```bash
./scripts/run_interactive.sh
```

Il réalise automatiquement :

✔ Génération HTTP
✔ Compilation optimisée O3 + LTO
✔ UML Mermaid + PlantUML
✔ PPTX + PDF + Reveal.js
✔ Stress-tests
✔ Benchmarks extrêmes
✔ Monitoring CPU/mémoire
✔ CI/CD GitHub Actions
✔ Kill multi-services propre

---

# 🔧 Intégration CI/CD — Workflows GitHub

Les workflows sont fournis dans :

```
.github/workflows/
├── build.yml
├── cppcheck.yml
├── codeql.yml
└── benchmarks.yml
```

Pour installer automatiquement :

```bash
python3 install_ci_cd.py
```

---

# 👤 Auteurs

| Auteur             | Rôle                    | Expertise                |
| ------------------ | ----------------------- | ------------------------ |
| Walid Ben Touhami  | DevOps, Multi-threading | High-performance systems |
| Yassin Ben Aoun    | HTTP parsing            | Network protocols        |
| Ghada Sakouhi      | FIFO Queue, UML         | Software architecture    |
| Islem Ben Chaabene | TCP mono-thread         | Systems programming      |

---

# 📜 Licence

```
MIT License — Academic Use Only
```

---



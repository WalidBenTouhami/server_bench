# 🚀 Serveur TCP & HTTP Hautes Performances — C/POSIX

## ⚡ Extreme Edition — Multi-threading · Queue FIFO · Benchmarks · UML · Mermaid · CI/CD

---

<p align="center">
  <img src="https://img.shields.io/badge/C89-POSIX-blue?style=flat-square"/>
  <img src="https://img.shields.io/badge/Multithreading-pthreads-purple?style=flat-square"/>
  <img src="https://img.shields.io/badge/HTTP-1.1-orange?style=flat-square"/>
  <img src="https://img.shields.io/badge/Benchmark-Python3-yellow?style=flat-square"/>
  <img src="https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square"/>
</p>

---

## 🔧 Badges GitHub Actions (CI/CD)

| Workflow        | Status |
|-----------------|--------|
| Build & Tests   | ![Build](https://img.shields.io/github/actions/workflow/status/WalidBenTouhami/SERVER_BENCH/build.yml?branch=main&style=flat-square) |
| Cppcheck        | ![Cppcheck](https://img.shields.io/github/actions/workflow/status/WalidBenTouhami/SERVER_BENCH/cppcheck.yml?branch=main&style=flat-square) |
| CodeQL          | ![CodeQL](https://img.shields.io/github/actions/workflow/status/WalidBenTouhami/SERVER_BENCH/codeql.yml?branch=main&style=flat-square) |
| Benchmarks      | ![Bench](https://img.shields.io/github/actions/workflow/status/WalidBenTouhami/SERVER_BENCH/benchmarks.yml?branch=main&style=flat-square) |
| Deploy Docs     | ![Deploy](https://img.shields.io/github/actions/workflow/status/WalidBenTouhami/SERVER_BENCH/deploy_docs.yml?branch=main&style=flat-square) |


🔥 **Throughput actuel :**

<img src="https://raw.githubusercontent.com/WalidBenTouhami/SERVER_BENCH/main/python/figures/THROUGHPUT_LIVE.png" width="350"/>

**Documentation en ligne** → <https://walidbentouhami.github.io/SERVER_BENCH/>

---

## 📚 Table des matières

* [🎥 GIF Démonstrations](#gif-démonstrations)
* [📦 Projet — Version FR/EN](#projet-version-fren)
* [🧠 Mermaid Diagrams](#mermaid-diagrams)
* [📊 Benchmarks](#benchmarks)
* [🛠 Installation](#installation)
* [⚙ Exécution](#exécution)
* [🧪 Tests & Validation](#tests-validation)
* [🚀 Optimisations Appliquées](#optimisations-appliquées)
* [📡 API HTTP](#api-http)
* [📂 Architecture du projet](#architecture-du-projet)
* [🚀 Pipeline DevOps complet](#pipeline-devops-complet)
* [👤 Auteurs](#auteurs)
* [📜 Licence](#licence)

---

## 🎥 GIF Démonstrations

### Serveur TCP Multi-thread

<!-- ![server-multi](docs/gif/server_multi.gif) -->
_GIF demonstration will be added soon._

### Stress Test & Benchmarks

<!-- ![bench](docs/gif/benchmark.gif) -->
_GIF demonstration will be added soon._

---

## 📦 Projet — Version FR/EN

## 🇫🇷 Version Française

Ce projet implémente **4 serveurs haute performance** :

| Serveur              | Protocole | Architecture        |
| -------------------- | --------- | ------------------- |
| `serveur_mono`       | TCP       | Mono-thread         |
| `serveur_multi`      | TCP       | Multi-thread + FIFO |
| `serveur_mono_http`  | HTTP 1.1  | Mono-thread         |
| `serveur_multi_http` | HTTP 1.1  | Multi-thread + FIFO |

Fonctionnalités incluses :

✔ Multi-threading (pthread)
✔ Queue FIFO thread-safe
✔ HTTP router minimal
✔ Benchmarks Python (latence, throughput, CPU, mémoire)
✔ UML + Mermaid
✔ CI/CD GitHub complet
✔ Pipeline DevOps automatique
✔ PPTX & PDF auto-générés

---

## 🇬🇧 English Summary

This project provides **4 high-performance network servers** using POSIX sockets:

✔ Multi-thread worker pool
✔ Thread-safe FIFO queue
✔ Minimal HTTP 1.1 router
✔ Python benchmark suite
✔ Full DevOps automation

---

## 🧠 Mermaid Diagrams

### Architecture Globale

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

### Queue FIFO

```mermaid
classDiagram
    class queue_t {
        +push()
        +pop()
        +destroy()
        size
        size_max
    }
    class queue_node_t {
        data
        next
    }
    queue_t --> queue_node_t
```

### Dispatcher & Workers

```mermaid
sequenceDiagram
    Client->>Dispatcher: accept()
    Dispatcher->>Queue: push(fd)
    Queue->>Worker: pop(fd)
    Worker->>Client: send()
```

---

## 📊 Benchmarks

### Throughput

![tput](python/figures/1-throughput.png)

### Latence P99

![latency](python/figures/2-latency_p99.png)

### CPU

![cpu](python/figures/3-cpu.png)

### Memory

![mem](python/figures/4-memory.png)

---

## 🛠 Installation

```bash
sudo apt install build-essential python3 python3-venv python3-pip
git clone https://github.com/WalidBenTouhami/SERVER_BENCH.git
cd SERVER_BENCH
make -j$(nproc)
```

---

## ⚙ Exécution

```bash
make run_mono
make run_multi
make run_mono_http
make run_multi_http
```

---

## 🧪 Tests & Validation

```bash
make test                                        # Run unit tests
make MODE=debug all                              # Build with sanitizers
valgrind --leak-check=full ./bin/serveur_multi  # Memory leak check
valgrind --tool=helgrind ./bin/serveur_multi    # Thread safety check
```

## 🚀 Optimisations Appliquées

Le projet utilise des optimisations avancées pour des performances maximales :

### Compilation
- `-O3 -march=native` : Optimisations agressives pour l'architecture cible
- `-flto` : Link-Time Optimization pour optimisations inter-modules
- `-ffast-math` : Optimisations mathématiques rapides
- `-funroll-loops` : Déroulement de boucles pour réduire les branchements
- `-DNDEBUG` : Désactive les assertions pour réduire le overhead

### Sécurité et Robustesse
- Signal handling : `SIGPIPE` ignoré pour gérer les connexions fermées
- `MSG_NOSIGNAL` : Évite les crashes sur envoi vers socket fermé
- Mutex avec `PTHREAD_MUTEX_ERRORCHECK` : Détection d'erreurs de verrouillage
- Format security : `-Wformat=2 -Wformat-security` pour prévenir les vulnérabilités

### Linker
- `-Wl,-O1` : Optimisations au niveau du linker
- `-Wl,--as-needed` : Réduit les dépendances inutiles

---

## 📡 API HTTP

| Route    | Description  |
| -------- | ------------ |
| `/`      | Accueil      |
| `/hello` | JSON         |
| `/time`  | Timestamp    |
| `/stats` | Statistiques |

Example:

```json
{
  "msg": "Hello from HTTP server",
  "requests": 128,
  "worker": 3
}
```

---

## 📂 Architecture du projet

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

## 🚀 Pipeline DevOps complet

### Exécution globale

```bash
./scripts/run_interactive.sh
```

Il exécute automatiquement :

✔ Génération HTTP
✔ Build C (O3 + LTO)
✔ Génération UML
✔ Génération PPTX + PDF
✔ Démarrage serveurs
✔ Tests `/`, `/hello`, `/time`, `/stats`
✔ Stress tests TCP/HTTP
✔ Benchmarks extrêmes
✔ Monitoring CPU/RAM
✔ Kill propre multi-thread

---

## 👤 Auteurs

| Auteur                 | Rôle                                | Expertise                |
| ---------------------- | ----------------------------------- | ------------------------ |
| **Walid Ben Touhami**  | DevOps, Multi-threading, Benchmarks | High-performance systems |
| **Yassin Ben Aoun**    | HTTP parser                         | Protocol engineering     |
| **Ghada Sakouhi**      | FIFO queue, UML                     | Software architecture    |
| **Islem Ben Chaabene** | TCP mono-thread                     | POSIX networking         |

---

## 📜 Licence

```
MIT License — Academic Use Only
```

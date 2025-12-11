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

# 🔧 Badges GitHub Actions (CI/CD)

# SERVER_BENCH – Comparaison mono-thread vs multi-thread (C + pthread)

![Build & Tests](https://github.com/WalidBenTouhami/SERVER_BENCH/workflows/Build%20&%20Test/badge.svg)
![Cppcheck](https://github.com/WalidBenTouhami/SERVER_BENCH/workflows/Cppcheck%20Analysis/badge.svg)
![CodeQL](https://github.com/WalidBenTouhami/SERVER_BENCH/workflows/CodeQL%20Security%20Scan/badge.svg)
![Benchmarks](https://github.com/WalidBenTouhami/SERVER_BENCH/workflows/Benchmarks/badge.svg)

**Performance actuelle (mise à jour automatique) :**  
![Throughput](https://img.shields.io/badge/throughput-XXX%20req/s-brightgreen)  
(rafraîchit à chaque push sur main)

---

# 📚 Table des matières

* [🎥 GIF Démonstrations](#-gif-démonstrations)
* [📦 Projet — Version FR/EN](#-projet--version-fren)
* [🧠 Mermaid Diagrams](#-mermaid-diagrams)
* [📊 Benchmarks](#-benchmarks)
* [🛠 Installation](#-installation)
* [⚙ Exécution](#-exécution)
* [🧪 Tests & Validation](#-tests--validation)
* [📡 API HTTP](#-api-http)
* [📂 Architecture du projet](#-architecture-du-projet)
* [🚀 Pipeline DevOps complet](#-pipeline-devops-complet)
* [👤 Auteurs](#-auteurs)
* [📜 Licence](#-licence)

---

# 🎥 GIF Démonstrations

### Serveur TCP Multi-thread

![server-multi](docs/gif/server_multi.gif)

### Stress Test & Benchmarks

![bench](docs/gif/benchmark.gif)

---

# 📦 Projet — Version FR/EN

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

# 🧠 Mermaid Diagrams

## Architecture Globale

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

## Queue FIFO

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

## Dispatcher & Workers

```mermaid
sequenceDiagram
    Client->>Dispatcher: accept()
    Dispatcher->>Queue: push(fd)
    Queue->>Worker: pop(fd)
    Worker->>Client: send()
```

---

# 📊 Benchmarks

### Throughput

![tput](python/figures/1-throughput.png)

### Latence P99

![latency](python/figures/2-latency_p99.png)

### CPU

![cpu](python/figures/3-cpu.png)

### Memory

![mem](python/figures/4-memory.png)

---

# 🛠 Installation

```bash
sudo apt install build-essential python3 python3-venv python3-pip
git clone https://github.com/WalidBenTouhami/SERVER_BENCH.git
cd SERVER_BENCH
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

### Exécution globale :

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

# 👤 Auteurs

| Auteur                 | Rôle                                | Expertise                |
| ---------------------- | ----------------------------------- | ------------------------ |
| **Walid Ben Touhami**  | DevOps, Multi-threading, Benchmarks | High-performance systems |
| **Yassin Ben Aoun**    | HTTP parser                         | Protocol engineering     |
| **Ghada Sakouhi**      | FIFO queue, UML                     | Software architecture    |
| **Islem Ben Chaabene** | TCP mono-thread                     | POSIX networking         |

---

# 📜 Licence

```
MIT License — Academic Use Only
```

---


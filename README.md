````markdown
# 🚀 Serveur TCP & HTTP Hautes Performances — C/POSIX  
### Projet Ingénieur — Multi-threading • Queue FIFO Générique • Benchmarks • Dashboard HTML

---

## 🏷️ Badges GitHub

![Build](https://img.shields.io/badge/build-passing-brightgreen?style=flat-square)
![C Language](https://img.shields.io/badge/language-C-blue?style=flat-square)
![POSIX](https://img.shields.io/badge/POSIX-Compliant-orange?style=flat-square)
![Threads](https://img.shields.io/badge/Multi--threading-pthreads-purple?style=flat-square)
![Python](https://img.shields.io/badge/Benchmark-Python3-yellow?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)

---

# 📦 Résumé du projet

Ce projet implémente **quatre serveurs réseau haute performance** en C/POSIX :

| Serveur | Protocole | Architecture | Fichier |
|--------|-----------|--------------|---------|
| `serveur_mono` | TCP | Mono-thread | `src/serveur_mono.c` |
| `serveur_multi` | TCP | Multi-thread + queue | `src/serveur_multi.c` |
| `serveur_mono_http` | HTTP 1.1 | Mono-thread | `src/serveur_mono_http.c` |
| `serveur_multi_http` | HTTP 1.1 | Multi-thread + queue | `src/serveur_multi_http.c` |

Le projet inclut :

- ✔ File FIFO générique thread-safe (`queue.c`)
- ✔ Parseur HTTP robuste (`http.c`)
- ✔ Benchmarks Python (latence, CPU, RAM, RPS)
- ✔ Dashboard interactif Plotly HTML
- ✔ Scripts DevOps (run_all, monitoring, auto-rebuild)
- ✔ Présentation académique PPTX + script PDF

---

# 🛠️ INSTALLATION (INSTALL.md intégré)

## 1️⃣ Prérequis système (Ubuntu / Debian)

```bash
sudo apt update
sudo apt install -y build-essential python3 python3-venv python3-pip curl netcat make git
````

Dépendances Python pour les benchmarks :

```bash
pip install psutil pandas matplotlib plotly kaleido
```

---

## 2️⃣ Cloner le projet

```bash
git clone https://github.com/.../SERVER_BENCH.git
cd server_project
```

---

## 3️⃣ Compiler les serveurs C

Mode normal :

```bash
make clean
make -j$(nproc)
```

Mode debug avec sanitizers :

```bash
make debug
```

---

## 4️⃣ Installer l’environnement Python

```bash
cd python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 5️⃣ Lancer un benchmark complet

Depuis la racine du projet :

```bash
./scripts/run_all.sh
```

Les résultats seront générés dans :

```
python/results.json  
python/results.xlsx  
python/figures/*.png
```

Et un Dashboard interactif :

```bash
python/dashboard.html
```

---

## 6️⃣ Tester le projet

```bash
./scripts/run_tests.sh
```

---

## 7️⃣ Nettoyage complet

```bash
./scripts/clean_project.sh
```

---

# 📂 Arborescence du projet

```text
server_project/
├── src/
│   ├── serveur_mono.c
│   ├── serveur_multi.c
│   ├── serveur_mono_http.c
│   ├── serveur_multi_http.c
│   ├── queue.c / queue.h
│   ├── http.c / http.h
│
├── python/
│   ├── benchmark.py
│   ├── client_stress.py
│   ├── dashboard.html
│   ├── results.json / results.xlsx
│   ├── figures/
│
├── presentation/
│   ├── presentation_finale_serveur.pptx
│   ├── script_presentation.pdf
│   └── backgrounds/
│
├── scripts/
│   ├── run_all.sh
│   ├── run_servers.sh
│   ├── run_tests.sh
│   ├── clean_project.sh
│   └── open_dashboard.sh
│
└── rebuild_project.py
```

---

# 🧠 UML — Architecture & Threads

## UML 1 — Architecture globale

![UML Architecture](docs/uml_architecture.png)

---

## UML 2 — Queue FIFO Thread-Safe

![UML Queue FIFO](docs/uml_queue.png)

---

## UML 3 — Multi-threading (Workers & Dispatcher)

![UML Threads](docs/uml_threads.png)

---

# 📊 Résultats Benchmark (images générées)

## Throughput (req/s)

![Throughput](python/figures/1-throughput.png)

## Latence P99

![Latency P99](python/figures/2-latency_p99.png)

## CPU Usage

![CPU](python/figures/3-cpu.png)

## Mémoire

![Memory](python/figures/4-memory.png)

## Speedup Multi-thread

![Speedup](python/figures/5-speedup.png)

---

# 🧪 Tests unitaires

```bash
make test
```

* Test FIFO
* Test multi-thread
* Tests d’intégrité sur queue

---

# 🛠️ Exécution des serveurs

```bash
make run_mono
make run_multi
make run_mono_http
make run_multi_http
```

Stopper :

```bash
make kill_servers
```

---

# 🎤 Présentation académique

```
presentation/presentation_finale_serveur.pptx
presentation/script_presentation.pdf
```

Inclut :

* UML
* Architecture serveur
* Expérimentation
* Analyse des performances

---

# 👤 **Auteurs — Membres du groupe**

| Membre                 | Rôle                                     | Expertise                           |
| ---------------------- | ---------------------------------------- | ----------------------------------- |
| **Walid Ben Touhami**  | Serveur multi-thread, Benchmarks, DevOps | Multi-threading, queue, performance |
| **Yassin Ben Aoun**    | Parsing HTTP, serveurs HTTP              | HTTP 1.1, robustesse protocolaire   |
| **Ghada Sakouhi**      | Architecture & queue générique           | UML, synchronisation                |
| **Islem Ben Chaabene** | Serveur TCP mono-thread                  | C bas-niveau, sockets               |

---

# 📄 Licence

```
MIT License — usage académique et professionnel autorisé
```


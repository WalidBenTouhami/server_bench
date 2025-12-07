```markdown
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
- ✔ Dashboard HTML Plotly interactif
- ✔ Scripts DevOps (run_all, build, clean, monitoring)
- ✔ Présentation PPTX + script PDF (générés automatiquement)

---

# 📂 Arborescence du projet

*(structure automatiquement récupérée du système)*

```

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
│   │   ├── 1-throughput.png
│   │   ├── 2-latency_p99.png
│   │   ├── 3-cpu.png
│   │   ├── 4-memory.png
│   │   ├── 5-speedup.png
│
├── presentation/
│   ├── presentation_finale_serveur.pptx
│   ├── script_presentation.pdf
│   └── backgrounds/
│
├── tests/
│   └── test_queue.c
│
├── scripts/
│   ├── run_all.sh
│   ├── run_servers.sh
│   ├── run_tests.sh
│   ├── clean_project.sh
│   ├── kill_servers.sh
│   └── open_dashboard.sh
│
└── rebuild_project.py

````

---

# 🧠 UML — Architecture & Threads

## UML 1 — Architecture globale du système
*(Place l'image suivante dans : `docs/uml_architecture.png`)*

```markdown
![UML Architecture](docs/uml_architecture.png)
````

## UML 2 — Queue FIFO Thread-Safe

*(Place l'image suivante dans : `docs/uml_queue.png`)*

```markdown
![UML Queue FIFO](docs/uml_queue.png)
```

## UML 3 — Multi-threading (Workers & Dispatcher)

*(Place l'image suivante dans : `docs/uml_threads.png`)*

```markdown
![UML Multi-thread](docs/uml_threads.png)
```

Je peux te générer les images UML maintenant si tu veux.

---

# 📊 Résultats de benchmarks (visualisation)

Les graphiques générés automatiquement sont affichés dans le README :

## Throughput (req/s)

![Throughput](python/figures/1-throughput.png)

## Latence P99

![Latency P99](python/figures/2-latency_p99.png)

## CPU usage

![CPU usage](python/figures/3-cpu.png)

## Mémoire utilisée

![Memory](python/figures/4-memory.png)

## Speedup multi-thread vs mono-thread

![Speedup](python/figures/5-speedup.png)

---

# 🧪 Tests unitaires

Exécuter :

```bash
make test
```

Testé :

* Queue FIFO générique
* Multi-thread safety
* Shutdown propre

---

# 🛠️ Compilation & Exécution

## Compiler entièrement

```bash
make clean
make -j$(nproc)
```

## Lancer un serveur :

```bash
make run_mono
make run_multi
make run_mono_http
make run_multi_http
```

## Arrêter tous les serveurs :

```bash
make kill_servers
```

---

# 📈 Pipeline Benchmark + Dashboard

Exécution complète :

```bash
./scripts/run_all.sh
```

Génération du dashboard :

```bash
python3 python/export_html.py
xdg-open python/dashboard.html
```

---

# 🎤 Présentation académique

La présentation PPTX + script PDF sont générés dans :

```
presentation/presentation_finale_serveur.pptx
presentation/script_presentation.pdf
```

---

# 👤 **Auteurs — Membres du groupe (ordre officiel)**

| Membre                 | Rôle principal                                      | Expertise                                           |
| ---------------------- | --------------------------------------------------- | --------------------------------------------------- |
| **Walid Ben Touhami**  | Serveur multi-thread TCP + HTTP, Benchmarks, DevOps | Multi-threading, Queue FIFO, Analyse de Performance |
| **Yassin Ben Aoun**    | Serveur HTTP, Parsing, Implémentation routing       | HTTP 1.1, parsing, robustesse protocolaire          |
| **Ghada Sakouhi**      | Architecture globale & Queue FIFO générique         | Structures de données, synchronisation, UML         |
| **Islem Ben Chaabene** | Serveur TCP mono-thread, protocole binaire          | C bas-niveau, sockets TCP, optimisation             |

### Profil global des auteurs :

**Ingénieurs Informatique — Systèmes & Réseaux**
Expertise :
• Serveurs C hautes performances
• Multi-threading / Pthreads
• Analyse de performances (CPU/RAM/RPS)
• Benchmarking Python
• DevOps & automatisation

---

# 📄 Licence

MIT — libre d’usage académique et professionnel.

```

---

# 🎁 **Souhaites-tu que je génère aussi :**

### ✔ les images UML automatiquement ?  
### ✔ les fichiers PNG de la UML en style "Engineering Blueprint" ?  
### ✔ la version anglaise du README ?  
### ✔ un badge GitHub Actions "Build & Test" ?  

Il suffit de dire : **"Génère les images UML"** ou autre.
```


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

## 🎥 Vidéo de Présentation

📺 **[Voir la présentation complète (8 min)](https://youtube.com/...)** 
*(À venir : démonstration live, architecture, résultats benchmarks)*

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

## 🔍 Comparaison Technique : Mono-thread vs Multi-thread

### Architecture Globale

| Aspect | Mono-thread | Multi-thread |
|--------|-------------|--------------|
| **Modèle** | Séquentiel | Producer-Consumer |
| **Threads** | 1 (main) | 9 (1 dispatcher + 8 workers) |
| **Synchronisation** | Aucune | Mutex + Cond Vars |
| **Complexité** | Simple | Moyenne |
| **Scalabilité** | Limitée (1 CPU) | Excellente (N CPUs) |
| **Latence** | Haute sous charge | Basse et stable |
| **Throughput** | ~10 req/s | ~50-80 req/s |

### 1. Création et Gestion des Threads

#### Mono-thread (`serveur_mono.c`)
```c
// Traitement strictement séquentiel
for (;;) {
    int client_fd = accept(server_fd, ...);
    
    // BLOQUANT : traite 1 client à la fois
    recv(client_fd, &number_net, sizeof(number_net), 0);
    traitement_lourd();  // 100ms CPU-bound
    send(client_fd, &result_net, sizeof(result_net), 0);
    
    close(client_fd);
    // Client suivant seulement APRÈS fermeture
}
```

**Limitation :** Avec 100 clients, temps total = 100 × 100ms = **10 secondes**

#### Multi-thread (`serveur_multi.c`)
```c
// Pool de 8 workers permanents
pthread_t workers[WORKER_COUNT];
for (int i = 0; i < WORKER_COUNT; i++) {
    pthread_create(&workers[i], NULL, worker_func, NULL);
}

// Dispatcher enfile les connexions
for (;;) {
    int client_fd = accept(server_fd, ...);
    
    int *fd_ptr = malloc(sizeof(int));
    *fd_ptr = client_fd;
    
    // NON-BLOQUANT : délègue au worker
    queue_push(&job_queue, fd_ptr);
    // accept() immédiatement disponible
}
```

**Avantage :** Avec 100 clients sur 8 workers, temps total ≈ (100÷8) × 100ms = **1.25 secondes** → **8× plus rapide**

### 2. Synchronisation et Zones Critiques

#### Queue FIFO Thread-Safe (`queue.c`)
```c
int queue_push(queue_t *q, void *data) {
    pthread_mutex_lock(&q->mutex);  // 🔒 ENTRÉE ZONE CRITIQUE
    
    // Attente active si queue pleine
    while (!q->shutdown && q->size >= q->size_max) {
        pthread_cond_wait(&q->not_full, &q->mutex);
    }
    
    if (q->shutdown) {
        pthread_mutex_unlock(&q->mutex);
        return -1;
    }
    
    // Insertion sécurisée dans la liste chaînée
    queue_node_t *node = malloc(sizeof(queue_node_t));
    node->data = data;
    node->next = NULL;
    
    if (q->tail)
        q->tail->next = node;
    else
        q->head = node;
    
    q->tail = node;
    q->size++;
    
    pthread_cond_signal(&q->not_empty);  // Réveille un worker
    pthread_mutex_unlock(&q->mutex);     // 🔓 SORTIE ZONE CRITIQUE
    
    return 0;
}
```

**Protection garantie :**
- ✅ Aucun accès concurrent à `q->head`, `q->tail`, `q->size`
- ✅ Atomicité de l'insertion
- ✅ Signalisation automatique des workers en attente

### 3. Boucle de Traitement

#### Mono-thread : Latence Cumulative
```
Client 1 : accept → traitement (100ms) → réponse → close
Client 2 :           ATTEND 100ms        → traitement (100ms) → réponse
Client 3 :                    ATTEND 200ms         → traitement (100ms)
...
Client 100:                   ATTEND 9900ms        → traitement
```
**Latence Client 100 = 9.9 secondes** ❌

#### Multi-thread : Parallélisme Réel
```
Worker 1 : Client 1 (100ms) | Client 9  (100ms) | Client 17 (100ms) ...
Worker 2 : Client 2 (100ms) | Client 10 (100ms) | Client 18 (100ms) ...
Worker 3 : Client 3 (100ms) | Client 11 (100ms) | Client 19 (100ms) ...
...
Worker 8 : Client 8 (100ms) | Client 16 (100ms) | Client 24 (100ms) ...
```
**Latence Client 100 ≈ 1.25 secondes** ✅

### 4. Structures de Données

#### File FIFO Bornée
```c
typedef struct queue {
    queue_node_t *head;           // Premier élément
    queue_node_t *tail;           // Dernier élément
    pthread_mutex_t mutex;        // Protection globale
    pthread_cond_t not_empty;     // Signal pour workers
    pthread_cond_t not_full;      // Signal pour dispatcher
    bool shutdown;                // Drapeau d'arrêt propre
    size_t size;                  // Nombre d'éléments actuels
    size_t size_max;              // Capacité maximale (128)
} queue_t;
```

**Propriétés :**
- ✅ Capacité bornée → évite saturation mémoire
- ✅ FIFO strict → équité de traitement
- ✅ Thread-safe → utilisable par N threads
- ✅ Shutdown gracieux → arrêt propre sans deadlock

### 5. Résultats Expérimentaux

#### Benchmark avec 300 Clients Simultanés

| Métrique | Mono-thread | Multi-thread | Amélioration |
|----------|-------------|--------------|--------------|
| **Throughput** | 9.2 req/s | 78.5 req/s | **8.5×** 🚀 |
| **Latence P50** | 5.4 s | 0.12 s | **45×** 🚀 |
| **Latence P99** | 29.1 s | 0.48 s | **60×** 🚀 |
| **CPU Usage** | 12% (1 core) | 95% (8 cores) | **8× mieux** |
| **Memory** | 8 MB | 12 MB | +50% acceptable |

#### Speedup Théorique vs Réel
```
Speedup théorique = N workers = 8
Speedup réel mesuré ≈ 6.5-7.0

Perte de 12-18% due à :
- Overhead de synchronisation (mutex lock/unlock)
- Context switching entre threads
- Contention sur accept() (un seul socket)
```

### 6. Cas d'Usage

#### Quand utiliser Mono-thread ?
- ✅ Charge faible (<10 req/s)
- ✅ Traitement ultra-rapide (<1ms)
- ✅ Simplicité critique (embedded systems)
- ✅ Pas besoin de scalabilité

#### Quand utiliser Multi-thread ?
- ✅ Charge élevée (>50 req/s)
- ✅ Traitement CPU-bound (calculs lourds)
- ✅ Latence critique (temps de réponse)
- ✅ Exploitation multi-cœurs obligatoire

---

# 🛠️ Installation

## ⚡ Installation Rapide

```bash
# Installation complète en une commande
./setup.sh
```

Ou manuellement :

## 1️⃣ Prérequis système (Ubuntu / Debian)

```bash
sudo apt update
sudo apt install -y build-essential python3 python3-venv python3-pip curl netcat make git
```

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

![UML Architecture](docs/docs/uml/uml_architecture.png)

---

## UML 2 — Queue FIFO Thread-Safe

![UML Queue FIFO](docs/docs/uml/uml_queue.png)

---

## UML 3 — Multi-threading (Workers & Dispatcher)

![UML Multi-thread](docs/docs/uml/uml_threads.png)

### Versions SVG (optionnel — plus propre pour LaTeX et zoom HD)

```html
<img src="docs/docs/uml/uml_architecture.svg" width="600">
<img src="docs/docs/uml/uml_queue.svg" width="600">
<img src="docs/docs/uml/uml_threads.svg" width="600">

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

## 🧪 Tests et Validation

### Tests Unitaires
```bash
make test              # Tests queue FIFO
./bin/test_queue       # Tests d'intégrité
```

### Tests de Charge
```bash
# Benchmark complet (10→300 clients)
./scripts/run_all.sh

# Test manuel mono-thread
./bin/serveur_mono &
python3 python/client_stress.py --port 5050 --clients 100

# Test manuel multi-thread
./bin/serveur_multi &
python3 python/client_stress.py --port 5051 --clients 300
```

### Validation Mémoire
```bash
# Détection fuites mémoires
valgrind --leak-check=full ./bin/serveur_multi

# Détection race conditions
valgrind --tool=helgrind ./bin/serveur_multi

# Mode debug avec sanitizers
make debug
./bin/serveur_multi
```

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

## 🚧 Défis Techniques Rencontrés

Voir documentation détaillée : [docs/CHALLENGES.md](docs/CHALLENGES.md)

**Résumé des principaux défis :**
- 🐛 **Race Conditions** : Accès concurrent à la queue → solution avec mutex
- 🔒 **Deadlock** : Shutdown bloqué → solution avec pthread_cond_broadcast()
- 💾 **Fuites Mémoires** : malloc sans free → détection Valgrind
- ⚡ **Saturation** : Queue trop petite → augmentation capacité
- 🔧 **Cohérence** : Données corrompues → stratégies d'atomicité

**Outils utilisés :**
- Valgrind (memcheck + helgrind)
- GDB avec breakpoints conditionnels
- AddressSanitizer + UndefinedBehaviorSanitizer
- Tests de charge progressifs (10→500 clients)

---

# 📄 Licence

```
MIT License — usage académique et professionnel autorisé
```


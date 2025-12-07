#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
create_http_files.py
--------------------
Script avancé de génération des fichiers HTTP côté C.

Il (re)génère :

  - src/http.h
  - src/http.c
  - src/serveur_mono_http.c
  - src/serveur_multi_http.c

Fonctionnalités HTTP :
  - parseur de requêtes (méthode, chemin, query)
  - réponses HTTP 1.1 avec Content-Length + Connection
  - routage simple : "/", "/hello", "/time", "/stats"
  - multi-thread HTTP avec queue FIFO (queue.h)
  - worker() corrigé (return NULL) et sécurisé
"""

from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
SRC_DIR.mkdir(exist_ok=True)

HTTP_H_PATH = SRC_DIR / "http.h"
HTTP_C_PATH = SRC_DIR / "http.c"
SERVEUR_MONO_HTTP_PATH = SRC_DIR / "serveur_mono_http.c"
SERVEUR_MULTI_HTTP_PATH = SRC_DIR / "serveur_multi_http.c"


# ======================================================================
# http.h
# ======================================================================

HTTP_H_TEMPLATE = textwrap.dedent(r"""
#ifndef HTTP_H
#define HTTP_H

/**
 * parse_http_request
 * ------------------
 * Extrait la méthode, le chemin et la query string à partir d'une
 * requête HTTP brute.
 *
 * - req    : buffer contenant la requête brute
 * - method : buffer de sortie pour la méthode (GET, POST, ...)
 * - path   : buffer de sortie pour le chemin (/hello, /time, ...)
 * - query  : buffer de sortie pour la query (?a=1&b=2)
 */
void parse_http_request(const char *req, char *method, char *path, char *query);

/**
 * send_http_response
 * ------------------
 * Envoie une réponse HTTP 1.1 complète :
 *
 *   HTTP/1.1 <status>\r\n
 *   Content-Type: <content_type>\r\n
 *   Content-Length: <len(body)>\r\n
 *   Connection: <connection>\r\n
 *
 *   <body>
 *
 * "connection" peut être "close" ou "keep-alive".
 */
void send_http_response(int client_fd,
                        const char *status,
                        const char *content_type,
                        const char *body,
                        const char *connection);

#endif
""")


# ======================================================================
# http.c
# ======================================================================

HTTP_C_TEMPLATE = textwrap.dedent(r"""
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include "http.h"

void parse_http_request(const char *req, char *method, char *path, char *query) {
    char line[1024] = {0};

    /* On récupère la première ligne : "GET /chemin?x=1 HTTP/1.1" */
    const char *end = strstr(req, "\r\n");
    if (end) {
        size_t len = end - req;
        if (len > sizeof(line) - 1) {
            len = sizeof(line) - 1;
        }
        memcpy(line, req, len);
        line[len] = '\0';
    } else {
        strncpy(line, req, sizeof(line) - 1);
    }

    char url[512] = {0};
    sscanf(line, "%15s %511s", method, url);

    /* Séparation chemin / query */
    char *qmark = strchr(url, '?');
    if (qmark) {
        *qmark = '\0';
        strncpy(query, qmark + 1, 255);
        query[255] = '\0';
    } else {
        query[0] = '\0';
    }

    strncpy(path, url, 255);
    path[255] = '\0';
}

void send_http_response(int client_fd,
                        const char *status,
                        const char *content_type,
                        const char *body,
                        const char *connection) {

    if (connection == NULL) {
        connection = "close";
    }

    char header[2048];
    size_t body_len = strlen(body);

    int n = snprintf(header, sizeof(header),
                     "HTTP/1.1 %s\r\n"
                     "Content-Type: %s\r\n"
                     "Content-Length: %zu\r\n"
                     "Connection: %s\r\n"
                     "\r\n",
                     status, content_type, body_len, connection);

    if (n < 0) {
        return;
    }

    send(client_fd, header, (size_t)n, 0);
    if (body_len > 0) {
        send(client_fd, body, body_len, 0);
    }
}
""")


# ======================================================================
# serveur_mono_http.c (router + endpoints)
# ======================================================================

SERVEUR_MONO_HTTP_TEMPLATE = textwrap.dedent(r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>

#include "http.h"

#define HTTP_PORT 8080
#define BACKLOG   32
#define BUF_SIZE  4096

/* Statistiques simples (non concurrentielles car mono-thread) */
static unsigned long total_requests   = 0;
static unsigned long hello_requests   = 0;
static unsigned long not_found_count  = 0;

static void route_request(int client_fd,
                          const char *method,
                          const char *path,
                          const char *query) {
    (void)query; /* pas encore utilisé */

    total_requests++;

    if (strcmp(path, "/") == 0) {
        const char *body =
            "<html><body>"
            "<h1>Serveur HTTP mono-thread</h1>"
            "<p>Routes disponibles :</p>"
            "<ul>"
            "<li><a href=\"/hello\">/hello</a></li>"
            "<li><a href=\"/time\">/time</a></li>"
            "<li><a href=\"/stats\">/stats</a></li>"
            "</ul>"
            "</body></html>";
        send_http_response(client_fd, "200 OK", "text/html", body, "close");
    }
    else if (strcmp(path, "/hello") == 0) {
        hello_requests++;
        const char *body =
            "{"
            "\"msg\":\"Bonjour depuis serveur HTTP mono-thread\","
            "\"method\":\"GET\""
            "}";
        send_http_response(client_fd, "200 OK", "application/json", body, "close");
    }
    else if (strcmp(path, "/time") == 0) {
        char body[256];
        time_t now = time(NULL);
        struct tm tm_now;
        localtime_r(&now, &tm_now);
        char buf[64];
        strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", &tm_now);

        snprintf(body, sizeof(body),
                 "{"
                 "\"server_time\":\"%s\""
                 "}",
                 buf);
        send_http_response(client_fd, "200 OK", "application/json", body, "close");
    }
    else if (strcmp(path, "/stats") == 0) {
        char body[256];
        snprintf(body, sizeof(body),
                 "{"
                 "\"total_requests\":%lu,"
                 "\"hello_requests\":%lu,"
                 "\"not_found\":%lu"
                 "}",
                 total_requests, hello_requests, not_found_count);
        send_http_response(client_fd, "200 OK", "application/json", body, "close");
    }
    else {
        not_found_count++;
        send_http_response(client_fd,
                           "404 Not Found",
                           "text/plain",
                           "404 NOT FOUND",
                           "close");
    }

    printf("[HTTP-MONO] %s %s (total=%lu)\n", method, path, total_requests);
}

int main(void) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return EXIT_FAILURE;
    }

    int opt = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("setsockopt SO_REUSEADDR");
    }

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family      = AF_INET;
    addr.sin_port        = htons(HTTP_PORT);
    addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(server_fd);
        return EXIT_FAILURE;
    }

    if (listen(server_fd, BACKLOG) < 0) {
        perror("listen");
        close(server_fd);
        return EXIT_FAILURE;
    }

    printf("[HTTP-MONO] Serveur HTTP mono-thread en écoute sur port %d\n", HTTP_PORT);

    for (;;) {
        int client_fd = accept(server_fd, NULL, NULL);
        if (client_fd < 0) {
            perror("accept");
            continue;
        }

        /* Timeout lecture pour éviter les connexions qui bloquent */
        struct timeval tv;
        tv.tv_sec = 5;
        tv.tv_usec = 0;
        setsockopt(client_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

        for (;;) {
            char buffer[BUF_SIZE];
            ssize_t n = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
            if (n <= 0) {
                break; /* fin de connexion ou timeout */
            }
            buffer[n] = '\0';

            char method[16] = {0};
            char path[256]  = {0};
            char query[256] = {0};

            parse_http_request(buffer, method, path, query);
            route_request(client_fd, method, path, query);

            /* Ici, on ferme après une requête.
             * Pour un vrai keep-alive, on pourrait garder
             * la connexion ouverte si l'en-tête "Connection: keep-alive"
             * est présent, mais ce n'est pas nécessaire pour le projet.
             */
            break;
        }

        close(client_fd);
    }

    close(server_fd);
    return EXIT_SUCCESS;
}
""")


# ======================================================================
# serveur_multi_http.c (worker corrigé + stats concurrentes)
# ======================================================================

SERVEUR_MULTI_HTTP_TEMPLATE = textwrap.dedent(r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <pthread.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>

#include "queue.h"
#include "http.h"

#define HTTP_PORT    8081        /* Port HTTP multi-thread */
#define BACKLOG      64
#define WORKERS      8
#define BUF_SIZE     4096

typedef struct {
    int client_fd;
} job_t;

static queue_t job_queue;

/* Statistiques globales, protégées par mutex */
static pthread_mutex_t stats_mutex = PTHREAD_MUTEX_INITIALIZER;
static unsigned long total_requests   = 0;
static unsigned long hello_requests   = 0;
static unsigned long not_found_count  = 0;

static void stats_increment_total(void) {
    pthread_mutex_lock(&stats_mutex);
    total_requests++;
    pthread_mutex_unlock(&stats_mutex);
}

static void stats_increment_hello(void) {
    pthread_mutex_lock(&stats_mutex);
    hello_requests++;
    pthread_mutex_unlock(&stats_mutex);
}

static void stats_increment_not_found(void) {
    pthread_mutex_lock(&stats_mutex);
    not_found_count++;
    pthread_mutex_unlock(&stats_mutex);
}

static void get_stats(unsigned long *total,
                      unsigned long *hello,
                      unsigned long *not_found) {
    pthread_mutex_lock(&stats_mutex);
    *total     = total_requests;
    *hello     = hello_requests;
    *not_found = not_found_count;
    pthread_mutex_unlock(&stats_mutex);
}

static void route_request(int client_fd,
                          const char *method,
                          const char *path,
                          const char *query) {
    (void)query;

    stats_increment_total();

    if (strcmp(path, "/") == 0) {
        const char *body =
            "<html><body>"
            "<h1>Serveur HTTP multi-thread</h1>"
            "<p>Routes disponibles :</p>"
            "<ul>"
            "<li><a href=\"/hello\">/hello</a></li>"
            "<li><a href=\"/time\">/time</a></li>"
            "<li><a href=\"/stats\">/stats</a></li>"
            "</ul>"
            "</body></html>";
        send_http_response(client_fd, "200 OK", "text/html", body, "close");
    }
    else if (strcmp(path, "/hello") == 0) {
        stats_increment_hello();
        const char *body =
            "{"
            "\"msg\":\"Hello depuis serveur HTTP multi-thread\","
            "\"worker\":\"pthread\""
            "}";
        send_http_response(client_fd, "200 OK", "application/json", body, "close");
    }
    else if (strcmp(path, "/time") == 0) {
        char body[256];
        time_t now = time(NULL);
        struct tm tm_now;
        localtime_r(&now, &tm_now);
        char buf[64];
        strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", &tm_now);

        snprintf(body, sizeof(body),
                 "{"
                 "\"server_time\":\"%s\""
                 "}",
                 buf);
        send_http_response(client_fd, "200 OK", "application/json", body, "close");
    }
    else if (strcmp(path, "/stats") == 0) {
        unsigned long t, h, nf;
        get_stats(&t, &h, &nf);
        char body[256];
        snprintf(body, sizeof(body),
                 "{"
                 "\"total_requests\":%lu,"
                 "\"hello_requests\":%lu,"
                 "\"not_found\":%lu"
                 "}",
                 t, h, nf);
        send_http_response(client_fd, "200 OK", "application/json", body, "close");
    }
    else {
        stats_increment_not_found();
        send_http_response(client_fd,
                           "404 Not Found",
                           "text/plain",
                           "404 NOT FOUND",
                           "close");
    }

    printf("[HTTP-MULTI] %s %s\n", method, path);
}

/**
 * worker
 * ------
 * Dépile un job de la queue, gère la connexion client (une ou plusieurs
 * requêtes), puis ferme le socket.
 */
static void* worker(void *arg) {
    (void)arg;

    for (;;) {
        job_t *job = (job_t*) queue_pop(&job_queue);
        if (!job) {
            /* Peut arriver si queue_shutdown est appelée.
             * Ici, on continue la boucle pour permettre un arrêt propre
             * si tu ajoutes un flag global plus tard.
             */
            continue;
        }

        int client_fd = job->client_fd;
        free(job);

        /* Timeout de réception pour éviter les connexions bloquées */
        struct timeval tv;
        tv.tv_sec = 5;
        tv.tv_usec = 0;
        setsockopt(client_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

        for (;;) {
            char buffer[BUF_SIZE];
            ssize_t n = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
            if (n <= 0) {
                break; /* fin connexion, timeout ou erreur */
            }
            buffer[n] = '\0';

            char method[16] = {0};
            char path[256]  = {0};
            char query[256] = {0};

            parse_http_request(buffer, method, path, query);
            route_request(client_fd, method, path, query);

            /* Pour simplifier : on traite une requête puis on ferme.
             * Pour un vrai keep-alive, il faudrait inspecter les headers
             * et éventuellement rester dans cette boucle.
             */
            break;
        }

        close(client_fd);
    }

    return NULL; /* important pour éviter le warning GCC */
}

int main(void) {
    queue_init(&job_queue, 128);

    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return EXIT_FAILURE;
    }

    int opt = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("setsockopt SO_REUSEADDR");
    }

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family      = AF_INET;
    addr.sin_port        = htons(HTTP_PORT);
    addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(server_fd);
        return EXIT_FAILURE;
    }

    if (listen(server_fd, BACKLOG) < 0) {
        perror("listen");
        close(server_fd);
        return EXIT_FAILURE;
    }

    printf("[HTTP-MULTI] Serveur HTTP multi-thread en écoute sur port %d\n", HTTP_PORT);

    pthread_t threads[WORKERS];
    for (int i = 0; i < WORKERS; i++) {
        if (pthread_create(&threads[i], NULL, worker, NULL) != 0) {
            perror("pthread_create");
            close(server_fd);
            return EXIT_FAILURE;
        }
    }

    /* Boucle d'acceptation */
    for (;;) {
        int client_fd = accept(server_fd, NULL, NULL);
        if (client_fd < 0) {
            perror("accept");
            continue;
        }

        job_t *job = (job_t*)malloc(sizeof(job_t));
        if (!job) {
            fprintf(stderr, "malloc failed\n");
            close(client_fd);
            continue;
        }
        job->client_fd = client_fd;

        if (queue_push(&job_queue, job) < 0) {
            fprintf(stderr, "queue_push failed\n");
            close(client_fd);
            free(job);
            continue;
        }
    }

    /* En pratique, ce code n'est pas atteint sans mécanisme d'arrêt propre */
    close(server_fd);
    queue_destroy(&job_queue);
    return EXIT_SUCCESS;
}
""")


# ======================================================================
# UTILITAIRES D'ÉCRITURE
# ======================================================================

def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✔ Fichier généré : {path}")


def main() -> None:
    print("──────────────────────────────────────────────")
    print("🛠  Génération des fichiers HTTP (version avancée)")
    print("Racine projet :", ROOT)
    print("──────────────────────────────────────────────")

    write_file(HTTP_H_PATH, HTTP_H_TEMPLATE)
    write_file(HTTP_C_PATH, HTTP_C_TEMPLATE)
    write_file(SERVEUR_MONO_HTTP_PATH, SERVEUR_MONO_HTTP_TEMPLATE)
    write_file(SERVEUR_MULTI_HTTP_PATH, SERVEUR_MULTI_HTTP_TEMPLATE)

    print("\n✅ Génération terminée. Commandes suggérées :")
    print("   make clean && make -j")
    print("   ./bin/serveur_mono_http   # HTTP mono-thread sur port 8080")
    print("   ./bin/serveur_multi_http  # HTTP multi-thread sur port 8081")


if __name__ == "__main__":
    main()


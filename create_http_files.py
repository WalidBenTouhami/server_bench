#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

SRC_DIR = "src"
os.makedirs(SRC_DIR, exist_ok=True)

print("📦 Génération des fichiers HTTP…")

# --------------------------------------------------------------------------
# http.h
# --------------------------------------------------------------------------
http_h = """#ifndef HTTP_H
#define HTTP_H

void parse_http_request(const char *req, char *method, char *path, char *query);
void send_http_response(int client_fd, const char *status,
                        const char *content_type, const char *body);

#endif
"""

# --------------------------------------------------------------------------
# http.c – version robuste HTTP/1.1
# --------------------------------------------------------------------------
http_c = r"""#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/socket.h>
#include "http.h"

void parse_http_request(const char *req, char *method, char *path, char *query) {
    char line[1024];
    const char *end = strpbrk(req, "\r\n");

    if (end) {
        size_t len = end - req;
        if (len >= sizeof(line)) len = sizeof(line) - 1;
        memcpy(line, req, len);
        line[len] = '\0';
    } else {
        strncpy(line, req, sizeof(line) - 1);
        line[sizeof(line) - 1] = '\0';
    }

    char url[512] = {0};
    sscanf(line, "%15s %511s", method, url);

    char *qmark = strchr(url, '?');
    if (qmark) {
        strcpy(query, qmark + 1);
        *qmark = '\0';
    } else {
        query[0] = '\0';
    }

    strcpy(path, url);
}

void send_http_response(int client_fd, const char *status,
                        const char *content_type, const char *body) {
    char header[4096];
    size_t body_len = strlen(body);

    snprintf(header, sizeof(header),
        "HTTP/1.1 %s\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %zu\r\n"
        "Connection: close\r\n"
        "\r\n",
        status, content_type, body_len
    );

    send(client_fd, header, strlen(header), 0);
    send(client_fd, body, body_len, 0);
}
"""

# --------------------------------------------------------------------------
# serveur_mono_http.c
# --------------------------------------------------------------------------
mono_http = r"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>
#include "http.h"

#define PORT 5050

int main(void) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return EXIT_FAILURE;
    }

    int opt = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("setsockopt");
    }

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family      = AF_INET;
    addr.sin_port        = htons(PORT);
    addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(server_fd);
        return EXIT_FAILURE;
    }

    if (listen(server_fd, 10) < 0) {
        perror("listen");
        close(server_fd);
        return EXIT_FAILURE;
    }

    printf("Serveur HTTP mono-thread sur port %d...\n", PORT);

    char buffer[4096];

    for (;;) {
        int client_fd = accept(server_fd, NULL, NULL);
        if (client_fd < 0) {
            perror("accept");
            continue;
        }

        int n = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
        if (n <= 0) {
            close(client_fd);
            continue;
        }
        buffer[n] = '\0';

        char method[16] = {0};
        char path[256]  = {0};
        char query[256] = {0};

        parse_http_request(buffer, method, path, query);
        printf("→ METHOD=%s | PATH=%s | QUERY=%s\n", method, path, query);

        if (strcmp(path, "/hello") == 0) {
            send_http_response(client_fd, "200 OK", "application/json",
                               "{\"msg\":\"Bonjour depuis mono-thread\"}");
        } else {
            send_http_response(client_fd, "404 Not Found", "text/plain",
                               "404 NOT FOUND");
        }

        close(client_fd);
    }

    return 0;
}
"""

# --------------------------------------------------------------------------
# serveur_multi_http.c
# --------------------------------------------------------------------------
multi_http = r"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>

#include "queue.h"
#include "http.h"

#define PORT        5051
#define WORKERS     8
#define BUFFER_SIZE 4096

typedef struct {
    int client_fd;
} job_t;

static queue_t job_queue;

static void* worker(void *arg) {
    (void)arg;

    for (;;) {
        job_t *job = (job_t*) queue_pop(&job_queue);
        if (!job) {
            continue;
        }

        char buffer[BUFFER_SIZE];
        int n = recv(job->client_fd, buffer, sizeof(buffer) - 1, 0);
        if (n <= 0) {
            close(job->client_fd);
            free(job);
            continue;
        }
        buffer[n] = '\0';

        printf("\n==== RAW HTTP REQUEST ====\n%s\n", buffer);

        char method[16] = {0};
        char path[256]  = {0};
        char query[256] = {0};

        parse_http_request(buffer, method, path, query);
        printf("METHOD='%s' | PATH='%s' | QUERY='%s'\n", method, path, query);

        if (strcmp(path, "/hello") == 0) {
            send_http_response(job->client_fd, "200 OK", "application/json",
                               "{\"msg\":\"Hello from multi-thread HTTP server\"}");
        } else {
            send_http_response(job->client_fd, "404 Not Found", "text/plain",
                               "404 NOT FOUND");
        }

        close(job->client_fd);
        free(job);
    }
}

int main(void) {
    queue_init(&job_queue, 64);

    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return EXIT_FAILURE;
    }

    int opt = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("setsockopt");
    }

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family      = AF_INET;
    addr.sin_port        = htons(PORT);
    addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(server_fd);
        return EXIT_FAILURE;
    }

    if (listen(server_fd, 50) < 0) {
        perror("listen");
        close(server_fd);
        return EXIT_FAILURE;
    }

    printf("Serveur HTTP multi-thread en écoute sur port %d...\n", PORT);

    pthread_t workers[WORKERS];
    for (int i = 0; i < WORKERS; i++) {
        if (pthread_create(&workers[i], NULL, worker, NULL) != 0) {
            perror("pthread_create");
            return EXIT_FAILURE;
        }
    }

    for (;;) {
        int client_fd = accept(server_fd, NULL, NULL);
        if (client_fd < 0) {
            perror("accept");
            continue;
        }

        job_t *job = malloc(sizeof(job_t));
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
        }
    }

    return 0;
}
"""

files = {
    "http.h": http_h,
    "http.c": http_c,
    "serveur_mono_http.c": mono_http,
    "serveur_multi_http.c": multi_http,
}

for name, content in files.items():
    path = os.path.join(SRC_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✔ Fichier généré : {path}")

print("\n🎉 Génération terminée : HTTP C files updated.\n")


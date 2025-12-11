
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

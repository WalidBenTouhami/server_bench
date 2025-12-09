#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <signal.h>
#include <pthread.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <errno.h>

#include "queue.h"
#include "http.h"

#define HTTP_PORT    8081
#define BACKLOG      64
#define WORKERS      8
#define BUF_SIZE     4096

/* -------------------------------------------------------------------------
 * Structure des jobs
 * -------------------------------------------------------------------------*/
typedef struct {
    int client_fd;
} job_t;

/* Queue de travail partagée */
static queue_t job_queue;

/* Flag d'exécution */
static volatile sig_atomic_t running = 1;

/* File descriptor du serveur */
static int server_fd = -1;

/* -------------------------------------------------------------------------
 * Statistiques globales protégées par mutex
 * -------------------------------------------------------------------------*/
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
                      unsigned long *not_found)
{
    pthread_mutex_lock(&stats_mutex);
    *total     = total_requests;
    *hello     = hello_requests;
    *not_found = not_found_count;
    pthread_mutex_unlock(&stats_mutex);
}

/* -------------------------------------------------------------------------
 * Handler SIGINT — Arrêt propre
 * -------------------------------------------------------------------------*/
static void handle_sigint(int sig) {
    (void)sig;
    printf("\n[HTTP-MULTI] 🔴 SIGINT reçu — arrêt en cours…\n");

    running = 0;

    if (server_fd >= 0) {
        close(server_fd);
        server_fd = -1;
    }

    queue_shutdown(&job_queue);
}

/* -------------------------------------------------------------------------
 * Route HTTP
 * -------------------------------------------------------------------------*/
static void route_request(int client_fd,
                          const char *method,
                          const char *path,
                          const char *query)
{
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
                 "{ \"server_time\":\"%s\" }", buf);

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

/* -------------------------------------------------------------------------
 * Thread worker
 * -------------------------------------------------------------------------*/
static void* worker(void *arg) {
    (void)arg;

    while (running) {

        job_t *job = (job_t*)queue_pop(&job_queue);

        if (!job) {
            if (!running)
                break;
            else
                continue;
        }

        int client_fd = job->client_fd;
        free(job);

        /* Timeout réception */
        struct timeval tv = { .tv_sec = 5, .tv_usec = 0 };
        setsockopt(client_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

        char buffer[BUF_SIZE];
        ssize_t n = recv(client_fd, buffer, sizeof(buffer) - 1, 0);

        if (n <= 0) {
            close(client_fd);
            continue;
        }

        buffer[n] = '\0';

        char method[16] = {0};
        char path[256]  = {0};
        char query[256] = {0};

        parse_http_request(buffer, method, path, query);
        route_request(client_fd, method, path, query);

        close(client_fd);
    }

    return NULL;
}

/* -------------------------------------------------------------------------
 * MAIN — Serveur HTTP multi-thread
 * -------------------------------------------------------------------------*/
int main(void) {

    signal(SIGINT, handle_sigint);

    queue_init(&job_queue, 128);

    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return EXIT_FAILURE;
    }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

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

    printf("[HTTP-MULTI] 🟢 Serveur HTTP multi-thread actif sur port %d\n", HTTP_PORT);

    /* Lancement des workers */
    pthread_t threads[WORKERS];
    for (int i = 0; i < WORKERS; i++) {
        pthread_create(&threads[i], NULL, worker, NULL);
    }

    /* Boucle d'acceptation */
    while (running) {

        int client_fd = accept(server_fd, NULL, NULL);

        if (!running)
            break;

        if (client_fd < 0) {
            if (errno == EINTR) continue;
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
            close(client_fd);
            free(job);
            continue;
        }
    }

    printf("[HTTP-MULTI] 🔵 Fermeture…\n");

    queue_shutdown(&job_queue);

    for (int i = 0; i < WORKERS; i++)
        pthread_join(threads[i], NULL);

    queue_destroy(&job_queue);

    if (server_fd >= 0)
        close(server_fd);

    printf("[HTTP-MULTI] 🟡 Serveur arrêté proprement.\n");

    return EXIT_SUCCESS;
}
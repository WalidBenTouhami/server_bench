#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <signal.h>
#include <string.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <time.h>
#include <stdint.h>
#include <pthread.h>
#include <errno.h>

#include "queue.h"

#define PORT 5051
#define BACKLOG 50
#define WORKER_COUNT 8
#define QUEUE_CAPACITY 128

static int server_fd = -1;
static queue_t job_queue;
static volatile sig_atomic_t running = 1;

/* ----------- Endianness ----------- */
static uint64_t htonll(uint64_t x) {
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    return __builtin_bswap64(x);
#else
    return x;
#endif
}

/* ----------- Simule une charge CPU ----------- */
static void traitement_lourd(void) {
    double x = 0.0;
    for (int i = 0; i < 100000; i++)
        x += sqrt(i);
    (void)x;

    /* Latence pseudo-aléatoire 10–100 ms */
    usleep((rand() % 90 + 10) * 1000);
}

/* ----------- Timestamp microsecondes ----------- */
static int64_t timestamp_us(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (int64_t)tv.tv_sec * 1000000LL + tv.tv_usec;
}

/* ----------- Handler SIGINT (Ctrl+C) ----------- */
static void handle_sigint(int sig) {
    (void)sig;
    running = 0;

    printf("\n[MULTI] 🔴 Signal SIGINT reçu — arrêt en cours…\n");

    if (server_fd >= 0) {
        close(server_fd);
        server_fd = -1;
    }

    /* Réveille tous les threads bloqués dans queue_pop() */
    queue_shutdown(&job_queue);
}

/* ===========================================================
   WORKER THREAD : dépile un job, traite un client, répond
   =========================================================== */
static void *worker_func(void *arg) {
    (void)arg;

    for (;;) {
        int *fd_ptr = (int*)queue_pop(&job_queue);

        /* Queue vide + shutdown → sortie propre */
        if (!fd_ptr) {
            if (!running)
                break;  
            else
                continue;
        }

        int client_fd = *fd_ptr;
        free(fd_ptr);

        int32_t number_net;
        ssize_t r = recv(client_fd, &number_net, sizeof(number_net), 0);

        if (r != sizeof(number_net)) {
            close(client_fd);
            continue;
        }

        int32_t number = ntohl(number_net);

        traitement_lourd();

        int32_t result_net = htonl(number * number);
        int64_t ts = timestamp_us();
        uint64_t ts_net = htonll((uint64_t)ts);

        send(client_fd, &result_net, sizeof(result_net), 0);
        send(client_fd, &ts_net, sizeof(ts_net), 0);

        close(client_fd);
    }

    return NULL;
}

/* ===========================================================
   MAIN SERVER — MULTI-THREAD + QUEUE FIFO
   =========================================================== */
int main(void) {
    signal(SIGINT, handle_sigint);
    srand((unsigned)time(NULL));

    queue_init(&job_queue, QUEUE_CAPACITY);

    /* Création socket serveur */
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        exit(EXIT_FAILURE);
    }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family      = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port        = htons(PORT);

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        exit(EXIT_FAILURE);
    }

    if (listen(server_fd, BACKLOG) < 0) {
        perror("listen");
        exit(EXIT_FAILURE);
    }

    printf("[MULTI] 🟢 Serveur multi-thread actif sur port %d\n", PORT);
    printf("[MULTI] Appuyer sur Ctrl+C pour arrêter proprement.\n");

    pthread_t workers[WORKER_COUNT];

    /* Lancement des workers */
    for (int i = 0; i < WORKER_COUNT; i++) {
        if (pthread_create(&workers[i], NULL, worker_func, NULL) != 0) {
            fprintf(stderr, "[MULTI] Erreur pthread_create\n");
            running = 0;
            queue_shutdown(&job_queue);
            exit(EXIT_FAILURE);
        }
    }

    /* Boucle principale */
    while (running) {

        struct sockaddr_in client;
        socklen_t len = sizeof(client);

        int client_fd = accept(server_fd, (struct sockaddr*)&client, &len);

        if (!running) break;

        if (client_fd < 0) {
            if (errno == EINTR) continue;  // accept interrompu par SIGINT
            perror("accept");
            continue;
        }

        int *fd_ptr = malloc(sizeof(int));
        if (!fd_ptr) {
            fprintf(stderr, "[MULTI] malloc failed\n");
            close(client_fd);
            continue;
        }

        *fd_ptr = client_fd;

        if (queue_push(&job_queue, fd_ptr) < 0) {
            close(client_fd);
            free(fd_ptr);
            break;
        }
    }

    /* Arrêt propre */
    running = 0;
    queue_shutdown(&job_queue);

    for (int i = 0; i < WORKER_COUNT; i++)
        pthread_join(workers[i], NULL);

    queue_destroy(&job_queue);

    printf("[MULTI] 🟡 Serveur multi-thread arrêté proprement.\n");

    return 0;
}

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
#include <errno.h>

#define PORT 5050
#define BACKLOG 50   /* Amélioré pour éviter saturation */

/* ---------- Variables globales pour shutdown propre ---------- */
static volatile sig_atomic_t running = 1;
static int server_fd = -1;

/* ---------- Conversion endian ---------- */
static uint64_t htonll(uint64_t x) {
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    return __builtin_bswap64(x);
#else
    return x;
#endif
}

/* ---------- Simule un traitement lourd ---------- */
static void traitement_lourd(void) {
    double x = 0.0;
    for (int i = 0; i < 100000; i++)
        x += sqrt(i);

    (void)x;
    usleep((rand() % 90 + 10) * 1000);
}

/* ---------- Timestamp us ---------- */
static int64_t timestamp_us(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (int64_t)tv.tv_sec * 1000000LL + tv.tv_usec;
}

/* ---------- Handler SIGINT propre ---------- */
static void handle_sigint(int sig) {
    (void)sig;
    running = 0;
    printf("\n[MONO] 🔴 Signal SIGINT reçu : arrêt en cours…\n");

    if (server_fd >= 0) {
        close(server_fd);
        server_fd = -1;
    }
}

/* ============================================================
   SERVEUR MONO-THREAD TCP
   ============================================================ */
int main(void) {

    /* Installation du handler */
    signal(SIGINT, handle_sigint);
    srand((unsigned)time(NULL));

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

    printf("[MONO] 🟢 Serveur mono-thread actif sur port %d\n", PORT);
    printf("[MONO] Appuyer sur Ctrl+C pour arrêter proprement.\n");

    /* Boucle principale */
    while (running) {

        struct sockaddr_in client;
        socklen_t len = sizeof(client);

        int client_fd = accept(server_fd, (struct sockaddr*)&client, &len);

        if (!running) break;

        if (client_fd < 0) {
            if (errno == EINTR) continue;  // interruption par signal → normal
            perror("accept");
            continue;
        }

        /* Lecture du nombre envoyé */
        int32_t number_net;
        ssize_t r = recv(client_fd, &number_net, sizeof(number_net), 0);

        if (r != sizeof(number_net)) {
            close(client_fd);
            continue;
        }

        int32_t number = ntohl(number_net);

        /* Traitement simulé */
        traitement_lourd();

        /* Résultat + timestamp */
        int32_t result_net = htonl(number * number);
        int64_t ts = timestamp_us();
        uint64_t ts_net = htonll((uint64_t)ts);

        send(client_fd, &result_net, sizeof(result_net), 0);
        send(client_fd, &ts_net, sizeof(ts_net), 0);

        close(client_fd);
    }

    printf("[MONO] 🟡 Fermeture du serveur mono-thread…\n");

    if (server_fd >= 0)
        close(server_fd);

    printf("[MONO] ✅ Arrêt propre effectué.\n");

    return 0;
}

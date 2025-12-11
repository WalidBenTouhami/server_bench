
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

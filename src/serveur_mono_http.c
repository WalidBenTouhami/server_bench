#include <stdio.h>
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

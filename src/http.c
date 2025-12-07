#include <stdio.h>
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

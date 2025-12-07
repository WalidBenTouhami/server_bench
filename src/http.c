
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

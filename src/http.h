#ifndef HTTP_H
#define HTTP_H

void parse_http_request(const char *req, char *method, char *path, char *query);
void send_http_response(int client_fd, const char *status,
                        const char *content_type, const char *body);

#endif

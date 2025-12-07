
#ifndef HTTP_H
#define HTTP_H

/**
 * parse_http_request
 * ------------------
 * Extrait la méthode, le chemin et la query string à partir d'une
 * requête HTTP brute.
 *
 * - req    : buffer contenant la requête brute
 * - method : buffer de sortie pour la méthode (GET, POST, ...)
 * - path   : buffer de sortie pour le chemin (/hello, /time, ...)
 * - query  : buffer de sortie pour la query (?a=1&b=2)
 */
void parse_http_request(const char *req, char *method, char *path, char *query);

/**
 * send_http_response
 * ------------------
 * Envoie une réponse HTTP 1.1 complète :
 *
 *   HTTP/1.1 <status>\r\n
 *   Content-Type: <content_type>\r\n
 *   Content-Length: <len(body)>\r\n
 *   Connection: <connection>\r\n
 *
 *   <body>
 *
 * "connection" peut être "close" ou "keep-alive".
 */
void send_http_response(int client_fd,
                        const char *status,
                        const char *content_type,
                        const char *body,
                        const char *connection);

#endif

#include "../src/http.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>

void test_parse_simple() {
    char method[256];
    char path[256];
    char query[256];

    const char *raw =
        "GET /hello?name=walid HTTP/1.1\r\n"
        "Host: localhost\r\n"
        "\r\n";

    parse_http_request(raw, method, path, query);
    assert(strcmp(method, "GET") == 0);
    assert(strcmp(path, "/hello") == 0);
    assert(strcmp(query, "name=walid") == 0);
}

void test_parse_no_query() {
    char method[256];
    char path[256];
    char query[256];

    const char *raw = "POST /api HTTP/1.1\r\n\r\n";

    parse_http_request(raw, method, path, query);
    assert(strcmp(method, "POST") == 0);
    assert(strcmp(path, "/api") == 0);
    assert(strcmp(query, "") == 0);
}

int main() {
    printf("Running HTTP tests…\n");

    test_parse_simple();
    test_parse_no_query();

    printf("All HTTP tests passed successfully.\n");
    return 0;
}
###############################################################################
#                           MAKEFILE PRO – C/POSIX SERVER (TCP + HTTP)
#                     Serveur Mono / Multi-thread + HTTP + Queue FIFO
#                     Auteur : Walid Ben Touhami (projet système)
###############################################################################

# Dossiers
SRC_DIR   := src
TEST_DIR  := tests
BUILD_DIR := build
BIN_DIR   := bin

# Compilateur & flags
CC       := gcc
CFLAGS   := -Wall -Wextra -O2 -pthread -I$(SRC_DIR)
DBGFLAGS := -g -fsanitize=address,undefined -DDEBUG -I$(SRC_DIR)
LDFLAGS  := -lm -pthread

# Fichiers sources C
SRC_FILES := $(wildcard $(SRC_DIR)/*.c)

# Objets compilés automatiquement
OBJ := $(SRC_FILES:$(SRC_DIR)/%.c=$(BUILD_DIR)/%.o)

# Programmes à générer
TARGETS := \
    $(BIN_DIR)/serveur_mono \
    $(BIN_DIR)/serveur_multi \
    $(BIN_DIR)/serveur_mono_http \
    $(BIN_DIR)/serveur_multi_http \
    $(BIN_DIR)/test_queue

HTTP_TARGETS := \
    $(BIN_DIR)/serveur_mono_http \
    $(BIN_DIR)/serveur_multi_http

# Tests unitaires
TEST_OBJ := $(TEST_DIR)/test_queue.o $(BUILD_DIR)/queue.o

# Couleurs terminal
GREEN  := \033[1;32m
BLUE   := \033[1;34m
YELLOW := \033[1;33m
RED    := \033[1;31m
RESET  := \033[0m

###############################################################################
#                           BUILD PAR DÉFAUT
###############################################################################
.PHONY: all
all: prep $(TARGETS)
	@echo "$(GREEN)[OK] Compilation complète réussie !$(RESET)"

###############################################################################
#                        PRÉPARATION DES DOSSIERS
###############################################################################
prep:
	@mkdir -p $(BUILD_DIR) $(BIN_DIR)

###############################################################################
#                          RÈGLES DE LINKING
###############################################################################

$(BIN_DIR)/serveur_mono: $(BUILD_DIR)/serveur_mono.o $(BUILD_DIR)/queue.o $(BUILD_DIR)/http.o
	@echo "$(BLUE)[LINK] $@$(RESET)"
	@$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BIN_DIR)/serveur_multi: $(BUILD_DIR)/serveur_multi.o $(BUILD_DIR)/queue.o $(BUILD_DIR)/http.o
	@echo "$(BLUE)[LINK] $@$(RESET)"
	@$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BIN_DIR)/serveur_mono_http: $(BUILD_DIR)/serveur_mono_http.o $(BUILD_DIR)/http.o $(BUILD_DIR)/queue.o
	@echo "$(BLUE)[LINK HTTP] $@$(RESET)"
	@$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BIN_DIR)/serveur_multi_http: $(BUILD_DIR)/serveur_multi_http.o $(BUILD_DIR)/queue.o $(BUILD_DIR)/http.o
	@echo "$(BLUE)[LINK HTTP] $@$(RESET)"
	@$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BIN_DIR)/test_queue: $(TEST_OBJ)
	@echo "$(BLUE)[LINK TEST] $@$(RESET)"
	@$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

###############################################################################
#                  RÈGLE GÉNÉRIQUE : .c → .o (src/)
###############################################################################
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c | prep
	@echo "$(YELLOW)[CC] $<$(RESET)"
	@$(CC) $(CFLAGS) -c $< -o $@

###############################################################################
#                    COMPILATION DES TESTS UNITAIRES
###############################################################################
$(TEST_DIR)/%.o: $(TEST_DIR)/%.c
	@echo "$(YELLOW)[CC TEST] $<$(RESET)"
	@$(CC) $(CFLAGS) -c $< -o $@

###############################################################################
#                           MODE DEBUG (SANITIZERS)
###############################################################################
.PHONY: debug
debug: CFLAGS += $(DBGFLAGS)
debug:
	@echo "$(YELLOW)[DEBUG] Rebuild complet avec sanitizers (ASan + UBSan)$(RESET)"
	@$(MAKE) clean
	@$(MAKE) prep
	@$(MAKE) $(TARGETS)
	@echo "$(GREEN)[DEBUG MODE ACTIVÉ – ASan + UBSan]$(RESET)"

###############################################################################
#                                 TESTS UNITAIRES
###############################################################################
.PHONY: test
test: prep $(BIN_DIR)/test_queue
	@echo "$(BLUE)[RUN] Test unitaire queue.c$(RESET)"
	@$(BIN_DIR)/test_queue

###############################################################################
#                       COMMANDES D’EXÉCUTION RAPIDE
###############################################################################
.PHONY: run_mono run_multi run_mono_http run_multi_http http kill_servers

run_mono: $(BIN_DIR)/serveur_mono
	@echo "$(BLUE)[RUN] serveur_mono sur port 5050$(RESET)"
	@$(BIN_DIR)/serveur_mono &

run_multi: $(BIN_DIR)/serveur_multi
	@echo "$(BLUE)[RUN] serveur_multi sur port 5051 (TCP)$(RESET)"
	@$(BIN_DIR)/serveur_multi &

run_mono_http: $(BIN_DIR)/serveur_mono_http
	@echo "$(BLUE)[RUN] serveur_mono_http sur port 5050 (HTTP)$(RESET)"
	@$(BIN_DIR)/serveur_mono_http &

run_multi_http: $(BIN_DIR)/serveur_multi_http
	@echo "$(BLUE)[RUN] serveur_multi_http sur port 5051 (HTTP)$(RESET)"
	@$(BIN_DIR)/serveur_multi_http &

# Build uniquement les serveurs HTTP
http: prep $(HTTP_TARGETS)
	@echo "$(GREEN)[OK] Serveurs HTTP compilés (mono + multi).$(RESET)"

kill_servers:
	@echo "$(RED)→ Arrêt des serveurs...$(RESET)"
	@pkill serveur_mono || true
	@pkill serveur_multi || true
	@pkill serveur_mono_http || true
	@pkill serveur_multi_http || true

###############################################################################
#                                   CLEAN
###############################################################################
.PHONY: clean
clean:
	@echo "$(RED)[CLEAN] Suppression build/ et bin/ + objets de test$(RESET)"
	rm -rf $(BUILD_DIR) $(BIN_DIR)
	rm -f $(TEST_DIR)/*.o

###############################################################################
#                                   REBUILD
###############################################################################
.PHONY: rebuild
rebuild:
	@echo "$(YELLOW)[REBUILD] Régénération des fichiers HTTP + recompilation complète$(RESET)"
	@$(MAKE) clean
	@python3 create_http_files.py
	@$(MAKE) -j$$(nproc)
	@echo "$(GREEN)[REBUILD] Projet reconstruit avec succès.$(RESET)"


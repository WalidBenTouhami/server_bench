###############################################################################
#   MAKEFILE ULTRA-OPTIMISÉ – Serveurs TCP/HTTP (C/POSIX) + Queue FIFO + HTTP
#   Auteur  : Walid Ben Touhami
#   Version : 3.0 (Release / Debug / Outils d'analyse)
###############################################################################

# ---------------------------------------------------------------------------
# Dossiers
# ---------------------------------------------------------------------------
SRC_DIR   := src
TEST_DIR  := tests
BUILD_DIR := build
BIN_DIR   := bin

# ---------------------------------------------------------------------------
# Mode de compilation : release (par défaut) ou debug
# Utilisation :
#   make            # => release
#   make debug      # => debug (sanitizers)
#   make MODE=debug # idem
# ---------------------------------------------------------------------------
MODE ?= release

# ---------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------
CC      := gcc
# Pour activer ccache : décommente la ligne suivante
# CC      := ccache gcc

# Flags communs
BASE_CFLAGS := -Wall -Wextra -pthread -I$(SRC_DIR)
DEPFLAGS    := -MMD -MP          # génération automatique des .d
LDFLAGS     := -lm -pthread

# Flags par mode
ifeq ($(MODE),release)
    OPT_FLAGS  := -O3 -march=native -flto
    CFLAGS     := $(BASE_CFLAGS) $(OPT_FLAGS)
    LDFLAGS    += -flto
    BUILD_TAG  := [RELEASE -O3 -march=native -flto]
else ifeq ($(MODE),debug)
    OPT_FLAGS  := -O0
    SAN_FLAGS  := -g -fsanitize=address,undefined -DDEBUG
    CFLAGS     := $(BASE_CFLAGS) $(OPT_FLAGS) $(SAN_FLAGS)
    BUILD_TAG  := [DEBUG + ASan + UBSan]
else
    $(error MODE doit être 'release' ou 'debug')
endif

# ---------------------------------------------------------------------------
# Programmes binaires
# ---------------------------------------------------------------------------
PROGS := \
    serveur_mono \
    serveur_multi \
    serveur_mono_http \
    serveur_multi_http

# Objets par programme (on ne lie que ce qui est nécessaire)
OBJS_serveur_mono       := $(addprefix $(BUILD_DIR)/,serveur_mono.o queue.o)
OBJS_serveur_multi      := $(addprefix $(BUILD_DIR)/,serveur_multi.o queue.o)
OBJS_serveur_mono_http  := $(addprefix $(BUILD_DIR)/,serveur_mono_http.o http.o queue.o)
OBJS_serveur_multi_http := $(addprefix $(BUILD_DIR)/,serveur_multi_http.o http.o queue.o)

# Tests unitaires (explicites pour rester maîtrisé)
TEST_BINS        := $(BIN_DIR)/test_queue
OBJS_test_queue  := $(BUILD_DIR)/queue.o $(TEST_DIR)/test_queue.o

# Tous les objets dans build/ (pour les dépendances .d)
ALL_OBJS := \
    $(OBJS_serveur_mono) \
    $(OBJS_serveur_multi) \
    $(OBJS_serveur_mono_http) \
    $(OBJS_serveur_multi_http)

DEPS := $(ALL_OBJS:.o=.d)

# ---------------------------------------------------------------------------
# Couleurs
# ---------------------------------------------------------------------------
GREEN  := \033[1;32m
BLUE   := \033[1;34m
YELLOW := \033[1;33m
RED    := \033[1;31m
CYAN   := \033[1;36m
RESET  := \033[0m

# ---------------------------------------------------------------------------
# Règle principale
# ---------------------------------------------------------------------------
.PHONY: all
all: banner prep bin_targets
	@echo "$(GREEN)[OK] Compilation complète réussie $(BUILD_TAG)$(RESET)"

.PHONY: banner
banner:
	@echo "$(CYAN)===============================================$(RESET)"
	@echo "$(CYAN)  Build MODE = $(MODE)  $(BUILD_TAG)$(RESET)"
	@echo "$(CYAN)===============================================$(RESET)"

.PHONY: bin_targets
bin_targets: \
	$(BIN_DIR)/serveur_mono \
	$(BIN_DIR)/serveur_multi \
	$(BIN_DIR)/serveur_mono_http \
	$(BIN_DIR)/serveur_multi_http \
	$(BIN_DIR)/test_queue

# ---------------------------------------------------------------------------
# Préparation dossiers
# ---------------------------------------------------------------------------
prep:
	@mkdir -p $(BUILD_DIR) $(BIN_DIR)

# ---------------------------------------------------------------------------
# Liens (serveurs TCP / HTTP)
# ---------------------------------------------------------------------------
$(BIN_DIR)/serveur_mono: $(OBJS_serveur_mono)
	@echo "$(BLUE)[LINK] $@$(RESET)"
	@$(CC) -o $@ $^ $(LDFLAGS)

$(BIN_DIR)/serveur_multi: $(OBJS_serveur_multi)
	@echo "$(BLUE)[LINK] $@$(RESET)"
	@$(CC) -o $@ $^ $(LDFLAGS)

$(BIN_DIR)/serveur_mono_http: $(OBJS_serveur_mono_http)
	@echo "$(BLUE)[LINK HTTP] $@$(RESET)"
	@$(CC) -o $@ $^ $(LDFLAGS)

$(BIN_DIR)/serveur_multi_http: $(OBJS_serveur_multi_http)
	@echo "$(BLUE)[LINK HTTP] $@$(RESET)"
	@$(CC) -o $@ $^ $(LDFLAGS)

# ---------------------------------------------------------------------------
# Tests unitaires
# ---------------------------------------------------------------------------
$(BIN_DIR)/test_queue: $(OBJS_test_queue)
	@echo "$(BLUE)[LINK TEST] $@$(RESET)"
	@$(CC) -o $@ $^ $(LDFLAGS)

# ---------------------------------------------------------------------------
# Compilation objets src/ -> build/
# ---------------------------------------------------------------------------
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c
	@echo "$(YELLOW)[CC] $<$(RESET)"
	@$(CC) $(CFLAGS) $(DEPFLAGS) -c $< -o $@

# ---------------------------------------------------------------------------
# Compilation objets tests/ -> tests/
# (on laisse les .o de tests dans tests/ pour bien les distinguer)
# ---------------------------------------------------------------------------
$(TEST_DIR)/%.o: $(TEST_DIR)/%.c
	@echo "$(YELLOW)[CC TEST] $<$(RESET)"
	@$(CC) $(CFLAGS) $(DEPFLAGS) -c $< -o $@

# ---------------------------------------------------------------------------
# Inclusion des fichiers de dépendances (.d) pour recompilations minimales
# ---------------------------------------------------------------------------
-include $(DEPS)

# ---------------------------------------------------------------------------
# Modes de build pratiques
# ---------------------------------------------------------------------------
.PHONY: debug release

# Debug : sanitizers + assertions
debug:
	@$(MAKE) MODE=debug clean all
	@echo "$(GREEN)[DEBUG] Build terminé avec ASan + UBSan$(RESET)"

# Release explicite
release:
	@$(MAKE) MODE=release clean all
	@echo "$(GREEN)[RELEASE] Build optimisé -O3 -march=native -flto$(RESET)"

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
.PHONY: test
test: prep $(BIN_DIR)/test_queue
	@echo "$(BLUE)[RUN] Test unitaire queue.c$(RESET)"
	@$(BIN_DIR)/test_queue

# ---------------------------------------------------------------------------
# Exécution des serveurs
# ---------------------------------------------------------------------------
.PHONY: run_mono run_multi run_mono_http run_multi_http kill_servers

run_mono: $(BIN_DIR)/serveur_mono
	$(BIN_DIR)/serveur_mono &

run_multi: $(BIN_DIR)/serveur_multi
	$(BIN_DIR)/serveur_multi &

run_mono_http: $(BIN_DIR)/serveur_mono_http
	$(BIN_DIR)/serveur_mono_http &

run_multi_http: $(BIN_DIR)/serveur_multi_http
	$(BIN_DIR)/serveur_multi_http &

kill_servers:
	@echo "$(RED)→ Arrêt des serveurs...$(RESET)"
	@pkill serveur_mono || true
	@pkill serveur_multi || true
	@pkill serveur_mono_http || true
	@pkill serveur_multi_http || true

# ---------------------------------------------------------------------------
# Outils : Valgrind, Helgrind, format, tidy
# ---------------------------------------------------------------------------
.PHONY: valgrind helgrind format tidy

valgrind: $(BIN_DIR)/serveur_multi
	valgrind --leak-check=full --show-leak-kinds=all $<

helgrind: $(BIN_DIR)/serveur_multi
	valgrind --tool=helgrind $<

format:
	clang-format -i $(SRC_DIR)/*.c $(SRC_DIR)/*.h $(TEST_DIR)/*.c || true

tidy:
	clang-tidy $(SRC_DIR)/*.c -- -I$(SRC_DIR)

# ---------------------------------------------------------------------------
# Aide
# ---------------------------------------------------------------------------
.PHONY: help
help:
	@echo "$(CYAN)Cibles principales :$(RESET)"
	@echo "  make              : build en mode release (par défaut)"
	@echo "  make debug        : build mode debug (ASan/UBSan)"
	@echo "  make release      : rebuild complet optimisé"
	@echo "  make test         : exécute les tests unitaires"
	@echo "  make run_mono     : lance le serveur TCP mono-thread"
	@echo "  make run_multi    : lance le serveur TCP multi-thread"
	@echo "  make run_mono_http: lance le serveur HTTP mono-thread"
	@echo "  make run_multi_http: lance le serveur HTTP multi-thread"
	@echo "  make valgrind     : analyse mémoire serveur_multi"
	@echo "  make helgrind     : analyse race conditions serveur_multi"
	@echo "  make format       : applique clang-format si dispo"
	@echo "  make tidy         : analyse statique clang-tidy"
	@echo "  make clean        : nettoie build/ et bin/"

# ---------------------------------------------------------------------------
# Nettoyage
# ---------------------------------------------------------------------------
.PHONY: clean
clean:
	@echo "$(RED)[CLEAN] Suppression build/ et bin/$(RESET)"
	@rm -rf $(BUILD_DIR) $(BIN_DIR)
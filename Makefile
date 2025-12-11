###############################################################################
#   MAKEFILE ULTRA-OPTIMISÉ – v3.2
#   Serveurs TCP/HTTP – POSIX / Threads / Queue FIFO / Stress Tests / UML
#   Auteur  : Walid Ben Touhami
###############################################################################

# ---------------------------------------------------------------------------
# Dossiers
# ---------------------------------------------------------------------------
SRC_DIR   := src
TEST_DIR  := tests
BUILD_DIR := build
BIN_DIR   := bin

UML_DIR   := docs/uml
UML_GEN   := $(UML_DIR)/generate_uml.py

UML_SEQ_BASENAMES := \
	uml_seq_tcp_monothread \
	uml_seq_tcp_multithread \
	uml_seq_http_monothread \
	uml_seq_http_multithread

# ---------------------------------------------------------------------------
# Mode compilation
# ---------------------------------------------------------------------------
MODE ?= release

CC      := gcc
PYTHON      ?= python3
VENV_PY     := venv/bin/python

BASE_CFLAGS := -Wall -Wextra -pthread -I$(SRC_DIR)
DEPFLAGS    := -MMD -MP
LDFLAGS     := -lm -pthread

ifeq ($(MODE),release)
    OPT_FLAGS  := -O3 -march=native -flto
    CFLAGS     := $(BASE_CFLAGS) $(OPT_FLAGS)
    LDFLAGS    += -flto
    BUILD_TAG  := [RELEASE]
else ifeq ($(MODE),debug)
    OPT_FLAGS  := -O0
    SAN_FLAGS  := -g -fsanitize=address,undefined -DDEBUG
    CFLAGS     := $(BASE_CFLAGS) $(OPT_FLAGS) $(SAN_FLAGS)
    LDFLAGS    += $(SAN_FLAGS)
    BUILD_TAG  := [DEBUG + ASan + UBSan]
else
    $(error MODE doit être 'release' ou 'debug')
endif

# ---------------------------------------------------------------------------
# Programmes
# ---------------------------------------------------------------------------
PROGS := \
    serveur_mono \
    serveur_multi \
    serveur_mono_http \
    serveur_multi_http

OBJS_serveur_mono       := $(addprefix $(BUILD_DIR)/,serveur_mono.o queue.o)
OBJS_serveur_multi      := $(addprefix $(BUILD_DIR)/,serveur_multi.o queue.o)
OBJS_serveur_mono_http  := $(addprefix $(BUILD_DIR)/,serveur_mono_http.o http.o queue.o)
OBJS_serveur_multi_http := $(addprefix $(BUILD_DIR)/,serveur_multi_http.o http.o queue.o)

TEST_BINS        := $(BIN_DIR)/test_queue
OBJS_test_queue  := $(BUILD_DIR)/queue.o $(TEST_DIR)/test_queue.o

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
	@echo "$(GREEN)[OK] Build complet $(BUILD_TAG)$(RESET)"

banner:
	@echo "$(CYAN)===============================================$(RESET)"
	@echo "$(CYAN)  Build MODE = $(MODE)  $(BUILD_TAG)$(RESET)"
	@echo "$(CYAN)===============================================$(RESET)"

bin_targets: \
	$(BIN_DIR)/serveur_mono \
	$(BIN_DIR)/serveur_multi \
	$(BIN_DIR)/serveur_mono_http \
	$(BIN_DIR)/serveur_multi_http \
	$(BIN_DIR)/test_queue

# ---------------------------------------------------------------------------
# Préparation
# ---------------------------------------------------------------------------
prep:
	@mkdir -p $(BUILD_DIR) $(BIN_DIR)

# ---------------------------------------------------------------------------
# Liens
# ---------------------------------------------------------------------------
$(BIN_DIR)/serveur_mono: $(OBJS_serveur_mono)
	@echo "$(BLUE)[LINK] TCP mono$(RESET)"
	@$(CC) -o $@ $^ $(LDFLAGS)

$(BIN_DIR)/serveur_multi: $(OBJS_serveur_multi)
	@echo "$(BLUE)[LINK] TCP multi$(RESET)"
	@$(CC) -o $@ $^ $(LDFLAGS)

$(BIN_DIR)/serveur_mono_http: $(OBJS_serveur_mono_http)
	@echo "$(BLUE)[LINK] HTTP mono$(RESET)"
	@$(CC) -o $@ $^ $(LDFLAGS)

$(BIN_DIR)/serveur_multi_http: $(OBJS_serveur_multi_http)
	@echo "$(BLUE)[LINK] HTTP multi$(RESET)"
	@$(CC) -o $@ $^ $(LDFLAGS)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
$(BIN_DIR)/test_queue: $(OBJS_test_queue)
	@echo "$(BLUE)[LINK TEST] queue$(RESET)"
	@$(CC) -o $@ $^ $(LDFLAGS)

# ---------------------------------------------------------------------------
# Compilation objets
# ---------------------------------------------------------------------------
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c
	@echo "$(YELLOW)[CC] $<$(RESET)"
	@$(CC) $(CFLAGS) $(DEPFLAGS) -c $< -o $@

$(TEST_DIR)/%.o: $(TEST_DIR)/%.c
	@echo "$(YELLOW)[CC TEST] $<$(RESET)"
	@$(CC) $(CFLAGS) $(DEPFLAGS) -c $< -o $@

-include $(DEPS)

# ---------------------------------------------------------------------------
# Modes debug / release
# ---------------------------------------------------------------------------
debug:
	@$(MAKE) MODE=debug clean all

release:
	@$(MAKE) MODE=release clean all

# ---------------------------------------------------------------------------
# Serveurs
# ---------------------------------------------------------------------------
run_mono: $(BIN_DIR)/serveur_mono
	$< &

run_multi: $(BIN_DIR)/serveur_multi
	$< &

run_mono_http: $(BIN_DIR)/serveur_mono_http
	$< &

run_multi_http: $(BIN_DIR)/serveur_multi_http
	$< &

kill_servers:
	@echo "$(RED)Arrêt serveurs...$(RESET)"
	@pkill serveur_mono       || true
	@pkill serveur_multi      || true
	@pkill serveur_mono_http  || true
	@pkill serveur_multi_http || true

# ---------------------------------------------------------------------------
# UML : génération + devserver
# ---------------------------------------------------------------------------
.PHONY: uml uml_clean uml_check uml_devserver uml_viewer

uml:
	@echo "$(BLUE)[UML] Génération UML$(RESET)"
	@python3 $(UML_GEN)
	@$(MAKE) uml_check

uml_clean:
	@echo "$(RED)[UML CLEAN]$(RESET)"
	@find $(UML_DIR) -maxdepth 1 -type f -name 'uml_*' -delete

uml_check:
	@echo "$(CYAN)[UML] Vérification nomenclature$(RESET)"
	cd $(UML_DIR) && \
	for b in $(UML_SEQ_BASENAMES); do \
		if [ ! -f "$$b.svg" ]; then \
			echo "$(RED)[MISSING] $$b.svg$(RESET)"; exit 1; \
		else \
			echo "$(GREEN)[OK] $$b.svg$(RESET)"; \
		fi; \
	done

uml_devserver:
	cd $(UML_DIR) && python3 uml_devserver.py

uml_viewer:
	@echo "Ouvres dans ton navigateur : http://localhost:9999/viewer.html"

# ---------------------------------------------------------------------------
# Benchmarks / Stress Tests
# ---------------------------------------------------------------------------
stress_tcp_mono:
	$(VENV_PY) python/client_stress_tcp.py  --port 5050 --ramp 10,50,100,200

stress_tcp_multi:
	$(VENV_PY) python/client_stress_tcp.py  --port 5051 --ramp 10,50,100,200

stress_http_mono:
	$(VENV_PY) python/client_stress_http.py --port 8080 --path /hello --ramp 10,50,100,200

stress_http_multi:
	$(VENV_PY) python/client_stress_http.py --port 8081 --path /hello --ramp 10,50,100,200

benchmark_extreme:
	$(VENV_PY) python/benchmark_extreme.py

full_run: clean all
	./scripts/start_all.sh
	$(VENV_PY) python/benchmark_extreme.py

# ---------------------------------------------------------------------------
# Présentation PPTX
# ---------------------------------------------------------------------------
ppt:
	cd presentation && ./generate_pptx_final.py

# ---------------------------------------------------------------------------
# Nettoyage global
# ---------------------------------------------------------------------------
clean:
	@echo "$(RED)[CLEAN] build/ + bin/$(RESET)"
	@rm -rf $(BUILD_DIR) $(BIN_DIR)


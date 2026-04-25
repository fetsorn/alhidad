# SPDX-License-Identifier: AGPL-3.0

CSVS    := csvs
GRAPH   := graph
PROSE   := prose
SCRIPTS := scripts

export CSVS
export GRAPH
export PROSE
CLASSIFY := $(SCRIPTS)/classify
INGEST := $(SCRIPTS)/ingest
SCRIBE := $(SCRIPTS)/scribe

# scribe
ARCHIVE  ?= archive
MODEL    ?= $(HOME)/whisper.cpp/models/ggml-large-v3-turbo.bin
WHISPER  ?= $(HOME)/whisper.cpp/build/bin/whisper-cli
CATEGORY ?= sound/recording
LIMIT    ?= 1
BACKEND  ?= arq

# Segment TTL files
DIRS_TTL   := $(GRAPH)/directories.ttl
CATS_TTL   := $(GRAPH)/categories.ttl
CLASS_TTL  := $(GRAPH)/classification.ttl
FILES_TTL  := $(GRAPH)/files.ttl
ASSETS_TTL := $(GRAPH)/assets.ttl
ITEMS_TTL  := $(GRAPH)/items.ttl

INFERRED := $(GRAPH)/inferred.ttl

SEGMENTS := $(DIRS_TTL) $(CATS_TTL) $(CLASS_TTL) $(FILES_TTL) $(ASSETS_TTL) $(ITEMS_TTL) $(INFERRED)
ALL_TTL  := $(GRAPH)/estate.ttl

# csvs inputs
DATA_PATH   := $(CSVS)/data-file.csv
DIR_PARENT  := $(CSVS)/dir-parent.csv
CAT_PATH    := $(CSVS)/category-dir.csv

.PHONY: all load clean segments list scribe

all: $(ALL_TTL)

segments: $(SEGMENTS)

# Step 0: generate dir-parent.csv from data-file.csv
$(DIR_PARENT): $(DATA_PATH) $(CLASSIFY)/gen-dir-parent.py
	cd $(CLASSIFY) && python3 gen-dir-parent.py

# Step 1: directories
$(DIRS_TTL): $(DIR_PARENT) $(CLASSIFY)/gen-directories.py
	cd $(CLASSIFY) && python3 gen-directories.py

# Step 2: categories
$(CATS_TTL): $(CAT_PATH) $(CLASSIFY)/gen-categories.py
	cd $(CLASSIFY) && python3 gen-categories.py

# Step 3: classification (direct path assignment, skos:broader* at query time)
$(CLASS_TTL): $(CAT_PATH) $(CLASSIFY)/gen-classification.py
	cd $(CLASSIFY) && python3 gen-classification.py

# Step 4a: files (path-based identity, one node per path)
$(FILES_TTL): $(DATA_PATH) $(CLASSIFY)/gen-files.py
	cd $(CLASSIFY) && python3 gen-files.py

# Step 4b: assets (content-based identity, one node per hash)
$(ASSETS_TTL): $(DATA_PATH) $(CLASSIFY)/gen-assets.py
	cd $(CLASSIFY) && python3 gen-assets.py

# Step 5: items
$(ITEMS_TTL): $(CSVS)/item-location.csv $(CLASSIFY)/gen-items.py
	cd $(CLASSIFY) && python3 gen-items.py

# Step 6: materialize category inheritance via SPARQL CONSTRUCT
$(INFERRED): $(CLASS_TTL) $(DIRS_TTL) queries/materialize-categories.rq
	nix-shell -p apache-jena --run 'arq --query queries/materialize-categories.rq --data $(CLASS_TTL) --data $(DIRS_TTL)' > $@

# Combined TTL for arq queries
$(ALL_TTL): $(SEGMENTS)
	cat $(SEGMENTS) > $@

# Load all segments into Oxigraph
load: segments
	cd $(CLASSIFY) && python3 load-oxigraph.py

# Load without clearing (append)
load-append: segments
	cd $(CLASSIFY) && python3 load-oxigraph.py --no-clear

# Transcribe all pending files
scribe:
	@$(SCRIBE)/targets --category $(CATEGORY) --backend $(BACKEND) $(if $(LIMIT),--limit $(LIMIT)) \
	| while IFS= read -r p; do \
		$(SCRIBE)/transcribe-one "$(ARCHIVE)/$$p" "${PROSE}/$$p.txt" "$(MODEL)" "$(WHISPER)"; \
	done

# Show what would be transcribed
list:
	@$(SCRIBE)/targets --category $(CATEGORY) --backend $(BACKEND) $(if $(LIMIT),--limit $(LIMIT))

clean:
	rm -f $(SEGMENTS) $(ALL_TTL) $(DIR_PARENT)

# facilitator-kit — Toorcamp 2026 "Dead Bytes Tell No Lies" workshop
#
# Targets:
#   make tarball   — assemble the source tree from canonical paths, compute
#                    manifests, and build a reproducible facilitator-kit-
#                    toorcamp-2026.tar.gz at ../ (i.e. workshop/)
#   make selftest  — run selftest.sh against the assembled source tree
#                    (MD5-verifies every kit file + exercises both Python
#                    scripts' self-test modes)
#   make clean     — remove the built tarball
#   make help      — list targets
#
# The tarball is built with sorted file order, fixed mtimes, and gzip --no-name
# so two consecutive `make tarball` runs produce byte-identical output.

KIT_NAME        := facilitator-kit-toorcamp-2026
KIT_VERSION     := 1.0.0
# Layout (post-restructure):
#   KIT_DIR       = workshop/kit   — this kit (the assembled/built unit)
#   WORKSHOP_DIR  = workshop       — holds the facing docs, src/, and kit/
#   WORKSHOP_SRC  = workshop/src   — Makefile-source files: the decode
#                                    reference + the two Python tools
KIT_DIR         := $(CURDIR)
WORKSHOP_DIR    := $(abspath $(KIT_DIR)/..)
WORKSHOP_SRC    := $(abspath $(WORKSHOP_DIR)/src)
# Tarball is written into workshop/ (one level up from the kit). Only the kit/
# subtree is archived (see the tarball target), so the sibling docs/src never
# leak into the bundle.
TARBALL         := $(WORKSHOP_DIR)/$(KIT_NAME).tar.gz

# Canonical source paths (absolute, defensive — never use relative paths so
# `make tarball` works from anywhere). The facing docs live in workshop/ (one
# level up from the kit); the decode reference + Python tools live in
# workshop/src/.
SRC_FACILITATOR_GUIDE     := $(WORKSHOP_DIR)/FACILITATOR-GUIDE.md
SRC_PARTICIPANT_HANDOUT   := $(WORKSHOP_DIR)/PARTICIPANT-HANDOUT.md
SRC_DECODE_REFERENCE      := $(WORKSHOP_SRC)/DATAFLASH-DECODE-REFERENCE.md
SRC_BUILD_INJECTED        := $(WORKSHOP_SRC)/build-injected.py
SRC_RECOVER_BASELINE      := $(WORKSHOP_SRC)/recover-baseline.py
# Self-service workshop tooling (the attendee read/write layer). decode-codes is
# the shared decoder; lock-tool is the read/write CLI bedrock; lock-menu + lock-
# panel are the thin convenience wrappers (TUI + browser control panel). All
# stdlib-only, all ship to the station tools/ dir.
SRC_DECODE_CODES          := $(WORKSHOP_SRC)/decode-codes.py
SRC_LOCK_TOOL             := $(WORKSHOP_SRC)/lock-tool.py
SRC_LOCK_MENU             := $(WORKSHOP_SRC)/lock-menu.py
SRC_LOCK_PANEL            := $(WORKSHOP_SRC)/lock-panel.py
SRC_MINIPRO_BIN           := /usr/local/bin/minipro
# GPLv3 attribution/NOTICE that travels WITH the bundled minipro binary. The
# binary is third-party Free Software (GPLv3); this file carries the upstream
# project + URL, the pinned version/commit, the source-availability offer, and
# rebuild instructions. It assembles into bin/ next to the binary it covers.
SRC_MINIPRO_NOTICE        := $(WORKSHOP_SRC)/MINIPRO-NOTICE.md
# Baseline is committed in-repo at the kit's own dumps/ dir (repo-self-contained).
# Because source == assemble destination, the copy below is guarded to a no-op
# when the two paths are the same file. The MD5 gate against
# EXPECTED_BASELINE_MD5 still runs on this file before packaging.
SRC_BASELINE_DUMP         := $(KIT_DIR)/dumps/intact-lock-AT45DB041E-main-2026-05-20.bin
SRC_UDEV_RULES_DIR        := /etc/udev/rules.d

# The canonical baseline MD5 (operator-bench validated).
EXPECTED_BASELINE_MD5     := eb6acff32ef13b29ac6ebed10d77316d

# Reproducible-build tuning. SOURCE_DATE_EPOCH is honored by GNU tar and many
# other tools to stamp a fixed timestamp into archive entries.
SOURCE_DATE_EPOCH := 1747526400
export SOURCE_DATE_EPOCH


.PHONY: help
help:
	@echo "facilitator-kit Makefile — $(KIT_NAME) v$(KIT_VERSION)"
	@echo
	@echo "Targets:"
	@echo "  make station   Assemble + verify + stand up the station (needs sudo for install)"
	@echo "  make assemble  Copy sources into the kit + regenerate manifests"
	@echo "  make tarball   Assemble + build $(KIT_NAME).tar.gz (reproducible)"
	@echo "  make selftest  MD5-verify kit files + exercise Python self-tests"
	@echo "  make clean     Remove the built tarball"
	@echo "  make help      This message"
	@echo
	@echo "Tarball output:  $(TARBALL)"


# -----------------------------------------------------------------------------
# Assembly — copy source-of-truth files into the kit's source tree. This is
# idempotent: re-running overwrites the assembled files with the latest
# canonical sources.
# -----------------------------------------------------------------------------
.PHONY: assemble
assemble:
	@echo "==> Assembling facilitator-kit source tree..."
	@# Documentation — copies (not symlinks) so the tarball is self-contained.
	@# Assembled doc set: FACILITATOR-GUIDE, PARTICIPANT-HANDOUT, and the decode
	@# reference. (Internal bench docs are not part of the shipped bundle.)
	@cp -f "$(SRC_FACILITATOR_GUIDE)"     "$(KIT_DIR)/docs/FACILITATOR-GUIDE.md"
	@cp -f "$(SRC_PARTICIPANT_HANDOUT)"   "$(KIT_DIR)/docs/PARTICIPANT-HANDOUT.md"
	@cp -f "$(SRC_DECODE_REFERENCE)"      "$(KIT_DIR)/docs/DATAFLASH-DECODE-REFERENCE.md"
	@# Tools — copies preserve executable bit
	@cp -f "$(SRC_BUILD_INJECTED)"        "$(KIT_DIR)/tools/build-injected.py"
	@cp -f "$(SRC_RECOVER_BASELINE)"      "$(KIT_DIR)/tools/recover-baseline.py"
	@# Self-service read/write tooling — copies preserve executable bit
	@cp -f "$(SRC_DECODE_CODES)"          "$(KIT_DIR)/tools/decode-codes.py"
	@cp -f "$(SRC_LOCK_TOOL)"             "$(KIT_DIR)/tools/lock-tool.py"
	@cp -f "$(SRC_LOCK_MENU)"             "$(KIT_DIR)/tools/lock-menu.py"
	@cp -f "$(SRC_LOCK_PANEL)"            "$(KIT_DIR)/tools/lock-panel.py"
	@chmod 755 "$(KIT_DIR)/tools/build-injected.py" "$(KIT_DIR)/tools/recover-baseline.py" \
	           "$(KIT_DIR)/tools/decode-codes.py" "$(KIT_DIR)/tools/lock-tool.py" \
	           "$(KIT_DIR)/tools/lock-menu.py" "$(KIT_DIR)/tools/lock-panel.py"
	@# minipro binary — Linux-AMD64 ELF, built from DavidGriffith fd6b56af.
	@# Refresh from the host build when present (operator-rebuild input); if the
	@# host has no minipro installed, keep the committed in-kit copy (same guard
	@# pattern as the udev rules below).
	@if [ -f "$(SRC_MINIPRO_BIN)" ]; then \
		cp -f "$(SRC_MINIPRO_BIN)" "$(KIT_DIR)/bin/minipro"; \
		echo "    [minipro] Refreshed bin/minipro from $(SRC_MINIPRO_BIN)"; \
	else \
		echo "    [minipro] Source not found at $(SRC_MINIPRO_BIN); keeping committed in-kit copy"; \
	fi
	@chmod 755 "$(KIT_DIR)/bin/minipro"
	@# minipro GPLv3 attribution/NOTICE — travels alongside the binary in bin/.
	@# Required for honest GPL redistribution-with-attribution of the bundled
	@# binary. Copied (not symlinked) so the tarball is self-contained.
	@cp -f "$(SRC_MINIPRO_NOTICE)"        "$(KIT_DIR)/bin/MINIPRO-NOTICE.md"
	@chmod 644 "$(KIT_DIR)/bin/MINIPRO-NOTICE.md"
	@# udev rules — three files shipped by minipro 0.7.4 `make install`
	@if [ -f "$(SRC_UDEV_RULES_DIR)/60-minipro.rules" ]; then \
		cp -f "$(SRC_UDEV_RULES_DIR)/60-minipro.rules"          "$(KIT_DIR)/etc/udev/rules.d/60-minipro.rules"; \
		cp -f "$(SRC_UDEV_RULES_DIR)/61-minipro-plugdev.rules"  "$(KIT_DIR)/etc/udev/rules.d/61-minipro-plugdev.rules"; \
		cp -f "$(SRC_UDEV_RULES_DIR)/61-minipro-uaccess.rules"  "$(KIT_DIR)/etc/udev/rules.d/61-minipro-uaccess.rules"; \
		echo "    [udev] Lifted 3 minipro rule files from $(SRC_UDEV_RULES_DIR)"; \
	else \
		echo "    [udev] Source rules not found at $(SRC_UDEV_RULES_DIR); using bundled minimal rule"; \
	fi
	@# Baseline dump — verify MD5 BEFORE copying; refuse on mismatch
	@actual_md5=$$(md5sum "$(SRC_BASELINE_DUMP)" | awk '{print $$1}'); \
	if [ "$$actual_md5" != "$(EXPECTED_BASELINE_MD5)" ]; then \
		echo "ERROR: baseline MD5 mismatch."; \
		echo "  Source:   $(SRC_BASELINE_DUMP)"; \
		echo "  Got:      $$actual_md5"; \
		echo "  Expected: $(EXPECTED_BASELINE_MD5)"; \
		echo "  Refusing to package a non-canonical baseline."; \
		exit 1; \
	fi
	@# Copy the validated baseline into dumps/. Source is the in-repo committed
	@# copy, which already lives at the destination, so skip the copy when source
	@# and destination are the same file (cp would otherwise error). The MD5 gate
	@# above has already run on the source either way.
	@if [ "$(SRC_BASELINE_DUMP)" -ef "$(KIT_DIR)/dumps/intact-lock-AT45DB041E-main-2026-05-20.bin" ]; then \
		echo "    [dump] Baseline source is the committed in-repo copy; copy is a no-op"; \
	else \
		cp -f "$(SRC_BASELINE_DUMP)" "$(KIT_DIR)/dumps/intact-lock-AT45DB041E-main-2026-05-20.bin"; \
	fi
	@chmod 644 "$(KIT_DIR)/dumps/intact-lock-AT45DB041E-main-2026-05-20.bin"
	@$(MAKE) --no-print-directory manifests
	@echo "==> Assembly complete."


# -----------------------------------------------------------------------------
# Manifests — generated, never hand-edited. Two manifests:
#   dumps/MANIFEST.md   sub-manifest for .bin files (sensitive — lock memory)
#   MANIFEST.md         top-level manifest covering every kit file
# -----------------------------------------------------------------------------
.PHONY: manifests
manifests:
	@echo "==> Generating manifests..."
	@bash "$(KIT_DIR)/scripts/gen-manifest.sh" "$(KIT_DIR)" "$(KIT_VERSION)" "$(SOURCE_DATE_EPOCH)"


# -----------------------------------------------------------------------------
# Tarball — deterministic build. We rely on:
#   --sort=name              sorted file order
#   --owner=0 --group=0      no per-host UID/GID leakage
#   --numeric-owner
#   --mtime=@$(SOURCE_DATE_EPOCH)   fixed timestamps
#   gzip --no-name --best    no embedded filename/timestamp, max compression
#
# We tar the kit/ subtree from its parent (workshop/) so the archive root is
# "kit/" — then rename that top-level entry to $(KIT_NAME) via --transform so
# the extracted directory is "facilitator-kit-toorcamp-2026/", matching the
# operator's documented `cd facilitator-kit-toorcamp-2026 && sudo ./install.sh`
# workflow. Only the kit/ subtree is named on the tar command line, so the
# sibling workshop/ docs and src/ never enter the bundle.
# -----------------------------------------------------------------------------
.PHONY: tarball
tarball: assemble
	@echo "==> Building reproducible tarball at $(TARBALL)..."
	@rm -f "$(TARBALL)"
	@cd "$(WORKSHOP_DIR)" && \
		tar --sort=name \
		    --owner=0 --group=0 --numeric-owner \
		    --mtime=@$(SOURCE_DATE_EPOCH) \
		    --transform='s,^kit,$(KIT_NAME),' \
		    --exclude='kit/.git' \
		    --exclude='kit/scripts' \
		    --exclude='*/__pycache__' \
		    --exclude='*.pyc' \
		    -cf - kit | \
		gzip --no-name --best > "$(TARBALL)"
	@echo "==> Tarball built. Size + MD5:"
	@ls -l "$(TARBALL)" | awk '{printf "    size: %s bytes\n", $$5}'
	@md5sum "$(TARBALL)" | awk '{printf "    md5:  %s\n", $$1}'


.PHONY: selftest
selftest:
	@bash "$(KIT_DIR)/selftest.sh"


# -----------------------------------------------------------------------------
# station — one-command station stand-up from the kit dir. Assembles, verifies,
# then runs the installer. The installer needs root (it writes /usr/local/bin
# and /etc/udev), so when not run under sudo this target stops after the verify
# and prints the exact `sudo` line to finish with. The repo-root `bootstrap.sh`
# is the friendlier front door (run from a fresh clone); this target is the
# in-kit equivalent for facilitators already sitting in workshop/kit/.
# -----------------------------------------------------------------------------
.PHONY: station
station: assemble selftest
	@echo "==> [station] kit assembled + verified."
	@if [ "$$(id -u)" -eq 0 ]; then \
		echo "==> [station] running installer (root)"; \
		bash "$(KIT_DIR)/install.sh"; \
	else \
		echo "==> [station] installer needs root. Finish with:"; \
		echo "        sudo $(KIT_DIR)/install.sh"; \
		echo "    (or, from the repo root: sudo ./bootstrap.sh)"; \
	fi


.PHONY: clean
clean:
	@echo "==> Removing built tarball..."
	@rm -f "$(TARBALL)"
	@echo "==> Done."

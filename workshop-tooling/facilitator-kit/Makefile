# facilitator-kit — Toorcamp 2026 "Dead Bytes Tell No Lies" workshop
#
# Targets:
#   make tarball   — assemble the source tree from canonical paths, compute
#                    manifests, and build a reproducible facilitator-kit-
#                    toorcamp-2026.tar.gz at ../facilitator-kit-toorcamp-2026.tar.gz
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
KIT_DIR         := $(CURDIR)
WORKSHOP_TOOLING := $(abspath $(KIT_DIR)/..)
TOORCAMP_OUT    := $(abspath $(KIT_DIR)/../..)
TARBALL         := $(WORKSHOP_TOOLING)/$(KIT_NAME).tar.gz

# Canonical source paths (absolute, defensive — never use relative paths so
# `make tarball` works from anywhere).
SRC_FACILITATOR_GUIDE     := $(TOORCAMP_OUT)/FACILITATOR-GUIDE.md
SRC_PARTICIPANT_HANDOUT   := $(TOORCAMP_OUT)/PARTICIPANT-HANDOUT.md
SRC_DUMP_VALIDATION       := $(WORKSHOP_TOOLING)/DUMP-VALIDATION.md
SRC_T48_KALI_PLAN         := $(WORKSHOP_TOOLING)/T48-KALI-PLAN.md
SRC_T4E_DUMP_VAL_REPORT   := $(WORKSHOP_TOOLING)/T+4e-DUMP-VALIDATION-REPORT.md
SRC_BUILD_INJECTED        := $(WORKSHOP_TOOLING)/build-injected.py
SRC_RECOVER_BASELINE      := $(WORKSHOP_TOOLING)/recover-baseline.py
SRC_MINIPRO_BIN           := /usr/local/bin/minipro
SRC_BASELINE_DUMP         := $(HOME)/Desktop/toorcamp-2026-dumps/intact-lock-AT45DB041E-main-2026-05-20.bin
SRC_UDEV_RULES_DIR        := /etc/udev/rules.d

# The canonical baseline MD5 (T+4e operator-bench validated).
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
	@# Documentation — copies (not symlinks) so the tarball is self-contained
	@cp -f "$(SRC_FACILITATOR_GUIDE)"     "$(KIT_DIR)/docs/FACILITATOR-GUIDE.md"
	@cp -f "$(SRC_PARTICIPANT_HANDOUT)"   "$(KIT_DIR)/docs/PARTICIPANT-HANDOUT.md"
	@cp -f "$(SRC_DUMP_VALIDATION)"       "$(KIT_DIR)/docs/DUMP-VALIDATION.md"
	@cp -f "$(SRC_T48_KALI_PLAN)"         "$(KIT_DIR)/docs/T48-KALI-PLAN.md"
	@cp -f "$(SRC_T4E_DUMP_VAL_REPORT)"   "$(KIT_DIR)/docs/T+4e-DUMP-VALIDATION-REPORT.md"
	@# Tools — copies preserve executable bit
	@cp -f "$(SRC_BUILD_INJECTED)"        "$(KIT_DIR)/tools/build-injected.py"
	@cp -f "$(SRC_RECOVER_BASELINE)"      "$(KIT_DIR)/tools/recover-baseline.py"
	@chmod 755 "$(KIT_DIR)/tools/build-injected.py" "$(KIT_DIR)/tools/recover-baseline.py"
	@# minipro binary — Linux-AMD64 ELF, built from DavidGriffith fd6b56af
	@cp -f "$(SRC_MINIPRO_BIN)"           "$(KIT_DIR)/bin/minipro"
	@chmod 755 "$(KIT_DIR)/bin/minipro"
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
	@cp -f "$(SRC_BASELINE_DUMP)"         "$(KIT_DIR)/dumps/intact-lock-AT45DB041E-main-2026-05-20.bin"
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
	@$(KIT_DIR)/scripts/gen-manifest.sh "$(KIT_DIR)" "$(KIT_VERSION)" "$(SOURCE_DATE_EPOCH)"


# -----------------------------------------------------------------------------
# Tarball — deterministic build. We rely on:
#   --sort=name              sorted file order
#   --owner=0 --group=0      no per-host UID/GID leakage
#   --numeric-owner
#   --mtime=@$(SOURCE_DATE_EPOCH)   fixed timestamps
#   gzip --no-name --best    no embedded filename/timestamp, max compression
#
# We tar from the parent directory (workshop-tooling/) into facilitator-kit/
# so the archive root is "facilitator-kit/" — matches operator's documented
# `cd facilitator-kit-toorcamp-2026 && sudo ./install.sh` workflow once the
# directory is renamed on extract. For unambiguous extraction we rename the
# top-level entry to $(KIT_NAME) via --transform.
# -----------------------------------------------------------------------------
.PHONY: tarball
tarball: assemble
	@echo "==> Building reproducible tarball at $(TARBALL)..."
	@rm -f "$(TARBALL)"
	@cd "$(WORKSHOP_TOOLING)" && \
		tar --sort=name \
		    --owner=0 --group=0 --numeric-owner \
		    --mtime=@$(SOURCE_DATE_EPOCH) \
		    --transform='s,^facilitator-kit,$(KIT_NAME),' \
		    --exclude='facilitator-kit/.git' \
		    --exclude='facilitator-kit/scripts' \
		    -cf - facilitator-kit | \
		gzip --no-name --best > "$(TARBALL)"
	@echo "==> Tarball built. Size + MD5:"
	@ls -l "$(TARBALL)" | awk '{printf "    size: %s bytes\n", $$5}'
	@md5sum "$(TARBALL)" | awk '{printf "    md5:  %s\n", $$1}'


.PHONY: selftest
selftest:
	@bash "$(KIT_DIR)/selftest.sh"


.PHONY: clean
clean:
	@echo "==> Removing built tarball..."
	@rm -f "$(TARBALL)"
	@echo "==> Done."

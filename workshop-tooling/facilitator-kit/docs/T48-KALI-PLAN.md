# T48-KALI-PLAN — Xgecu T48 In-Circuit Clip Read **and Write** on Kali

## ToorCamp 2026 · "Dead Bytes Tell No Lies" · Session T+4c forged, T+4d refined, T+4e validated, T+4f revised

> **Authoring agent:** Electrode (Electrical & Hardware Engineering specialist), routed by Neo.
> **Status:** **Plan VALIDATED end-to-end at T+4e on physical hardware** — Phases 1–5 all PASS on the
> primary SOIC-8-clip-via-ZIF rig (read + write + verify + functional keypad unlock of injected codes).
> T+4f folds the bench reality back into this document: (a) `-i` flag standardised across every minipro
> invocation (T+4e empirical finding — see §1.5 and §3.4); (b) device-name string corrected throughout
> to `AT45DB041E[Page264]@SOIC8` (bare `AT45DB041E` returns "Device not found"); (c) Phase 4.2 expected-
> size clarified for the 540,672 vs 540,800 distinction; (d) §3.2 ICSP map upgraded from "research-photo-
> derived inference" to "T48 side-printed Xgecu diagram, empirically validated"; (e) §1.5 firmware-
> mismatch warning re-classified from "untested risk" to "validated NON-BLOCKING"; (f) **new Appendix A**
> documents the second-board individual-lead-clip all-zero-dump diagnostic procedure for T+4g.
> **Scope:** Build and validate an Xgecu T48 toolchain on Kali, and use it to **read AND write** the
> access-control lock's AT45DB041E DataFlash **in-circuit, via a SOIC-8 clip**, replicating the
> methodology the operator's own `PhysAccessDigiLies` research used. The plan now covers **two Linux
> toolchains** — `minipro` (native) and **Xgpro under Wine** (the research's actual, proven path) — and
> validates the **full read → validate → write → verify pipeline**, because the workshop's
> lock-exploitation arc includes code injection (a write).
> **This is a toolchain-build-and-validation plan, not a workshop-rollout plan.** The
> CH341A-vs-T48 workshop-toolchain decision is **deferred** by operator decision. Phase 6 gives the
> operator the cost / setup / UX facts to make that deferred call; it does not make the call.

---

## 0. Why this plan exists — what changed since T4-DIAGNOSTIC-AND-TOOLCHAIN.md

`T4-DIAGNOSTIC-AND-TOOLCHAIN.md` (read it for the full history) chased a **CH341A + flashrom** toolchain
across three bench failures:

- **T+4b** — in-circuit read on a *live, self-powered* lock board: `LIBUSB_TRANSFER_ERROR` flood from the
  CH341A browning out (two 3.3 V sources on the chip's VCC rail + the live MSP430 contending on the SPI bus).
- **T+4c** — out-of-circuit read (chip desoldered onto a SOIC-8-to-DIP adapter): brown-out / re-enumeration
  loop, then `No EEPROM/flash device found`.

**Three decisive facts from the operator scope this plan:**

1. **The desoldered chip ran very hot when powered by the CH341A** — and never got hot during the
   in-circuit attempts on the lock board. A chip drawing enough current to run hot is damaged. The
   **desoldering operation cooked the chip.** The CH341A brown-outs in T+4c were that damaged chip pulling
   the CH341A's weak regulator down — the H.1 rank-2 "current-leaky / latch-up-damaged chip" hypothesis,
   now **confirmed** by the thermal observation. The chip read by the CH341A is dead; it is not ground
   truth for the workshop and the original lock's codes are no longer recoverable from *that* chip.
2. **The `PhysAccessDigiLies` research read AND wrote the lock's AT45DB041E IN-CIRCUIT with a SOIC-8
   clip — no desoldering.** The research notes say it plainly: *"I clipped onto the NAND to read existing
   codes and write my own."* The T48 powered the lock board through the clip and read/wrote the chip in
   place. This **contradicts Section G of the diagnostic doc**, which *inferred* (from "the T48 is a
   ZIF-socket programmer") that the research used an out-of-circuit ZIF socket. **The research evidence is
   the authority: it was an in-circuit clip read AND write.** See Section 8 for the reconciliation flag.
3. **The research's programmer software was Xgpro, not `minipro`.** The research notes' "Tooling Note:
   Xgpro Software" section and the `uploads/plan` write-up (*"I was using the wrong settings in XGPro,
   and thus would always get all 00 to the flash"*) confirm the research toolchain was **Xgpro (the
   Xgecu Windows software) coerced onto Linux under Wine.** `minipro` (clean native-Linux) was *not* the
   research's path. This plan now documents **both** Linux toolchains and recommends a sequencing.

**The consequence.** Desoldering is what cooked the chip. An in-circuit clip read+write, if reproducible
on the T48, lets the workshop skip desoldering entirely — removing both the step that destroyed the chip
and the desolder/resolder skill barrier for a 90-minute room. The operator owns an Xgecu T48 and wants to
prove the **full read AND write pipeline** works **in-circuit, via clip, on Kali, easily** — to replicate
the research and to decide whether to commit to purchasing T48 units for the workshop.

> **Important — this plan needs a chip with live data, and a SPARE chip for the write test.** The chip the
> CH341A cooked is gone. To recover the *original lock's* user codes, the operator must use a **second,
> intact lock** (chip never desoldered, never CH341A-powered) and clip onto *that* lock's AT45DB041E
> in-circuit. **The write test (Phase 5) must NOT target that intact lock** — it targets a SEPARATE,
> non-critical AT45DB041E. See the Phase 5 safety constraint. **Confirm with the operator which lock/chip
> Phase 4 reads and which separate chip Phase 5 writes before those phases start.**

---

## Phase summary

| Phase | What it does | Primary actor |
|---|---|---|
| 1 | Build & install **`minipro`** (David Griffith fork) on Kali — the native-Linux toolchain | Neo via Kali MCP |
| 1b | **Xgpro under Wine** — the documented fallback toolchain (research's actual path) | Neo via MCP + Operator |
| 2 | T48 USB bring-up — enumeration, permissions, the toolchain opens the device | Neo via MCP + Operator (plug in T48) |
| 3 | In-circuit SOIC-8 clip read — clip-to-T48 wiring, power/contention strategy | Operator (physical) + Neo (verify) |
| 4 | The **read** and verification — read command, dump size, ground-truth validation | Neo via MCP + Operator (clip on) |
| 5 | The **write + verify** — write a test pattern to a SPARE chip, read back, confirm | Neo via MCP + Operator (clip on) |
| 6 | Workshop-decision input — honest CH341A-vs-T48 comparison for the deferred call | Neo presents; Operator decides |
| 7 | Session/phase mapping — who does each step, for Neo to map onto sessions | — |

---

## PHASE 1 — `minipro` on Kali (native-Linux toolchain)

> **✅ T+4d execution status: Phase 1 COMPLETE — `minipro` 0.7.4 built & verified.** Built from David
> Griffith's GitLab fork (commit `fd6b56afcfee1bbcef78e465b7c512c1cd1999d3`, 2026-03-09, branch `master`)
> on the operator's Kali box via the `kali` MCP. `minipro --version` reports T48 support with **29,739
> devices** in the T48 database; binary installed to `/usr/local/bin/minipro`. The AT45DB041E device-name
> string is now **CONFIRMED** (§1.4b). The commands below record what actually ran; the call-outs in
> §1.3c, §1.4 and §1.5 reflect bench findings.

**Goal:** a working `minipro` binary on the operator's Kali box (kernel 6.19.14, x86_64) that recognises
the Xgecu T48 and has the AT45DB041E in its device database.

> **Why two toolchains.** `minipro` is the *clean, native-Linux* path. **Xgpro-under-Wine (Phase 1b) is
> the path the `PhysAccessDigiLies` research actually used and is therefore the path KNOWN to work** for
> this exact chip on this exact lock board. The operator's stated T+4d goal is to prove the T48 works
> "easily, without headache" on Kali — so the plan attempts the lower-friction path first and keeps the
> proven path as a documented, fully-actionable fallback. The sequencing recommendation is in §1b.5.

### 1.1 — Which fork, and the T48 support fact

- **The correct fork is David Griffith's `minipro` — `gitlab.com/DavidGriffith/minipro`.** This is the
  actively-maintained one. Do **not** use older mirrors, the unrelated GitHub `radiomanV/TL866` work,
  or `wd5gnr/qtl866` (a separate Qt GUI). The diagnostic doc already names this fork (Section A.6).
- **T48 support is present in the current `minipro`.** The repository README's supported-hardware line
  reads: *"Compatibility with TL866CS, TL866A, TL866II+, T48, and T56 from XGecu."* T48 / TL866-3G
  support was added after the original 2022 feature request (issue #270) and is in the **`master`
  branch** today. **Build from the current `master` HEAD** — do not pin to an old tagged release; T48
  support is comparatively recent (post-2022) and `master` is where it is most complete.
- The Kali apt repositories do **not** carry `minipro` (confirmed T+4b and re-confirmed for this plan —
  `apt-cache policy minipro` returns nothing). Build-from-source is the only path on Kali.

### 1.2 — Build dependencies (Kali / Debian)

The minipro README's Debian/Ubuntu dependency line is:

```
build-essential pkg-config git libusb-1.0-0-dev zlib1g-dev
```

**Bench check already done for this plan** on the operator's Kali box:

| Package | Status on the operator's Kali |
|---|---|
| `git` | INSTALLED |
| `build-essential` | INSTALLED |
| `pkg-config` | **MISSING — must install** |
| `libusb-1.0-0-dev` | **MISSING — must install** |
| `zlib1g-dev` | check at run time (likely missing) |

So Phase 1 **does** need an `apt-get install` step. **⚠ ToorCamp is offline.** Do Phase 1 at home, on
network, before leaving — exactly as the diagnostic doc's "offline-at-campground note" says for flashrom.
For a campground rebuild on another laptop, the `.deb` files for these four packages would need to be
vendored (mirrors the Section E standalone-package idea, but that is out of scope here).

```bash
# 1.2 — [Neo via MCP] install minipro build dependencies (CHANGES THE SYSTEM — needs network)
sudo apt-get update
sudo apt-get install -y build-essential pkg-config git libusb-1.0-0-dev zlib1g-dev
```

### 1.3 — Build from source

> **⚠ The `kali` MCP runs as root.** Commands issued via the MCP execute as `root`, so `~` resolves to
> **`/root`** — the build was done in `/root/minipro`, and the `sudo`-prefixed commands in this plan ran
> *without* `sudo` (already root) when executed via the MCP. The `~/minipro/...` paths in Phase 2.3 are
> therefore `/root/minipro/...` on the operator's box; keep that in mind if the operator runs any step
> from a non-root shell.

```bash
# 1.3a — [Neo via MCP] clone the actively-maintained fork
cd ~                                  # or any working dir the operator prefers
git clone https://gitlab.com/DavidGriffith/minipro.git
cd minipro
git log -1 --format='%H  %ci'          # RECORD the commit hash + date — provenance for the build

# 1.3b — [Neo via MCP] build
make

# 1.3c — [Neo via MCP] install (CHANGES THE SYSTEM — installs the binary + man pages; STAGES udev rules)
sudo make install
```

Notes:
- `sudo make install` places the `minipro` binary in `/usr/local/bin`, installs man pages and
  bash-completion. **It does NOT install the udev rules to the system** — the Makefile's udev step is
  conditional on a rules-directory variable that resolved **empty** on the bench (T+4d), so the rule
  files were **not** copied to `/etc/udev/rules.d/`. They are **staged in the source tree** at
  `~/minipro/udev/` (`/root/minipro/udev/` for MCP-run commands) — three files: `60-minipro.rules`,
  `61-minipro-plugdev.rules`, `61-minipro-uaccess.rules`. **Phase 2.3 is the step that installs them
  to the system** by copying them manually.
- The README documents `sudo make install-algorithm` **for the T56 only** (it ships per-device
  programming-algorithm blobs). The **T48 does not need `install-algorithm`** — skip it.
- If `make` fails on a missing header, the cause is almost always a missing dependency from 1.2 —
  re-check `pkg-config` and `libusb-1.0-0-dev` first.

### 1.4 — Verify the install

> **⚠ `minipro -l` is INTERACTIVE without a programmer attached — it will HANG under the MCP.** With no
> T48 plugged in, `minipro -l` prints `No device found. Which database do you want to display?` then a
> menu (`1) TL866A/CS  2) TL866II+/T48/T56  3) T76  4) Abort`) and **blocks on stdin**. The `kali` MCP
> provides no stdin, so a bare `minipro -l | grep ...` or `| wc -l` hangs until the MCP timeout kills it.
> The commands below were rewritten (T+4d) to use **non-interactive** methods that need no programmer and
> no stdin. (Once the T48 *is* plugged in — Phase 2+ — `minipro -l` does not show the prompt and can be
> used directly.)

```bash
# 1.4a — [Neo via MCP] version + provenance
minipro --version

# 1.4b — [Neo via MCP] confirm the AT45DB041E is in the device database — grep the device DB XML
#         directly: no programmer, no stdin prompt, robust under the MCP.
grep -io 'AT45DB041[A-Z0-9@]*' /usr/local/share/minipro/infoic.xml | sort -u

# 1.4c — [Neo via MCP] confirm the device DB loaded — feed the menu choice non-interactively
#         (option 2 = TL866II+/T48/T56 = the T48's database) and count the rows.
echo 2 | minipro -l 2>/dev/null | wc -l        # a large number = the device DB loaded correctly
```

**Expected:**
- `1.4a` → a version string. **T+4d bench result:** `minipro version 0.7.4` (built from `master` HEAD
  commit `fd6b56a…`, *"Updated T48 latest firmware (01.1.38 / 0x126)"*, 2026-03-09). **Recorded.**
- `1.4b` → **RE-RESOLVED (T+4e — supersedes T+4d).** The device DB
  (`/usr/local/share/minipro/infoic.xml`, 17.8 MB) carries plain-string entries `AT45DB041E` and
  `AT45DB041D` AND package-suffixed entries. **T+4e bench finding: passing the bare string
  `AT45DB041E` to `minipro -p` returns `Device AT45DB041E not found!`.** The string `minipro` actually
  accepts on the bench is the **fully-qualified, package-suffixed, page-mode-qualified form**:
  **`AT45DB041E[Page264]@SOIC8`** — 264-byte native page mode, SOIC-8 package. **This is the confirmed
  `-p` argument for Phases 3.4, 4.1, 5.4 and the Phase 7 session map.** The earlier T+4d note that the
  plain `AT45DB041E` entry "is the confirmed `-p` argument" was wrong on the empirical bench — the DB
  carries the entry but the CLI does not resolve it. Use `AT45DB041E[Page264]@SOIC8` everywhere.
- `1.4c` → tens of thousands of lines. **T+4d bench result:** `minipro --version` reports the T48
  database holds **29,739 devices** — the DB loaded correctly.

> **Note — the T48 hardware is *not* verified by Phase 1.** `minipro -l` reads the *device* database;
> it does not touch the programmer. `minipro` reports the **programmer model** only when it performs a
> **device action** with the T48 plugged in — the first confirmation is **Phase 2.4 / 2.5**.

### 1.5 — ℹ Informational: T48 firmware vs. `minipro` version disagreement — VALIDATED NON-BLOCKING

> **T+4e empirical disposition — supersedes the T+4c/T+4d framing as "risk".** On the operator's bench
> the T48 reports firmware **00.1.34 (0x122)** and `minipro` 0.7.4 expects **01.1.38 (0x126)** — a
> two-revision firmware lag. `minipro` prints the mismatch as a warning on every device action. **T+4e
> tested every operation in the Phase 2→5 workflow against this warning — `minipro -k`, `-L`, `-d`, the
> Phase 3.4 dry probe, the Phase 4 full main-array read (twice, byte-identical), and the Phase 5 full
> main-array write+verify on the live intact lock — and ALL succeeded `exit=0` with the warning printed
> and zero protocol mangling.** The warning is **informational only**; it is **NOT a blocker** and the
> entire read/write pipeline operates correctly through it. The check below is retained for diagnostic
> visibility, but the recommendation in the disposition list is updated accordingly.

This is a real, documented risk and the operator must know it before relying on the `minipro` toolchain:

- The T48 has **on-board firmware**. Xgecu's Xgpro software ships firmware **bundled per Xgpro version** —
  installing a given Xgpro version can flash a matching firmware onto the T48. The current Xgpro line is
  around v13.x (released 2026).
- `minipro` speaks the T48 protocol for chip read/write/verify, but expects the T48's firmware to be
  within a protocol range it understands. If the T48's firmware is **newer or older** than the installed
  `minipro` build handles, `minipro` may print a firmware warning, refuse to run, or behave unpredictably.
- **`minipro` cannot update the T48's firmware. Only Xgpro can.** This is the one task that unavoidably
  needs Xgpro — which, usefully, the plan now sets up under Wine in Phase 1b anyway.

**How to check and handle it (do this in Phase 2, once the T48 is plugged in):**

```bash
# [Neo via MCP] minipro prints firmware info on a device action:
minipro --version            # software version
sudo minipro -q              # query — minipro reports the programmer model AND firmware version
                             # (if -q is not accepted on this build, any device action surfaces it)
```

- Clean firmware line, proceeds → **no action needed.**
- Firmware **mismatch warning printed but operation completes `exit=0`** (the T+4e-observed case) →
  **proceed.** This is the validated NON-BLOCKING state. Record the warning text for diagnostic
  provenance and continue with Phases 2→5. The remaining minipro invocations in this plan use `-i`
  (skip-ID-check, see §3.4) which is the standing fix going forward.
- **Updated standing recommendation re: `--update_firmware`.** `minipro` man-page does expose
  `--update_firmware`, but **do not use it.** Reasoning: (a) no symptom currently to fix — the
  mismatch is validated NON-BLOCKING across the full Phase 2→5 workflow; (b) a failed firmware flash
  can brick the programmer; (c) flashing reframes the T48's provenance and may diverge it from what
  the operator's existing toolchain expects. **Standing rule: do not flash T48 firmware.** This rule
  holds even if `minipro` is upgraded later — the right hedge is `git pull && make && sudo make
  install` of `minipro`, not flashing the T48.
- If a future bench session ever observes a *protocol failure* (not just the warning) attributable to
  the firmware lag — read garbage, write that does not take, USB transfer errors — only then
  **(a)** rebuild minipro from current master OR **(b)** fall back to Xgpro-under-Wine (Phase 1b),
  Xgpro is firmware-matched by construction. Neither path requires flashing the T48.

---

## PHASE 1b — Xgpro under Wine on Kali (the documented fallback toolchain)

**Goal:** a working Xgpro install running under Wine on Kali, recognising the T48 — the toolchain the
`PhysAccessDigiLies` research actually used, set up so it is a real, actionable fallback rather than a
hand-wave. This phase can be deferred until/unless Phase 1/2 with `minipro` hits a wall (firmware
mismatch, T48 not recognised, AT45DB041E DataFlash read/write quirks) — but the operator should know the
full procedure up front.

### 1b.1 — Why Xgpro-under-Wine is the *known-good* path

- The research notes are explicit: the lock's AT45DB041E was read and written **with Xgpro**, and the
  `uploads/plan` write-up records a real Xgpro operational gotcha (*"I was using the wrong settings in
  XGPro, and thus would always get all 00 to the flash"*) — i.e. Xgpro **did the job**, with the usual
  learning curve. `minipro` was never part of the research.
- Xgpro is firmware-matched to the T48 by construction (the firmware ships inside the Xgpro installer),
  so the Phase 1.5 firmware-mismatch risk **does not exist** on the Xgpro path.
- Xgpro carries Xgecu's own AT45-series **DataFlash** algorithm and its per-chip **ICSP pinout diagram**
  (see §3.2) — both are first-party and authoritative.

The cost is setup friction: Xgpro is Windows software, and the research notes call its Linux/Wine setup
*"an exercise in patience."* §1b.5 makes the honest recommendation on sequencing.

### 1b.2 — A SAFER software source (do not use the .cn HTTP sites)

The research notes warn, verbatim:

> *"The official Xgpro software is only available via sketchy .cn sites over plaintext HTTP."*

**Do not download Xgpro from the .cn plaintext-HTTP mirrors.** The research notes themselves give the
safer source, and this plan adopts it:

- **Safer software source — `github.com/radiomanV/XGecu_Software`.** This is the source the research
  notes recommend in place of the .cn sites; `radiomanV` is the same maintainer associated with the
  open TL866 ecosystem. Fetch Xgpro from there (HTTPS, version-tagged) — **[Operator]** action, on
  network, at home before camp.
- A useful Linux setup reference the research notes also cite: **`boseji.com/posts/running-tl866ii-plus-in-manjaro/`**
  ("running TL866II-plus in Manjaro"). It targets the TL866II+ on Manjaro, but the Wine + udev pattern
  generalises directly to the T48 on Kali — use it as the worked reference for the steps below.

> **⚠ Provenance discipline.** Even from the safer GitHub source, this is third-party-redistributed
> vendor software. Record the exact release tag / commit and the file hash when fetched, the same
> provenance discipline §1.3a applies to the `minipro` build. Treat the binary as the operator's
> deliberate, eyes-open choice.

### 1b.3 — Wine + the Xgpro install

```bash
# 1b.3a — [Neo via MCP] install Wine on Kali (CHANGES THE SYSTEM — needs network, do at home)
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install -y wine wine32:i386 winetricks

# 1b.3b — [Operator] run the Xgpro installer under Wine
#         (the .exe fetched from github.com/radiomanV/XGecu_Software in 1b.2)
wine /path/to/Xgpro_setup.exe
```

**The two Wine-specific setup specifics the research notes flag — both are required:**

1. **`setupapi.dll` dropped into the Xgpro install directory.** Xgpro expects a Windows
   `setupapi.dll`; Wine's built-in one is not sufficient for Xgpro's USB device handling. Place a
   `setupapi.dll` into the Xgpro program directory (typically
   `~/.wine/drive_c/Program Files (x86)/Xgpro/` or `.../XGecu/Xgpro/`) and, if needed, set Wine to
   prefer the native DLL for that application via `winecfg` → Libraries → add `setupapi` → set to
   *native*. **[Operator]** action — the research notes record this as a hard requirement.
2. **Custom `udev` rules for the T48.** Wine reaches USB through the host's libusb; the operator's user
   must have non-root access to the T48 (`a466:0a53`). Install a udev rule granting `plugdev` (or the
   operator's group) read/write to that VID:PID — this is the **same udev requirement as the `minipro`
   path** (Phase 2.3), so if Phase 2.3 was done, this is already satisfied. If Phase 1b is run
   standalone, drop a rule equivalent to:

```
# /etc/udev/rules.d/60-xgecu-t48.rules — [Neo via MCP]
SUBSYSTEM=="usb", ATTRS{idVendor}=="a466", ATTRS{idProduct}=="0a53", MODE="0666", GROUP="plugdev"
```

```bash
# 1b.3c — [Neo via MCP] reload udev after writing the rule
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### 1b.4 — Verify Xgpro sees the T48

- **[Operator]** launch Xgpro under Wine (`wine "C:\Program Files (x86)\Xgpro\Xgpro.exe"` or via the
  Wine Start-menu shortcut). Xgpro's status bar / device dialog should report the **T48** connected and
  its firmware version. **Record both.**
- Select the chip in Xgpro: `AT45DB041E` (Adesto/Atmel, under the SPI DataFlash family). Confirm Xgpro
  loads the part with no error.
- If Xgpro reports no programmer: re-check the `setupapi.dll` placement (1b.3 step 1), the udev rule
  (1b.3 step 2 — and re-plug the T48 after a udev change), and try a different USB port/cable.

### 1b.5 — ⭐ SPECIALIST RECOMMENDATION — minipro-native first, Xgpro-under-Wine as fallback

**Recommendation: attempt `minipro` (Phases 1–2) FIRST; keep Xgpro-under-Wine (Phase 1b) as the
documented fallback. Reasoning, stated honestly both ways:**

- **`minipro` is the lower-friction path on Kali**, and the operator's explicit T+4d goal is to prove
  the T48 works "easily, without headache." `minipro` is a native-Linux CLI: install five apt packages,
  one `git clone`, one `make`, one `sudo make install`, one udev rule. No Wine prefix, no `setupapi.dll`
  surgery, no Windows installer, no third-party-redistributed vendor binary. It is also fully scriptable
  by Neo via the Kali MCP, which matters for a clean phase-by-phase run. If `minipro` works, it is the
  easiest possible answer to the operator's question.
- **But `minipro` is not yet proven on this chip.** It carries one genuine unknown — the firmware-vs-
  protocol mismatch risk (§1.5) — and DataFlash (not plain 25-series NOR) is a part class where an
  open-source tool's algorithm coverage should be *verified, not assumed*. `minipro` being lower-friction
  is a hypothesis until Phase 4/5 passes.
- **Xgpro-under-Wine is the path KNOWN to work.** The research read AND wrote this exact AT45DB041E on
  this exact lock board with Xgpro. It is firmware-matched, carries Xgecu's first-party DataFlash
  algorithm, and carries the authoritative per-chip ICSP pinout diagram. Its only liability is setup
  friction — and that friction is a *one-time* cost, fully enumerated in §1b.2–1b.4.

**Net:** try the easy path, fall back to the proven path. Concretely — **if at any point in Phases 1–5
`minipro` (a) reports a firmware mismatch it cannot resolve by rebuilding, (b) fails to recognise the
T48, or (c) mis-reads / fails to write the AT45DB041E DataFlash** — switch to Xgpro-under-Wine without
hesitation; it is set up and waiting. Do **not** burn the session fighting `minipro` past the point
where the fallback would be faster. The deliverable is a *proven* read+write pipeline, not a `minipro`
purity badge. (For the workshop-rollout implications of "Linux CLI vs. Wine GUI", see Phase 6.)

---

## PHASE 2 — T48 USB bring-up on Kali

**Goal:** the T48 enumerates on USB, the operator's user can access it without root, and the chosen
toolchain opens it and reports the programmer model.

### 2.1 — Enumerate the T48

Operator plugs the T48 into the laptop with the supplied USB cable, then:

```bash
# 2.1 — [Neo via MCP] does the T48 appear on the USB bus?
lsusb
lsusb | grep -i 'a466'
lsusb -t                              # confirm it sits at high-speed (480M)
```

**Expected VID:PID — `a466:0a53`.** The Xgecu T48 (along with the TL866II+ and T56) enumerates as
**`a466:0a53`** — this is the VID:PID the minipro `udev/` rules file targets for those three models,
and the same VID:PID the Phase 1b.3 Xgpro udev rule uses. (The older TL866A/CS is `04d8:e11c`; the newer
T76 is `a466:1a86` — neither is the operator's device.) The `lsusb` description text varies by firmware;
identify the T48 by **`a466:0a53`**, not by the description string.

> **If `lsusb` shows no `a466` device:** try a different USB cable and a different port, then re-run.
> Unlike the CH341A, the T48 is a **USB 2.0 high-speed (480 Mbit/s)** device — natively scheduled by the
> laptop's xHCI controller and **structurally immune** to the full-speed-on-xHCI failure mode that broke
> the CH341A (diagnostic doc Section F.2). The T48 plugs **directly into any USB port** — no USB 2.0 hub
> needed. `lsusb -t` should show it at `480M`.

### 2.2 — Confirm high-speed and power

```bash
# 2.2 — [Neo via MCP] descriptor sanity
lsusb -v -d a466:0a53 2>/dev/null | grep -E 'bcdUSB|bMaxPacketSize0|MaxPower|bcdDevice|iProduct'
```

- `bcdUSB` should read `2.x` (high-speed) — contrast with the CH341A's `1.10`. This is the property
  that makes the T48 immune to the Section F xHCI failure.
- `MaxPower` — note it. The T48 has its own current-capable supply for the chip-under-test; the USB
  `MaxPower` is the *programmer's own* draw, not the chip's.
- `bcdDevice` is the firmware-related device-release field — record it (feeds the Phase 1.5 firmware check).

### 2.3 — udev permissions for non-root access

`sudo make install` (Phase 1.3c) only **stages** the udev rules in the source tree's `udev/` directory —
it confirmed at T+4d that it does **not** install them to `/etc/udev/rules.d/`. **This step is what
installs them**, so the toolchain runs **without `sudo`**. (This step also satisfies the Xgpro-under-Wine
udev requirement of Phase 1b.3 — the VID:PID is the same.)

```bash
# 2.3a — [Neo via MCP] install minipro's three staged udev rules (CHANGES THE SYSTEM)
#         (~ = /root for MCP-run commands — see the Phase 1.3 root note)
sudo cp ~/minipro/udev/*.rules /etc/udev/rules.d/

# 2.3b — [Neo via MCP] reload
sudo udevadm control --reload-rules && sudo udevadm trigger

# 2.3c — [Neo via MCP] minipro's rule grants access via the 'plugdev' group — add the operator's user
sudo usermod -a -G plugdev "$(logname 2>/dev/null || echo "$USER")"
```

> **⚠ Group-membership caveat.** Adding a user to `plugdev` only takes effect on a **new login session**.
> If the toolchain still reports a permissions error after 2.3, either log out and back in, or run
> `minipro` with `sudo` for the bench session. **Running `minipro` under `sudo` is a valid, zero-friction
> fallback.** The commands in Phases 2.4–5 are written with `sudo` for safety; drop it if 2.3 succeeded
> and the operator has re-logged-in.
>
> **After 2.3, the operator should physically unplug and re-plug the T48** so the new rule applies.

### 2.4 — Confirm the toolchain opens the T48

```bash
# 2.4 — [Neo via MCP] minipro reports the PROGRAMMER MODEL on a device action
sudo minipro -q 2>&1 || sudo minipro --version 2>&1
```

`minipro -q` (query) makes `minipro` open the programmer and report **what it is** — the first point in
the plan where the **T48 hardware itself is confirmed working** on the `minipro` path. Expect a line
naming the programmer plus a firmware version line. **Record both.**

> **If `minipro -q` is not a valid flag on this build**, any device action surfaces the same info — e.g.
> the dry-probe in Phase 3.4. Consult `minipro --help`.
>
> **On the Xgpro-under-Wine path**, the equivalent confirmation is Phase 1b.4 — Xgpro's device dialog
> naming the T48 and its firmware.

### 2.5 — Phase 2 success criterion

- `lsusb` shows `a466:0a53` at high-speed; **and**
- the chosen toolchain opens the programmer and prints the programmer model + firmware version with no
  error (or only a firmware note that Phase 1.5 / the Phase 1b fallback dispositions).

If both hold → Phase 2 done, proceed to Phase 3. If the toolchain cannot open the device, work the
Phase 1.5 firmware check, the 2.3 permissions caveat, and — if `minipro` is the blocker — the Phase 1b
Xgpro fallback before going further.

---

## PHASE 3 — The in-circuit SOIC-8 clip read setup

This is the heart of the plan: clipping a SOIC-8 test clip onto the AT45DB041E **while it is still
soldered to the lock's PCB**, and driving it from the T48. This replicates the `PhysAccessDigiLies`
research method (evidence-confirmed — see §3.2) and, if reproducible, lets the workshop skip desoldering
entirely.

### 3.1 — The AT45DB041E SOIC-8 pinout (load-bearing fact)

From the AT45DB041E datasheet (`pdf/AT45Datasheet.pdf`, Atmel/Adesto 8783L–DFLASH; §1 "Pin Configurations
and Pinouts", 8-lead SOIC) — cross-checked against diagnostic doc Section H.2:

| Pin | Signal | Role | Maps to (programmer side) |
|---|---|---|---|
| 1 | **SI**   | Serial Input (MOSI — data into chip) | programmer MOSI / SI / DI |
| 2 | **SCK**  | Serial Clock                          | programmer CLK / SCK |
| 3 | **RESET**| Hardware reset, active-low, internal pull-up | see 3.3 — usually left to its pull-up |
| 4 | **GND**  | Ground                                | programmer GND |
| 5 | **CS**   | Chip Select, active-low               | programmer CS / SS |
| 6 | **WP**   | Write Protect, active-low, internal pull-up | see 3.3 / 5.3 |
| 7 | **VCC**  | Supply, 1.65–3.6 V (**3.3 V nominal**) | programmer **3.3 V** target supply |
| 8 | **SO**   | Serial Output (MISO — data out of chip)| programmer MISO / SO / DO |

Pin 1 = the **dot / notch** on the package; numbering runs **counter-clockwise from pin 1** viewed from
the top. **VCC = pin 7, GND = pin 4** — these are **not** a diagonal corner pair; count pins, do not
assume the "opposite corners" shortcut.

> **⚠ Confidence on this pinout: HIGH** — it is the standard AT45DB-series 8-SOIC assignment, confirmed
> directly in the operator's own copy of the datasheet (`pdf/AT45Datasheet.pdf`). The chip on the lock
> board is the **8-lead SOIC** (`adesto … 45DB041E SHN`, visible in the research photos
> `Media/20241001_223009.jpg` and `Media/20241130_223006.jpg` — `SHN` is the SOIC package suffix). The
> chip also ships in 8-UDFN with a different pad layout; the SOIC pinout above is the one that applies.

### 3.2 — How the SOIC-8 clip connects to the T48 — research-grounded

**The research evidence pins this down. From the `PhysAccessDigiLies` research repo:**

- The research notes state plainly: *"I clipped onto the NAND to read existing codes and write my own."*
  — an **in-circuit clip** read+write, not an out-of-circuit socket read.
- The research photo **`Media/20241002_205355.jpg`** shows the actual rig: the **Xgecu T48** (the black
  ZIF-socket programmer, blue power LED lit, ZIF lever up) with a **multi-conductor rainbow ribbon
  running from the T48 to a small adapter PCB**, while the lock board sits elevated on standoffs.
- The research photo **`Media/20241204_221147.jpg`** shows it more directly: the T48 connected by a
  ribbon to a **SOIC-8 clip clamped onto a chip on the lock board**, the clip's flying leads routed up
  to the T48's header.
- The research notes' `uploads/plan` write-up repeatedly references reading and writing the chip with
  the T48/Xgpro in this in-circuit configuration (*"When checked using a T48, all data was listed as
  00"*).

**What the evidence supports, raised to its warranted confidence:**

1. **Clip type — a SOIC-8 (8-pin, 1.27 mm pitch) test clip.** Confirmed: the research clipped onto the
   8-lead SOIC AT45DB041E in place. *Confidence: HIGH.*
2. **The clip met the T48 via a small ADAPTER PCB carrying a ribbon, not 8 bare flying leads.** The
   photos show a ribbon-to-adapter arrangement between clip and programmer. *Confidence: MODERATE–HIGH.*
   This matters: it means the clip's 8 signals were marshalled through an adapter into the T48's
   header — likely the T48's **ICSP** path, since ICSP is the T48's in-circuit interface (see below).
3. **The T48 powered the lock board through the clip** — see §3.3(c). *Confidence: HIGH* (the research
   describes the T48-only-powered configuration explicitly).

**ICSP map — RESOLVED at T+4e, source upgraded.** The T48's own **side-printed Xgecu ICSP wiring
diagram** (silk-printed on the side of the T48 case) is now the load-bearing source for the ICSP pinout.
The operator's bench orientation when reading it (T+4e): **dot upper-left, lever lower-right.** Read in
that orientation, the diagram resolves to standard 8-pin DIP convention:

> **SOIC-8 clip pin N → T48 ZIF pin N at the marker-end of the socket.**

i.e. clip pin 1 (the dotted/marker side of the clip) lands on the ZIF socket pin closest to the socket's
own marker end, clip pin 2 on ZIF pin 2 of that same end, and so on through pin 8. Cross-validated by the
operator's recall of the original `PhysAccessDigiLies` research's radiomanV/XGecu reference map. Most
importantly, **the T+4e bench session executed Phases 3.4 → 4 → 5 against this map and got byte-identical
repeat reads, a clean Phase 5 write+verify, and a functional keypad-unlock outcome on the lock** —
empirical confirmation that the map is correct. *Confidence: VERY HIGH — bench-validated end-to-end.*

This empirical confirmation supersedes the earlier "research-photo-derived inference" framing. The
fallback sources below remain documented for cross-checking on a different T48 unit, but they no longer
gate the wiring decision on this T48.

**Fallback ICSP-map cross-check sources** (if the T48's side-printed diagram is unreadable on a given
unit, or on a future second T48 whose firmware/silk may differ):

  1. **The T48's own side-printed Xgecu diagram** — the primary source, T+4e-validated above.
  2. **Xgpro's per-chip ICSP pinout screen.** Xgpro shows, **per selected chip**, an "ICSP" diagram
     giving the exact wire-to-pin map for that device. Select `AT45DB041E[Page264]@SOIC8` in Xgpro
     (already installed under Wine if Phase 1b was run) and read its ICSP diagram — definitive,
     chip-specific, first-party.
  3. **The leaflet in the T48's box.** Many T48 units carry the ICSP map both as silkscreen and as
     printed leaflet.
  4. **`man minipro` / minipro ICSP docs** — describes minipro's ICSP usage and any ICSP mode flag.
  5. **A top-down photo of the T48** in good light capturing the side-printed diagram, for
     Neo/Electrode to confirm before the clip is wired on a future unit.

**What the research evidence pinned down but did NOT identify as the source of authority** (kept for
historical completeness — superseded by the side-printed diagram above): the research photos
`Media/20241002_205355.jpg` and `Media/20241204_221147.jpg` show a SOIC-8 clip + ribbon + adapter rig to
the T48 on the lock board, confirming the in-circuit clip method, but they did not surface the pin-by-pin
ICSP map at legible resolution. The T48's side-printed diagram + the T+4e empirical bench run resolved
the map.

**What the ICSP wiring must achieve** (independent of exact pin numbers): each of the 8 SOIC-8 clip
leads — SI, SCK, RESET, GND, CS, WP, VCC, SO — connects, through the adapter, to the T48 pin carrying
the *same* signal. For an SPI DataFlash read the indispensable lines are **VCC, GND, CS, SCK, SI (MOSI),
SO (MISO)**; **RESET and WP** are active-low with internal pull-ups and are normally fine left to their
pull-ups for a read (the write phase revisits WP — see §5.3).

> **Out-of-circuit ZIF-socket-via-adapter is NOT what the research did and NOT this plan's path.** A
> SOIC-8 clip can instead terminate at an adapter that plugs into the ZIF socket — but that is only for a
> chip *not* on a powered board. The research evidence is unambiguous that the read/write was
> **in-circuit via clip**; ICSP is the correct T48 interface for it. **Confirm with the T48
> documentation / Xgpro that ICSP is the intended in-circuit path for an 8-pin SPI DataFlash part before
> proceeding.**

### 3.3 — The in-circuit contention question — reconciled against the research evidence

The lock's AT45DB041E is on a PCB that also carries a **live MSP430 microcontroller** (the board's normal
SPI master to this DataFlash) and the lock has **its own battery pack**. Reading/writing in-circuit means
the T48 and the lock's own electronics share the SPI bus and potentially the power rail. The diagnostic
doc Section F.0 identified this exact configuration as what browned out the *CH341A*. The questions, and
the answers — now reconciled against the research's documented working setup:

**The research's documented working configuration.** The `PhysAccessDigiLies` notes describe the setup
that produced **reliable reads and writes**, verbatim:

> *"Only the programmer was plugged into USB. / The board was rock still. / A successful memory read
> occurred first. / A small write was done. / Then the main memory was erased and a full upload
> attempted."*

This is the ground truth the plan's contention reasoning must match. It tells us four things: (1) **the
T48 was the only USB device** — nothing else energised or contending; (2) **mechanical stillness mattered**
— consistent with a fussy in-circuit clip contact; (3) **read happened before any write** — the safe
ordering this plan builds into Phases 4→5; (4) the research does **not** mention the lock battery as part
of the working write setup. The plan's "battery out" reasoning below is consistent with the research and
is sound first-principles practice; the research evidence *refines* it on two points (marked **[refined]**).

**(a) Power — remove the lock's battery; let the T48 power the board through the clip.**
- **Remove the lock's battery pack.** With the lock battery in *and* the T48 supplying VCC through the
  clip, there are **two power sources on the chip's VCC rail** — the dual-power conflict of diagnostic
  doc F.0 Mechanism 1. Two low-impedance 3.3 V sources never sit at the same voltage; one back-feeds the
  other. **Battery out.**
- **[refined]** The research's *"only the programmer was plugged into USB"* generalises to the same
  intent: **only the T48 should be energising the system.** Battery-out is the lock-board-side expression
  of that single-source principle. With the battery out, the **T48's clip is the only power source** —
  it energises the chip *and* the rest of the otherwise-unpowered lock board through the clip's VCC line.

**(b) The MSP430 on the shared SPI bus.**
- With the lock battery removed, the MSP430 is **de-energised** — it cannot run firmware and cannot
  actively drive CLK / MOSI / CS as a competing SPI master. That removes diagnostic doc F.0 Mechanism 2
  (bus contention from a live second master). This is the primary reason "battery out" matters.
- **Residual effect:** the MSP430's port pins, even unpowered, still present some loading (input
  capacitance, internal ESD diodes) on the shared SI/SCK/SO/CS nets. For a small lock board this is
  normally a tolerable load — the research's repeated in-circuit success is the evidence — but it is why
  an in-circuit read/write is never *quite* as clean as a socketed one, and it is why §5.4 calls for an
  extra verification pass after a write.
- **Does the MSP430 need to be held in reset?** With the battery removed it is not running, so an
  explicit reset hold is **not required** for the basic case. *If* an in-circuit operation with the
  battery out still returns garbage or fails to detect the chip, holding the MSP430 in reset is the next
  mitigation — a **board-level intervention; flag it to the operator, treat it as a contingency.**

> **Scope boundary — do not conflate the DataFlash clip with the MSP430 UART/BSL work.** The research
> notes also describe *"I soldered micro-jumpers to UART pins under conformal coating — barely connecting
> to the BSL for an instant one time"* and extensive MSP430 JTAG firmware work (MSP-FET, UniFlash,
> Ghidra). **That is MSP430-firmware tradecraft and is OUT OF SCOPE for this plan.** This plan covers
> only the **AT45DB041E DataFlash** accessed via **SOIC-8 clip**. The MSP430 appears here solely as a
> bus/power neighbour to be silenced (battery out), not as a target. The research photos from Nov 2024
> onward (`Media/20241115_*`, `20241116_*`, `20241130_*`, `20241204_*` MSP-FET shots) are the firmware
> work; the DataFlash-clip evidence is the Oct 2024 cluster (`Media/20241001_*`, `20241002_205355.jpg`).

**(c) Why the T48 succeeds in-circuit where the CH341A browned out — the supply-current point.**
- The CH341A's 3.3 V comes from a **tiny, weak on-board regulator** cheaply derived from USB 5 V. It is
  sized to power *one bare flash chip*, not a whole PCB. Asked to source current into an entire lock
  board through the clip, its rail collapses, it browns out, its USB PHY resets — the observed
  T+4b/T+4c failure.
- The **T48 has a real, current-capable regulated target power supply** — the same supply that drives
  chips in its 40-pin ZIF socket. It can energise the chip **plus the modest load of a small lock board**
  through the clip without browning out. **This is the structural reason the research's in-circuit clip
  read+write worked on a T48 and the bench's in-circuit attempt failed on a CH341A** — a power-delivery
  capability difference, not a protocol difference. (Diagnostic doc Section G.4 reaches the same
  conclusion.)

**(d) Target voltage — 3.3 V.**
- The AT45DB041E is a **1.65–3.6 V part, 3.3 V nominal** (datasheet §Description; diagnostic doc A.5).
  **The T48's target supply must be set to 3.3 V.** In `minipro` this follows from selecting the
  `AT45DB041E` device (the device entry carries the part's voltage); in Xgpro the device selection sets
  it likewise. Verify it in any voltage/options output the toolchain prints, and **never override it
  upward** — a 5 V drive into a 3.6 V-max part is a chip-killing hazard.

**(e) Clip-contact discipline.** A SOIC-8 clip onto a soldered chip is mechanically fussy — all 8 jaws
must seat on all 8 leads, and pin-1 of the clip must align to pin-1 (the dot) of the chip. The research's
*"the board was rock still"* is exactly this concern. A poor clip contact produces a "no device found" or
an all-`0xFF` / all-`0x00` read. If Phase 4 detects nothing, **re-seat the clip before suspecting anything
else.** For the write phase a mid-operation contact loss is worse than a failed read — see §5.

### 3.4 — Dry probe (clip on, before committing to a full read)

```bash
# 3.4 — [Neo via MCP] confirm the toolchain sees the chip through the clip. Device-name string is the
#        fully-qualified 'AT45DB041E[Page264]@SOIC8' (T+4e bench finding — bare 'AT45DB041E' returns
#        'Device AT45DB041E not found!').
#
#        First-pass dry probe — NO -i — to read the chip's JEDEC ID through the protocol:
sudo minipro -p 'AT45DB041E[Page264]@SOIC8' -D 2>&1        # -D = --read_id: read the chip ID off the bus
# -D reads the chip ID and does nothing else — it is the online hardware ID read that confirms the chip
# is on the SPI bus. Xgpro path: select AT45DB041E[Page264]@SOIC8, use Xgpro's "Detect/Read ID" — same
# goal: identify the chip, write nothing.
```

> **⚠ Use `-D` (uppercase), NOT `-d` (lowercase), for the dry probe — they are different operations.**
> Ground-truth from `man minipro` on the operator's `minipro 0.7.4` (confirmed empirically at T+4g — the
> 2nd board returned the correct chip ID `0x1F24` with `-D`):
>
> - **`-d, --get_info <device>`** — "Show device information." This is an **OFFLINE database lookup**
>   that takes a `<device>` argument and prints the part's parameters from `minipro`'s device DB. It
>   **never touches the SPI bus** and therefore **cannot tell you whether a chip is actually present and
>   responding** on the clip. (Lowercase `-d` is still the correct flag for the legitimate "what does
>   the DB say about this part" use — e.g. surfacing the `Code Memory 540,672 + 64 + 64` line in §4.2.)
> - **`-D, --read_id`** — "Just read the chip ID and do nothing else." This is an **ONLINE hardware
>   chip-ID read** over the SPI bus — built for scripts that need to "detect if a chip is inserted." This
>   is the operation a dry probe wants: it discriminates chip-on-bus from chip-absent.
>
> The dry probe's entire purpose is to confirm the chip responds on the bus, so it **must** use `-D`. An
> earlier draft used lowercase `-d` here — an offline DB lookup that would "succeed" with no chip clipped
> at all, hiding the exact failure the probe exists to catch.

**Expected:** the toolchain opens the T48, identifies the AT45DB041E (JEDEC ID `0x1F24`), prints chip
parameters with no USB error. The firmware-mismatch warning (§1.5) WILL be printed — that is benign.

**T+4e bench empirics on the dry probe:** the first attempt occasionally returns `Chip ID 0x0000`
(unknown) — caused by either an imperfect clip contact OR an intermittent T48-firmware-vs-`minipro`
ID-check handshake glitch with this specific AT45DB041E sample. The fix is two-step: **(a)** re-seat the
clip per §3.3e; **(b)** re-run the dry probe. On a clean re-seat the second attempt has returned **Chip
ID 0x1F24 OK** (matches the AT45DB041E JEDEC vendor+device-ID bytes) — at which point the SPI handshake
is empirically proven and Phase 4 is safe to proceed.

> **⚠ The standing fix for the ID-check intermittency — `-i` from Phase 4 onward.** Once the §3.4 dry
> probe has confirmed JEDEC ID `0x1F24` **at least once**, **every subsequent `minipro` invocation in
> Phases 4, 5, 5.4 uses the `-i` flag** (skip-ID-check). Rationale: the T48 firmware (`00.1.34` /
> `0x122`) returns Chip ID `0x0000` *intermittently* during the ID-check exchange with this AT45DB041E
> sample, even when the chip is responding correctly on the SPI bus. The intermittent failure stops the
> programmer's read/write sequence at the ID check despite the chip being healthy. T+4e empirically
> validated that `-i` resolves this — the read/write/verify pipeline succeeds with `-i` after the dry
> probe has confirmed the chip is on the bus once. This is **the** standing flag going forward. (It is
> the CLI equivalent of unchecking *"Match Chip ID"* in Xgpro, which the original `PhysAccessDigiLies`
> research also did.) **Do not use `-i` on the very first dry probe** — the dry probe is exactly when
> you *want* the ID check to fire so you know the SPI handshake works at least once.

If the dry probe reports the wrong chip ID or "device not detected" *after re-seating*, re-check pin-1
alignment, re-confirm the ICSP wiring (3.2) before Phase 4. If repeated dry-probe attempts cannot get
JEDEC ID `0x1F24` even once, escalate to Appendix A (alternative-clip-rig diagnostic) before assuming the
chip is dead — the all-zero failure mode there is the canonical "chip not actually on the SPI bus" case.

---

## PHASE 4 — The read and ground-truth validation

**Goal:** a faithful binary dump of the lock's AT45DB041E, validated as ground truth. **This read must
complete and validate BEFORE any write is attempted** (Phase 5) — see the §5 ordering constraint.

### 4.1 — The read command

```bash
# 4.1 — [Neo via MCP] read the AT45DB041E main array to a file.
#        Device-name string is the fully-qualified 'AT45DB041E[Page264]@SOIC8' (T+4e bench finding —
#        bare 'AT45DB041E' returns 'Device AT45DB041E not found!').
#        -i flag skips the ID check (the §3.4 dry probe is the once-per-session ID-check confirmation).
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -r dump.bin
# Xgpro path: select AT45DB041E[Page264]@SOIC8, uncheck "Match Chip ID", Read -> save the buffer to
#             dump.bin.
```

- `minipro` uses `-p <device>` to select the chip and `-r <file>` to read it into a file. `-i` is the
  standing flag from §3.4 (skip-ID-check after dry-probe confirmation).
- The `-p` string is the fully-qualified **`AT45DB041E[Page264]@SOIC8`** — confirmed empirically at
  T+4e. The bare `AT45DB041E` returns `Device AT45DB041E not found!`; the DB carries the entry but the
  CLI requires the page-mode + package suffix. If `minipro` ever rejects the qualified name, re-confirm
  with `grep -io 'AT45DB041[A-Z0-9@\[\]]*' /usr/local/share/minipro/infoic.xml | sort -u`.
- **⚠ Xgpro page-mode setting.** The research's `uploads/plan` records a real Xgpro gotcha — *"I was
  using the wrong settings in XGPro, and thus would always get all 00 to the flash."* On the Xgpro path,
  confirm the AT45DB041E **page-mode / read settings** are correct (264-byte native vs 256-byte power-of-2
  — see §4.2) before trusting a read. An all-`0x00` Xgpro result is the documented symptom of a wrong
  setting, not necessarily a dead chip. The same all-`0x00` failure mode shows up on `minipro` with
  `-y` (force) if the chip isn't actually responding — see Appendix A.

### 4.2 — Expected dump size — record which page mode

The AT45DB041E is **DataFlash** (NOR-based, SRAM-buffered), not plain 25-series SPI NOR. Its capacity
depends on its **page-size mode**:

- **Default 264-byte page mode:** 2048 pages × 264 bytes = **540,672 bytes (~528 KB).**
- **Power-of-2 (256-byte page) mode:** 2048 pages × 256 bytes = **524,288 bytes (512 KB).**

**`minipro` `-w`/`-r` on this device entry reads/writes the 540,672-byte MAIN ARRAY ONLY.**
(T+4e validated — both Phase 4 reads produced exactly 540,672 bytes, and the Phase 5 write+verify
round-tripped 540,672 bytes byte-identically.) The chip ALSO carries a **128-byte Security Register**
(the +64 factory-programmed silicon-serial half + the +64 user-programmable half — `minipro -d`
surfaces them as `Code Memory 540,672 + 64 + 64` in its info output), but `minipro`'s `-r` and `-w` do
**NOT** round-trip the Security Register on this device entry. The Security Register requires
separate, vendor-specific commands; `minipro` does not expose them via `-w`/`-r`.

> **⚠ The 540,672 vs 540,800 distinction — DO NOT chase the 128-byte delta.** Some `PhysAccessDigiLies`
> research dumps total **540,800 bytes** = 540,672 main + 128 Security Register. **Those dumps are NOT
> minipro output.** They were captured by a different toolchain (Xgpro / vendor utility) that DOES
> round-trip the Security Register. A future operator who reads "research dump = 540,800 bytes" and
> compares it byte-by-byte to a minipro dump = 540,672 bytes will see the 128-byte delta and
> incorrectly suspect a truncation bug. There is no truncation bug — the two byte counts measure
> different scopes (main-array-only vs main-array-plus-SR). For workshop purposes, the **main array
> alone is sufficient** (user-code page, audit log, and lock-identity record all live in the main
> array — see T+4e-DUMP-VALIDATION-REPORT.md), and the 540,672-byte minipro output is the validated
> ground-truth scope.

**The operator's research dumps in 264-byte native mode** — `DUMP-VALIDATION.md` confirms
`AT45DB041E[Page264]@SOIC8.BIN` is exactly 540,672 bytes (2048 × 264) for the main-array-only case (and
540,800 bytes for the main-plus-Security-Register case) and that the handout's "524,288" claim is wrong
for these reads. **Record the exact byte count the toolchain produces** and note which page mode and
which scope it implies.

```bash
# 4.2 — [Neo via MCP] record the actual dump size
ls -l dump.bin
stat -c '%s bytes' dump.bin
# Expected on minipro: 540672 bytes (main array only — Security Register not in scope of -r).
```

> **The dump's byte size and contents are properties of the CHIP + the toolchain's read-scope, NOT just
> the programmer.** A T48-via-minipro read is valid ground truth for the workshop's "what size is the
> main-array dump" question (540,672); a 540,800-byte dump from a different toolchain is the same chip
> read with the Security Register appended.

### 4.3 — Content validation

```bash
# 4.3a — [Neo via MCP] eyeball the start of the dump
xxd dump.bin | head -40

# 4.3b — [Neo via MCP] sanity: a faithful dump is NOT uniformly 0xFF and NOT uniformly 0x00
xxd dump.bin | awk '{print $2,$3,$4,$5,$6,$7,$8,$9}' | sort -u | head
```

**Success criteria — all of:**
1. the toolchain completed the read with **no error and no USB transfer failure**;
2. `dump.bin` is **540,672 / 540,800 or 524,288 bytes** (record which);
3. the dump is **not uniformly `0xFF` and not uniformly `0x00`** — structured, varied data;
4. *(if the chip is from an intact lock)* the dump contains a plausible `0xFD` user-code page —
   per DUMP-VALIDATION.md the user-code page is **page 0, file offset `0x00000`**, first byte `0xFD`,
   first four bytes `fd 12 22 ff` for the factory-default-master case. A varied, structured dump with a
   recognisable FD page is the toolchain go signal.

> **Optional second read for confidence:** read again to `dump2.bin` and `cmp dump.bin dump2.bin`. Two
> byte-identical reads is strong evidence the in-circuit clip read is stable and repeatable.

### 4.4 — Phase 4 success criterion = the READ half of the toolchain is validated, and ground truth is captured

If 4.3's criteria 1–3 hold, the **T48-on-Kali in-circuit clip READ works**, and — critically — the
intact lock's original data is now **captured to `dump.bin` and validated.** That capture is the
precondition for Phase 5: only once a validated ground-truth read exists is it safe to attempt a write.

> **🔒 GATE:** Do not proceed to Phase 5 until `dump.bin` is captured, validated (4.3), and **backed up**
> (copy it off the working directory). Phase 5's safety constraint depends on this.

---

## PHASE 5 — The write and verify (the full-pipeline proof)

**Goal:** prove the T48-on-Kali toolchain can **write** the AT45DB041E in-circuit and that the write
**takes** — completing the read-AND-write pipeline the workshop's code-injection arc requires. The
operator has stated they will not commit to purchasing T48 units until read+write is proven easy on Kali;
this phase produces that proof.

> The research did write to this chip in-circuit — *"I clipped onto the NAND to read existing codes and
> **write my own**"*, and the working sequence in §3.3 ends *"A small write was done. Then the main
> memory was erased and a full upload attempted."* Phase 5 reproduces a **small, safe** write of that
> kind — not a firmware-level injection.

### 5.1 — 🔴 CRITICAL SAFETY CONSTRAINT — read first, write on a SEPARATE target

This constraint is non-negotiable and is built into the phase ordering:

1. **The write test MUST target a SPARE / non-critical AT45DB041E — NEVER the intact lock whose original
   codes are being recovered.** A botched write (aborted mid-page, wrong page mode, contention glitch)
   **destroys ground-truth data.** The research itself records exactly this class of loss: *"NAND flash
   returned only zeroes and refused to accept writes … I'd turned a lock into a very expensive
   paperweight."* The intact lock is a one-of-a-kind source; do not gamble it on a write test.
2. **The write test runs only AFTER Phase 4's read of the intact lock is captured and validated** (§4.4
   gate). Even on a separate chip, write only once the read half is proven and the irreplaceable data is
   safely off the bench.
3. **Ordering, explicit and mandatory:**
   **READ the intact lock (Phase 4) → VALIDATE + back up that dump (§4.4) → only then WRITE, and only to
   a separate spare AT45DB041E (Phase 5).** Never write to a chip whose data has not yet been captured.
4. Acceptable Phase-5 write targets, in order of preference: (a) a **dedicated spare AT45DB041E** on a
   sacrificial/spare lock board or breakout the operator does not need intact; (b) a chip on an
   **already-damaged board** (e.g. a previously bricked unit) where loss is acceptable. If only the one
   intact lock exists, **Phase 5 must be deferred** until a spare chip is available — Phases 1–4 still
   stand alone as a validated read pipeline. **Confirm the spare-chip target with the operator before
   Phase 5.**

### 5.2 — AT45DB041E write/erase behavior (relevant to a reliable write)

From the AT45DB041E datasheet (`pdf/AT45Datasheet.pdf`) — the DataFlash write model differs from plain
NOR and the toolchain must respect it:

- **SRAM-buffered page architecture.** The chip has **two independent SRAM data buffers** (256/264
  bytes each). A page program is a two-step path: data is first loaded into an SRAM buffer (*Buffer
  Write*), then committed to the array (*Buffer to Main Memory Page Program*). There is also a direct
  *Byte/Page Program* path. A programmer writing the AT45DB041E uses these DataFlash-specific commands —
  it is **not** the simple "erase sector, then program" sequence of 25-series NOR.
- **Page erase granularity.** Erase options are **Page (256/264 bytes)**, Block (2 KB), Sector (64 KB),
  and Chip. A reliable single-page write to one user-code page is a **page erase + page program** at the
  264-byte page boundary — small, fast, self-timed. A whole-chip erase is unnecessary for the Phase 5
  test and is riskier on a fussy in-circuit clip (longer operation = more exposure to a contact glitch).
- **Page-mode consistency.** The buffer and page sizes (256 vs 264) follow the chip's one-time page-size
  configuration. The write must use the **same page mode the chip is in** (the research dumps are
  264-byte native — §4.2). A page-mode mismatch on write is a likely corruption source — and is
  consistent with the Xgpro all-`0x00` gotcha the research recorded.
- **Self-timed, 100,000 P/E cycles, 20-year retention** — a handful of test writes is well within
  endurance; this is not an endurance concern.

### 5.3 — Write Protect (WP, pin 6) and the clip

The AT45DB041E **WP pin (pin 6)** is active-low with an internal pull-up; the chip also has
software-controlled sector protection / lockdown. For a *read* (Phase 3.2) WP can be left to its
pull-up. For a *write*:

- If the ICSP/clip leaves WP on its internal pull-up, WP is **de-asserted (high) = writes allowed** —
  which is the desired state for the write test. Confirm the clip is not pulling WP low.
- If the toolchain reports a write-protected / sector-protected error, the chip's **software sector
  protection** may be enabled — the toolchain (Xgpro or `minipro`) can issue the *Disable Sector
  Protection* command; do this deliberately and only on the **spare** chip.
- Record WP's state alongside the rest of the wiring confirmation in §3.2.

### 5.4 — The write + verify procedure

Target: the **spare** AT45DB041E (per §5.1). Pattern: a **small, known, safe** payload — a single
264-byte test page of a recognisable pattern (e.g. an incrementing byte ramp, or a test user-code page
mirroring the `0xFD`-header structure from DUMP-VALIDATION.md §2). Keep it to **one page** — small write,
short operation, minimal clip-contact exposure, mirroring the research's *"a small write was done."*

```bash
# 5.4a — [Neo via MCP] FIRST: capture the spare chip's current contents (so even the spare is recoverable).
#         Device-name + -i flag per §3.4 / §4.1.
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -r spare_before.bin
ls -l spare_before.bin                       # validate size = 540,672 (main array only), as Phase 4.2

# 5.4b — [Operator/Neo] build a small, known test payload (one 264-byte page of a recognisable pattern).
#         Keep a copy of the exact bytes written — it is the expected value for the 5.4d verify.

# 5.4c — [Neo via MCP] write the test payload to the spare chip.
#         minipro: -w writes a file; the chip is page-erased+programmed as needed by the device entry.
#         -i and the page-mode-qualified device name are standing flags per §3.4 / §4.1.
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -w testpattern.bin
# Xgpro path: load testpattern into the Xgpro buffer -> Program. Confirm the AT45DB041E[Page264]@SOIC8
#             page mode first (§4.2 / §5.2) — the research's all-0x00 gotcha was a wrong-settings write.
# T+4e empirical baseline: the live-lock Phase 5 injection write completed in 20 seconds, exit=0, with
# minipro's built-in "Verification OK" post-write. A 264-byte single-page test will complete much faster.

# 5.4d — [Neo via MCP] VERIFY: read the chip back and compare to what was written.
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -r spare_after.bin
cmp testpattern.bin spare_after.bin           # or compare the written page region byte-for-byte
xxd spare_after.bin | head -40                # eyeball the written page
```

- `minipro -w <file>` performs the write; many builds verify automatically after a write, but **5.4d's
  explicit independent read-back is mandatory** — an in-circuit write over a shared bus with an unpowered
  MSP430 on it (§3.3b) warrants confirmation that the write *took*, not just that the programmer
  *reported* success.
- If `minipro` exposes a verify flag, also run it; the read-back `cmp` is the authoritative check.

### 5.5 — Phase 5 success criterion = the WRITE half of the toolchain is validated

The full read-AND-write pipeline is proven if **all** hold:
1. Phase 4's read of the intact lock completed, validated, and was backed up (the §4.4 gate);
2. the Phase 5 write targeted a **separate spare chip**, never the intact lock (§5.1);
3. `5.4c` completed with no error and no USB transfer failure;
4. `5.4d`'s read-back **matches the written test payload** in the written page region (`cmp` clean, or
   byte-for-byte match of the page) — the write **took** and is **verifiable**.

If 1–4 hold, the **T48-on-Kali in-circuit clip read AND write pipeline works** on Kali. That is the
deliverable this plan exists to produce, and the proof the operator needs to decide on purchasing T48
units. It also gives the operator the concrete facts Phase 6 needs.

> **If the write fails or the read-back does not match:** suspect, in order — (a) page-mode mismatch
> (§4.2/§5.2 — the research's all-`0x00` Xgpro gotcha); (b) WP / sector protection (§5.3); (c) clip
> contact lost mid-write (§3.3e); (d) on the `minipro` path, a DataFlash algorithm gap — **fall back to
> Xgpro-under-Wine** (§1b.5), the path proven to write this exact chip.

---

## PHASE 6 — Workshop-decision input (the deferred CH341A-vs-T48 call)

> **This plan does NOT make the decision.** The operator deferred the CH341A-vs-T48 workshop-toolchain
> call. This section gives the honest facts to decide with, framed around the operator's **explicit T+4d
> sequencing**: (a) first prove the T48 read+write pipeline works **easily** on Kali (Phases 1–5);
> (b) then empirically **re-test whether the CH341A is sufficient** for the demo; (c) only then commit.

### 6.1 — The operator's stated sequencing — and the CH341A re-test is still pending

**The CH341A has NOT been disqualified.** It is important to be honest here:

- T+4c's CH341A read was performed on a chip that was **already cooked by desoldering** (Section 0,
  fact 1). The CH341A's brown-outs in T+4c were that *damaged chip* dragging the CH341A's weak regulator
  down — **not** a clean test of the CH341A against a healthy chip.
- Therefore **"the CH341A is insufficient" is NOT an established fact.** It is an open question. The
  CH341A out-of-circuit path has never been validated on a *live, non-cooked* chip.
- The operator's plan is explicitly to **empirically re-test the CH341A** — on an intact chip,
  out-of-circuit, with the USB-2.0-hub mitigation — *after* the T48 pipeline is proven. That CH341A
  re-validation is a **still-pending future step**, not a settled conclusion. This plan must not assert
  the CH341A is inadequate; it can only report that the CH341A's adequacy is **unproven in both
  directions** and that the re-test is the next thing that resolves it.

So the decision path is: **prove T48 (Phases 1–5) → re-test CH341A on a live chip → compare → commit.**
Phases 1–5 produce one half of that evidence; the CH341A re-test produces the other half.

### 6.2 — Side-by-side comparison (as currently known)

| Factor | CH341A + flashrom | Xgecu T48 |
|---|---|---|
| **Per-station hardware cost** | ~$7 (board) | ~$30–55 (programmer) |
| **Linux software** | flashrom 1.6.0 — already in Kali apt; trivial | **two paths** — `minipro` (build from source, Phase 1) **or** Xgpro-under-Wine (Phase 1b) |
| **Per-station setup burden** | Install flashrom (apt) + udev rule | `minipro`: deps+clone+make+install+udev. Xgpro: Wine + `setupapi.dll` + udev + Windows installer |
| **USB transport** | USB 1.1 full-speed — **fails on xHCI-only laptops** w/o a USB 2.0 hub (diag. doc F.2) | USB 2.0 high-speed — **natively xHCI-scheduled, immune** to that failure |
| **Target power supply** | Tiny weak regulator — browns out powering anything beyond a bare chip (diag. doc F.0) | Real current-capable regulated supply — drives a chip + a small board through a clip |
| **In-circuit clip read** | Not demonstrated; weak supply expected to brown out on a board's load | **Yes — the research method; validated by this plan if Phase 4 passes** |
| **In-circuit clip WRITE** | Not demonstrated | **Yes — the research wrote in-circuit; validated by this plan if Phase 5 passes** |
| **Desoldering required?** | Open — CH341A's reliable path has historically been out-of-circuit, but the live-chip re-test (§6.1) is pending | **No — in-circuit clip read+write** (Phases 3–5) |
| **Target voltage** | Often ~5 V at socket on cheap boards — chip-stress hazard (diag. doc A.5) | Software-selectable, correct 3.3 V for the AT45DB041E |
| **Demonstrated bench reliability** | 3 failures across T+4b/T+4c — **but all on a cooked chip; a clean re-test is pending** | TBD — pending this plan's Phases 4–5; the research used the T48 successfully in-circuit for read AND write |
| **Firmware dependency** | None | `minipro` path: firmware↔version can disagree (Phase 1.5). Xgpro path: firmware-matched, no mismatch |

### 6.3 — Setup-burden detail (the honest cost of the T48 path)

- The T48 path has **two sub-paths**, and neither is as trivial as `flashrom`-from-apt:
  - **`minipro`** — per laptop: five apt packages (network), a clone, `make && sudo make install`, a
    udev rule. Native, scriptable, no Wine — but carries the firmware-mismatch risk.
  - **Xgpro-under-Wine** — per laptop: Wine + 32-bit support, the Xgpro installer (from the safer
    `radiomanV` GitHub source, network), a `setupapi.dll` drop, a udev rule. More moving parts, a GUI
    rather than a CLI — but firmware-matched and proven on this exact chip.
- ToorCamp is **offline** — every laptop must be prepped *before* camp, or the toolchain shipped pre-built.
- **Mitigations if the workshop goes T48:** (a) ship a **pre-built `minipro` binary** + udev rules on a
  USB stick; (b) or a **pre-imaged Kali USB / live environment** with the chosen toolchain (and, for
  Xgpro, the Wine prefix) already installed; (c) or facilitators pre-install on a pool of loaner
  laptops. Any of these turns "set up the T48 toolchain per station" into a one-time facilitator task.

### 6.4 — The big UX point — no desoldering

The single most consequential T48 advantage: **an in-circuit clip read+write means attendees do NOT
desolder.** Desoldering is the operation that **cooked the operator's chip** (Section 0). It is also a
real skill barrier — a 90-minute room cannot teach reliable SOIC-8 desoldering and resoldering. **A T48
in-circuit clip read+write removes that whole failure surface:** attendees clip onto a chip still on its
lock board, battery removed. No desolder, no adapter pre-screening, no cooked chips.

### 6.5 — The per-station consequence the operator named

The operator has stated the concrete per-station consequence the toolchain choice drives:

- **If the CH341A re-test (§6.1) shows the CH341A is sufficient** for the demo: it is cheap enough that
  **every attendee gets their own ~$7 board** — a true one-board-per-person workshop.
- **If the T48 turns out to be the only reliable path:** T48s at ~$30–55 each are too expensive for one
  per attendee, so **attendees SHARE 2–3 programmers** across stations, and the operator **supplements
  with demonstrations** drawn from their own `PhysAccessDigiLies` research (the captured dumps, the
  worked decode, the injection result matrix).

This is a real workshop-design fork — one-per-person hands-on vs. shared-station-plus-demo — and it
rides directly on the §6.1 re-test outcome. The plan surfaces it; it does not decide it.

### 6.6 — What each choice implies for the workshop files

- **If the workshop stays CH341A:** `FACILITATOR-GUIDE.md` / `PARTICIPANT-HANDOUT.md` keep the `flashrom`
  steps, keep the out-of-circuit / chip-prep procedure, keep STAGE 4-ter troubleshooting, and
  *conditionally* add the USB 2.0 hub.
- **If the workshop switches to the T48:** the command steps must be **rewritten for `minipro`** or
  **Xgpro**; the desoldering / chip-prep / adapter-pre-screening sections can be **removed** in favour of
  an in-circuit clip procedure; the USB-2-hub line is dropped; the handout gains a **write/inject**
  procedure (the read-AND-write pipeline). This is a SMYTH (ghostwriter) file-update task.
- Either way, the workshop files currently describe an out-of-circuit method premised on the
  now-contradicted Section G inference — see the reconciliation flag in Section 8.

### 6.7 — Framing for the operator (not a decision)

- The T48 costs ~4–8× more per station and adds a per-laptop toolchain build, but it **removes
  desoldering** and is **structurally immune** to the xHCI USB failure that broke the CH341A.
- The CH341A is cheap and its software is trivial — and its adequacy is **genuinely still open**: the
  one bench test of it ran on a cooked chip, so the §6.1 live-chip re-test must happen before the CH341A
  is either chosen or ruled out.
- **The decision the operator builds toward:** prove the T48 read+write pipeline easy (Phases 1–5),
  re-test the CH341A on a live chip, then weigh ~$30–55/station-plus-build (T48, shared, demo-supplemented)
  against ~$7/station (CH341A, one-per-person) — knowing the no-desolder UX and the per-station
  consequence in §6.5. **Present these facts; do not decide.**

### 6.8 — T48-acquisition decision (T+4g — FINALIZED: (b) acquire 3 more T48s)

> **✅ DECISION FINALIZED 2026-05-20 (T+4g): OUTCOME (b) — acquire 3 more T48 units (4 stations total);
> the CH341A is DROPPED as a per-attendee programmer.** The CH341A in-circuit-through-harness re-test
> (`T+4g-CH341A-RETEST.md` §F.4) returned the **decisive negative** on the live `111111` lock board.
> The verdict rests on a clean engineering result, not a tooling/wiring fault:
>
> - **NOT a pinout problem.** The operator built the §F function-matched pin-remap harness and it is wired
>   correctly: §F.2 **H1 (continuity) PASSED** (all 8 mapped wires beep, all isolation pairs open) and
>   **H2 PASSED** (clip pin 7 = ≈3.3 V with the clip empty, pin 8 not at VCC). The VCC pin-8→pin-7 move and
>   the data-line crossover are verified — the headline pinout fix **WORKED.**
> - **NOT (strictly) a brown-out.** The CH341A **stayed enumerated on USB (`1a86:5512`) throughout** — no
>   `LIBUSB_TRANSFER_ERROR` flood, no drop-off, no xHCI re-enumeration. This is a **DETECTION failure, not a
>   power collapse.**
> - **The dominant mechanism is in-circuit shared-bus contention / loading.** The AT45DB041E sits on an SPI
>   bus shared with the lock's MCU. Batteries IN: the live MCU actively drives/holds the shared SPI lines
>   (the **red flashing LED** confirmed the MCU was awake and reacting to bus activity), defeating the
>   CH341A's weak SPI drivers. Batteries OUT: the unpowered MCU's GPIO/ESD clamps load the shared lines
>   enough that the CH341A's weak drivers can't establish clean SPI signaling. flashrom returned
>   `No EEPROM/flash device found` (auto AND `-c "AT45DB041D"`) in **both** battery states.
> - **The operator exhausted the reseat ladder** ("no matter how many times I reseated the clip with and
>   without battery") — the §F.4 GLOBAL STOP threshold (2 attempts across both battery states) is met.
>   With H1/H2 already ruling out a wiring/power fault, the exhausted-reseat-both-states evidence makes
>   contention/driver-strength the dominant explanation, not marginal clip contact.
> - **Why the T48 succeeds where the CH341A fails.** The T48 has stronger, current-capable output drivers
>   that overpower the MCU loading/contention (and a RESET hold), validated end-to-end in-circuit at T+4e.
>   The CH341A's drivers cannot. This is the same physics the T48 was acquired to beat.
>
> **Operator pre-authorization:** the operator explicitly pre-authorized this conditional ("if it doesn't
> work in-circuit, acquire more T48s — the T48 demo is stronger anyway"). The test failed in-circuit, so
> outcome **(b)** is the decided call: **acquire 3 more T48s (4 stations total).**
>
> ---
>
> *Original decision scaffolding retained below for the record.* The operator named the outstanding
> procurement decision at T+4g: **acquire 3 more T48 units** (one per
> station; ~$50–70 each) **vs. a cheaper per-attendee CH341A path** (~$7 each, but historically higher
> board-damage risk). **The operator leans T48.** The decision is gated on **T+4g Task 2** — the CH341A
> empirical-sufficiency re-test on a spare, uncooked AT45DB041E (the next bench task). This scaffold lets
> the operator finalize the moment Task 2 returns a result:
>
> **(a) IF the CH341A re-test PASSES** — the CH341A reads **and** writes the AT45DB041E reliably on the
> spare, out-of-circuit, with no brown-out and no board damage:
> → the **cheap per-attendee CH341A path is viable as a supplementary option** (true one-board-per-person,
> §6.5). Acquire CH341A boards for per-attendee use; the T48s remain the facilitator/station programmers
> for the validated in-circuit clip flow. This is the only branch in which the cheap alternative survives.
>
> **(b) IF the CH341A re-test FAILS** — unreliable read/write, brown-out on the spare, or it damages the
> board (the historical risk):  ◀◀◀ **SELECTED 2026-05-20 (T+4g): in-circuit no-detect via shared-bus
> contention; see the finalized decision block at the top of §6.8.**
> → the **cheap alternative is DROPPED**, and **T48 acquisition (3 more units, 4 stations total) is the
> justified path.** This matches the operator's lean. The per-station consequence (§6.5) then holds:
> shared programmers + operator demonstrations from the `PhysAccessDigiLies` research supplement the
> hands-on slots.
>
> **Decision inputs the operator already has in hand:** the T48 in-circuit read+write pipeline is
> validated end-to-end (T+4e); the T48 path's no-desolder UX and xHCI-immunity are settled (§6.4, §6.2);
> the only open variable is the CH341A's live-chip sufficiency (Task 2). **Drop-dead:** finalize at the
> close of the Task 2 bench session — carrying an undecided programmer choice into facilitator-kit
> assembly introduces workshop-day risk.

---

## PHASE 7 — Session / phase mapping (who does what)

Tagged so Neo can map the plan onto sessions. **[Neo/MCP]** = Neo runs it via the Kali MCP (root on
`127.0.0.1:5000`). **[Operator]** = physical hardware action only the operator can do. **[Operator
decision]** = an operator judgement call.

| Step | Action | Actor |
|---|---|---|
| **Pre-Phase-1** | Confirm which **intact** lock Phase 4 reads, and which **separate spare** chip Phase 5 writes (§5.1) | **[Operator decision]** |
| 1.2 | `apt-get install` minipro build deps — **needs network, do at home before camp** | **[Neo/MCP]** — ✅ DONE T+4d |
| 1.3 | `git clone`, `make`, `sudo make install` minipro from `master` | **[Neo/MCP]** — ✅ DONE T+4d (`minipro` 0.7.4) |
| 1.4 | Verify install; device-name string **CONFIRMED `AT45DB041E[Page264]@SOIC8`** (T+4e — bare name returns Device not found); 29,739 devices in T48 DB | **[Neo/MCP]** — ✅ DONE T+4d, string corrected T+4e |
| 1.5 | Firmware-risk note — checked in Phase 2 once T48 is plugged in | **[Neo/MCP]** + **[Operator decision]** if a firmware flash is ever considered |
| 1b.2 | Fetch Xgpro from the **safer** `github.com/radiomanV/XGecu_Software` source — **network, do at home** | **[Operator]** |
| 1b.3 | Install Wine + 32-bit; run Xgpro installer; drop `setupapi.dll`; udev rule (boseji.com reference) | **[Neo/MCP]** + **[Operator]** |
| 1b.4 | Launch Xgpro under Wine; confirm it sees the T48 + firmware; select `AT45DB041E[Page264]@SOIC8` (or the Xgpro UI's equivalent — Adesto/Atmel SPI DataFlash family, AT45DB041E, 264-byte page, SOIC8 package) | **[Operator]** |
| 1b.5 | Sequencing call — minipro-first, Xgpro-under-Wine fallback (this plan's recommendation) | **[Operator decision]** |
| 2.1 | Plug in the T48 | **[Operator]** |
| 2.1–2.2 | `lsusb` enumeration, high-speed + descriptor check (`a466:0a53`) | **[Neo/MCP]** |
| 2.3 | Install udev rules, reload, add user to `plugdev` | **[Neo/MCP]** |
| 2.3 | Unplug / re-plug the T48 after udev change | **[Operator]** |
| 2.4 | Confirm the toolchain opens the T48 — programmer model + firmware version | **[Neo/MCP]** / **[Operator]** (Xgpro) |
| 3.1–3.2 | Confirm AT45DB041E pinout vs datasheet; **confirm T48 ICSP pinout** (Xgpro diagram / silkscreen / photo) | **[Operator]** + **[Neo/Electrode]** (verify a photo) |
| 3.3 | Remove the lock's battery; wire the SOIC-8 clip to the T48 ICSP per the confirmed pinout; set/confirm 3.3 V | **[Operator]** |
| 3.3 | Clip the SOIC-8 clip onto the in-circuit AT45DB041E, pin-1 aligned | **[Operator]** |
| 3.4 | Dry probe — confirm chip detected, no write | **[Neo/MCP]** / **[Operator]** (Xgpro) |
| 4.1 | Read the intact lock's AT45DB041E to `dump.bin` | **[Neo/MCP]** / **[Operator]** (Xgpro) |
| 4.2–4.3 | Record dump size; validate contents (FD page, not all-0xFF/0x00); optional second read + `cmp` | **[Neo/MCP]** |
| 4.4 | 🔒 GATE — confirm read validated and `dump.bin` **backed up** before any write | **[Neo/MCP]** + **[Operator]** review |
| 5.1 | Confirm the Phase 5 write target is a **separate spare** chip — never the intact lock | **[Operator decision]** |
| 5.3 | Confirm WP / sector-protection state on the spare chip | **[Operator]** + **[Neo/MCP]** |
| 5.4 | Capture `spare_before.bin`; write a small known test page; read back; `cmp`-verify | **[Neo/MCP]** / **[Operator]** (Xgpro) |
| 5.5 | Confirm read-AND-write pipeline validated | **[Neo/MCP]** + **[Operator]** review |
| 6 | Review the CH341A-vs-T48 comparison; note the **pending CH341A live-chip re-test**; make or defer the call | **[Operator decision]** |

**Suggested session decomposition (Neo to confirm against HALF-LIFE.md):**
- **Session A — Phases 1, 1b & 2.** Software/USB bring-up: build `minipro`, set up Xgpro-under-Wine,
  T48 USB bring-up. Almost entirely **[Neo/MCP]** plus operator actions for Xgpro install/launch and one
  T48 re-plug. Self-contained, low physical risk. Good first session and a clean handoff point.
- **Session B — Phase 3.** Physical: ICSP-pinout confirmation, clip wiring, battery removal, clipping
  on, dry probe. Heavy **[Operator]** involvement. Gated on Session A. The ICSP-pinout confirmation
  (§3.2) is the gating unknown — resolve it (Xgpro's per-chip ICSP diagram is now available) before the
  clip is wired.
- **Session C — Phase 4.** The read of the intact lock and ground-truth validation, ending at the §4.4
  gate (validated, backed-up `dump.bin`). Gated on Session B.
- **Session D — Phases 5 & 6.** The write+verify on the **separate spare chip**, then laying the
  CH341A-vs-T48 facts (including the pending CH341A re-test) in front of the operator. Gated on
  Session C's §4.4 gate. Ends with the operator making or re-deferring the call.

Sessions C and D may merge if Phase 4 goes quickly and a spare chip is on hand. If a firmware mismatch
surfaces in Session A on the `minipro` path, the Xgpro-under-Wine toolchain (Phase 1b) is the in-plan
fallback — a branch, not a blocker.

---

## 8. Reconciliation flag — Section G premise vs. the research evidence

> **This plan does not edit `T4-DIAGNOSTIC-AND-TOOLCHAIN.md` or any workshop file. This section only
> flags what will need reconciliation once the workshop toolchain decision is made.**

- **Diagnostic doc Section G (and G.0, G.4) states the `PhysAccessDigiLies` research used an
  out-of-circuit ZIF-socket read** — it *inferred* this from "the T48 is a ZIF-socket programmer." The
  **research evidence confirms this inference is wrong:** the research notes say *"I clipped onto the
  NAND to read existing codes and write my own"*, and the research photos (`Media/20241002_205355.jpg`,
  `Media/20241204_221147.jpg`) show a SOIC-8 clip + ribbon + adapter to the T48 on the lock board. The
  research read **and wrote** the AT45DB041E **in-circuit, via a SOIC-8 clip**.
- **What this contradicts:**
  - **Section G.0** — frames out-of-circuit reading as "the methodology the source research validated."
    It did not; the research validated an **in-circuit clip read+write**.
  - **STAGE 4-bis step 4-bis-b** — its "Best — read the chip out of circuit … the original research used
    a ZIF-socket programmer" guidance rests on the same wrong inference.
  - **Section G.4 / Section D** — describe the T48's value partly as "ZIF socket enforces out-of-circuit
    reading by construction." The T48's *real* in-circuit advantage is its **current-capable supply**
    (§3.3c), which is what let the research clip-read AND clip-write a live board — not its socket.
  - **STAGE 4-ter / Section H** — the out-of-circuit-adapter failure mode (cooked chip, solder bridges,
    180° orientation) is downstream of recommending desoldering. If the workshop adopts an in-circuit T48
    clip read+write, STAGE 4-ter stops being on the attendee critical path.
  - **`FACILITATOR-GUIDE.md` / `PARTICIPANT-HANDOUT.md`** — currently carry the out-of-circuit chip-prep
    procedure and do not yet cover an in-circuit **write/inject** step.
- **The DUMP-VALIDATION.md §6 "out-of-circuit" note is also superseded.** That note (written T+4c) said
  the operator had "locked the workshop on an out-of-circuit desolder→read→resolder arc" and treated the
  in-circuit research quotes as historical. The operator's T+4d position **re-opens** the in-circuit
  path: the workshop toolchain decision is **deferred**, and this plan validates the in-circuit clip
  read+write precisely because it is back on the table.
- **The cooked-chip fact also reframes Section H.** Section H ranked "current-leaky / heat-damaged chip"
  as rank-2 (~30%); the operator's thermal observation **confirms** that hypothesis. Section H's H.1
  ranking can be updated once reconciliation happens.
- **Recommended handling:** do **not** rewrite these sections now. Once the operator makes (or
  re-defers) the Phase 6 toolchain decision, route a single reconciliation pass — diagnostic-doc Section
  G/H/STAGE-4-bis/STAGE-4-ter edits to a hardware/diagnostic specialist, and the `FACILITATOR-GUIDE.md` /
  `PARTICIPANT-HANDOUT.md` rewrites to SMYTH — so all files reflect (a) the in-circuit clip read+write
  method, (b) the confirmed cooked-chip cause, and (c) the two-toolchain reality consistently.

---

## 9. Open items the operator must resolve

> **✅ CLOSED (T+4e — supersedes T+4d): the `minipro` device-name string.** Earlier drafts hedged the
> `-p` argument and T+4d's resolution proposed the plain `AT45DB041E`. T+4e bench testing showed bare
> `AT45DB041E` returns `Device AT45DB041E not found!`. The empirically-accepted string is the
> fully-qualified **`AT45DB041E[Page264]@SOIC8`** (264-byte native page mode, SOIC-8 package). Phases
> 3.4, 4.1, 5.4 and the Phase 7 session map are updated. No longer an open item.

> **✅ CLOSED (T+4e): T48 ICSP pinout.** Phases 3.4 → 4 → 5 ran end-to-end against the T48's
> side-printed Xgecu diagram (operator bench orientation: dot upper-left, lever lower-right; standard
> 8-pin-DIP "SOIC-8 clip pin N → ZIF pin N at the marker-end of the socket"). Empirical confirmation:
> byte-identical repeat reads + clean write+verify + functional keypad unlock. No longer an open item.

> **✅ CLOSED (T+4e): firmware-mismatch warning.** Validated NON-BLOCKING across the full Phase 2–5
> workflow. §1.5 updated. Standing recommendation: do NOT flash T48 firmware. No longer an open item.

> **✅ CLOSED (T+4e): the `-i` flag is the standing fix for intermittent `Chip ID 0x0000` returns.**
> §3.4 documents the policy. No longer an open item.

1. **Which lock/chip Phase 4 reads** — must be a **second, intact lock** (chip never desoldered, never
   CH341A-powered). The CH341A-cooked chip's data is unrecoverable. Confirm before Phase 4.
2. **Which SEPARATE spare chip Phase 5 writes** — the write test MUST NOT touch the intact lock (§5.1). A
   dedicated spare AT45DB041E or an already-damaged board is required. **If no spare chip exists, Phase 5
   is deferred** and Phases 1–4 stand as a validated read-only pipeline. Confirm before Phase 5.
3. **T48 ICSP pinout** (§3.2) — **CLOSED at T+4e — validated empirically.** The T48's side-printed
   Xgecu diagram, read in the operator's bench orientation (dot upper-left, lever lower-right), gives
   the standard 8-pin DIP map "SOIC-8 clip pin N → ZIF pin N at the marker-end of the socket". Phases
   3.4 → 4 → 5 all passed against this map. Retained as item 3 only as a reminder that a *second*
   T48 (e.g. a freshly-procured workshop unit on different firmware) must be cross-checked against
   the same side-printed diagram before its first use — the map should be identical across T48s on
   the same firmware family, but verify per unit.
4. **Network for Phase 1.2 and Phase 1b.2.** Both the `minipro` build deps and the Xgpro download need
   network — do them at home before ToorCamp (the camp is offline).
5. **A known-good SOIC-8 test clip** (8-pin, 1.27 mm pitch) that fits the AT45DB041E 8-SOIC package and
   reaches the T48 ICSP header (likely via a small adapter, as the research photos show).
6. **Xgpro provenance** — Xgpro is third-party-redistributed vendor software even from the safer
   `radiomanV` GitHub source. Fetch only from there (not the .cn HTTP mirrors), and record the release
   tag + file hash. The operator should treat using Xgpro as a deliberate, eyes-open choice.
7. **The pending CH341A live-chip re-test** (§6.1) — the workshop decision is not just "is the T48 good";
   it is also "is the cheap CH341A *actually* insufficient." The CH341A has only ever been tested against
   a cooked chip. A clean re-test on a live chip is a still-pending step the operator owns.

---

## Appendix — confidence and sources

| Claim | Confidence | Source |
|---|---|---|
| David Griffith's `gitlab.com/DavidGriffith/minipro` is the actively-maintained fork | HIGH | Diagnostic doc A.6; minipro GitLab repo |
| `minipro` 0.7.4 builds & installs cleanly on the operator's Kali — binary at `/usr/local/bin/minipro` | **CONFIRMED (T+4d)** | T+4d bench build via `kali` MCP from `master` HEAD commit `fd6b56afcfee1bbcef78e465b7c512c1cd1999d3` (2026-03-09) |
| T48 / TL866-3G is supported in current `minipro` `master`; `master` actively tracks recent T48 firmware | **CONFIRMED (T+4d)** | minipro README supported-hardware line; `master` HEAD commit subject "Updated T48 latest firmware (01.1.38 / 0x126)"; `minipro --version` reports T48 DB = 29,739 devices |
| The research toolchain was **Xgpro**, not `minipro` | HIGH | `PhysAccessDigiLies` notes "Tooling Note: Xgpro Software"; `uploads/plan` ("wrong settings in XGPro"); DUMP-VALIDATION.md §6 |
| Safer Xgpro source = `github.com/radiomanV/XGecu_Software`; Linux setup ref = `boseji.com` TL866II+/Manjaro guide | HIGH | `PhysAccessDigiLies` notes verbatim; DUMP-VALIDATION.md §6 verbatim quotes |
| Xgpro-under-Wine needs custom udev rules + a `setupapi.dll` in the install dir | HIGH | `PhysAccessDigiLies` notes "Tooling Note: Xgpro Software" verbatim |
| T48 USB VID:PID = `a466:0a53` | MODERATE–HIGH | minipro `udev` rules file lists `a466:0a53` for TL866II+/T48/T56; confirm against actual `lsusb` at Phase 2.1 |
| minipro build deps = `build-essential pkg-config git libusb-1.0-0-dev zlib1g-dev` | HIGH | minipro README Debian/Ubuntu dependency line; `pkg-config`+`libusb-1.0-0-dev` confirmed missing on the operator's Kali |
| minipro cannot update T48 firmware; only Xgpro can; firmware bundled per Xgpro version | HIGH | Multiple consistent T48/Xgpro sources; firmware-mismatch is a documented real risk |
| AT45DB041E 8-SOIC pinout (VCC pin 7, GND pin 4) | HIGH | `pdf/AT45Datasheet.pdf` §1; cross-checked with diagnostic doc H.2 |
| The research read+wrote the AT45DB041E **in-circuit, via a SOIC-8 clip** | HIGH | `PhysAccessDigiLies` notes ("I clipped onto the NAND to read existing codes and write my own"); research photos `Media/20241002_205355.jpg`, `Media/20241204_221147.jpg` |
| The clip met the T48 via a small adapter PCB + ribbon (likely ICSP path) | MODERATE–HIGH | research photos `Media/20241002_205355.jpg`, `Media/20241204_221147.jpg` |
| Exact T48 ICSP header pin map for an 8-pin SPI DataFlash part | **RESOLVED (T+4e — see row below)** | Superseded by the T+4e empirical-validation row immediately below |
| The reliable-write setup = only the programmer on USB, board still, read-before-write | HIGH | `PhysAccessDigiLies` notes verbatim ("Only the programmer was plugged into USB / … A successful memory read occurred first / A small write was done") |
| T48 succeeds in-circuit because of its current-capable supply (not its socket) | HIGH | First-principles power analysis; consistent with diagnostic doc F.0/G.4; research's in-circuit success is the evidence |
| AT45DB041E write/erase = SRAM-buffered pages, Page/Block/Sector/Chip erase, 100k P/E cycles | HIGH | `pdf/AT45Datasheet.pdf` Features + Description (8783L–DFLASH) |
| `minipro -p <name> -r/-w file` are the read/write invocations | HIGH | Standard minipro CLI |
| The AT45DB041E device-name string the `minipro` CLI accepts on the bench is **`AT45DB041E[Page264]@SOIC8`**; the bare `AT45DB041E` is in the DB but the CLI returns "not found" for it | **CONFIRMED (T+4e — supersedes T+4d)** | T+4e bench: `sudo minipro -p 'AT45DB041E' ...` → `Device AT45DB041E not found!`; `sudo minipro -p 'AT45DB041E[Page264]@SOIC8' ...` → device recognised, dry probe + read + write all `exit=0` |
| The T48 ICSP pinout is the side-printed Xgecu diagram on the T48's case — standard 8-pin DIP convention "SOIC-8 clip pin N → ZIF pin N at the marker-end of the socket" | **CONFIRMED (T+4e — supersedes earlier MODERATE rating)** | T+4e bench: operator orientation dot upper-left, lever lower-right; Phases 3.4 → 4 → 5 all passed end-to-end against the map (repeat reads byte-identical, write+verify clean, keypad unlock functional) |
| Firmware mismatch (T48 `00.1.34` / `0x122` vs `minipro` expects `01.1.38` / `0x126`) is NON-BLOCKING — warning printed, every operation exits 0 | **CONFIRMED (T+4e)** | T+4e bench: `-k`, `-L`, `-d`, dry probe, full read (×2), full write+verify all completed `exit=0` with the warning printed |
| The `-i` flag (skip-ID-check) is the standing fix for the intermittent `Chip ID 0x0000` return on the T48 firmware `00.1.34` + this AT45DB041E sample | **CONFIRMED (T+4e)** | T+4e bench: 1st dry-probe attempt returned `0x0000`; re-seat + 2nd attempt returned correct `0x1F24`; thereafter `-i` used on all read/write invocations (equivalent of Xgpro's "Match Chip ID" unchecked) |
| `minipro -w`/`-r` on `AT45DB041E[Page264]@SOIC8` round-trips the **540,672-byte main array only** — the 128-byte Security Register surfaces in `-d` info but is NOT in scope of `-w`/`-r` | **CONFIRMED (T+4e)** | T+4e bench: every Phase 4 read and every Phase 5 write completed at exactly 540,672 bytes; research dumps totalling 540,800 bytes come from a different toolchain that round-trips the Security Register |
| `minipro -l` is interactive (DB-selection prompt) when no programmer is attached — hangs under the MCP | **CONFIRMED (T+4d)** | T+4d bench: bare `minipro -l` blocks on a `1) TL866A/CS … 4) Abort` stdin menu; mitigated in §1.4 by grepping `infoic.xml` / piping `echo 2` |
| `make install` STAGES the udev rules in the source tree but does NOT install them to the system | **CONFIRMED (T+4d)** | T+4d bench: Makefile udev step is conditional on an empty rules-dir variable; rules left at `~/minipro/udev/` — Phase 2.3 installs them |
| AT45DB041E dump = 540,672 B (264-byte page) / 540,800 B (+Security Register) / 524,288 B (256-byte page) | HIGH | DataFlash page-mode arithmetic; DUMP-VALIDATION.md §1 (research dumps are 264-byte native) |
| The CH341A's T+4c failure was on an already-cooked chip — its adequacy is unproven, not disproven | HIGH | Section 0 fact 1; diagnostic doc Section H; the live-chip re-test is a stated pending step |

---

## Appendix A — Alternative Clip-Rig Diagnostic (the second-board all-zero-dump case)

> **Status:** authored by Electrode at T+4f for **execution at T+4g** by the operator. Pre-staged
> per the operator's documented preference for hardware-iteration blocks: copy/paste sequence + manual
> vary list + success signal + escalate threshold provided upfront, so the bench iteration does not
> round-trip every attempt.

### A.0 — Why this appendix exists

At T+4e, after the primary first-board pipeline (SOIC-8 clip via ZIF socket → T48 → `minipro` on Kali)
had validated end-to-end, the operator briefly switched to a **second board** to test an alternative
clip-on rig: **individual long clips on separate breakout leads**, instead of the integrated SOIC-8 ZIF
clip. The motivation: this is the planned workshop alternative-clip method (cheaper, more granular, and
useful when a SOIC-8 clip can't reach a board geometry), so it needs to be proven before ToorCamp.

The T+4e attempt with the individual-lead rig produced this exact, distinctive failure mode:

- `sudo minipro -y -p 'AT45DB041E[Page264]@SOIC8' -r dump.bin` (`-y` to force past the ID-check)
  reported `Reading Code... 1.45 Sec OK` and `Reading Data... 0.4 ms OK`, exit `0`.
- **The 540,672-byte dump was uniformly `0x00` across every single byte.** MD5
  `911ebc6e12bbf70c90f1d36b346f07a7`.
- Without `-y`, the same rig returned `Invalid Chip ID: expected 0x1F24, got 0x0000` and refused to
  read.

This exactly matches the failure mode the operator's own original research documented (`uploads/plan`
line 76): *"when checked using a T48, all data was listed as 00"*. **The chip was not actually
responding on the SPI bus.** The `-y` flag bypassed the chip-ID check, so `minipro` proceeded into the
read sequence and dutifully clocked out 540,672 bytes of whatever the bus was presenting — which, with
the chip not responding, was the null-byte / pulled-low / floating-bus default. The T48 reported a
"successful" read because at its level it was clocking and capturing as instructed; the data was
garbage because nothing was driving MISO.

Diagnosis was deferred to T+4g. This appendix is the diagnostic procedure pre-staged for that bench
session.

### A.1 — Orientation verification (before any electrical check)

The individual-lead rig has **eight separate jumpers** and the operator must verify that **each one**
lands on the correct chip pad and the correct T48 ZIF socket pin. Standard 8-SOIC pinout from §3.1
(reproduced here so the bench operator does not have to scroll up):

| Chip pin | Signal | T48 ZIF pin (per the side-printed map, §3.2) |
|---|---|---|
| 1 (next to dot) | SI (MOSI — into chip) | ZIF pin 1 at marker-end |
| 2 | SCK (clock) | ZIF pin 2 at marker-end |
| 3 | RESET (active-low, internal pull-up) | ZIF pin 3 at marker-end |
| 4 | GND | ZIF pin 4 at marker-end |
| 5 | CS (active-low) | ZIF pin 5 at marker-end |
| 6 | WP (active-low, internal pull-up) | ZIF pin 6 at marker-end |
| 7 | VCC (3.3 V) | ZIF pin 7 at marker-end |
| 8 | SO (MISO — out of chip) | ZIF pin 8 at marker-end |

**Verification steps — visual only, no power applied:**

1. **Find the chip's pin-1 dot/notch** with a magnifier in good light. Take a close-up photo (see A.3).
   Pin 1 is on one *short* side of the SOIC-8; numbering then runs *counter-clockwise viewed from
   above*. Pin 1 is to the LEFT of the dot when the dot is at the top of the chip.
2. **Confirm each individual lead's chip-end clip is on the correct pin.** Trace each lead from clip
   to its other end. Use a label or marker on each lead.
3. **Confirm each individual lead's T48-end is in the correct ZIF socket position.** The ZIF socket's
   marker end is the same end as the silk-printed pin-1 indicator on the T48's case.
4. **Critical failure modes from a single mis-orientation:**
   - **VCC and GND swapped** (clip pin 7 ↔ pin 4): reverse-polarity damage to the chip on power-on.
     This is the worst case — *flag this if found and STOP before applying power*. T+4e's primary
     rig avoided this risk by using the SOIC-8 clip's fixed-pin-position ribbon.
   - **MISO grounded** (clip pin 8 wired to GND): the all-`0x00` symptom we observed at T+4e.
     **Rank-1 candidate** for the observed failure — see A.5.
   - **CS pulled high** (clip pin 5 disconnected, relying on internal pull-up that may not exist
     externally): the chip never asserts → MISO floats → all-`0x00` or all-`0xFF` (bus state
     dependent). **Rank-2 candidate.**
   - **SCK or SI open** (clip pin 2 or 1 disconnected): the chip receives no command → never drives
     MISO → all-`0x00` symptom. **Rank-3 candidate.**
   - **Two leads on adjacent pins shorted by clip jaw seating**: depends on which pins; can short
     VCC↔SI (chip stress), CS↔WP (write-block during read attempts — but read should still work),
     SCK↔RESET (reset asserted on each clock — chip refuses to respond). Multimeter A.2 catches this.
   - **Single jaw not making contact**: same as the corresponding "open" case above.

> **If ANY orientation check fails the visual pass, STOP and re-route the wire BEFORE applying power.**
> Especially the VCC/GND case — a reverse-polarity event on the AT45DB041E destroys the chip
> instantly. The chip is a 3.3 V part; backwards-applied 3.3 V is sufficient to forward-bias the
> internal ESD diodes into latch-up.

### A.2 — Multimeter checklist (chip un-powered, leads connected, T48 unplugged or off)

This is a **continuity / static-resistance** check, not a live-signal check. The goal: prove that
every lead connects what it should connect, and nothing more.

**Tools:** a multimeter on **continuity mode** (audible buzzer) for the binary checks, and on **20 kΩ
ohm-meter mode** for the impedance-discrimination checks.

**Per-lead continuity (all chip pads accessible — clip clamped, but T48 unplugged):**

For each of the 8 leads, probe **(chip-side clip jaw N) ↔ (T48 ZIF pin N at the marker-end)**:

| Reading | Healthy | Indicates a fault |
|---|---|---|
| Continuity buzz (< 1 Ω) | ✓ lead is intact end-to-end | — |
| Open (no buzz, infinite Ω) | — | **OPEN LEAD** — the jumper is broken, the clip jaw is not seating, or the T48-end is not seated in the ZIF |
| Reads 50–500 Ω | — | **Partial open / oxidised contact** — jaw barely making contact, or a corroded crimp |
| Reads continuity to a DIFFERENT pin number | — | **MIS-WIRED** — re-route this lead before continuing |

**Per-lead cross-isolation (pairs):**

Probe pairs of T48-ZIF pins against each other to check for shorts:

| Pair to probe | Healthy reading | Failure mode |
|---|---|---|
| ZIF pin 4 (GND) ↔ ZIF pin 7 (VCC) | Open (>20 kΩ — the chip's internal impedance) | **Buzz = short** → DO NOT POWER UP; lead-to-lead short, often a flex bend that's stripped jacket. The T+4e primary rig won't help diagnose this; you must inspect lead routing. |
| ZIF pin 4 (GND) ↔ ZIF pin 8 (SO/MISO) | Open (>10 kΩ) | **Buzz or low Ω = MISO grounded** → this is the **RANK-1 candidate root cause** for the T+4e all-`0x00` symptom. Re-route the MISO lead; it is connecting to GND somewhere along its path. |
| ZIF pin 4 (GND) ↔ ZIF pin 5 (CS) | Open (>10 kΩ) | **Buzz = CS shorted to GND** — chip would be *permanently selected*, which actually helps reads, but combined with another fault is a confounder. |
| ZIF pin 1 (SI) ↔ ZIF pin 2 (SCK) | Open (>10 kΩ) | **Buzz = data and clock shorted** — chip cannot interpret a command — reads garbage. |
| ZIF pin 4 (GND) ↔ ZIF pin 2 (SCK) | Open (>10 kΩ) | **Buzz = SCK grounded** — chip never clocks — all-`0x00` or all-`0xFF`. **RANK-3 candidate.** |
| ZIF pin 4 (GND) ↔ ZIF pin 1 (SI) | Open (>10 kΩ) | **Buzz = SI grounded** — chip receives nothing but `0x00` commands — all-`0x00` symptom. **RANK-3 candidate** (tie with SCK-grounded). |

**Capture each reading.** Photograph the multimeter display or write the value into a table. A
remote-diagnostic pass at T+4g+ will be straightforward if these readings exist; impossible without
them.

> **Why ohm-meter and not just continuity:** the chip's internal pull-ups on RESET (pin 3) and WP
> (pin 6) read in the **20–100 kΩ** range to VCC. A continuity buzzer will not buzz on those because
> they are above the buzzer's threshold; an ohm-meter will resolve them. Reading 20–100 kΩ on
> RESET↔VCC or WP↔VCC with the chip *un-powered* is the chip's internal pull-up — **healthy**. Open
> (infinite) on those pairs with the chip un-powered is also fine (it just means you can't see the
> pull-up without the chip being powered). A **dead short** to GND on RESET or WP is the fault.

### A.3 — Bench photo specs (so T+4g+ can be diagnosed remotely if needed)

The operator should capture **at minimum the following four photos**, then attach them to the T+4g
bench note:

1. **Overhead-of-full-rig.** Camera straight down, T48 + ZIF socket + all 8 individual leads + chip
   under clip in frame. Ruler in the frame for scale. **Focus must be sharp enough to read the silk
   on the T48 and the lead labels.**
2. **Close-up of the clip on the chip.** Macro shot, top-down. Must show the chip's pin-1 dot/notch,
   the clip's pin-1 mark, and at least one full edge of the chip body so all 8 pins are visible.
3. **Close-up of the T48 ZIF socket area.** Camera at a slight angle so each lead's insertion point
   in the ZIF socket is visible. Ruler or labels next to each lead identifying which signal it is.
4. **Close-up of one mid-lead crimp / connector**, repeated for any lead that fails A.2's continuity
   check (so the failure-mode source is visible).

Optional but useful:

- 5. **Side-on of the chip and clip** — shows whether each jaw is seating on the chip pad or perched
  on the package shoulder.
- 6. **Photo of the multimeter readings table** if it's hand-written, OR a screenshot of a digital
  notes file if typed.

> **File-naming convention:** `T+4g-second-board-{view}.jpg` (e.g.
> `T+4g-second-board-overhead.jpg`, `T+4g-second-board-clip-closeup.jpg`). Place in
> `~/Desktop/toorcamp-2026-dumps/T+4g-second-board-diagnostic/`.

### A.4 — Iteration block (copy/paste-able, attempt sequence with escalate threshold)

> Use this block at the bench. Run the first command, observe the result, follow the branch. Do not
> round-trip with Electrode per attempt — the branches below cover the expected outcomes.

```bash
# A.4.0 — confirm T48 is enumerated (sanity check, not a fault discriminator)
lsusb | grep -i 'a466:0a53'                          # expect one matching line
sudo minipro -k                                       # expect 't48: T48'

# A.4.1 — dry probe WITHOUT -i, using -D (--read_id) to read the chip ID off the SPI bus.
#         This is the diagnostic gold standard: -D reads the chip ID over the bus and does nothing
#         else, so if the chip is genuinely responding the probe returns Chip ID 0x1F24. If the chip
#         is not on the bus, it returns 0x0000 (or "Invalid Chip ID").
#         ⚠ -D (uppercase) is --read_id, the ONLINE bus read. Do NOT use -d (lowercase) here: -d is
#         --get_info, an OFFLINE DB lookup that never touches the bus and would "succeed" with no
#         chip clipped at all — exactly hiding the failure this probe exists to catch. (T+4g: the
#         2nd board returned the correct chip ID 0x1F24 with -D.)
sudo minipro -p 'AT45DB041E[Page264]@SOIC8' -D
# Branch on the output:
#   - "Chip ID 0x1F24 OK" + chip parameters printed:
#       → THE INDIVIDUAL-LEAD RIG IS WORKING. Proceed with the standard Phase 4 read using -i.
#       → Stop the diagnostic here.
#   - "Invalid Chip ID: expected 0x1F24, got 0x0000":
#       → Chip not on the bus. Go to A.4.2 (re-seat) and then A.4.3 (multimeter).
#   - "Invalid Chip ID: expected 0x1F24, got 0x{anything else}":
#       → Partial response — possible MISO partial-short, marginal contact. Treat like 0x0000;
#         the chip is misbehaving on the bus.
#   - USB transfer error / programmer disconnect:
#       → A short on VCC/GND is browning out the T48's target supply. STOP, disconnect, re-do A.1
#         and A.2 visually + with the multimeter before re-attempting. This is a chip-stress event.

# A.4.2 — re-seat the individual-lead clips. Power-off, re-clamp each chip-pad jaw, re-seat each
#         T48-ZIF-end pin. Repeat A.4.1.

# A.4.3 — multimeter sweep per A.2. Capture each reading. Find the failure (open / short / mis-wire).

# A.4.4 — after A.4.3 has identified a fault and the fault is repaired, repeat A.4.1.

# A.4.5 — if A.4.1 still fails after A.4.2 and A.4.3 have been done THREE times (clip re-seated 3x,
#         multimeter sweep 3x), declare the individual-lead-rig non-functional and route to A.6.
#         Do not continue iterating past 3 full cycles — the rig is structurally bad.
```

**Explicit escalate threshold:** **3 full A.4.1 → A.4.2 → A.4.3 cycles.** If the rig has been
re-seated 3× and the multimeter sweep has been done 3× and the dry probe still returns `0x0000`, the
rig is structurally bad — go to A.6 (workshop fallback decision).

> **Do NOT use `-y` on the diagnostic.** The whole point of A.4.1 is to LET the ID check fire so you
> can see whether the chip is actually on the bus. `-y` bypasses the ID check and proceeds into the
> read sequence — which is what produced the all-zero dump at T+4e. `-y` is a *force* flag for use
> when you already know the chip is healthy but the ID-check exchange is glitching (the §1.5 firmware
> case). On a *diagnostic* run, `-y` hides the symptom you're trying to find. **Use `-i` and `-y`
> only AFTER A.4.1 has returned `0x1F24` at least once.**

### A.5 — Likely root causes ranked (by 'all-zero dump' signature match)

Given the T+4e symptom (`-y` → "Reading Code/Data OK" + 540,672 bytes uniformly `0x00`), the
diagnostic prior is:

| Rank | Hypothesis | A.2 finding that confirms | Why this rank |
|---|---|---|---|
| 1 | **MISO (chip pin 8 / SO) wire is grounded somewhere along its path** | Continuity buzz (or <100 Ω) between ZIF pin 8 and ZIF pin 4 (GND) | The all-`0x00` symptom is exactly the MISO-tied-to-GND signature. The bus clocks, the read sequencer runs, but MISO is held low — every byte is `0x00`. Most common physical cause: a long jumper's jacket nicked against a GND clip jaw, or a breakout-board solder bridge between pin-8 and pin-4 lands. |
| 2 | **MISO (chip pin 8 / SO) wire is completely open** (no contact at chip jaw OR no insertion at ZIF) | Open (infinite Ω) between ZIF pin 8 and the chip pin 8 pad probed directly | An open MISO floats the bus. On many T48-firmware combos and short stub lengths, a floating MISO reads low (capacitive pull-down by stray board capacitance + the MOSI/SCK lines toggling). All-`0x00` is the most common float-read result, though all-`0xFF` and patterns are also possible. |
| 3 | **SCK or SI is grounded** (chip never receives a command — its command interpreter never starts — MISO defaults to idle low) | Continuity between ZIF pin 2 or 1 and ZIF pin 4 | The chip simply doesn't begin a read sequence — MISO sits at idle. Same all-`0x00` symptom as ranks 1–2 but with a different repair path. |
| 4 | **CS (chip pin 5) is open / un-seated** — chip is never asserted | Open between ZIF pin 5 and chip pin 5 | Chip remains de-selected, never drives MISO, output is hi-Z; result is all-`0x00` or all-`0xFF` depending on bus pull state. |
| 5 | **VCC under-supplied** — the chip is powered but at insufficient voltage for SPI to work | A.2 cannot detect this without a live probe. Symptom: chip warm but read fails | The individual-lead rig may have higher VCC-line resistance than the SOIC-8 clip's integrated ribbon. The T48's 3.3 V target supply might be drooping at the chip end. Less likely than ranks 1–3 but worth checking under load (live probe at chip pin 7 — needs a slim probe). |
| 6 | **Multiple simultaneous faults** — common on hand-built individual-lead rigs | A.2 finds two or more anomalies | If A.2 turns up multiple findings, repair them all and retry. Don't try to repair only the worst one and assume the rest is fine. |
| 7 | **The second-board chip is actually damaged** (e.g. cooked by a prior reverse-polarity event on this rig, or shipped DOA) | All A.2 readings clean, but A.4.1 still fails after 3 iterations | Last-resort hypothesis. If the first-board chip is known healthy via SOIC-8-clip on the same T48, swap the chips between the boards and re-test on this second-board's rig — if the swap moves the failure with the chip, the chip is the fault; if the swap leaves the failure on the second board, the rig is the fault. |

### A.6 — Workshop fallback decision criterion

> **✅ RESOLVED (2026-05-20, T+4g) — supersedes the binary criterion below.** At the T+4g bench session
> the 2nd-board individual-lead rig was re-probed with the **corrected `-D` dry probe** (the earlier
> all-`0x00` T+4e result was a contact/flag artifact compounded by the `-d` vs `-D` defect, now fixed —
> see §A.4.1). With `-D` the 2nd board returned the **correct chip ID `0x1F24`**. **The individual-lead
> rig is therefore TECHNICALLY VIABLE.**
>
> **However — operator workshop-design decision (T+4g):** technical viability does **not** make the
> individual-lead method a station method. The operator has decided:
>
> - The **SOIC-8 clip-on method is the DEFAULT, sole per-station method** — it is much easier and faster,
>   and it is the method validated end-to-end at T+4e.
> - The **individual-lead-clip method is relegated to AD-HOC, per-attendee-need ONLY.** It is **NOT** to
>   be written about, featured, or addressed as a standard procedure in any workshop literature
>   (FACILITATOR-GUIDE.md, PARTICIPANT-HANDOUT.md). A facilitator may reach for it on the spot if a
>   specific board geometry defeats the SOIC-8 clip, but it is not part of the documented attendee flow.
>
> The binary A.6/B-criterion below (which contemplated *adding* a working individual-lead rig to the
> FACILITATOR-GUIDE as an attendee procedure) is **superseded by this decision** — even though the rig
> passed the "viable" branch, the workshop docs stay SOIC-8-only. The criterion is retained for
> historical context only.

> The workshop's plan **originally** called for **two clip methods per station**: (a) the validated
> SOIC-8 clip via ZIF (Phase 3–5, proven) and (b) the individual-long-clip-on-breakout-leads rig (the
> alternative). The fallback decision criterion below was the explicit bench rule before the T+4g
> workshop-design decision above closed it in favour of SOIC-8-only-in-literature.

**Decision rule (binary):**

- **IF** A.4 successfully returns `Chip ID 0x1F24 OK` (the §A.4.1 healthy branch) **within 3
  iterations of the escalate threshold**, **AND** a full Phase 4 read of the second-board chip
  produces a 540,672-byte dump consistent with §4.3 criteria 1–3 (no error, correct size, varied
  non-uniform data),
  → **the individual-lead-clip rig is workshop-viable.** Document the working configuration; add it
  to the FACILITATOR-GUIDE alternative-clip-method procedure; replicate the rig 3 times for the 3
  co-facilitator stations.

- **ELSE** (any failure at the escalate threshold, OR a read that returns all-`0x00` / all-`0xFF` /
  the chip-cooked symptom),
  → **the individual-lead-clip rig CANNOT be salvaged in time for the workshop.** The workshop falls
  back to **SOIC-8-only** as the per-station clip method. The alternative-clip-method is REMOVED from
  the FACILITATOR-GUIDE attendee flow and noted only as "advanced-discussion" material — the
  SOIC-8-via-ZIF method we validated at T+4e is the per-attendee path. Update PARTICIPANT-HANDOUT.md
  and FACILITATOR-GUIDE.md accordingly (route this update to SMYTH).

**Drop-dead time:** the operator should make this decision **at the close of T+4g**. Carrying an
unresolved second-board failure into procurement decisions or into the FACILITATOR-GUIDE write-up
introduces workshop-day risk. SOIC-8-only is a known-good fallback; do not over-invest in salvaging
the alternative-clip method if A.4 doesn't resolve it in three iterations.

### A.7 — Open-issue trail for T+4g

> **✅ T+4g OUTCOME (2026-05-20).** The second-board case is **resolved**: the all-`0x00` T+4e symptom
> was a contact/flag artifact compounded by the `-d`-vs-`-D` dry-probe defect (§A.4.1). Re-probed with
> the corrected **`-D`** (`--read_id`) dry probe, the 2nd board returned the correct chip ID `0x1F24` —
> the chip IS on the bus and the individual-lead rig IS electrically functional. **A.5 hypotheses ranks
> 1–7 are all moot** for this board: none was a true fault; the apparent failure was the diagnostic flag
> (`-d` offline DB lookup) plus marginal contact, not a wiring or chip fault. **Workshop disposition
> (operator decision, T+4g):** the rig's viability does not promote it to a station method — SOIC-8 clip-on
> is the default sole per-station method, individual-lead is ad-hoc-per-attendee-need only and is NOT in
> workshop literature (see §A.6). No further T+4h diagnostic action required on the second board.

If a future bench session re-opens the second-board case, record the residual diagnosis state here:

- Which of the 7 A.5 hypotheses were positively confirmed or ruled out by A.2 measurements
- Which iterations of A.4.1 / A.4.2 / A.4.3 were run
- Whether the chip-swap test (A.5 rank 7) was attempted, and the result
- Whether the chip on the second board has any visible damage on close-up photo inspection (lifted
  pad, solder bridge between adjacent pads, scorched marking)
- The final fallback decision (A.6 binary)

---

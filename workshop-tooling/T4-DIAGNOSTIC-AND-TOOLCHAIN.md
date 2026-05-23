# T+4 — Diagnostic & Toolchain Assessment
## ToorCamp 2026 · "Dead Bytes Tell No Lies" · Hardware-Validation Session

**Author:** Breeder (Systems Engineer) · The Manhattan Project
**Date:** 2026-05-15
**Target:** Adesto AT45DB041E (4 Mbit SPI DataFlash, JEDEC `1F 24 00`)
**Programmer:** CH341A mini programmer (USB `1a86:5512`, bcdDevice 3.04)
**Host:** Kali Linux, kernel 6.19.14+kali-amd64, x86_64

> **One-line bottom line:** Keep the $7 CH341A board. Drop `ch341prog`. Use **flashrom** — already installed (`v1.6.0-3`) — with `-p ch341a_spi` and chip `AT45DB041D`. `ch341prog` *cannot* read the AT45DB041E; the reason is in its source, not the hardware.
>
> **⚠ Updated after the T+4b bench:** flashrom is confirmed the right software, but a *second* problem surfaced — the CH341A floods `LIBUSB_TRANSFER_ERROR` and keeps dropping off the USB bus.
>
> **⚠ Updated again — operator reported a new fact NOT in the first diagnosis:** the chip is being read **in-circuit** — still soldered to the lock's PCB, with the lock's **own battery pack energizing the board** (operator measured 3.3 V on a flash pin). So the chip's VCC rail has **two power sources at once** (the lock battery *and* the CH341A's clip), and the lock's MSP430 microcontroller is **live and contending on the shared SPI bus**. This is now the **leading suspect** for the bench failure — it is a **zero-cost** thing to rule out and must be checked **before** buying any USB hub. The USB-2-hub / xHCI hypothesis is now the *second* candidate. See revised Sections F, G, and STAGE 4-bis.
>
> **⚠ Updated at T+4c — a THIRD, distinct failure surfaced.** The operator desoldered the chip and mounted it on a SOIC-8-to-DIP adapter (doing exactly what Section G.0 recommends — read out of circuit). New symptom: `Couldn't open device 1a86:5512` / `Programmer initialization failed`, the CH341A **dropped fully off the USB bus** (`lsusb` shows no `1a86` device), and `dmesg` shows an xHCI **enumeration loop** (`error -71`, `unable to enumerate USB device`) — but with **no `LIBUSB_TRANSFER_ERROR` flood**. Diagnosis: a **VCC↔GND short** — most likely a solder bridge on the adapter, possibly a chip cooked by desoldering heat/ESD — brown-outs the CH341A, the same end-state as the in-circuit case but from a single shorted chip+adapter. This is documented as **STAGE 4-ter** (Section B) and **Section H** (root cause + the operator's multimeter procedure). It is intrinsic to out-of-circuit prep and **doubles as workshop troubleshooting** — attendees who mount their own chips will hit solder bridges.

> **⚠ T+4c dispatch 2 — bench facts changed the diagnosis; the cause list is RE-RANKED.** Three new facts came back from the bench. (1) **The CH341A board is undamaged** — removing the adapter so the ZIF socket is *empty* then re-plugging recovered it cleanly (`lsusb` shows `1a86:5512`, `dmesg` shows a clean enumeration with no `error -71`, `flashrom` with the socket empty returns a benign `No EEPROM/flash device found`). Re-plugging *with the shorted adapter still seated* did **not** clear the loop — only emptying the socket did. (2) **The static VCC↔GND continuity test on the bare adapter read OPEN** — no beep, no hard solder bridge. (3) The brown-out is still real and reproducible — it occurs *only* with the adapter seated in the correct powered 25-series rows, and clears when the adapter is removed. **The critical correction: a static "open" VCC↔GND meter reading does NOT exonerate the adapter or chip.** Two mechanisms brown out the CH341A while *passing* a static bare-adapter VCC↔GND test: **reverse-polarity orientation** (adapter seated 180° → CH341A drives VCC into the chip's GND pin; the chip's substrate / ESD-protection diodes conduct hard only *when powered*, and read perfectly open on an unpowered bare-adapter meter test) and a **current-leaky / latch-up-damaged chip** (a chip cooked by desolder heat or ESD draws excess supply current only when powered, also reading open statically). The leading hypothesis is now **reverse-polarity orientation or a cooked chip**, not a hard solder bridge. STAGE 4-ter and Section H below are revised accordingly — orientation verification now comes **before** the meter-based conclusions.

> **⚠ UPDATE (T+4d/T+4e — workshop-arc PIVOT; this doc's CH341A/out-of-circuit posture is now historical).** Between T+4c (this doc's last edit) and T+4e two facts overturned the out-of-circuit posture this document is built around:
>
> 1. **The original research method was IN-CIRCUIT SOIC-8 clip via ZIF ICSP — not out-of-circuit ZIF.** T+4c inferred "ZIF programmer = out-of-circuit" from the research's choice of an Xgecu T48, but the research notes (`PhysAccessDigiLies_PhrackSubPiano.txt`, surfaced at T+4d) and the operator's own recall establish that the T48 was used **in-circuit with a SOIC-8 clip wired into the ZIF socket**. The T48 reads in-circuit cleanly because it has a real current-capable 3.3 V supply (the reason the original research chose it over the CH341A). The "must desolder / out-of-circuit" decision in Section G.0 was a **CH341A-specific power-rail constraint**, not a methodology constraint of the research.
> 2. **The T+4e bench validated the in-circuit T48 + SOIC-8 clip method end-to-end on physical hardware** — `minipro 0.7.4` + Xgecu T48 + SOIC-8 clip clamped on the intact lock's AT45DB041E **in circuit**, full read (540,672 bytes), byte-identical re-read, write+verify of an injected payload, keypad-unlock functional verification. Report: `T+4e-DUMP-VALIDATION-REPORT.md` + `T+4e-INJECTION-PAYLOAD.md`. The workshop's primary toolchain is now **T48 + minipro + in-circuit SOIC-8 clip + Kali**, documented in `T48-KALI-PLAN.md`. The CH341A path remains a candidate for the per-attendee tooling decision pending a Phase 6 / T+4g live-chip re-test on a non-cooked spare.
>
> **What this means for the sections below.** Sections G / G.0 / G.4 prescribe out-of-circuit reading as the workshop methodology — they are now **historical** (the methodology the workshop *considered* at T+4b based on incomplete information, then superseded once the research was actually read and the bench validated the in-circuit method). STAGE 4-bis and STAGE 4-ter carry the same out-of-circuit framing forward into remediation; they are **retained for the CH341A re-test scenario and for diagnostic teaching value** but their "desolder first" framing no longer applies to the workshop arc. Section H (cooked-chip-by-desolder) is now **outside the workshop's threat model** (the workshop does not desolder) and is **retained as a training reference**. Per-section banners follow in G, G.0, G.4, STAGE 4-bis, STAGE 4-ter, and H. Sections A, B (other than 4-bis/4-ter), C, D, E, F are unaffected. See `T48-KALI-PLAN.md` for the validated alternative and `T+4e-DUMP-VALIDATION-REPORT.md` for the bench evidence.

---

## A. TOOLCHAIN ASSESSMENT & RECOMMENDATION

### A.0 — Headline recommendation

| | Tool | Version | Read command (the AT45DB041E) |
|---|---|---|---|
| **RECOMMENDED** | `flashrom` | `1.6.0` (Kali pkg, already installed) | `sudo flashrom -p ch341a_spi -c AT45DB041D -r dump.bin` |
| **FALLBACK** | Xgecu T48 + `minipro` (Linux) or Xgpro (Windows) | T48 / minipro 0.7+ | CLI: `minipro -p AT45DB041E -r dump.bin`; GUI: select `AT45DB041E`, Read |

The CH341A **board** is fine. The fault that this section addresses is purely in the **software tool** the workshop files currently name (`ch341prog`) — switching tools is a zero-hardware-cost fix.

> **⚠ UPDATE (T+4b bench — see Sections F & G).** A *second*, independent problem surfaced on the bench: even with the correct software (flashrom), the CH341A would not communicate — a flood of `LIBUSB_TRANSFER_ERROR` plus the device repeatedly dropping off the USB bus. **Root cause, revised after the operator disclosed the chip is being read in-circuit (Section F.0):** the leading cause (~60%) is the **in-circuit dual-power conflict** — the chip is still on the lock's PCB with the lock's battery energising it, so two 3.3 V sources sit on the chip's VCC rail (the lock battery and the CH341A clip) while the lock's MSP430 is live on the shared SPI bus; this browns out the weak CH341A supply and resets its USB PHY. The full-speed-on-xHCI USB-transport interaction is the *second* candidate (~30%). **The free, first fix is to read the chip out of circuit / with the lock's battery removed** — only if that does not clear it is a **USB 2.0 hub per station** (~$5–10) the next move, with the **Xgecu T48** (USB 2.0 high-speed, immune to the xHCI failure) as the robust fallback. See Section F.0 (revised diagnosis), Section B STAGE 4-bis (reordered remediation), Section G.0/G.1 (procedure + equipment impact).

### A.1 — Can `ch341prog` read an AT45DB041E? NO.

Confirmed by direct inspection of the downloaded source at
`/home/qweary/Desktop/ToorCampWorkshop/ch341prog-master/`. Three independent, load-bearing reasons:

**Reason 1 — Hardcoded 25-series Read opcode.**
`ch341SpiRead()` in `ch341a.c` (line ~422) issues:
```c
out[idx++] = swapByte(fourbyte? 0x13: 0x03);   // 0x03 = 25-series "Read Array"
out[idx++] = swapByte(add >> 16);
out[idx++] = swapByte(add >> 8);
out[idx++] = swapByte(add);
```
Opcode `0x03` with a **3-byte linear byte address** is the standard SPI NOR (25-series) Read Array command. The AT45DB041E in its **default 264-byte-page mode** does not use a linear byte address — it uses a *split address*: high bits select the page, low 9 bits are the byte offset *within a 264-byte page*. Feeding `0x03` + linear address to a DataFlash chip in default mode reads from the wrong physical locations; you get a 512 KB file of misaligned / wrapped garbage, not a faithful image. (The AT45DB041E *does* implement a 25-series-style continuous read at opcode `0x03`/`0x0B`, but `ch341prog` also assumes a power-of-2 address space — see Reason 3 — so even the continuous-read path is not safe here.)

**Reason 2 — Capacity detection is built for 25-series ID / CFI, not DataFlash.**
`ch341SpiCapacity()` (line ~249) reads JEDEC `0x9F`, then derives capacity from either a CFI `QRY` structure or `in[3]` (the third ID byte) interpreted as a 25-series capacity code. The AT45DB041E returns JEDEC `1F 24 00`. Byte 3 is `0x00`, which is **not** a 25-series capacity code. `ch341prog` will either misreport capacity or fall through to its "set manually" path — and even with `-l 524288` forced, Reason 1 still corrupts the data.

**Reason 3 — No DataFlash page-geometry awareness anywhere in the codebase.**
`grep` of `ch341a.c` / `main.c` shows no AT45/DataFlash handling, no page-size register read (status register bit that reports 264 vs 256), no 33/32 address scaling. Every read/write/erase path (`0x03` read, `0x02` page program, `0xC7` chip erase, `0x05` status) is 25-series SPI NOR. The security-register code (`0x42/0x44/0x48`) is Winbond W25Q-specific and irrelevant to DataFlash.

**Verdict:** `ch341prog` is structurally a 25-series SPI NOR tool. It has no code path that can correctly address an AT45DB041E. The operator's failed install attempts spared them from a worse outcome — a tool that *runs* and produces a *plausible-looking* 512 KB file that is silently wrong.

### A.2 — The correct tool: flashrom with the `at45db` driver

flashrom has a dedicated DataFlash driver (`at45db.c`) that:

- Reads the chip's **status register** to detect whether the chip is in 264-byte or 256-byte (power-of-2) page mode, and scales all geometry by **33/32** accordingly.
- Performs the correct **split-address** translation (page bits in the high field, byte offset in the low field) so a full-chip read is faithful regardless of page mode.
- Distinguishes the **E variant** from the D variant using **Extended Device Information (EDI = `0x0100`)** via `probe_spi_at45db_e()` — the D and E share JEDEC `1F 24 00`, so EDI is the discriminator.

**flashrom AT45DB041E support is mature** — the `at45db` driver and AT45DB041E entry predate flashrom 1.0 (Atmel DataFlash work landed circa 2012–2013). The Kali-installed **flashrom 1.6.0** (released July 2025) includes it.

**Chip-name caveat — important for the read command.** On the operator's installed flashrom 1.6.0, `flashrom -L` lists the family entry as **`AT45DB041D`** (512 KB, `PREW`), and does **not** print a separate `AT45DB041E` row. In flashrom's chip database the 041E is defined as "same JEDEC ID as 041D, distinguished by EDI" and, in this packaging, presents under the **`AT45DB041D`** name. The 041D and 041E are pin- and function-compatible 4 Mbit DataFlash parts with identical geometry for read purposes. **Use `-c AT45DB041D`.** If a future flashrom on the bench *does* list `AT45DB041E` separately, prefer that exact string. Stage 5 of Section B handles both cases with a branch.

The `ch341a_spi` programmer driver is present in the installed flashrom (`flashrom -p` choices include `ch341a_spi` — verified). SPI clock on the CH341A is fixed at ~2 MHz; a 512 KB read completes in well under a minute.

### A.3 — Confirmed: keep the CH341A, switch the tool

The CH341A board does raw SPI to any SPI device — the AT45DB041E is an SPI device. The limiting factor was 100% the software (`ch341prog`'s 25-series-only command set). Pairing the same board with flashrom's `at45db` driver is the **affordable fix at $0 incremental hardware cost**. No new programmer is required for the recommended path.

### A.4 — Page-mode subtlety and the handout's "512 KB" claim

The AT45DB041E ships in **default 264-byte-page mode**. Power-of-2 (256-byte) mode is a **one-time-programmable** config-register change.

| Page mode | Pages | Page size | Total addressable | Bytes |
|---|---|---|---|---|
| **Default (DataFlash)** | 2048 | **264 B** | 2048 × 264 | **540,672** (528 KiB) |
| Power-of-2 (binary) | 2048 | 256 B | 2048 × 256 | **524,288** (512 KiB) |

The chip's *advertised* capacity is **4 Mbit = 4,194,304 bits = 524,288 bytes** — that figure assumes the binary 256-byte page. The extra 8 bytes/page in default mode are real, addressable, usable storage (DataFlash's "extra" per-page bytes), giving **540,672 bytes**.

**⚠ FLAG FOR SMYTH (file-update phase) — handout/guide inconsistency:**
Both `PARTICIPANT-HANDOUT.md` (line 65) and `FACILITATOR-GUIDE.md` (line 134) claim the dump is **"524,288 bytes (512 KB)"**. This is **only correct if the specific chip has been switched to power-of-2 mode** — which is not the factory default and is irreversible. Three sub-issues for SMYTH to resolve once Stage 5 runs on real hardware:

1. **Dump size depends on what flashrom reports.** When flashrom probes the chip it prints the detected page mode and total size. If the chip is in **default 264-byte mode**, flashrom will read **540,672 bytes**, *not* 524,288. The handout's "file should be 524,288 bytes" success check would then **falsely fail a correct dump**.
2. The handout's offset map (page header `FD` at `0x0000`, columns at `0x0001`–`0x00FF`, "jump ahead 264 bytes / `0x0108`") is **page-relative and 264-byte-page-based** — internally consistent with *default* DataFlash mode. So the handout *body* assumes 264-byte pages while the *size claim* assumes 256-byte pages. These contradict each other.
3. **Recommended fix for SMYTH:** change the success criterion from a hardcoded byte count to *"flashrom reports the chip and the read completes with no error; note the size flashrom prints (≈528 KB in default mode, ≈512 KB if power-of-2)."* The exact number should be confirmed against the operator's real bench read in Stage 5 and then written in as ground truth. Do **not** print a hardcoded size until that read is done.

### A.5 — CH341A 5V / 3.3V issue — RELEVANT, mitigation warranted

The AT45DB041E is a **1.65–3.6 V** part (3.3 V nominal). Many CH341A "black board" units power the IC socket / SPI I/O at **~5 V** because the design pulls VCC for the level section from USB 5 V; the official flashrom CH341A page documents this explicitly: *"a voltage of just under 5 volts at the outputs of the CH341A that lead to the IC socket, which is usually too much for the inputs of the EEPROMs and can cause them to break."*

**Why it matters for this workshop specifically:** this is not a single read — it is **~20+ participants each reading a chip, with re-seats and retries**, i.e. many hundreds of clip-on cycles across the session. Sustained 5 V on a 3.3 V part's I/O risks **cumulative latch-up / input-clamp stress**, intermittent bad reads that look like "bad clip," and occasional dead chips mid-workshop.

**Assessment:** medium risk. A single read on a 5 V board often "works"; the failure mode is degraded chips and flaky reads under repeated use — exactly the workshop's load profile. The well-known hardware fix (lifting CH341A pin 28 and tying the level-section VCC to the 3.3 V rail) is a **soldering modification** and is **electrical-hardware tradecraft outside a Systems Engineer's lane.**

**Mitigations, ranked (operator chooses; items 2–4 should be routed to an electrical/hardware specialist for the actual modification):**

1. **Measure first (no tools beyond a multimeter).** Before the workshop, with the clip *unconnected*, measure DC voltage between the clip's VCC (pin 8) and GND (pin 4) while the CH341A is plugged into USB. **If it reads ~3.3 V → no action needed**, the board is a 3.3 V-correct unit (some newer boards are). **If it reads ~5 V → mitigation needed.**
2. **Buy 3.3 V-correct boards / a small adapter.** "CH341A 1.8V/3.3V adapter" boards and known-good 3.3 V CH341A revisions exist for a few dollars; cheapest reliable path if procurement time allows.
3. **The pin-28 lift mod** — the canonical fix, but soldering; do on a couple of facilitator reference units, not 20.
4. **Power the target from a clean 3.3 V source** and only use the CH341A for the SPI signal lines — more setup complexity than a workshop wants.

> **ROUTING NOTE FOR NEO:** The voltage *measurement* (item 1) is in scope for the operator to run as a probe. The board *modification* (items 2–4, especially the pin-28 lift) is **electrical/hardware-engineering work and should be routed to a hardware/electronics specialist** in a follow-up if the measurement comes back at 5 V. Do not have a software specialist spec a soldering mod.

### A.6 — Other DataFlash-capable tools (for completeness)

- **flashrom** — recommended; covered above.
- **`minipro`** (David Griffith fork) — open-source CLI for Xgecu TL866/T48 programmers; large device DB that includes AT45DB DataFlash. Linux-native. This is the *fallback hardware's* Linux tool.
- **`libxsvf` / Arduino DataFlash libraries / `dd` over `linux_spi`** — would require wiring the chip to a Raspberry Pi or SPI-capable SBC and using flashrom's `linux_spi` programmer. Viable but adds an SBC per station — not workshop-affordable. Mentioned only to be exhaustive.
- **`ch341eepromtool`** — I2C EEPROM only; irrelevant to SPI DataFlash.

### A.7 — Options ranked by USD cost

| Rank | Path | Hardware cost | Software | Reliability for AT45DB041E |
|---|---|---|---|---|
| 1 | **CH341A board + flashrom, chip read OUT OF CIRCUIT / power-isolated** | ~$7 board (+ optional **$5–10 hub/station** only if xHCI failure is confirmed after power isolation) | flashrom 1.6.0, already on Kali | High — `at45db` driver handles DataFlash correctly; reading out of circuit removes the dual-power conflict (Section F.0); a USB 2.0 hub is added only if the xHCI failure (F.2) survives power isolation |
| 2 | CH341A + flashrom, **with 3.3 V fix** (adapter board) | +$2–5 adapter (+ hub only if F.2 confirmed) | flashrom | High + protects chips over many reads; addresses the 5 V I/O concern (A.5), separate from the F.0/F.2 bench failure |
| 3 | CH341A + `ch341prog` | $7 | builds from downloaded source | **Unusable — wrong command set** |
| 4 | Xgecu T48 + `minipro` (Linux) | ~$30–55 | minipro (open source) | High; **USB 2.0 high-speed — immune to the Section F xHCI failure**; T48 support in minipro is newer — test first |
| 5 | Xgecu T48 + Xgpro (Windows) | ~$30–55 | Xgpro (Windows GUI) | High — vendor-supported; the writeup's original tool; same robust USB-2 hardware |

> **⚠ UPDATE (T+4b bench, revised per Section F.0).** Rank 1's "$0 extra hardware" holds **only if the chip is read out of circuit / power-isolated.** The bench failure was leading-cause traced (Section F.0) to reading the chip **in-circuit on a live, self-powered board** — a *procedure* fault, not an equipment shortfall. Reading out of circuit is free; it is the workshop-procedure change in Section G.0. A **USB 2.0 hub** ($5–10/station) is needed only as a *second* remedy, if the failure survives power isolation and the xHCI hypothesis (F.2) is confirmed. The T48 (Ranks 4–5) remains the *robust* choice because its USB 2.0 high-speed transport structurally avoids the xHCI failure mode and the ZIF socket enforces out-of-circuit reading by construction.

**Recommendation: Rank 1 (CH341A + flashrom) for the workshop, reading chips OUT OF CIRCUIT / power-isolated (Section G.0), with the 3.3 V voltage check (A.5) done beforehand. STAGE 4-bis tests the free power-isolation fix first; a USB 2.0 hub is added only if that fails. If neither resolves it, switch wholesale to the Xgecu T48 (Rank 4/5) — see Section G.**

---

## B. STAGED INTERACTIVE DIAGNOSTIC & REMEDIATION PLAN

> **How to run this:** Each STAGE is a block of commands the operator runs on Kali and pastes the output back. Deterministic stages can be run back-to-back without re-consulting. **BRANCH** points are the only places a decision is needed. Commands that change the system are explicitly flagged; everything else is read-only.
>
> Goal: a verified, faithful binary dump of the AT45DB041E using the CH341A.

### STAGE 0 — Baseline probe (read-only, run all at once)

```bash
# 0a. flashrom present and version
flashrom --version

# 0b. ch341a_spi programmer driver compiled in
flashrom -p list 2>&1 | tr ',' '\n' | grep -i ch341 || echo "ch341a_spi NOT listed"

# 0c. AT45DB041 chip entry present in the chip DB
flashrom -L 2>/dev/null | grep -iE "AT45DB041"

# 0d. CH341A enumerated on USB
lsusb | grep -i "1a86:5512" || echo "CH341A NOT enumerated"

# 0e. xxd present (hex viewer for the dump)
which xxd
```

**Expected output (matches what the operator's machine already showed):**
- `0a` → `flashrom v1.6.0 on Linux ...`
- `0b` → `ch341a_spi`
- `0c` → `Atmel  AT45DB041D  PREW  512  SPI` (note: name is **041D**, not 041E — expected, see A.2)
- `0d` → `Bus 001 Device NNN: ID 1a86:5512 QinHeng Electronics CH341 ...`
- `0e` → `/usr/bin/xxd`

**BRANCH:**
- All five OK → **skip Stage 1 entirely, go straight to STAGE 2.** (flashrom and xxd are already installed on this Kali box — confirmed during T+4 probing. Stage 1 is only for a fresh machine.)
- `0a` empty / "command not found" → flashrom missing → **STAGE 1**.
- `0b` says "NOT listed" → flashrom built without `ch341a_spi` (rare on Kali) → **STAGE 1** (reinstall the distro package, which has it).
- `0c` empty → flashrom too old or chip DB stripped → **STAGE 1** to get the current package.
- `0d` says "NOT enumerated" → re-plug the CH341A, try another USB port / cable, re-run `0d`. If still absent → it is a hardware/cable fault, not software → **STAGE 4 troubleshooting**, do not proceed.

### STAGE 1 — Dependency install (ONLY if Stage 0 flagged something missing)

> ⚠ **This stage installs packages — it changes the system.** It is needed only on a machine that does not already have flashrom. On the operator's current Kali box, **Stage 0 passes and Stage 1 is skipped.**

**Recommended: distro package (NOT building `ch341prog`).** flashrom is a maintained Kali package; building the downloaded `ch341prog` source is both unnecessary *and* would produce a tool that cannot read this chip (Section A.1). Do not build `ch341prog`.

```bash
# 1a. update index and install flashrom + xxd
sudo apt-get update
sudo apt-get install -y flashrom xxd

# 1b. re-verify
flashrom --version
flashrom -p list 2>&1 | tr ',' '\n' | grep -i ch341
flashrom -L 2>/dev/null | grep -iE "AT45DB041"
```

**Expected:** `flashrom v1.6.0` (or newer), `ch341a_spi` listed, `AT45DB041D` row present.

> **Offline-at-campground note:** `apt-get` needs network. ToorCamp runs offline. **Do Stage 0/1 at home before leaving**, while network is available — or use the Section E standalone package (which vendors the `.deb` files for offline install). The operator already has `flashrom 1.6.0-3` installed, so for *this* operator no network is required at camp.

**BRANCH:**
- `1b` all OK → **STAGE 2**.
- `apt-get` cannot reach the mirror → you are offline → install from the cached `.deb` files (`sudo dpkg -i flashrom_*.deb`) — note the operator already has several `.deb` files staged in the repo root; flashrom itself is already installed so this is moot for this machine.

### STAGE 2 — udev permissions so flashrom runs without sudo (optional, recommended)

> ⚠ **This stage writes one udev rule file — a small, reversible system change.** Skip it and use `sudo flashrom` instead if you prefer zero system changes; functionally identical.

```bash
# 2a. install a udev rule granting access to the CH341A
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="5512", MODE="0666"' \
  | sudo tee /etc/udev/rules.d/99-ch341a.rules

# 2b. reload rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

**Then physically unplug and re-plug the CH341A.**

**Expected:** no output errors from `2a`/`2b`.

**BRANCH:** Either path works —
- Did Stage 2 → later flashrom commands run **without** `sudo`.
- Skipped Stage 2 → prepend **`sudo`** to every `flashrom` command in Stages 3–5.
The plan below writes `sudo` in front of flashrom for safety; drop it if Stage 2 was done.

### STAGE 3 — Chip detection (the real go/no-go gate)

Seat the SOP8 clip on a known-good AT45DB041E (pin 1 / dot aligned to the clip arrow), CH341A plugged in.

```bash
# 3a. probe the chip — DO NOT pass -r/-w/-c yet; let flashrom identify it
sudo flashrom -p ch341a_spi
```

**Expected (success):** flashrom prints lines similar to:
```
Found Atmel flash chip "AT45DB041D" (512 kB, SPI) on ch341a_spi.
```
(It may also note the detected **page size** — 264 B or 256 B — and total size. **Record what it prints.**)

**BRANCH:**
- Output names an **`AT45DB041*`** chip → detection works → **STAGE 5** (Stage 4 is the failure branch, skip it).
- Output says **"No EEPROM/flash device found"** or **"Probing for ... failed"** → **STAGE 4**.
- Output says **"Multiple flash chip definitions match"** and lists several AT45DB names → this is normal for shared-JEDEC-ID parts → go to **STAGE 5** and pass `-c AT45DB041D` explicitly (Stage 5 already does this).
- `libusb` / permission error (`Could not open device`, `Access denied`) → permissions → do **STAGE 2** if skipped, or run with `sudo`; re-run `3a`.
- `cannot find libusb` at runtime → flashrom package is broken → re-run **STAGE 1**.
- **`Couldn't open device 1a86:5512` / `Programmer initialization failed`** *with sudo already in use* — not a permission error — and `lsusb` shows **no `1a86` device** (CH341A gone from the bus) and/or `dmesg` shows an xHCI enumeration loop (`error -71`, `unable to enumerate USB device`) → the CH341A has browned out and dropped off the bus. If the chip is **out of circuit on a SOIC-to-DIP adapter / breakout** and there was **no `LIBUSB_TRANSFER_ERROR` flood**, suspect an **excess load on the CH341A 3.3 V rail from the chip-plus-adapter** — reverse-polarity orientation, a cooked/leaky chip, or a VCC↔GND short → **STAGE 4-ter** (Section H). If the chip is still **in-circuit on a live board**, this is the Section F.0 dual-power brown-out → **STAGE 4-bis**.

### STAGE 4 — Detection-failure remediation (only if Stage 3 failed)

Work top to bottom; re-run `sudo flashrom -p ch341a_spi` after each fix until it detects the chip.

```bash
# 4a. confirm the board is still on the bus
lsusb | grep -i "1a86:5512"

# 4b. check kernel messages for USB faults
dmesg | tail -20
```

Remediation checklist (cheapest/most-likely first):
1. **Re-seat the SOP8 clip.** #1 failure mode. Pin 1 dot ↔ clip arrow. Press firmly, hold during the probe.
2. **Swap the clip cable.** SOP8 clips wear out and develop intermittent contacts.
3. **Different USB port; avoid unpowered hubs.** Use a direct port or a *powered* hub.
4. **Swap the CH341A unit.** Some boards are simply bad. (Facilitator brings spares.)
5. **Voltage check (see A.5).** With the clip off, measure VCC↔GND on the clip while the board is plugged in. ~5 V on a 3.3 V part can cause flaky/failed detection. If 5 V → use a 3.3 V-correct board or the adapter; route the board mod to a hardware specialist.
6. **Try a different known-good chip** to isolate chip-vs-programmer.

**BRANCH:**
- Any fix → Stage 3 now detects → **STAGE 5**.
- Exhausted the checklist, still no detection on multiple boards + chips → the **CH341A path is not reliable on this hardware** → **fall back to the Xgecu T48 path (Section D, Rank 4)**. Do not burn workshop time fighting it.
- Output is **not** "No flash device found" but instead a flood of **`cb_out: error: LIBUSB_TRANSFER_ERROR`** / `Failed to write N bytes`, or `config_stream: Failed to write 3 bytes` / `Programmer initialization failed`, and/or the CH341A keeps **disconnecting and re-enumerating** → this is **not** a clip-contact failure → **STAGE 4-bis** (Stage 4 above does not address it). The leading cause is the CH341A's power being destabilised — most often by reading the chip **in-circuit on a live board** (Section F.0); STAGE 4-bis tests that first, for free, before any USB-transport remedy.
- Output is **`Couldn't open device 1a86:5512` / `Programmer initialization failed`**, or `lsusb` shows **no `1a86` device at all** (the CH341A has dropped fully off the bus), or `dmesg` shows an xHCI **enumeration loop** (`device not accepting address N, error -71`, `unable to enumerate USB device`) — and the chip is **out of circuit on a SOIC-to-DIP adapter / breakout**, with **no `LIBUSB_TRANSFER_ERROR` flood** at the moment of failure → this is an **excess load on the CH341A 3.3 V rail from the chip-plus-adapter** — reverse-polarity orientation, a cooked/leaky chip, or a VCC↔GND short — not a clip-contact fault and not the in-circuit dual-power fault → **STAGE 4-ter** (Section H is the diagnosis + operator procedure). This is the common attendee failure after desoldering and mounting their own chip.

### STAGE 4-bis — `LIBUSB_TRANSFER_ERROR` remediation (USB-transport / in-circuit power failure)

> **⚠ SCOPE NARROWED (T+4d/T+4e supersession).** STAGE 4-bis was authored when the workshop arc was CH341A + (later) out-of-circuit. The workshop arc is now **T48 + in-circuit SOIC-8 clip** (`T48-KALI-PLAN.md`, T+4e-validated). STAGE 4-bis is therefore retained for **two specific scenarios only**:
> 1. The Phase 6 / T+4g **CH341A live-chip re-test** on a non-cooked spare — if the same in-circuit brown-out symptom surfaces, this stage's diagnosis still applies (the T+4g re-test will likely be in-circuit, since the workshop is now in-circuit).
> 2. As a **training reference** for the dual-power-rail brown-out failure mode, which has standalone teaching value for any operator using a weak-LDO programmer.
>
> **The "desolder first / read out of circuit" framing in step 4-bis-b option 1 below no longer represents the workshop's procedure.** The workshop reads in-circuit on T48s. Option 2 (disconnect the lock's battery — read with the programmer as sole supply) **is** the correct first move both for the T48 and the CH341A. The desoldering option is retained as a diagnostic / training option, not a workshop procedure. Step 4-bis-b is annotated accordingly.

> **When you are here:** Stage 3 did *not* print "No flash device found" as its main symptom. Instead flashrom emitted many repetitions of `cb_out: error: LIBUSB_TRANSFER_ERROR` + `ch341a_spi_spi_send_command: Failed to write N bytes` and then `No EEPROM/flash device found` — or, on a retry, failed even earlier with `config_stream: Failed to write 3 bytes` / `Could not configure stream interface` / `Programmer initialization failed`, and the CH341A repeatedly disconnected and re-enumerated. **This is a different failure from Stage 4.** Stage 4 assumes the USB link to the CH341A is healthy and the *SPI clip contact* is the problem. Here the USB link itself is failing: every **bulk-OUT** transfer to the CH341A errors out, even though enumeration (control transfers) succeeded. See **Section F** for the full root-cause diagnosis.
>
> **⚠ REORDERED after the operator disclosed the chip is being read in-circuit.** Per **Section F.0**, the leading suspect is no longer the USB transport — it is the **in-circuit dual-power conflict**: the lock's battery and the CH341A's clip both feed 3.3 V onto the chip's VCC rail, browning out the CH341A, while the live MSP430 contends on the SPI bus. **The discriminating test for that is FREE — disconnect the lock's power — so it now runs FIRST, before any USB-2 hub is acquired.** The USB-2-hub and cable/board steps are retained but moved *after* the power-isolation step. Re-run the probe after each step.

**Step 4-bis-a — [Neo via MCP] capture the current state (read-only, no change).**

```bash
# 4bis-a. [Neo via MCP] confirm the board is enumerated, capture speed + descriptor + cycling
lsusb | grep -i "1a86:5512"
lsusb -t                                  # shows which controller/speed the device sits on
lsusb -v -d 1a86:5512 2>/dev/null | grep -E "bcdUSB|bMaxPacketSize0|MaxPower|bcdDevice"
dmesg | grep -iE "usb|xhci|disconnect" | tail -30   # look for disconnect/reconnect cycling
```

**Step 4-bis-b — [Operator — physical action] ISOLATE THE CHIP'S POWER. THIS IS THE FIRST AND HIGHEST-PROBABILITY FIX, AND IT COSTS NOTHING.**
The chip is currently being read **in-circuit on a live, self-powered board** — two 3.3 V sources on its VCC rail and the lock's MSP430 live on the SPI bus (Section F.0). Remove that condition. In order of preference:

1. **~~Best —~~ [T+4d/T+4e: NO LONGER THE WORKSHOP PROCEDURE; retained as a diagnostic / training option only] read the chip out of circuit.** If the AT45DB041E can be desoldered and read in a SOP8 socket / adapter (or on a bare breakout with nothing else attached), do that. This eliminates *both* the dual-power conflict *and* the MSP430 bus contention in one move. ~~The original `PhysAccessDigiLies` research used a ZIF-socket programmer (Xgecu T48), i.e. the chip was read **out of circuit** — that is the known-good methodology.~~ **[T+4d/T+4e correction: the research used the T48's ZIF as an ICSP wiring endpoint for a SOIC-8 clip and read IN-CIRCUIT; see G.0 correction banner. Desoldering is NOT the research method and is NOT the workshop method.]** ⚠ *Desoldering/resoldering the chip is board-level rework — electrical-hardware tradecraft, out of the Systems Engineer lane. If the operator wants the chip removed, route that to a hardware/electronics specialist; do not spec the rework here.* **Use option 2 first** — it achieves the same dual-power-rail fix with no rework, and it is what the T+4e bench did (battery out, T48 powering only the chip-plus-quiet-board through the clip).
2. **If reading in-circuit — disconnect the lock's battery pack completely** so the **CH341A's clip is the only power source** on the chip's VCC rail. This removes the dual-power conflict (Mechanism 1) and de-energises the MSP430 so it can no longer drive the SPI bus (Mechanism 2). This is the **zero-cost, zero-tool action the operator should do right now.** Pull the battery, leave the clip on, nothing else changes. **[T+4d/T+4e: this option, combined with a current-capable programmer like the T48, is now the workshop's standing method — T+4e-validated on physical hardware. For the CH341A path, the same step is still the right first move; whether the CH341A's weak LDO can sustain it across a full read+write is the open question for the T+4g CH341A live-chip re-test.]**
3. **Only if the board cannot be fully de-powered — isolate the VCC pin.** Lift the chip's VCC pin from the board (or cut the clip's VCC line) so the CH341A powers the chip alone while the rest of the board stays unpowered. ⚠ *Lifting a pin is board-level rework — out of lane; route to a hardware specialist. Option 2 (just unplug the battery) achieves the same VCC-rail result with no rework and is strongly preferred.*

After the operator has done step 1 or 2, **[Neo via MCP]** re-probe:

```bash
# 4bis-b. [Neo via MCP] after the operator removes the lock's battery (or sockets the chip):
dmesg | grep -iE "usb|disconnect" | tail -15   # has the re-enumeration cycling stopped?
sudo flashrom -p ch341a_spi                    # re-probe
```

**BRANCH:**
- Probe now prints **`Found ... AT45DB041*`**, and `dmesg` no longer shows the CH341A cycling → **the in-circuit dual-power conflict WAS the cause (F.0 Mechanism 1 confirmed).** Go to **STAGE 5**. **No USB hub is needed — do not spend money on one.** Record this: the workshop must read chips out-of-circuit / power-isolated (see Section G).
- Probe still floods `LIBUSB_TRANSFER_ERROR` *with the lock battery disconnected and the CH341A as the sole power source* → the dual-power conflict is **excluded**, the USB-transport hypothesis (F.2) is back in play → continue to step 4-bis-c.
- Probe stops flooding `LIBUSB_TRANSFER_ERROR` but now reports **`No EEPROM/flash device found`** or an all-`0xFF` read → the USB link is healthy and the *remaining* problem is SPI-side (clip contact, or — if the board is still powered — residual MSP430 contention). This is now a **STAGE 4** symptom, not a 4-bis one → finish power-isolating the board, then work the **STAGE 4** clip checklist.

**Step 4-bis-c — [Neo via MCP] USB port reset (no operator action, no hardware change).**
Re-enumerating the device from the host side clears a wedged endpoint and is free. The CH341A re-enumerates anyway (the bench saw device numbers 6→7→8), so this is low-risk.

```bash
# find the device's bus/dev path, then toggle 'authorized' to force a clean re-enumeration
for d in /sys/bus/usb/devices/*; do
  [ -f "$d/idVendor" ] && [ "$(cat "$d/idVendor" 2>/dev/null)" = "1a86" ] && \
  [ "$(cat "$d/idProduct" 2>/dev/null)" = "5512" ] && echo "CH341A at: $d"
done
# for the path printed above (e.g. /sys/bus/usb/devices/1-1):
echo 0 | sudo tee /sys/bus/usb/devices/1-1/authorized
sleep 1
echo 1 | sudo tee /sys/bus/usb/devices/1-1/authorized
sleep 2
lsusb | grep -i "1a86:5512"     # confirm it came back
sudo flashrom -p ch341a_spi      # re-probe
```

**BRANCH:**
- Probe now detects the chip → **STAGE 5**.
- Still `LIBUSB_TRANSFER_ERROR` → continue. (A port reset rarely fixes a *structural* problem; it mainly clears a transient wedge. Expect to continue.)

**Step 4-bis-d — [Operator — physical action] try every other port, including the USB-3 (blue, 5000M) ports.**
Move the CH341A — *directly*, no hub — to each remaining physical port on the laptop one at a time. On this bench both controllers are xHCI (there is no USB-2-only EHCI companion), so this is not expected to fix it, but it is free, it isolates a single dead port, and on some laptops different xHCI root ports behave differently. After each move, **[Neo via MCP]** re-run `sudo flashrom -p ch341a_spi`.

**BRANCH:**
- One port detects the chip reliably (run the probe 2–3×) → **STAGE 5**, and note which port for the workshop.
- No port works → continue. This is the expected outcome on an all-xHCI host and points at the transaction-translator fix below.

**Step 4-bis-e — [Operator — physical action] insert a powered USB 2.0 hub between the laptop and the CH341A. Highest-probability fix for the USB-transport hypothesis — but only reached if power isolation (4-bis-b) did NOT fix it.**
Plug a **USB 2.0** hub (not USB 3.0 — see note) into the laptop, plug the CH341A into the hub, then **[Neo via MCP]** re-probe. A USB 2.0 hub contains a **Transaction Translator (TT)**: the xHCI host talks high-speed (480M) to the hub's TT, and the TT does the full-speed (12M) bulk transactions to the CH341A. This restores the split-transaction path that a bare xHCI root port does not provide for full-speed bulk endpoints, and is the documented fix for the USB-transport failure mode (F.2).

```bash
# 4bis-e. [Neo via MCP] after the operator inserts the hub:
lsusb -t                                  # CH341A should now appear BELOW a hub, still at 12M
sudo flashrom -p ch341a_spi                # re-probe
```

> **Hub choice — important.** Use a **USB 2.0** hub specifically. A "USB 3.0" hub presents the full-speed device to a *separate internal USB-2 hub block* that does have a TT, so most USB 3.0 hubs also work — but cheap USB 3.0 hubs are inconsistent here. A plain USB 2.0 hub is the reliable, cheap choice. **Powered** (external supply) is preferred so hub-port power is clean, though the CH341A's 100 mA draw is modest. Pass-through bus-powered USB 2.0 hubs usually also work.

**BRANCH:**
- Probe detects the chip through the hub → **STAGE 5.** Record it — it has direct workshop-equipment consequences (see **Section G**).
- Still failing through the hub → continue to 4-bis-f. (If the hub is itself USB 3.0, retry with a known USB 2.0 hub before concluding.)

**Step 4-bis-f — [Operator — physical action] swap the USB cable, then swap the CH341A board.**
A marginal cable causes intermittent bulk-transfer errors that look identical to the transport problem. Use a **short, known-good** USB cable (the CH341A's bulk traffic is unforgiving of marginal cabling; shorter is better). If a cable swap does not help, swap to a different CH341A unit (board quality varies; the bench saw the device re-enumerating 6→7→8 and degrading between runs, which can indicate a flaky board as well as a transport mismatch or a brown-out). **[Neo via MCP]** re-probe after each swap.

**BRANCH:**
- Cable or board swap fixes it (with or without the hub) → **STAGE 5**.
- No combination of power isolation + port + hub + cable + board works → continue to 4-bis-g.

**Step 4-bis-g — [Neo via MCP] last-resort software angle: lower the clock and re-probe.**
The `ch341a_spi` programmer accepts a `spispeed` parameter. A slower SPI clock does not change the *USB* transport, but it reduces the per-command burst size and pacing and occasionally lets a marginal link through. Low cost, low expectation — try it before declaring no-go.

```bash
# 4bis-g. [Neo via MCP]
sudo flashrom -p ch341a_spi:spispeed=khz_set    # see what speeds the driver accepts; if it errors, just try a slow value:
sudo flashrom -p ch341a_spi:spispeed=khz
# (consult `flashrom -p ch341a_spi:help` or the man page for the exact accepted token on 1.6.0)
```

> **Out-of-lane note.** If at this point someone proposes a kernel-side fix — patching xHCI quirk flags, forcing the device onto a different controller, or rebuilding flashrom against a different libusb — that is **kernel/driver-integration work beyond a Systems Engineer's USB-transport-and-toolchain lane**, and for a 20-station *bring-your-own-laptop* workshop it is also non-scalable (you cannot repatch 20 strangers' kernels). Likewise, **desoldering the chip, lifting pins, or modifying the CH341A board are board-level electrical-hardware tasks — out of lane; route to a hardware/electronics specialist.** The in-lane scalable fixes are: read out of circuit / power-isolate (4-bis-b), and the powered USB 2.0 hub (4-bis-e).

**GO / NO-GO for the CH341A path:**
- **GO** — any step above makes `sudo flashrom -p ch341a_spi` print **`Found ... AT45DB041*`** *reliably* (probe 3× in a row, all detect; ideally one clean run of STAGE 5 to `VERIFIED`). The toolchain works; proceed to STAGE 5. If the win required power isolation (4-bis-b), the workshop must read chips out-of-circuit / power-isolated — see Section G. If it additionally required a hub (4-bis-e), the hub is also mandatory workshop equipment.
- **NO-GO** — power isolation, port changes, a known-good USB 2.0 hub, a known-good short cable, **and** a second CH341A board have all been tried and the probe still floods `LIBUSB_TRANSFER_ERROR` → **stop fighting the CH341A.** The board cannot be made reliable within workshop constraints → **fall back to the Xgecu T48 path (Section D — now Rank 1 of the fallbacks; see revised Section D and Section G).**

### STAGE 4-ter — adapter / chip VCC↔GND short remediation (out-of-circuit, chip on a SOIC-to-DIP adapter)

> **⚠ SCOPE NARROWED (T+4d/T+4e supersession).** STAGE 4-ter was authored when Section G.0 told the workshop to read chips out of circuit on attendee-mounted adapters — *that is no longer the workshop arc.* The workshop reads in-circuit with SOIC-8 clips on T48s; **attendees do not desolder and do not mount chips on adapters**, so the entire scenario this stage was built for is **outside the workshop's threat model**. The stage is **retained for**:
> 1. The Phase 6 / T+4g CH341A live-chip re-test, if the operator chooses to bench-test the CH341A out-of-circuit on a spare adapter (a deliberate diagnostic choice, not a workshop procedure).
> 2. Operators who, outside the workshop arc, choose to desolder and read in a socket — this stage is the diagnostic playbook for the brown-out / cooked-chip / orientation-error failure modes intrinsic to that path.
> 3. **Training reference** — the reverse-polarity / cooked-chip / sub-beep-threshold-partial-short diagnostic content has standalone teaching value (operator may want it for a future talk).
>
> **The "attendees mount their own chips → this is workshop guidance" framing in the original banner below is RETRACTED.** The H.4 SMYTH guidance ("pre-screen every adapter") and the H banner's "this failure mode is intrinsic to the G.0 recommendation" claim are likewise narrowed — they apply only if the workshop reverts to out-of-circuit, which it has not.

> **⚠ Added after the T+4c bench (HISTORICAL framing — see scope-narrowed banner above).** The operator did exactly what Section G.0 recommends — desoldered the AT45DB041E from the lock and mounted it on a SOIC-8-to-DIP adapter seated in the CH341A's onboard ZIF socket — and hit a **third, distinct failure**. STAGE 4-ter exists for it. ~~**This is also workshop-troubleshooting guidance:** every attendee who desolders and mounts their own chip on an adapter can hit a solder bridge, and a bridge between VCC and GND reproduces this exact failure. Treat 4-ter as part of the attendee flow, not just a bench note.~~ **[T+4d/T+4e: RETRACTED. Attendees do not desolder; this is NOT part of the workshop attendee flow.]**

> **When you are here:** the chip is **out of circuit** (on an adapter or breakout, not on a live lock — so this is *not* STAGE 4-bis), and one of these symptoms appeared:
> - flashrom reports **`Couldn't open device 1a86:5512. Error: Programmer initialization failed.`** — flashrom cannot even open the CH341A; *and/or*
> - `lsusb` no longer shows **any** `1a86` device — the CH341A has dropped **fully off the bus**; *and/or*
> - `dmesg` shows the CH341A in a **re-enumeration loop** — `Device not responding to setup address`, `device not accepting address N, error -71`, `unable to enumerate USB device`, `attempt power cycle`.
>
> Critically — and this is what tells STAGE 4-ter apart from STAGE 4-bis — **there is no `LIBUSB_TRANSFER_ERROR` flood at the moment of failure.** In STAGE 4-bis the device stays *enumerated* and individual bulk-OUT transfers fail (`LIBUSB_TRANSFER_ERROR` × hundreds). Here the device cannot be *opened at all*, or has vanished from `lsusb` entirely, because it has browned out hard enough to drop its USB PHY before flashrom ever issues a transfer.

**STAGE 4 vs. STAGE 4-bis vs. STAGE 4-ter — the three CH341A failure modes, kept distinct:**

| | STAGE 4 | STAGE 4-bis | STAGE 4-ter |
|---|---|---|---|
| **Symptom** | `No EEPROM/flash device found` | `LIBUSB_TRANSFER_ERROR` flood; device re-enumerates *while still listed* | `Couldn't open device` / `Programmer initialization failed`; device **gone from `lsusb`**; xHCI enumeration loop in `dmesg` |
| **USB transport** | Healthy | Failing on bulk-OUT, but device enumerates | Device will not enumerate at all |
| **Chip wiring** | On-board or socketed; clip contact poor | **In-circuit on a live, self-powered board** | **Out of circuit** — chip on a SOIC-to-DIP adapter or breakout |
| **Root cause** | Clip not contacting the chip's pads | In-circuit dual-power brown-out + MSP430 SPI contention (Section F.0) | **Excess load on the CH341A 3.3 V rail from one chip-plus-adapter** — reverse-polarity orientation, a cooked/leaky chip, or a VCC↔GND short (Section H) |
| **Remediation** | STAGE 4 | STAGE 4-bis | **STAGE 4-ter (this stage)** |

**The mechanism (full diagnosis in Section H).** When the adapter is seated in a *powered* socket position, the CH341A's weak on-board 3.3 V regulator is asked to drive an excessive or near-short load; its rail collapses, the device browns out, and — exactly as in STAGE 4-bis Mechanism 1 — the USB PHY drops. The difference from 4-bis is the *source*: 4-bis is a whole live board; 4-ter is one shorted-or-misoriented chip-plus-adapter. **Note the seating subtlety the T+4c bench surfaced:** a chip seated in the *wrong* rows of the ZIF socket may never have its VCC pin connected — so it draws no current, the device stays enumerated, and flashrom merely reports `No EEPROM/flash device found` (a STAGE-4-looking symptom). Moving the adapter to the *correct, powered* rows wires VCC for the first time — and *that* is when the fault bites. **A failure that appears only after re-seating the adapter into the correct socket position is the signature of STAGE 4-ter.**

> **⚠ T+4c dispatch 2 — the cause is NOT necessarily a hard solder bridge.** The bench measured the bare adapter's VCC↔GND with the meter in continuity mode and it read **open** — no hard bridge. **That does not exonerate the adapter or chip.** Three mechanisms produce this exact brown-out, and only one of them shows up on a static VCC↔GND meter test:
> - **Reverse-polarity orientation** — if the SOIC-DIP adapter is seated 180° in the ZIF socket (or the chip soldered onto the adapter rotated), the CH341A drives its switched 3.3 V into the chip's **GND pin** and ties the chip's **VCC pin to socket ground.** The chip's internal substrate / ESD-protection diodes are then forward-biased and conduct hard — a near-short *that exists only when the socket is powered.* On a static meter test of the bare unpowered adapter, VCC↔GND reads **perfectly open** — the diodes are not conducting, there is no metal bridge. The meter cannot catch this. **This is now a leading candidate.**
> - **Current-leaky / latch-up-damaged chip** — a chip cooked by desolder heat or ESD can draw far more supply current than the AT45DB041E's normal few-mA, enough to brown out the weak CH341A LDO. Like reverse-polarity, it draws that excess current **only when powered** and reads **open** VCC↔GND statically.
> - **Hard solder bridge / partial resistive short** — a metal VCC↔GND path on the adapter. *This* is the one a static meter test catches: a hard bridge beeps; a partial short shows tens-to-low-hundreds of ohms. The bench's open continuity reading **excludes a hard bridge** but does **not** exclude a partial resistive short below the meter's beep threshold — see Step 4-ter-c.
>
> Therefore STAGE 4-ter step order is revised: **verify orientation FIRST** (free, most likely), and only then trust meter-based conclusions.

> **⚠ T+4c dispatch 2 — step order revised.** Steps now run **orientation re-verify → meter test → inspection → cooked-chip discriminator → recover**, cheapest-and-most-likely first. Orientation re-verification is free and is the leading candidate, so it comes before any meter-based conclusion. The bench has already confirmed the CH341A board itself is undamaged (it recovered cleanly with the socket empty), so step 4-ter-a below is a state-capture confirmation, not the open question it was in dispatch 1.

**Step 4-ter-a — [Operator + Neo] get the CH341A off USB and confirm the state (do this first).**
The CH341A must come off USB so it stops the brown-out / re-enumeration loop and so the adapter can be worked on safely. Neo should already have instructed this; if not, **unplug the CH341A from USB now.** Then capture the state:

```bash
# 4ter-a. [Neo via MCP] confirm the CH341A is no longer enumerating
lsusb | grep -i "1a86:5512" || echo "CH341A NOT on the bus"
dmesg | grep -iE "usb|xhci|enumerate|error -71" | tail -20
```

A `dmesg` tail showing `device not accepting address`, `error -71`, `unable to enumerate USB device` confirms the brown-out / enumeration-loop signature. (Per the T+4c dispatch-2 facts, this loop is cleared by **emptying the ZIF socket** — removing the adapter — then re-plugging; re-plugging with the shorted adapter still seated does not clear it.)

**Step 4-ter-b — [Operator — physical action] verify pin-1 orientation of the adapter in the ZIF socket. FIRST — this is free and the leading candidate.**
*Tools: eyes, good light, the adapter, the chip datasheet or a photo.* A SOIC-DIP adapter seated 180° in the ZIF socket — or a chip soldered onto the adapter rotated — drives the CH341A's 3.3 V into the chip's GND pin: the chip's internal protection diodes conduct hard and brown out the CH341A. This reads **open** on a static VCC↔GND meter test, so the meter will *not* catch it — orientation must be checked by eye. The full orientation-verification procedure — chip pin-1 mark, adapter silkscreen, the CH341A 25-series socket corner — is in **Section H.2a**. Run Section H.2a now, then return here.

In short: confirm the chip's pin-1 dot, confirm the adapter's pin-1 mark, confirm where pin 1 must sit in the CH341A's 25-series ZIF rows, and confirm all three agree. If orientation was wrong, **correct it and go straight to Step 4-ter-e (recover and retry)** — do not run the meter test first; a wrong orientation fully explains the brown-out and is free to fix.

**Step 4-ter-c — [Operator — physical action] VCC↔GND test with a multimeter — resistance mode, not just continuity.**
*Tools: a multimeter. CH341A unplugged from USB; adapter removed from the ZIF socket.* Run this only if orientation (4-ter-b) checked out correct. **The full operator procedure — exact AT45DB041E pinout, what readings mean healthy vs. short vs. partial short, adjacent-pin checks, adapter inspection, the cooked-chip discriminator, CH341A recovery — is in Section H.** Run Section H now, then return here.

In short: probe **VCC against GND on the chip** (AT45DB041E SOIC-8: **VCC = pin 7, GND = pin 4** — verify against the chip datasheet / adapter silkscreen, see Section H). Use the meter's **ohms range, not just the continuity beep** — the beep threshold is only ~30–50 Ω and would miss a 50–300 Ω partial short. A reading **near 0 Ω** is a dead bridge; **tens-to-low-hundreds of ohms** is a partial resistive short — both are STAGE 4-ter. An **open / kΩ-and-up reading** means no metal short — but per the dispatch-2 note above, this does *not* clear a cooked chip; proceed to the cooked-chip discriminator (Section H.3 step 5).

**Step 4-ter-d — [Operator — physical action] clear the short, or run the cooked-chip discriminator.**
Per Section H: inspect the adapter under light/magnification for solder bridges (most common at the close-pitch SOIC pads), clear any bridge with flux + solder braid, reflow cold joints. If the meter test was open, the brown-out is most likely orientation (already handled in 4-ter-b) or a cooked chip — run the cooked-chip discriminator (Section H.3 step 5): a known-good spare AT45DB041E on a known-good adapter in the verified-correct orientation. Spare works ⇒ the original chip is cooked, abandon it. Spare also browns out ⇒ the fault is socket-side or CH341A-side.

**Step 4-ter-e — [Operator + Neo] recover the CH341A and re-verify.**
Once orientation is corrected and/or the short is cleared (adapter NOT yet re-seated), re-plug the CH341A into USB and confirm it recovered:

```bash
# 4ter-e. [Neo via MCP] confirm the CH341A re-enumerated cleanly
lsusb | grep -i "1a86:5512"          # must show 1a86:5512 again
dmesg | grep -iE "usb|xhci" | tail -10   # a clean 'new full-speed USB device' line, NO error -71 / no loop
```

**BRANCH:**
- `lsusb` shows `1a86:5512` again and `dmesg` shows a single clean enumeration with no `error -71` and no loop → the CH341A has recovered (this is expected — the bench has confirmed the board is undamaged). Now seat the adapter in the **correct** ZIF rows **in the verified-correct orientation** and go to **STAGE 3** to re-probe, then **STAGE 5**.
- STAGE 3 still browns out the CH341A with the adapter correctly oriented and the meter test open → the chip is the most likely remaining cause → run the cooked-chip discriminator (Step 4-ter-d / Section H.3 step 5) with a spare.
- The VCC↔GND short persists even with the chip lifted off the adapter pads / on a bare known-good adapter → the **chip is cooked** (Section H discriminator) → abandon this chip, use a spare loose AT45DB041E.

**GO / NO-GO for STAGE 4-ter:**
- **GO** — orientation verified correct, the VCC↔GND test reads open (or any found short cleared), the CH341A re-enumerates cleanly as `1a86:5512`, and (chip on the correctly-oriented adapter, correct rows) STAGE 3 detects the chip → **STAGE 5**.
- **NO-GO** — a spare chip on a known-good adapter *also* browns out the CH341A in the verified-correct orientation → the fault is no longer the chip/adapter; treat the CH341A or socket as suspect (swap board), and if that fails, fall back as in STAGE 4-bis NO-GO. **Workshop note:** because every attendee who mounts their own chip can hit a bridge or a 180° orientation error, the facilitator should pre-screen each adapter — orientation by eye plus the Section H VCC↔GND test — *before* the attendee plugs in. It is a five-second check that prevents a cascade of CH341A brown-outs across the room.

### STAGE 5 — The hardware read (final stage; clear success criterion)

Chip detected in Stage 3. Now produce the dump.

```bash
# 5a. full chip read into dump.bin, with verify-on-read for integrity
sudo flashrom -p ch341a_spi -c AT45DB041D -r dump.bin

# 5b. report the actual size flashrom produced
ls -l dump.bin
stat -c '%s bytes' dump.bin

# 5c. eyeball the start of the dump — look for the page-header marker
xxd dump.bin | head -20

# 5d. sanity check: a faithful dump is NOT uniformly 0xFF and NOT uniformly 0x00
xxd dump.bin | grep -vE '^[0-9a-f]+: (ffff ){7}ffff ' | head -5
```

**SUCCESS CRITERIA (all must hold):**
1. `5a` ends with **`VERIFIED`** (or `... done.` with no error) — flashrom completed the read with no transaction errors.
2. `5b` size is a **consistent multiple of the page size flashrom reported in Stage 3** — expect **≈540,672 bytes** if the chip is in default 264-byte mode, or **≈524,288 bytes** if it is in power-of-2 mode. **Either is a valid dump** — record which, this is the ground-truth number for SMYTH (Section A.4).
3. `5c` shows real structure — the workshop expects byte **`FD`** at offset `0x0000` of a user-code page (per the handout). At minimum the dump must not be uniformly `FF` or `00`.
4. `5d` returns at least some non-all-`FF` lines — i.e. the chip has real content.

**BRANCH:**
- All four hold → **DONE. The CH341A + flashrom toolchain is confirmed on real hardware.** Report the exact byte size back so the workshop files can be corrected. The Section E standalone package is now unblocked to be built in the next phase.
- `5a` errors mid-read ("transaction error", "read failed") → re-seat clip, retry once; if it recurs → Stage 4 voltage/board checks; chronic → Section D fallback.
- `5b` size is "512 kB" but `5c` shows the data looks shifted/garbled vs. the expected `FD`-at-`0x0000` layout → the chip may be in an unexpected page mode, OR the `-c AT45DB041D` geometry mismatched a 041E in default mode → re-run `5a` **without** `-c` and let flashrom auto-detect; compare. If a future flashrom lists `AT45DB041E` separately, use `-c AT45DB041E`.
- `5c` is uniformly `FF` → clip not contacting (Stage 4 step 1–2) — *not* a tool problem.
- `5c` is plausible hex but `FD` is not at `0x0000` → may simply be a non-user-code page; per the handout, jump ahead one page and re-check. This is a *content/layout* question for the workshop, not a toolchain failure — the dump itself is good.
- `5a` fails with **`Couldn't open device` / `Programmer initialization failed`**, or the CH341A **drops off `lsusb`** mid-read, with the chip on a **SOIC-to-DIP adapter / breakout** and **no `LIBUSB_TRANSFER_ERROR` flood** → a **VCC↔GND short** has browned out the CH341A → **STAGE 4-ter** (Section H). A short can be intermittent — re-seating or thermal movement can make a marginal bridge connect — so this can surface even after Stage 3 detected the chip once.

---

## C. IMHEX RECOMMENDATION

**Use the official prebuilt `.deb` release. Do NOT build ImHex from the downloaded `ImHex-master/` source.**

Rationale: ImHex is a large C++ project with a `vcpkg`-based dependency tree (it pulls and compiles many libraries). A source build needs a current CMake, a C++23-capable toolchain, and a long compile — this is almost certainly where the operator's earlier install attempt stalled. The ImHex project ships **official prebuilt `.deb` packages and an AppImage** for exactly this reason. There is no workshop benefit to a source build.

### Recommended path — official `.deb` (Kali / Debian)

```bash
# C1. download the current ImHex .deb (do this at home, with network)
#     get the URL from the GitHub releases page:
#       https://github.com/WerWolv/ImHex/releases/latest
#     pick the file named like:  imhex-X.YY.X-Ubuntu-24.04-x86_64.deb

# C2. install it (pulls dependencies from the Kali repos)
sudo apt-get install -y ./imhex-*.deb

# C3. verify
which imhex && imhex --version
```

If `apt-get install ./file.deb` complains about dependencies on Kali, install with `sudo dpkg -i ./imhex-*.deb` then `sudo apt-get -f install` to pull the missing deps.

### Fallback — AppImage (no install, fully portable, offline-friendly)

```bash
# from the same releases page, download:  imhex-X.YY.X-x86_64.AppImage
chmod +x imhex-*.AppImage
./imhex-*.AppImage
```

The AppImage is the **best offline-at-campground choice** for participants: a single self-contained executable, no root, no dependency resolution. Vendor it on the facilitator's USB stick.

### Lightweight alternatives (already named in the workshop files)

- **`xxd`** — built into Kali (`/usr/bin/xxd`, confirmed). Zero install. `xxd dump.bin | less` is entirely sufficient for the workshop's "find `FD`, read byte offsets" task and is what the Facilitator Guide already uses for its pre-session test read. **For a 90-minute workshop, `xxd` alone covers every required step.** ImHex is a *nice-to-have* GUI for participants who want one, not a requirement.
- **`hexdump -C dump.bin | less`** — also built in; equivalent to `xxd`.
- **`HxD`** — Windows-only; fine for Windows participants but outside the Kali toolchain.

**Recommendation:** Standardize on **`xxd`** as the baseline (zero setup, already present), and offer the **ImHex AppImage** from the USB stick to anyone who wants a GUI. Skip the `.deb` unless the facilitator wants ImHex permanently installed on the reference laptop.

---

## D. AFFORDABLE-ALTERNATIVES RANKING (if the CH341A path fails)

Use this if Stage 4 exhausts clip-contact troubleshooting on multiple boards and chips, **or** if STAGE 4-bis cannot make the CH341A's USB transport reliable on a modern xHCI host.

> **Re-ranked after the T+4b bench / Section F.** The CH341A's USB 1.1 full-speed transport is the root of the bench failure (Section F), and that failure is likely to recur on participants' modern xHCI-only laptops (Section G). The **Xgecu T48 is a USB 2.0 high-speed device and is structurally immune to that failure** — so it is promoted to **Rank 1 of the fallbacks**. The "second CH341A board" option drops, because a different CH341A unit does not fix a USB-topology incompatibility.

| Rank | Option | Rough USD | Notes |
|---|---|---|---|
| 1 | **Xgecu T48 + `minipro` (Linux/Kali)** | **$30–55** | **Primary fallback.** T48 is a **USB 2.0 high-speed** device — natively scheduled by xHCI, **immune to the full-speed-on-xHCI failure (Section F)**. Open-source `minipro` (David Griffith fork) runs it natively on Kali; device DB includes AT45DB DataFlash. CLI: `minipro -p AT45DB041E -r dump.bin`. T48 support in `minipro` is **newer** — bench-test before the workshop. The reliability choice for a bring-your-own-laptop room. |
| 2 | **Xgecu T48 + Xgpro (Windows)** | **$30–55** (same hardware) | The programmer named in the original `PhysAccessDigiLies` writeup. Xgpro GUI supports **`AT45DB041E`** by name — select it, click Read. Xgpro is **Windows-only** — Windows-laptop-only at the workshop. Most vendor-certain path; same robust USB-2 hardware as Rank 1. |
| 3 | **CH341A + 3.3 V adapter board** | board $7 + adapter **$2–5** | Addresses the *5 V I/O* concern (A.5) only — **does not address the Section F USB-transport failure.** Still needs the USB 2.0 hub (Section G) on a modern host. A *fix for a different problem*; keep in mind but it is not the answer to `LIBUSB_TRANSFER_ERROR`. |
| 4 | **Raspberry Pi + flashrom `linux_spi`** | $15–40 (if no Pi on hand) | Wire the chip to the Pi's SPI header, `flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=2000`. 3.3 V-native and avoids the CH341A entirely, but adds an SBC per station — not workshop-scalable. Listed for completeness. |

**Guidance:** The **primary workshop plan remains CH341A + flashrom + a USB 2.0 hub per station** (Section G, Plan A) — that keeps the workshop cheapest *if* STAGE 4-bis confirms the hub fix on real hardware. **If STAGE 4-bis does not cleanly resolve it — or if the facilitator wants to eliminate the USB-topology variable across 20 unknown laptops — switch the whole workshop to the Xgecu T48 (Rank 1/2 here).** The T48's high-speed USB structurally avoids the failure that blocked the bench. Switching to the T48 means the Facilitator Guide and Handout command steps must be rewritten for `minipro` (Linux) or Xgpro (Windows) — a SMYTH file-update task.

---

## E. ONE-COMMAND STANDALONE PACKAGE — DESIGN OUTLINE ONLY

> **Not built in this phase.** Building is gated on Stage 5 succeeding on real hardware (so the package vendors a *confirmed* toolchain, not a hypothesis). This section is the blueprint for the later build phase.

### E.1 — Goal

A single directory the operator copies to any Kali/Debian laptop (or hands to a participant), runs **one command**, and ends up with a working, **offline-capable** AT45DB041E read toolchain — no network needed at the campground.

### E.2 — Proposed layout

```
toorcamp-flash-toolkit/
├── setup.sh                     # the one command: ./setup.sh
├── README.md                    # what it does, what it installs, how to undo
├── USAGE.md                      # the read procedure (mirrors Section B Stage 5)
├── vendor/
│   ├── debs/                     # pinned .deb files for fully-offline install
│   │   ├── flashrom_1.6.0-3_amd64.deb
│   │   ├── libftdi1-2_*.deb       # flashrom runtime deps, resolved + pinned
│   │   └── ...                    # (xxd ships in vim-common; vendor if not present)
│   ├── imhex/
│   │   └── imhex-X.YY.X-x86_64.AppImage   # GUI hex editor, portable, no install
│   └── CHECKSUMS.sha256          # sha256 of every vendored file; verified by setup.sh
├── udev/
│   └── 99-ch341a.rules           # the CH341A permissions rule
└── verify/
    └── self-test.sh              # post-install self-verification
```

> **Deliberate design choice — vendor flashrom, NOT ch341prog.** The package ships flashrom because Section A proved `ch341prog` cannot read this chip. The downloaded `ch341prog-master/` source is *not* included.

### E.3 — `setup.sh` flow (one command)

1. **Preflight** — confirm Kali/Debian + x86_64; confirm root or prompt for `sudo`.
2. **Integrity** — verify every `vendor/` file against `CHECKSUMS.sha256`; abort on mismatch.
3. **Dependency install** — *offline first*: `dpkg -i vendor/debs/*.deb`. If that leaves unmet deps and network *is* available, `apt-get -f install`; if offline, fail loudly listing the missing packages so they can be vendored. (flashrom has few runtime deps — `libusb-1.0`, `libftdi1` — all pin-able.)
4. **udev rule** — install `udev/99-ch341a.rules` to `/etc/udev/rules.d/`, reload (`udevadm control --reload-rules && udevadm trigger`).
5. **ImHex** — copy the AppImage to `~/.local/bin/imhex` (or leave in place), `chmod +x`; symlink optional.
6. **Self-verification (the critical step)** — run `verify/self-test.sh`:
   - `flashrom --version` parses and is ≥ 1.6.0
   - `flashrom -p list` includes `ch341a_spi`
   - `flashrom -L | grep AT45DB041` returns a row
   - if a CH341A is plugged in: `lsusb` shows `1a86:5512`, and optionally `flashrom -p ch341a_spi` reaches the probe stage
   - `xxd` and the ImHex AppImage are executable
   - Print a green **READY** / red **NOT READY (reason)** summary.
7. **Print next step** — echo the exact Stage 5 read command (`flashrom -p ch341a_spi -c AT45DB041D -r dump.bin`).

### E.4 — Cross-platform / robustness notes

- **Local-first:** the vendored `.deb` + AppImage path means a campground laptop with zero network still installs cleanly. Network is only a *fallback* for unmet deps.
- **Reversible:** ship an `uninstall.sh` (or document `apt-get remove flashrom`, `rm /etc/udev/rules.d/99-ch341a.rules`).
- **Pin everything:** exact `.deb` versions + checksums so the package is reproducible and tamper-evident; never `apt-get install <name>` against a live moving repo inside the package.
- **OS scope:** target Kali/Debian x86_64 (the workshop's stated environment). A note in `README.md` should point macOS users at Homebrew `flashrom` and Windows users at the Xgecu/Xgpro fallback — do not try to make one `setup.sh` cover all three; keep the platform-specific layer thin (Systems Engineer operating principle).

### E.5 — Guide structure to ship alongside

- **`README.md`** — one-paragraph "what this is", the single `./setup.sh` command, what it installs, how to undo, offline behavior.
- **`USAGE.md`** — the participant-facing read procedure: seat clip → `flashrom -p ch341a_spi -c AT45DB041D -r dump.bin` → check size → `xxd dump.bin | less` or open in ImHex → success criteria. This is Section B Stage 5 distilled to participant register (a SMYTH task — keep it consistent with the corrected handout).
- **Troubleshooting appendix** — the Stage 4 checklist condensed.

### E.6 — Build-phase preconditions (gates)

Do not build E until:
1. **Stage 5 succeeds on the operator's real AT45DB041E** — confirms flashrom + `-c AT45DB041D` is the right invocation and yields a faithful dump.
2. **The real dump size is recorded** (≈528 KB vs ≈512 KB per A.4) — so `USAGE.md` states the true success criterion.
3. **The CH341A voltage question is settled** (A.5) — if a 3.3 V adapter is needed, the package README must say so.

---

## F. ROOT-CAUSE DIAGNOSIS — `LIBUSB_TRANSFER_ERROR` ON THE CH341A (T+4b bench)

> **Added after the T+4b bench run.** STAGE 0 passed all five baseline checks; STAGE 3 then failed — but **not** with the clip-contact symptom Section B Stage 4 was written for. It failed with a USB-transport symptom. This section is the diagnosis; Section B's **STAGE 4-bis** is the remediation; **Section G** is the workshop-equipment fallout.
>
> **⚠ REVISED — new fact from the operator.** The first cut of this section (F.1–F.4 below, written before the operator disclosed how the chip was wired) attributed the failure to the full-speed-on-xHCI USB-transport interaction with ~85% confidence. The operator then reported that the chip is being read **in-circuit on a live, self-powered board**. That fact materially changes the diagnosis. **F.0 below is the revised verdict and takes precedence over F.2.** F.1–F.4 are retained as the still-valid analysis of the USB-transport candidate, which is now the *second* hypothesis rather than the leading one.

### F.0 — REVISED VERDICT: in-circuit reading on a live, dual-powered board is the leading suspect

**The new fact.** The AT45DB041E is **still soldered to the access-control lock's PCB**. The operator has the lock's **own battery pack plugged in and energizing that board**, and measured **~3.3 V on a flash-chip pin** — that is the lock's supply reaching the chip. Meanwhile the CH341A's SOP8 clip **also drives 3.3 V VCC** onto the same pin. So during the failed probe there were **two independent 3.3 V sources tied together on the chip's VCC rail**, and the rest of the lock board — critically its **MSP430 microcontroller, which is the board's normal SPI master to this DataFlash** — was **powered and live on the shared SPI bus** while flashrom tried to drive that bus through the CH341A.

This was **not known** when F.1–F.4 were written. It introduces two failure mechanisms that the original USB-transport diagnosis did not consider, and at least one of them explains the bench symptoms *better* than the xHCI hypothesis does.

**Mechanism 1 — power-rail conflict / back-feed browns out the CH341A and resets its USB PHY.** Two low-impedance 3.3 V sources wired in parallel never sit at exactly the same voltage. The higher one **back-feeds current into the lower** through whatever the difference is divided by the (very low) combined source impedance. Two consequences, both bad:

- The CH341A's on-board 3.3 V is a small, weak regulator (the "black board" derives it cheaply from USB 5 V). Asking it to *also* source current into the lock battery and into a whole live PCB — the MSP430, pull-ups, decoupling-cap inrush, indicator LEDs, every other component on that board — is a load it was never sized for. The CH341A draws its own power from the USB port; if its 3.3 V rail collapses or its input current spikes, the **CH341A itself browns out**. A USB device that briefs out **resets its USB PHY and drops off the bus** — which is *exactly* the **repeated disconnect / re-enumeration (device 6 → 7 → 8)** the bench saw. A USB-transport mismatch (the xHCI hypothesis) does **not** by itself power-cycle a device; a power problem does. The re-enumeration cycling is the single strongest tell, and it points at power, not at transaction translators.
- Conversely, if the **lock battery is the higher source**, it pushes current back into the CH341A's VCC pin and into its 3.3 V regulator's *output* — back-feeding a regulator from its output is an abnormal, unspecified condition that can latch the regulator up, trip protection, or hold the CH341A in a marginal brown-out state. Either direction of imbalance destabilises the CH341A's own supply.

When the CH341A's supply is unstable, its USB engine cannot reliably complete **bulk-OUT** transfers — the controller NAKs/errors, libusb reports `LIBUSB_TRANSFER_ERROR`, and on the next run the device has dropped and come back as a new device number so flashrom fails even earlier at `config_stream`. **This reproduces the entire observed symptom set — the `LIBUSB_TRANSFER_ERROR` flood, the init-stage degradation on retry, AND the re-enumeration cycling — from a single cause.** The xHCI hypothesis explains the first two well but explains the re-enumeration only weakly (as an endpoint-wedge side effect).

**Mechanism 2 — the live MSP430 is a second SPI master fighting for the bus.** The AT45DB041E's CLK, MOSI (SI), MISO (SO) and CS lines are wired on the lock PCB to the MSP430, which is that DataFlash's normal SPI master. With the board powered, the MSP430 is **running its firmware** and may at any time drive CLK, drive MOSI, or assert/deassert CS — actively, as a push-pull output. The CH341A is simultaneously driving those same lines. **Two push-pull outputs fighting on one net is bus contention:** one driving high while the other drives low creates a near-short through both output stages, pulls the line to an indeterminate mid-level, and injects large current transients onto the shared 3.3 V rail. That contention:

- **corrupts every SPI transaction** — flashrom's command bytes and the chip's response are both mangled, so the chip never answers a JEDEC ID correctly even if a transfer *does* complete; and
- **feeds back into Mechanism 1** — the contention current spikes load the same weak CH341A rail, deepening the brown-out.

The MSP430 may also be holding the DataFlash's CS **asserted** for its own use, in which case the chip is listening to the MSP430 and ignoring the CH341A entirely; or holding **CLK** in a state that the CH341A cannot override. The lock could also be actively *using* the flash (it is an access-control device — it reads user codes from this exact chip), so the contention is not hypothetical.

**Where each mechanism sits in the failure stack.** This matters for reading the symptoms:

- **Mechanism 1 (power) is *upstream* of the USB-layer error.** It is the same layer the `LIBUSB_TRANSFER_ERROR` lives at — it directly produces that error and the re-enumeration. It is the one that explains the bench observations.
- **Mechanism 2 (SPI contention) is *downstream* of the USB layer.** Pure SPI contention, on its own, would let the USB link stay healthy and instead produce flashrom's `No EEPROM/flash device found` or a garbled/`0xFF` dump — a STAGE-4-style symptom, not a `LIBUSB_TRANSFER_ERROR`. The bench did **not** primarily show that; it showed the USB-layer error. **So Mechanism 1 is doing the visible damage.** Mechanism 2 is still real and would block a correct read even if the USB link were fixed — but it is a *second* problem waiting behind the first, not the cause of the `LIBUSB_TRANSFER_ERROR`. Both feed the same shared-rail current transients, so they are not fully independent.

**Competing or contributing? — revised confidence-ranked verdict.**

| Rank | Hypothesis | Confidence | Explains the re-enumeration? | Explains `LIBUSB_TRANSFER_ERROR`? |
|---|---|---|---|---|
| **1** | **In-circuit dual-power conflict browning out the CH341A** (Mechanism 1) | **~60%** | **Yes — directly.** A browning-out device resets its PHY and drops off the bus. | **Yes — directly.** An unstable supply cannot complete bulk-OUT transfers. |
| 2 | Full-speed-on-xHCI / missing transaction translator (original F.2) | ~30% | Weakly — only as an endpoint-wedge side effect. | Yes — this is the classic signature for it. |
| 3 | Marginal USB cable / flaky CH341A board | ~10% | Yes — a flaky board re-enumerates. | Yes — intermittent bulk errors. |

They are **not mutually exclusive** — a modern xHCI-only laptop *plus* an in-circuit dual-power setup could both be contributing, and the bench laptop genuinely is xHCI-only. But the **re-enumeration cycling tips the balance decisively toward Mechanism 1**: the original xHCI diagnosis had to explain the disconnect/reconnect as a secondary endpoint-wedge effect (F.2 point 3), which was always its weakest point. The dual-power brown-out explains it as a *primary* effect. **The single most likely cause is the live, self-powered board feeding a second 3.3 V source onto the CH341A's clip rail.**

Crucially, **the test that discriminates between hypotheses 1 and 2 is free**: disconnect the lock's battery (and ideally read the chip out of circuit). If the failure clears, it was the in-circuit dual-power situation — no USB hub needed, no money spent. If it persists with the CH341A as the *only* power source and nothing else on the bus, *then* the xHCI hypothesis is back in play and the USB-2 hub is the next move. **This is why STAGE 4-bis is reordered (below) to put the power-isolation check first.**

### F.1 — What the bench actually showed

| Observation | Detail |
|---|---|
| STAGE 3 probe | ~700 repetitions of `cb_out: error: LIBUSB_TRANSFER_ERROR` + `ch341a_spi_spi_send_command: Failed to write 36–40 bytes`, then `No EEPROM/flash device found`, then `enable_pins: Failed to write 4 bytes` / `Could not disable output pins`. |
| Clean retry | **Degraded** — did not even reach the probe: `config_stream: Failed to write 3 bytes` → `Could not configure stream interface` → `Programmer initialization failed`. |
| Enumeration | CH341A *does* enumerate — `lsusb` shows `1a86:5512 ... CH341 in EPP/MEM/I2C mode`. It has re-enumerated repeatedly (device 6→7→8); dmesg shows `USB disconnect` → `new full-speed USB device` cycles. |
| Kernel driver | **NONE** on the interface. No `ch341`/`i2c-ch341`/`spi-ch341` modules loaded. flashrom has uncontested ownership. |
| USB topology | Device runs at **full-speed (12 Mbit/s)** on an **`xhci_hcd` root port**. Host has only two xHCI root hubs (Bus 001 480M, Bus 002 5000M) — **no EHCI / USB-2-only companion controller**. No external hub anywhere in the path. |
| USB descriptor | `bcdUSB 1.10` (the CH341A is a **USB 1.1 device**), `bMaxPacketSize0 8`, endpoints EP2-IN/EP2-OUT bulk + EP1-IN interrupt, `MaxPower 100mA`. |
| Power management | Device `power/control = on` — **autosuspend already disabled at the device.** |
| dmesg | No kernel-level USB transfer errors; the failure is in libusb's async transfer layer. (Unrelated `pcieport ... RxErr` PCIe noise is a different link — ignore.) |

### F.2 — Diagnosis

**The failure is a USB-transport incompatibility between a USB 1.1 full-speed device and an xHCI-only host, manifesting on bulk transfers.** Reasoning, in order:

1. **Enumeration succeeds, bulk fails.** The device enumerates cleanly — `lsusb` and the full descriptor read both work. Enumeration uses **control transfers** on endpoint 0. Every failing operation — `ch341a_spi_spi_send_command` (write SPI command), `config_stream` (configure the CH341A's stream interface), `enable_pins` — is a **bulk-OUT** transfer to EP2-OUT. **Control transfers work; bulk-OUT transfers fail.** This split is the signature of a host-controller transaction-handling problem, not a dead device, not a power problem, not a cable that is simply open.

2. **Full-speed device on a bare xHCI root port.** The CH341A is `bcdUSB 1.10` and is running at **full-speed (12 Mbit/s)**. xHCI host controllers do not natively schedule low-/full-speed traffic the way the old EHCI+companion-controller model did. On a healthy USB-2 tree a **Transaction Translator (TT)** — located in any USB 2.0 *hub* — bridges the host's high-speed bus to the full-speed device, issuing **split transactions**. On this laptop the CH341A is plugged **directly into an xHCI root port with no USB-2 hub in the path**, so **there is no TT**. The xHCI root hub must itself handle the full-speed split transactions for the bulk endpoints, and on this controller + firmware + libusb-async combination it does not do so reliably — every bulk-OUT errors with `LIBUSB_TRANSFER_ERROR`. flashrom's `ch341a_spi` driver is known to be sensitive here: it issues many small async bulk transfers, and the upstream flashrom CH341A documentation and multiple user reports describe exactly this `LIBUSB_TRANSFER_*` / "Failed to write N bytes" pattern on USB 3.x / xHCI ports, with the standard advice being "use a USB 2.0 port / hub."

3. **The retry degrading to an init-stage failure** (`config_stream: Failed to write 3 bytes` before the probe even starts) and the **repeated disconnect/reconnect cycling** (device 6→7→8) are consistent with the controller leaving the device's endpoints in a wedged state after a failed transfer burst — each failed run leaves the link in a worse state until a re-enumeration resets it. This is *behavioural confirmation* of a transport-layer fault, not an intermittent SPI-side contact problem (a bad clip does not make the device drop off the USB bus).

4. **The error lives in libusb's async layer, not the kernel.** dmesg shows no kernel USB transfer errors — the kernel hands the transfer to userspace and libusb's async completion reports `LIBUSB_TRANSFER_ERROR`. That places the fault precisely at the host-controller ↔ full-speed-device transaction boundary, which is what a TT exists to mediate.

**⚠ Confidence — SUPERSEDED.** As originally written, this section rated the full-speed-on-xHCI interaction the dominant cause at ~85%. **That figure assumed the CH341A was the chip's only power source and the SPI bus was otherwise quiet** — which the operator's later disclosure (F.0) showed was false. With the in-circuit dual-power fact in hand, this hypothesis is **downgraded to ~30% and to second place** behind the dual-power brown-out (Mechanism 1, F.0). The reasoning in F.2 points 1–4 remains *technically sound for an out-of-circuit CH341A on an xHCI host* — it is a real and documented failure mode, and the bench laptop genuinely is xHCI-only — but it is no longer the leading explanation for *this* bench failure, because it explains the repeated re-enumeration only weakly (point 3) whereas Mechanism 1 explains it directly. **Read F.0 for the operative verdict.** This hypothesis comes back to the front only if the failure persists after the lock's battery is disconnected and the chip is the CH341A's sole load (STAGE 4-bis confirms this with a free test).

### F.3 — Causes ruled OUT

- **Driver conflict — ruled out.** No kernel module claims the interface (`driver: NONE`); flashrom has uncontested ownership. There is nothing to unbind.
- **USB autosuspend — ruled out.** The device's `power/control` is already `on`; autosuspend cannot be putting it to sleep mid-transfer.
- **SPI clip / chip contact (open / poor contact) — not relevant to *this* error.** A clip that is simply *not making contact* produces flashrom's "No flash device found" or an all-`0xFF` dump — a *SPI-bus* symptom, downstream of the CH341A. `LIBUSB_TRANSFER_ERROR` / `config_stream: Failed to write 3 bytes` is a *USB-bus* symptom **upstream of the SPI bus** — it occurs before any SPI command reaches the chip, and `config_stream`/`enable_pins` do not even touch the chip. Re-seating the clip cannot fix the `LIBUSB_TRANSFER_ERROR`. ⚠ **Note the distinction from F.0:** "poor clip *contact*" is ruled out, but *what the clip is connected to* — a live, dual-powered board — is **not** ruled out and is now the leading suspect (F.0 Mechanism 1). The clip itself is fine; the problem is the energised PCB on the other side of it.
- **Permissions — ruled out.** A permissions fault is `Could not open device` / `Access denied` at open time; here the device opens and enumerates, and only bulk transfers fail.

### F.4 — Causes still OPEN (and where Section B addresses them)

- **🔴 In-circuit dual-power conflict (NEW — now the leading suspect).** Disclosed by the operator after F.1–F.3 were written; full analysis in **F.0**. The lock's battery and the CH341A's clip both source 3.3 V onto the chip's VCC rail, and the live MSP430 contends on the SPI bus. The discriminating test is **free** — disconnect the lock battery / read out of circuit — and is the new **first step of STAGE 4-bis** (step 4-bis-a, below).
- **The USB cable.** A marginal/long cable produces intermittent bulk errors indistinguishable from the xHCI problem. Cheap to exclude — STAGE 4-bis step 4-bis-f.
- **CH341A board quality.** The repeated re-enumeration *can* also indicate a flaky board, not only a transport mismatch or a brown-out. A second board is the control — STAGE 4-bis step 4-bis-f.
- **The specific xHCI controller / firmware.** Whether *this* laptop's xHCI is unusually bad, or whether every modern xHCI host shows this, is not yet known from one bench — and is only worth investigating *after* the in-circuit dual-power cause (F.0) is excluded. The powered USB 2.0 hub (STAGE 4-bis step 4-bis-d) sidesteps the question by reinserting a TT, which is why it is both the fix *and* the diagnostic confirmation **for the xHCI hypothesis specifically**. **This open question matters for Section G** — but only if the failure survives the free power-isolation test; if disconnecting the lock battery clears it, the xHCI question is moot for the workshop.

---

## G. WORKSHOP-EQUIPMENT & PROCEDURE IMPACT ASSESSMENT — the consequential part

> **⚠ HISTORICAL (T+4d/T+4e supersession).** Section G was written at T+4b/T+4c when the workshop arc was assumed to be **CH341A + out-of-circuit ZIF**. T+4d (research notes surfaced) and T+4e (bench validation) overturned that assumption: the research's actual method is **in-circuit SOIC-8 clip via ZIF ICSP on a T48**, and the T+4e bench validated that path end-to-end (`T+4e-DUMP-VALIDATION-REPORT.md`). The workshop's primary toolchain is now **T48 + minipro + in-circuit SOIC-8 clip + Kali** per `T48-KALI-PLAN.md`. The CH341A is **still** a candidate for per-attendee tooling pending the Phase 6 / T+4g CH341A live-chip re-test on a non-cooked spare — and that re-test will likely also be in-circuit. **Read Section G as the historical record of the procurement / procedure decision evolution** — the analysis was correct given the CH341A's power-rail constraint, but the constraint was tool-specific, not methodology-required. The CH341A-specific equipment analysis (USB 2.0 hub, A.5 5V issue, etc.) below remains valid **for the CH341A re-test scenario**; the "out-of-circuit is the methodology" claim does not.

> **This is the part that matters for ToorCamp.** The bench is the operator's own (older) GL752VW laptop. Two candidate causes are in play (Section F): the in-circuit dual-power conflict (F.0, leading) and the full-speed-on-xHCI USB transport (F.2, second). They have *different* workshop consequences — the first is a **procedure** change (how chips are read), the second is an **equipment** change (a USB-2 hub per station). This section covers both, because the workshop files must be written for whichever the bench confirms.

### G.0 — Reading methodology: in-circuit vs. out-of-circuit (the procedure decision)

> **⚠ CORRECTION (T+4d/T+4e supersession).** The paragraph below contains the load-bearing factual error this whole document was built on: *"a ZIF socket means the chip was removed from the lock and read out of circuit."* That inference was **wrong.** The research notes (`PhysAccessDigiLies_PhrackSubPiano.txt`, surfaced T+4d) and the operator's own recall establish that the research used the T48's ZIF socket **as the ICSP-clip endpoint** — a SOIC-8 clip wired into the ZIF rows, then clamped onto the chip **in circuit on the lock board**. The T48 reads in-circuit cleanly because, unlike the CH341A, it has a real current-capable 3.3 V supply (which is the original research's reason for selecting the T48). The T+4e bench then validated the in-circuit T48 + SOIC-8 clip method end-to-end on physical hardware — full read, byte-identical re-read, write+verify, keypad unlock. So:
>
> - **"Read out of circuit because the research did" — RETRACTED.** The research read in-circuit; G.0's appeal-to-precedent argument was inverted.
> - **"Read out of circuit because reading a live self-powered board failed the bench" — STILL TRUE, but only for the CH341A**, whose weak on-board LDO browns out under the dual-power-rail load of a self-powered board (Section F.0). With a programmer that has a real supply (T48), the in-circuit read on a live board is what the research did and what T+4e validated.
> - **Out-of-circuit reading is now CH341A-conditional**: it remains the only known-safe CH341A approach for *this* bench's failure modes, and would re-apply if the T+4g CH341A live-chip re-test surfaces the same brown-out. It is **not the workshop methodology** any longer. The workshop methodology is in-circuit SOIC-8 clip on a T48; see `T48-KALI-PLAN.md` Phase 3 + 4 + 5.
> - **For the workshop:** treat the three-option ranking below (option 1 = out-of-circuit, option 2 = in-circuit-de-powered, option 3 = in-circuit-live) as **CH341A-specific guidance**, retained because the CH341A is still a candidate per-attendee toolchain. The T48 path collapses this ranking: in-circuit on a live board (option 3 here) **works** on a T48 because the T48 sources adequate current and tolerates host-MCU SPI presence (research-confirmed and T+4e-validated).

> **Added after the operator disclosed the chip was being read in-circuit on a live board (Section F.0).** This is a workshop-procedure question, not only a bench question, and it should be settled *before* the Facilitator Guide and Handout are finalised.

**The standard tradecraft (HISTORICAL framing — see correction banner above; the research-precedent claim in this paragraph is RETRACTED).** SPI flash is normally read **out of circuit** — chip removed from the board and read in a socket/adapter — or, if read in-circuit, **with the board's own power fully removed.** Reading a *live, self-powered* board through the programmer's clip is the failure mode the bench just hit: two power sources on the VCC rail and the host MCU contending on the SPI bus (Section F.0). The original `PhysAccessDigiLies` research used an **Xgecu T48, a ZIF-socket programmer** — ~~a ZIF socket means **the chip was removed from the lock and read out of circuit.**~~ **[T+4d/T+4e correction: the research actually used the ZIF socket as the wiring endpoint for a SOIC-8 clip and read the chip IN CIRCUIT on the lock board; the T48's real current-capable supply is why this works where the CH341A fails. See banner above.]** ~~That is the methodology the source research validated, and it is the methodology the workshop should adopt.~~ **[T+4d/T+4e correction: the methodology the workshop should adopt — and now has, after the T+4e bench — is in-circuit SOIC-8 clip on a T48; see `T48-KALI-PLAN.md`.]**

**Recommendation for the workshop — in priority order:**

1. **Preferred — read the chips OUT OF CIRCUIT, pre-removed by facilitators.** Before the session, a facilitator (or whoever has soldering skill) desolders the AT45DB041E from each lock and mounts it on a **SOP8 breakout board / socket**, or the workshop simply uses **loose AT45DB041E chips in SOP8 sockets** that were never in a lock. Participants then clip onto a chip that has the CH341A as its *only* power source and *nothing else* on its SPI bus. This eliminates the dual-power conflict and the MSP430 contention by construction, matches the source research's method, and makes every station's read deterministic. It also sidesteps the question of whether each lock's MSP430 firmware happens to be holding CS or CLK.
2. **Acceptable — read in-circuit with the lock's battery/power fully removed.** If desoldering 20+ chips is not practical, participants may clip onto the chip *while it is still on the lock PCB* — but the **lock must be completely de-powered** (battery out, no other supply). The CH341A's clip then powers only the chip-plus-quiet-board, and the de-energised MSP430 cannot drive the SPI bus. This usually works for DataFlash because the rest of a small lock board presents a modest load, but it carries residual risk: the clip is powering the whole (quiet) board through eight tiny contacts, the MSP430's port pins still present some loading on the SPI nets, and a board with large bulk capacitance can still brown out the weak CH341A supply at power-on inrush.
3. **Not acceptable for the workshop — read in-circuit with the board live.** This is what the bench did and what failed. Two 3.3 V sources on the VCC rail and a live SPI master on the bus (Section F.0). Do not write this into the workshop procedure.

**The hazard to call out explicitly:** powering an *entire board* through a tiny SOP8 clip can itself overload the CH341A's weak on-board 3.3 V supply, even when the board is otherwise quiet — that is one of the two F.0 mechanisms. Out-of-circuit reading (option 1) avoids this hazard entirely; in-circuit-but-de-powered (option 2) reduces it but does not eliminate it. For a 90-minute room with 20+ participants who cannot stop to debug a brown-out, **option 1 is the robust call.**

**Out-of-lane note.** Desoldering chips and mounting them on breakout boards is **board-level electrical-hardware rework — outside the Systems Engineer lane.** This section *specifies the methodology* (read out of circuit, socketed); the actual chip removal and breakout-board assembly is a hardware/electronics task and should be routed accordingly, or assigned to a facilitator with soldering skill as a pre-session prep task.

### G.1 — Does this change the Section A recommendation?

**The *tool* recommendation stands. The *procedure* changes (G.0); the *station-kit* change is now conditional.**

- Section A's core finding is unaffected: `ch341prog` still cannot read an AT45DB041E; **flashrom is still the correct software**, and the **CH341A board is still electrically capable**. Section F is not a flashrom defect and not a board defect.
- **The procedure changes:** per G.0, the workshop should read chips **out of circuit / power-isolated**, not in-circuit on a live board. This is a Facilitator-Guide and Handout change (G.3) and a pre-session prep task (removing chips / preparing socketed chips). It costs facilitator time, not money.
- **The station-kit change is now conditional, not certain.** *If* STAGE 4-bis shows the failure was the in-circuit dual-power conflict (the leading hypothesis, F.0), then reading out of circuit fixes it and **no USB 2.0 hub is needed** — "CH341A + flashrom at $0 incremental hardware" holds after all. *Only if* the failure persists with the CH341A as the chip's sole power source does the USB-transport hypothesis (F.2) stand, and *then* the **powered USB 2.0 hub per station** becomes a real per-station cost. The hub is no longer assumed — it is gated on STAGE 4-bis step 4-bis-b *failing*. Section A.0 / A.7 are updated to reflect this conditional.

### G.2 — Concrete equipment-list change (CONDITIONAL)

> **⚠ This whole subsection is now gated on STAGE 4-bis step 4-bis-b *failing*.** If disconnecting the lock's power / reading the chip out of circuit clears the failure (the leading expectation, F.0), the workshop needs **no USB 2.0 hub** and the procedure change in G.0 is the only change required. The hub becomes equipment only if the failure survives power isolation and the USB-transport hypothesis (F.2) is confirmed. Stage the line item below, but do not procure 20 hubs until 4-bis-b has been run.

If STAGE 4-bis step 4-bis-b does **not** fix it and step 4-bis-e (the hub) does, the per-station kit gains one item:

| Item | Qty | Rough USD each | Notes |
|---|---|---|---|
| **USB 2.0 hub** (powered preferred; 4-port) | 1 per station + 2–3 spares | **$5–10** | A plain USB 2.0 hub. Provides the transaction translator the xHCI root port lacks. Powered is preferred for clean port power but bus-powered USB 2.0 hubs generally work too. |

**Budget impact for a 20-station workshop:** ~20 stations + 3 spares ≈ **23 hubs × $5–10 = roughly $115–230 total.** A multi-pack of basic USB 2.0 hubs is the cheap path; this keeps the workshop in its affordable bracket and is far below the cost of switching every station to a $30–55 T48. **A facilitator can also pre-stage 4–6 hubs as a shared pool** rather than one-per-station, since not every participant's laptop will need one — but bringing one-per-station removes a live-troubleshooting bottleneck in a 90-minute session and is the safer plan.

> **Out-of-lane note.** The pin-28 / voltage hardware mod (A.5) remains separate electrical-hardware tradecraft and is unaffected by this section. The USB 2.0 hub is **not** a soldering item — it is off-the-shelf equipment selection, squarely in the Systems Engineer lane.

### G.3 — SMYTH-ready guidance for `FACILITATOR-GUIDE.md` and `PARTICIPANT-HANDOUT.md`

> **FLAG FOR SMYTH (file-update phase).** Two distinct guidance blocks follow. **Block 1 (reading methodology) is unconditional** — it should go into the workshop files regardless of how STAGE 4-bis resolves, because reading a live self-powered board is wrong tradecraft either way. **Block 2 (USB 2.0 hub) is conditional** — only include it if STAGE 4-bis step 4-bis-b fails and the hub (4-bis-e) is what fixes the bench.

**BLOCK 1 — reading methodology (UNCONDITIONAL — include this).**

**For `FACILITATOR-GUIDE.md` — pre-session prep + procedure:** *Add a pre-session prep task: "Before the workshop, prepare the chips for OUT-OF-CIRCUIT reading. Either (a) desolder the AT45DB041E from each lock and mount it on a SOP8 breakout board / socket, or (b) provide loose AT45DB041E chips already in SOP8 sockets. Participants must clip onto a chip that is NOT installed in a powered lock. Reading the chip while it is still on a live lock board causes the programmer to fail with USB transfer errors — the lock's own battery and the programmer's clip both feed power to the chip, and the lock's microcontroller fights the programmer for the SPI bus." Add to the procedure: "Confirm each station's chip is out of circuit (on a breakout/socket) before the participant connects the programmer. If a chip must be read in-circuit, the lock's battery must be completely removed first — never read a chip on a powered board."*

**For `PARTICIPANT-HANDOUT.md` — setup step + troubleshooting:** *Add to the connection step: "You will clip the programmer onto a flash chip mounted on a small breakout board (or in a socket). The chip is NOT in a powered lock — that is deliberate: the programmer must be the only thing supplying power to the chip." Add to the troubleshooting box: "Seeing many lines of 'LIBUSB_TRANSFER_ERROR' or 'Failed to write N bytes'? The most common cause is the chip still being connected to something else that has power — make sure you are reading a chip on its own breakout board with nothing else attached, and ask a facilitator."*

**BLOCK 2 — USB 2.0 hub (CONDITIONAL — include ONLY if STAGE 4-bis step 4-bis-b fails and the hub fixes it).**

**For `FACILITATOR-GUIDE.md` — equipment list:** *Add one line item to the per-station kit: "1× USB 2.0 hub (powered preferred) — required to connect the CH341A programmer. Modern laptops with only USB 3.0/USB-C ports cannot reliably drive the CH341A directly; the USB 2.0 hub provides the transaction translator the programmer needs. Bring 2–3 spares." Add a setup note: "Connect the CH341A to the laptop through the USB 2.0 hub, never directly into a USB-3 (blue) or USB-C port."*

**For `PARTICIPANT-HANDOUT.md` — setup step:** *Add to the connection step: "Plug the CH341A programmer into the supplied USB 2.0 hub, and plug the hub into your laptop — do not plug the programmer directly into your laptop's USB port. Modern laptops need the hub in between for the programmer to work reliably."*

### G.4 — Re-weighing the Xgecu T48 fallback (was Section D Rank 3)

> **⚠ CORRECTION (T+4d/T+4e supersession).** The second bullet below — *"The T48 is a ZIF-socket programmer: the chip is removed from the board and dropped into the socket, so it is read out of circuit by construction"* — is **factually wrong**. The T48 supports both modes; the research used the ZIF socket as an **ICSP wiring endpoint** for a SOIC-8 clip and read **in-circuit on the lock board**. T+4e validated this on physical hardware. **The correct reason the T48 sidesteps the in-circuit dual-power failure is that the T48 has a real current-capable 3.3 V supply (and not a weak on-board LDO like the CH341A's), so it can power the chip-plus-quiet-board through the clip without browning out.** The xHCI / USB-transport advantage (first bullet) is correct as written; the "out-of-circuit by construction" claim (second bullet) is retracted. **Net conclusion is unchanged — the T48 is now the validated workshop primary** — but for the right reason: real supply current, not socket-only operation. See `T48-KALI-PLAN.md` for the validated execution plan and `T+4e-DUMP-VALIDATION-REPORT.md` for the bench evidence.

**Would the T48 suffer the same xHCI problem? Almost certainly not — and it is also immune to the in-circuit dual-power problem ~~by construction~~ [because it has a real current-capable 3.3 V supply, T+4e-validated].**

- The CH341A is a **USB 1.1 full-speed (12 Mbit/s)** device — that is the *xHCI*-hypothesis problem; full-speed is exactly the speed class that needs a transaction translator on an xHCI host. The **Xgecu T48 is a USB 2.0 high-speed (480 Mbit/s) device**, scheduled **natively by xHCI controllers** — it does not need a transaction translator and does not exhibit that failure mode. *(T+4e confirmed: lsusb shows `a466:0a53` at 480M / USB 2.0; no transport issues across full read + write + verify.)*
- ~~The T48 is a **ZIF-socket programmer**: the chip is removed from the board and dropped into the socket, so it is read **out of circuit** by construction.~~ **[T+4d/T+4e correction: RETRACTED. The T48's ZIF socket can be wired as the ICSP endpoint for a SOIC-8 clip and used for IN-CIRCUIT reads — that is what the original research did and what T+4e validated.]** The T48 sidesteps the in-circuit dual-power conflict (F.0) not because it forces out-of-circuit operation, but because **its 3.3 V supply is current-capable enough to power a chip-plus-quiet-board through the clip without browning out** — the precise constraint the CH341A's weak LDO violates. The T48 sidesteps *both* candidate failure modes (xHCI transport and in-circuit dual-power), not just the xHCI one.
- The T48 also has vendor-maintained software (Xgpro) and a maintained open-source path (`minipro`), and supports `AT45DB041E` **by name**.

**The one caveat unchanged from before:** Xgpro is Windows-only, and `minipro`'s T48 support is newer — whichever software path is chosen must be bench-tested before the workshop.

**Recommendation — keep the T48 as the primary fallback.** The workshop should make a deliberate go/no-go decision:

- **Plan A (recommended, cheapest):** CH341A + flashrom, chips read **out of circuit / power-isolated** (Section G.0). If STAGE 4-bis step 4-bis-b confirms power isolation alone fixes the bench, this is **$0 extra hardware** — only facilitator chip-prep time. A USB 2.0 hub per station is added only if the failure survives power isolation (xHCI hypothesis F.2 confirmed), keeping it in the ~$15–20/station bracket.
- **Plan B (robust, pricier):** if STAGE 4-bis does **not** cleanly fix it even with the chip out of circuit and a USB 2.0 hub, or if the facilitator wants to eliminate both the USB-topology variable *and* the in-circuit-wiring variable across 20 unknown laptops, **switch the workshop to the Xgecu T48.** Its ZIF socket and high-speed USB make it immune to both candidate failures. Cost rises to ~$30–55/station; the Facilitator Guide and Handout command steps must be rewritten for the T48 software (a SMYTH task).

Section D is updated below to reflect this re-ranking.

---

## H. ROOT-CAUSE DIAGNOSIS & OPERATOR PROCEDURE — adapter / chip VCC↔GND short (T+4c bench)

> **⚠ OUT OF WORKSHOP THREAT MODEL (T+4d/T+4e supersession) — Section H retained as a training reference.** Section H diagnoses a failure mode (chip cooked by desolder + adapter brown-out) that **cannot occur in the workshop as now scoped**: the workshop does not desolder chips and does not mount chips on adapters — it reads chips **in-circuit via SOIC-8 clip** on T48s (per `T48-KALI-PLAN.md`, T+4e-validated). The scenarios in H should not occur during the actual workshop.
>
> Section H is **retained, not deleted**, for three reasons:
> 1. **Training reference** — the dispatch-2 diagnosis (reverse-polarity orientation, current-leaky cooked chip, sub-beep-threshold partial short, three-way separation of failure modes by `lsusb`-presence × `LIBUSB_TRANSFER_ERROR`-presence) is high-quality electrical-hardware diagnostic material with standalone teaching value. The operator may want it for a future talk.
> 2. **For any operator who chooses to desolder outside the workshop** — e.g. the Phase 6 / T+4g CH341A live-chip re-test if the operator elects to bench it on a desoldered spare, or a post-conference research session that goes deeper into the chip.
> 3. **As historical record** of the T+4c bench's chip-cooked diagnosis — the operator's *own* chip got cooked at T+4c and that finding led directly to the T48 pivot. Section H is the autopsy.
>
> **The H.4 "workshop fallout" subsection** (pre-screen every adapter, budget spare pre-mounted chips) **is RETRACTED as workshop guidance** — see H.4 banner. Re-applicable only if the workshop reverts to out-of-circuit.

> **Added after the T+4c bench run (HISTORICAL framing — see banner above).** The operator followed Section G.0 — desoldered the AT45DB041E from the lock, soldered it onto a SOIC-8-to-DIP adapter, and seated the adapter in the CH341A's onboard ZIF socket. STAGE 4-bis's in-circuit dual-power conflict was thereby eliminated. A **third, distinct failure** then surfaced. This section is the diagnosis (H.0–H.2); **STAGE 4-ter** in Section B is the staged remediation; **H.3 is the copy-pasteable operator bench procedure**; H.4 is the workshop fallout.
>
> ~~**⚠ This failure mode is intrinsic to the Section G.0 recommendation.**~~ **[T+4d/T+4e: RETRACTED. Section G.0's out-of-circuit recommendation has itself been superseded — see G.0 correction banner. The failure mode is intrinsic to *desoldering and adapter-mounting*, which is no longer in the workshop's scope.]** G.0 tells the workshop to read chips out of circuit on socketed adapters/breakouts. The act of mounting a SOIC-8 chip on an adapter is a soldering operation, and a VCC↔GND solder bridge is one of its most common defects. So this is not an edge case — it is the predictable next failure once attendees start preparing their own chips. ~~H.4 folds it into the workshop troubleshooting flow.~~ **[T+4d/T+4e: RETRACTED — see H.4 retraction banner.]**

### H.0 — VERDICT: an excess load on the CH341A 3.3 V rail brown-outs it — reverse-polarity orientation, a cooked chip, or a VCC↔GND short

> **⚠ T+4c dispatch 2 — verdict refined; cause list re-ranked.** Dispatch 1 led with a VCC↔GND solder bridge (~65%). The bench then returned three facts that move the diagnosis:
> 1. **The CH341A board is undamaged.** Recovery worked: unplug → remove the adapter so the ZIF socket is **empty** → re-plug. It re-enumerated cleanly — `lsusb` shows `1a86:5512`; `dmesg` shows `New USB device found, idVendor=1a86, idProduct=5512, bcdDevice=3.04, Product: USB UART-LPT` with **no `error -71`** and no power-cycle loop; `flashrom -p ch341a_spi` with the socket empty returns a clean `No EEPROM/flash device found`. Re-plugging *with the shorted adapter still seated* did **not** clear the loop — only emptying the socket did. So the CH341A LDO and USB PHY are healthy; the brown-out load is entirely the chip-plus-adapter.
> 2. **The static VCC↔GND continuity test on the bare adapter read OPEN** — no beep. **There is no hard VCC↔GND solder bridge.** Dispatch 1's leading hypothesis is wounded.
> 3. **The brown-out is real and reproducible** — it occurs only with the adapter seated in the correct, powered 25-series rows and clears when the adapter is removed. Something on the adapter-plus-chip genuinely collapses the CH341A's 3.3 V rail *when powered.*
>
> **The key correction: a static "open" VCC↔GND meter reading does NOT exonerate the adapter or chip.** Two failure modes brown out the CH341A while passing a static bare-adapter VCC↔GND test, because both draw their excess current only when the socket is powered:
> - **Reverse-polarity orientation** — the adapter (or the chip on it) is seated 180°. The CH341A drives 3.3 V into the chip's GND pin and ties the chip's VCC pin to ground. The chip's substrate / ESD-protection diodes are forward-biased and conduct hard — a near-short, but a *powered-only* one: on a static meter test of the bare unpowered adapter, VCC↔GND reads open.
> - **Current-leaky / latch-up-damaged chip** — a chip cooked by desolder heat or ESD draws far more than the AT45DB041E's normal supply current; it too reads open VCC↔GND statically and only loads the rail when powered.
>
> The re-ranked cause list is in **H.1**. Reverse-polarity orientation is added as an explicit, prominent mechanism (**H.2a** is the orientation-verification procedure).

**What the T+4c bench showed.**

| Observation | Detail |
|---|---|
| Initial probe, adapter in wrong socket rows | `flashrom -p ch341a_spi -c AT45DB041D -r dump.bin` → `No EEPROM/flash device found`. Auto-probe (no `-c`) → same. **No `LIBUSB_TRANSFER_ERROR`** — USB transport clean. |
| Seating disclosure | The adapter had been seated at the **wrong end** of the ZIF socket — the end nearest the lever pivot, which is the **24-series I²C row set**. Re-seated to the correct end (farthest from the lever pivot, the **25-series SPI rows**), chip pin 1 toward the lever-handle column. |
| Probe after re-seating | **NEW error:** `Couldn't open device 1a86:5512. Error: Programmer initialization failed.` |
| `lsusb` | **No `1a86` device listed at all** — the CH341A has dropped fully off the USB bus. |
| `dmesg` tail | `attempt power cycle` → `new full-speed USB device number 8` → `Device not responding to setup address` → `device not accepting address 8, error -71` → `invalid context state for evaluate context command` → `new full-speed USB device number 9` → `device not accepting address 9, error -71` → `unable to enumerate USB device`. A **brown-out / re-enumeration loop** — the CH341A cannot complete enumeration. |
| Recovery (T+4c dispatch 2) | Unplug → **remove the adapter so the ZIF socket is empty** → re-plug → the CH341A re-enumerated cleanly: `lsusb` shows `1a86:5512`; `dmesg` shows `New USB device found, idVendor=1a86, idProduct=5512, bcdDevice=3.04, Product: USB UART-LPT`, **no `error -71`**, no loop; `flashrom` with the socket empty returns a benign `No EEPROM/flash device found`. Re-plugging *with the shorted adapter still seated* did **not** clear the loop. ⇒ **The CH341A board is undamaged.** The brown-out load is the chip-plus-adapter, and it must be powered through the socket to bite. |
| Static VCC↔GND test (T+4c dispatch 2) | Continuity mode, bare adapter out of socket, CH341A unpowered: VCC (pin 7) ↔ GND (pin 4) reads **open / no beep**. ⇒ **No hard VCC↔GND solder bridge.** Does *not* exclude reverse-polarity orientation, a cooked/leaky chip, or a sub-beep-threshold partial short — all of which read open statically (see H.1). |

**The mechanism — a near-zero-ohm load on the CH341A's 3.3 V rail.** The key discriminator is the **sequence**: the failure changed character *exactly* when the adapter moved from the wrong socket rows to the correct ones. That is not a coincidence — it is the diagnosis.

- **Wrong rows → no symptom worse than "no flash found."** The CH341A ZIF socket has two distinct row sets — a 24-series (I²C EEPROM) set and a 25-series (SPI flash) set — at opposite ends of the socket. Seating a 25-series-pinout adapter in the 24-series rows lands the chip's pins on the wrong socket contacts; in particular **the chip's VCC pin never reaches the socket's switched 3.3 V supply.** An unpowered chip draws no current, so the CH341A's rail is undisturbed, the device stays enumerated, and flashrom simply finds nothing on the SPI bus → `No EEPROM/flash device found`. **This is why the first probe looked like a benign STAGE-4 miss.**
- **Correct rows → VCC wired for the first time → the short bites.** Moving the adapter to the 25-series rows connects the chip's VCC pin to the socket's 3.3 V rail for the first time in this bench session. If there is a **low-impedance path from VCC to GND** — a solder bridge on the adapter, a damaged chip, conductive debris — then the instant VCC is powered, the CH341A's small on-board 3.3 V regulator is asked to drive a **near-short**. Its rail collapses. The CH341A browns out. A USB device whose supply collapses **resets its USB PHY and drops off the bus** — and then the host's xHCI controller tries to re-address it, the half-powered device cannot answer (`error -71` = `EPROTO`, a protocol/handshake failure), and it loops: `attempt power cycle` → new device number → `not accepting address` → repeat → `unable to enumerate USB device`.

**This is the same end-state as STAGE 4-bis Mechanism 1 (a brown-out that drops the USB PHY) but a different cause.** STAGE 4-bis: the load is a whole live, self-powered lock board. STAGE 4-ter: the load is a single shorted chip-plus-adapter. The remediation is correspondingly different — there is no battery to unplug; the fix is to find and clear the short on the adapter, or replace the chip.

**Why this is NOT STAGE 4-bis and NOT STAGE 4** — a clean three-way distinction:

- **vs. STAGE 4 (`No flash device found`, USB healthy):** STAGE 4 is poor *clip/socket contact* — the USB link to the CH341A is fine, the device stays on `lsusb`, only the SPI side finds nothing. STAGE 4-ter takes the **CH341A itself off the bus**.
- **vs. STAGE 4-bis (`LIBUSB_TRANSFER_ERROR` flood, in-circuit dual power):** STAGE 4-bis keeps the device **enumerated** — it is present on `lsusb`, and the failure is hundreds of *individual bulk-OUT transfers* erroring (`LIBUSB_TRANSFER_ERROR`). STAGE 4-ter never gets that far: there is **no `LIBUSB_TRANSFER_ERROR` flood**, because the device browns out *before* flashrom can open it and issue transfers — flashrom reports `Couldn't open device` / `Programmer initialization failed`, and the device is **absent from `lsusb`**. The presence-vs-absence of the device on `lsusb`, and the presence-vs-absence of the `LIBUSB_TRANSFER_ERROR` flood, are the two fields that separate 4-bis from 4-ter.

### H.1 — Confidence-ranked candidate causes

> **⚠ T+4c dispatch 2 — re-ranked.** Dispatch 1 ranked a hard VCC↔GND solder bridge first (~65%). The bench's static VCC↔GND continuity test came back **open** — that **excludes a hard bridge** and drops it far down the list. It does *not* exonerate the adapter or chip: reverse-polarity orientation and a current-leaky chip both brown out the CH341A while reading open on a static meter test. The re-ranked list, most likely first:

| Rank | Hypothesis | Confidence | Notes |
|---|---|---|---|
| **1** | **Reverse-polarity orientation — adapter (or chip on adapter) seated 180° in the ZIF socket** | **~45%** | The operator described the re-seat with uncertainty — "pin one on the same column as the lever," and explicitly said they may have socket pin-1 wrong. If the adapter is 180°, the CH341A drives 3.3 V into the chip's GND pin and ties VCC to ground; the chip's substrate / ESD-protection diodes conduct hard → brown-out. **Reads perfectly open on a static bare-adapter VCC↔GND meter test** — the diodes only conduct when powered — so the meter does not catch it. Free to verify and fix (H.2a). Best fits the facts: a healthy CH341A, an open static meter test, and a brown-out that appears only when the socket is powered. |
| 2 | **Current-leaky / latch-up-damaged chip — cooked by desolder heat or ESD** | ~30% | Two solder operations (desolder from lock + solder to adapter) put sustained heat into the die; ESD exposure is also likely. A damaged DataFlash die can draw far more than its normal few-mA supply current, or latch up, browning out the weak CH341A LDO. **Also reads open VCC↔GND statically** — it only draws excess current when powered. Discriminated by the H.3 step-5 spare-chip test. |
| 3 | **Partial resistive short on the adapter (50–300 Ω VCC↔GND), below the continuity-beep threshold** | ~12% | The bench used continuity mode; its beep threshold is only ~30–50 Ω, so a partial resistive short — flux residue, a fine solder whisker, a hairline bridge — would read "open / no beep" yet still load the rail. Caught by re-measuring in **ohms mode** (H.3 step 3). |
| 4 | **Hard VCC↔GND solder bridge** | ~5% | Dispatch 1's leading hypothesis. **Largely excluded** by the open continuity reading — a true metal bridge beeps. Retained at low probability only for an intermittent bridge that was not contacting at meter time. |
| 5 | **Damaged / dirty CH341A ZIF socket** | ~8% | A bent socket contact or solder/flux debris bridging socket pins. Lower probability because the CH341A recovered cleanly with the socket empty (the socket carried no fault then), and the symptom tracked the adapter re-seat. Still possible if debris only bridges when an adapter compresses the contacts. |

These are **not mutually exclusive**, but they split into two action paths. Cause 1 (orientation) is verified **by eye, free, first** — H.2a. Causes 2–5 are then separated by the ohms-mode meter test (H.3 step 3) and the spare-chip discriminator (H.3 step 5). The CH341A board itself is **ruled out** as the fault (it recovered cleanly with the socket empty) unless the spare-chip test in H.3 step 5 brings it back as the last remaining variable.

### H.2 — AT45DB041E SOIC-8 pinout (the load-bearing fact for the test)

The operator must know which pins are **VCC** and **GND** to run the short test. The AT45DB041E 8-lead SOIC (208-mil, "8S2" / "MA" package) pinout, from the Adesto/Atmel/Renesas *AT45DB041E* datasheet "Pin Configurations and Pinouts" table:

| Pin | Signal | Notes |
|---|---|---|
| 1 | **SI** | Serial Input (MOSI — data into the chip) |
| 2 | **SCK** | Serial Clock |
| 3 | **RESET** | Hardware reset, active-low; internal pull-up |
| 4 | **GND** | Ground |
| 5 | **CS** | Chip Select, active-low |
| 6 | **WP** | Write Protect, active-low; internal pull-up |
| 7 | **VCC** | Supply, 1.65–3.6 V (3.3 V nominal) |
| 8 | **SO** | Serial Output (MISO — data out of the chip) |

Pin 1 is identified by the **dot / notch** on the chip package; numbering runs **counter-clockwise** from pin 1 when viewed from the top (printed face up). **VCC is pin 7; GND is pin 4.** Note these are **not** a diagonal corner-to-corner pair — pin 7 is one in from a corner — so the operator must count pins, not assume the "two opposite corners" shortcut that holds for many other 8-pin parts.

> **⚠ Confidence on this pinout: HIGH, but verify on the bench before probing.** This is the standard Atmel/Adesto AT45DB-series serial DataFlash 8-SOIC assignment and it is consistent across the AT45DB041D and AT45DB041E datasheets (the D and E are pin-compatible — Section A.2). **However, this document's author has not measured the operator's specific chip,** and getting VCC/GND wrong sends the operator probing the wrong pins. **Confirm before trusting it**, by either of these, which should agree with the table above:
> 1. **Adapter silkscreen.** Most SOIC-to-DIP adapters silk-print pin numbers or a pin-1 marker; a few also mark VCC/GND. Match the chip's pin-1 dot to the adapter's pin-1 mark, then count.
> 2. **The chip datasheet.** Search "AT45DB041E datasheet" → the "Pin Configurations and Pinouts" / "Pin Descriptions" section → the **8-SOIC** column (the chip also comes in 8-UDFN and other packages with different pad layouts — use the SOIC column).
>
> If the silkscreen or datasheet disagrees with the table above, **trust the datasheet for the operator's actual part** and do not proceed on the table alone.

### H.2a — Pin-1 orientation verification (T+4c dispatch 2 — run this FIRST)

> **⚠ Added at T+4c dispatch 2.** Reverse-polarity orientation is the leading candidate (H.1 rank 1) and is **free to verify and fix.** A static VCC↔GND meter test cannot catch it — so orientation must be confirmed by eye **before** any meter-based conclusion. There are *two* independent orientations to get right, and a 180° error in either produces the same brown-out:
> 1. **The chip on the adapter** — was the SOIC-8 chip soldered onto the adapter with its pin-1 dot aligned to the adapter's pin-1 mark?
> 2. **The adapter in the ZIF socket** — is the adapter's pin-1 end seated in the correct corner of the CH341A's 25-series rows?

**Step A — find pin 1 on the chip.** The AT45DB041E SOIC-8 marks pin 1 with a **dot or a notch** at one corner of the package (printed face up). Pin numbering runs **counter-clockwise from pin 1** when viewed from the top. From H.2: pin 1 = SI, then 2 = SCK, 3 = RESET, 4 = GND down that side; 5 = CS, 6 = WP, 7 = VCC, 8 = SO up the other side.

**Step B — find pin 1 on the adapter, and confirm the chip is soldered on correctly.** A SOIC-to-DIP adapter silk-prints a **pin-1 marker** — a dot, a `1`, a square pad (vs. round for the others), or a bevelled corner of the chip outline. The chip's pin-1 dot must sit at the adapter's pin-1 mark. If the chip was soldered on rotated 180°, fix that first (this is a resolder — board-level rework; the operator's call) or simply mount a correctly-oriented spare chip.

**Step C — confirm where pin 1 must sit in the CH341A's 25-series ZIF socket.**

> **⚠ Confidence on the exact CH341A socket orientation: MODERATE — confirm on the board before trusting it.** This document's author has not inspected the operator's specific CH341A board. The classic black CH341A programmer has a single 8-pin (sometimes wide) ZIF socket with a lever at one end. The widely-documented convention for the classic black CH341A is: **for 25-series SPI flash, the chip is seated at the END OF THE SOCKET FARTHEST FROM THE ZIF LEVER PIVOT, with pin 1 of the chip toward the lever** (i.e. pin 1 in the row of the socket nearest the lever handle). The board itself is the authority — do **not** seat the chip on this paragraph alone. Confirm by one of these, in order of trust:
> 1. **The board's own silkscreen.** Classic black CH341A boards print a small `25xx` chip outline (often with a pin-1 dot or a notch in the printed rectangle) **and** a separate `24xx` outline next to the socket, showing exactly which rows and which orientation each chip family uses. Match the chip's pin-1 dot to the pin-1 corner of the printed `25xx` outline. This is the definitive answer for the operator's specific board.
> 2. **Photograph the board** top-down, in good light, and read the silkscreen `25xx` / `24xx` outlines and any pin-1 dot from the photo. If the silkscreen is ambiguous or worn, send the photo for confirmation rather than guessing.
> 3. The 25-series rows are the set the operator already identified as "correct, powered" — the end opposite the 24-series I²C rows. Section H.0 records the bench finding that the 24-series rows are nearest the lever pivot and the 25-series SPI rows are farthest from it; the silkscreen `25xx` outline confirms this and also gives the pin-1 corner.

**Step D — cross-check all three agree.** Chip pin-1 dot ↔ adapter pin-1 mark ↔ the pin-1 corner of the board's `25xx` outline. If all three line up, orientation is correct — proceed to the meter test (H.3 step 3). If any is wrong, **correct it and retry the read first** — a wrong orientation is a complete explanation for the brown-out and costs nothing to fix.

> **A note on the operator's described re-seat.** The operator placed the adapter "at the far end from the lever pivot" with "pin one on the same column as the lever (opposite end)" and flagged that they may have socket pin-1 wrong. The far end from the pivot is consistent with the 25-series rows. "Pin 1 toward the lever" is consistent with the documented classic-black-CH341A convention in Step C — but because the operator is unsure and the author has not seen the board, **do not treat this as confirmed.** Read the board's `25xx` silkscreen outline (Step C.1) or photograph it (Step C.2) and verify pin 1 against that. The silkscreen is the only fully reliable source here.

### H.3 — OPERATOR BENCH PROCEDURE — orientation check, VCC↔GND short test, adapter inspection, CH341A recovery

> This is the full procedure for the operator at the bench. It is also reproduced as the user-facing answer in the dispatch report. **Preconditions: CH341A unplugged from USB; adapter removed from the ZIF socket; a multimeter on hand.**
>
> **⚠ T+4c dispatch 2 — step order revised.** Orientation verification (new Step 2) now runs before the meter test, because it is free and is the leading candidate (H.1 rank 1). The meter test (Step 3) now calls for **ohms mode, not just the continuity beep** — the beep threshold misses a 50–300 Ω partial short. Step 5 (the cooked-chip discriminator — the spare-chip swap) is the resolution path when orientation and the meter both come back clean.

**Step 1 — CH341A off USB.** Unplug the CH341A from the laptop. This stops the brown-out / re-enumeration loop and makes the adapter safe to handle and meter. Leave it unplugged for the whole of steps 2–5 (re-plug only at Step 6). (Per the T+4c bench, the brown-out loop is cleared specifically by **emptying the ZIF socket** then re-plugging — re-plugging with the shorted adapter still seated does not clear it.)

**Step 2 — verify pin-1 orientation. FIRST — free, and the leading candidate.** Before any meter work, confirm the adapter is not seated 180°. Run **Section H.2a** in full: confirm the chip's pin-1 dot ↔ the adapter's pin-1 mark ↔ the pin-1 corner of the board's `25xx` silkscreen outline. A reversed adapter drives 3.3 V into the chip's GND pin, the chip's protection diodes conduct, and the CH341A browns out — and this reads **perfectly open** on the static VCC↔GND meter test in Step 3, so the meter will not catch it.
- **If orientation was wrong:** correct it (re-seat the adapter the right way round; if the *chip* was soldered onto the adapter reversed, that is a resolder or a swap to a correctly-mounted spare). Then go straight to **Step 5** (recover and retry) — skip the meter test; a wrong orientation is a complete explanation and the cheapest fix.
- **If orientation checks out correct:** continue to Step 3.

**Step 3 — VCC↔GND test (multimeter — ohms mode, not just continuity).**
- Set the multimeter to a **resistance range** (200 Ω, and also a higher range such as 2 kΩ / 20 kΩ to read a partial short) — **read the actual ohms number, do not rely on the continuity beep alone.** The continuity beep typically triggers only below ~30–50 Ω, so a **50–300 Ω partial short** — flux residue, a fine whisker, a hairline bridge — would read "no beep" yet still load the rail. Use continuity mode only as a quick first pass; the ohms number is the real measurement.
- Identify **VCC = pin 7** and **GND = pin 4** on the AT45DB041E (H.2 — pin 1 = the dot; count counter-clockwise from the top). On the DIP adapter these map to the corresponding adapter pins — confirm against the adapter silkscreen.
- Probe **one meter lead on VCC (pin 7), one on GND (pin 4)**, with the adapter out of the socket and the CH341A unpowered. Touch firmly to clean metal (pad, pin, or DIP leg).

  - **HEALTHY (no metal short):** an **open circuit** (meter shows `OL` / `1`), or a reading that **settles in the kΩ-and-up range**. It is normal to see the resistance reading **start low and climb** for a second or two — that is the chip's decoupling capacitor charging through the meter; a value that *settles high* (or open) is fine. ⚠ **An open / high reading here does NOT clear the chip** — a cooked, current-leaky chip and a reverse-polarity orientation both read open statically. If orientation (Step 2) was correct and this test is open, the brown-out is most likely a leaky chip — go to Step 4.
  - **PARTIAL RESISTIVE SHORT:** a value that **settles in the tens-to-low-hundreds of ohms** (roughly 5 Ω–300 Ω) and stays there. This is enough to brown out the CH341A's weak LDO even though it may not trigger the continuity beep. Treat it as a short — inspect and clear it (Step 3 inspection below / Step 4).
  - **DEAD SHORT:** a reading **near 0 Ω** (typically < 5–10 Ω) that **stays there**, with a **continuous beep** in continuity mode. A low-impedance metal VCC↔GND path. Do **not** re-plug the CH341A until it is cleared. (The T+4c bench's continuity test read open — so a dead bridge is largely excluded for the operator's current adapter, but this remains the check every attendee adapter needs.)

- **Also walk every adjacent-pin pair, in ohms mode.** A bridge does not have to be VCC-to-GND directly — it can be VCC (pin 7) bridged to SO (pin 8) or to WP (pin 6), or GND (pin 4) bridged to RESET (pin 3) or CS (pin 5). Walk the meter along **every adjacent pin pair** (1-2, 2-3, 3-4, 5-6, 6-7, 7-8, and the across-the-package pairs 1-8 and 4-5). **How to read the walk:** any pair settling **near 0 Ω is a solder bridge** — clear it. **Normal, not a bridge:** `RESET` (pin 3) and `WP` (pin 6) each have an **internal pull-up to VCC** — a meter probing pin 3→VCC or pin 6→VCC will read **tens to hundreds of kΩ**, which is the pull-up, not a defect. Likewise any pin reading high-kΩ to another pin through the chip's internal structures is normal. Only a **near-0 Ω / low-ohms** adjacent reading is a bridge. If the whole adjacent-pair walk is open or high-kΩ, there is no bridge — the fault is orientation (Step 2) or a leaky chip (Step 4).

**Step 4 — adapter solder-bridge inspection and repair.** (Run if Step 3 found a short or a partial short. If Step 3 was open and orientation was correct, skip to Step 5.)
- **Look first.** Under good light and magnification (a phone macro photo zoomed in works), inspect both faces of the adapter. **Where bridges form on a SOIC-8 adapter:** between adjacent SOIC pads on the fine-pitch side (1.27 mm pitch — the chip side), and at the via/trace where each SOIC pad fans out to its DIP leg. A bridge looks like a solder blob spanning two pads, or a hair-thin solder whisker between them. Excess flux residue can also be mildly conductive (and is the classic cause of a 50–300 Ω partial short) — clean it off with isopropyl alcohol and a brush.
- **Clear a bridge.** Apply **flux** to the bridged pads, lay **solder braid (desoldering wick)** over the bridge, and press a clean soldering iron tip onto the braid until the braid wicks the excess solder away. Lift the braid while it is still hot. Repeat until the pads are separate and shiny. Re-meter the pair (Step 3, ohms mode) to confirm the short is gone.
- **Reflow a cold / open joint.** While inspecting, also check for the opposite defect — a **cold joint** (dull, grainy, or balled-up solder not wetted to the pad) or an **open pin** (no solder, pin not connected). A cold joint on a signal pin causes a STAGE-4 `No flash device found`, not the brown-out — but fix it while the chip is out: add a touch of flux, reheat the joint with the iron until the solder flows shiny and wets both the pin and the pad, and let it cool without moving the chip.

**Step 5 — the discriminator: orientation vs. cooked chip vs. socket/CH341A.**

> **⚠ T+4c dispatch 2 — this is the definitive discriminator** for the case where orientation has been verified correct (Step 2) and the meter test (Step 3) reads open — i.e. there is no metal short, yet the CH341A still browns out. Run it in this order, cheapest first:

1. **Re-verify orientation — already done in Step 2, free.** If Step 2 found and corrected a 180° error, this is over: recover the CH341A (Step 6) and retry. Only continue down this list if orientation was confirmed *correct.*
2. **Swap in a known-good spare AT45DB041E on a known-good adapter, in the verified-correct orientation, and retry the read.** This is the single test that separates a cooked chip from everything else:
   - **Spare works (STAGE 3 detects it, no brown-out)** ⇒ **the original chip is cooked** — desolder heat or ESD left it current-leaky / latched-up. It read open VCC↔GND statically because it only draws excess current when powered. A cooked chip cannot be repaired. **Abandon it; use the spare.**
   - **Spare also browns out the CH341A** ⇒ the fault is *not* the original chip. It is now socket-side or CH341A-side: a damaged/dirty ZIF socket contact (H.1 rank 5), or — last — the CH341A board. Meter the spare's bare adapter VCC↔GND (should be open), inspect the ZIF socket for bent contacts and debris, and if both are clean, treat the CH341A board as suspect and swap it (Step 6 / STAGE 4-bis step 4-bis-f).
3. **Optional cross-check — lift the original chip off the adapter and meter its bare pins.** If you want to confirm a *static* internal short on the original chip (the rare dead-short variety of cook), desolder it from the adapter and meter VCC↔GND across the bare chip directly. A short still present on the bare chip = cooked. A short that disappears off the adapter = it was an adapter bridge. Note: a *current-leaky* cook (the common one) still reads open on this static test — the spare-swap in point 2 is the reliable discriminator, the bare-chip meter test only catches a hard internal short.

**Step 6 — recover and verify the CH341A.**
With orientation corrected and/or any short cleared, and **the adapter NOT yet re-seated**, re-plug the CH341A into USB.
- **Recovered (expected):** the CH341A re-enumerates cleanly. Neo will confirm via `lsusb` (the device shows up again as **`1a86:5512`**) and `dmesg` (a single clean `New USB device found ... idVendor=1a86, idProduct=5512` line, with **no `error -71`, no `unable to enumerate`, no power-cycle loop**). The T+4c bench already demonstrated this recovery with the socket empty — the CH341A board is undamaged.
- **Not recovered:** if `lsusb` still shows nothing and `dmesg` still loops *with the adapter out of the socket*, the CH341A itself is damaged → use a spare CH341A board. (The bench result makes this unlikely for the operator's current board.)
- Once the CH341A is confirmed healthy on `lsusb`, seat the adapter in the **correct 25-series rows, in the verified-correct orientation** (Section H.2a) and re-probe.

**Step 7 — decision point: when to abandon this chip.**
Switch to a **spare, loose, pre-written AT45DB041E on a known-good adapter** if **any** of these is true:
- The discriminator (Step 5) shows the original chip is cooked.
- A correctly-oriented original chip on a short-free adapter still browns out the CH341A.
- You have reflowed/cleared the adapter twice and a short keeps returning.

A spare loose chip on a verified adapter, in a verified orientation, removes every variable this stage is about. **Do not spend bench time resurrecting one chip** — the goal is a verified dump, and the chip's contents are what the workshop needs, which a pre-written spare already has. **Workshop-relevant note:** whatever caused this — a reversed adapter, a solder bridge, or a heat-killed chip — **will recur for attendees**, because the workshop has attendees desolder and mount their own chips (Section G.0). Budget spare pre-written chips and spare adapters accordingly, and have facilitators pre-screen each attendee adapter — orientation by eye plus the Step 3 VCC↔GND test — before it is plugged into a CH341A.

**Step 8 — where it is safe to re-attempt the STAGE 5 read.**
Re-attempt the read **only after all three of these hold:** (a) the adapter's pin-1 orientation is **verified correct** against the chip dot, the adapter mark, and the board `25xx` silkscreen (Section H.2a); (b) the VCC↔GND test reads **open** in ohms mode on the chip-on-adapter that will be used (no metal short, no partial short); and (c) the CH341A has **recovered and re-enumerated cleanly as `1a86:5512`** (Step 6). With those satisfied, seat the adapter in the **correct 25-series ZIF rows** and go to **STAGE 3** to re-probe; a clean `Found ... AT45DB041*` then unblocks **STAGE 5** (`sudo flashrom -p ch341a_spi -c AT45DB041D -r dump.bin`). If STAGE 3 still says `No EEPROM/flash device found` but the CH341A is healthy on `lsusb`, that is now an ordinary **STAGE 4** clip/socket-contact issue — a cold joint on a signal pin (Step 4) or a seating problem — not STAGE 4-ter.

### H.4 — Workshop fallout

> **⚠ RETRACTED as workshop guidance (T+4d/T+4e supersession).** H.4 was authored when the workshop arc was attendees desoldering and mounting their own chips on adapters. That arc has been **superseded** — the workshop now reads in-circuit with SOIC-8 clips on T48s, and attendees do not desolder or mount chips. Therefore: H.4's pre-screening procedure, spare-adapter stockpiling, and `FACILITATOR-GUIDE.md`/`PARTICIPANT-HANDOUT.md` SMYTH guidance are **NOT to be folded into the workshop files**. The text below is **retained as a training reference** (re-applicable if the workshop ever reverts to out-of-circuit, or for an operator running an out-of-circuit session outside the workshop arc). **The SMYTH guidance for the actual ToorCamp 2026 workshop lives in `T48-KALI-PLAN.md` Phase 3/4/5 + the T+4f workshop redesign work, not here.**

- **~~This is a workshop troubleshooting stage, not just a bench note.~~ [T+4d/T+4e: RETRACTED — this is a training-reference stage now; the workshop does not desolder.]** Section G.0 has attendees read chips out of circuit on socketed adapters/breakouts; preparing those adapters is a soldering task and VCC↔GND bridges — *and 180° orientation errors* — are predictable results. STAGE 4-ter / Section H must be reflected in the facilitator's troubleshooting playbook.
- **Pre-screen every adapter — orientation AND meter.** A facilitator should, for each attendee-mounted adapter, **before** it is plugged into a CH341A: (1) check pin-1 orientation by eye (chip dot ↔ adapter mark ↔ socket `25xx` silkscreen — Section H.2a), and (2) run the H.3 step-3 VCC↔GND test in ohms mode. Together these are a ten-second check and they prevent one attendee's reversed adapter or solder bridge from browning out and re-enumeration-looping a CH341A — a failure that looks alarming and eats session time.
- **Stock spares.** Budget **spare pre-written AT45DB041E chips** and **spare known-good adapters** — a heat-killed chip cannot be repaired and an attendee with a dead chip needs an immediate swap to stay with the session. This reinforces the Section G.0 recommendation that facilitators prepare socketed chips ahead of time: facilitator-prepped, pre-screened, correctly-oriented chips remove the soldering-defect variable from the attendee's critical path entirely.
- **SMYTH guidance (file-update phase).** *For `FACILITATOR-GUIDE.md` — troubleshooting + prep:* add to the troubleshooting playbook: "If a programmer drops off USB entirely (disappears from `lsusb`, kernel logs an enumeration loop / `error -71`) right after a chip-on-adapter is connected, the adapter or chip is browning out the programmer. **Check orientation first** — a chip adapter seated 180° drives power into the chip's ground pin and browns out the programmer, and a multimeter will *not* catch it. Confirm the chip's pin-1 dot lines up with the adapter's pin-1 mark and with the programmer socket's `25xx` outline. If orientation is correct, unplug the programmer and meter VCC↔GND on the chip in ohms mode — near-0 Ω or tens-to-hundreds of ohms means a short; clear it with flux + solder braid. If orientation and meter are both clean and it still browns out, the chip is heat-damaged — swap to a spare. To recover a looping programmer, empty its socket and re-plug." Add to prep: "Pre-screen every chip-on-adapter — orientation by eye, then a VCC↔GND ohms-mode check — before the session." *For `PARTICIPANT-HANDOUT.md` — troubleshooting box:* "If the programmer's light goes out / your computer stops seeing it right after you plug in your chip adapter: first check your adapter is the right way round (the chip's dotted corner must match the programmer socket's marked pin-1 corner) — a backwards adapter does this. If it's the right way round, you may have a solder bridge. Either way, unplug the programmer, take the adapter out, and ask a facilitator to check it before reconnecting."
- This does **not** change the tool recommendation (flashrom + CH341A) or the Section G.0 procedure (read out of circuit). It is a soldering-quality / chip-handling failure intrinsic to out-of-circuit prep — a reversed adapter, a solder bridge, or a heat-killed chip — and it is handled by an orientation check plus a multimeter, both already needed at the bench.

> **⚠ T+4c dispatch 2 — refinement summary.** The bench established the CH341A board is undamaged (it recovered cleanly with the socket emptied) and that the bare-adapter VCC↔GND test reads open (no hard solder bridge). STAGE 4-ter and Section H are revised accordingly: a static "open" VCC↔GND meter reading does **not** exonerate the adapter or chip, because **reverse-polarity orientation** (adapter seated 180°) and a **current-leaky heat-damaged chip** both brown out the CH341A while passing a static meter test. Reverse-polarity orientation is added as the leading mechanism (H.1 rank 1; H.2a is the verification procedure), the cause list is re-ranked (H.1), the meter test now calls for ohms mode to catch a sub-beep-threshold partial short, and orientation verification is ordered **before** all meter-based conclusions throughout STAGE 4-ter and H.3.

---

## SUMMARY FOR NEO

> **⚠ SUMMARY SUPERSEDED (T+4d/T+4e). Read this first.** The bullets below summarize this document as it stood at T+4c. Since then:
>
> - **Workshop primary toolchain is now T48 + minipro + in-circuit SOIC-8 clip + Kali** (not CH341A + out-of-circuit). The T48 path is documented in `T48-KALI-PLAN.md` and was end-to-end validated on physical hardware at T+4e (full read 540,672 bytes, byte-identical re-read, write+verify of an injected payload, keypad-unlock functional success — see `T+4e-DUMP-VALIDATION-REPORT.md` and `T+4e-INJECTION-PAYLOAD.md`).
> - **The "research used out-of-circuit ZIF" inference behind the original workshop methodology was wrong.** The research used the T48's ZIF socket as a SOIC-8-clip ICSP wiring endpoint and read **in-circuit**. The T48 reads in-circuit cleanly because it has a real current-capable 3.3 V supply (the CH341A's weak on-board LDO is the actual constraint that drove the out-of-circuit recommendation, not the methodology of the research).
> - **CH341A status:** still a candidate for the per-attendee tooling decision pending a Phase 6 / T+4g CH341A live-chip re-test on a non-cooked spare chip (likely in-circuit, since the workshop is now in-circuit). The CH341A toolchain assessment in Sections A, D, F, and the CH341A-specific equipment items in Section G remain valid **for the CH341A re-test scenario**; the "out-of-circuit is the workshop methodology" framing does not.
> - **The summary below is RETAINED as historical record of the T+4c posture and the CH341A diagnostic path** — those bullets are still the right answer for *the CH341A*, just no longer the workshop's primary path.

- **Recommended toolchain (one line):** ~~CH341A board + **flashrom 1.6.0** (already installed on Kali) — `sudo flashrom -p ch341a_spi -c AT45DB041D -r dump.bin` — read with the chip **out of circuit / power-isolated** (see revised root cause below).~~ **[T+4d/T+4e: SUPERSEDED. Workshop primary is now T48 + minipro 0.7.4 + in-circuit SOIC-8 clip — `sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -r dump.bin` — see `T48-KALI-PLAN.md`. The CH341A line below remains valid for the T+4g CH341A re-test scenario only.]**
- **Is `ch341prog` viable for the AT45DB041E? NO.** Source inspection of the downloaded `ch341a.c` proves it: `ch341SpiRead()` hardcodes the 25-series Read opcode `0x03` with a linear 3-byte byte-address, and `ch341SpiCapacity()` expects 25-series JEDEC/CFI capacity codes. It has zero DataFlash page-geometry awareness. It is a 25-series SPI NOR tool; the AT45DB041E is DataFlash. It would produce a plausible-looking but silently corrupt 512 KB file. flashrom's `at45db` driver, by contrast, handles DataFlash addressing and the 264-vs-256-byte page modes correctly.
- **🔴 BLOCKER (T+4b bench) — CH341A failure; root cause REVISED after a new operator fact.** STAGE 0 passed all five checks; STAGE 3 then failed with a flood of `cb_out: error: LIBUSB_TRANSFER_ERROR` / `Failed to write N bytes`, a retry degrading to `config_stream: Failed to write 3 bytes` / `Programmer initialization failed`, and the CH341A **repeatedly disconnecting and re-enumerating** (device 6→7→8). The first diagnosis blamed the full-speed-on-xHCI USB transport at ~85%. **The operator then disclosed the chip is being read IN-CIRCUIT on a LIVE board** — the AT45DB041E is still on the lock PCB, the lock's battery is energising it (3.3 V measured on a flash pin), and the lock's MSP430 microcontroller is live on the shared SPI bus. **Revised verdict (Section F.0):** the leading cause (~60%) is the **in-circuit dual-power conflict** — the lock battery and the CH341A clip both source 3.3 V onto the chip's VCC rail, browning out the CH341A and **resetting its USB PHY**, which is what makes it drop off the bus. The re-enumeration cycling is the strong tell — a USB-transport mismatch does not power-cycle a device, but a brown-out does. The xHCI hypothesis is **downgraded to ~30%, second place**. The two are not exclusive (the bench laptop is genuinely xHCI-only) but the dual-power cause explains the full symptom set from one mechanism.
- **The fix is FREE and must be tried FIRST — do NOT buy a USB hub yet.** Disconnecting the lock's battery so the CH341A is the chip's only power source (ideally reading the chip out of circuit) costs nothing and is the discriminating test. If it clears the failure, the cause was the in-circuit dual-power situation and **no USB 2.0 hub is needed.** Only if the failure survives full power isolation does the USB-transport hypothesis stand, and *then* a **powered USB 2.0 hub per station** ($5–10, ≈$115–230 for 20 stations) becomes the next move; if even that fails, switch to the **Xgecu T48** (USB 2.0 high-speed, structurally immune to the xHCI failure — Section D Rank 1).
- **First commands the operator should run — STAGE 4-bis, reordered** (the bench is mid-failure at STAGE 3): **(1) [Neo via MCP]** `lsusb -t` / descriptor / `dmesg` capture (4-bis-a); **(2) [Operator]** disconnect the lock's battery pack — and ideally read the chip out of circuit — so the CH341A is the only power source (4-bis-b); **(3) [Neo via MCP]** re-run `sudo flashrom -p ch341a_spi` and check `dmesg` for whether the re-enumeration cycling has stopped (4-bis-b). If it now detects the chip → STAGE 5, no hub needed. If it still floods `LIBUSB_TRANSFER_ERROR` with the CH341A as the sole power source → the USB-transport hypothesis is back in play, continue to the port-reset / USB-2-hub / cable steps.
- **🔴 BLOCKER (T+4c bench) — chip-plus-adapter brown-outs the CH341A; a third, distinct failure. ROOT CAUSE RE-RANKED at T+4c dispatch 2.** The operator read the chip out of circuit (Section G.0) — desoldered it and mounted it on a SOIC-8-to-DIP adapter. Symptom: `Couldn't open device 1a86:5512` / `Programmer initialization failed`, the CH341A **dropped fully off the USB bus** (no `1a86` in `lsusb`), `dmesg` shows an xHCI enumeration loop (`error -71`, `unable to enumerate USB device`), and — the discriminator — **no `LIBUSB_TRANSFER_ERROR` flood.** Mechanism: the chip-plus-adapter is an excess load on the CH341A's weak 3.3 V rail; the rail collapses, the USB PHY drops. **Dispatch 2 bench facts changed the diagnosis.** (1) The CH341A board is **undamaged** — emptying the ZIF socket and re-plugging recovered it cleanly (`lsusb` shows `1a86:5512`, `dmesg` clean, `flashrom` with socket empty returns a benign `No EEPROM/flash device found`). (2) The static bare-adapter VCC↔GND continuity test read **open** — **no hard solder bridge.** (3) The brown-out is still real and reproducible only with the adapter seated in the powered 25-series rows. A static "open" VCC↔GND reading does **not** exonerate the adapter or chip — both reverse-polarity orientation and a current-leaky cooked chip brown out the CH341A while passing a static meter test. **Re-ranked causes (Section H.1):** reverse-polarity orientation (adapter seated 180°) ~45%; current-leaky / heat-damaged chip ~30%; partial resistive short below the continuity-beep threshold ~12%; damaged ZIF socket ~8%; hard solder bridge ~5% (largely excluded by the open meter reading). Remediation is **STAGE 4-ter** (Section B) — operator procedure in **Section H.2a + H.3**, ordered cheapest-first: **(1) verify pin-1 orientation by eye** (chip dot ↔ adapter mark ↔ board `25xx` silkscreen — free, leading candidate); (2) VCC↔GND test in **ohms mode** not just continuity (AT45DB041E SOIC-8: **VCC = pin 7, GND = pin 4**); (3) clear any bridge; (4) **discriminator** — a known-good spare chip on a known-good adapter in the verified-correct orientation: spare works ⇒ original chip cooked; spare also browns out ⇒ socket/CH341A-side; (5) recover the CH341A. Decision point: swap to a spare pre-written chip once the chip is shown cooked or after two clears. This will recur for attendees who mount their own chips — facilitators should pre-screen every adapter for both orientation and a VCC↔GND short.
- **In-circuit-vs-socketed methodology (Section G.0) — workshop-procedure change.** The workshop should read chips **out of circuit / socketed** (chips pre-removed by facilitators and mounted on SOP8 breakouts, or loose AT45DB041E in sockets) — this matches the original `PhysAccessDigiLies` research, which used a ZIF-socket programmer. In-circuit reading is acceptable *only* with the lock fully de-powered; reading a live board is the failure the bench hit. Note the hazard: powering a whole board through a tiny SOP8 clip can itself brown out the weak CH341A supply — out-of-circuit reading avoids it entirely.
- **SMYTH guidance is staged in Section G.3** — two blocks: **Block 1 (reading methodology — unconditional)**: instruct out-of-circuit reading in `FACILITATOR-GUIDE.md`/`PARTICIPANT-HANDOUT.md` and add a chip-prep pre-session task; **Block 2 (USB 2.0 hub — conditional)**: include only if STAGE 4-bis step 4-bis-b fails and the hub is what fixes the bench.
- **Blocking unknowns / flags:**
  1. **CH341A bench failure (blocking)** — root cause revised to in-circuit dual-power conflict (Section F.0, leading) vs. full-speed-on-xHCI transport (F.2, second). Resolution path is the reordered STAGE 4-bis, power-isolation first. The bench cannot reach a successful read until this clears.
  2. **Handout size claim is likely wrong.** Both workshop files say the dump is 524,288 bytes — that is only true in power-of-2 mode. In the chip's *default* 264-byte mode the dump is **540,672 bytes**. The real number must be confirmed by the Stage 5 hardware read, then SMYTH corrects both files. The handout's success check would otherwise falsely fail a correct dump.
  3. **CH341A 5 V issue is real and workshop-relevant** (20+ participants, hundreds of clip cycles on a 3.3 V part). The operator should *measure* VCC on the clip before the workshop (in scope). If it reads ~5 V, the board-modification fix is **electrical/hardware tradecraft and must be routed to a hardware specialist** — out of Systems Engineering lane. (Independent of the bench blocker.)
  4. **Chip removal for out-of-circuit reading is out-of-lane.** Section G.0 specifies the *methodology* (read socketed); the actual desoldering of chips and assembly of SOP8 breakouts is board-level rework and must be routed to a hardware/electronics specialist or assigned to a facilitator with soldering skill as a pre-session prep task.
  5. The deliverable cannot be fully closed until **STAGE 4-bis clears the bench failure and the Stage 5 read runs on real hardware** — the standalone package (Section E) is intentionally design-only and gated on that confirmation.

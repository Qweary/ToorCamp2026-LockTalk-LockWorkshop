# T+4g — CH341A Sufficiency Re-Test (IN-CIRCUIT, against injected.bin ground truth)

**Author:** Electrode (Electrical/Hardware Engineer) · The Manhattan Project
**Date:** 2026-05-20 (revised — in-circuit / injected.bin reality)
**Engagement:** ToorCamp 2026 talk-prep · "Dead Bytes Tell No Lies" · Session T+4g, Task 2
**Target chip:** Adesto/Atmel AT45DB041E (4 Mbit SPI **DataFlash**, JEDEC `1F 24 00`), native **264-byte page** mode
**Programmer under test:** CH341A mini programmer (USB `1a86:5512`), flashrom 1.6.0
**Test topology:** **IN-CIRCUIT** — chip soldered on the live Alarm Lock T2/T3 board, read via SOIC-8 / SOP8 clip
**Ground truth (no reference read needed):** `injected.bin` — the exact bytes the **T48 wrote+verified** to this chip this session
  · path `/home/qweary/Desktop/toorcamp-2026-dumps/T+4g-second-board-diagnostic/injected.bin`
  · size **540,672 bytes** (2048 × 264, native mode) · **MD5 `56947205a9cffa1de45f6b3f0f8611f5`** (confirmed at bench, T+4g)

> **What changed from the prior version of this doc.** The T48 is now **disconnected** — there is **no** authoritative
> reference-read step. The chip under test is the **in-circuit** chip on the live lock board that the T48 just programmed,
> so the CH341A read is compared against the already-captured **`injected.bin`**, not a fresh read. This re-test settles
> §6.8 (a)/(b) of `T48-KALI-PLAN.md` for the **in-circuit** case specifically — which is the realistic attendee scenario
> ("attendee clips a lock"), and which directly re-enters the T+4b brown-out failure mode (see §A header).
>
> **Audit-band caveat (expected, NOT a failure):** after the T48 write, batteries were reinstalled and codes were
> keypad-tested. Those keypad events write the lock's audit log. So the **audit-log band `0x42000`–`0x46938` may differ**
> from injected.bin. **Compare page 0 / the code region for the patch match; expect the audit band to differ.** A full-image
> `cmp` whose **only** mismatch falls inside `0x42000`–`0x46938` is a **PASS**.

---

## 0. Pre-flight findings (validated on this Kali box, T+4g)

| Check | Command | Result |
|---|---|---|
| flashrom version | `flashrom --version` | **`flashrom v1.6.0 on Linux 6.19.14+kali-amd64 (x86_64)`** — has the `at45db` DataFlash driver |
| `ch341a_spi` driver | `flashrom -p list` | **present** (`ch341a_spi`) |
| AT45DB041**E** in chip DB | `flashrom -L \| grep -i at45db041` | **NOT listed.** Only **`AT45DB041D`** (Atmel, `PREW`, 512 kB, SPI) appears. |
| CH341A USB ID to grep | (expected enumeration) | **`1a86:5512`** (QinHeng CH341) — not currently plugged in |
| Ground-truth `injected.bin` | `md5sum injected.bin` | **`56947205a9cffa1de45f6b3f0f8611f5`**, 540,672 bytes — confirmed |

**Therefore the `-c` argument is `AT45DB041D`, NOT `AT45DB041E`** (041D and 041E share JEDEC `1F 24 00`; 041E is
absent from `flashrom -L` and presents under the 041D name; per `T4-DIAGNOSTIC-AND-TOOLCHAIN.md` §A.2). The 264↔256-byte
page-size bit is **OTP/irreversible**; flashrom's `at45db` `-r`/`-w` path **adapts to the existing mode** and never issues
the page-size configure command — **never run a page-size configure op on a workshop chip** (§C).

---

## A. COPY/PASTE BENCH RE-TEST BLOCK (IN-CIRCUIT)

> **THE CENTRAL TECHNICAL REALITY — this is the T+4b brown-out problem, by design.** Reading **in-circuit** makes the
> CH341A try to power the **entire lock board** through the SOP8 clip. Its weak ~3.3 V LDO browns out, the USB PHY drops off
> the bus, and you get the `LIBUSB_TRANSFER_ERROR` flood (T+4b / STAGE 4-bis Mechanism 1). The T48 succeeded in-circuit at
> T+4e precisely because it has a **real current-capable target supply** (and holds the lock MCU in RESET). The CH341A has
> **neither**. Battery state is now the decisive variable — both cases are addressed below.
>
> Run top-to-bottom. Each step has a **SUCCESS SIGNAL** and an **ESCALATE** one-liner. **STEP 0 is a multimeter VCC
> pre-flight you do BEFORE clipping onto the live board — STEP 1 onward must not start until STEP 0 reads ≈3.3 V.**
> Steps 1–5 are read-only (the chip is not modified). Step 5 is the **only** writing step and is gated behind a clean 0–4.
>
> **GLOBAL BROWN-OUT WATCH (every CH341A step):** a flood of `cb_out: error: LIBUSB_TRANSFER_ERROR` / `Failed to write N
> bytes`, OR the CH341A vanishing from `lsusb` mid-command, OR `dmesg` xHCI re-enumeration cycling = the CH341A is browning
> out under the board's load. This is the **expected dominant failure for the BATTERIES-OUT case** (CH341A sources the whole
> board) and a **likely failure for BATTERIES-IN** (rail contention). **GLOBAL STOP THRESHOLD:** if brown-out floods on
> **2 attempts across BOTH battery states**, that is the **NEGATIVE result** — record §6.8 **(b)**, stop, do **not** force.

> **⚡ DO STEP 0 FIRST — DO NOT CLIP ONTO THE LOCK BOARD UNTIL STEP 0 PASSES.** The clip is the LAST thing you connect.
> Steps 1–5 below all assume STEP 0 returned ≈3.3 V on the clip VCC pin. If STEP 0 reads ≈5 V, the CH341A is the well-known
> 5 V-rail board and clipping it onto this **live 3.3 V lock board** can stress/damage both the AT45DB041E and the lock MCU —
> **STOP at STEP 0** and resolve the adapter question (STEP 0 ruling) before touching the board.

> **🔴🔴 PINOUT-MISMATCH FOOT-GUN — READ BEFORE STEP 0. THIS IS THE DECISIVE FINDING (T+4g STEP 0b bench data).**
> **The AT45DB041E DataFlash pinout is NOT the same as the 25-series (W25Q / 25xxx) SPI-flash pinout that standard CH341A
> SOIC-8 clips and the CH341A's onboard ZIF socket are wired for.** The two pinouts disagree on FOUR pins — including
> **where VCC lives** (AT45DB = **pin 7**; 25-series = **pin 8**). Clipping a 25-series-wired clip onto the AT45DB041E puts
> the programmer's **VCC onto the chip's SO/MISO pin (pin 8)** and leaves the chip's **real VCC (pin 7) unpowered**, while
> the data lines are also permuted. **This is exactly what the T+4g STEP 0b multimeter readings show** (pin 7 VCC = 0 V,
> a ~3.3 V-magnitude potential appearing on pin 8/SO). Pin layouts (notch up, pins 1–4 left top→bottom, 5–8 right
> bottom→top):
>
> | SOIC-8 pin | **AT45DB041E (Atmel DataFlash)** | **25-series (W25Q / 25xxx)** | Same? |
> |---|---|---|---|
> | 1 | SI (data in) | CS# (chip select) | ✗ |
> | 2 | SCK (clock) | DO / MISO (data out) | ✗ |
> | 3 | RESET# | WP# / IO2 | ✗ |
> | 4 | **GND** | **GND** | ✓ (common) |
> | 5 | CS# (chip select) | DI / MOSI (data in) | ✗ |
> | 6 | WP# | CLK (clock) | ✗ |
> | 7 | **VCC** | HOLD# / IO3 | ✗ |
> | 8 | SO (data out / MISO) | **VCC** | ✗ |
>
> **Only GND (pin 4) is common.** A pin-4 ground reference is valid either way, but VCC is NOT — and neither are SI/SO/SCK/CS.
> **A standard 25-series clip cannot read the AT45DB041E**, even with a power remap, because the data/clock/CS pins are also
> scrambled. **Engineering verdict (T+4g): the cheap CH341A path is structurally impractical for the workshop — see §B / §6.8.**

```bash
# =====================================================================
# T+4g CH341A IN-CIRCUIT SUFFICIENCY RE-TEST
#   target: the live lock-board chip the T48 just programmed this session
#   ground truth: injected.bin  (MD5 56947205a9cffa1de45f6b3f0f8611f5, 540672 B)
# =====================================================================
mkdir -p ~/t4g-retest && cd ~/t4g-retest
REF=/home/qweary/Desktop/toorcamp-2026-dumps/T+4g-second-board-diagnostic/injected.bin
sudo md5sum "$REF"     # MUST print 56947205a9cffa1de45f6b3f0f8611f5  (re-confirm the ground truth)

# =====================================================================
# STEP 0 — VCC / VOLTAGE SAFETY PRE-FLIGHT  *** DO THIS BEFORE CLIPPING ***
#   NO clip on the board yet. Tools: multimeter (DC volts) + the CH341A.
#   The AT45DB041E is a 3.3 V-class DataFlash: valid VCC = 2.5 V – 3.6 V,
#   ABSOLUTE MAX 4.0 V. So 1.8 V = far BELOW Vcc(min) (won't run);
#   5 V = ABOVE the 3.6 V max / past abs-max (device stress). Target = 3.3 V.
# ---------------------------------------------------------------------
# 0a. ADAPTER RULING — the 1.8 V adapter:
#     >>> DO NOT USE THE 1.8 V ADAPTER. <<<  1.8 V is below the AT45DB041E's
#     Vcc(min) of 2.5 V — the chip would be under-powered, giving failed or
#     garbage SPI reads, and in-circuit it can't even begin to hold the bus.
#     The 1.8 V setting is the WRONG voltage for this 3.3 V part. Use 3.3 V.
#
# 0b. 5 V-RAIL HAZARD CHECK (the classic CH341A black-board flaw):
#     Plug the CH341A into USB. DO NOT clip it to the lock board.
#     Set the CH341A to its 3.3 V position (or fit a 3.3 V level-shift adapter).
#     With a multimeter on DC volts, measure the rail the clip/socket DELIVERS
#     to GND (pin 4). >>> PINOUT WARNING (see the red box above STEP 0): the clip's
#     VCC wire lands on whatever pin the CLIP is wired for — on a standard 25-series
#     clip that is PHYSICAL PIN 8. But on the AT45DB041E target, PIN 8 = SO/MISO and
#     the chip's real VCC is PIN 7. So measure the CLIP's VCC-carrying pin (the rail
#     the clip would source), and SEPARATELY note AT45DB pin 7 vs pin 8:
#       SUCCESS SIGNAL (SAFE — proceed):  ≈ 3.0–3.6 V  (nominally 3.3 V).
#       STOP THRESHOLD (DANGER):          ≈ 4.5–5.5 V  (the flawed 5 V-rail board).
#     If it reads ≈5 V you have a 5 V-rail CH341A. DO NOT CLIP IT ONTO THE
#     LIVE 3.3 V LOCK BOARD — that 5 V would fight the lock's 3.3 V regulator
#     and reach the lock MCU, not just the flash. This matters MORE in-circuit
#     than on a loose chip: in-circuit you can damage the lock, not only a chip.
#     >>> If ≈5 V: fit a 3.3 V level-shifting adapter (or use a known-3.3 V-safe
#         CH341A / 3.3 V mod), then RE-MEASURE 0b until it reads ≈3.3 V.
#     >>> A 1.8 V adapter does NOT fix this (wrong voltage, see 0a).
#     >>> If your only adapter is the 1.8 V one and the board reads ≈5 V:
#         do NOT run the in-circuit CH341A test today — it maps straight to the
#         "acquire more T48s" / §6.8 (b) decision. The honest call is to stop here.
#
# 0c. GATE: only continue to STEP 1 once 0b reads ≈3.3 V (2.7–3.6 V) on the
#     UNclipped clip VCC pin. If you cannot get a ≈3.3 V reading, STOP.
#   ESCALATE: any reading outside 2.7–3.6 V after fitting the correct 3.3 V
#     adapter -> faulty CH341A/adapter; swap unit once; still wrong -> STOP,
#     do not clip onto the live lock board.

# ---------------------------------------------------------------------
# STEP 1 — CH341A USB ENUMERATION SANITY (read-only)  *** REQUIRES STEP 0 PASS ***
#   Only after STEP 0 confirmed ≈3.3 V on the UNclipped clip VCC pin:
#   plug in the CH341A (its own USB), THEN clip the SOIC-8 onto the lock-board
#   chip, pin-1 dot <-> clip arrow. Decide battery state per STEP 2 before probing.
# ---------------------------------------------------------------------
lsusb | grep -i '1a86:5512' || echo 'CH341A NOT enumerated (1a86:5512 absent)'
flashrom --version
flashrom -L 2>/dev/null | grep -i 'at45db041'     # name-confirm: expect AT45DB041D (NOT 041E)
#   SUCCESS SIGNAL: a 'Bus ... ID 1a86:5512 QinHeng Electronics CH341 ...' line, flashrom v1.6.0,
#     and an 'AT45DB041D' row.  >>> USE -c "AT45DB041D" below (unless flashrom prints 041E separately).
#   ESCALATE: 1a86:5512 absent after re-plug + different port + different cable (3 tries) -> swap the
#     CH341A unit once; still absent => NEGATIVE on this hardware, STOP and record.

# ---------------------------------------------------------------------
# STEP 2 — CH341A flashrom PROBE, IN-CIRCUIT  (NO read, NO write — identify only)
#   *** REQUIRES STEP 0 PASS (clip VCC measured ≈3.3 V) before the clip went on ***
#   *** BATTERY-STATE BRANCH — try CASE A first (lower risk), then CASE B ***
# ---------------------------------------------------------------------
# -- CASE A: BATTERIES OUT (lock MCU dead; CH341A must source the WHOLE board through the clip) --
#    This is the realistic "attendee clips a battery-pulled lock" case. Expect the T+4b brown-out.
sudo flashrom -p ch341a_spi                        # auto-probe
sudo flashrom -p ch341a_spi -c "AT45DB041D"        # if auto-probe is ambiguous, pin the name
#   SUCCESS SIGNAL: 'Found Atmel flash chip "AT45DB041D" (528 kB, SPI) on ch341a_spi.'
#     READ THE SIZE: ~528 kB (540672) => native 264-byte mode (GOOD). ~512 kB (524288) => binary mode (FLAG, see SecB/C).
#   IF brown-out flood (LIBUSB_TRANSFER_ERROR / drops off lsusb): this is Mechanism 1 — the CH341A
#     cannot power the whole board. Re-seat the clip ONCE, retry ONCE. If it still floods -> go to CASE B.
#
# -- CASE B: BATTERIES IN (lock MCU live; it drives/contends on the shared SPI bus, and the lock's
#            3.3 V rail fights the CH341A's). Expect bus contention / corrupt probe / programmer confusion.
#    ⚠ Potentially risky to BOTH the lock MCU and the CH341A (two rails fighting). Brief probe only.
sudo flashrom -p ch341a_spi -c "AT45DB041D"
#   SUCCESS SIGNAL: same 'Found ... AT45DB041D (528 kB)'. A clean probe here is LESS likely than CASE A.
#   IF garbage/no-detect/wrong-ID or brown-out: contention or rail-fight — record it, do NOT linger.
#   GLOBAL STOP: if BOTH CASE A and CASE B brown out / fail to probe across 2 attempts each ->
#     NEGATIVE result, §6.8 (b). STOP. Do not force. (See BROWN-OUT WATCH.)

# ---------------------------------------------------------------------
# STEP 3 — CH341A flashrom READ, IN-CIRCUIT  (read-only; produces a file, does not alter the chip)
#   Use whichever battery state PROBED CLEAN in STEP 2. Use the name STEP 1 confirmed.
# ---------------------------------------------------------------------
sudo flashrom -p ch341a_spi -c "AT45DB041D" -r spare-ch341a.bin
ls -l spare-ch341a.bin
sudo md5sum spare-ch341a.bin
#   SUCCESS SIGNAL: 'Reading flash... done' with NO error AND a file is produced.
#   RECORD the EXACT byte size — it is the page-mode + completeness answer:
#     540672 => native 264-byte mode, full read (matches injected.bin scope)   GOOD
#     524288 => binary 256-byte mode (page-mode mismatch -> SecB/C, do NOT compare/write)
#     short / 0 / partial => brown-out aborted the read mid-stream
#   ESCALATE: read aborts / partial / LIBUSB flood -> BROWN-OUT WATCH; re-seat, retry ONCE in the
#     same battery state, then try the OTHER battery state ONCE. Still no full 540672 read across
#     both states -> NEGATIVE result, §6.8 (b), record + STOP.

# ---------------------------------------------------------------------
# STEP 4 — COMPARE the CH341A read against injected.bin  (full + page-0/code-region focused)
#   PASS rule: code region matches; the ONLY tolerated full-image diff is inside the audit band.
# ---------------------------------------------------------------------
# 4a. sizes + hashes side by side
ls -l "$REF" spare-ch341a.bin
sudo md5sum "$REF" spare-ch341a.bin
#     IDENTICAL md5 => perfect match (means the audit band did NOT change, or batteries stayed out). Best case.

# 4b. PAGE 0 / CODE REGION compare — this is the PATCH-MATCH check (the bytes the T48 injected):
cmp <(sudo head -c 264 "$REF") <(head -c 264 spare-ch341a.bin) \
    && echo 'PAGE0 CODE REGION: IDENTICAL (patch confirmed)' \
    || echo 'PAGE0 CODE REGION: DIFFERS  <-- this is a REAL mismatch, NOT the audit band'
#     SUCCESS SIGNAL: 'PAGE0 CODE REGION: IDENTICAL' => the injected code/patch bytes read back faithfully.

# 4c. FULL-IMAGE compare — locate where (if anywhere) the images diverge:
cmp -l "$REF" spare-ch341a.bin | awk '{printf "0x%X\n",$1-1}' | sort -u > /tmp/diff-offsets.txt
if [ ! -s /tmp/diff-offsets.txt ]; then
  echo 'FULL IMAGE: BYTE-IDENTICAL'
else
  echo "FULL IMAGE: differs at $(wc -l </tmp/diff-offsets.txt) offsets; range:"
  head -1 /tmp/diff-offsets.txt; tail -1 /tmp/diff-offsets.txt
  # PASS-if-audit-only test: are ALL diffs inside the audit band 0x42000..0x46938?
  awk 'BEGIN{ok=1} { d=strtonum($0); if (d<0x42000 || d>0x46938) ok=0 }
       END{ if(ok) print "ALL DIFFS INSIDE AUDIT BAND 0x42000-0x46938 => PASS (expected from keypad tests)";
            else print "DIFFS OUTSIDE AUDIT BAND => REAL MISMATCH, investigate" }' /tmp/diff-offsets.txt
fi
#   SUCCESS SIGNAL (PASS): EITHER 'FULL IMAGE: BYTE-IDENTICAL'
#     OR 'PAGE0 CODE REGION: IDENTICAL' + 'ALL DIFFS INSIDE AUDIT BAND ... => PASS'.
#   FAIL: page 0 differs, or diffs land OUTSIDE 0x42000-0x46938 -> the CH341A read is NOT faithful
#     (or page-mode mismatch). Do NOT proceed to STEP 5. Map to Section B.

# ---------------------------------------------------------------------
# STEP 5 — OPTIONAL IN-CIRCUIT WRITE TEST  (modifies the live chip)  *** GATED ***
#   ONLY if STEP 2 PROBED clean, STEP 3 READ a full 540672 bytes, AND STEP 4 PASSED.
#   If any of those failed, SKIP STEP 5 entirely. Use the SAME battery state that read clean.
#   (Writing in-circuit draws MORE current than reading; brown-out risk is HIGHER here.)
# ---------------------------------------------------------------------
sudo flashrom -p ch341a_spi -c "AT45DB041D" -w "$REF"
sudo flashrom -p ch341a_spi -c "AT45DB041D" -r spare-verify.bin
cmp <(sudo head -c 264 "$REF") <(head -c 264 spare-verify.bin) \
    && echo 'WRITE-BACK PAGE0: VERIFIED' || echo 'WRITE-BACK PAGE0: MISMATCH'
#   SUCCESS SIGNAL: flashrom prints 'Erase/write done' + 'Verifying flash... VERIFIED', and
#     'WRITE-BACK PAGE0: VERIFIED'. (Audit band may differ again from new keypad activity — ignore it.)
#   ESCALATE: any write/verify error, brown-out, or 'WRITE-BACK PAGE0: MISMATCH' -> CH341A in-circuit
#     write is NOT reliable; record + STOP. Do NOT retry-loop a failing write (risk of half-written chip).
```

**Manual-vary list (try these before escalating any step, in order):**
1. Re-seat the SOIC-8 clip — pin-1 dot to clip arrow, press firmly, hold during the command (#1 contact failure mode).
2. **Switch battery state** — CASE A (out) ↔ CASE B (in). This is the decisive in-circuit variable, not a side knob.
3. Swap the clip ribbon cable (clips develop intermittent contacts).
4. Different USB port (avoid unpowered hubs) / power-cycle the CH341A (unplug + re-plug its USB).
5. Swap the CH341A unit (bring a spare board).
6. Confirm the exact chip name with `flashrom -L | grep -i at45db041` and use it for `-c`.

> **Why no "ensure out-of-circuit" item:** this test is **deliberately in-circuit** — that IS the scenario being settled.
> The brown-out is not a setup error to eliminate here; it is the **measured outcome**. The variable you trade is battery state.

---

## B. INTERPRETATION / DECISION FRAMEWORK — mapped to the binary question

The operator's framing is binary: **either the CH341A works in-circuit for the demo, or we acquire more T48s.** Every bench
outcome maps to one side. Then update `T48-KALI-PLAN.md` §6.8 (operator runs it; do not pre-edit).

| Bench outcome (in-circuit) | Diagnosis | Binary verdict | §6.8 |
|---|---|---|---|
| **STEP 3 reads 540,672 + STEP 4 PASS (page 0 identical; diffs audit-band-only) + (if run) STEP 5 WRITE VERIFIED** — in **either** battery state | CH341A's LDO sustains this board in-circuit and reads/writes the native 264-byte DataFlash faithfully | **CH341A WORKS IN-CIRCUIT.** Cheap per-attendee path viable | **(a)** |
| **STEP 3 reads 540,672 + STEP 4 PASS, but STEP 5 write fails / browns out** | Read-faithful in-circuit, write-unreliable (write draws more current → brown-out, or marginal page-program timing) | **CH341A WORKS FOR READS ONLY; injection stays on a T48.** Operator's call whether read-only attendee boards are worth it | **(a\*)** |
| **CASE A (batteries out) brown-outs, CASE B (batteries in) gives contention / corrupt / wrong-ID** — both fail to yield a clean 540,672 read  ◀◀◀ **OBSERVED 2026-05-20 (refined: no-detect via bus loading, NOT a brown-out — see §F.4 bench result)** | Mechanism 1 (CH341A can't power the board) AND Mechanism 2 (live-MCU bus contention / loading) — neither battery state is clean. **T+4g: Mechanism 2 dominated — `No EEPROM/flash device found` both states, CH341A stayed USB-enumerated (no brown-out)** | **CH341A DOES NOT WORK IN-CIRCUIT → ACQUIRE MORE T48s** | **(b)** |
| **STEP 3 reads only 524,288 (binary mode) OR flashrom prompts/needs a page-size switch** | Page-mode **incompatibility** — byte layout won't match injected.bin's 264-byte offsets. **See §C — OTP irreversibility.** | **DROP CH341A → ACQUIRE MORE T48s** | **(b)** |
| **STEP 4 page-0 DIFFERS, or full-image diffs land OUTSIDE the audit band** | Read is corrupt (contention/marginal SPI) even though it "completed" — exactly the silent-bad-data risk | **CH341A NOT TRUSTWORTHY IN-CIRCUIT → ACQUIRE MORE T48s** | **(b)** |
| **Brown-out flood / drops off bus on 2 attempts across BOTH battery states** | CH341A LDO categorically marginal for this board in-circuit at workshop volume | **DROP CH341A → ACQUIRE MORE T48s** | **(b)** |

> Only the **first** row (and arguably the second, for reads only) lets the cheap in-circuit path survive. Every other row =
> **acquire more T48s.** The audit-band-only `cmp` diff is **not** a fail — it is the expected signature of the keypad tests.

> **🔴 T+4g STEP 0b PRE-EMPTS THE BENCH BRANCH — PINOUT MISMATCH (settles §6.8 toward "acquire more T48s").** The STEP 0b
> multimeter readings (pin 7 VCC = **0 V**; ~3.3 V-magnitude appearing on pin 8/SO; I/O pins ≈1.79 V) are the signature of a
> **25-series-wired clip on an AT45DB DataFlash pinout** (see the red box / pin-map table above STEP 0). This is a
> **structural** incompatibility, not a brown-out tuning issue: the clip mis-powers the chip (VCC pin-7↔pin-8 swap) AND
> scrambles SI/SO/SCK/CS. **No amount of battery-state or LDO luck fixes a permuted pinout** — and a clean remap is not
> achievable with a standard clip (you would need a custom pin-7↔pin-8 + data-line crossover adapter per attendee). The
> ≈1.79 V on the I/O lines additionally indicates the **1.8 V adapter is likely still in the path** (must be removed; the
> part needs 2.5–3.6 V). **Engineering verdict: the cheap CH341A path is structurally impractical for this workshop → §6.8
> (b), ACQUIRE MORE T48s.** This conclusion does NOT require a successful read to reach. (Final call left to operator;
> `T48-KALI-PLAN.md` §6.8 deliberately NOT edited here.)

---

## C. PAGE-MODE IRREVERSIBILITY ANALYSIS (unchanged hazard, restated for in-circuit)

The AT45DB041E has a **page-size configuration bit** selecting the factory-default **264-byte ("DataFlash") page** vs a
**256-byte ("binary"/power-of-2) page**. Per the Adesto/Atmel datasheet this is set by a dedicated command and is a
**one-time-programmable (OTP)** operation — **once switched to power-of-2 mode it cannot be returned** to 264-byte mode
(`T4-DIAGNOSTIC-AND-TOOLCHAIN.md` §A.4).

**flashrom's `at45db` driver reads the status register and adapts to whichever page mode the chip is already in** — it scales
geometry 33/32 for 264-byte parts and performs the split-address translation. **In normal `-r`/`-w` it does NOT issue the OTP
page-size command** — that command is outside the read/write path. So the **expected, safe** result is row 1 of §B: a
540,672-byte native read with **no** configuration change.

**Hard guardrail (do NOT perform blindly):** **never run any flashrom command, flag, or DataFlash "configure page size" /
"power-of-2" operation on a workshop chip — least of all the live lock chip.** The re-test uses only `-r` (read) and a single
gated `-w` (write of the native-layout `injected.bin`). If flashrom ever reports a binary/256-byte geometry or prompts to
change page size, **STOP and record it as the §6.8 (b) page-mode-incompatibility outcome** — do not "fix" it by switching
modes. An accidental OTP flip would permanently desync this chip from injected.bin and the research, with no undo. This is
**even more important in-circuit**, where the chip is the live lock you intend to keep functional.

---

## D. A-PRIORI EXPECTATION — IN-CIRCUIT specifically (calling my shot)

The prior version of this doc put brown-out at ~12% to overturn — but **that was for an out-of-circuit loose spare**, where
the CH341A only had to power one chip. **In-circuit, brown-out is the dominant risk, not the tail.** In-circuit the CH341A
must power (CASE A) or contend with (CASE B) the **entire lock board** through the clip — the exact condition that produced
the T+4b `LIBUSB_TRANSFER_ERROR` flood, and the exact condition the T48 only survived because it has a real current-capable
supply and a RESET hold the CH341A lacks. My honest in-circuit call:

- **Most likely (~55%): NEGATIVE — brown-out (CASE A) and/or bus contention (CASE B)** prevents a clean 540,672 read in
  either battery state. **→ acquire more T48s, §6.8 (b).** This is the single most probable result and the operator should
  expect it.
- **Plausible (~20%): a marginal CASE-A read squeaks through** (light enough board quiescent draw that the LDO holds for the
  ~minute-long read) and STEP 4 PASSes for **reads** — but the heavier-current **write (STEP 5) browns out**.
  **→ reads-only, §6.8 (a\*).**
- **Lower (~15%): silent corruption** — a read "completes" but STEP 4 shows page-0 or non-audit diffs (CASE B contention is
  the usual culprit). **→ not trustworthy, §6.8 (b).** This is the dangerous-looking-success case STEP 4 exists to catch.
- **Low (~10%): clean in-circuit read AND write in some battery state.** **→ CH341A works, §6.8 (a).** Possible if this
  board's quiescent current is unusually low and the CH341A unit's LDO is on the strong end — but I would not bank on it.

**Bottom line for the binary decision.** A priori I expect the in-circuit CH341A test to land on the **"acquire more T48s"**
side of the operator's binary — most likely outright brown-out/contention, possibly reads-only at best. The CH341A's value
proposition (cheap take-home board) was always strongest for an **out-of-circuit** read; **in-circuit it is fighting the same
physics the T48 was bought to beat.** If the bench surprises us with a clean in-circuit read+write, that is a genuine win for
the cheap path — but the engineering expectation is that the **T48 remains the reliable in-circuit programmer**, and the
realistic workshop posture is **more T48 stations**, with the CH341A at most an optional take-home read board for an
out-of-circuit chip. The bench output decides which §B row we land on.

---

## F. OPERATOR-PROPOSED PIN-REMAP HARNESS (function-matched adapter)

> **Updated bench facts (supersede the "1.8 V adapter in path" hypothesis in §B's red box):** the operator confirms the
> **1.8 V adapter is NOT connected** — the ≈1.79 V on the I/O pins is the CH341A's own **idle logic level**, not an adapter
> rail. Voltages were measured at the **CH341A onboard lever-clamp ZIF socket** (the 25xx socket the SOIC-8 adapter plugs
> into), confirming that socket is **25-series-wired** (VCC at socket pin 8). The −3.31 V seen on socket pin 8 is the
> CH341A's ~3.3 V VCC rail read with **reversed probe polarity** → this CH341A runs at **3.3 V** (NOT the 5 V-flaw board —
> good). The pinout mismatch (§B red box) remains the decisive blocker; this section designs the operator's fix for it.

The operator proposes a **pre-wired function-matched jumper harness** sitting between the CH341A lever socket and the
SOIC-8 clip, wiring each CH341A signal to the AT45DB041E pin **of the same function** (not the same pin number). This is a
real, correct fix for the *pinout* mismatch and a good pedagogical artifact ("adapt a programmer to a non-standard
pinout"). It does **not** address brown-out (in-circuit) or page-mode — see the §F.3 viability tree.

### F.1 Harness wiring table (function-matched)

Both pinouts are notch-up, pins 1–4 left top→bottom, 5–8 right bottom→top. Datasheet anchors:
**AT45DB041E SOIC-8:** 1=SI(MOSI in), 2=SCK, 3=RESET#(active-low, internal pull-up), 4=GND, 5=CS#(active-low),
6=WP#(active-low, internal pull-up), 7=VCC, 8=SO(MISO out).
**25-series (W25Q-style) SOIC-8 that the CH341A socket drives:** 1=CS#, 2=DO(MISO), 3=WP#/IO2, 4=GND, 5=DI(MOSI),
6=CLK, 7=HOLD#/IO3, 8=VCC.

| Function | CH341A socket pin (25-series) | → | AT45DB041E clip pin | Notes |
|---|---|---|---|---|
| **VCC** | **8** (VCC) | → | **7** (VCC) | the VCC pin-8→pin-7 move — the headline fix |
| **GND** | **4** (GND) | → | **4** (GND) | only common pin; straight-through |
| **SCK / clock** | **6** (CLK) | → | **2** (SCK) | clock |
| **MOSI / data-in** | **5** (DI) | → | **1** (SI) | host→chip |
| **MISO / data-out** | **2** (DO) | → | **8** (SO) | chip→host |
| **CS#** | **1** (CS#) | → | **5** (CS#) | active-low chip select |
| **RESET#** (tie-high) | from CH341A socket **pin 8** (VCC) | → | **3** (RESET#) | **tie HIGH to VCC** — see ruling |
| **WP#** (tie-high) | from CH341A socket **pin 8** (VCC) | → | **6** (WP#) | **tie HIGH to VCC** — see ruling |
| *(unused)* | **3** (WP#/IO2) | — | *not connected* | 25-series-only function; leave floating |
| *(unused)* | **7** (HOLD#/IO3) | — | *not connected* | 25-series-only function; leave floating |

**RESET#/WP# ruling — TIE BOTH HIGH TO VCC at the harness (recommended).** Both are active-low with internal pull-ups,
so the chip would *technically* run with pins 3 and 6 left open. **But tie them high anyway**, for three reasons:
(1) it **guarantees** the chip is out of reset (RESET# high) and write-unprotected (WP# high) regardless of pull-up
strength or in-circuit board pull-downs; (2) it removes two floating, high-impedance inputs that can pick up noise on a
hand-built clip-lead harness; (3) it costs two short jumpers off the VCC node. **WP# high is required for the §F.2 STEP 5
write test** — leave it open and a board-side pull-down (in-circuit) could keep the chip write-protected and silently fail
the write. Tie both to the **AT45DB pin-7 VCC node** (i.e. branch off the same wire that drives pin 7), not to the CH341A
socket pin 8 directly via a separate run — electrically identical, but a single VCC node on the clip side is cleaner to
verify.

**Per-wire build list (6 signal wires + 2 tie-high jumpers):**
1. CH341A socket **pin 8** → AT45DB clip **pin 7**  (VCC)
2. CH341A socket **pin 4** → AT45DB clip **pin 4**  (GND)
3. CH341A socket **pin 6** → AT45DB clip **pin 2**  (SCK ← CLK)
4. CH341A socket **pin 5** → AT45DB clip **pin 1**  (SI ← DI / MOSI)
5. CH341A socket **pin 2** → AT45DB clip **pin 8**  (SO → DO / MISO)
6. CH341A socket **pin 1** → AT45DB clip **pin 5**  (CS# ← CS#)
7. AT45DB clip **pin 7 (VCC node)** → AT45DB clip **pin 3**  (RESET# tie-high)
8. AT45DB clip **pin 7 (VCC node)** → AT45DB clip **pin 6**  (WP# tie-high)
   — CH341A socket **pin 3** and **pin 7**: **leave unconnected.**

**🔴 Destructive-miswire flags (the ones that damage the chip — verify these in §F.2 before power):**
- **VCC ↔ GND short** (wire 1's pin-7 destination touching wire 2's pin-4, or socket 8↔4 bridged): dead short across the
  CH341A LDO → brown-out at best, blown LDO at worst. **#1 thing to continuity-check.**
- **VCC onto a data/clock pin** — the *exact* failure the un-remapped clip causes: VCC (socket 8) landing on AT45DB pin 8
  (SO, an **output** the chip drives) fights the chip's output driver → can damage SO. Also VCC onto pin 1/2/5.
  Double-check wire 1 lands on **pin 7 only**, and that the tie-high jumpers go to **3 and 6 only** (both safe high-Z
  inputs), never to 1/2/5/8.
- **Reversed VCC/GND** (pin 7 ↔ pin 4 swapped): reverse-polarity across the chip. Confirm pin 7 is the positive node.
- Less destructive but breaks the read: SCK/MOSI/MISO/CS swapped among themselves (no detect / garbage), or RESET# tied
  **low** (chip held in reset, no response).

### F.2 BUILD + VERIFY + TEST BENCH BLOCK — *** OUT-OF-CIRCUIT on the SPARE chip ***

> **Critical framing:** test this harness **OUT-OF-CIRCUIT** — on a **loose spare uncooked AT45DB041E** (or a board that is
> NOT otherwise powered), **NOT** the in-circuit live lock board. The harness fixes the *pinout*; it does **nothing** for
> brown-out. Isolating to out-of-circuit (CH341A powers exactly one chip) gives a **clean answer to the pinout-fix
> question** with brown-out removed as a variable. Run top-to-bottom; each step has SUCCESS / ESCALATE / STOP.

```bash
# =====================================================================
# T+4g  PIN-REMAP HARNESS  — BUILD + VERIFY + TEST   *** OUT-OF-CIRCUIT ***
#   target: a LOOSE SPARE AT45DB041E (or an unpowered board). NOT the live lock.
#   harness: function-matched (see §F.1 table). CH341A confirmed 3.3 V.
# =====================================================================
mkdir -p ~/t4g-harness && cd ~/t4g-harness
REF=/home/qweary/Desktop/toorcamp-2026-dumps/T+4g-second-board-diagnostic/injected.bin
# (REF used only for an optional write test; the read/probe answer needs no reference.)

# ---------------------------------------------------------------------
# STEP H0 — BUILD the harness per §F.1 (power OFF: CH341A UNPLUGGED, no chip in clip)
# ---------------------------------------------------------------------
#   Wire the 6 signal lines + 2 tie-high jumpers exactly per the §F.1 per-wire build list:
#     1) CH341A sock 8 -> clip 7   (VCC)
#     2) CH341A sock 4 -> clip 4   (GND)
#     3) CH341A sock 6 -> clip 2   (SCK)
#     4) CH341A sock 5 -> clip 1   (SI/MOSI)
#     5) CH341A sock 2 -> clip 8   (SO/MISO)
#     6) CH341A sock 1 -> clip 5   (CS#)
#     7) clip 7 (VCC) -> clip 3    (RESET# tie-high)
#     8) clip 7 (VCC) -> clip 6    (WP# tie-high)
#   Leave CH341A sock 3 and sock 7 UNCONNECTED. Label both ends. Keep leads short.

# ---------------------------------------------------------------------
# STEP H1 — CONTINUITY VERIFY  *** BEFORE ANY POWER ***  (multimeter in continuity/beep)
#   CH341A UNPLUGGED, no chip in the clip. Probe socket-pin <-> clip-pin.
# ---------------------------------------------------------------------
#   1a. EACH mapped wire beeps end-to-end:
#       sock8<->clip7, sock4<->clip4, sock6<->clip2, sock5<->clip1, sock2<->clip8, sock1<->clip5,
#       clip7<->clip3, clip7<->clip6.
#       SUCCESS: all eight beep.   ESCALATE: any open -> reseat/resolder that wire, re-test.
#   1b. ISOLATION (these MUST NOT beep — destructive if they do):
#       clip7 (VCC) <-> clip4 (GND)        -> MUST be open   (VCC-GND short check)
#       clip7 (VCC) <-> clip1, clip2, clip5, clip8  -> each MUST be open  (VCC onto data/clock/CS)
#       clip3 (RESET#) and clip6 (WP#) should each beep ONLY to clip7 (the tie-high), nothing else.
#       SUCCESS: every isolation pair is OPEN.
#       STOP (DO NOT POWER): ANY isolation pair beeps -> a destructive short. Fix before STEP H2.

# ---------------------------------------------------------------------
# STEP H2 — POWER VERIFY  (CH341A plugged into USB; harness on the clip; clip NOT yet on a chip)
#   Multimeter on DC volts. RED probe = AT45DB clip pin 7, BLACK probe = clip pin 4 (GND).
# ---------------------------------------------------------------------
lsusb | grep -i '1a86:5512' || echo 'CH341A NOT enumerated'
#   Measure clip pin 7 vs pin 4:
#     SUCCESS SIGNAL: clip pin 7 reads +3.0 .. +3.6 V (nominally +3.3 V)  -> the remap MOVED VCC to pin 7. PROCEED.
#     Also sanity: clip pin 8 (SO) should NOT sit at VCC now (it's an input-floating data line here) -> expect ~0 V / idle.
#   STOP THRESHOLD:
#     clip pin 7 = 0 V            -> VCC not routed to 7 (check wire 1 / sock-8 contact). FIX, do not clip a chip.
#     VCC shows on pin 8 not 7    -> harness not remapping (built like a straight clip). FIX wire 1.
#     pin 7 = ~5 V                -> would mean a 5 V-rail CH341A after all; STOP, do not use on the spare.
#   ESCALATE: pin 7 outside 2.7-3.6 V after reseating sock-8 -> bad socket contact / bad unit; swap once, else STOP.

# ---------------------------------------------------------------------
# STEP H3 — flashrom PROBE  (OUT-OF-CIRCUIT; clip the SPARE chip, pin-1 dot <-> clip arrow)
# ---------------------------------------------------------------------
sudo flashrom -p ch341a_spi                         # auto-probe
sudo flashrom -p ch341a_spi -c "AT45DB041D"         # if auto-probe ambiguous, pin the name
#   SUCCESS SIGNAL: 'Found Atmel flash chip "AT45DB041D" (528 kB, SPI) on ch341a_spi.'
#     -> the function-matched harness WORKS: the chip enumerates. This alone validates the pinout fix.
#   ESCALATE: 'No EEPROM/flash device found' -> reseat clip (pin-1!), retry once; then re-verify H1 wire map
#     (most likely a swapped SCK/MOSI/MISO/CS). STOP after 2 clean reseat attempts with no detect.

# ---------------------------------------------------------------------
# STEP H4 — flashrom READ  (read-only; produces a file)  *** RECORD THE EXACT BYTE SIZE ***
# ---------------------------------------------------------------------
sudo flashrom -p ch341a_spi -c "AT45DB041D" -r harness-spare.bin
ls -l harness-spare.bin            # <-- REPORT THIS EXACT BYTE COUNT
sudo md5sum harness-spare.bin
#   THE SIZE IS THE PAGE-MODE ANSWER:
#     540672 (2048 x 264) => NATIVE 264-byte mode, full read  -> maps to injected.bin offsets. BEST CASE (§F.3 a).
#     524288 (512 KiB)    => BINARY 256-byte mode -> layout will NOT map to build-injected.py native offsets (§F.3 b).
#     short / 0 / partial => read aborted (out-of-circuit this should NOT brown out; suspect contact/cable).
#   SUCCESS SIGNAL: 'Reading flash... done', file produced, size recorded.
#   ESCALATE: partial/abort out-of-circuit -> reseat clip + swap ribbon, retry once; else STOP.

# ---------------------------------------------------------------------
# STEP H5 — SANITY-CHECK the dump (no T48 reference needed; use one if you have it for this spare)
# ---------------------------------------------------------------------
# 5a. page-0 low-nibble invariant (page-0 byte 0 low nibble should be 0xD per the page-0 invariant):
sudo xxd -l 16 harness-spare.bin
#     SUCCESS hint: byte 0 low nibble = 0xD; data looks non-uniform (not all 00 / all FF).
# 5b. if (and ONLY if) this spare was previously T48-imaged to a known file, compare:
#     cmp <known-spare-ref.bin> harness-spare.bin   # else skip — do NOT compare to injected.bin (different chip)
# 5c. OPTIONAL write test (modifies the spare; out-of-circuit, WP# is tied high so writes are enabled):
#     sudo flashrom -p ch341a_spi -c "AT45DB041D" -w "$REF"     # only meaningful if H4 read 540672
#     SUCCESS: 'Erase/write done' + 'Verifying flash... VERIFIED'.
#   >>> If H4 read 524288 (binary mode): DO NOT write injected.bin (native 540672 layout) to it — offsets won't map.
```

**Manual-vary list (try before escalating any step, in order):**
1. Reseat the SOIC-8 clip — pin-1 dot to clip arrow, press firmly, hold during the command (#1 contact failure).
2. Reseat the harness in the CH341A lever socket — press the clamp fully.
3. Swap the clip ribbon cable.
4. Re-verify H1 continuity for the four data/clock/CS wires (a swap there = detect-but-garbage or no-detect).
5. Different USB port (avoid unpowered hubs); power-cycle the CH341A.
6. Confirm chip name with `flashrom -L | grep -i at45db041` and use it for `-c`.

**GLOBAL STOP RULE:** if H2 cannot put ≈3.3 V on clip pin 7, or H3 cannot detect the chip after two clean reseats with a
verified-continuous harness, **STOP** — the pinout-fix attempt has failed and the §6.8 verdict reverts to "acquire more
T48s." Out-of-circuit there is **no brown-out excuse**, so a failure here is a real harness/contact fault, not physics.

### F.3 HONEST VIABILITY VERDICT (even with a perfect harness)

The harness is a **correct fix for the pinout mismatch** — the one blocker it can actually remove. Two *other* blockers
remain. Decision tree on the H4 byte-size outcome:

- **(a) H4 reads native 540,672 + H5 data maps (page-0 nibble 0xD, non-uniform):** the function-matched harness yields a
  **usable OUT-OF-CIRCUIT read path** (and, if H5c write VERIFIES, a write path too). The native 264-byte layout maps to
  `build-injected.py`'s 540,672-byte offsets. **This is a genuine win for the cheap path as an out-of-circuit read/take-home
  board** and a strong pedagogical artifact — revisit §6.8 toward (a)/(a\*) **for the out-of-circuit case**. It does **not**
  rehabilitate in-circuit use (see (c)).

- **(b) H4 reads only 524,288 (binary 256-byte mode):** the harness fixed the pinout, but the **page-mode mismatch still
  blocks faithful native images.** A 256-byte-geometry dump will **not** line up with injected.bin's / `build-injected.py`'s
  native-540,672 byte offsets — every page-boundary past page 0 is shifted by the 264↔256 (33/32) scaling, so the injected
  code/patch bytes land at the wrong file offsets. **CH341A is still not a drop-in for the injection attack** even though
  probe and read "succeeded." It can still serve as a **teaching demo** (show attendees the read working, then explain why
  the offsets don't map) — but it is not an injection tool. Map to §6.8 (b).

- **(c) Brown-out remains for ANY in-circuit use, regardless of the harness.** The harness changes *pin routing*, not the
  CH341A's LDO current capacity. In-circuit it must still power (batteries-out) or contend with (batteries-in) the whole
  lock board through the clip — the §D physics is unchanged. So even outcome (a) only buys an **out-of-circuit** path; the
  T48 remains the in-circuit programmer.

**My honest page-mode expectation.** flashrom's `at45db` driver reads the AT45DB status register and **adapts to whichever
page mode the chip is already in** (§C; `T4-DIAGNOSTIC-AND-TOOLCHAIN.md` §A.2/§A.4). This spare is an **uncooked**
AT45DB041E, i.e. still in its **factory-default 264-byte DataFlash mode** (the power-of-2 switch is OTP and has not been
issued). So the `at45db` driver should detect 264-byte geometry and read the **native 540,672 bytes** — i.e. I expect
**outcome (a)** out-of-circuit on a virgin spare, ≈70–75% likely, with the residual going to contact/cable faults rather
than to (b). The (b) "binary mode" outcome is only expected if this particular spare was previously flipped to power-of-2
mode — confirm by reading the size (H4). **Net: build the harness.** It is cheap, it is the right fix for the pinout, the
pedagogy is real ("function-match a programmer to a non-standard pinout"), and out-of-circuit on a virgin spare I expect a
faithful native 540,672-byte read. Just do not expect it to replace the T48 for **in-circuit** injection — that is the
brown-out wall (c), which no harness moves. Final §6.8 call left to the operator.

### F.4 — IN-CIRCUIT TEST THROUGH THE HARNESS *** the live `111111` lock board ***

> **Honest framing — read before clipping on.** Clipping the CH341A onto a **live** board through the harness is the
> *exact physics the T48 was bought to beat.* The §F harness removes the **pinout** objection (VCC pin-8→pin-7, data-line
> crossover) — and that is real. It does **NOT** remove the **power** objection, and it likely **worsens** brown-out: the
> harness adds lead length, contact resistance, and inductance in series on the VCC/GND path, so the CH341A's weak ~3.3 V
> LDO droops **harder** under the board's load than a direct clip would. Realistic expectation: this most likely **browns
> out** (CASE A) or **contends** (CASE B). If it does, that is a *clean* result — it maps straight to "acquire T48," which
> the operator has already judged the **stronger demo** (real current-capable supply + RESET hold). We are not hoping the
> CH341A wins here; we are settling §6.8 (a)/(b) for the in-circuit-through-harness case with eyes open.
>
> **This is §A STEPS 1–5 with the §F harness in the signal path** — probe → read → exact-byte-size → compare-to-injected.bin
> → optional gated write — facing the same brown-out + page-mode walls, now through the harness.

> **GATE — H1 + H2 MUST HAVE PASSED FIRST (do NOT duplicate them; see §F.2).** Before clipping onto the live board:
> **(H1)** continuity verified — all 8 mapped wires beep, all isolation pairs OPEN (no VCC↔GND / VCC↔data short); and
> **(H2)** with the CH341A on USB and the clip EMPTY, clip **pin 7 reads ≈3.3 V (2.7–3.6 V)** and pin 8 is NOT at VCC.
> If H1 or H2 has not passed, STOP and finish §F.2 — clipping a mis-wired or mis-powered harness onto the **live lock**
> can damage the lock MCU, not just a loose chip.

> **GLOBAL BROWN-OUT WATCH (every CH341A step):** `LIBUSB_TRANSFER_ERROR` / `Failed to write N bytes` flood, OR the
> CH341A vanishing from `lsusb` mid-command, OR `dmesg` xHCI re-enumeration cycling = the CH341A is browning out under the
> board's load **through the harness**. Expected dominant failure (CASE A), likely (CASE B rail-fight).
> **GLOBAL STOP:** brown-out floods on **2 attempts across BOTH battery states** = the NEGATIVE result, §6.8 **(b)** —
> stop, do **not** force.

```bash
# =====================================================================
# T+4g  IN-CIRCUIT TEST THROUGH THE HARNESS   *** LIVE 111111 LOCK BOARD ***
#   PRECONDITION: §F.2 H1 (continuity) AND H2 (clip pin7 = 3.3 V, clip empty) PASSED.
#   target: the live lock-board chip the T48 programmed this session (code 111111)
#   ground truth: injected.bin  (MD5 56947205a9cffa1de45f6b3f0f8611f5, 540672 B)
#   harness: function-matched per §F.1, in the signal path (clip side faces the live board)
# =====================================================================
mkdir -p ~/t4g-harness-ic && cd ~/t4g-harness-ic
REF=/home/qweary/Desktop/toorcamp-2026-dumps/T+4g-second-board-diagnostic/injected.bin
sudo md5sum "$REF"     # MUST print 56947205a9cffa1de45f6b3f0f8611f5  (re-confirm ground truth)

# ---------------------------------------------------------------------
# STEP IC0 — GATE CONFIRM (no new measurement — just confirm §F.2 results stand)
#   >>> H1 PASSED: all 8 wires beep, all isolation pairs OPEN (no VCC-GND / VCC-data short).
#   >>> H2 PASSED: clip pin 7 = +3.0..+3.6 V with clip EMPTY; pin 8 NOT at VCC.
#   If either is in doubt, STOP and re-run §F.2 H1/H2. Do NOT clip the live board on an unverified harness.
# ---------------------------------------------------------------------

# ---------------------------------------------------------------------
# STEP IC1 — CLIP-ON ORDER  (this exact order)
#   1) CH341A already plugged into USB (it was, for H2).
#   2) Harness verified (H2 just passed). Clip is EMPTY right now.
#   3) NOW clip the harness'd SOIC-8 onto the 111111 board's chip:
#        AT45DB pin-1 DOT  <->  clip pin-1 (arrow).  Press firmly, hold during commands.
#   4) Decide battery state per IC2 (try CASE A first), THEN probe.
# ---------------------------------------------------------------------
lsusb | grep -i '1a86:5512' || echo 'CH341A NOT enumerated (1a86:5512 absent)'
#   SUCCESS SIGNAL: CH341A still enumerates after the clip goes on the live board.
#   ESCALATE: if 1a86:5512 DROPS the instant the clip touches the board -> immediate brown-out/short;
#     UNCLIP, re-confirm H1 isolation (a VCC-data contact on the live board), retry once, else STOP.

# ---------------------------------------------------------------------
# STEP IC2 — PROBE, IN-CIRCUIT THROUGH HARNESS  (identify only; no read, no write)
#   *** BATTERY-STATE BRANCH — CASE A first (lower risk), then CASE B if needed ***
# ---------------------------------------------------------------------
# -- CASE A: BATTERIES OUT (lock MCU dead; CH341A must source the WHOLE board through harness+clip) --
#    ⚠ EXPECTED DOMINANT FAILURE: the harness's added lead length + contact resistance + inductance on the
#    VCC/GND path makes brown-out MORE likely here than a direct clip (more series R/L -> worse droop under
#    the board's load). This is the realistic "attendee clips a battery-pulled lock" case.
sudo flashrom -p ch341a_spi                         # auto-probe
sudo flashrom -p ch341a_spi -c "AT45DB041D"         # if auto-probe ambiguous, pin the name
#   SUCCESS SIGNAL: 'Found Atmel flash chip "AT45DB041D" (528 kB, SPI) on ch341a_spi.'
#     READ THE SIZE: ~528 kB (540672) => native 264-byte mode GOOD. ~512 kB (524288) => binary mode (FLAG, §C/§F.3).
#   IF brown-out flood (LIBUSB_TRANSFER_ERROR / drops off lsusb): Mechanism 1 — through the harness the CH341A
#     can't power the board. Re-seat clip ONCE, retry ONCE. Still floods -> go to CASE B.
#
# -- CASE B: BATTERIES IN (lock MCU live; it drives/contends on the shared SPI bus; the lock's 3.3 V rail
#            meets the CH341A's THROUGH THE HARNESS) --
#    ⚠ RAIL-FIGHT RISK to BOTH the lock MCU and the CH341A (two 3.3 V rails contending across the harness),
#    plus bus contention / corrupt probe. BRIEF probe only — do NOT linger.
sudo flashrom -p ch341a_spi -c "AT45DB041D"
#   SUCCESS SIGNAL: same 'Found ... AT45DB041D (528 kB)'. A clean probe here is LESS likely than CASE A.
#   IF garbage/no-detect/wrong-ID or brown-out: contention or rail-fight — record it, UNCLIP promptly.
#   GLOBAL STOP: BOTH CASE A and CASE B brown out / fail to probe across 2 attempts each ->
#     NEGATIVE result, §6.8 (b). STOP. Do not force. (See BROWN-OUT WATCH.)

# ---------------------------------------------------------------------
# STEP IC3 — READ, IN-CIRCUIT THROUGH HARNESS  (read-only; produces a file)  *** RECORD EXACT BYTE SIZE ***
#   Use whichever battery state PROBED CLEAN in IC2. Use the name IC2 confirmed.
# ---------------------------------------------------------------------
sudo flashrom -p ch341a_spi -c "AT45DB041D" -r ic-harness.bin
ls -l ic-harness.bin            # <-- REPORT THIS EXACT BYTE COUNT
sudo md5sum ic-harness.bin
#   THE EXACT BYTE SIZE IS THE PAGE-MODE + COMPLETENESS ANSWER:
#     540672 => native 264-byte mode, full read (matches injected.bin scope)              GOOD
#     524288 => binary 256-byte mode (page-mode mismatch -> §C/§F.3; do NOT compare/write)
#     short / 0 / partial => brown-out aborted the read mid-stream (the harness-droop signature)
#   SUCCESS SIGNAL: 'Reading flash... done' with NO error AND a file is produced.
#   ESCALATE: read aborts / partial / LIBUSB flood -> BROWN-OUT WATCH; re-seat + retry ONCE same battery
#     state, then try the OTHER battery state ONCE. Still no full 540672 read across both -> §6.8 (b), STOP.

# ---------------------------------------------------------------------
# STEP IC4 — COMPARE ic-harness.bin against injected.bin  (full + page-0/code-region focused)
#   PASS rule (same as §A STEP 4): code region matches; the ONLY tolerated full-image diff is the audit band.
# ---------------------------------------------------------------------
# 4a. sizes + hashes side by side
ls -l "$REF" ic-harness.bin
sudo md5sum "$REF" ic-harness.bin
#     IDENTICAL md5 => perfect match (audit band unchanged, or batteries stayed out). Best case.

# 4b. PAGE 0 / CODE REGION compare — the PATCH-MATCH check (the bytes the T48 injected):
cmp <(sudo head -c 264 "$REF") <(head -c 264 ic-harness.bin) \
    && echo 'PAGE0 CODE REGION: IDENTICAL (patch confirmed)' \
    || echo 'PAGE0 CODE REGION: DIFFERS  <-- REAL mismatch, NOT the audit band'
#     SUCCESS SIGNAL: 'PAGE0 CODE REGION: IDENTICAL' => the injected code/patch bytes read back faithfully.

# 4c. FULL-IMAGE compare — locate where (if anywhere) the images diverge:
cmp -l "$REF" ic-harness.bin | awk '{printf "0x%X\n",$1-1}' | sort -u > /tmp/ic-diff-offsets.txt
if [ ! -s /tmp/ic-diff-offsets.txt ]; then
  echo 'FULL IMAGE: BYTE-IDENTICAL'
else
  echo "FULL IMAGE: differs at $(wc -l </tmp/ic-diff-offsets.txt) offsets; range:"
  head -1 /tmp/ic-diff-offsets.txt; tail -1 /tmp/ic-diff-offsets.txt
  # PASS-if-audit-only test: are ALL diffs inside the audit band 0x42000..0x46938?
  awk 'BEGIN{ok=1} { d=strtonum($0); if (d<0x42000 || d>0x46938) ok=0 }
       END{ if(ok) print "ALL DIFFS INSIDE AUDIT BAND 0x42000-0x46938 => PASS (expected from keypad tests)";
            else print "DIFFS OUTSIDE AUDIT BAND => REAL MISMATCH, investigate" }' /tmp/ic-diff-offsets.txt
fi
#   SUCCESS SIGNAL (PASS): EITHER 'FULL IMAGE: BYTE-IDENTICAL'
#     OR 'PAGE0 CODE REGION: IDENTICAL' + 'ALL DIFFS INSIDE AUDIT BAND ... => PASS'.
#   FAIL: page 0 differs, or diffs land OUTSIDE 0x42000-0x46938 -> the read is NOT faithful (contention/marginal
#     SPI/page-mode). Do NOT proceed to IC5. Map to §B.

# ---------------------------------------------------------------------
# STEP IC5 — OPTIONAL IN-CIRCUIT WRITE TEST  (modifies the live chip)  *** GATED ***
#   ONLY if IC2 PROBED clean, IC3 READ a full 540672 bytes, AND IC4 PASSED. Else SKIP entirely.
#   Use the SAME battery state that read clean.
#   ⚠ Writing in-circuit draws MORE current than reading -> through the harness the brown-out risk is even
#     HIGHER here than IC3. Single attempt; do NOT retry-loop a failing write (half-written chip risk).
# ---------------------------------------------------------------------
sudo flashrom -p ch341a_spi -c "AT45DB041D" -w "$REF"
sudo flashrom -p ch341a_spi -c "AT45DB041D" -r ic-verify.bin
cmp <(sudo head -c 264 "$REF") <(head -c 264 ic-verify.bin) \
    && echo 'WRITE-BACK PAGE0: VERIFIED' || echo 'WRITE-BACK PAGE0: MISMATCH'
#   SUCCESS SIGNAL: flashrom prints 'Erase/write done' + 'Verifying flash... VERIFIED', and
#     'WRITE-BACK PAGE0: VERIFIED'. (Audit band may differ again from new keypad activity — ignore it.)
#   ESCALATE: any write/verify error, brown-out, or 'WRITE-BACK PAGE0: MISMATCH' -> CH341A in-circuit write
#     through the harness is NOT reliable; record + STOP.
```

**Manual-vary list (try before escalating any step, in order):**
1. Re-seat the SOIC-8 clip — pin-1 dot to clip arrow, press firmly, **hold** during the command (#1 contact failure).
2. **Switch battery state** — CASE A (out) ↔ CASE B (in). The decisive in-circuit variable, not a side knob.
3. Re-seat the harness in the CH341A lever socket (press the clamp fully) — harness leads are the new series-R suspect.
4. Swap the clip ribbon cable.
5. Different USB port (avoid unpowered hubs); power-cycle the CH341A.
6. Confirm chip name with `flashrom -L | grep -i at45db041` and use it for `-c`.

> **GLOBAL STOP RULE (in-circuit-through-harness):** brown-out flood / drops off bus on **2 attempts across BOTH
> battery states** = NEGATIVE, §6.8 **(b)** — stop, do not force. Unlike §F.2 (out-of-circuit, "no brown-out excuse"),
> here brown-out IS the expected physics and the clean read of the result. A brown-out here is not a harness fault to
> chase — it is the answer: **acquire T48**, the stronger demo.

> **Where this lands on §B.** A clean IC3 540,672 read + IC4 PASS (+ IC5 VERIFIED) in either battery state = §B row 1,
> §6.8 **(a)** — cheap in-circuit path viable. Read-clean but IC5 write browns out = §B row 2, §6.8 **(a\*)**, reads-only.
> Brown-out/contention/page-mode-binary/silent-corruption = the "acquire more T48s" rows, §6.8 **(b)**. Do NOT pre-edit
> `T48-KALI-PLAN.md` §6.8 — map the bench output onto §B, then the operator finalizes §6.8.

### F.4 — BENCH RESULT (2026-05-20, T+4g) — DECISIVE NEGATIVE → §6.8 (b)

> **✅ RAN. RESULT: in-circuit-through-harness probe = `No EEPROM/flash device found`, both battery states.
> NOT a brown-out. → §6.8 (b), acquire more T48s. The CH341A in-circuit path is conclusively closed.**

| Step | What happened | Reading |
|---|---|---|
| §F.2 **H1** (continuity) | All 8 mapped wires beep; all isolation pairs OPEN (no VCC↔GND, no VCC↔data short) | **PASS** — harness wired correctly |
| §F.2 **H2** (power, clip empty) | Clip **pin 7 ≈ 3.3 V**; pin 8 not at VCC | **PASS** — pinout fix delivers VCC to the right pin |
| **IC2** probe (auto + `-c "AT45DB041D"`) | `No EEPROM/flash device found` — **batteries IN and batteries OUT** | **NO-DETECT both states** |
| **GLOBAL BROWN-OUT WATCH** | CH341A stayed enumerated on USB (`1a86:5512` present) throughout; no `LIBUSB_TRANSFER_ERROR` flood, no drop-off, no xHCI re-enumeration | **NOT a brown-out — this is a DETECTION failure, not a power collapse** |
| Battery-IN observation | Lock board went to a **red flashing LED** with the clip on | lock MCU is **powered, active, contending** on the shared SPI bus |
| Reseat ladder | Operator reseated the clip many times, both battery states | **EXHAUSTED — §F.4 GLOBAL STOP threshold met** |

**Interpretation (mechanism).** H1/H2 already rule out a wiring or power-delivery fault — the pinout fix
worked and 3.3 V reaches AT45DB pin 7. Yet flashrom cannot enumerate the chip in **either** battery state,
**without** browning out. The dominant mechanism is **in-circuit shared-bus contention / loading defeating
the CH341A's weak SPI drivers**: the AT45DB041E shares its SPI bus with the lock MCU (the lock's normal
flash interface). **Batteries IN** — the live MCU actively drives/holds the shared CS#/CLK/MISO lines (the
red flashing LED confirms it is awake and reacting to the bus), so the CH341A's weak drivers can't take the
bus. **Batteries OUT** — the unpowered MCU's GPIO/ESD clamps on the shared lines load the bus enough that
the CH341A's weak drivers can't establish clean SPI signaling. The T48 succeeds in-circuit (T+4e) because
its **stronger, current-capable output drivers overpower the MCU loading/contention** (plus a RESET hold)
where the CH341A's cannot. The only alternative explanation — marginal clip contact — is ruled out by the
**exhausted-reseat-across-both-battery-states** evidence combined with H1/H2 passing; a contact fault would
not be invariant across that many reseats in both states. **Contention/driver-strength is the dominant
explanation, not a harness fault.**

**This maps to §B row 3** ("CASE A … CASE B … both fail to yield a clean 540,672 read" → Mechanism 2
live-MCU bus contention / loading) — refined: the failure mode here is **no-detect via bus loading, without
a brown-out**, rather than the LDO collapse §B/§D forecast as the dominant in-circuit risk. Either way the
**verdict is identical: CH341A DOES NOT WORK IN-CIRCUIT → §6.8 (b), ACQUIRE MORE T48s.** `T48-KALI-PLAN.md`
§6.8 has been finalized to (b) accordingly (2026-05-20).

**Salvage value.** The harness is NOT wasted effort: it correctly remaps the CH341A↔AT45DB041E pinout (H1/H2
proven), so it remains a valid **out-of-circuit** read path on a loose spare and a genuine **pedagogical
artifact** — a "how to function-match a programmer to a non-standard pinout" demo. It is **not** an
in-circuit injection tool. The workshop's per-station programmer is the **T48** (in-circuit, validated
end-to-end T+4e); the CH341A/harness, if used at all, is an optional out-of-circuit side-demo, not a station
tool.

**Anything left to try? — No, conclusively done.** Remaining in-circuit avenues (lifting the chip's CS#,
holding the MCU in reset) all require board modification, which violates the workshop's no-desolder /
no-board-mod constraint, and the T48 already works in-circuit end-to-end. **Recommendation: stop here,
proceed with the T48.**

---

## E. Cited sources

- `T48-KALI-PLAN.md` — §6.8 (decision scaffolding being settled), §4.2/§4.3 (540,672-byte main array; page-0 user-code at
  file offset `0x00000`, first bytes `fd 12 22 ff`), T+4e validation (in-circuit T48 read+write+verify).
- `T4-DIAGNOSTIC-AND-TOOLCHAIN.md` — §A.2 (flashrom `at45db`; chip presents as `AT45DB041D`), §A.4 (page-mode table + OTP
  irreversibility), §A.5 (5 V I/O stress), §F.0 / STAGE 3 / STAGE 4-bis (in-circuit dual-power brown-out: Mechanism 1
  CH341A can't power the board, Mechanism 2 live-MCU SPI bus contention).
- `injected.bin` — ground-truth payload the T48 wrote+verified this session: 540,672 bytes, **MD5
  `56947205a9cffa1de45f6b3f0f8611f5`** (re-confirmed at bench, T+4g).
- Bench pre-flight (this box, T+4g): `flashrom v1.6.0`, `ch341a_spi` present, `flashrom -L` lists `AT45DB041D` only.

**STATUS (FINAL, 2026-05-20 / T+4g):** ✅ **RAN — DECISIVE NEGATIVE for the in-circuit CH341A path.** §F.4 in-circuit-through-harness
probe = `No EEPROM/flash device found` in both battery states; harness pinout fix verified (H1/H2 PASS); NOT a brown-out
(CH341A stayed USB-enumerated); red-LED MCU contention battery-in. Maps to §B row 3 (refined: no-detect via shared-bus
loading, not LDO collapse). **`T48-KALI-PLAN.md` §6.8 FINALIZED to (b) — acquire 3 more T48s (4 stations total); CH341A
dropped as a per-attendee programmer.** Harness retained as an out-of-circuit read path + pedagogical artifact. CH341A
in-circuit path conclusively closed — proceed with the T48.

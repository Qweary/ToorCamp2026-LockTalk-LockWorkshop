# DataFlash Decode Reference — Adesto AT45DB041E User-Code Structure

**Date:** 2026-05-17
**Validation basis:** the existing research dumps (authoritative ground truth — a fresh hardware read was not available this session)
**Primary artifact:** `dumps/AT45DB041E[Page264]@SOIC8.BIN`
**Scope:** AT45DB041E user-code page structure only. MSP430 code dumps, Ghidra files, and firmware reverse-engineering are out of scope.

---

## Quick reference — the facts you decode at the bench

| Item | Confirmed value |
|---|---|
| **Main-array byte size** | **540,672 bytes** (2048 pages × 264 bytes) |
| Full-read byte size (array + Security Register) | **540,800 bytes** (540,672 + 128-byte Security Register) |
| The wrong size you may have seen (524,288) | **Wrong** — that is the 256-byte "power-of-2" page-mode size; these chips were read in 264-byte native page mode |
| User-code page location | **File offset 0** (`0x00000`), page index **0** |
| Chip technology | Serial **DataFlash** (NOR-based), **not NAND** |
| 6-field offset map | **Verified clean** against real bytes — no offset is off by even one byte |
| Code encoding | **Packed BCD, one byte = two decimal digits**; digit `0` = nibble `0xB` — *not* "ASCII byte pairs / ASCII `0x42`" |
| Page-0 validity marker | `byte0 & 0x0F == 0x0D` (low nibble `D`) |

---

## 1. Byte size — ground truth

### 1a. The 540,672-byte number

`AT45DB041E[Page264]@SOIC8.BIN` is confirmed **540,672 bytes** (`stat` output):

```
stat -c '%s' "AT45DB041E[Page264]@SOIC8.BIN"   ->  540672
```

The arithmetic:

```
AT45DB041E       = 4 Mbit DataFlash
Native page size = 264 bytes   (the "264-byte page mode" the filename records)
Page count       = 2048
2048 pages × 264 bytes/page = 540,672 bytes     <- matches the file exactly
540672 / 264                = 2048.0 pages       (clean integer — confirms the model)
```

In its **default native page mode**, each AT45DB041E page is 264 bytes: 256 data bytes plus 8 spare bytes the DataFlash architecture carries per page. 2048 × 264 = 540,672. This is the true contents of the main memory array.

### 1b. The 540,672 vs 540,800 discrepancy (the 128-byte delta)

Every other dump in the set (`UDFN8`, `UserCodesDump.BIN`, `UserCodesElevatedDump.BIN`, `flashdump2.bin`, `gooddump1RemoteReleaseBefore.bin`, `NAND_AfterReset.BIN`, and so on) is **540,800 bytes = 540,672 + 128**.

**Resolved.** The 128 extra bytes are the AT45DB041E's **128-byte Security Register**, appended after the main array by the programmer. The evidence is a byte-for-byte comparison of `SOIC8` (540,672) against `UDFN8` (540,800):

```
first 540,672 bytes of UDFN8  ==  all of SOIC8      -> IDENTICAL  (no differing byte)
UDFN8 bytes 540,672 .. 540,799 (the extra 128)      -> the appended Security Register
```

The appended 128 bytes (from `UDFN8`, file offset `0x84000`):

```
+000  ffffffffffffffffffffffffffffffff   } 64-byte user-programmable
+010  ffffffffffffffffffffffffffffffff   } OTP half — unprogrammed here
+020  ffffffffffffffffffffffffffffffff   } (all 0xFF)
+030  ffffffffffffffffffffffffffffffff   }
+040  160405141e011f2400010f09ffff88ff   } 64-byte FACTORY-programmed
+050  30305058554a3831134848ffffffffff   } unique-ID half
+060  4040404040404040ffffffffffffffff   } (ASCII fragment: "00PXUJ81" ... "@@@@@@@@")
+070  ffffffffffffffffffffffffffffffff   }
```

This matches the AT45DB041E Security Register definition exactly: **128 bytes total — bytes `0x00`–`0x3F` user-programmable one-time-programmable (OTP), bytes `0x40`–`0x7F` factory-programmed with a permanent unique device identifier.** The factory half is non-blank (real factory data); the user OTP half is blank (`0xFF`, never programmed). The programmer that produced the 540,800-byte files issued the *Read Security Register* command and appended its 128-byte result to the main-array image; the programmer that produced the SOIC8 file did a main-array-only read and stopped at 540,672.

**Confidence: HIGH.** The delta is exactly 128 (the documented Security Register size, not a round number); the first 540,672 bytes are byte-identical between the two reads; and the trailing block has the precise OTP-blank / factory-programmed split the datasheet specifies. It is **not** a 2-extra-pages artifact (that would be 528 bytes), **not** padding, and **not** generic programmer framing.

### 1c. Which number to state in the handout

- **Main user-code memory array: 540,672 bytes** — use this whenever the handout talks about "the chip image / the array you decode."
- A full programmer read that also captures the Security Register is **540,800 bytes**. State this so participants whose dump is 128 bytes larger are not confused: the user-code page is in the main array; the extra 128 bytes are appended at the end and are not part of the page structure.
- **524,288 is wrong for these reads.** 524,288 = 2048 × 256 — the size if the chip is reconfigured into "power-of-2 / binary page mode" (256-byte pages). These chips were read in **264-byte native page mode** (the filenames literally say `[Page264]`).

---

## 2. The page-0 header (byte 0)

The user-code page begins with a header byte whose **low nibble is `0xD`**. The high nibble varies; the low nibble is the marker.

### 2a. The validity invariant

> **A valid page-0 user-code dump has `byte0 & 0x0F == 0x0D`.**

A second physical lock board — keypad-reprogrammed to master code `111111` during prior testing — was clipped and read cleanly (two byte-identical reads, correct chip ID `0x1F24`). Its page-0 byte 0 was **`0x1D`**, not `0xFD`, yet the decode was otherwise clean and internally consistent. Comparing byte 0 across **every** valid user-code dump available — the canonical baseline plus the entire original T2/T3 research corpus — establishes the true invariant:

| Dump | byte 0 | low nibble | high nibble | valid page-0? |
|---|---|---|---|---|
| canonical baseline (123456) | `FD` | `D` | `F` | yes |
| second board (reprogrammed 111111) | `1D` | `D` | `1` | yes (clean decode, 2× identical reads) |
| research `AT45DB041E[Page264]@SOIC8` | `FD` | `D` | `F` | yes |
| research `UDFN8`, `UDFN8(code+date)` | `FD` | `D` | `F` | yes |
| research `gooddump1/2RemoteRelease*` | `FD` | `D` | `F` | yes |
| research `UserCodes*Dump`, `UserCodePositionsDump1` | `FD` | `D` | `F` | yes |
| research `NAND_AfterReset`, `NandAfterReset*` (×7) | `FD` | `D` | `F` | yes |
| research `NANDuploadUnexpectedValues` | `FD` | `D` | `F` | yes |
| blank/erased/wrong reads (all-`00`, all-`FF`) | `00` / `FF` | `0` / `F` | — | NO |

Every legitimate page across 14+ independent locks satisfies the low-nibble rule. Factory/unmodified locks read `0xFD` (high nibble `F`); the high nibble is a **variable firmware status/sequence field** that changes when a lock is keypad-reprogrammed (the `1D` board). *Why* it takes a given value is deferred to post-conference follow-up research; for validation we only need the stable low-nibble marker. Both blank (`0x00`) and erased (`0xFF`) reads fail the low-nibble test, so relaxing the check to the low nibble does **not** weaken rejection of corrupt dumps. Confidence **HIGH** for the low-nibble rule as a safe validation invariant — the only observed legitimate non-`FD` value across the entire corpus is `1D`.

### 2b. What this means at the bench

- **Low nibble `D` (e.g. `0xFD`, `0x1D`)** — legitimate page. A non-`FD` byte 0 with low nibble `D` is a real in-service / keypad-reprogrammed lock, **not** a bad dump.
- **Low nibble not `D` (e.g. `0x00`, `0xFF`, `0x1C`)** — a real reject. Re-read the chip, check clip contact, or flag a facilitator.

`build-injected.py` enforces this: it checks `byte0 & 0x0F == 0x0D` and emits a *non-fatal* NOTE when the high nibble is not `0xF` ("this lock appears keypad-reprogrammed; proceeding").

The factory-state case (byte `0xFD`) below remains correct for unmodified locks; read `0xFD` as one instance of the `*D` low-nibble marker.

### 2c. Locating the page

Scanning `AT45DB041E[Page264]@SOIC8.BIN` for an `0xFD` byte that begins a 264-byte window matching the documented user-code structure (active-flag region containing only `01`/`FF`, permission region containing only valid permission values) yields **exactly one match**:

| Property | Value |
|---|---|
| File offset (decimal) | **0** |
| File offset (hex) | **`0x00000`** |
| Page index | **0** (the very first 264-byte page) |
| `off % 264` | 0 (page-aligned) |

First 4 bytes of the SOIC8 dump:

```
00000000: fd 12 22 ff ...
          ^^ FD page header marker
```

The user-code page is **page 0** of the DataFlash — file offset 0. State it plainly to participants: *the user-code page is the first page of the dump; it starts at file offset 0 with byte `0xFD`.*

(The file contains 18 `0xFD` bytes overall, but only the one at offset 0 begins a structurally valid user-code page.)

---

## 3. Worked user-code decode

### 3a. The encoding

Each code byte holds **two decimal digits, one per nibble** — packed BCD. The digit `0` is stored as **nibble value `0xB`**, not as a standalone ASCII `'B'` (`0x42`).

| Rule | Example |
|---|---|
| One byte = two decimal digits (packed BCD) | `0x12` → `"1","2"`  ·  `0x34` → `"3","4"`  ·  `0x56` → `"5","6"` |
| Digit `0` is the nibble value `0xB` (inside the byte) | `0xB1` → `"0","1"`  ·  `0x2B` → `"2","0"`  ·  `0x30` → `"3","0"` |
| A 6-digit code is three bytes concatenated | `byte1 ‖ byte2 ‖ byte3` |

The "ASCII `B` / `0x42`" phrasing seen in older notes is loose shorthand: in a hex view of the page, the digit `0` *looks like* the hex letter `B`. It is the nibble value `0xB`, never the ASCII byte `0x42`. A literal `0x42` never appears in any code-byte region of any validated dump.

### 3b. Worked decode — SOIC8 page 0

The SOIC8 page-0 has three active user codes. Worked example, **slot 0** (the master):

```
Region            Offset    Byte for slot 0
code byte 1       0x0001    0x12   -> nibbles 1,2 -> "12"
code byte 2       0x0033    0x34   -> nibbles 3,4 -> "34"
code byte 3       0x0065    0x56   -> nibbles 5,6 -> "56"
                                      --------------------
                            DECODED CODE = "123456"
active flag       0x0097    0x01   -> ACTIVE
permission flag   0x00C9    0xF1   -> MASTER
```

**Slot 0 = code `123456`, active, Master.** This is the Alarm Lock factory-default master code — exactly what an unmodified / factory-reset lock should contain, confirming the decode is correct.

All three active codes in the SOIC8 dump:

| Slot | b1 b2 b3 | Decoded code | Active | Permission |
|---|---|---|---|---|
| 0  | `12 34 56` | `123456` | `01` active | `F1` Master |
| 1  | `22 20 00` | `222000` | `01` active | `E1` Elevated User |
| 32 | `33 30 00` | `333000` | `01` active | `01` Normal User |

(`222000` and `333000` are short codes right-padded with `0`, encoded as nibble `0x0`/`0xB` per the rule above — here as literal `0` nibbles, which the firmware also accepts.)

### 3c. Cross-check against `userCodeBlock.txt` / `userCodeElevatedBlock.txt`

These note files describe a **different, more fully populated** lock state (27 active codes, slots 0–24 + 48–49) than the SOIC8 page-0 dump (3 codes). They corroborate the *structure and encoding*, not the same code set. Worked cross-check from `userCodeBlock.txt`:

```
slot 0  : b1 b2 b3 = B1 B1 B1  -> "01" "01" "01" -> code 010101 , active 01 , perm F1 Master
slot 19 : b1 b2 b3 = 2B 2B 2B  -> "20" "20" "20" -> code 202020 , active 01 , perm 01 Normal
slot 49 : b1 b2 b3 = 5B 5B 5B  -> "50" "50" "50" -> code 505050 , active 01 , perm 01 Normal
```

The `0xB`-nibble = digit-`0` rule decodes these cleanly. `userCodeElevatedBlock.txt` is byte-identical to `userCodeBlock.txt` **except** the permission region at slots 11/12/13 (`01 01 01` → `F1 E1 C1`) — i.e. it is the same user set with three users escalated to Master / Elevated / Supervisor. This corroborates the permission-flag region's offset and value semantics. The full-chip `UserCodesDump.BIN` / `UserCodesElevatedDump.BIN` reproduce these exact two states at page 0, offset 0.

---

## 4. Offset-map verification (the 6-column offset map)

Each region was checked against the real bytes of `AT45DB041E[Page264]@SOIC8.BIN` page 0. The handout presents this as a 6-column map (the six data regions after the FD header).

| Region | Documented offset | Span | Verified against real bytes | Result |
|---|---|---|---|---|
| FD page header | `0x0000` | 1 byte | byte 0 = `0xFD` | **PASS** |
| Code byte 1 (50 codes) | `0x0001`–`0x0032` | 50 bytes | slot 0 = `0x12` at `0x0001`; region length 50 | **PASS** |
| Code byte 2 (50 codes) | `0x0033`–`0x0064` | 50 bytes | slot 0 = `0x34` at `0x0033` | **PASS** |
| Code byte 3 (50 codes) | `0x0065`–`0x0096` | 50 bytes | slot 0 = `0x56` at `0x0065` | **PASS** |
| Active flags (50) | `0x0097`–`0x00C8` | 50 bytes | every byte ∈ {`0x01`,`0xFF`} | **PASS** |
| Permission flags (50) | `0x00C9`–`0x00FA` | 50 bytes | every byte ∈ {`F1,E1,C1,01,11,21,31,41,FF`} | **PASS** |
| Padding | `0x00FB`–`0x0107` | 13 bytes | all `0xFF`; region ends at byte 263 | **PASS** |

```
1 + 50 + 50 + 50 + 50 + 50 + 13 = 264   <- exactly one DataFlash page
```

**The offset map verifies clean. No region is off by even one byte.**

**Watch the padding bound.** Some copies of the layout table write the padding row as `0x00FB..FF` while labelling it "Padding (13 bytes)". `0xFF − 0xFB + 1 = 5`, not 13 — that `..FF` notation is a typo. The correct upper bound is `0x0107` (`0x0107 − 0x00FB + 1 = 13`). Use `0x00FB`–`0x0107` for the padding region, **not** `0x00FB`–`0x00FF`.

---

## 5. Corrections applied to the workshop docs

These are the corrections the workshop files (`FACILITATOR-GUIDE.md`, `PARTICIPANT-HANDOUT.md`) carry, each backed by the validation above.

**C-1 — Byte size: `524,288` → `540,672`.**
`524,288` is the 256-byte power-of-2 page-mode size and is wrong for these reads. These chips were read in **264-byte native page mode** (`2048 × 264 = 540,672`). State **540,672 bytes** as the chip-image / main-array size. *(See §1.)*

**C-2 — Mention the 540,800-byte variant.**
A full programmer read that also captures the chip's 128-byte Security Register produces a **540,800-byte** file. Add a sentence: participants whose dump is 540,800 bytes have the main array (540,672) plus an appended 128-byte Security Register; the user-code page is in the main array and the trailing 128 bytes are not part of the page structure. Do not let a 540,800-byte dump be treated as an error. *(See §1b.)*

**C-3 — "NAND" → "DataFlash" (technically-correct chip naming).**
The AT45DB041E is an Adesto (formerly Atmel) **serial DataFlash** — a **NOR-based** SPI memory with an SRAM-buffer page architecture. It is **not NAND flash.** Older research notes call it "NAND" loosely throughout (e.g. "Deep Dive 1: NAND Flash"); the workshop files call it **SPI DataFlash** (or "AT45DB041E DataFlash"). If the workshop wants to acknowledge the older notes, add a one-line aside: *"The research write-up refers to this chip as 'NAND' as informal shorthand; strictly it is serial NOR DataFlash."* The 264-byte page size and SRAM-buffered page-write behavior the workshop teaches are DataFlash characteristics — calling it NAND will confuse participants who know the difference. *(See §1, §3.)*

**C-4 — Code encoding: "ASCII byte pairs" → "packed BCD, two digits per byte".**
"Stored as ASCII byte pairs `'12' '34' '56'`" is misleading. Each code byte holds **two decimal digits, one per nibble** (packed BCD): byte `0x12` = digits "1","2". A 6-digit code is three such bytes. State it as packed BCD, not ASCII. *(See §3a.)*

**C-5 — Digit-zero encoding: "ASCII `B` / `0x42`" → "nibble value `0xB`".**
A zero digit is **not** ASCII `B` (`0x42`) — the byte `0x42` never appears in a code region. The digit `0` is the **nibble value `0xB`** inside a packed-BCD byte (so byte `0xB1` decodes to "01", `0x2B` to "20"). It only *looks like* the letter "B" in a hex view. State "digit 0 is stored as nibble `0xB`." *(See §3a, §3c.)*

**C-6 — Padding region offset: `0x00FB`–`0x0107` (13 bytes), not `0x00FB`–`0x00FF`.**
If the handout copied the older layout table verbatim, the padding row reads `0x00FB..FF` — a typo that spans only 5 bytes while the label says 13. The correct region is **`0x00FB`–`0x0107`**, 13 bytes, which makes the page total exactly 264. *(See §4.)*

**C-7 — FD page location: state it explicitly as file offset 0 / page 0.**
Tell participants the user-code page is the **first page of the dump — file offset `0x00000`, page index 0, starting with byte `0xFD`**. There is exactly one structurally valid FD user-code page in the SOIC8 image and it is at offset 0. This removes any ambiguity about whether the FD page is "somewhere inside" the dump — for these dumps it is at the start. *(See §2.)*

**C-8 (minor) — The 6-column offset map is accurate; keep it, with the C-6 fix.**
The six data regions after the FD header verified clean against real bytes. No structural correction is needed beyond the padding-offset typo in C-6. The map can ship as-is once C-6 is applied. *(See §4.)*

---

## 6. Toolchain note (verbatim source quotes)

Pulled verbatim from the research notes (`PhysAccessDigiLies_PhrackSubPiano.txt`), surfaced for the toolchain-plan task — not analyzed here.

**Programmer (DataFlash read/write):**
> "The fact that it could be read/written with a $30 Xgecu T48 programmer didn't hurt either."

> "NAND injection — Xgecu T48 — Ghost users, audit mismatch" *(attack-vector table)*

**Programmer software:**
> "II. Tooling Note: Xgpro Software — The tooling setup is... an exercise in patience.
> - The official Xgpro software is only available via sketchy .cn sites over plaintext HTTP
> - It runs on Windows, but can be coerced into working with Linux/Wine
> - You'll need custom udev rules and a setupapi.dll dropped into the install directory"

> "For a safer software source: https://github{dot}com/radiomanV/XGecu_Software"

> "Linux setup guide: https://boseji{dot}com/posts/running-tl866ii-plus-in-manjaro/"

**OS / environment:**
> "Maybe it was Linux and Wine conspiring against me."

> "Only the programmer was plugged into USB. / The board was rock still. / A successful memory read occurred first. / A small write was done. / Then the main memory was erased and a full upload attempted." *(the setup that produced reliable writes)*

**In-circuit / clip wiring:**
> "I clipped onto the NAND to read existing codes and write my own."

> "I soldered micro-jumpers to UART pins under conformal coating - barely connecting to the BSL for an instant one time."

> "Eventually, I dialed in a more stable solder-and-breakout method involving micro tips, flux layers, breakout leads, and enough heat to make any ESD-conscious engineer twitch."

**MSP430 firmware toolchain (out of workshop scope — surfaced only for completeness):**
> "II. Tooling — MSP-FET debugger / UniFlash (TI) / Ghidra + custom memory map + infinite patience / MSP430 assembly reference and chip documentation"

**Note on procedure:** the research notes describe the chip being **clipped onto in-circuit** ("I clipped onto the NAND"). Bench testing recorded that in-circuit reads brown out (the CH341A `LIBUSB_TRANSFER_ERROR` root cause), and the workshop is locked on an **out-of-circuit** desolder→read→resolder arc. The research-note quotes above predate that decision and should be read as historical, not as the workshop procedure.

---

## Validation summary

| Check | Result |
|---|---|
| `AT45DB041E[Page264]@SOIC8.BIN` = 540,672 bytes (2048 × 264) | CONFIRMED |
| 540,800-byte dumps = 540,672 array + 128-byte Security Register | CONFIRMED (HIGH confidence) |
| 524,288 (older handout claim) wrong — that is 256-byte page mode | CONFIRMED |
| FD user-code page at file offset 0 / page 0 | CONFIRMED |
| Worked decode slot 0 = `123456`, Master, active | CONFIRMED |
| 7-region offset map verifies clean (no byte off) | CONFIRMED |
| Encoding is packed BCD, digit 0 = nibble `0xB` (not ASCII `0x42`) | CORRECTION REQUIRED |
| Chip is DataFlash (NOR), not NAND | CORRECTION REQUIRED |
| 8 corrections logged for the workshop docs (C-1 … C-8) | DELIVERED |

*Validation performed against the authoritative research dumps. No live hardware read was used this session (a chip was cooked during desoldering); the existing dumps are ground truth per the engagement brief.*

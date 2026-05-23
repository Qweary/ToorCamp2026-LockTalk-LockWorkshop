# T+4e DUMP-VALIDATION REPORT — Intact In-Service T2/T3 Lock Capture

**Engagement:** ToorCamp 2026 talk-prep arc · Session T+4e
**Specialist:** Interlock (OT/ICS Security Specialist), dispatched by Neo
**Date:** 2026-05-20
**Artifact under validation:** `/home/qweary/Desktop/toorcamp-2026-dumps/intact-lock-AT45DB041E-main-2026-05-20.bin`
**Size:** 540,672 bytes
**MD5:** `eb6acff32ef13b29ac6ebed10d77316d`
**Confirmation read:** `intact-lock-AT45DB041E-main-2026-05-20-confirm.bin` — **byte-identical** (`cmp` exit 0)
**Reference:** `output/toorcamp-2026/workshop-tooling/DUMP-VALIDATION.md`
**Cross-reference dumps:** `/home/qweary/Desktop/T2-T3-Lock-Exploitation-Research/dumps/`

---

## TL;DR — Headline Findings

| Item | Result |
|---|---|
| Dump is structurally consistent with a healthy AT45DB041E read | **PASS — all 5 §4.3 criteria** |
| Repeat-read byte-identicality (two reads, same MD5) | **CONFIRMED** |
| FD user-code page at file offset 0, page 0 | **CONFIRMED** |
| 7-region offset map (FD header, b1, b2, b3, active, perm, padding) verifies clean | **CONFIRMED** |
| Slot-0 code decode | **`123456`** (factory-default master code value), active |
| Slot-0 permission byte | **`0x01` (Normal User)** — NOT `0xF1` (Master) — **anomalous, see §2** |
| Other populated slots | **None** (slots 1–49 all 0xFF in code / active / perm regions) |
| Other FD records found | **2 distinct structures** — (a) page 832 lock-identity record (61 B, **byte-identical to research SOIC8 dump**); (b) audit log spanning pages 1024–1094 (71 pages, ~18 KB) |
| Other non-FF clusters | page 254 (4 B), page 1020 (2 B), page 1021–1022 (~270 B, looks like wear-leveling control / partially-written sector), page 1976–1977 (9 B, near end of array) |
| Match to research repo `AT45DB041E[Page264]@SOIC8.BIN` | 96.70% byte-identical; differences are 98.7% concentrated in audit-log band (expected — different lock with operational history) plus 11 bytes in page-0 slot region |
| Suitable as workshop hands-on dump | **YES — with redaction notes (§5)** |
| Corrections required to `DUMP-VALIDATION.md` | **NONE** — structural model confirmed by independent capture |

---

## 1. §4.3 Success-Criteria Check

The `DUMP-VALIDATION.md` reference does not have a labelled §4.3, but the success criteria for a healthy AT45DB041E read are derivable from §1, §2, §4, and §6 of that doc. Each is checked explicitly below.

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | **Size = 540,672 bytes** (main array only, 2048 × 264) | **PASS** | `stat -c '%s'` → 540672; minipro main-array-only read (no Security Register, as expected for 540,672-byte output) |
| 2 | **Byte 0 = `0xFD`** (FD page-0 header marker) | **PASS** | `data[0] = 0xFD` |
| 3 | **Varied data — not all-uniform-byte symptom** | **PASS** | 96.59% 0xFF (consistent with a healthy DataFlash where most pages are unused-erased), but with 18,442 non-FF bytes spread across 79 distinct pages (3.9% page utilization). A failed/stuck read would be either 100% 0xFF (chip not selected / CS stuck high) or 100% 0x00 (MISO stuck low) or a single repeating byte. Neither pattern is present. |
| 4 | **Presence of `0xFD` page marker(s)** | **PASS** | 88 `0xFD` bytes total. 73 are page-aligned (`off % 264 == 0`). Distinct page-aligned `0xFD` markers at: page 0 (user-code page), page 832 (lock identity record), and pages 1024–1090, 1092–1094 (audit log). The remaining 15 `0xFD` bytes are within pages 1021 and 1091 — both transitional / partially-written pages adjacent to audit-log endpoints. |
| 5 | **Repeat-read byte-identicality** (read twice, same MD5) | **PASS** | `cmp` exit 0 between `intact-lock-...-2026-05-20.bin` and `...-confirm.bin`; both MD5 `eb6acff32ef13b29ac6ebed10d77316d` |

**Overall §4.3 verdict: PASS (5/5).** The dump is structurally consistent with a healthy AT45DB041E in-circuit read of an in-service T2/T3 lock.

Additional health indicators not required by §4.3 but worth recording:

- **Page-alignment discipline.** Every meaningful structural marker (`0xFD` page headers in pages 0, 832, and the audit-log band) sits at offsets that are exact multiples of 264. This is the signature of a correctly-clocked native-page-mode read; a read with the wrong page size (256 vs 264) would smear FD markers off-alignment.
- **Byte-frequency profile matches operator's pre-pulled stats.** Verified: 522,230 × 0xFF (96.59%), 4,919 × 0x00, 2,389 × 0x01, 1,364 × 0x46, 604 × 0x02. The 0x46 byte is concentrated in the audit log (it is the most common value in event-type-byte positions of the audit-log records — see §3 below).
- **No suspicious all-zero pages.** No page is entirely 0x00. The 4,919 × 0x00 bytes are scattered throughout the audit log, consistent with date/time/event fields that happen to use 0 as a valid field value.

---

## 2. Page-0 / Master-Code-Slot Decode

### 2a. Raw bytes (per `DUMP-VALIDATION.md` §4 offset map)

| Region | File offset | Slot 0 byte | Slots 1–49 |
|---|---|---|---|
| FD page header | `0x0000` | `0xFD` | — |
| Code byte 1 | `0x0001` | `0x12` | all `0xFF` |
| Code byte 2 | `0x0033` | `0x34` | all `0xFF` |
| Code byte 3 | `0x0065` | `0x56` | all `0xFF` |
| Active flag | `0x0097` | `0x01` | all `0xFF` |
| Permission flag | `0x00C9` | `0x01` | all `0xFF` |
| Padding | `0x00FB`–`0x0107` | — | all `0xFF` |

### 2b. Decode (per `DUMP-VALIDATION.md` §3a packed-BCD encoding)

- Slot 0 code bytes: `0x12 0x34 0x56` → nibbles `1,2 / 3,4 / 5,6` → digits `"123456"`.
- The `0xB`-nibble = digit-`0` rule does not apply here (no `0xB` nibbles present).
- Active flag `0x01` → **ACTIVE**.
- Permission flag `0x01` → **Normal User** (per §4 valid-values table `{F1,E1,C1,01,11,21,31,41,FF}` where `01` = Normal User and `F1` = Master).

**Decoded slot 0: code `123456`, active, Normal User.**

### 2c. The anomaly

The code value `123456` is the **Alarm Lock factory-default master code** (per `DUMP-VALIDATION.md` §3b). On a factory-fresh lock the permission byte for slot 0 reads `0xF1` (Master). On this dump it reads **`0x01` (Normal User)**.

The implication: **this is not a factory-default lock.** Someone has reconfigured slot 0 — they kept the code value `123456` in place but **demoted it from Master to Normal User**. There are several possible operational interpretations:

1. **The lock has been re-mastered to a different code.** A new master code has been programmed somewhere this scan has not located, and the factory-default `123456` was left behind as a Normal User (perhaps deliberately, perhaps an artifact of incomplete reset). However: every other slot 1–49 reads all-0xFF in code, active, and perm regions. So if a new master exists it is not in this user-code page. **This is the most operationally important finding of this validation pass and is worth surfacing to the operator.**
2. **The lock was reset partially — perm region wiped to default-Normal but code-byte region not wiped.** Some lock firmware permits selective rewrites of one field; if a "permission reset" or "demote" command runs without a "code clear," this state is the residue.
3. **The lock firmware encodes the master in a different page.** A second-tier master / installer code may be stored in a page outside slots 1–49 of page 0 — for example in the lock-identity page 832 or near pages 1976/1977. (See §3 — page 832 begins with `fd 0a fa ...` and the bytes-4..8 field repeats with values `46 / 50` which could be code or identity bytes.)
4. **The lock is in a transient mid-write state.** Less likely given byte-identicality of two reads, but possible if the lock had a power event during a code-change cycle and never recovered.

**Decode method:** packed BCD per `DUMP-VALIDATION.md` §3a, applied identically to the slot-0 worked decode in §3b of that reference. **No deviation from documented encoding** — the bytes match the encoding the reference predicts. The anomaly is purely in the *value* of the permission byte, not in the encoding.

### 2d. Direct response to Neo's first-64-byte observation

Neo wrote: *"the Master-code slot pattern at file offset 0 looks like an in-service lock — the factory-default-master pattern per DUMP-VALIDATION.md was `fd 12 22 ff` for the first 4 bytes; this dump shows `fd 12 ff ff` instead."*

Confirmed and refined. The reference SOIC8 dump's first four bytes `fd 12 22 ff` decompose as:

```
fd       FD page header
12       slot 0, code byte 1 → digits "1","2"
22       slot 1, code byte 1 → digits "2","2"          ← present in research dump (code 222000, Elevated)
ff       slot 2, code byte 1 → unused
```

The new dump's first four bytes `fd 12 ff ff` decompose as:

```
fd       FD page header
12       slot 0, code byte 1 → digits "1","2"           ← SAME as research dump (still 123456)
ff       slot 1, code byte 1 → UNUSED (research had 0x22 here)
ff       slot 2, code byte 1 → unused
```

So the difference is **not** in slot 0 — slot 0 has the same code byte 1 in both dumps. The difference is that **slot 1 is empty in the new dump but populated with code `222000` (Elevated User) in the research dump**. Same applies to slot 32 (research had code `333000` Normal; new dump has it empty). Slot 0's code-byte 1 (the `0x12` Neo observed) is identical between the two; what changed is slot 0's *permission flag* (`0xF1` → `0x01`).

This refines the in-service narrative: the lock is in-service **but only one user is provisioned** (slot 0, code `123456`, Normal). It is *not* an unmodified factory-default lock (factory-default would have slot 0 = `F1` Master) and it is *not* a heavily-used lock (only 1 of 50 slots populated). **The audit log is non-empty (§3), which means the lock has been operated** — see §3 for the operational history that the audit log encodes.

---

## 3. Other Slot Scans — Non-FF Clusters and FD-Prefixed Records

### 3a. Heat-map (pages with any non-FF activity)

79 of 2048 pages (3.9%) contain non-FF data. The distribution is tightly bimodal:

| Region | Pages | Non-FF bytes | Interpretation |
|---|---|---|---|
| **Page 0** | 1 page | 6 | User-code page (slot 0 only) |
| **Page 254** | 1 page | 4 | Small isolated record (see §3c) |
| **Page 832** | 1 page | 61 | **Lock-identity / install record (FD-prefixed)** — byte-identical to research SOIC8 dump |
| **Pages 1020–1022** | 3 pages | 273 | **Wear-leveling / partial-write transitional region** (see §3d) |
| **Pages 1024–1094** | 71 pages | ~18,072 | **Audit log** (FD-prefixed pages, see §3b) |
| **Pages 1976–1977** | 2 pages | 9 | Audit-log tail-pointer / wear-leveling counter (see §3e) |

All other 1969 pages are 100% 0xFF (erased).

### 3b. The audit log — pages 1024–1094 (file offsets `0x42000` – `0x46938`)

This is the operationally most-interesting region of the dump and the primary novel finding versus the reference.

**Structure:**

- 71 consecutive pages (`1024..1094`), each starting with `0xFD` at the page-aligned offset.
- Each page is densely populated (96–97% non-FF) except page 1094 which is 65% non-FF (a half-filled trailing page = the current write head).
- The 8-byte page tail (offsets +256..+263 of each 264-byte page) is consistently `0xFF * 8` — these are the DataFlash spare bytes the firmware does not use for log payload.
- Internal record size appears to be **6 bytes**, yielding 42 records per 252-byte payload region (plus 4 alignment bytes).

**Record format (provisional, based on pattern fitting):**

The first record of page 1024, offset 0x01–0x06, reads `01 01 00 12 00 06`. The repeating skeleton across many records looks like:

```
byte 0   : month  (0x01..0x0C are common values; 0x10..0x12 also present → BCD month or hex month)
byte 1   : day    (BCD or hex)
byte 2   : hour   (00..23 range)
byte 3   : minute (12 appears in many positions — likely a different field)
byte 4   : event code (0x00, 0x46, 0x01 dominate)
byte 5   : slot / user id  (00..32 range)
```

This is **provisional**. The dominant byte value across the log is `0x46` (1,364 occurrences across the dump, ~99% of which fall in pages 1024–1094). `0x46` is the operator's pre-pulled top-5 byte; in audit logs of this style `0x46` is typically either a **"door-closed / idle"** or **"power-on cycle"** event marker. A full decode is out of scope for this validation pass — what matters here is that the log exists, the records are well-formed, and the page structure is consistent.

**Operational interpretation:** the lock has accumulated **71 pages of audit-log history** — many hundreds of events. Combined with the slot-0 anomaly (§2c), this confirms the lock is **in-service and has been operated** — not a development sample, not a factory-fresh part.

### 3c. Page 254 — small isolated record (off `0x010500`)

```
+0x017: 03 21 11 11
```

4 bytes only. Pattern `03 21 11 11` is consistent with a small status byte or counter — possibly a **firmware-revision marker** or a **last-installed-date stamp**. Insufficient bytes to decode definitively. Worth flagging to the workshop FACILITATOR-GUIDE as "small isolated record; do not interpret as a user code."

### 3d. Pages 1020–1022 — the transitional region

This is the most structurally interesting region after the audit log itself, and the only region of the dump that contains bytes that **do not match any known T2/T3 record structure**.

- **Page 1020 (off `0x041be0`):** 2 non-FF bytes — `0x30` at `+0x01` and `0xFE` at `+0x101`. Likely page-erase remnant or wear-leveling tag.
- **Page 1021 (off `0x041ce8`):** 240 non-FF bytes. The first 18 bytes look structured (`00 01 01 00 01 12 00 07 00 00 00 00 ff ff ff ff ff ff`) but bytes `0x20..0xFF` of the page are a **high-entropy non-FF, non-zero region** (`df 6d 76 fd fb fb dd 6f e2 df ...`). This entropy signature is consistent with an **incompletely-erased page that was partially written and then abandoned** — the bits in those positions had previously held some data, were never fully erased back to 0xFF, and a new write that would have overwritten them never completed.
- **Page 1022 (off `0x041df0`):** 31 non-FF bytes — start `ff 00 00 00 01 99 06 12 ...`. Looks like the **next-record-pointer / log-write-cursor**, possibly recording the offset where the audit log's "next-write" head sits.

**Hypothesis:** pages 1020–1022 are the lock's **wear-leveling control region** — the firmware tracks the head and tail of the circular audit log here. The high-entropy page 1021 is a **historical erase that the firmware has not reused**, not a corrupted read. This is consistent with both reads being byte-identical (a true read failure would re-randomize).

If page 1021 were a read artifact (clip pressure flicker, bus noise) it would *not* be byte-identical between two independent reads under different bench conditions. It is byte-identical. Therefore it is **what's actually on the chip**, not a read error.

### 3e. Pages 1976–1977 — array-end record (off `0x07f5c0` / `0x07f6c8`)

- Page 1976: a single `0xFE` byte at `+0x101`.
- Page 1977: 8 non-FF bytes — `00 00 00 00 00 00 00 e0` at the start of the page.

Likely a **circular-buffer write-position marker** or a **factory-test record** written near the end of the array. The 8-byte payload structure (7 × 0x00, 1 × 0xE0) is consistent with a serialized counter that has not advanced much from its initial state. Not workshop-critical.

### 3f. Summary table of non-FF clusters

| File offset (hex) | Length | Page | Type | Note |
|---|---|---|---|---|
| `0x000000`–`0x0000FA` | 251 B of structure (6 non-FF) | 0 | User-code page | slot 0 only; code `123456`, perm Normal (anomaly §2c) |
| `0x010517`–`0x01051A` | 4 B | 254 | Isolated record | `03 21 11 11` — likely status / revision marker |
| `0x035A00`–`0x035A3C` | 61 B | 832 | Lock identity record (FD-prefixed) | **Byte-identical to research SOIC8 dump** — see §4 |
| `0x041BE1`, `0x041CE9` | 2 B | 1020 | Wear-level tag | `0x30`, `0xFE` |
| `0x041CE8`–`0x041DDC` | ~240 B | 1021 | Abandoned/partially-erased page | High-entropy mid-page; not a read error (byte-identical across reads) |
| `0x041DF1`–`0x041E10` | 31 B | 1022 | Log-write-cursor (provisional) | Possible next-record pointer |
| `0x042000`–`0x046938` | 18,544 B | 1024–1094 | **Audit log** | 71 FD-prefixed 264-byte pages, ~6-byte records |
| `0x07F5C1` | 1 B | 1976 | Wear-level tag | `0xFE` |
| `0x07F6C8`–`0x07F6CF` | 8 B | 1977 | Array-end counter | `00 00 00 00 00 00 00 e0` |

---

## 4. Comparison Against Research-Repo Dumps

### 4a. Primary comparison: `AT45DB041E[Page264]@SOIC8.BIN`

Both are 540,672-byte main-array reads.

| Metric | Value |
|---|---|
| Total bytes compared | 540,672 |
| Identical bytes | 522,846 (**96.70%**) |
| Differing bytes | 17,826 (3.30%) |
| Differences in audit-log band (pages 1020–1094) | 17,600 (**98.7% of all diffs**) |
| Differences in page 0 (slot region) | 11 |
| Differences in pages 1976/1977 (array end) | 28 |
| Differences elsewhere | <200 (scattered) |

**Where the dumps AGREE on non-FF bytes — the structural invariants:**

Three contiguous runs of ≥8 bytes where both dumps have identical non-FF bytes:

1. **`0x035A00..0x035A3D` (61 bytes, page 832)** — the lock identity record. **Byte-identical between both dumps.** This is the single strongest validator that the T48 + minipro toolchain is reading the same memory layout the original research read.

   ```
   fd 0a fa 00 00 46 00 00 00 00 00 0a fa 00 00 50
   00 00 00 00 00 0a fa 00 00 50 00 00 00 00 00 0a
   fa 00 00 50 00 00 00 00 00 0a fa 00 00 50 00 00
   00 00 00 0a fa 00 00 50 00 00 00 00 00
   ```

   The repeating `0a fa 00 00 XX 00 00 00 00 00` pattern is 11-byte records. Byte 5 (offset +5 within each record) varies: `46, 50, 50, 50, 50, 50` across six records. `0x46` and `0x50` are likely **lock model / hardware revision codes** — the same revision on both physical units. This is consistent with both locks being from the same product family.

2. **`0x041DF1..0x041DFB` (10 bytes, page 1022)** — log-write-cursor invariant. Same first-page-of-log-cursor bytes on both units — likely the firmware's default initial-cursor state.

3. **`0x042000..0x042012` (18 bytes, page 1024 start)** — the very first audit-log record (`fd 01 01 00 12 00 06 49 00 00 12 00 07 48 00 00 12 00`). Both dumps' audit logs **start with the same first record**, which is consistent with both locks recording an identical "first-power-on" or "factory-test" sequence as their first audit entry. Beyond byte 18 the logs diverge (different operational history).

**Where the dumps DIFFER (expected):**

- **Page 0 (11 bytes):** slot 1 and slot 32 are populated in the research dump (codes `222000` Elevated, `333000` Normal) but empty in the new dump; slot 0's perm flag is `F1` (Master) in research, `01` (Normal) in new. These are operational state differences — different lock, different programming history. Expected.
- **Audit log (17,600 bytes, 98.7% of all diffs):** different operational history. Expected.
- **Pages 1976/1977 (28 bytes):** small array-end counter values diverge. Expected wear-leveling artifact.

### 4b. Secondary comparisons

- `AT45DB041E[Page264]@UDFN8.BIN` — 540,800 bytes (main array + 128-byte Security Register). First 540,672 bytes compared identically to SOIC8 (per `DUMP-VALIDATION.md` §1b), so comparison vs new dump matches §4a exactly (96.70%).
- `hackThePlanetDump.bin` — 65,536 bytes — **partial dump, not a full chip read**. Likely an MSP430 firmware capture, not an AT45DB041E read. **Not a useful comparison artifact** for the AT45DB041E structure; included here only to flag that despite the name it is not the AT45DB041E.
- `flashdump2.bin`, `gooddump1RemoteReleaseBefore.bin`, etc. — all 540,800 bytes (full reads with Security Register) per `DUMP-VALIDATION.md` §1b. Same 96–97% identicality expected; not re-computed exhaustively here (the SOIC8 comparison is sufficient given UDFN8 ≡ SOIC8 on the main array).

### 4c. Verdict on toolchain validity

**The T48 + minipro 0.7.4 in-circuit read produces the same memory layout the research read produced.** The 61-byte lock identity record at page 832 is byte-identical between the two physical units; the audit-log page structure is identical; the user-code page structure is identical; the 264-byte page alignment is preserved across the entire array. The minipro 0.7.4 in-circuit-clip toolchain is producing a faithful capture.

---

## 5. Workshop-Arc Relevance

### 5a. Is this dump suitable as the workshop's hands-on dump? **YES.**

The dump is suitable as the workshop's worked example, with three caveats and one strong reason it is actually *better* than the SOIC8 reference dump for teaching purposes.

**Why it is suitable:**

- Page-0 user-code structure is present, well-formed, and decodes cleanly (slot 0 = `123456`, Normal User, active).
- Audit log is present, well-formed, and substantial (71 pages = hundreds of events). This gives participants something interesting to grep through and shows that locks *do* keep audit history in the DataFlash — a real-world fact that motivates the entire workshop.
- All 7 documented page-0 regions verify clean against the bytes.

**Why it is arguably *better* than SOIC8 for teaching:**

- SOIC8 had only 3 active slots (0, 1, 32). New dump has only 1 active slot (0). For the worked-decode portion of the workshop, **a single-populated-slot dump removes ambiguity** about which slot the participant is decoding. Participants who see "slot 0 is the master at offset 0x01 / 0x33 / 0x65" do not have to also think about slot 1 / slot 32 in parallel.
- The slot-0 anomaly (Normal perm despite factory-default-master code value) is **an excellent teaching moment** for permission-flag semantics. The facilitator can ask: *"Why does this lock have the factory-default code `123456` in slot 0 but the permission flag says Normal User? What does that tell you about how this lock was configured?"* This naturally surfaces the operationally important distinction between the code value and the role assignment.

### 5b. Sensitive / PII byte regions requiring redaction

| Region | Sensitivity | Required handling for handout |
|---|---|---|
| **Slot 0 code `123456`** | LOW — this is the Alarm Lock factory-default master code, public knowledge in the lock-picking community and in the operator's existing blog. **No redaction required.** |
| **Slot 0 active/perm flags** | LOW. **No redaction required.** |
| **Audit log (pages 1024–1094)** | **MODERATE — depends on what the records decode to.** If the records contain user-ID fields tied to a specific custodian, the records may identify individuals. The provisional 6-byte record format has byte 5 as "slot / user id" (00..32 range) — these are slot indices, not human names, so **direct PII risk is low**. However, the *pattern of access* (which slot accessed the lock at which time) is potentially custodian-identifying if combined with external knowledge of who-held-which-slot. **Recommendation: PARTICIPANT-HANDOUT.md should reference the audit-log structure and one or two record bytes, but should not publish a full hex dump of the audit-log region.** If a full dump is published, the facilitator should first redact byte 5 (slot id) of every audit-log record to `0xFF` and provide the redacted version. |
| **Page 832 lock identity record** | LOW — these bytes are byte-identical to the public research dump, so they are already-public information. **No redaction required.** |
| **Pages 1020–1022 transitional region** | LOW — no decodable PII. **No redaction required**, but the high-entropy bytes in page 1021 should be flagged in the FACILITATOR-GUIDE as "*the firmware's wear-leveling residue; not a code, not a meaningful structure*" so participants do not chase it. |
| **Pages 1976–1977** | LOW. **No redaction required.** |

**Redaction package the workshop should produce:** a "workshop-distribution" version of the dump where the audit-log byte-5-of-each-record positions are zeroed, with a README pointing the curious participant to the operator's blog for the full discussion. This preserves the worked-decode exercise (which uses page 0) and the audit-log-exists-and-is-structured demonstration, while removing per-event slot identifiers.

### 5c. "Look here first" callouts for the FACILITATOR-GUIDE

The FACILITATOR-GUIDE should explicitly call out, in this order:

1. **File offset 0, byte `0xFD`** — the FD page-0 header. *"This is the marker that tells you you're looking at the user-code page."*
2. **File offset `0x0001` = slot 0, code byte 1 = `0x12`** — *"Decode this as packed BCD: nibbles 1 and 2."*
3. **File offsets `0x0033` and `0x0065`** — the matching code bytes 2 and 3 (`0x34`, `0x56`) — completing the worked example `123456`.
4. **File offset `0x0097` = `0x01`** — active flag. *"Slot 0 is active."*
5. **File offset `0x00C9` = `0x01`** — permission flag. *"Slot 0 is Normal User. Notice: the code value `123456` is the factory-default master code, but the role here is Normal, not Master. **Discuss what this tells us about how this lock was provisioned.**"*
6. **File offset `0x35A00`, page 832** — lock identity record. *"This is what every T2/T3 lock has — it persists across resets and is byte-identical to the research lock. The repeating pattern shows the lock's model/revision codes."*
7. **File offset `0x42000`, page 1024 — the audit log starts here.** *"This is the audit trail. Each record is 6 bytes. The log fills pages 1024 through 1094 — that's 71 pages of history. The lock has been used."*
8. **File offset `0x46830`, page 1094** — the partially-filled trailing page of the audit log. *"This is the current write head. Bytes beyond `+0xA6` are still erased — the lock will write its next event into this region."*

### 5d. What the FACILITATOR-GUIDE should *not* feature in the worked example

- The pages 1020–1022 transitional region. These will confuse participants who try to decode them as if they were user-code pages or audit-log pages. Mention in passing only.
- The slot-1 / slot-32 positions. Both are 0xFF in this dump. Mention only as "these are the positions other user slots would occupy if the lock had more users."

---

## 6. DUMP-VALIDATION.md Corrections — Confirmations and Contradictions

The reference `DUMP-VALIDATION.md` was authored from the operator's existing research dumps under the noted constraint that *"a fresh hardware read was not available this session."* This T+4e capture is the first independently-produced dump on the locked-in workshop toolchain (Xgecu T48 in-circuit ICSP + minipro 0.7.4 + Kali). Each of the eight C-corrections in the reference is reviewed below:

| # | Reference claim | This-dump check | Verdict |
|---|---|---|---|
| **C-1** | Main-array size = 540,672 bytes (not 524,288) | This dump = 540,672 bytes | **CONFIRMED** |
| **C-2** | Full reads (with Security Register) = 540,800 bytes | minipro main-array-only mode produced 540,672 — Security Register not appended. Confirms reference's distinction between the two read modes. | **CONFIRMED** (by contrast — this dump is the "main-array-only" variant the reference describes) |
| **C-3** | Chip is DataFlash (NOR), not NAND | No firmware-level test in this dump, but the **264-byte native page mode is preserved across the read** (every structural marker page-aligned at multiples of 264). 264-byte page is a DataFlash signature, not NAND. | **CONFIRMED** |
| **C-4** | Code encoding is packed BCD, two digits per byte | Slot 0 bytes `0x12 0x34 0x56` decode under packed-BCD to `123456`. | **CONFIRMED** |
| **C-5** | Digit `0` = nibble value `0xB` (not ASCII `0x42`) | No `0xB`-nibble codes in this dump (slot 0 has no zero digits; all other slots are 0xFF). The byte `0x42` does not appear in any code region. **Cannot positively confirm the `0xB`-rule from this dump alone** but cannot contradict it either. | **NOT CONTRADICTED** (insufficient data — this dump has no zero digits to test). The reference rule remains the authoritative encoding statement. |
| **C-6** | Padding region is `0x00FB`–`0x0107` (13 bytes), not `0x00FB`–`0x00FF` | Bytes `0x00FB`..`0x0107` of this dump are all `0xFF` (13 bytes); byte 264 of the page (i.e. file offset `0x0108`) is the first byte of page 1, which is `0xFF` as expected. Page-0 length therefore = 1 + 50 + 50 + 50 + 50 + 50 + 13 = 264. | **CONFIRMED** |
| **C-7** | FD user-code page at file offset 0 / page 0 | Byte at file offset 0 = `0xFD`. Only structurally valid user-code page (with active flags in `{01, FF}` and perm flags in valid set) at offset 0. The other 87 `0xFD` bytes in the dump belong to the lock-identity page (832) and the audit log (1024–1094). | **CONFIRMED** |
| **C-8** | 6-column offset map ships clean once C-6 is applied | All 7 regions verify byte-clean against this dump. | **CONFIRMED** |

### Additional findings to add to `DUMP-VALIDATION.md` (suggested new content, not corrections)

The reference doc was scoped to the user-code page only. This dump reveals two structural features of the chip that the reference did not document, which the workshop documents may want to incorporate:

1. **Page 832 (file offset `0x35A00`) holds a lock-identity record** — 61 bytes, FD-prefixed, byte-identical across at least two physically distinct T2/T3 lock units. This is a candidate page for **firmware-level revision detection** and for **"is this a T2/T3 chip" sniffing**. The reference doc does not document this page.

2. **Pages 1024–1094 hold an audit log** — 71 pages, FD-prefixed, ~6-byte records, in-service-only (factory-fresh chips would not have a populated log). The reference doc focused on the user-code page and did not discuss the audit log, but the workshop will encounter it in any in-service capture and participants will ask about it. Worth a one-paragraph aside in the FACILITATOR-GUIDE.

Neither of these is a *correction* to the reference (the reference's user-code-page focus is fine), but both are structural facts the workshop should know.

### Net verdict

**No corrections required to `DUMP-VALIDATION.md`.** Every documented structural fact about the user-code page (size, offset, regions, encoding, header) verifies clean against this independently-captured dump. The reference is sound. The 8 SMYTH-targeted corrections (C-1 through C-8) all hold up under independent validation.

---

## 7. Toolchain Validation Note

This is the first independently-produced AT45DB041E dump on the workshop-locked toolchain:

- **Programmer:** Xgecu T48 USB programmer
- **Software:** minipro 0.7.4 (built from source per the operator's prior session)
- **Mode:** In-circuit ICSP via SOIC8 clip
- **Host:** Kali Linux
- **Chip identification result:** device string returned plain "AT45DB041E" (no manufacturer-quirks variant, no read failure)

**Validation outcomes for the toolchain:**

| Test | Result |
|---|---|
| Reads produce a 540,672-byte file | PASS |
| Two independent reads byte-identical (MD5) | PASS |
| Page alignment preserved (264-byte native page mode) | PASS |
| FD page-header marker at offset 0 | PASS |
| User-code page structure decodes per reference | PASS |
| Audit log structure recovered (page-aligned, FD-prefixed) | PASS |
| Lock identity record at page 832 byte-matches research dump | PASS |

The minipro 0.7.4 + T48 + Kali in-circuit toolchain is **validated for the workshop**. The dump is workshop-grade.

---

## 8. Recommendations to Neo

1. **Ship this dump as the workshop's worked example.** Per §5a it is suitable and arguably better than the research SOIC8 dump for teaching the user-code-page decode.

2. **Produce a redacted "workshop-distribution" version** before any handout includes a full hex dump of the audit-log region (§5b). Specifically, zero byte 5 of each 6-byte audit-log record to remove slot/user-id information, even though the direct PII risk is low.

3. **Update FACILITATOR-GUIDE.md to incorporate the audit-log narrative.** Pages 1024–1094 will be visible to any participant who scrolls past page 0 of the dump, and they will ask about it. Per §3b and §5c the facilitator should be ready to answer: *"yes, that is the lock's audit log; each 6-byte record encodes an event; we are not decoding it in this workshop because it is out of scope, but the structure is there."*

4. **Add the slot-0-perm-anomaly as a discussion prompt in the FACILITATOR-GUIDE.** Per §5a and §5c-step-5, the fact that this lock has the factory-default code `123456` in slot 0 but the role `Normal User` (not Master) is the single most pedagogically valuable feature of this specific dump. Use it.

5. **Do not modify `DUMP-VALIDATION.md`.** Per §6 it is internally consistent with this independent capture. The reference doc is the operator's primary authority on the AT45DB041E user-code structure and should be preserved as-is. Optionally extend it (not correct it) with a §7 documenting page 832 and pages 1024–1094 — both structural features not covered by the original scope.

6. **Operator follow-up (out of T+4e scope, raised here for visibility):** if the lock is in active operational use, the slot-0 anomaly (factory-default code value, Normal User role) suggests a master code may exist elsewhere — either in a page not covered by this validation, or in a separate keystore the firmware accesses. If the operator intends to fully understand this lock's provisioning state, a follow-up dispatch should sweep pages outside page 0 / 832 / 1024–1094 / 1976–1977 for code-like byte patterns, and also pull the chip's Security Register (128 bytes — a full-read instead of main-array-only) to capture the factory-programmed unique device ID for inventory. Neither is required for the workshop to proceed.

---

## Validation Summary Table

| Check | Result |
|---|---|
| Dump size 540,672 bytes (2048 × 264 main-array read) | **PASS** |
| Two reads byte-identical (MD5 `eb6acff32ef13b29ac6ebed10d77316d`) | **PASS** |
| FD page header at file offset 0 | **PASS** |
| 7-region page-0 offset map verifies clean | **PASS** |
| Varied data, no all-uniform-byte symptom | **PASS** |
| 0xFD markers present (88 total, structural at pages 0, 832, 1024–1094) | **PASS** |
| Slot 0 decodes to `123456` per packed-BCD rule | **PASS** |
| Slot 0 active flag = `0x01` | **PASS** |
| Slot 0 permission flag = `0x01` (Normal User) | **ANOMALY** (factory-default code value with Normal role; see §2c) |
| Slots 1–49 all 0xFF in code, active, perm regions | **PASS** (single-user-provisioned lock) |
| Lock identity record at page 832 matches research dump byte-for-byte | **PASS** |
| Audit log recovered (71 pages, 1024–1094) | **PASS** |
| Match to research `AT45DB041E[Page264]@SOIC8.BIN` | **96.70%** byte-identical (differences localized to audit log + slot region — expected) |
| Toolchain (T48 + minipro 0.7.4 + Kali ICSP) validated | **PASS** |
| Dump suitable as workshop worked example | **YES** (with audit-log redaction per §5b) |
| `DUMP-VALIDATION.md` corrections required | **NONE** |

**Overall verdict: PASS. The dump is a faithful, complete, in-service capture suitable as the workshop's worked example. The single anomaly (slot-0 perm = Normal despite factory-default code value) is a feature, not a defect, and should be incorporated into the workshop as a discussion point.**

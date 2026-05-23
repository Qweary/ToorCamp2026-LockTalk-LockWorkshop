# T+4g Manual-Method End-to-End Verification Block

## ToorCamp 2026 · "Dead Bytes Tell No Lies" · Session T+4g (2026-05-20)

> **Authoring agent:** Electrode (Electrical & Hardware Engineering specialist), routed by Neo.
> **Purpose:** A single copy-pasteable bench dry-run of the **exact documented per-station attendee
> flow** (FACILITATOR-GUIDE.md §"The per-attendee flow", Steps 1–9). The operator runs this RIGHT NOW on
> the live, working **T48 + SOIC-8 clip + ZIF ICSP adapter + `minipro 0.7.4`** rig to confirm that every
> copy-pasteable line in the workshop documentation produces the promised result end-to-end.
> **Rig:** SOIC-8 clip-on (the default, sole per-station method). Lock batteries OUT; T48 powers the chip
> through the clip. **Not** the individual-lead rig (ad-hoc-only, off-flow — see T48-KALI-PLAN.md §A.6).
>
> **Standing command rules (verify each invocation against these):**
> - **`-i`** on every read (`-r`) and write (`-w`) — the standing skip-ID-check flag after the dry probe.
> - **`-D`** (uppercase, `--read_id`) for the chip-ID check — the ONLINE bus read. **Never `-d`**
>   (lowercase, `--get_info`) for a presence check: `-d` is an OFFLINE DB lookup that never touches the
>   bus and would "succeed" with no chip clipped (T+4g defect fix — T48-KALI-PLAN.md §A.4.1).
> - **`-y`** (force / `--no_id_error`) ONLY as a documented force flag for the firmware-warning case
>   AFTER the chip is confirmed on the bus — never on a presence check, never to mask a wiring fault.
>
> **Canonical fixtures (T+4e):** baseline `intact-lock-AT45DB041E-main-2026-05-20.bin` MD5
> `eb6acff32ef13b29ac6ebed10d77316d`; injected MD5 `47b6faaf1217389afa7a879d93c024dd`; size 540,672 bytes.

---

## How to run this

Run each numbered block in order. After each block, check the **SUCCESS SIGNAL**. If it does not appear,
follow the **ESCALATE** one-liner — do not round-trip back to Electrode/Neo per attempt; the escalate
hints cover the expected failure branches. Steps 1, 7 are physical (keypad / battery); the rest run at the
Kali laptop shell. Work from `~/workshop` (the documented station working directory).

```bash
cd ~/workshop
```

---

### Step 0 — Rig sanity (T48 enumerated + programmer opens)

```bash
lsusb | grep -i 'a466:0a53'                    # T48 on the USB bus
sudo minipro -k                                # programmer opens, reports model
```

- **SUCCESS SIGNAL:** one `a466:0a53` line from `lsusb`, and `minipro -k` prints `t48: T48`.
- **ESCALATE:** no `a466` line → try a different USB cable/port, re-plug. `minipro -k` errors on
  permissions → run with `sudo` (you already are) or confirm the udev rules + `plugdev` membership
  (T48-KALI-PLAN.md §2.3).

---

### Step 1 — Confirm the lock works as it ships (physical, batteries IN)

- Punch `123456` → lock **unlocks**. Punch `999999` → lock **does not** unlock.
- **SUCCESS SIGNAL:** factory code opens it, wrong code does not. This is the "before" state.
- **ESCALATE:** `123456` does not open → this lock was re-mastered or its battery is flat; swap to a
  known-good prepped board before continuing. Do not proceed on a lock you cannot open in its ship state.

---

### Step 2 — Batteries OUT, clip onto the chip (physical)

- Pull the lock batteries. Open the PCB side. Align SOIC-8 clip pin 1 (marked jaw) to chip pin 1 (dot/
  notch). Clamp; wiggle gently to seat all 8 jaws. Clip's other end → ZIF ICSP adapter → T48 ZIF socket,
  lever down. T48 plugged into the laptop.
- **SUCCESS SIGNAL:** clip seated, lever down, T48 power LED lit. (Electrical confirmation is Step 2b.)

---

### Step 2b — Dry probe: confirm the chip is on the bus (chip-ID read, `-D`)

```bash
sudo minipro -p 'AT45DB041E[Page264]@SOIC8' -D
```

- **SUCCESS SIGNAL:** reports chip ID **`0x1F24`** (the AT45DB041E JEDEC ID). The firmware-mismatch
  warning will print — that is benign and expected.
- **ESCALATE:** `Invalid Chip ID ... got 0x0000` → the clip is not biting. Re-seat (open fully, re-align
  pin 1, re-clamp, light downward pressure), re-run. If it still fails after 2–3 re-seats, swap the
  SOIC-8 clip, then the board (FACILITATOR-GUIDE.md clip-bite ladder). **Do NOT add `-y` here** — the
  whole point of this probe is to let the ID check fire so you know the chip is genuinely responding.

---

### Step 3 — Read the intact lock to a baseline file (`-i -r`), confirm size + MD5

```bash
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -r my-dump.bin
ls -l my-dump.bin
md5sum my-dump.bin
```

- **SUCCESS SIGNAL:** read completes with no USB error (`Reading Code... OK`); `ls -l` shows **`540672`**
  bytes; `md5sum` is stable across a second read. If this is THE canonical T+4e intact lock, the MD5 is
  **`eb6acff32ef13b29ac6ebed10d77316d`**. (A different intact lock will have a different MD5 — that is
  fine; size 540,672 and a structured non-uniform dump are the load-bearing checks.) A `Reading User...`
  timeout is benign — that is the Security Register, which `-r` does not target.
- **ESCALATE:** size is `524288` → the chip read in 256-byte page mode; re-run with the exact device
  string above (it forces 264-byte native mode). Size is `540800` → the tool also grabbed the 128-byte
  Security Register; the first 540,672 bytes are the main array and decode normally. Read errors / USB
  drop mid-read → re-seat the clip (contact slip), re-run.

```bash
# (optional) prove the read is stable — two byte-identical reads
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -r my-dump2.bin
cmp my-dump.bin my-dump2.bin && echo "STABLE READ — byte-identical"
```

- **SUCCESS SIGNAL:** `STABLE READ — byte-identical`.

---

### Step 4 — Decode the user-code page; confirm slot 0 = `123456`

Decode method per DUMP-VALIDATION.md offset map (also in PARTICIPANT-HANDOUT.md §"DataFlash Page Layout"
and FACILITATOR-GUIDE.md Pocket Reference). The user-code page is **page 0, file offset `0x00000`**, first
byte `0xFD`. Slot N: code byte 1 at `0x0001+N`, byte 2 at `0x0033+N`, byte 3 at `0x0065+N`, active flag at
`0x0097+N`, permission at `0x00C9+N`.

```bash
xxd my-dump.bin | head -20
# Read off slot 0 directly from the offset map:
echo -n "slot0 code byte1 (0x0001): "; xxd -s 0x0001 -l 1 my-dump.bin | awk '{print $2}'   # expect 12
echo -n "slot0 code byte2 (0x0033): "; xxd -s 0x0033 -l 1 my-dump.bin | awk '{print $2}'   # expect 34
echo -n "slot0 code byte3 (0x0065): "; xxd -s 0x0065 -l 1 my-dump.bin | awk '{print $2}'   # expect 56
echo -n "slot0 active   (0x0097): ";   xxd -s 0x0097 -l 1 my-dump.bin | awk '{print $2}'   # expect 01
echo -n "slot0 perm     (0x00C9): ";   xxd -s 0x00C9 -l 1 my-dump.bin | awk '{print $2}'   # expect 01
```

- **SUCCESS SIGNAL:** byte 0 of the dump is `fd`; the three code bytes are `12 34 56` → packed-BCD decode
  `1,2 / 3,4 / 5,6` = **`123456`** (the factory-default master code value); active = `01`; permission =
  `01` (**Normal User, not Master** — the slot-0 anomaly the workshop teaches).
- **ESCALATE:** byte 0 is not `fd`, or the code bytes are not `12 34 56` → this is not the FD page-0
  dump, or the read is corrupt. Re-confirm the read (Step 3) and that this is the intact lock.

---

### Step 5 — Build the injected payload; confirm expected MD5

```bash
python3 ~/workshop/build-injected.py my-dump.bin injected.bin
md5sum injected.bin
xxd injected.bin | head -20
```

- **SUCCESS SIGNAL:** the script prints its 15-byte change table (slots 19/32/49) and `Wrote injected.bin
  (540,672 bytes)`. **IF `my-dump.bin` is the canonical T+4e baseline** (MD5
  `eb6acff32ef13b29ac6ebed10d77316d`), the injected MD5 is **`47b6faaf1217389afa7a879d93c024dd`**. In the
  `xxd` output, the digit-zero-as-`0xB` rule is visible: `b4` at column `0x53` and `2b` at column `0x85`
  (slot 32's `420420`).
- **ESCALATE:** the script exits with a size or FD-header error → `my-dump.bin` is the wrong size/scope
  (re-do Step 3, trim a 540,800-byte file's trailing 128 bytes). MD5 differs from the canonical and you
  ARE on the T+4e baseline → re-read the chip; your `my-dump.bin` is not byte-identical to the baseline.
  (If you are on a DIFFERENT intact lock, the injected MD5 will differ — that is expected; the patch table
  printout is the per-byte check.)

---

### Step 6 — Write the injected payload (`-i -w`); confirm Verification OK + exit 0

> Clip still on the chip, batteries still OUT, T48 powering the chip through the clip.
> **In a real workshop this writes a SPARE / sacrificial chip per the read-before-write safety rule —
> never the only intact lock.** For THIS verification dry-run, the operator already has the baseline
> captured (Step 3) and the recovery write (Step 8) restores it, so a write to the working lock is
> recoverable; confirm you are comfortable writing this chip before proceeding.

```bash
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -w injected.bin; echo "exit=$?"
```

- **SUCCESS SIGNAL:** completes in ~20 s, prints `Verification OK`, and `exit=0`.
- **ESCALATE:** the write aborts on the firmware-mismatch warning on this build → add `-y` (the documented
  force flag) and re-run: `sudo minipro -i -y -p 'AT45DB041E[Page264]@SOIC8' -w injected.bin`. Verification
  fails mid-write → the clip slipped; re-seat and re-run (the write is idempotent against the same
  `injected.bin`). USB drop → re-seat clip, re-run.

---

### Step 6b (optional) — Read back + cmp to confirm byte-identical

```bash
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -r post-write.bin
cmp injected.bin post-write.bin && echo "FULL IMAGE MATCH — write took"
```

- **SUCCESS SIGNAL:** `FULL IMAGE MATCH — write took`.
- **ESCALATE:** `cmp` reports differences ONLY in the audit-log band (`0x42000`–`0x46938`) or at the array
  end → still a PASS (the lock logged a power event during the write). What matters is page 0 (first 264
  bytes) matches `injected.bin`:
  `cmp <(head -c 264 injected.bin) <(head -c 264 post-write.bin) && echo "PAGE 0 MATCH — patch took"`.
  If page 0 differs → the write did not take; re-clip, re-write (Step 6).

---

### Step 7 — Battery reinstall + keypad-unlock demonstration (physical)

- Unclip the SOIC-8 carefully. Reinstall the lock batteries. Wait for the boot chirp / LED cycle.
- Punch each code in sequence and watch the lock:
  - `133769` → unlocks (slot 19 **Master**, `0xF1`)
  - `420420` → unlocks (slot 32 **Supervisor**, `0xC1`) — **this proves the `0xB`-for-zero encoding rule**
  - `696969` → unlocks (slot 49 **Elevated**, `0xE1`)
  - `123456` → still unlocks (slot 0, untouched factory default)
- **SUCCESS SIGNAL:** **all four codes unlock the lock.** This is the workshop's central proof — the
  injected codes the attendee wrote unlock real hardware, including the zero-bearing `420420`.
- **ESCALATE (these are the documented "what it means if a code fails" branches):**
  - All three injected fail, `123456` still works → page 0 did not take; re-clip, re-read, re-write.
  - `133769` + `696969` work but `420420` fails → the `0xB`-for-zero rule is wrong for this firmware rev
    (an interesting finding — flag it; try `0xA`/`0xC` for the zero nibble on a follow-up).
  - Only `133769` works → permission-flag semantics differ on this rev (`0xC1`/`0xE1` may not map to
    "permits door operation"); flag it.
  - Nothing unlocks, including `123456` → page 0 corrupted; run Step 8 recovery, then re-attempt.

---

### Step 8 — Recovery path (if a write goes bad): `recover-baseline.py`

The recovery script is the safety net — it restores the canonical baseline with size + MD5 pre-flight
gates so it refuses to write a wrong-baseline file. It wraps
`sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -w <baseline>`.

```bash
# self-test first (no hardware touched) — confirms the baseline file is the canonical T+4e master
python3 ~/workshop/recover-baseline.py --self-test \
    --baseline ~/workshop/intact-lock-AT45DB041E-main-2026-05-20.bin

# then the recovery write (clip on the chip, batteries OUT) — confirmation gate, then write + verify
python3 ~/workshop/recover-baseline.py \
    --baseline ~/workshop/intact-lock-AT45DB041E-main-2026-05-20.bin
```

> **Path note:** the script's built-in default baseline path is
> `~/Desktop/toorcamp-2026-dumps/intact-lock-AT45DB041E-main-2026-05-20.bin`, while the FACILITATOR-GUIDE
> stages the baseline at `~/workshop/`. Pass `--baseline ~/workshop/...` explicitly (as above) so the
> script targets the workshop-staged copy. (This path divergence is pre-existing and worth the operator
> reconciling between recover-baseline.py and the FACILITATOR-GUIDE before kit assembly.)

- **SUCCESS SIGNAL:** `--self-test` prints `RESULT: PASS — baseline is the canonical T+4e master`; the
  recovery run streams the write, prints `POST-WRITE VERIFY: PASS — chip MD5 matches baseline MD5`, then
  `Recovery complete`. Reinstall batteries → `123456` unlocks, injected codes are gone.
- **ESCALATE:** self-test FAIL on MD5 → you are pointing at the wrong baseline file; point at the canonical
  `eb6acff32ef13b29ac6ebed10d77316d` file. Recovery write returns non-zero → clip contact (re-seat,
  re-run; the script is safe to re-run).

---

## Verification outcome to record

After the run, record: (1) Step 2b chip ID; (2) Step 3 dump size + MD5; (3) Step 5 injected MD5; (4)
Step 6 `Verification OK` + exit code; (5) Step 7 which of the four codes unlocked; (6) whether Step 8
recovery restored `123456`. A clean pass on all six confirms the workshop documentation's copy-pasteable
lines demonstrate the full envisioned attack end-to-end on the live rig.

## Command-divergence findings (from deriving this block against FACILITATOR-GUIDE.md)

- **`-d` → `-D` dry-probe defect (FIXED at T+4g).** The dry probe in T48-KALI-PLAN.md §3.4 and §A.4.1 used
  lowercase `-d` (`--get_info`, offline DB lookup) where it needed uppercase `-D` (`--read_id`, online bus
  read). Corrected in the plan; this block uses `-D` at Step 2b. The FACILITATOR-GUIDE and
  PARTICIPANT-HANDOUT per-station flows skip the dry probe entirely (they go straight to `-i -r`), so they
  carried no `-d` defect — verified clean.
- **No further command errors found.** The FACILITATOR-GUIDE / PARTICIPANT-HANDOUT minipro invocations
  (`-i -r`, `-i -w`, the `cmp` verify, the recovery `-i -w`) are all internally consistent with the
  standing rules. The only non-command issue surfaced is the `recover-baseline.py` default-path vs
  `~/workshop` divergence noted at Step 8 — a path reconciliation, not a command error.

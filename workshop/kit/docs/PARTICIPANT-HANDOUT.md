# Dead Bytes Tell No Lies
## Hands-On DataFlash Decoding and Injection for Access Control Locks
### ToorCamp 2026 · Qweary

---

## Do the whole workshop yourself, in three commands

This workshop is **self-service**. With the repo cloned, a Kali laptop, and (optionally) the hardware, you can do the entire thing from this handout alone — no facilitator required. An organizer may be circulating if you want a hand, but you do not need one.

Everything below the three commands is the *why* — the page layout, the encoding trap, the slot map. You still want to read it, because the point of the workshop is to **understand** what you are decoding. But the procedure itself is three commands.

**1. SET UP the station (one command).** From the cloned repo root:

```bash
sudo ./bootstrap.sh
```

It is path-relative — clone the repo anywhere and run it. It assembles the kit, verifies it (hardware-free), installs `minipro` + the T48 udev rules, and populates `~/workshop/` with the docs, the tools, and the bundled sample dump. (The same stand-up is also available as `make station` from `workshop/kit`.)

**2. READ the codes (one command).** From `~/workshop`:

```bash
cd ~/workshop
python3 tools/lock-tool.py read --all
```

This dumps and decodes all 50 code slots in readable form. It runs on a **copy of the bundled sample dump** — no hardware needed, so you can do this step the moment the station is up.

**3. WRITE your own code (one command).**

```bash
python3 tools/lock-tool.py write --code NNNNNN --slot N --role ROLE
```

Replace `NNNNNN` with any six-digit code (zeros allowed — the tool applies the `0xB`-for-zero rule for you), `N` with a slot `0`–`49`, and `ROLE` with `master`, `elevated`, `supervisor`, or `normal`. It bakes your value into a **copy** of the sample dump and re-decodes it so you watch your code land. Nothing touches a real chip.

### Easier on-ramps (all wrap the same tool)

If you would rather not type flags, two convenience front-ends drive the exact same READ and WRITE:

```bash
python3 tools/lock-menu.py     # a plain-text menu: pick READ or WRITE
python3 tools/lock-panel.py    # a localhost browser panel: a READ button,
                               # a custom-value field, and a WRITE button
```

The menu and panel are thin wrappers — if either won't launch, the `lock-tool.py` one-liners above still work, and the wrappers print them for you.

### Everything above is SAFE — the live chip is the advanced opt-in

All three commands operate on a **copy of the bundled sample dump** by default. Nothing erases or reprograms real hardware. The live-chip path is the **advanced, optional** `--live` flag on `lock-tool.py` — it needs the T48 programmer clipped to the chip and is confirmation-gated. It is covered at the end of this handout under [Advanced: the live chip](#advanced-the-live-chip). Do not reach for `--live` until you have read that section; you do not need hardware to complete the workshop.

> **Just want the decode lesson? Skip `sudo ./bootstrap.sh`.** The READ and WRITE are pure-Python on a copy — no root, no setup. From a fresh clone, run them straight from the repo root:
> ```bash
> python3 workshop/kit/tools/lock-tool.py read --all
> python3 workshop/kit/tools/lock-tool.py write --code NNNNNN --slot N --role ROLE
> ```
> The `sudo ./bootstrap.sh` setup is what you want if you intend to do the live-chip (`--live`) path, or for the convenience of running from `~/workshop`.

---

## DataFlash Page Layout Reference

**Chip**: Adesto AT45DB041E — 4 Mbit SPI **DataFlash** (NOR-based, SRAM-buffered).

**Native page mode**: 264 bytes per page, 2048 pages → main-array size **540,672 bytes**. (If your tool also reads the 128-byte Security Register, the file will be **540,800 bytes** — same chip, the trailing 128 bytes are the Security Register appended after the main array. `minipro -w` does not target the Security Register; the workshop uses 540,672-byte files.)

**The user-code page is page 0** — file offset `0x00000`, first byte `0xFD`. No hunting. The dump starts on the page you want.

**Slot layout — fields stored column-by-column across 50 slots per page:**

| File offset | Length | Content |
|---|---|---|
| `0x0000` | 1 byte | FD page-header marker (`0xFD`) |
| `0x0001`–`0x0032` | 50 bytes | Code byte 1 for slots 0–49 |
| `0x0033`–`0x0064` | 50 bytes | Code byte 2 for slots 0–49 |
| `0x0065`–`0x0096` | 50 bytes | Code byte 3 for slots 0–49 |
| `0x0097`–`0x00C8` | 50 bytes | Active flag for slots 0–49 (`0x01` = active, `0xFF` = empty) |
| `0x00C9`–`0x00FA` | 50 bytes | Permission flag for slots 0–49 |
| `0x00FB`–`0x0107` | 13 bytes | Padding (all `0xFF`) |

Total: 1 + 50 + 50 + 50 + 50 + 50 + 13 = **264 bytes**. One page.

For slot N (0 through 49): code byte 1 lives at `0x0001 + N`, code byte 2 at `0x0033 + N`, code byte 3 at `0x0065 + N`, active flag at `0x0097 + N`, permission at `0x00C9 + N`. To read one user's full code you pull one byte from each of the three code-byte ranges. (`lock-tool.py read --all` does exactly this for all 50 slots and prints the result — the table below is what it is decoding under the hood.)

**Permission flag values**: `0xF1` Master · `0xE1` Elevated User · `0xC1` Supervisor · `0x01` Normal User · `0xFF` empty slot.

### Encoding — packed BCD, with one trap

Each code byte holds **two decimal digits, one per nibble** — packed BCD. Byte `0x12` decodes to digits "1" and "2". Byte `0x34` decodes to "3" and "4". A six-digit code lives in three concatenated bytes.

**The digit `0` is stored as the nibble value `0xB`** — not as ASCII `0x30`, not as BCD `0x00`. This is the workshop's trap. In a hex view of the page, a digit-zero looks like the letter `B` because of the nibble value, but it is not the ASCII character `B` (which would be `0x42`) and it is not the BCD zero (which would be `0x00`).

**Worked example — slot 0 on this lock:**

```
Region              File offset    Byte    Decode
code byte 1         0x0001         0x12    nibbles 1,2 → "12"
code byte 2         0x0033         0x34    nibbles 3,4 → "34"
code byte 3         0x0065         0x56    nibbles 5,6 → "56"
                                           ──────────
                                           CODE = "123456"
active flag         0x0097         0x01    ACTIVE
permission flag     0x00C9         0x01    Normal User
```

Slot 0 holds `123456` — the Alarm Lock factory-default master code. But the permission byte is `0x01` (Normal User), not `0xF1` (Master). **The code value is decoupled from the role.** Sit with what that tells you about how this lock was configured before you read the answer at the bottom of this page — `lock-tool.py read --all` shows you the same slot-0 row, code `123456` against a Normal User role.

**Worked example — `420420`:**

```
digits:     4   2   0   4   2   0
nibbles:    4,2     B,4     2,B          ← the 0 becomes nibble 0xB
bytes:      0x42    0xB4    0x2B
```

This is the exact substitution `lock-tool.py write` performs for you when a code contains a zero. Write `420420` into a slot, re-decode it, and you can confirm the `0xB`-for-zero rule in the tool's output — and on real hardware if you take the live path.

### A note on the audit log

Pages 1024–1094 of the dump (file offsets `0x42000`–`0x46938`) hold the lock's audit log: 71 pages of 6-byte records — many hundreds of events. The dump on your laptop is the workshop-distribution version, with byte 5 of every audit-log record zeroed; that byte is the slot/user-id field, and zeroing it removes per-event slot identifiers from the file before any full hex dump is printed in the handout. The audit log's structural fact (it exists, it is FD-prefixed, it is structured) is part of the workshop. The per-event decode is not.

---

## What the three commands do, step by step

You already have the one-command flow at the top. This section is the longer-form view of the same three actions, so you can see what is happening inside each one and verify it went right.

**1. Read all 50 slots.**

```bash
cd ~/workshop
python3 tools/lock-tool.py read --all
```

This loads a copy of the bundled sample dump, validates that byte 0 is the page-0 marker, walks the slot/offset map above, and prints every slot's code, active flag, and role. Find slot 0 in the output: code `123456`, role **Normal User**. That `123456`-value-but-Normal-User-role pairing is the **slot-0 anomaly** — sit with what it means before reading the answer at the bottom.

**2. Write a custom code into a copy.**

```bash
python3 tools/lock-tool.py write --code 420420 --slot 32 --role supervisor
```

This bakes your code into a **copy** of the sample dump using the packed-BCD / `0xB`-for-zero encoding, then re-decodes the result and shows it back to you. The tool prints a `CONFIRMED: slot 32 now decodes to 420420 (Supervisor), active` line when your value landed. `420420` is the one to watch: its two zero digits become nibble `0xB` in code bytes 2 and 3 (`0x42 0xB4 0x2B`) — that is the `0xB`-for-zero rule, performed for you, visible in the re-decode.

Try it with different roles and slots:

```bash
python3 tools/lock-tool.py write --code 133769 --slot 19 --role master
python3 tools/lock-tool.py write --code 696969 --slot 49 --role elevated
```

| Slot | Code | Bytes (packed BCD) | Role | Perm byte |
|---|---|---|---|---|
| 19 | `133769` | `0x13 0x37 0x69` | Master | `0xF1` |
| 32 | `420420` | `0x42 0xB4 0x2B` | Supervisor | `0xC1` |
| 49 | `696969` | `0x69 0x69 0x69` | Elevated | `0xE1` |

Slot 32 is the one to watch — its zero digits land at nibble `0xB`, which is exactly what the re-decode confirms.

**3. (Optional) drive it from the menu or the panel.**

```bash
python3 tools/lock-menu.py     # pick READ or WRITE from a list
python3 tools/lock-panel.py    # READ button + custom-value field + WRITE button in your browser
```

Both call the same READ and WRITE under the hood, so the result is identical to the one-liners.

---

## Advanced: the live chip

You do **not** need this to finish the workshop — the three commands above teach the whole decode/inject lesson on the sample dump. The live path is here for anyone who wants to do it on real hardware. It needs the T48 programmer, an SOIC-8 clip, and a prepped lock board, and every step is the same flow you already ran, with the `--live` flag added.

You will: read the chip on a real lock, write a code you forged into it, and watch the lock accept that code on the keypad. If something goes wrong, recovery restores the lock to the state it was in when you sat down.

**A. Clip onto the chip.**
With the batteries out, open the PCB side of the lock. The AT45DB041E is the 8-pin SOIC near the MSP430; the resin is already cleaned off. Match pin 1 of the SOIC-8 clip to pin 1 of the chip (the dot or notch). Clamp the clip onto the chip. The clip's other end goes into the ZIF ICSP adapter; the adapter sits in the T48's ZIF socket; the T48 is plugged into the laptop.

**B. Read the live chip.**

```bash
python3 tools/lock-tool.py read --all --live
```

`--live` reads the real chip first, then decodes it. If the chip-ID returns `0x0000`, the clip didn't bite — re-seat it and run again. The firmware-mismatch warning that prints is non-blocking. A clean read is 540,672 bytes.

**C. Write your forged code to the live chip.**

```bash
python3 tools/lock-tool.py write --code 420420 --slot 32 --role supervisor --live
```

`--live` flashes the result to the real chip. It is confirmation-gated — the tool prints exactly what it will do and waits for you to type `yes`. The write takes about 20 seconds; `minipro` reports `Verification OK` at the end.

**D. Reinstall batteries; demonstrate.**
Unclip the SOIC-8 carefully. Put the batteries back in. Wait for the boot chirp. Punch each code you wrote:

- `133769` — should unlock (slot 19 Master)
- `420420` — should unlock (slot 32 Supervisor) — this is the `0xB`-for-zero confirmation on real hardware
- `696969` — should unlock (slot 49 Elevated)
- `123456` — still unlocks (slot 0, untouched)

**E. The defender's tell (worth a minute).**
Try `133769` for programming-mode entry. It will not work — even though `133769` is set as Master on the chip, programming mode rejects it. The flash-write attack is sufficient for unauthorized entry but not for sustained operational control. That difference is the defender's tell.

**F. Recovery — always available.**
If anything goes sideways, restore the baseline:

```bash
python3 tools/recover-baseline.py
```

That restores the lock to its baseline. The AT45DB041E has no OTP fuses; recovery is unconditionally available.

---

## Common Errors and Fixes

The sample-dump commands have almost nothing to go wrong — they run offline on a copy. Most of this table is the **live** (`--live`) path.

| Symptom | First move |
|---|---|
| `read --all` errors that the dump can't be found | The station isn't set up. Run `sudo ./bootstrap.sh` from the repo root first; it populates `~/workshop/` |
| The menu or panel won't launch | The `lock-tool.py` one-liners still work — the wrappers print them. Use those |
| (`--live`) `Chip ID: 0x0000` | Re-seat the clip. Check pin 1 alignment. The chip-ID check is what catches a wiring problem — don't bypass it on the first attempt |
| (`--live`) Dump is all `0x00` | Clip is electrically wired to something other than the chip. Re-seat the SOIC-8 clip |
| (`--live`) Dump size is 524,288 bytes | Tool reported the chip in 256-byte "binary page mode" instead of native 264-byte page mode. The workshop chip is in 264-byte mode; this dump is unusable, re-run |
| (`--live`) Dump size is 540,800 bytes | Tool also captured the 128-byte Security Register. The first 540,672 bytes are the main array and decode normally; ignore the trailing 128 |
| (`--live`) Write failed `Verification` | Clip slipped mid-write. Re-seat, re-run. The write is idempotent against the same dump |
| (`--live`) Firmware-mismatch warning | Non-blocking. Let it scroll past. Do not attempt to update the T48 firmware during the workshop |
| (`--live`) `420420` does not unlock | The `0xB`-for-zero rule might be wrong on this firmware revision — itself an interesting finding |
| (`--live`) Lock unresponsive after writing | Reinstall batteries first. If still unresponsive, run `python3 tools/recover-baseline.py` |

---

## Take-Home Resources

- **The author** — code, dumps, handwritten notes, and the blog series live on GitHub and the blog:
  `github.com/qweary` · `qweary.github.io`

- **Tool** — `minipro` (David Griffith fork), the maintained native-Linux toolchain for the Xgecu T48:
  `https://gitlab.com/DavidGriffith/minipro`

- **Programmer** — Xgecu T48, ~$30–55. The reason the in-circuit clip read works on this chip and didn't on cheaper programmers: the T48 has a current-capable regulated supply that powers the chip plus the modest load of a small lock board through the clip without browning out

- **Hex editor** (cross-platform, free) — `https://imhex.werwolv.net`

- **Datasheet** — Adesto AT45DB041E DataFlash, Atmel/Adesto 8783L–DFLASH — the canonical reference for the 264-byte native page mode, the Security Register, and the page program / erase opcodes

---

### Answer to the slot-0 anomaly question

The lock was re-mastered before you got here. Someone programmed a new master code; the new master lives somewhere on the chip that this validation hasn't located, while the factory-default code value `123456` was left in slot 0 as a Normal User. The role assignment in flash is its own field and the firmware honors it independently of the code value or the slot index.

That's the lesson the workshop is built around.

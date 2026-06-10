#!/usr/bin/env python3
"""
lock-tool.py — One tool for the workshop's two attendee actions: READ and WRITE.

The thin command-line bedrock that the TUI menu and the local control panel wrap.
It does two things, both on the SAFE sample-dump-copy path by default:

  read    Decode the page-0 user-code table and print it in readable form.
          (Delegates to decode-codes.py's decoder so there is exactly one
          decode implementation in the kit.)

  write   Bake an attendee's own custom code into a COPY of the sample dump,
          using build-injected.py's packed-BCD / 0xB-for-zero encoding, then
          RE-DECODE the result and show it so the attendee sees their value
          land. Optionally writes that result to the live chip (advanced,
          confirmation-gated opt-in).

STDLIB-ONLY plus the two bundled sibling tools (decode-codes.py,
build-injected.py). No pip, no internet. A fresh offline Kali laptop runs this
with nothing but python3 + the bundled files.

Usage:
    python3 lock-tool.py read [--dump PATH] [--all] [--live]
    python3 lock-tool.py write --code 246810 [--slot 25] [--role supervisor]
                               [--out injected.bin] [--live]
    python3 lock-tool.py --self-test

Default everything is the no-hardware, copy-of-the-sample path. --live is the
advanced, confirmation-gated path that touches the real chip.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

# Import the two bundled sibling tools by file path. Both ship next to this one
# (workshop/src/ in dev, ~/workshop/tools/ on a station), so resolve relative to
# this script's own directory and load them as modules. This keeps a single
# decode implementation and a single encode implementation in the kit — no
# reinvented offset map, no reinvented 0xB-for-zero rule.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# Do not litter the shipped tools/ dir with __pycache__/*.pyc. These tools are a
# kit file set verified by MD5 manifest; stray bytecode caches would be non-
# manifested, non-deterministic build artifacts. Loading the siblings below
# without writing bytecode keeps the kit clean and reproducible.
sys.dont_write_bytecode = True

import importlib.util


def _load_sibling(module_name: str, file_basename: str):
    """Load a sibling tool (whose filename has a hyphen, so it is not directly
    importable) as a module from this script's directory. Fails loud with a
    clear message if the sibling is missing."""
    path = os.path.join(_HERE, file_basename)
    if not os.path.isfile(path):
        sys.exit(
            f"ERROR: required bundled tool '{file_basename}' not found next to "
            f"lock-tool.py (looked in {_HERE}). The kit is incomplete — re-run "
            f"the kit's selftest, or re-extract the tarball."
        )
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


decode_codes = _load_sibling("decode_codes_mod", "decode-codes.py")
build_injected = _load_sibling("build_injected_mod", "build-injected.py")

# Role name (case-insensitive) -> permission byte, for the write field. These
# are the documented roles per DATAFLASH-DECODE-REFERENCE.md §4. Master/Elevated/
# Supervisor/Normal cover the workshop; the numeric variants are accepted too.
ROLE_TO_PERM = {
    "master": 0xF1,
    "elevated": 0xE1,
    "elevated user": 0xE1,
    "supervisor": 0xC1,
    "normal": 0x01,
    "normal user": 0x01,
    "user": 0x01,
}
PERM_TO_ROLE_NAME = {
    0xF1: "Master",
    0xE1: "Elevated",
    0xC1: "Supervisor",
    0x01: "Normal User",
}

DEVICE_NAME = decode_codes.DEVICE_NAME
MINIPRO_BIN = decode_codes.MINIPRO_BIN
# Retained for compatibility; no longer prefixes minipro. The installed uaccess
# udev rule grants the logged-in user direct device access, so the live write
# runs unprivileged.
SUDO_BIN = decode_codes.SUDO_BIN
DUMP_SIZE = build_injected.DUMP_SIZE
MAX_SLOT = build_injected.MAX_SLOT

# What a canonical attendee LIVE write lands on the lock. The live write flashes
# a copy of the bundled sample dump with the attendee's code injected, and that
# sample already carries the three workshop demo codes (baked at slots 19/32/49)
# plus the 123456 starter code at slot 0. So every attendee ends on the SAME
# known-good state: the three demo codes + 123456 + their own code. This is the
# SAMPLE-flash model (deterministic, repeatable across many attendees), not an
# additive read-modify-write of whatever was previously on the chip. Surfaced to
# the panel UI via lands_on_lock_summary() so the browser can tell the attendee
# exactly what ends up on the lock.
DEMO_CODES = [
    {"code": "133769", "slot": 19, "role": "Master"},
    {"code": "420420", "slot": 32, "role": "Elevated"},
    {"code": "696969", "slot": 49, "role": "Supervisor"},
]
STARTER_CODE = {"code": "123456", "slot": 0, "role": "Normal User"}


def lands_on_lock_summary(code: str, slot: int, role_display: str) -> str:
    """One-line, panel-displayable summary of exactly what a canonical LIVE
    write puts on the lock: the three workshop demo codes + the 123456 starter
    + the attendee's own code. Pure (no I/O) so the panel and the self-test can
    both consume it."""
    demos = ", ".join(d["code"] for d in DEMO_CODES)
    return (f"Lands on the lock: your code {code} (slot {slot}, {role_display}) "
            f"+ the 3 demo codes {demos} + the {STARTER_CODE['code']} starter.")


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------
def cmd_read(args) -> int:
    """READ control: decode + print the user-code table. Just drives the shared
    decoder so the panel/TUI 'READ' button and the CLI 'read' agree exactly."""
    if args.live:
        dump_path = decode_codes.read_live_chip()
        source_label = f"LIVE chip read ({dump_path})"
        cleanup_dir = os.path.dirname(dump_path)
    elif args.dump is not None:
        dump_path = args.dump
        if not os.path.isfile(dump_path):
            sys.exit(f"ERROR: dump file not found: {dump_path}")
        source_label = dump_path
        cleanup_dir = None
    else:
        dump_path, source_label, _ = decode_codes.load_sample_copy()
        cleanup_dir = os.path.dirname(dump_path)
    try:
        with open(dump_path, "rb") as f:
            data = f.read()
        decode_codes.validate_page0(data, dump_path)
        slots = decode_codes.parse_slots(data)
        decode_codes.print_table(slots, show_all=args.all, source_label=source_label)
        if not args.live:
            # Depth for advanced users from the safe path: show the exact
            # minipro read command the --live path WOULD run against the real
            # chip. (This decode came from a file/sample copy, not hardware.)
            would_run = " ".join(decode_codes.live_read_command("live-read.bin"))
            print("  Under the hood, the live read path (--live) would run:")
            print(f"    $ {would_run}")
            print()
    finally:
        if cleanup_dir is not None:
            shutil.rmtree(cleanup_dir, ignore_errors=True)
    return 0


# ---------------------------------------------------------------------------
# WRITE
# ---------------------------------------------------------------------------
def resolve_role(role_arg: str | None) -> tuple[int, str]:
    """Map a --role value (name or 0xNN) to (perm_byte, display_name).

    Default role is Normal User (0x01) — the least-privileged, safest default
    for an attendee's first custom code.
    """
    if role_arg is None:
        return 0x01, "Normal User"
    raw = role_arg.strip().lower()
    if raw in ROLE_TO_PERM:
        perm = ROLE_TO_PERM[raw]
        return perm, PERM_TO_ROLE_NAME.get(perm, raw.title())
    # accept a literal 0xNN / NN hex permission byte
    try:
        perm = int(raw, 16) if raw.startswith("0x") else int(raw, 16)
    except ValueError:
        valid = ", ".join(sorted(set(ROLE_TO_PERM)))
        sys.exit(
            f"ERROR: unknown role {role_arg!r}. Use one of: {valid} "
            f"(or a hex permission byte like 0xF1)."
        )
    if perm not in build_injected.VALID_PERMS:
        valid = ", ".join(f"0x{v:02X}" for v in sorted(build_injected.VALID_PERMS))
        sys.exit(f"ERROR: permission 0x{perm:02X} not in valid set ({valid}).")
    return perm, PERM_TO_ROLE_NAME.get(perm, f"0x{perm:02X}")


def live_write_command(injected_path: str, minipro_bin: str = MINIPRO_BIN) -> list[str]:
    """The exact minipro argv that the --live write path runs to flash
    `injected_path` onto the real chip. One definition, shared by the preview
    surfacing (so advanced users see the under-the-hood command from the safe
    path) and by _flash_live (the path that actually runs it). No sudo: the
    installed uaccess udev rule grants the logged-in user direct device access.

    `minipro_bin` defaults to the bare 'minipro' name (so the preview command
    reads as the canonical PATH invocation); _flash_live passes the RESOLVED
    path (PATH minipro, else the bundled bin/minipro) so the actual flash works
    even before install.sh has put minipro on PATH."""
    # Scope the write (erase+program+verify) to the 'code' main-array memory
    # region. The AT45DB041E user-id signature-section read/write times out on
    # T48 firmware 00.1.34 (LIBUSB_ERROR_TIMEOUT; vendor notes "T48 support is
    # not yet complete"), and the write's verify pass would hit that same
    # section. The lock's entire user-code table lives in the 'code' main
    # array, so '-c code' writes exactly the bytes this tool uses and avoids
    # the flaky signature section — robust and exactly-targeted, not a hack.
    return [minipro_bin, "-i", "-p", DEVICE_NAME, "-c", "code", "-w", injected_path]


def occupied_slot_warning(source_bytes: bytes, slot: int) -> str | None:
    """Return the occupied-slot warning string if `slot` is already active in
    `source_bytes`, else None. Pure (no I/O) so the self-test can assert on the
    exact message without capturing stdout. cmd_write calls this and prints the
    result before the write; a None result means a normal additive add (no warn).
    """
    source_slots = decode_codes.parse_slots(source_bytes)
    existing = next((s for s in source_slots if s["slot"] == slot), None)
    if existing is not None and existing["active"]:
        return (f"WARNING: slot {slot} is already occupied by code "
                f"{existing['code']} ({existing['role']}) — your write OVERWRITES "
                f"that slot. All other slots are preserved (this is an additive "
                f"read-modify-write).")
    return None


def cmd_write(args) -> int:
    """WRITE control with a custom-value field.

    Bakes the attendee's own code (+ slot + role) into a COPY of the sample
    dump via build-injected.py's encoder, writes the result file, RE-DECODES it,
    and shows the attendee their value in the same readable form the READ
    control prints. Optionally flashes the result to the live chip (advanced,
    confirmation-gated).
    """
    code = args.code.strip()
    if len(code) != 6 or not code.isdigit():
        sys.exit(f"ERROR: --code {args.code!r} must be exactly 6 decimal digits "
                 f"(e.g. 246810). Zeros are allowed — the tool encodes them with "
                 f"the 0xB-for-zero rule for you.")
    slot = args.slot
    if not (0 <= slot <= MAX_SLOT):
        sys.exit(f"ERROR: --slot {slot} out of range 0..{MAX_SLOT}.")
    perm, role_display = resolve_role(args.role)

    # Locate + copy the baseline. We never touch the bundled original; we build
    # the injected dump from a COPY.
    src = decode_codes.find_sample_dump()
    if src is None:
        sys.exit(
            "ERROR: could not locate the bundled sample dump to build from. "
            "Expected it in a sibling dumps/ directory. Pass --baseline-dump if "
            "you must build from a non-standard path."
        )
    if args.baseline_dump is not None:
        src = args.baseline_dump
        if not os.path.isfile(src):
            sys.exit(f"ERROR: --baseline-dump not found: {src}")

    with open(src, "rb") as f:
        baseline = f.read()
    build_injected.validate_baseline(baseline, src)

    # Occupied-slot pre-write notice. The default sample now ships the three
    # workshop codes baked at slots 19/32/49, so an attendee who writes to one of
    # those slots OVERWRITES a default code rather than adding a fresh one. If the
    # target slot is already active in the SOURCE, surface a clear warning BEFORE
    # the write result. This is informational only — it does not change the
    # additive read-modify-write, the successful-write path, or the exit code; an
    # empty target slot produces no warning (a normal additive add).
    warn = occupied_slot_warning(baseline, slot)
    if warn is not None:
        print()
        print(f"  {warn}")

    patches = [{
        "slot": slot,
        "code": code,
        "perm": perm,
        "perm_name": role_display,
    }]
    build_injected.validate_patches(patches)
    injected, changes = build_injected.apply_patches(baseline, patches)

    # Decide where to write the injected dump. Default to a tempdir copy unless
    # the attendee names --out (so they can keep the artifact / flash it later).
    if args.out is not None:
        out_path = args.out
        out_dir_cleanup = None
    else:
        out_dir_cleanup = tempfile.mkdtemp(prefix="lock-tool-write-")
        out_path = os.path.join(out_dir_cleanup, "injected.bin")

    try:
        with open(out_path, "wb") as f:
            f.write(injected)

        print()
        print("=" * 72)
        print("  WRITE — your custom value baked into a copy of the sample dump")
        print("=" * 72)
        print(f"  Code:        {code}")
        print(f"  Slot:        {slot}")
        print(f"  Role:        {role_display} (0x{perm:02X})")
        print(f"  Built from:  {src}  (a copy — original untouched)")
        print(f"  Result file: {out_path}")
        build_injected.print_changes(changes)

        # RE-DECODE the injected result so the attendee sees their value land in
        # the same table the READ control prints.
        with open(out_path, "rb") as f:
            data = f.read()
        decode_codes.validate_page0(data, out_path)
        slots = decode_codes.parse_slots(data)
        print("  Re-decoding the result so you can see your value land:")
        decode_codes.print_table(
            slots, show_all=False,
            source_label=f"your injected dump ({out_path})")

        # Confirm the attendee's slot now reads back what they entered IN THE
        # COPY. This verifies the encode/decode round trip — it says nothing
        # about the real chip. The verdict line below makes that unmissable.
        target = next(s for s in slots if s["slot"] == slot)
        round_trip_ok = (target["code"] == code and target["active"])
        if not round_trip_ok:
            print(f"  WARNING: slot {slot} re-decode = {target['code']!r}, "
                  f"active={target['active']} — expected {code}. "
                  f"This should not happen; flag a facilitator.")
            print()

        if args.live:
            # The --live path actually writes to hardware; its own confirmation
            # banner and post-flash "landed on the real chip" verdict are
            # printed by _flash_live. No PREVIEW banner here.
            _flash_live(out_path, code, slot, role_display, args.yes)
        else:
            # PREVIEW / PRACTICE PATH — nothing was written to the lock. Say so
            # LOUDLY so it can't be skimmed past. The earlier "CONFIRMED … your
            # value landed" wording was a trap: it read like a hardware success
            # on a path that never touched the chip.
            would_run = " ".join(live_write_command(out_path))
            print("=" * 72)
            print("  PREVIEW ONLY — nothing was written to the lock.")
            print("=" * 72)
            if round_trip_ok:
                print(f"  Your code {code} decodes correctly in slot {slot} "
                      f"({role_display}) — but only in this COPY of the dump.")
            print("  This built a copy of the dump so you can see your code")
            print("  decode; the real chip is untouched.")
            print("  To actually flash this onto the lock: re-run with --live")
            print("  (or use the browser panel's Live-lock mode).")
            print("  Under the hood, the live path would run:")
            print(f"    $ {would_run}")
            print("=" * 72)
            print()

    finally:
        if out_dir_cleanup is not None:
            shutil.rmtree(out_dir_cleanup, ignore_errors=True)
    return 0


def _flash_live(injected_path: str, code: str, slot: int,
                role_display: str, assume_yes: bool) -> None:
    """ADVANCED: flash the injected dump to the real chip. Confirmation-gated,
    reusing recover-baseline.py's safety posture (loud-fail on missing
    programmer, explicit gate, fully-qualified device string)."""
    minipro_bin = decode_codes.resolve_minipro()
    if minipro_bin is None:
        # Shared, actionable message (bundled binary + install helper + Mac/Win).
        # The injected dump is already saved, so note that before the message.
        sys.exit(
            f"  (Your injected dump was still built and saved at {injected_path}; "
            f"the SAFE path stops here.)\n"
            + decode_codes.minipro_not_found_message("live write")
        )
    # No sudo: the uaccess udev rule grants the logged-in user direct device
    # access, so minipro runs as the unprivileged attendee. Same command the
    # preview path advertises (live_write_command), now actually run with the
    # RESOLVED binary (PATH minipro, else the bundled bin/minipro).
    cmd = live_write_command(injected_path, minipro_bin)
    print("=" * 72)
    print("  LIVE CHIP WRITE — advanced, confirmation gate")
    print("=" * 72)
    print(f"  This will ERASE + REPROGRAM the real lock's page-0 with your")
    print(f"  custom code {code} in slot {slot} ({role_display}).")
    print(f"  Clip must be seated on the AT45DB041E; lock batteries OUT.")
    print(f"  Recovery is always available: recover-baseline.py restores the")
    print(f"  canonical baseline (MD5-gated).")
    print(f"  Command:")
    print(f"    {' '.join(cmd)}")
    print("=" * 72)
    if not assume_yes:
        try:
            answer = input("  Proceed with LIVE write? [yes/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            sys.exit("\nERROR: confirmation aborted — no live write performed.")
        if answer not in ("yes", "y"):
            sys.exit("ERROR: confirmation declined — no live write performed.")
    print()
    print(f"  $ {' '.join(cmd)}")
    print()
    try:
        rc = subprocess.call(cmd)
    except FileNotFoundError as e:
        sys.exit(f"ERROR: {e}. minipro lives at /usr/local/bin/minipro.")
    except KeyboardInterrupt:
        sys.exit("\nERROR: live write aborted (Ctrl-C). The chip may be in a "
                 "partially-written state — run recover-baseline.py to restore.")
    if rc != 0:
        sys.exit(
            f"ERROR: minipro write returned exit code {rc}. Re-seat the clip "
            f"and re-run, or run recover-baseline.py to restore the baseline."
        )
    print()
    print(f"  LIVE WRITE OK — landed on the REAL chip. {lands_on_lock_summary(code, slot, role_display)}")
    print("  Reinstall the lock batteries and try your code on the keypad.")
    print("  If anything is wrong, run recover-baseline.py.")
    print()


# ---------------------------------------------------------------------------
# Panel-callable entry points (programmatic, no input() deadlock)
# ---------------------------------------------------------------------------
def _ns(**kw):
    """Build a SimpleNamespace args object the cmd_* functions accept. Fills the
    optional fields cmd_read/cmd_write read so the panel doesn't have to."""
    from types import SimpleNamespace
    return SimpleNamespace(**kw)


def read_live(show_all: bool = True) -> int:
    """LIVE READ entry point for the browser panel (or any programmatic caller).

    Reads the real chip via minipro and prints the decoded user-code table to
    stdout. No input() anywhere on this path, so it is safe to call from inside
    an HTTP handler with stdout captured. Loud-fails (SystemExit) if minipro is
    missing or the clip did not bite — the caller surfaces that text. Returns 0
    on success.
    """
    return cmd_read(_ns(dump=None, all=show_all, live=True))


def flash_attendee_live(code: str, slot: int = 25, role: str | None = None,
                        out: str | None = None) -> int:
    """LIVE WRITE entry point for the browser panel — confirmation PRE-GRANTED.

    The panel does its own confirmation in the browser, then calls this. It
    flashes the canonical SAMPLE-flash state to the real chip: a copy of the
    bundled sample dump (which already carries the three demo codes at slots
    19/32/49 + the 123456 starter at slot 0) with the attendee's `code` injected
    at `slot`/`role`. Every attendee therefore ends on the same deterministic,
    repeatable known-good state — see lands_on_lock_summary() for the exact
    contents to display in the UI.

    yes=True is passed through to cmd_write -> _flash_live(assume_yes=True), so
    NO input() is ever reached: this will not deadlock in an HTTP handler. The
    loud-fail-on-missing-minipro guard and the recover-baseline.py safety
    language are preserved unchanged. Returns 0 on a successful flash; raises
    SystemExit (with operator-facing text) on any failure the caller can show.
    """
    return cmd_write(_ns(code=code, slot=slot, role=role, out=out,
                         baseline_dump=None, live=True, yes=True))


# ---------------------------------------------------------------------------
# Self-test — no hardware. Exercises a full write-into-a-copy + re-decode round
# trip for a custom code (including a zero digit, to hit the 0xB rule) and
# confirms the re-decode reads back exactly what was written.
# ---------------------------------------------------------------------------
def run_self_test() -> int:
    print("lock-tool.py self-test")
    failures = 0

    def check(label, ok, detail=""):
        nonlocal failures
        print(f"  [{'PASS' if ok else 'FAIL'}] {label} {detail}")
        if not ok:
            failures += 1

    # Role resolution
    perm, name = resolve_role("supervisor")
    check("role 'supervisor' -> 0xC1", perm == 0xC1, f"(got 0x{perm:02X} {name})")
    perm, name = resolve_role(None)
    check("default role -> Normal User 0x01", perm == 0x01, f"(got 0x{perm:02X} {name})")
    perm, name = resolve_role("0xF1")
    check("role '0xF1' -> Master", perm == 0xF1, f"(got 0x{perm:02X} {name})")

    # Full encode -> apply -> re-decode round trip on a synthetic baseline, with
    # a zero digit to exercise the 0xB-for-zero path end to end.
    page = bytearray([0xFF] * DUMP_SIZE)
    page[0] = 0xFD
    # seed slot 0 = 123456 Normal so the baseline validates + has a known slot
    page[build_injected.OFF_CODE_BYTE_1] = 0x12
    page[build_injected.OFF_CODE_BYTE_2] = 0x34
    page[build_injected.OFF_CODE_BYTE_3] = 0x56
    page[build_injected.OFF_ACTIVE] = 0x01
    page[build_injected.OFF_PERM] = 0x01
    baseline = bytes(page)
    test_code = "240680"   # contains zeros -> exercises 0xB nibble
    patches = [{"slot": 25, "code": test_code, "perm": 0xC1, "perm_name": "Supervisor"}]
    build_injected.validate_patches(patches)
    injected, _changes = build_injected.apply_patches(baseline, patches)
    slots = decode_codes.parse_slots(injected)
    s25 = next(s for s in slots if s["slot"] == 25)
    check("write 240680 -> slot 25 re-decodes to 240680",
          s25["code"] == test_code and s25["active"],
          f"(got {s25['code']!r}, active={s25['active']})")
    check("slot 25 role is Supervisor", s25["role"] == "Supervisor",
          f"(got {s25['role']!r})")
    # untouched slot 0 still reads 123456
    s0 = next(s for s in slots if s["slot"] == 0)
    check("untouched slot 0 still 123456", s0["code"] == "123456",
          f"(got {s0['code']!r})")

    # Occupied-slot warning: slot 0 is active in `baseline`, so writing to it
    # must emit the warning; an empty slot (25) must NOT. Assert on the pure
    # helper so the contract holds without capturing cmd_write's stdout.
    warn_occupied = occupied_slot_warning(baseline, 0)
    check("occupied slot 0 emits warning",
          warn_occupied is not None and "already occupied" in warn_occupied
          and "123456" in warn_occupied,
          f"(got {warn_occupied!r})")
    check("empty slot 25 emits no warning",
          occupied_slot_warning(baseline, 25) is None,
          f"(got {occupied_slot_warning(baseline, 25)!r})")

    # D2: the live minipro write command surfacing is exact + copy-pasteable.
    wcmd = live_write_command("/tmp/injected.bin")
    check("live write command is the minipro -c code -w invocation",
          wcmd == [MINIPRO_BIN, "-i", "-p", DEVICE_NAME, "-c", "code",
                   "-w", "/tmp/injected.bin"],
          f"(got {' '.join(wcmd)!r})")
    rcmd = decode_codes.live_read_command("/tmp/live-read.bin")
    check("live read command is the minipro -c code -r invocation",
          rcmd == [decode_codes.MINIPRO_BIN, "-i", "-p", decode_codes.DEVICE_NAME,
                   "-c", "code", "-r", "/tmp/live-read.bin"],
          f"(got {' '.join(rcmd)!r})")

    # D4: the panel's 'what lands on the lock' summary names the attendee code +
    # all three demo codes + the starter, so the UI can display it verbatim.
    summary = lands_on_lock_summary("246810", 25, "Normal User")
    check("lands-on-lock summary names attendee code + 3 demos + starter",
          "246810" in summary and "133769" in summary and "420420" in summary
          and "696969" in summary and "123456" in summary,
          f"(got {summary!r})")

    # Roll the bundled-tool self-tests in so a regression in either sibling also
    # fails lock-tool --self-test.
    print()
    print("  --- decode-codes.py decoder self-test ---")
    rc_dec = decode_codes.run_self_test()
    if rc_dec != 0:
        failures += 1

    print()
    if failures:
        print(f"  RESULT: FAIL — {failures} lock-tool check(s) failed.")
        return 1
    print("  RESULT: PASS — read/write round trip holds.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Read or write the AT45DB041E lock user-code table. READ decodes the "
            "page-0 table; WRITE bakes your own custom code into a copy of the "
            "sample dump and shows you the result. Safe sample-dump-copy path by "
            "default; --live is the advanced real-chip path."
        )
    )
    parser.add_argument("--self-test", action="store_true",
                        help="run the read/write round-trip self-test and exit")
    sub = parser.add_subparsers(dest="command")

    p_read = sub.add_parser("read", help="decode + print the user-code table")
    p_read.add_argument("--dump", default=None,
                        help="decode this dump file instead of the bundled sample")
    p_read.add_argument("--all", action="store_true",
                        help="list every slot including empty ones")
    p_read.add_argument("--live", action="store_true",
                        help="ADVANCED: read the real chip first, then decode")

    p_write = sub.add_parser("write", help="bake a custom code into a copy + re-decode")
    p_write.add_argument("--code", required=True,
                         help="your 6-digit code, e.g. 246810 (zeros allowed)")
    p_write.add_argument("--slot", type=int, default=25,
                         help=f"slot 0..{MAX_SLOT} to write into (default 25)")
    p_write.add_argument("--role", default=None,
                         help="master | elevated | supervisor | normal "
                              "(or a hex perm byte; default normal)")
    p_write.add_argument("--out", default=None,
                         help="write the injected dump here (default: a tempfile)")
    p_write.add_argument("--baseline-dump", default=None,
                         help="build from this baseline instead of the bundled sample")
    p_write.add_argument("--live", action="store_true",
                         help="ADVANCED: flash the result to the real chip "
                              "(confirmation-gated)")
    p_write.add_argument("--yes", action="store_true",
                         help="skip the live-write confirmation (batch only)")

    args = parser.parse_args()

    if args.self_test:
        sys.exit(run_self_test())
    if args.command == "read":
        sys.exit(cmd_read(args))
    if args.command == "write":
        sys.exit(cmd_write(args))
    parser.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()

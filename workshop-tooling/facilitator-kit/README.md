# facilitator-kit-toorcamp-2026

**ToorCamp 2026 — "Dead Bytes Tell No Lies: Hands-On NAND Flash Decoding for Access Control Locks"**

One-command bootstrap for a workshop station laptop. Drop the tarball on a fresh Kali install, extract, run the installer, the station is workshop-ready.

---

## Quick start (facilitator on workshop day)

```
tar -xzf facilitator-kit-toorcamp-2026.tar.gz
cd facilitator-kit-toorcamp-2026
sudo ./install.sh
```

That's it. After `install.sh` completes:

- `minipro` is on `$PATH` at `/usr/local/bin/minipro`
- T48 udev rules are installed so non-root users in the `plugdev` group can access the programmer
- Your invoking user (`$SUDO_USER`) has been added to `plugdev` (must log out + back in for the group change to take effect on existing shells)
- `~/workshop/` is populated with:
  - `docs/` — the four-doc reference set
  - `tools/` — the two Python scripts
  - `dumps/` — the canonical T+4e baseline (the recovery dump every station uses)

Both Python scripts' self-test modes are exercised as the final smoke gate; the installer exits non-zero on any failure.

## Verify the kit before you trust it

Before running the installer, MD5-verify the kit against its bundled manifest:

```
./selftest.sh
```

or equivalently:

```
make selftest
```

`selftest.sh` is **hardware-free** — it does not need the T48 programmer or any USB device. It walks `MANIFEST.md`, re-MD5s every file in the kit, and then exercises the Python self-test entry points against the bundled baseline. Run this:

- After any transfer (USB stick, scp, download) to catch corruption
- On every station before opening the doors to attendees
- Any time the kit's MD5 surprises you

## What's in the kit

```
facilitator-kit/
├── README.md                          this file
├── Makefile                           build targets (tarball, selftest, clean)
├── install.sh                         one-command Kali stand-up
├── selftest.sh                        hardware-free integrity check
├── MANIFEST.md                        every kit file + size + MD5 + role
├── bin/
│   └── minipro                        minipro 0.7.4 (Linux-AMD64 ELF)
├── etc/udev/rules.d/
│   ├── 60-minipro.rules               USB vendor:product tagging
│   ├── 61-minipro-plugdev.rules       MODE=660 GROUP=plugdev
│   └── 61-minipro-uaccess.rules       TAG+=uaccess (logind seat access)
├── docs/
│   ├── FACILITATOR-GUIDE.md           facilitator-facing bench-day runbook
│   ├── PARTICIPANT-HANDOUT.md         attendee-facing 1-page handout
│   ├── DUMP-VALIDATION.md             AT45DB041E page-0 layout + BCD-B encoding
│   ├── T48-KALI-PLAN.md               T48 Kali bring-up reference
│   └── T+4e-DUMP-VALIDATION-REPORT.md provenance of the canonical baseline
├── tools/
│   ├── build-injected.py              builds injected.bin from baseline + patch
│   └── recover-baseline.py            recovers from a botched workshop write
└── dumps/
    ├── intact-lock-AT45DB041E-main-2026-05-20.bin   the T+4e canonical baseline
    └── MANIFEST.md                                  sub-manifest for .bin files
```

## Bench-day workflow

Once the laptop is set up, the operative reference is `~/workshop/docs/FACILITATOR-GUIDE.md`. The 30-second summary:

1. Clip the SOIC-8 onto the lock's AT45DB041E. Batteries OUT.
2. Read the chip → attendee constructs an injected.bin via `tools/build-injected.py`.
3. Write the injected.bin → attendee tests their codes.
4. **When something goes wrong** — write fails, attendee panics, MD5 doesn't match — the recovery path is:
   ```
   python3 ~/workshop/tools/recover-baseline.py
   ```
   That script refuses to write anything except the canonical T+4e baseline (MD5-gated), prompts for confirmation, and verifies post-write by read-back. Default-on safety, ~20s extra; `--skip-verify` opts out if time pressure demands.

The recovery script now auto-detects the baseline. On a station the installer lands the canonical dump at `~/workshop/dumps/intact-lock-AT45DB041E-main-2026-05-20.bin`, and the script finds it there automatically — no `--baseline` flag and no symlink needed. (It also still resolves the operator's bench path at `~/Desktop/toorcamp-2026-dumps/intact-lock-AT45DB041E-main-2026-05-20.bin`.) Pass `--baseline /path/to/dump` only if the baseline lives somewhere non-standard. The MD5 gate is unchanged: whatever path is resolved, the script refuses to write anything but the canonical `eb6acff32ef13b29ac6ebed10d77316d` baseline.

## Provenance

- **Kit version:** 1.0.0
- **Built from source tree:** `output/toorcamp-2026/workshop-tooling/facilitator-kit/` in the TMP repo
- **minipro source:** DavidGriffith GitLab fork commit `fd6b56af`, built on the operator's Kali host T+1 (binary copied straight from `/usr/local/bin/minipro` after a clean `make && sudo make install`)
- **Canonical baseline MD5:** `eb6acff32ef13b29ac6ebed10d77316d` (T+4e operator-bench validated; two independent reads byte-identical)
- **Baseline size:** 540,672 bytes (AT45DB041E main array, 2048 pages * 264 bytes — NOT including the 128-byte Security Register)

## Known limitations

- **Architecture:** Kali-AMD64 only. The bundled `bin/minipro` is x86_64 ELF. The installer refuses to run on any other architecture in the preflight step.
- **Requires sudo:** the installer drops a binary in `/usr/local/bin/`, udev rules in `/etc/udev/rules.d/`, reloads udev, and (defensively) ensures the invoking user is in `plugdev`. There is no rootless install path.
- **Per-station hardware:** the laptop alone is insufficient. Each station also needs a T48 USB programmer, a Pomona 5250 SOIC-8 clip (or equivalent), and an Alarm Lock T2/T3 keypad lock with an AT45DB041E DataFlash.
- **plugdev group change requires re-login:** if the installer adds `$SUDO_USER` to `plugdev`, that user must log out and back in (or run `newgrp plugdev`) before they can talk to the T48 without `sudo`. Existing shells inherit the old group set.
- **Sensitive content:** `dumps/intact-lock-AT45DB041E-main-2026-05-20.bin` is a real captured memory image of a real lock unit. Workshop-internal only — do not redistribute outside the facilitator chain-of-custody.

## Support

The kit is built and maintained from the TMP repo at `output/toorcamp-2026/workshop-tooling/facilitator-kit/`. Rebuild with `make tarball`; the build is reproducible (two consecutive builds produce byte-identical output) under `SOURCE_DATE_EPOCH=1747526400`.

If `install.sh` fails partway, it prints a `--resume-from <step>` hint. Fix the underlying issue, then re-run with the hint to continue from where it stopped.

If `selftest.sh` fails with MD5 mismatches, the tarball is corrupt. Re-download the kit. Do not attempt to "fix" individual files — the baseline is MD5-gated downstream by `recover-baseline.py` and a wrong baseline at recovery time is worse than no kit at all.

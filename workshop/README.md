# Workshop — Dead Bytes Tell No Lies

The hands-on companion to the talk. Attendees clip a flash programmer onto a real Alarm Lock T2/T3's AT45DB041E DataFlash chip, decode the user-code page by hand, build an injected dump that adds their own codes, write it back, and watch the lock open with a code they just forged.

## Start here — reading order

1. **`PARTICIPANT-HANDOUT.md`** — what an attendee follows at the bench. The 1-page hands-on flow.
2. **`FACILITATOR-GUIDE.md`** — what a facilitator runs: station map, run-of-show, per-attendee flow, troubleshooting, and the pocket reference.
3. **`kit/`** — the build kit that stands up a workshop station laptop (`make` targets, `install.sh`, the tools, and the baseline dump).
4. **`kit/docs/DATAFLASH-DECODE-REFERENCE.md`** — the decode reference: the AT45DB041E page-0 layout, the offset map, and the packed-BCD / `0xB`-for-zero encoding rules.

## Self-service read/write tools

Once the station is up, `~/workshop/tools/` holds the attendee read/write tooling, layered from a dead-simple bedrock up to convenience wrappers:

- `lock-tool.py read --all` — decode and print the page-0 user-code table (the **READ**). No hardware needed; it works on a copy of the bundled sample dump.
- `lock-tool.py write --code 246810 --slot 25 --role supervisor` — bake your own custom code into a copy and re-decode it so you see it land (the **WRITE**).
- `lock-menu.py` — a plain-text menu over those same actions.
- `lock-panel.py` — a localhost browser control panel: a READ button, a custom-value field, and a WRITE button.

The menu and panel are thin wrappers; if either won't launch, the `lock-tool.py` one-liners still work and the wrappers print them. The live-chip read/write path is the advanced, confirmation-gated opt-in (`lock-tool.py ... --live`); everything defaults to the safe sample-dump-copy path.

---

## For organizers — building & standing up a station

The rest of this README is facilitator-oriented: building and verifying the kit, standing up a station laptop, and editing the source docs. **A pure attendee does not need any of it** — clone the repo and follow `PARTICIPANT-HANDOUT.md`. This section is for whoever is provisioning the station hardware.

### Build and verify the kit

The kit is built and validated from `kit/`. Run these from the kit directory:

1. Assemble the kit from its source files. This copies the latest facing docs, the decode reference, and the Python tools into the kit, then regenerates the manifests. From the repo root:

   ```
   cd workshop/kit
   make assemble
   ```

   The command prints `==> Assembly complete.` on success.

2. Verify kit integrity. This MD5-checks every kit file against `MANIFEST.md` and exercises both Python tools' self-test modes. It is hardware-free — no T48 programmer or USB device required.

   ```
   make selftest
   ```

   The run must end with `selftest RESULT: PASS` and `Checked: 18 files`.

3. (Optional) Build the distributable tarball. This produces a reproducible `facilitator-kit-toorcamp-2026.tar.gz` one level up, in `workshop/`.

   ```
   make tarball
   ```

   Two consecutive `make tarball` runs produce byte-identical output. Run `make clean` to remove the built tarball, or `make help` to list all targets.

### Stand up a station laptop

On a fresh Kali laptop, drop the tarball, extract it, and run the installer:

```
tar -xzf facilitator-kit-toorcamp-2026.tar.gz
cd facilitator-kit-toorcamp-2026
sudo ./install.sh
```

After `install.sh` completes, `minipro` is on `$PATH`, the T48 udev rules are installed, the invoking user is in the `plugdev` group (log out and back in for that to take effect), and `~/workshop/` holds the docs, the Python tools, and the canonical baseline dump. The installer exercises every Python tool's self-test as its final smoke gate and exits non-zero on any failure. See `kit/README.md` for the full stand-up walkthrough, the recovery workflow, and known limitations.

#### One command from a fresh clone

If you would rather not `cd` into the kit, the repo root ships a single bootstrap that assembles, verifies, and stands up the station in one go. From the cloned repo root:

```
sudo ./bootstrap.sh
```

It is path-relative — clone the repo anywhere and run it; nothing hardcodes a home directory. The same end-to-end stand-up is available from the kit as `make station`.

### Editing the docs — edit the sources, not the kit copies

`kit/docs/` and `kit/tools/` are **build outputs**. `make assemble` regenerates them by copying from the source files in `workshop/` and `workshop/src/`:

| Edit this source | Regenerated kit copy |
|---|---|
| `workshop/FACILITATOR-GUIDE.md` | `kit/docs/FACILITATOR-GUIDE.md` |
| `workshop/PARTICIPANT-HANDOUT.md` | `kit/docs/PARTICIPANT-HANDOUT.md` |
| `workshop/src/DATAFLASH-DECODE-REFERENCE.md` | `kit/docs/DATAFLASH-DECODE-REFERENCE.md` |
| `workshop/src/build-injected.py` | `kit/tools/build-injected.py` |
| `workshop/src/recover-baseline.py` | `kit/tools/recover-baseline.py` |

After editing any source, re-run `make assemble && make selftest` from `kit/` so the kit copies and their MD5 manifests stay current. Never hand-edit a file under `kit/docs/` or `kit/tools/` — the next `make assemble` will overwrite it.

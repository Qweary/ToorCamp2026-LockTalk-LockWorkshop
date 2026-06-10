# minipro — bundled binary attribution and license notice

This kit ships a compiled copy of **minipro** at `bin/minipro` (Linux x86-64
ELF). minipro is third-party Free Software, distributed here under the terms of
its own license. The workshop's own code (the Python tools, the docs, the build
scripts) is licensed separately — see the repository's top-level `LICENSE`. This
notice covers **only** the bundled `bin/minipro` binary.

## What it is

minipro is an open-source command-line programmer for the TL866/T48/T56/T76
family of EEPROM/flash programmers. The workshop uses it to read and write the
serial DataFlash chip on the lock board over a SOIC-8 clip.

## Upstream project

- **Project:** minipro
- **Maintainer:** David Griffith and contributors
- **Source:** <https://gitlab.com/DavidGriffith/minipro>

## Bundled version

- **Version:** 0.7.4
- **Commit:** `fd6b56afcfee1bbcef78e465b7c512c1cd1999d3`
  (the short form `fd6b56af` appears in the kit Makefile and in the
  `MANIFEST.md` provenance for `bin/minipro`)
- **Build target:** Linux x86-64 (AMD64) ELF

Both the version string (`0.7.4`) and the full commit hash are embedded in the
binary itself and can be confirmed with:

    strings bin/minipro | grep -E '0\.7\.4|fd6b56af'
    bin/minipro -V

## License

minipro is licensed under the **GNU General Public License, version 3 (GPLv3)**.
The full license text is published with the upstream source at the URL above
(the `COPYING` file in the project root). Because GPLv3 governs the binary, the
binary may be freely used, studied, copied, and redistributed under those terms.

## Source availability (GPL §3 / §6 — written offer)

The complete corresponding source for this exact binary is the upstream
repository at the commit pinned above. To obtain it:

    git clone https://gitlab.com/DavidGriffith/minipro.git
    cd minipro
    git checkout fd6b56afcfee1bbcef78e465b7c512c1cd1999d3

This satisfies the GPL requirement that the source corresponding to a
distributed binary remain available to anyone who receives the binary.

## Rebuilding from source

The binary in this kit was built from the source above. To rebuild an
equivalent binary on a Debian/Kali host:

    sudo apt-get install -y build-essential pkg-config libusb-1.0-0-dev git
    git clone https://gitlab.com/DavidGriffith/minipro.git
    cd minipro
    git checkout fd6b56afcfee1bbcef78e465b7c512c1cd1999d3
    make
    sudo make install        # installs minipro + the udev rules to the system

The `make install` step is also where the three bundled udev rules
(`60-minipro.rules`, `61-minipro-plugdev.rules`, `61-minipro-uaccess.rules`)
originate; this kit ships copies of those so device access works without a
separate upstream install.

## Other platforms

The bundled `bin/minipro` is a Linux x86-64 ELF and will not run on macOS or
Windows. On those platforms, install minipro from its own distribution:

- **macOS (Homebrew):** `brew install minipro`
- **Windows / other:** build from the upstream source above, or use a release
  from <https://gitlab.com/DavidGriffith/minipro/-/releases>

---

*This file is part of the workshop kit purely to honor minipro's GPLv3
redistribution-with-attribution terms. It is regenerated into the shipped kit by
`make assemble` and verified by `selftest.sh` via the kit `MANIFEST.md`.*

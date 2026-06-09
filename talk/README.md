# Talk — Dead Bytes Tell No Lies

The ToorCamp 2026 conference talk on the Alarm Lock Trilogy T2/T3 access-control lock: a five-layer attack chain (physical, DataFlash, firmware, USB-cable, audit-trail) told from a locksmith's lens.

## View the slides

1. Open **`index.html`** in any modern browser (double-click it, or `file://` it). The deck is a self-contained [reveal.js](https://revealjs.com) presentation — reveal.js is vendored under `lib/`, so there is no build step and no network needed.
2. Navigate with the **arrow keys** (`→` / `←` advance and reverse; `↓` / `↑` move within a vertical stack). Press `Esc` or `o` for the slide overview grid, and `f` for fullscreen.

That is the whole viewer. There is no separate speaker-view window in this deck — the speaker companion is `SPEAKING-NOTES.md` (below), read alongside the slides.

## Speaker materials

| File | What it is |
|---|---|
| **`index.html`** | The slide deck — open this to present. |
| **`SPEAKING-NOTES.md`** | The speaker's running notes: per-section cue-lines, timing windows, stage directions (`[PAUSE]`, `[CLICK]`, `[VIDEO]`), demo timing, and a timing summary table. Read this while rehearsing. |
| **`SLIDE-CONTENT.md`** | The slide-by-slide content outline — what appears on each slide (S1–S20 plus the demo-backup slide), with anchors and clock windows. Use it to edit slide copy or cross-check the deck. |

## Supporting files

- `lib/` — vendored reveal.js (the presentation engine). Do not edit.
- `css/`, `fonts/` — the deck's custom styling and typefaces.

## Showing the deck with media

The full-resolution photos (`img/`) and the factory-reset demo video
(`video/`) are **kept off-repo** so this clone stays small and fast — attendees
don't need to download hundreds of megabytes to read the deck.

The media zip is kept in your own storage. To show the full-quality photos and
the video (e.g. on a TV at the talk):

1. Place **`toorcamp-media.zip`** in your `Downloads` folder (this is all you
   need on a borrowed laptop — drop the zip in and go).
2. From the `talk/` directory, run:

   ```sh
   ./rehydrate-media.sh
   ```

   If you saved the zip somewhere else, pass its path:

   ```sh
   ./rehydrate-media.sh /path/to/toorcamp-media.zip
   ```

   The script unpacks the media into `img/` and `video/`, then prints
   `PASS — media is in place` (or tells you exactly what's missing). It's safe
   to re-run.
3. Open `index.html` and present — the deck now shows every photo and the demo
   video.

Without the media, the deck still loads and runs; the image and video slots
just show placeholders.


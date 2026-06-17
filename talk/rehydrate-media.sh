#!/usr/bin/env bash
#
# rehydrate-media.sh — drop the talk's full-resolution photos and demo video
# back into place from a single zip, so the deck shows everything.
#
# The media lives off-repo (it is large) and is kept in your own storage. Drop
# the zip locally, then run this script: it unzips the media so every file lands
# at exactly talk/img/<name> and talk/video/<name>, then verifies the count and
# prints a clear PASS/FAIL.
#
# Usage:
#   ./rehydrate-media.sh [path-to-zip]
#
#   path-to-zip   Optional. Where the media zip is. Defaults to
#                 ~/Downloads/toorcamp-media.zip
#
# Examples:
#   ./rehydrate-media.sh                         # uses ~/Downloads/toorcamp-media.zip
#   ./rehydrate-media.sh ~/Downloads/media.zip   # explicit path
#   ./rehydrate-media.sh /run/media/usb/x.zip    # from a USB stick
#
# Safe to re-run: it overwrites in place.

set -eu

# ----- expected media ------------------------------------------------------
EXPECTED_IMAGES=20
EXPECTED_VIDEOS=1
EXPECTED_POSTERS=1
EXPECTED_TOTAL=22

# ----- resolve paths from the SCRIPT's own location (run from anywhere) ----
# This script lives in <repo>/talk/, so the repo root is its parent's parent.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TALK_DIR="$SCRIPT_DIR"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IMG_DIR="$TALK_DIR/img"
VIDEO_DIR="$TALK_DIR/video"

# ----- the zip to unpack ---------------------------------------------------
DEFAULT_ZIP="$HOME/Downloads/toorcamp-media.zip"
ZIP_PATH="${1:-$DEFAULT_ZIP}"

say()  { printf '%s\n' "$*"; }
err()  { printf '%s\n' "$*" >&2; }

# ----- preflight: unzip present? ------------------------------------------
if ! command -v unzip >/dev/null 2>&1; then
  err "ERROR: 'unzip' is not installed."
  err "  Debian/Ubuntu/Kali:  sudo apt-get install unzip"
  err "  Fedora:              sudo dnf install unzip"
  err "  macOS:               brew install unzip   (usually preinstalled)"
  exit 1
fi

# ----- preflight: zip exists? ----------------------------------------------
if [ ! -f "$ZIP_PATH" ]; then
  err "ERROR: media zip not found at:"
  err "    $ZIP_PATH"
  err ""
  err "Fix one of these and re-run:"
  err "  1. Place 'toorcamp-media.zip' in your Downloads folder, then run:"
  err "       $0"
  err "  2. Or point this script straight at wherever you saved it:"
  err "       $0 /path/to/toorcamp-media.zip"
  exit 1
fi

say "Rehydrating talk media"
say "  zip:       $ZIP_PATH"
say "  repo root: $REPO_ROOT"
say ""

# ----- unzip into the repo root -------------------------------------------
# The zip stores files with repo-root-relative paths (talk/img/..., talk/video/...),
# so unzipping at the repo root places them exactly. -o overwrites (idempotent).
mkdir -p "$IMG_DIR" "$VIDEO_DIR"
unzip -o -q "$ZIP_PATH" 'talk/img/*' 'talk/video/*' -d "$REPO_ROOT"

# ----- verify --------------------------------------------------------------
# Images live in talk/img/ (*.jpg). The video dir holds the demo video (*.mp4)
# AND a poster still (*.jpg) — both must land. README.md is a tracked
# placeholder, not media, so it is never counted.
img_count=$(find "$IMG_DIR" -maxdepth 1 -type f -name '*.jpg' | wc -l | tr -d '[:space:]')
vid_count=$(find "$VIDEO_DIR" -maxdepth 1 -type f -name '*.mp4' | wc -l | tr -d '[:space:]')
poster_count=$(find "$VIDEO_DIR" -maxdepth 1 -type f -name '*.jpg' | wc -l | tr -d '[:space:]')
total=$(( img_count + vid_count + poster_count ))

say "  images:    $img_count / $EXPECTED_IMAGES"
say "  videos:    $vid_count / $EXPECTED_VIDEOS"
say "  posters:   $poster_count / $EXPECTED_POSTERS"
say "  total:     $total / $EXPECTED_TOTAL"
say ""

if [ "$img_count" -eq "$EXPECTED_IMAGES" ] \
   && [ "$vid_count" -eq "$EXPECTED_VIDEOS" ] \
   && [ "$poster_count" -eq "$EXPECTED_POSTERS" ]; then
  say "PASS — media is in place. Open talk/index.html and present."
  exit 0
fi

# ----- FAIL: report exactly what is missing --------------------------------
err "FAIL — media is incomplete."
if [ "$img_count" -ne "$EXPECTED_IMAGES" ]; then
  err "  Expected $EXPECTED_IMAGES images in talk/img/, found $img_count."
fi
if [ "$vid_count" -ne "$EXPECTED_VIDEOS" ]; then
  err "  Expected $EXPECTED_VIDEOS video in talk/video/, found $vid_count."
fi
if [ "$poster_count" -ne "$EXPECTED_POSTERS" ]; then
  err "  Expected $EXPECTED_POSTERS poster still (*.jpg) in talk/video/, found $poster_count."
fi
err ""
err "  The zip may be the wrong file or truncated. Replace it with a good copy"
err "  and re-run:  $0 $ZIP_PATH"
exit 1

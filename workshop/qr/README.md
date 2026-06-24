# Workshop QR code

QR code for the workshop repo, for slides / signage / a laser-engraved sign or light-up box.

- **Encodes:** `https://github.com/Qweary/deadbytes`
- **`deadbytes-qr.svg`** — vector, single path. Use this for laser (LightBurn/Inkscape import cleanly). Scales to any size with no quality loss.
- **`deadbytes-qr.png`** — raster preview for slides/screens.
- **Spec:** version 5, 37×37 modules, error-correction level **H (~30%)**, 4-module quiet zone.

## Laser / engraving notes
- Engrave the **dark modules** as the marked/opaque areas; keep the light areas and the 4-module quiet-zone border clear. Do **not** invert.
- Keep high contrast. For a back-lit box, dark modules should block light and the background transmit (or vice-versa) — whichever gives a scanner clear dark-on-light contrast.
- Don't go below ~2 cm square; bigger is safer for camera scans across a room.
- ECC is H, so a small center logo (up to ~30% area) is tolerable — but **test-scan** if you add one.
- **Always phone-scan the final piece before committing to a permanent engrave.**

## Regenerate (if the URL/repo name changes)
```
python3 - <<'PY'
import qrcode, qrcode.image.svg
URL = "https://github.com/Qweary/deadbytes"
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
qr.add_data(URL); qr.make(fit=True)
qr.make_image(image_factory=qrcode.image.svg.SvgPathImage).save("deadbytes-qr.svg")
q2 = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=20, border=4)
q2.add_data(URL); q2.make(fit=True)
q2.make_image(fill_color="black", back_color="white").save("deadbytes-qr.png")
PY
```

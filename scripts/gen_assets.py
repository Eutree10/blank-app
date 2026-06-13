#!/usr/bin/env python3
"""Generate Questline raster assets from the brand emblem geometry.

Outputs (committed under resources/drawables/):
  * launcher_icon.png  - app launcher icon (gold emblem on solid black)
  * logo.png           - 64px hub logo (transparent background)
  * logo_large.png     - 96px logo for larger surfaces

Requires Pillow:  pip install Pillow
Run from the repo root:  python3 scripts/gen_assets.py

The vector source of truth is resources/drawables/logo.svg.
"""
import math
from PIL import Image, ImageDraw

GOLD = (244, 180, 0, 255)       # #F4B400 brand/time
GOLD_DIM = (180, 132, 0, 255)
LIME = (163, 230, 53, 255)       # #A3E635 energy
TRANSPARENT = (0, 0, 0, 0)


def emblem(size, ring_frac=0.085):
    """A stopwatch / target dial: gold ring, crown button, ticks and a hand."""
    S = size * 4  # supersample then downscale for clean edges
    img = Image.new("RGBA", (S, S), TRANSPARENT)
    d = ImageDraw.Draw(img)
    cx = cy = S / 2
    r = S * 0.40
    rw = max(2, int(S * ring_frac))

    # Crown / start button on top
    bw, bh = S * 0.14, S * 0.10
    d.rounded_rectangle([cx - bw / 2, cy - r - bh * 1.3, cx + bw / 2, cy - r + bh * 0.2],
                        radius=bh * 0.4, fill=GOLD)
    sb = S * 0.05
    d.line([(cx + r * 0.72, cy - r * 0.72), (cx + r * 0.72 + sb, cy - r * 0.72 - sb)],
           fill=GOLD, width=int(rw * 0.9))

    # Outer ring
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD, width=rw)

    # Tick marks
    outer = r - rw * 0.6
    for i in range(12):
        a = math.radians(i * 30 - 90)
        major = (i % 3 == 0)
        ti = r - rw * (3.0 if major else 2.3)
        d.line([(cx + ti * math.cos(a), cy + ti * math.sin(a)),
                (cx + outer * math.cos(a), cy + outer * math.sin(a))],
               fill=GOLD if major else GOLD_DIM,
               width=int(rw * (0.8 if major else 0.5)))

    # Hands + center dot
    a = math.radians(45 - 90)
    d.line([(cx, cy), (cx + r * 0.62 * math.cos(a), cy + r * 0.62 * math.sin(a))],
           fill=LIME, width=int(rw))
    d.line([(cx, cy), (cx, cy + r * 0.30)], fill=GOLD, width=int(rw * 0.8))
    cr = rw * 1.1
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=GOLD)

    return img.resize((size, size), Image.LANCZOS)


def main():
    # Launcher icon: emblem on solid black.
    sz = 80
    base = Image.new("RGBA", (sz, sz), (0, 0, 0, 255))
    em = emblem(int(sz * 0.92))
    off = (sz - em.size[0]) // 2
    base.alpha_composite(em, (off, off))
    base.save("resources/drawables/launcher_icon.png")

    emblem(64).save("resources/drawables/logo.png")
    emblem(96).save("resources/drawables/logo_large.png")
    print("Questline assets written to resources/drawables/")


if __name__ == "__main__":
    main()

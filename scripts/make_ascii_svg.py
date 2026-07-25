#!/usr/bin/env python3
"""Render a prepped portrait (RGBA, background removed) into a monochrome
ASCII-art SVG that types itself in like a terminal.

Tune COLS/CONTRAST/GAMMA/WHITE_FLOOR below until the face reads well.
Set STATIC=1 to render the finished frame with no reveal animation
(useful for qlmanage previews, which show the SVG's t=0 state).
"""
import os
import sys

import numpy as np
from PIL import Image

# ---- tunables ----
COLS = 100
CHAR_ASPECT = 0.48       # monospace glyph width/height ratio
FONT_SIZE = 11           # px; controls cell size and overall SVG dimensions
CONTRAST = 1.0
GAMMA = 1.8              # >1 compresses midtones toward "sparse" so only true shadows go dense
WHITE_FLOOR = 30         # minimum text brightness (0-255) so shadows stay legible
TYPE_SPEED_MS = 2        # per-glyph reveal delay step (only rendered glyphs count)
BG_COLOR = "#0d1117"
RAMP = " .:-=+*#%@"
ALPHA_THRESHOLD = 40     # below this alpha, treat the cell as background

SRC = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
OUT = sys.argv[2] if len(sys.argv) > 2 else "avi-ascii.svg"
STATIC = os.environ.get("STATIC") == "1"


def load_grid():
    img = Image.open(SRC).convert("RGBA")
    w, h = img.size
    cell_w = w / COLS
    cell_h = cell_w / CHAR_ASPECT
    rows = max(1, int(h / cell_h))
    small = img.resize((COLS, rows), Image.LANCZOS)
    arr = np.array(small).astype(np.float32)
    lum = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]) / 255.0
    alpha = arr[:, :, 3]
    return lum, alpha, rows


def map_cell(lum_val: float):
    # Invert: shadows (eyes, brows, hairline) are the darkest pixels, so they
    # need to map to the densest glyphs -- otherwise they vanish into the
    # transparent background and the face reads as a blank skull.
    dark = 1.0 - lum_val
    dark = max(0.0, min(1.0, (dark - 0.5) * CONTRAST + 0.5))
    norm = dark ** GAMMA
    char = RAMP[int(norm * (len(RAMP) - 1))]
    gray = int(WHITE_FLOOR + (255 - WHITE_FLOOR) * norm)
    return char, gray


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;")


def build_svg() -> str:
    lum, alpha, rows = load_grid()
    cell_w = FONT_SIZE * CHAR_ASPECT
    cell_h = FONT_SIZE * 1.15
    width = COLS * cell_w
    height = rows * cell_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
        f'width="{width:.0f}" height="{height:.0f}" font-family="SFMono-Regular, Consolas, '
        f'\'Liberation Mono\', Menlo, monospace" font-size="{FONT_SIZE}">',
        f'<rect width="100%" height="100%" fill="{BG_COLOR}"/>',
    ]

    if not STATIC:
        parts.append(
            "<style>"
            ".c{opacity:0;animation:reveal .01s linear forwards;"
            f"animation-delay:calc(var(--i) * {TYPE_SPEED_MS}ms)}}"
            "@keyframes reveal{to{opacity:1}}"
            ".cursor{opacity:0;animation:blink 1s steps(1) infinite}"
            "@keyframes blink{0%,49%{opacity:0}50%,100%{opacity:1}}"
            "</style>"
        )

    idx = 0
    last_x = last_y = 0.0
    for r in range(rows):
        y = r * cell_h + FONT_SIZE
        for c in range(COLS):
            x = c * cell_w
            if alpha[r, c] < ALPHA_THRESHOLD:
                continue
            char, gray = map_cell(lum[r, c])
            if char == " ":
                continue
            cls = "" if STATIC else ' class="c"'
            style = "" if STATIC else f' style="--i:{idx}"'
            parts.append(
                f'<text x="{x:.1f}" y="{y:.1f}" fill="rgb({gray},{gray},{gray})"{cls}{style}>{esc(char)}</text>'
            )
            last_x, last_y = x, y
            idx += 1

    if not STATIC:
        cursor_delay = idx * TYPE_SPEED_MS
        parts.append(
            f'<rect class="cursor" x="{last_x:.1f}" y="{last_y - FONT_SIZE:.1f}" '
            f'width="{cell_w:.1f}" height="{cell_h:.1f}" fill="#e6edf3" opacity="0" '
            f'style="animation-delay:{cursor_delay}ms"/>'
        )

    parts.append("</svg>")
    return "".join(parts)


def main():
    svg = build_svg()
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render a terminal-style info card SVG. Edit HOST/ROWS below with real
content, then rerun. Keep H equal to the portrait's rendered height; bump it
if the rows overflow.
"""
import os
import sys

WIDTH = 490
H = 568          # matches the portrait's displayed height at width=370
FONT_SIZE = 14
LINE_H = 22
PAD_X = 20
HEADER_H = 34
BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"
PROMPT_COLOR = "#39d353"
TEXT_COLOR = "#c9d1d9"
MUTED_COLOR = "#8b949e"
LINE_STEP_MS = 90

HOST = "dhanush@github"

# Each row is (prompt, text). prompt="$" renders a command line;
# prompt="" renders plain output text.
ROWS = [
    ("$", "whoami"),
    ("", "Dhanush Aleti"),
    ("", "Building AI Products | Into Startups & Tech"),
    ("$", "cat focus.txt"),
    ("", "AI products, startups, product engineering"),
    ("$", "ls stack/"),
    ("", "python  typescript  react  nextjs  postgres"),
    ("$", "cat links.txt"),
    ("", "linkedin.com/in/dhanushaleti"),
    ("", "instagram.com/dxnush369"),
]

OUT = sys.argv[1] if len(sys.argv) > 1 else "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;")


def build_svg() -> str:
    needed = HEADER_H + 24 + len(ROWS) * LINE_H
    if needed > H:
        print(f"warning: ROWS overflow H={H} (need >= {needed}); bump H", file=sys.stderr)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {H}" '
        f'width="{WIDTH}" height="{H}" font-family="SFMono-Regular, Consolas, '
        f'\'Liberation Mono\', Menlo, monospace" font-size="{FONT_SIZE}">',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{H - 1}" rx="8" '
        f'fill="{BG_COLOR}" stroke="{BORDER_COLOR}"/>',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEADER_H}" rx="8" fill="#161b22"/>',
        f'<rect x="0.5" y="{HEADER_H - 8}" width="{WIDTH - 1}" height="8" fill="#161b22"/>',
    ]
    for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{20 + i * 18}" cy="{HEADER_H / 2}" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="{WIDTH / 2}" y="{HEADER_H / 2 + 4}" text-anchor="middle" '
        f'fill="{MUTED_COLOR}" font-size="12">{esc(HOST)}</text>'
    )

    if not STATIC:
        parts.append(
            "<style>"
            ".row{opacity:0;animation:reveal .01s linear forwards;"
            f"animation-delay:calc(var(--i) * {LINE_STEP_MS}ms)}}"
            "@keyframes reveal{to{opacity:1}}"
            "</style>"
        )

    content_h = len(ROWS) * LINE_H
    available_h = H - HEADER_H
    y = HEADER_H + max(28, (available_h - content_h) / 2 + LINE_H * 0.6)
    for i, (prompt, text) in enumerate(ROWS):
        cls = "" if STATIC else ' class="row"'
        style = "" if STATIC else f' style="--i:{i}"'
        parts.append(f'<g{cls}{style}>')
        if prompt:
            parts.append(f'<text x="{PAD_X}" y="{y}" fill="{PROMPT_COLOR}">{esc(prompt)}</text>')
            parts.append(f'<text x="{PAD_X + 16}" y="{y}" fill="{TEXT_COLOR}">{esc(text)}</text>')
        else:
            parts.append(f'<text x="{PAD_X + 16}" y="{y}" fill="{MUTED_COLOR}">{esc(text)}</text>')
        parts.append("</g>")
        y += LINE_H

    parts.append("</svg>")
    return "".join(parts)


def main():
    svg = build_svg()
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render contributions.json into a GitHub-style heatmap SVG that reveals
cell by cell, with a Less->More legend and real streak stats.
"""
import json
import os
import sys
from datetime import datetime, timedelta

IN = sys.argv[1] if len(sys.argv) > 1 else "contributions.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

CELL = 11
GAP = 3
RADIUS = 2
REVEAL_STEP_MS = 6
BG_COLOR = "#0d1117"
LEVEL_COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
TEXT_COLOR = "#c9d1d9"
MUTED_COLOR = "#8b949e"
MONTH_LABEL_H = 16
LEGEND_H = 20
STATS_H = 20
LEFT_PAD = 4


def load():
    with open(IN) as f:
        return json.load(f)


def level_for(day):
    lvl = day.get("level")
    if lvl is not None:
        return max(0, min(4, lvl))
    count = day.get("count") or 0
    if count == 0:
        return 0
    if count < 3:
        return 1
    if count < 6:
        return 2
    if count < 10:
        return 3
    return 4


def build_weeks(days):
    by_date = {d["date"]: d for d in days}
    dates = sorted(by_date)
    if not dates:
        return []
    start = datetime.strptime(dates[0], "%Y-%m-%d").date()
    start -= timedelta(days=(start.weekday() + 1) % 7)  # back up to Sunday
    end = datetime.strptime(dates[-1], "%Y-%m-%d").date()

    weeks, week = [], []
    cur = start
    while cur <= end:
        key = cur.isoformat()
        day = by_date.get(key)
        week.append({"date": key, "level": level_for(day) if day else -1})
        if cur.weekday() == 5:  # Saturday closes the week (starts Sunday)
            weeks.append(week)
            week = []
        cur += timedelta(days=1)
    if week:
        weeks.append(week)
    return weeks


def month_labels(weeks):
    labels, last_month = [], None
    for i, week in enumerate(weeks):
        first_valid = next((d for d in week if d["level"] >= 0), None)
        if not first_valid:
            continue
        month = first_valid["date"][:7]
        if month != last_month:
            labels.append((i, datetime.strptime(first_valid["date"], "%Y-%m-%d").strftime("%b")))
            last_month = month
    return labels


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;")


def build_svg(data):
    weeks = build_weeks(data["days"])
    stats = data.get("stats", {})
    cols = len(weeks)
    width = LEFT_PAD + cols * (CELL + GAP)
    grid_h = 7 * (CELL + GAP)
    height = MONTH_LABEL_H + grid_h + LEGEND_H + STATS_H

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="SFMono-Regular, Consolas, '
        f'\'Liberation Mono\', Menlo, monospace" font-size="10">',
        f'<rect width="100%" height="100%" fill="{BG_COLOR}"/>',
    ]

    if not STATIC:
        parts.append(
            "<style>.cell{opacity:0;animation:reveal .01s linear forwards;"
            f"animation-delay:calc(var(--i) * {REVEAL_STEP_MS}ms)}}"
            "@keyframes reveal{to{opacity:1}}</style>"
        )

    for i, label in month_labels(weeks):
        x = LEFT_PAD + i * (CELL + GAP)
        parts.append(f'<text x="{x}" y="{MONTH_LABEL_H - 4}" fill="{MUTED_COLOR}">{label}</text>')

    idx = 0
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            if day["level"] < 0:
                continue
            x = LEFT_PAD + wi * (CELL + GAP)
            y = MONTH_LABEL_H + di * (CELL + GAP)
            color = LEVEL_COLORS[day["level"]]
            cls = "" if STATIC else ' class="cell"'
            style = "" if STATIC else f' style="--i:{idx}"'
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RADIUS}" '
                f'fill="{color}"{cls}{style}><title>{esc(day["date"])}</title></rect>'
            )
            idx += 1

    legend_y = MONTH_LABEL_H + grid_h + 12
    parts.append(f'<text x="{LEFT_PAD}" y="{legend_y}" fill="{MUTED_COLOR}">Less</text>')
    lx = LEFT_PAD + 32
    for i, color in enumerate(LEVEL_COLORS):
        parts.append(
            f'<rect x="{lx + i * (CELL + GAP)}" y="{legend_y - CELL + 2}" '
            f'width="{CELL}" height="{CELL}" rx="{RADIUS}" fill="{color}"/>'
        )
    parts.append(
        f'<text x="{lx + len(LEVEL_COLORS) * (CELL + GAP) + 4}" y="{legend_y}" '
        f'fill="{MUTED_COLOR}">More</text>'
    )

    stats_y = legend_y + STATS_H
    stats_line = (
        f'{stats.get("total", 0)} contributions   '
        f'current streak {stats.get("current_streak", 0)}d   '
        f'longest streak {stats.get("longest_streak", 0)}d'
    )
    parts.append(f'<text x="{LEFT_PAD}" y="{stats_y}" fill="{TEXT_COLOR}">{esc(stats_line)}</text>')
    parts.append("</svg>")
    return "".join(parts), width, height


def main():
    data = load()
    svg, w, h = build_svg(data)
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT} ({w}x{h})")


if __name__ == "__main__":
    main()

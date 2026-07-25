#!/usr/bin/env python3
"""Scrape a public GitHub contribution calendar (no auth needed) into JSON."""
import json
import os
import re
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_PROFILE_USER", "").strip()
OUT = sys.argv[1] if len(sys.argv) > 1 else "contributions.json"
URL = f"https://github.com/users/{USERNAME}/contributions"

# GitHub no longer puts the count on the <td> itself -- it only shows up in
# the text of a linked <tool-tip for="...">N contributions on ...</tool-tip>.
COUNT_RE = re.compile(r"^(No|\d+)\s+contributions?", re.IGNORECASE)


def fetch_days():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tooltip_by_target = {
        tt.get("for"): tt.get_text(strip=True) for tt in soup.select("tool-tip[for]")
    }

    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date], td[data-date]"):
        date = cell.get("data-date")
        if not date:
            continue
        level = cell.get("data-level")
        count = None
        tip = tooltip_by_target.get(cell.get("id"))
        if tip:
            m = COUNT_RE.match(tip)
            if m:
                count = 0 if m.group(1).lower() == "no" else int(m.group(1))
        days.append({
            "date": date,
            "level": int(level) if level is not None else None,
            "count": count,
        })

    if not days:
        for rect in soup.select("rect[data-date]"):
            date = rect.get("data-date")
            if not date:
                continue
            days.append({
                "date": date,
                "level": int(rect.get("data-level", 0)),
                "count": None,
            })

    return sorted(days, key=lambda d: d["date"])


def compute_stats(days):
    counts = [(d["date"], d.get("count") or 0) for d in days]

    longest = running = 0
    for _, count in counts:
        if count > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0

    current = 0
    for _, count in reversed(counts):
        if count > 0:
            current += 1
        else:
            break

    return {
        "total": sum(c for _, c in counts),
        "longest_streak": longest,
        "current_streak": current,
    }


def main():
    if not USERNAME:
        print("set GH_PROFILE_USER env var", file=sys.stderr)
        sys.exit(1)

    days = fetch_days()
    if not days:
        print("no contribution data found (GitHub markup may have changed)", file=sys.stderr)
        sys.exit(1)

    stats = compute_stats(days)
    payload = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
    }

    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"wrote {OUT}: {len(days)} days, {stats}")


if __name__ == "__main__":
    main()

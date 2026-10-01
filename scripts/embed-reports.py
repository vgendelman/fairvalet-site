#!/usr/bin/env python3
"""Embed data/reports.json into reports/index.html so the live page shows stories without waiting on JS."""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "reports.json"
PAGE = ROOT / "reports" / "index.html"

# Legacy type keys may still exist on older reports.json rows; cards use title, not type.
REGULATION_LABELS = {
    "yes": "Yes",
    "no": "No",
    "unsure": "Unsure",
}


def format_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        # Keep short ISO date for static HTML (timezone-agnostic)
        return iso[:10]
    except Exception:
        return iso


def render_articles(reports: list) -> str:
    if not reports:
        return '<p class="note" id="reports-empty" style="margin:0">No published reports yet.</p>'
    parts = []
    for r in reports:
        when = format_date(r.get("submitted_at") or r.get("published_at") or "")
        who = escape(str(r.get("name") or "").strip())
        venue = escape(str(r.get("venue") or "").strip())
        location = escape(str(r.get("location") or "").strip())
        details = escape(str(r.get("details") or ""))
        title = escape(str(r.get("title") or "").strip())
        heading = title or "Report"
        place_bits = [b for b in (venue, location) if b]
        byline_bits = [b for b in (who, escape(when) if when else "") if b]
        reg_raw = str(r.get("want_regulation") or "").strip().lower()
        reg_label = REGULATION_LABELS.get(reg_raw) or (escape(reg_raw) if reg_raw else "")
        reg = (
            f'<span class="report-meta">Supports valet-spot regulation: {reg_label}</span>'
            if reg_label
            else ""
        )
        place = (
            f'<span class="report-meta">{" · ".join(place_bits)}</span>'
            if place_bits
            else ""
        )
        byline = (
            f'<span class="report-meta">{" · ".join(byline_bits)}</span>'
            if byline_bits
            else ""
        )
        parts.append(
            '<article class="story">'
            f"<strong>{heading}</strong>"
            f'<p class="report-details">{details}</p>'
            f"{place}"
            f"{reg}"
            f"{byline}"
            "</article>"
        )
    return "\n        ".join(parts)


def main() -> None:
    reports = []
    if DATA.exists():
        raw = json.loads(DATA.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            reports = raw
    html = PAGE.read_text(encoding="utf-8")
    articles = render_articles(reports)
    # Replace the stories container contents
    pattern = re.compile(
        r'(<div class="stories" id="community-reports">)(.*?)(</div>)',
        re.S,
    )
    new_html, n = pattern.subn(rf"\1\n        {articles}\n      \3", html, count=1)
    if n != 1:
        raise SystemExit("Could not find #community-reports container to embed into")
    PAGE.write_text(new_html, encoding="utf-8")
    print(f"Embedded {len(reports)} report(s) into {PAGE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

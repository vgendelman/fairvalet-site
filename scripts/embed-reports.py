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

TYPE_LABELS = {
    "front_spaces_reserved": "Best spots reserved for valet cars",
    "forced_or_pushed": "Felt forced into valet / little self-park choice",
    "cones_or_blocked": "Cones or barriers blocking ordinary parking",
    "parked_far_anyway": "Paid valet but car still parked far away",
    "good_example": "They do valet fairly",
    "other": "Something else",
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
        type_label = TYPE_LABELS.get(r.get("type") or "", r.get("type") or "Report")
        when = format_date(r.get("date_shared") or r.get("published_at") or r.get("submitted_at") or "")
        who = escape(str(r.get("name") or "").strip())
        venue = escape(str(r.get("venue") or "Venue"))
        location = escape(str(r.get("location") or ""))
        details = escape(str(r.get("details") or ""))
        title = escape(str(r.get("title") or "").strip())
        heading = title or venue
        meta_bits = []
        if who:
            meta_bits.append(who)
        if title and r.get("venue"):
            meta_bits.append(venue)
        if location:
            meta_bits.append(location)
        if type_label:
            meta_bits.append(escape(type_label))
        if when:
            meta_bits.append(escape(when))
        meta = " · ".join(meta_bits)
        parts.append(
            '<article class="story">'
            f"<strong>{heading}</strong>"
            f'<span class="report-meta">{meta}</span>'
            f'<p class="report-details">{details}</p>'
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

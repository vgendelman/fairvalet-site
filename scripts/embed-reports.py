#!/usr/bin/env python3
"""Embed data/reports.json into reports pages + sitemap.

- Assigns stable URL-safe slugs (persisted into reports.json).
- Writes /reports/<slug>/index.html for each published report.
- Embeds linked teasers into #community-reports on /reports/index.html.
- Regenerates sitemap.xml with static pages + every report URL.
"""
from __future__ import annotations

import json
import re
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "reports.json"
LIST_PAGE = ROOT / "reports" / "index.html"
SITEMAP = ROOT / "sitemap.xml"
REPORTS_DIR = ROOT / "reports"

REGULATION_LABELS = {
    "yes": "Yes",
    "no": "No",
    "unsure": "Unsure",
}

STATIC_SITEMAP_PATHS = [
    "/",
    "/reports/",
    "/contact/",
    "/what-is-fair-valet/",
    "/why-valets-cone-front-spots/",
    "/valet-vs-self-park/",
    "/valet-blocking-rules/",
    "/how-to-report/",
    "/policy-template/",
]

MENU_SCRIPT = """
  <script>
    const menuToggle = document.querySelector(".menu-toggle");
    const siteNav = document.getElementById("site-nav");
    if (menuToggle && siteNav) {
      menuToggle.addEventListener("click", () => {
        const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
        menuToggle.setAttribute("aria-expanded", String(!isOpen));
        siteNav.hidden = isOpen;
      });
      siteNav.addEventListener("click", (event) => {
        if (event.target.closest("a")) {
          menuToggle.setAttribute("aria-expanded", "false");
          siteNav.hidden = true;
        }
      });
    }
  </script>
"""

SHARED_CSS = """
    :root {
      --ink: #1a1f2e;
      --muted: #5c6578;
      --line: #e4e7ee;
      --bg: #fafbfc;
      --card: #ffffff;
      --accent: #0179d6;
      --accent-soft: #e8f3fc;
      --warn: #8a4b08;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "DM Sans", system-ui, sans-serif;
      color: var(--ink);
      background: var(--bg);
      line-height: 1.55;
      font-size: 1.05rem;
    }
    .wrap {
      max-width: 40rem;
      margin: 0 auto;
      padding: 1.25rem 1.25rem 4rem;
    }
    header { margin-bottom: 2.5rem; }
    .chrome {
      position: relative;
      display: flex;
      justify-content: flex-start;
      align-items: flex-start;
      margin: 0 0 1rem;
      min-height: 2.5rem;
      z-index: 30;
    }
    .mark {
      display: flex;
      justify-content: center;
      align-items: center;
      width: 100%;
      text-decoration: none;
      line-height: 0;
    }
    .mark img {
      display: block;
      width: min(100%, 18rem);
      height: auto;
    }
    h1 {
      font-size: clamp(1.75rem, 4.5vw, 2.25rem);
      line-height: 1.2;
      letter-spacing: -0.03em;
      margin: 1.25rem 0 0.75rem;
      font-weight: 700;
    }
    .lede {
      color: var(--muted);
      font-size: 1.1rem;
      margin: 0;
    }
    .menu-toggle {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.55rem;
      margin: 0;
      width: auto;
      min-width: 7rem;
      border: 1px solid var(--line);
      background: var(--card);
      color: var(--ink);
      font: inherit;
      font-size: 0.9rem;
      font-weight: 600;
      padding: 0.55rem 0.8rem;
      border-radius: 0.55rem;
      cursor: pointer;
    }
    .menu-toggle:hover { border-color: var(--accent); color: var(--accent); filter: none; }
    .menu-icon { display: grid; gap: 3px; }
    .menu-icon span { display: block; width: 1rem; height: 2px; background: currentColor; border-radius: 2px; }
    .site-nav {
      position: absolute;
      top: calc(100% + 0.4rem);
      left: 0;
      display: flex;
      flex-direction: column;
      align-items: stretch;
      gap: 0.2rem;
      width: min(18.5rem, calc(100vw - 2.5rem));
      margin: 0;
      padding: 0.75rem 0.9rem;
      border: 1px solid var(--line);
      border-radius: 0.75rem;
      background: var(--card);
      box-shadow: 0 10px 28px rgba(26, 31, 46, 0.1);
      z-index: 40;
    }
    .site-nav[hidden] { display: none; }
    .site-nav a {
      color: var(--accent);
      font-size: 0.95rem;
      font-weight: 600;
      text-decoration: none;
      padding: 0.3rem 0.15rem;
    }
    .site-nav a:hover { text-decoration: underline; }
    .nav-label {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-top: 0.45rem;
      padding-top: 0.55rem;
      border-top: 1px solid var(--line);
    }
    section {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 1rem;
      padding: 1.5rem 1.35rem;
      margin-bottom: 1.25rem;
    }
    h2 {
      font-size: 1.05rem;
      margin: 0 0 0.85rem;
      letter-spacing: -0.01em;
    }
    p { margin: 0 0 0.9rem; }
    p:last-child { margin-bottom: 0; }
    .note {
      font-size: 0.85rem;
      color: var(--muted);
      margin-top: 0.85rem;
    }
    .report-meta {
      color: var(--muted);
      font-size: 0.85rem;
      display: block;
      margin-top: 0.35rem;
    }
    .report-details { margin: 0.45rem 0 0; font-size: 0.95rem; }
    .back-link {
      display: inline-block;
      margin-bottom: 1rem;
      font-weight: 600;
      color: var(--accent);
      text-decoration: none;
    }
    .back-link:hover { text-decoration: underline; }
    .story a.story-title { color: var(--ink); text-decoration: none; }
    .story a.story-title:hover { color: var(--accent); text-decoration: underline; }
    .read-more {
      display: inline-block;
      margin-top: 0.55rem;
      font-size: 0.9rem;
      font-weight: 600;
      color: var(--accent);
      text-decoration: none;
    }
    .read-more:hover { text-decoration: underline; }
    footer {
      margin-top: 2rem;
      color: var(--muted);
      font-size: 0.85rem;
      text-align: center;
    }
    a { color: var(--accent); }
"""


def format_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        return iso[:10]
    except Exception:
        return iso


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower().strip())
    s = s.strip("-")
    return (s[:80].rstrip("-") if s else "") or "report"


def ensure_slugs(reports: list) -> None:
    used: set[str] = set()
    for r in reports:
        existing = str(r.get("slug") or "").strip()
        if existing and existing not in used:
            used.add(existing)
            r["slug"] = existing
            continue
        title = str(r.get("title") or "").strip() or "report"
        venue = str(r.get("venue") or "").strip()
        base = slugify(f"{title} {venue}".strip() if venue else title)
        slug = base
        n = 2
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        r["slug"] = slug
        used.add(slug)


def truncate(text: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0]
    return (cut or text[: limit - 1]).rstrip(".,;:") + "…"


def nav_html(report_href: str = "/#report") -> str:
    return f"""      <div class="chrome">
        <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-nav">
          Menu <span class="menu-icon" aria-hidden="true"><span></span><span></span><span></span></span>
        </button>
        <nav class="site-nav" id="site-nav" aria-label="Main navigation" hidden>
          <a href="/">Home</a>
          <a href="/reports/">Reports</a>
          <a href="/contact/">Contact</a>
          <a href="{escape(report_href)}">Report an experience</a>
          <span class="nav-label">Explainers</span>
          <a href="/what-is-fair-valet/">What is fair valet</a>
          <a href="/why-valets-cone-front-spots/">Why valets cone spots</a>
          <a href="/valet-vs-self-park/">Valet vs self-park</a>
          <a href="/valet-blocking-rules/">Blocking rules</a>
          <a href="/how-to-report/">How to report</a>
          <a href="/policy-template/">Policy template</a>
        </nav>
      </div>"""


def meta_block(title: str, description: str, canonical: str) -> str:
    t = escape(title)
    d = escape(description)
    c = escape(canonical)
    return f"""  <title>{t}</title>
  <meta name="description" content="{d}" />
  <link rel="canonical" href="{c}" />
  <meta property="og:type" content="article" />
  <meta property="og:title" content="{t}" />
  <meta property="og:description" content="{d}" />
  <meta property="og:url" content="{c}" />
  <meta property="og:site_name" content="FairValet" />
  <meta property="og:image" content="https://fairvalet.org/assets/fairvalet-logo.png" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{t}" />
  <meta name="twitter:description" content="{d}" />
  <meta name="twitter:image" content="https://fairvalet.org/assets/fairvalet-logo.png" />
  <link rel="icon" href="../../assets/favicon.ico" sizes="any" />
  <link rel="icon" href="../../assets/favicon.png" type="image/png" sizes="32x32" />
  <link rel="icon" href="../../assets/favicon-32.png" type="image/png" sizes="32x32" />
  <link rel="icon" href="../../assets/favicon-16.png" type="image/png" sizes="16x16" />
  <link rel="apple-touch-icon" href="../../assets/apple-touch-icon.png" sizes="180x180" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap" rel="stylesheet" />
"""


def render_list_articles(reports: list) -> str:
    if not reports:
        return '<p class="note" id="reports-empty" style="margin:0">No published reports yet.</p>'
    parts = []
    for r in reports:
        slug = escape(str(r.get("slug") or ""))
        href = f"/reports/{slug}/"
        when = format_date(r.get("submitted_at") or r.get("published_at") or "")
        who = escape(str(r.get("name") or "").strip())
        venue = escape(str(r.get("venue") or "").strip())
        location = escape(str(r.get("location") or "").strip())
        teaser = escape(truncate(str(r.get("details") or "")))
        title = escape(str(r.get("title") or "").strip() or "Report")
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
            f'<strong><a class="story-title" href="{href}">{title}</a></strong>'
            f'<p class="report-details">{teaser}</p>'
            f"{place}"
            f"{reg}"
            f"{byline}"
            f'<a class="read-more" href="{href}">Read full report →</a>'
            "</article>"
        )
    return "\n        ".join(parts)


def write_detail_page(r: dict) -> Path:
    slug = str(r["slug"])
    title_raw = str(r.get("title") or "").strip() or "Report"
    venue = str(r.get("venue") or "").strip()
    location = str(r.get("location") or "").strip()
    details = str(r.get("details") or "")
    who = str(r.get("name") or "").strip()
    when = format_date(r.get("submitted_at") or r.get("published_at") or "")
    reg_raw = str(r.get("want_regulation") or "").strip().lower()
    reg_label = REGULATION_LABELS.get(reg_raw) or (reg_raw if reg_raw else "")

    place_bits = [b for b in (venue, location) if b]
    place_str = " · ".join(place_bits)

    page_title = f"{title_raw} at {venue} — FairValet" if venue else f"{title_raw} — FairValet report"
    desc_bits = [b for b in (venue, location, when) if b]
    meta_desc = (
        f"Community report: {title_raw}. "
        + (" · ".join(desc_bits) + ". " if desc_bits else "")
        + truncate(details, 120)
    )
    canonical = f"https://fairvalet.org/reports/{slug}/"

    place_html = f'<span class="report-meta">{escape(place_str)}</span>' if place_str else ""
    reg_html = (
        f'<span class="report-meta">Supports valet-spot regulation: {escape(reg_label)}</span>'
        if reg_label
        else ""
    )
    byline_bits = [escape(who)] if who else []
    if when:
        byline_bits.append(escape(when))
    byline_html = (
        f'<span class="report-meta">{" · ".join(byline_bits)}</span>' if byline_bits else ""
    )

    fact_lines = []
    if venue:
        fact_lines.append(f"<strong>Venue:</strong> {escape(venue)}")
    if location:
        fact_lines.append(f"<strong>Location:</strong> {escape(location)}")
    if when:
        fact_lines.append(f"<strong>Date:</strong> {escape(when)}")
    facts = (
        '<p class="lede" style="margin-top:0.75rem">' + "<br />".join(fact_lines) + "</p>"
        if fact_lines
        else ""
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
{meta_block(page_title, meta_desc, canonical)}  <style>
{SHARED_CSS}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
{nav_html()}
      <a class="mark" href="/" aria-label="FairValet home">
        <img src="../../assets/fairvalet-logo.png" width="288" height="288" alt="FairValet — Valet should save you a walk, not make everyone else walk farther." />
      </a>
    </header>

    <p><a class="back-link" href="/reports/">← All reports</a></p>

    <section>
      <h1>{escape(title_raw)}</h1>
      {facts}
      <p class="report-details" style="margin-top:1rem">{escape(details)}</p>
      {place_html}
      {reg_html}
      {byline_html}
      <p class="note" style="margin-top:1.1rem">Published community report. Email addresses are never shown. Business names appear only after review.</p>
    </section>

    <section>
      <h2>Seen something similar?</h2>
      <p><a href="/#report">Report an experience</a> · <a href="/how-to-report/">How to report</a> · <a href="/what-is-fair-valet/">What is fair valet</a></p>
    </section>

    <footer>
      FairValet · Consumer movement for fair parking
    </footer>
  </div>
{MENU_SCRIPT}
</body>
</html>
"""
    out_dir = REPORTS_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


def write_sitemap(reports: list, lastmod: str) -> None:
    urls = list(STATIC_SITEMAP_PATHS)
    for r in reports:
        slug = str(r.get("slug") or "").strip()
        if slug:
            urls.append(f"/reports/{slug}/")
    seen: set[str] = set()
    ordered: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path in ordered:
        parts.append("  <url>")
        parts.append(f"    <loc>https://fairvalet.org{path}</loc>")
        parts.append(f"    <lastmod>{lastmod}</lastmod>")
        parts.append("  </url>")
    parts.append("</urlset>")
    parts.append("")
    SITEMAP.write_text("\n".join(parts), encoding="utf-8")


def embed_list_page(reports: list) -> None:
    html = LIST_PAGE.read_text(encoding="utf-8")
    articles = render_list_articles(reports)
    pattern = re.compile(
        r'(<div class="stories" id="community-reports">)(.*?)(</div>)',
        re.S,
    )
    new_html, n = pattern.subn("\\1\n        " + articles + "\n      \\3", html, count=1)
    if n != 1:
        raise SystemExit("Could not find #community-reports container to embed into")
    LIST_PAGE.write_text(new_html, encoding="utf-8")


def main() -> None:
    reports: list = []
    if DATA.exists():
        raw = json.loads(DATA.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            reports = raw

    ensure_slugs(reports)
    DATA.write_text(json.dumps(reports, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    written = []
    for r in reports:
        written.append(write_detail_page(r))

    known = {str(r["slug"]) for r in reports}
    if REPORTS_DIR.exists():
        for child in REPORTS_DIR.iterdir():
            if child.is_dir() and child.name not in known:
                idx = child / "index.html"
                if idx.exists():
                    idx.unlink()
                    try:
                        child.rmdir()
                    except OSError:
                        pass

    embed_list_page(reports)
    lastmod = date.today().isoformat()
    write_sitemap(reports, lastmod)

    print(f"Embedded {len(reports)} report(s) into {LIST_PAGE.relative_to(ROOT)}")
    for p in written:
        print(f"  wrote {p.relative_to(ROOT)}")
    print(f"Updated {SITEMAP.relative_to(ROOT)} (lastmod={lastmod})")


if __name__ == "__main__":
    main()

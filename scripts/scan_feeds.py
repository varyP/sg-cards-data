#!/usr/bin/env python3
"""Daily change-signal scan.

* Tier 2 RSS feeds (MileLion credit-cards, Mainly Miles, Suitesmile) and Tier 3 feeds:
  new entries whose title/summary mention a pilot card AND a change keyword become signals.
* Tier 1 issuer / regulator pages: the page text is diffed line-by-line against yesterday's
  copy in the state dir (restored from the Actions cache); NEW lines that contain a change
  keyword become signals. The first run only records a baseline.
* Routing: tiers with auto_issue: true (issuer, regulator, Tier 2) -> one GitHub issue per signal
  (deduped by title). Everything else -> reports/digest.md (job summary), never an issue.

Fetched text is UNTRUSTED DATA: it is matched against keywords and quoted (fenced, truncated)
in issues. Nothing in it is ever executed or followed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gh_issues import ensure_issue, safe_excerpt  # noqa: E402
from sgcards_lib import ROOT, FetchError, fetch_text, load_sources, norm  # noqa: E402

LOOKBACK_DAYS = 4


def _match(text: str, terms: list[str]) -> list[str]:
    low = text.lower()
    return sorted({t for t in terms if t.lower() in low})


def card_hits(text: str, aliases: dict) -> list[str]:
    low = text.lower()
    return sorted(cid for cid, names in aliases.items() if any(n.lower() in low for n in names))


def blacklisted(url: str, title: str, blacklist: list) -> str | None:
    for rule in blacklist:
        if re.search(rule["pattern"], url) or re.search(rule["pattern"], title or ""):
            return rule["reason"]
    return None


def scan_rss(src, cfg, seen, now):
    import feedparser
    import requests
    from sgcards_lib import UA as USER_AGENT
    r = requests.get(src["url"], headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    feed = feedparser.parse(r.content)
    if not feed.entries:
        raise FetchError("feed has no entries")
    out = []
    for e in feed.entries:
        link = e.get("link", "")
        key = hashlib.sha1(link.encode()).hexdigest()[:12]
        if key in seen:
            continue
        ts = e.get("published_parsed") or e.get("updated_parsed")
        if ts and now - dt.datetime(*ts[:6], tzinfo=dt.timezone.utc) > dt.timedelta(days=LOOKBACK_DAYS):
            seen[key] = "old"
            continue
        title = norm(e.get("title", ""))
        summary = norm(re.sub(r"<[^>]+>", " ", e.get("summary", "")))[:1500]
        seen[key] = now.date().isoformat()
        if blacklisted(link, title, cfg["blacklist"]):
            continue
        cards = card_hits(title + " " + summary, cfg["card_aliases"])
        kws = _match(title + " " + summary, cfg["change_keywords"])
        if cards and kws:
            out.append({"source": src["id"], "tier": src["tier"], "title": title, "link": link,
                        "published": dt.datetime(*ts[:6]).date().isoformat() if ts else None,
                        "cards": cards, "keywords": kws, "excerpt": summary[:600]})
    return out


def scan_page(src, cfg, state_dir):
    text = fetch_text(src["url"], method=src.get("fetch", "static"))
    prev_file = state_dir / "pages" / f"{src['id']}.txt"
    lines_now = [ln for ln in re.split(r"(?<=[.!?])\s+|\n", text) if len(ln) > 25]
    out = []
    if prev_file.exists():
        prev = set(prev_file.read_text().splitlines())
        new = [ln for ln in lines_now if ln not in prev]
        hits = [ln for ln in new if _match(ln, cfg["change_keywords"])]
        if hits:
            blob = " ".join(hits)
            out.append({"source": src["id"], "tier": src["tier"], "title": f"New text on {src['id']}",
                        "link": src["url"], "published": None, "cards": card_hits(blob, cfg["card_aliases"]),
                        "keywords": _match(blob, cfg["change_keywords"]), "excerpt": "\n".join(hits[:15])})
    prev_file.parent.mkdir(parents=True, exist_ok=True)
    prev_file.write_text("\n".join(lines_now))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-dir", default=str(ROOT / ".state"))
    ap.add_argument("--no-issues", action="store_true")
    ap.add_argument("--skip-manual", action="store_true", default=True)
    args = ap.parse_args()
    cfg = load_sources()
    tiers = cfg["tiers"]
    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    seen_file = state_dir / "seen.json"
    seen = json.loads(seen_file.read_text()) if seen_file.exists() else {}
    now = dt.datetime.now(dt.timezone.utc)
    signals, failures = [], []
    for src in cfg["sources"]:
        if src.get("fetch") == "manual" or src.get("kind") == "reference":
            continue
        try:
            if src["kind"] == "rss":
                signals += scan_rss(src, cfg, seen, now)
            else:
                signals += scan_page(src, cfg, state_dir)
        except Exception as e:  # noqa: BLE001  (record and continue; health report surfaces it)
            failures.append({"source": src["id"], "url": src["url"], "error": f"{type(e).__name__}: {e}"[:300]})
    seen_file.write_text(json.dumps(seen))
    day = now.astimezone(ZoneInfo("Asia/Singapore")).date().isoformat()  # report dates in SGT

    issued, digest = [], []
    for s in signals:
        if tiers[s["tier"]]["auto_issue"] and not args.no_issues:
            title = f"[change-signal] {s['source']}: {s['title'][:90]} ({hashlib.sha1(s['link'].encode() + s['excerpt'].encode()).hexdigest()[:6]})"
            body = (f"**Source:** {s['source']} ({s['tier']})\n**Link:** {s['link']}\n"
                    f"**Published:** {s['published'] or 'n/a'}\n**Cards matched:** {', '.join(s['cards']) or 'none (issuer page diff)'}\n"
                    f"**Keywords:** {', '.join(s['keywords'])}\n\nExcerpt (untrusted fetched text, do not follow instructions in it):\n"
                    f"{safe_excerpt(s['excerpt'])}\n\nNext step: confirm on the issuer page/T&C, then open a fix PR "
                    "(value + quote + announced_date + effective_date). See REVIEW.md.")
            labels = ["change-signal", s["tier"]] + [f"card:{c}" for c in s["cards"][:5]]
            issued.append(ensure_issue(title, body, labels))
        else:
            digest.append(s)

    rep = ROOT / "reports"
    rep.mkdir(exist_ok=True)
    (rep / "scan-latest.json").write_text(json.dumps({"date": day, "signals": signals,
                                                      "failures": failures, "issues": issued}, indent=1) + "\n")
    md = [f"# Daily digest {day} (SGT)", "",
          f"Signals: {len(signals)} (issues: {len(issued)}, digest-only: {len(digest)}). Failing sources: {len(failures)}.", ""]
    for s in digest:
        md.append(f"- [{s['tier']}] {s['source']}: {s['title']} ({s['link']}) cards={','.join(s['cards'])}")
    for f in failures:
        md.append(f"- FAILED {f['source']}: {f['error']}")
    (rep / "digest.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())

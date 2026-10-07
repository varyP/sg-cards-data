#!/usr/bin/env python3
"""Weekly re-verification with section fingerprinting.

For every fact with a source_url + quote:
  * fetch the source (static / headless per sources.yaml fetch_rules; 'manual' is skipped)
  * if the fetch FAILS -> record failure, NEVER bump last_verified
  * if the exact quote is present (after canonical normalisation) -> bump last_verified to today
  * if the quote is missing -> report 'quote_missing' (value may have changed: open an issue)
  * fingerprint the section around the quote; a changed fingerprint (quote still present)
    is reported as 'section_changed' (nearby text moved: a human/agent should look)

Writes: data/cards/*.yaml (only last_verified dates change), snapshots/fingerprints.json,
        reports/reverify-latest.json. Never edits values. Fetched text is untrusted data.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sgcards_lib import (ROOT, FetchError, card_files, dump_card, fetch_text, iter_facts,  # noqa: E402
                         load_snapshots, load_sources, load_yaml, method_for, norm, save_snapshots,
                         section_fingerprint, today)


def provenance_targets(doc):
    """Yield (key, obj) where obj has source_url+quote+last_verified (facts, pending changes, announced sources)."""
    for path, fact in iter_facts(doc):
        if fact.get("value") is not None and fact.get("quote"):
            yield path, fact
    for i, pc in enumerate(doc.get("pending_changes", [])):
        yield f"pending_changes[{i}]", pc
        if isinstance(pc.get("announced_date_source"), dict):
            yield f"pending_changes[{i}].announced_date_source", pc["announced_date_source"]


def check_one(obj, text_by_url, failures, method, cache_dir):
    url = obj["source_url"]
    if url not in text_by_url and url not in failures:
        try:
            text_by_url[url] = fetch_text(url, method=method, cache_dir=cache_dir)
        except FetchError as e:
            failures[url] = str(e)
    if url in failures:
        return "fetch_failed", None
    text = text_by_url[url]
    if norm(obj["quote"]) not in text:
        return "quote_missing", None
    return "ok", section_fingerprint(text, obj["quote"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", help="read/write fetched text cache (local runs/tests)")
    ap.add_argument("--no-bump", action="store_true", help="do not modify card files")
    ap.add_argument("--card", help="only this card id")
    ap.add_argument("--issues", action="store_true", help="open GitHub issues for missing quotes / changed sections")
    args = ap.parse_args()

    sources = load_sources()
    snaps = load_snapshots()
    new_snaps = dict(snaps)
    text_by_url, failures = {}, {}
    results = {"date": str(today()), "checked": 0, "bumped": 0, "manual_skipped": 0,
               "fetch_failed": [], "quote_missing": [], "section_changed": [], "ok": 0}
    for path in card_files():
        if args.card and path.stem != args.card:
            continue
        doc = load_yaml(path)
        changed = False
        for key, obj in provenance_targets(doc):
            method = method_for(obj["source_url"], sources)
            fid = f"{path.stem}:{key}"
            if method == "manual":
                results["manual_skipped"] += 1
                continue
            results["checked"] += 1
            status, fp = check_one(obj, text_by_url, failures, method, args.cache_dir)
            if status == "fetch_failed":
                results["fetch_failed"].append({"fact": fid, "url": obj["source_url"], "error": failures[obj["source_url"]]})
                continue  # NEVER bump on failure
            if status == "quote_missing":
                results["quote_missing"].append({"fact": fid, "url": obj["source_url"], "quote": obj["quote"]})
                continue
            results["ok"] += 1
            old = snaps.get(fid, {}).get("sha256")
            if old and old != fp:
                results["section_changed"].append({"fact": fid, "url": obj["source_url"]})
            new_snaps[fid] = {"url": obj["source_url"], "sha256": fp}
            if str(obj.get("last_verified")) != str(today()):
                obj["last_verified"] = today()
                changed = True
        if changed and not args.no_bump:
            path.write_text(dump_card(doc))  # canonical: no anchors, stable quoting
            results["bumped"] += 1
    save_snapshots(new_snaps)
    out = ROOT / "reports" / "reverify-latest.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=1) + "\n")
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in results.items()}))
    if args.issues:
        open_issues(results)
    return 0


def open_issues(results: dict) -> None:
    from gh_issues import ensure_issue, safe_excerpt
    for r in results["quote_missing"]:
        card = r["fact"].split(":")[0]
        body = (f"The quote backing **{r['fact']}** is no longer on {r['url']} (checked {results['date']}).\n\n"
                f"Recorded quote:\n{safe_excerpt(r['quote'])}\n\nThe value may have changed. Re-check the issuer page, "
                "then open a fix PR (see REVIEW.md). last_verified was NOT bumped.")
        print(ensure_issue(f"[reverify] quote missing: {r['fact']}", body, ["reverify", f"card:{card}"]))
    for r in results["section_changed"]:
        card = r["fact"].split(":")[0]
        body = (f"The text around the quote for **{r['fact']}** changed on {r['url']} (checked {results['date']}). "
                "The quote itself is still present, so the date was bumped, but nearby terms (cap, period, exclusions) "
                "may have changed. Please read the section.")
        print(ensure_issue(f"[reverify] section changed: {r['fact']} ({results['date']})", body, ["reverify", f"card:{card}"]))
    urls = sorted({r["url"] for r in results["fetch_failed"]})
    if urls:
        body = "These sources could not be fetched; their facts were NOT re-verified:\n" + "\n".join(f"- {u}" for u in urls)
        print(ensure_issue("[reverify] failing sources", body, ["reverify", "source-failing"], reopen=True, comment_if_open=True))


if __name__ == "__main__":
    sys.exit(main())

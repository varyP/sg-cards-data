#!/usr/bin/env python3
"""Validate data/cards/*.yaml.

FAILS (exit 1) on:
  * schema violations (schema/card.schema.json)
  * any number that is not inside an object carrying source_url + quote + last_verified
  * a pending change whose effective_date has passed (apply it via a reviewed PR)
  * last_verified in the future
WARNS on:
  * facts older than 30 days (warn) / 60 days (stale: bot must not state as current)
  * numeric value not visible in its own quote (unless derived: true)
  * third_party-only numeric facts, expired promos (effective_to passed)
Usage: python scripts/validate.py [--json] [--today YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sgcards_lib import ROOT, as_date, card_files, iter_facts, load_yaml, today  # noqa: E402

import jsonschema  # noqa: E402

WARN_DAYS, STALE_DAYS = 30, 60
EXEMPT_NUMERIC_KEYS = {"schema_version"}


def jsonable(o):
    if isinstance(o, dict):
        return {k: jsonable(v) for k, v in o.items()}
    if isinstance(o, list):
        return [jsonable(v) for v in o]
    if isinstance(o, (dt.date, dt.datetime)):
        return o.isoformat()
    return o


def numeric_leaves(node, path=""):
    """Yield (path, key, parent_dict) for every int/float leaf."""
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{path}.{k}" if path else str(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                yield p, k, node
            elif isinstance(v, (dict, list)):
                yield from numeric_leaves(v, p)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                yield f"{path}[{i}]", None, None
            else:
                yield from numeric_leaves(v, f"{path}[{i}]")


def number_variants(v: float) -> list[str]:
    out = {str(v)}
    if float(v).is_integer():
        i = int(v)
        out |= {str(i), f"{i:,}"}
    else:
        out |= {f"{v:.2f}", f"{v:,.2f}", f"{v:g}"}
    return list(out)


def value_in_quote(v, quote: str) -> bool:
    q = quote.replace("S$", " ").replace("SGD", " ")
    return any(re.search(rf"(?<![\d.]){re.escape(s)}(?![\d])", q) for s in number_variants(v))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--today", help="override today's date (testing)")
    ap.add_argument("--cards-dir", help="validate cards in another directory (testing)")
    args = ap.parse_args()
    now = dt.date.fromisoformat(args.today) if args.today else today()

    schema = json.loads((ROOT / "schema" / "card.schema.json").read_text())
    validator = jsonschema.Draft202012Validator(schema)
    errors, warnings = [], []
    stats = {"cards": 0, "facts": 0, "verified": 0, "null": 0, "issuer": 0, "third_party": 0,
             "fresh": 0, "warn_30d": 0, "stale_60d": 0, "pending_changes": 0}
    aging, pending = [], []
    ids = set()

    for path in card_files(args.cards_dir):
        doc = load_yaml(path)
        cid = path.stem
        stats["cards"] += 1
        if doc.get("id") != cid:
            errors.append(f"{cid}: id '{doc.get('id')}' must match filename")
        if cid in ids:
            errors.append(f"{cid}: duplicate id")
        ids.add(cid)
        for err in validator.iter_errors(jsonable(doc)):
            loc = "/".join(str(p) for p in err.absolute_path)
            errors.append(f"{cid}: schema: {loc}: {err.message[:200]}")

        # 1) every number needs provenance in the same object
        for p, key, parent in numeric_leaves(doc):
            if key in EXEMPT_NUMERIC_KEYS:
                continue
            if parent is None or not all(parent.get(k) for k in ("source_url", "quote", "last_verified")):
                errors.append(f"{cid}: {p}: number without source_url+quote+last_verified")

        # 2) per-fact checks
        for fpath, fact in iter_facts(doc):
            stats["facts"] += 1
            if fact.get("value") is None:
                stats["null"] += 1
                continue
            stats["verified"] += 1
            stats[fact.get("source_type", "issuer")] = stats.get(fact.get("source_type", "issuer"), 0) + 1
            lv = as_date(fact.get("last_verified"))
            if lv is None:
                errors.append(f"{cid}: {fpath}: missing last_verified")
                continue
            age = (now - lv).days
            if age < 0:
                errors.append(f"{cid}: {fpath}: last_verified {lv} is in the future")
            elif age > STALE_DAYS:
                stats["stale_60d"] += 1
                aging.append({"card": cid, "fact": fpath, "age_days": age, "level": "stale"})
            elif age > WARN_DAYS:
                stats["warn_30d"] += 1
                aging.append({"card": cid, "fact": fpath, "age_days": age, "level": "warn"})
            else:
                stats["fresh"] += 1
            v = fact.get("value")
            if isinstance(v, (int, float)) and not isinstance(v, bool) and not fact.get("derived"):
                if not value_in_quote(v, fact.get("quote", "")):
                    warnings.append(f"{cid}: {fpath}: value {v} not visible in quote (check, or mark derived: true with a note)")
                if fact.get("source_type") == "third_party":
                    warnings.append(f"{cid}: {fpath}: number backed only by a third_party source (label 'unconfirmed' in answers)")
            et = as_date(fact.get("effective_to"))
            if et and et < now:
                warnings.append(f"{cid}: {fpath}: promo expired on {et}; remove or update via PR")

        # 3) pending changes
        for pc in doc.get("pending_changes", []):
            stats["pending_changes"] += 1
            eff = as_date(pc.get("effective_date"))
            pending.append({"card": cid, "field": pc.get("field"), "old": pc.get("old_value"), "new": pc.get("new_value"),
                            "effective_date": str(eff), "days_until": (eff - now).days if eff else None})
            if eff and eff <= now:
                errors.append(f"{cid}: pending change on {pc.get('field')} took effect {eff}: open a PR that applies new_value and removes the pending entry")

    verified = stats["verified"] or 1
    stats["pct_issuer_verified_fresh"] = round(100 * min(stats["fresh"], stats["issuer"]) / max(stats["facts"], 1), 1)
    result = {"date": str(now), "ok": not errors, "stats": stats, "errors": errors, "warnings": warnings,
              "aging": aging, "pending": sorted(pending, key=lambda x: x["effective_date"])}
    if args.json:
        print(json.dumps(result, indent=1, default=str))
    else:
        print(f"Validated {stats['cards']} cards, {stats['facts']} facts: {stats['verified']} verified "
              f"({stats['issuer']} issuer, {stats['third_party']} third_party), {stats['null']} null.")
        print(f"Freshness: {stats['fresh']} fresh, {stats['warn_30d']} >30d (warn), {stats['stale_60d']} >60d (stale).")
        for a in aging:
            print(f"  {a['level'].upper():5} {a['card']}: {a['fact']} ({a['age_days']}d)")
        print(f"Pending changes: {stats['pending_changes']}")
        for p in result["pending"]:
            print(f"  {p['effective_date']} ({p['days_until']}d) {p['card']}: {p['field']} {p['old']} -> {p['new']}")
        for w in warnings:
            print(f"WARN  {w}")
        for e in errors:
            print(f"ERROR {e}")
        print("RESULT:", "PASS" if not errors else f"FAIL ({len(errors)} errors)")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())

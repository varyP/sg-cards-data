#!/usr/bin/env python3
"""Weekly health report: is the data still trustworthy, and is anyone reviewing?

Reports: % issuer-verified-and-fresh, stale/aging facts, manual-check queue, pending changes
(especially those taking effect within 14 days), failing sources (from reverify-latest.json),
the canary result, and review backlog. SHOUTS (opens/updates an issue + ::error annotation)
when a PR or change-signal issue has waited more than 7 days for review, when facts are
stale, when sources fail, or when the canary fails.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canary  # noqa: E402
from gh_issues import ensure_issue  # noqa: E402
from sgcards_lib import ROOT, card_files, iter_facts, load_sources, load_yaml, method_for, today  # noqa: E402

BACKLOG_DAYS = 7


def gh_json(args):
    if not (shutil.which("gh") and (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))):
        return None
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else None


def age_days(iso: str) -> int:
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (dt.datetime.now(dt.timezone.utc) - t).days


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-issues", action="store_true")
    args = ap.parse_args()
    v = json.loads(subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py"), "--json"],
                                  capture_output=True, text=True).stdout)
    st = v["stats"]
    sources = load_sources()
    manual = sorted({f["source_url"] for p in card_files() for _, f in iter_facts(load_yaml(p))
                     if f.get("value") is not None and method_for(f["source_url"], sources) == "manual"})
    rv_file = ROOT / "reports" / "reverify-latest.json"
    rv = json.loads(rv_file.read_text()) if rv_file.exists() else None
    failing = sorted({f["url"] for f in (rv or {}).get("fetch_failed", [])})
    canary_problems = canary.run()

    prs = gh_json(["pr", "list", "--state", "open", "--json", "number,title,createdAt,url,isDraft"]) or []
    sig = gh_json(["issue", "list", "--state", "open", "--label", "change-signal", "--limit", "200",
                   "--json", "number,title,createdAt,url"]) or []
    old_prs = [p for p in prs if not p.get("isDraft") and age_days(p["createdAt"]) > BACKLOG_DAYS]
    old_sig = [i for i in sig if age_days(i["createdAt"]) > BACKLOG_DAYS]

    soon = [p for p in v["pending"] if p["days_until"] <= 14]
    L = [f"# Health report {today()} (SGT)", "",
         f"- Cards: {st['cards']}; facts: {st['facts']} ({st['verified']} verified, {st['null']} null with reason)",
         f"- Issuer-verified & fresh (<=30d): **{st['fresh']}/{st['verified']}** verified facts; "
         f"aging 30-60d: {st['warn_30d']}; stale >60d: **{st['stale_60d']}**",
         f"- Third-party-only numbers: {st['third_party']}",
         f"- Validator: {'PASS' if v['ok'] else 'FAIL'} ({len(v['errors'])} errors, {len(v['warnings'])} warnings)",
         f"- Pending changes: {len(v['pending'])}; taking effect within 14 days: {len(soon)}",
         f"- Manual-check sources (bot-walled or robots-disallowed; an agent must re-check by hand): {len(manual)}",
         f"- Last re-verify: {rv['date'] if rv else 'none'}; checked {rv['checked'] if rv else 0}, "
         f"quote missing {len(rv['quote_missing']) if rv else 0}, section changed {len(rv['section_changed']) if rv else 0}, "
         f"failing URLs {len(failing)}",
         f"- Canary: {'OK' if not canary_problems else 'FAILED: ' + '; '.join(canary_problems)}",
         f"- Open PRs: {len(prs)} (waiting >{BACKLOG_DAYS}d: **{len(old_prs)}**); open change-signal issues: {len(sig)} "
         f"(>{BACKLOG_DAYS}d: **{len(old_sig)}**)", ""]
    if soon:
        L += ["## Taking effect soon"] + [f"- {p['effective_date']} {p['card']} {p['field']}: {p['old']} -> {p['new']}" for p in soon] + [""]
    if v["aging"]:
        L += ["## Aging / stale facts"] + [f"- {a}" for a in v["aging"][:60]] + [""]
    if failing:
        L += ["## Failing sources"] + [f"- {u}" for u in failing] + [""]
    if manual:
        L += ["## Manual-check queue"] + [f"- {u}" for u in manual] + [""]
    if old_prs or old_sig:
        L += [f"## 🚨 REVIEW BACKLOG: waiting more than {BACKLOG_DAYS} days"]
        L += [f"- PR #{p['number']} ({age_days(p['createdAt'])}d): {p['title']} {p['url']}" for p in old_prs]
        L += [f"- Issue #{i['number']} ({age_days(i['createdAt'])}d): {i['title']} {i['url']}" for i in old_sig] + [""]
    report = "\n".join(L) + "\n"
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "health.md").write_text(report)
    print(report)

    attention = bool(old_prs or old_sig or st["stale_60d"] or failing or canary_problems or not v["ok"])
    if old_prs or old_sig:
        print(f"::error title=Review backlog::{len(old_prs)} PR(s) and {len(old_sig)} change-signal issue(s) waiting > {BACKLOG_DAYS} days")
    if attention and not args.no_issues:
        print(ensure_issue("[health] attention needed", report, ["health"], reopen=True, comment_if_open=True))
    return 1 if canary_problems or not v["ok"] else 0


if __name__ == "__main__":
    sys.exit(main())

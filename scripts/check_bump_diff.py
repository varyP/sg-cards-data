#!/usr/bin/env python3
"""Guard for the weekly re-verify PR: card files may differ from a git ref ONLY in last_verified.

Compares every data/cards/*.yaml in the working tree with the same file at --base (default HEAD):
  * parsed content must be identical once every `last_verified` is ignored (no value, quote,
    source or structure change; no added or removed cards);
  * a last_verified may only move forward, and never past today (SGT);
  * with --strict-text, the text diff may only touch `last_verified:` lines (catches re-quoting,
    renamed anchors and other re-dump noise).
Exit 0 if clean, 1 otherwise. Prints a one-line summary suitable for a PR body.
"""
from __future__ import annotations

import argparse
import difflib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml  # noqa: E402

from sgcards_lib import ROOT, as_date, card_files, today  # noqa: E402


def _strip(node, dates, path=""):
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k == "last_verified":
                dates[path] = as_date(v)
                continue
            out[k] = _strip(v, dates, f"{path}.{k}")
        return out
    if isinstance(node, list):
        return [_strip(v, dates, f"{path}[{i}]") for i, v in enumerate(node)]
    return node


def _git_show(ref: str, rel: str) -> str | None:
    r = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="HEAD")
    ap.add_argument("--strict-text", action="store_true")
    args = ap.parse_args()
    problems, bumped_files, bumped_facts = [], 0, 0
    tracked = subprocess.run(["git", "ls-tree", "--name-only", args.base, "data/cards/"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.split()
    current = {str(p.relative_to(ROOT)) for p in card_files()}
    for rel in sorted(set(tracked) ^ current):
        problems.append(f"{rel}: card file added or removed")
    for rel in sorted(current & set(tracked)):
        new_text = (ROOT / rel).read_text()
        old_text = _git_show(args.base, rel)
        if old_text == new_text:
            continue
        old_d, new_d = {}, {}
        if _strip(yaml.safe_load(old_text), old_d) != _strip(yaml.safe_load(new_text), new_d):
            problems.append(f"{rel}: content other than last_verified changed")
            continue
        n = 0
        for k, nv in new_d.items():
            ov = old_d.get(k)
            if ov == nv:
                continue
            n += 1
            if ov is None or nv is None or nv < ov:
                problems.append(f"{rel}{k}: last_verified {ov} -> {nv} (must move forward)")
            elif nv > today():
                problems.append(f"{rel}{k}: last_verified {nv} is in the future")
        if set(old_d) != set(new_d):
            problems.append(f"{rel}: set of last_verified fields changed")
        if args.strict_text:
            for line in difflib.unified_diff(old_text.splitlines(), new_text.splitlines(), lineterm="", n=0):
                if line.startswith(("---", "+++", "@@")):
                    continue
                if not line[1:].lstrip().startswith("last_verified:"):
                    problems.append(f"{rel}: non-date text change: {line[:120]}")
                    break
        bumped_files += 1
        bumped_facts += n
    for p in problems:
        print("ERROR", p)
    print(f"bump diff vs {args.base}: {bumped_files} card files, {bumped_facts} last_verified dates moved; "
          f"{'OK' if not problems else f'FAIL ({len(problems)} problems)'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Canary: prove the change-detection path still works, using fixed fixtures (no network).

1. unchanged page          -> quote found, fingerprint stable
2. nearby text changed     -> quote found, fingerprint CHANGED  (section_changed)
3. quoted number changed   -> quote MISSING                     (quote_missing)
4. fetch failure           -> fetch_failed and last_verified NOT bumped
Exit 1 (and the workflow opens a 'pipeline broken' issue) if any expectation fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reverify import check_one  # noqa: E402
from sgcards_lib import ROOT, norm  # noqa: E402

FIX = ROOT / "tests" / "fixtures"
URL = "https://example.invalid/canary"
FACT = {"value": 4, "source_url": URL, "quote": "Earn 4 miles per dollar (mpd) on online spend.",
        "last_verified": "2026-01-01"}


def run() -> list[str]:
    problems = []
    v1, v2, v3 = (norm((FIX / n).read_text()) for n in
                  ("canary_v1.txt", "canary_v2_section_changed.txt", "canary_v3_quote_changed.txt"))
    s1, fp1 = check_one(FACT, {URL: v1}, {}, "static", None)
    s1b, fp1b = check_one(FACT, {URL: v1}, {}, "static", None)
    if s1 != "ok" or fp1 != fp1b:
        problems.append(f"unchanged page: expected ok+stable fingerprint, got {s1}")
    s2, fp2 = check_one(FACT, {URL: v2}, {}, "static", None)
    if s2 != "ok" or fp2 == fp1:
        problems.append(f"section change not detected (status={s2}, same_fp={fp2 == fp1})")
    s3, _ = check_one(FACT, {URL: v3}, {}, "static", None)
    if s3 != "quote_missing":
        problems.append(f"changed number not detected (status={s3})")
    fact = dict(FACT)
    s4, _ = check_one(fact, {}, {URL: "simulated outage"}, "static", None)
    if s4 != "fetch_failed" or fact["last_verified"] != "2026-01-01":
        problems.append("fetch failure was not reported as fetch_failed / date changed")
    return problems


if __name__ == "__main__":
    probs = run()
    print("CANARY OK" if not probs else "CANARY FAILED:\n- " + "\n- ".join(probs))
    sys.exit(1 if probs else 0)

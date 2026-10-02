#!/usr/bin/env python3
"""Pre-push / CI scan for secrets, personal data and tracking links. Exit 1 on any finding.

Checks every tracked text file for:
  * credential shapes (GitHub/AWS/Slack/Google tokens, private keys, bearer tokens)
  * e-mail addresses (only GitHub noreply addresses allowed), SG NRIC/FIN shapes, card-number shapes
  * affiliate / referral / tracking parameters in URLs
  * a hashed deny-list of names that must never appear in this public repo (stored as hashes so
    the list itself does not publish them)
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DENY_SHA256_16 = {"f4482939d91a358c", "297ab5cccd5dccdd", "2f6eebe1a1533c7c", "e341649cb35956a8"}
PATTERNS = {
    "github_token": r"\b(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})",
    "aws_key": r"\bAKIA[0-9A-Z]{16}\b",
    "slack_token": r"\bxox[abprs]-[A-Za-z0-9-]{10,}",
    "google_key": r"\bAIza[0-9A-Za-z_\-]{35}\b",
    "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "bearer": r"(?i)\bbearer\s+[a-z0-9._\-]{20,}",
    "secret_assign": r"(?i)\b(api[_-]?key|secret|passwd|password|token)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]",
    "nric": r"\b[STFGM]\d{7}[A-Z]\b",
    "card_number": r"\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2})[ -]?\d{4}[ -]?\d{4}[ -]?\d{3,4}\b",
    "tracking_param": r"(?i)https?://[^\s\"')]*[?&](utm_[a-z]+|ref|referral|refcode|aff|aff_id|affiliate|clickid|irclickid|gclid|fbclid|s_cid|cid|pid|promo_code)=",
    "referral_path": r"(?i)https?://[^\s\"')]*/(refer|referral|go|out)/[^\s\"')]+",
}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ALLOWED_EMAIL = re.compile(r"(@users\.noreply\.github\.com|@example\.(com|invalid))$")
SKIP_SUFFIX = {".png", ".jpg", ".pdf", ".ico"}
SELF = {"scripts/scan_repo.py"}  # contains the patterns themselves


def luhn(s: str) -> bool:
    d = [int(c) for c in s if c.isdigit()][::-1]
    return sum(x if i % 2 == 0 else (x * 2 - 9 if x * 2 > 9 else x * 2) for i, x in enumerate(d)) % 10 == 0


def files() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True)
    return [ROOT / f for f in out.stdout.splitlines() if f and Path(f).suffix not in SKIP_SUFFIX]


def main() -> int:
    findings = []
    for path in files():
        rel = str(path.relative_to(ROOT))
        try:
            text = path.read_text(errors="ignore")
        except (IsADirectoryError, FileNotFoundError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if rel not in SELF:
                for name, pat in PATTERNS.items():
                    m = re.search(pat, line)
                    if not m:
                        continue
                    if name == "card_number" and ("MCC" in line or not luhn(m.group(0))):
                        continue  # MCC code lists look like card numbers; real PANs pass Luhn
                    findings.append(f"{rel}:{n}: {name}")
                for m in EMAIL.finditer(line):
                    if not ALLOWED_EMAIL.search(m.group(0)):
                        findings.append(f"{rel}:{n}: email {m.group(0)}")
            for tok in re.findall(r"[A-Za-z]+", line):
                if hashlib.sha256(tok.lower().encode()).hexdigest()[:16] in DENY_SHA256_16:
                    findings.append(f"{rel}:{n}: deny-listed name")
    if findings:
        print("SCAN FAILED:\n" + "\n".join(findings))
        return 1
    print(f"scan ok: {len(files())} files, no secrets / personal data / tracking links")
    return 0


if __name__ == "__main__":
    sys.exit(main())

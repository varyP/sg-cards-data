"""Shared helpers for the SG cards data repo.

SECURITY NOTE: every byte fetched from the web is UNTRUSTED DATA. This module only
normalises text, searches it for exact quotes and hashes sections. It never
executes, evaluates or follows instructions found in fetched content, and callers
must never paste fetched text into prompts as instructions.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parent.parent
CARDS_DIR = ROOT / "data" / "cards"
SOURCES_FILE = ROOT / "sources.yaml"
SNAPSHOT_FILE = ROOT / "snapshots" / "fingerprints.json"
UA = os.environ.get(
    "SGCARDS_UA",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36 sg-cards-data-bot/0.1 (+public data repo; polite, low-frequency)",
)
PROVENANCE_KEYS = ("source_url", "quote", "last_verified")

# ---------------------------------------------------------------- text
_TRANS = str.maketrans({
    "\u00a0": " ", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u200b": "", "\u00ad": "",
})


def norm(text: str) -> str:
    """Canonical normalisation used for quotes AND fetched text. Keep in sync."""
    return re.sub(r"\s+", " ", (text or "").translate(_TRANS)).strip()


def today() -> dt.date:
    # Repo convention: dates are Asia/Singapore calendar dates.
    return (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()


def as_date(v) -> dt.date | None:
    if v is None:
        return None
    if isinstance(v, dt.date):
        return v
    return dt.date.fromisoformat(str(v))


# ---------------------------------------------------------------- fetching
class FetchError(Exception):
    pass


_last_hit: dict[str, float] = {}


def _polite_wait(url: str, delay: float) -> None:
    host = urlparse(url).netloc
    wait = _last_hit.get(host, 0) + delay - time.time()
    if wait > 0:
        time.sleep(wait)
    _last_hit[host] = time.time()


def html_to_text(html: bytes | str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):  # keep <noscript>: DBS serves content there
        tag.decompose()
    return norm(soup.get_text(" "))


def pdf_to_text(data: bytes) -> str:
    proc = subprocess.run(["pdftotext", "-", "-"], input=data, capture_output=True, timeout=120)
    if proc.returncode != 0:
        raise FetchError(f"pdftotext failed: {proc.stderr[:200]!r}")
    return norm(proc.stdout.decode("utf-8", "replace"))


def fetch_text(url: str, method: str = "static", delay: float = 3.0, cache_dir: str | None = None) -> str:
    """Return normalised text for url. Raises FetchError on ANY failure.

    method: static (requests) | headless (Chrome --dump-dom) | manual (always raises).
    A failure must never be treated as 'quote still present'.
    """
    if method == "manual":
        raise FetchError("manual source: needs a human/agent check, not automated fetch")
    if cache_dir:
        cp = Path(cache_dir) / (hashlib.sha1(url.encode()).hexdigest()[:12] + ".txt")
        if cp.exists():
            return norm(cp.read_text())
    _polite_wait(url, delay)
    try:
        if method == "headless":
            chrome = os.environ.get("CHROME_BIN", "google-chrome")
            proc = subprocess.run(
                ["timeout", "120", chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
                 "--virtual-time-budget=15000", f"--user-agent={UA}", "--dump-dom", url],
                capture_output=True, timeout=150,
            )
            if proc.returncode != 0 or len(proc.stdout) < 2000:
                raise FetchError(f"headless fetch failed rc={proc.returncode} bytes={len(proc.stdout)}")
            text = html_to_text(proc.stdout)
        else:
            import requests

            r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "en-SG,en;q=0.9"}, timeout=45)
            if r.status_code != 200:
                raise FetchError(f"HTTP {r.status_code}")
            ctype = r.headers.get("content-type", "")
            if url.lower().split("?")[0].endswith(".pdf") or "pdf" in ctype:
                text = pdf_to_text(r.content)
            else:
                text = html_to_text(r.content)
    except FetchError:
        raise
    except Exception as e:  # network, timeout, parser
        raise FetchError(f"{e.__class__.__name__}: {str(e)[:160]}") from e
    if len(text) < 500:
        raise FetchError(f"suspiciously short page ({len(text)} chars): bot wall or JS shell?")
    if cache_dir:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        cp.write_text(text)
    return text


def section_fingerprint(text: str, quote: str, radius: int = 400) -> str | None:
    """sha256 of the normalised window around the quote (the 'section')."""
    q = norm(quote)
    i = text.find(q)
    if i < 0:
        return None
    window = text[max(0, i - radius): i + len(q) + radius]
    # strip volatile bits (dates like 'Updated 27 Jul 2026' stay, but digits in counters are rare)
    return hashlib.sha256(window.encode()).hexdigest()


# ---------------------------------------------------------------- data model
def load_yaml(path: Path):
    with open(path) as f:
        return yaml.safe_load(f)


CARD_HEADER = "# Information only, not financial advice. Every fact cites its source; check the issuer T&C.\n"


class _NoAliasDumper(yaml.SafeDumper):
    """Never emit &anchors / *aliases: each fact is written out in full, so a re-dump is stable."""

    def ignore_aliases(self, data):
        return True


def dump_card(doc) -> str:
    """Canonical card-file text. dump_card(yaml.safe_load(dump_card(d))) == dump_card(d)."""
    return CARD_HEADER + yaml.dump(doc, Dumper=_NoAliasDumper, sort_keys=False, allow_unicode=True, width=1000)


def card_files(cards_dir=None):
    return sorted(Path(cards_dir or CARDS_DIR).glob("*.yaml"))


def is_fact(node) -> bool:
    return isinstance(node, dict) and "value" in node and ("source_url" in node or "null_reason" in node)


def iter_facts(node, path=""):
    """Yield (path, fact_dict) for every fact object in a card document."""
    if is_fact(node):
        yield path, node
        # facts may nest (e.g. pending change inside); keep walking children that are dicts/lists
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, (dict, list)):
                yield from iter_facts(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            key = v.get("category") if isinstance(v, dict) and v.get("category") else str(i)
            yield from iter_facts(v, f"{path}[{key}]")


def load_sources():
    return load_yaml(SOURCES_FILE) if SOURCES_FILE.exists() else {}


def method_for(url: str, sources: dict) -> str:
    """Fetch method from sources.yaml host rules (first matching prefix wins)."""
    for rule in sources.get("fetch_rules", []):
        if url.startswith(rule["prefix"]):
            return rule["method"]
    return "static"


def load_snapshots() -> dict:
    if SNAPSHOT_FILE.exists():
        return json.loads(SNAPSHOT_FILE.read_text())
    return {}


def save_snapshots(data: dict) -> None:
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_FILE.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")

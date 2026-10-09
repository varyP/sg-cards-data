#!/usr/bin/env python3
"""Build the ChatGPT skills-only plugin ZIP from chatgpt/sg-cards-guide/.

The repo keeps the owner name out of tracked files (see scripts/scan_repo.py), so the package
template uses placeholders that are filled in only at build time:
  {{REPO_OWNER}}      GitHub owner of the public sg-cards-data repo (used in the raw data URLs)
  {{DEVELOPER_NAME}}  publisher name shown in the listing
  {{CATEGORY}}        category title exactly as listed in the OpenAI plugin dashboard

Usage: python scripts/build_chatgpt_plugin.py --owner OWNER --developer-name NAME --category CAT [--out dist]
Writes <out>/sg-cards-guide/ and <out>/sg-cards-guide-<version>.zip. The output is never committed.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "chatgpt" / "sg-cards-guide"
TEXT_SUFFIX = {".md", ".json"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", required=True)
    ap.add_argument("--developer-name", required=True)
    ap.add_argument("--category", required=True)
    ap.add_argument("--out", default="dist")
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", a.owner):
        sys.exit("--owner must be a GitHub user or org name")
    values = {"REPO_OWNER": a.owner, "DEVELOPER_NAME": a.developer_name, "CATEGORY": a.category}

    out = (ROOT / a.out).resolve()
    dest = out / SRC.name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(SRC, dest)
    for f in dest.rglob("*"):
        if f.is_file() and f.suffix in TEXT_SUFFIX:
            text = f.read_text()
            for k, v in values.items():
                text = text.replace("{{" + k + "}}", v)
            if "{{" in text:
                sys.exit(f"unfilled placeholder in {f.relative_to(out)}")
            f.write_text(text)

    manifest = json.loads((dest / "plugin.json").read_text())
    for path in re.findall(r'"(\./[^"]+)"', (dest / "plugin.json").read_text()):
        if not (dest / path).exists():
            sys.exit(f"plugin.json references a missing file: {path}")
    if not (dest / "skills").is_dir() or not any((dest / "skills").glob("*/SKILL.md")):
        sys.exit("no skills/<name>/SKILL.md found")

    zip_base = out / f"{manifest['name']}-{manifest['version']}"
    # The ZIP holds one plugin folder, as the submission docs describe.
    shutil.make_archive(str(zip_base), "zip", root_dir=out, base_dir=SRC.name)
    print(f"built {zip_base}.zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

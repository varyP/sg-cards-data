"""Minimal GitHub issue helper using the `gh` CLI and the workflow's built-in GITHUB_TOKEN.

No personal access tokens. If `gh` or GH_TOKEN is missing (local run), prints a dry-run instead.
Issue bodies may contain excerpts of fetched web text: they are fenced, truncated and have
@-mentions neutralised, because fetched text is untrusted data.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess

MAX_EXCERPT = 1200


def safe_excerpt(text: str, limit: int = MAX_EXCERPT) -> str:
    text = (text or "").replace("```", "'''").replace("@", "@\u200b")
    if len(text) > limit:
        text = text[:limit] + " …[truncated]"
    return "```text\n" + text + "\n```"


def _gh_ok() -> bool:
    return bool(shutil.which("gh")) and bool(os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))


def _run(args: list[str]) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def find_issue(title: str, state: str = "all") -> dict | None:
    if not _gh_ok():
        return None
    out = _run(["issue", "list", "--state", state, "--limit", "200", "--search", f'"{title}" in:title',
                "--json", "number,title,state"])
    for it in json.loads(out or "[]"):
        if it["title"] == title:
            return it
    return None


def ensure_labels(labels: list[str]) -> None:
    if not _gh_ok():
        return
    for lab in labels:
        subprocess.run(["gh", "label", "create", lab, "--force", "--color", "ededed"], capture_output=True, text=True)


def ensure_issue(title: str, body: str, labels: list[str], reopen: bool = False, comment_if_open: bool = False) -> str:
    """Create the issue unless one with the exact title exists. Returns a short status string."""
    if not _gh_ok():
        print(f"[dry-run] issue: {title} labels={labels}")
        return "dry-run"
    existing = find_issue(title)
    if existing:
        if existing["state"] == "OPEN" and comment_if_open:
            _run(["issue", "comment", str(existing["number"]), "--body", body])
            return f"commented #{existing['number']}"
        if existing["state"] != "OPEN" and reopen:
            _run(["issue", "reopen", str(existing["number"])])
            _run(["issue", "comment", str(existing["number"]), "--body", body])
            return f"reopened #{existing['number']}"
        return f"exists #{existing['number']}"
    ensure_labels(labels)
    args = ["issue", "create", "--title", title, "--body", body]
    for lab in labels:
        args += ["--label", lab]
    return "created " + _run(args).strip()

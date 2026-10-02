#!/usr/bin/env python3
"""Open (or comment on) a 'pipeline broken' issue when a scheduled job fails. Usage: pipeline_broken.py NAME RUN_URL"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gh_issues import ensure_issue  # noqa: E402

name, url = sys.argv[1], sys.argv[2]
print(ensure_issue(f"[pipeline broken] {name}",
                   f"The scheduled job **{name}** failed: {url}\n\nUntil it is fixed, facts are not being re-checked "
                   "and dates must not be trusted as current.", ["pipeline-broken"], reopen=True, comment_if_open=True))

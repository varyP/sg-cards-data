# sg-cards-data

Verified, source-cited data on Singapore credit cards, plus the pipeline that keeps it fresh.
Information only, not financial advice. Card terms change: always confirm on the issuer's T&Cs.

## What's here
| Path | What |
|---|---|
| `data/cards/*.yaml` | One file per card; the current count is the `count` field in `data/index.json`. Every fact has `value`, `source_url`, a verbatim `quote` and `last_verified`, or `value: null` with a `null_reason`. |
| `data/index.json` | Generated card list (`id`, `issuer`, `name`, `path`). **Use this to find cards** instead of listing files through the GitHub API (unauthenticated calls are rate-limited). |
| `schema/card.schema.json` | JSON Schema for card files |
| `sources.yaml` | Source tiers, allowlist, blacklist, fetch rules, change keywords, card aliases |
| `scripts/validate.py` | Fails on schema errors, numbers without provenance, expired pending changes, future dates, and a missing or stale `data/index.json`. Warns on facts older than 30/60 days. |
| `scripts/build_index.py` | Regenerates `data/index.json` from the card files (`--check` to verify only) |
| `scripts/check_bump_diff.py` | Guard for the weekly re-verify PR: card files may differ from `HEAD` only in `last_verified` (dates move forward only); `--strict-text` also flags re-dump noise |
| `scripts/scan_feeds.py` | Daily: Tier 2 RSS + issuer page diffs, sends signals to issues (issuer/Tier 2) or a digest (everything else) |
| `scripts/reverify.py` | Weekly: re-fetches sources, bumps `last_verified` only when the exact quote is still present, section-fingerprint diff |
| `scripts/health_report.py` | Weekly: freshness, stale facts, failing sources, pending changes, canary, review backlog over 7 days |
| `scripts/canary.py` | Proves the change-detection path still works (fixtures in `tests/fixtures`) |
| `scripts/scan_repo.py` | Secret / personal-data / tracking-link scan (runs in CI) |
| `tests/eval_set.yaml` | Bot evaluation set (owner: second reviewer) |
| `bot/system_prompt.md` | Behaviour contract for the chat bot |
| `REVIEW.md` | Two-reviewer handshake; the repo owner merges |

## Card list for bots and scripts
Fetch `data/index.json` as a raw file from the `main` branch:
`https://raw.githubusercontent.com/<repo owner>/sg-cards-data/main/data/index.json` (the owner handle
is kept out of tracked files by `scripts/scan_repo.py`). Each card's raw URL is the same base plus
its `path`. Raw files are not subject to the GitHub API's unauthenticated rate limit.

## Source tiers
1. **Issuer** pages, T&Cs and announcements, plus MAS / MoneySense / ABS: the only sole source for a number.
2. **Change signals:** MileLion, Mainly Miles, Suitesmile. Two independent hits = high confidence, still confirmed on the issuer site.
3. **Cross-check only:** SingSaver, MoneySmart (affiliate-funded; used only with a card-level T&C linked) and Sethisfy.
   **Explainer only:** the MoneySmart credit card knowledge hub, for concepts (DCC, MCCs, how caps and
   fee-waiver requests work). Never a source or check for a number; its card-level figures are often stale.

## Automation (GitHub Actions, no secrets)
| Workflow | When (SGT) | Permissions |
|---|---|---|
| `validate` | every push / PR | `contents: read` |
| `daily-scan` | daily 09:15 | `contents: read`, `issues: write` |
| `weekly-reverify` | Mon 10:00 | `contents: write`, `pull-requests: write`, `issues: write` |
| `weekly-health` | Mon 12:00 | `contents: read`, `issues: write`, `pull-requests: read`, `actions: read` |

Only the built-in `GITHUB_TOKEN` is used; there are no repository secrets and no personal access
tokens. Opening the re-verify PR needs *Settings → Actions → General → "Allow GitHub Actions to
create and approve pull requests"*; without it the job pushes the branch and opens an issue instead.

## Known limits
- **Manual sources:** Maybank and American Express block scripted fetches (bot wall); HSBC and some
  Standard Chartered PDFs are disallowed by robots.txt. These facts are skipped by the re-verify job
  and listed in the health report's manual-check queue; they go stale unless an agent re-checks them.
- **JS-rendered pages:** DBS card pages and Trust product pages need headless Chrome (present on
  GitHub's Ubuntu runners). If Chrome is missing, those fetches fail and dates are not bumped.
- Issuer sites may block cloud IP ranges, including GitHub runners. Failed fetches never bump dates;
  they show up as failing sources.

## Run locally
```bash
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
python scripts/build_index.py   # after adding, renaming or editing a card's id/issuer/name
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/scan_repo.py
```

## Licence
| What | Licence | File |
|---|---|---|
| Data: `data/` (card files, `index.json`), `sources.yaml`, `tests/eval_set.yaml`, plus `snapshots/`, `reports/` and the docs (`README.md`, `REVIEW.md`, `CHANGELOG.md`, `bot/`, the text in `chatgpt/`) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | `LICENSE-DATA` |
| Code: `scripts/`, `.github/workflows/`, `schema/`, test code (`tests/test_pipeline.py`, `tests/fixtures/`) | MIT | `LICENSE` |

Reuse the data freely, including commercially, with attribution: "sg-cards-data contributors,
CC BY 4.0" plus a link to this repository and a note of any changes. The short `quote` excerpts are
from issuer and regulator documents and stay with their owners; they are here only so each fact can
be checked, and are not relicensed. Card names and trademarks belong to their owners.

## Notes on content
Quotes are short excerpts from issuer documents, kept only so each fact can be checked. Card names
and trademarks belong to their owners. No referral or affiliate links, ever.

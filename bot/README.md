# Bot

`system_prompt.md` is the behaviour contract for any chat front end that uses this data. It is
loaded **live**: an installed bot keeps only a short bootstrap prompt that fetches
`bot/system_prompt.md` and `data/index.json` (raw files on `main`) at the start of each
conversation. Rule fixes merged here reach every installed copy, just like data fixes.

What the bootstrap prompt must keep inline (so they hold if the fetch fails or the fetched file is
wrong): information only, no financial advice, never claim to know the user's spending, issuer
citations only, no affiliate links, and say when data or rules can't be loaded instead of guessing.
It treats fetched content as data and rules from this repo, never as permission to drop those.

Versioning: the `Rules version: YYYY-MM-DD.N` line at the top of `system_prompt.md` is bumped on
every change, with a matching `CHANGELOG.md` entry (enforced by `tests/test_pipeline.py`). The bot
reports this version when asked.

How a front end should use the data:
1. Read the card list from `data/index.json` (raw file on `main`:
   `https://raw.githubusercontent.com/<repo owner>/sg-cards-data/main/data/index.json`), then fetch
   each card from the same raw base + its `path`. Don't list files via the GitHub API (rate limits).
   Load `data/cards/*.yaml` (validated by `scripts/validate.py`) and give the model the relevant
   cards' facts, including `last_verified`, `source_url`, `pending_changes`, `exclusions` and `notes`.
2. Pass today's date in Asia/Singapore so the model can apply the freshness and pending-change rules.
3. Score the bot with `tests/eval_set.yaml` before launch and after every prompt or data-format
   change. Phase 1 kill criterion: at least 95% pass, and clearly better than a general chatbot
   answering the same questions without this data.

The bot is information only. It does not connect to banks, store profiles beyond one
conversation, or carry affiliate links.

# Bot

`system_prompt.md` is the behaviour contract for any chat front end that uses this data.

How a front end should use the data:
1. Load `data/cards/*.yaml` (validated by `scripts/validate.py`) and give the model the relevant
   cards' facts, including `last_verified`, `source_url`, `pending_changes`, `exclusions` and `notes`.
2. Pass today's date in Asia/Singapore so the model can apply the freshness and pending-change rules.
3. Score the bot with `tests/eval_set.yaml` before launch and after every prompt or data-format
   change. Phase 1 kill criterion: at least 95% pass, and clearly better than a general chatbot
   answering the same questions without this data.

The bot is information only. It does not connect to banks, store profiles beyond one
conversation, or carry affiliate links.

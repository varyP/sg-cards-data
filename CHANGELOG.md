# Changelog

## 2026-10-07: licences
- Data under CC BY 4.0 (`LICENSE-DATA`): `data/`, `sources.yaml`, `tests/eval_set.yaml`, plus
  `snapshots/`, `reports/` and the docs. Code under MIT (`LICENSE`): `scripts/`, workflows, `schema/`,
  test code. Issuer quote excerpts are not relicensed. README "Licence" section added.
- No card data or bot rules changed.

## 2026-10-05: answer-quality rules from test chats (rules version 2026-10-05.2)
- New ground rules 11-14 in `bot/system_prompt.md`: coverage honesty ("among the N cards I track";
  no "no card beats X" without a market check on issuer pages in the chat); cards outside the dataset
  only with figures read live from the issuer page in the chat, cited with link and date and labelled
  "not in my checked list"; outcomes, not orders ("on these numbers X comes out ahead"); unsourced
  claims marked "unconfirmed" with no number, or left out.
- Citations required inline in follow-up answers too; the disclaimer goes on every shortlist or
  comparison; never save a user's cards, spending, trips or income beyond the conversation.
- "Only the data" and the load-failure rule now allow the rule-12 exception.
- Tests check the new wording. No card data changed.

## 2026-10-05: live bot rules (rules version 2026-10-05.1)
- `bot/system_prompt.md` is now loaded live by each installed bot at the start of every conversation
  (bootstrap prompt keeps the hard safety rules inline). Added the `Rules version: 2026-10-05.1` line,
  a "How this file is used" section (bootstrap rules win; bump version on every change; report the
  version when asked) and an explicit "say so when data can't be loaded, never answer from memory" rule.
- Tests: the rules file must carry a well-formed version line that is recorded in this changelog, and
  must keep the core safety rules.
- No card data changed.

## 2026-10-05: portal bonuses and UOB overseas-processed SGD fee (data)
- UOB PRVI Miles: added promotion earn rows for the dedicated Agoda site (up to 8 mpd, foreign-currency
  hotel spend, bookings to 2027-08-15, Japan stays excluded) and Expedia site (up to 8 mpd hotels/other,
  up to 3 mpd flights, bookings to 2027-03-31); new fact `overseas_processed_sgd_fee_pct` = 1% for SGD
  transactions on Visa/Mastercard processed outside Singapore (UOB general card information).
- Citi PremierMiles: added promotion earn rows for Kaligo (10 mpd, to 2026-12-31) and Agoda (up to
  7.2 mpd, bookings to 2026-12-31, stays to 2027-04-30) via the dedicated links.
- All quotes verbatim from issuer pages, checked 2026-10-05. Caps and minimum spend not stated on the
  product pages, so `null` with a reason.

## 2026-10-04: MoneySmart knowledge hub audited (explainer tier)
- New `tier3_explainer` tier in `sources.yaml` and source `moneysmart-knowledge-hub`
  (kind: reference, fetch: manual, so the pipeline never fetches it). Concepts only: never the source
  or check for a number, not a change signal, link only a bare canonical article URL.
- Audit: 10 sampled claims; 6 matched issuer/MAS pages, 4 wrong or stale (DBS Vantage fee waiver,
  Maybank F&F tier, OCBC 365 streaming rate and the 1 Nov revision missing, MAS credit-limit table).
  No card data changed.

## 2026-10-03: fix 1 (self-test findings)
- Eval set: M7 expected answer now matches the quoted exclusion data (MCC 6300 quoted for DBS, UOB,
  OCBC; Maybank F&F lists 5960/6381/6399; no insurance MCC quoted for Citi). F1 cites the 30,000-mile
  option from the now-quoted Citi PremierMiles welcome text. Meta: owner Maxis, maintained with grokbot.
- Filled with verbatim issuer quotes: FX fees for HSBC Live+/Revolution/TravelOne (up to 3.25%),
  Maybank F&F/Horizon (up to 3.25%, derived 2.25% + up to 1%), AMEX KrisFlyer Ascend/True Cashback
  (3.25%), SC Journey/Smart (3.5%, derived 1% + 2.5%), Citi Rewards (up to 3.25%); Citi points
  transfer fee S$27.25 (PremierMiles and Rewards); OCBC 365 spend-based waiver S$10,000 a year.
- New generated `data/index.json` (card id, issuer, name, path) and `scripts/build_index.py`; the
  validator fails when the index is stale. Bot prompt and README point to the raw index file.

## 2026-10-03: phase 1 pilot
- 25 pilot cards (DBS, UOB, OCBC, Citi, HSBC, Standard Chartered, Trust, Maybank, American Express),
  every fact issuer-sourced with a verbatim quote, checked 2026-10-03 (SGT).
- Pending changes recorded: DBS Vantage local earn 1.5 to 1.4 mpd (from 2026-11-02); OCBC 365
  cashback programme revision (from 2026-11-01); Trust Freedom stockback 3% promo ends 2026-12-31,
  then 2% local / 0.5% foreign.
- Already in effect and recorded: DBS Altitude / Woman's World / Vantage spend-based fee waivers
  ceased from 2026-08-01.
- Left out of the pilot: SC Simply Cash (no fee data on its page), DBS Live Fresh (not on the DBS
  listing when checked), DBS Chromo (ages 21-29 only).
- Pipeline: schema, validator, daily scan, weekly re-verify with section fingerprints, weekly
  health report with canary and a 7-day review-backlog alarm, repo secret/personal-data scan.
- Eval set (57 cases) and bot system prompt.

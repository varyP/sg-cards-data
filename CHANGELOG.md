# Changelog

## 2026-10-09: rules 2026-10-09.1 (bot rules, owner merge)
- Memory: closed-card facts now expire. A "Closed <card>, <month year>" fact is removed once 13 months
  have passed since the closure month, checked at the start of every conversation alongside the "Until"
  notes (e.g. "Closed Citi Rewards, Mar 2026" is removed from 1 Apr 2027). Memory stays on by default.

## 2026-10-08: Maybank Family & Friends, two more MCC exclusion rows (data)
- Added the two missing rows of Maybank's 1-Dec-2025 MCC table to Family & Friends: cash
  disbursement/quasi-cash/top-ups (6010, 6011, 6050, 6529, 6530, 6534, 7511) and cleaning, maintenance
  and janitorial services (7349). Quotes come from the reviewer's 2026-10-07 manual read, same framing
  statement and issuer page as the existing rows. F&F now lists all five table rows, matching XL.

## 2026-10-08: rules 2026-10-08.1 (bot rules, owner merge)
- New "Memory" section: each private copy remembers its owner's card profile (cards, categories, goal, closed cards, expiring trip notes), never card numbers, IDs, income or third parties; plus family one-off questions, stricter "outcomes, not orders", and unconfirmed merchant/charge treatment.

## 2026-10-07: merge rights for the bot rules
- `REVIEW.md`: any PR that changes `bot/system_prompt.md` is merged by the repo owner in person, even
  after both reviewers say OK (every installed bot loads it live); such changes go in their own PR
  marked owner-merge. Agents may merge only data, sources and tooling PRs.

## 2026-10-07: Maybank manual read and Maybank XL Rewards (data)
- Maybank blocks automated fetches, so a reviewer read the issuer pages manually in a browser on
  2026-10-07. Facts whose quote matched that read verbatim now carry last_verified 2026-10-07 and the
  note "Manual read by reviewer". Family & Friends: annual fee and 3-year waiver, both tiers (6% at
  S$800, S$20 cap; 8% at S$1,600, S$30 cap), base 0.22%, FX fee. Horizon: 2.8 mpd with S$800 minimum,
  1.2 mpd (minimum spend filled: none), FX fee, the insurance/medical/education earn statement. FX fee
  2.25% + up to 1% re-confirmed on the charges page. After review, the reviewer supplied verbatim quotes
  for the rest (F&F S$12,000 waiver and MCC exclusions; Horizon minimum income, fee and waivers, 40,000 TP
  air-ticket cap), so those are also 2026-10-07.
- New `overseas_processed_sgd_fee_pct` (up to 1%) on all three Maybank cards (charges page).
- Horizon's reported 26 May 2025 change stays unconfirmed (no issuer quote; T&C PDF not read).
- New card: Maybank XL Rewards (29 in `data/index.json`): minimum income S$30,000, age 21 to 39, the
  1-Dec-2025 Maybank MCC exclusions, and the full S$500 minimum-spend sentence (all spend counts).
  Conversion ratio and fee stay null (no exact quote).

## 2026-10-07: stable weekly re-verify (tooling)
- `scripts/reverify.py` now writes card files with `sgcards_lib.dump_card` (no YAML anchors, stable
  quoting), so a re-run changes only `last_verified` lines. Six card files that still used anchors or
  non-canonical quoting were re-dumped once (formatting only; parsed content identical).
- New `scripts/check_bump_diff.py`: fails if a card file changes in anything but `last_verified`, or a
  date moves backwards or into the future. The weekly workflow now runs the validator, unit tests,
  privacy scan and this guard, and puts the results in the PR body (Actions-opened PRs get no CI).
- Tests: dump is lossless and idempotent; a date bump changes only date lines.

## 2026-10-07: issue #8 gaps and three new cards (data)
- New cards (28 in `data/index.json`): UOB Visa Signature, Citi Cash Back, DBS Live Fresh (closed to
  new applicants from 7 Sep 2026; existing cardmembers still earn). Maybank XL Rewards not added: every
  maybank2u.com.sg URL returned Akamai 403 / HTTP 500 on 2026-10-07, so no fact could be quoted.
- UOB Lady's / Lady's Solitaire: category lock period (calendar quarter, change applies from the next
  quarter), selection deadline and default; Travel defined in the T&C as airlines and hotels only, with
  no MCC list (so MCC 4722 travel agencies and 7512 car rental are not confirmed); product page wording
  recorded alongside; Transport MCC whitelist; `UNI$1 = 2 miles` conversion filled.
- UOB One / Preferred Visa / Lady's / Solitaire: `overseas_processed_sgd_fee_pct` = 1 (UOB general card
  information), as already on PRVI Miles.
- DBS (Altitude, Vantage, Woman's World, yuu, Live Fresh): `overseas_processed_sgd_fee_pct` = 1 from the
  DBS Credit Card Agreement cl. 9.3 (last updated 30 June 2026); the 2.8% figure is recorded separately
  as the debit-card section of the Rates & Fees page ("As at 30 December 2020"). `fx_fee_pct` (3.25%,
  unchanged) now quotes the credit card agreement instead of the debit-card section.
- Trust Freedom: Miles / Unlimited / Bonus cashback modes added as earn rows with `value: null` (rates
  shown only as images in the KFS); quarterly mode switching, bonus minimum-spend period, overseas SGD
  treatment, Trust Miles conversion ratio and S$27.25 fee filled.

## 2026-10-07: Maybank and AMEX manual re-check (data)
- AMEX KrisFlyer Ascend and True Cashback: every quote re-read verbatim from the product pages and
  T&C PDFs on 2026-10-07 (dates bumped). No value changed. Filled: Ascend SIA/Scoot/KrisShop/Pelago cap
  (none, "with no cap"); True Cashback minimum spend (none) for both rows; exclusions from the AMEX
  non-eligible purchases list (updated 21 Aug 2025): Ascend 8 entries (insurance except via AMEX
  channel, utilities, education/non-profit, public hospitals, bill payments/SingPost, public transit,
  wallet top-ups, SPC); True Cashback public transit and wallet top-ups.
- Maybank Family & Friends and Horizon Visa Signature: not re-readable (Akamai 403 to scripted and
  browser fetches from the box, WebFetch HTTP 500). Dates NOT bumped; a note records the attempt.
- Files rewritten with the canonical dumper (no YAML anchors), so `*id001` aliases are expanded.

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

# Changelog

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

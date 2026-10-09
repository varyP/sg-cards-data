# ChatGPT plugin (skills-only)

`sg-cards-guide/` is the source of the SG Cards Guide plugin for ChatGPT and Codex. It is
**skills-only**: one skill, no MCP server, nothing hosted. It shares one base with the Grok bot: the
skill fetches `bot/system_prompt.md`, `data/index.json` and `data/cards/*.yaml` live from `main` at
the start of every conversation, and inlines only the hard safety rules. No card facts or data
snapshot live in the skill, so data and rules fixes reach the plugin with no new upload. Only a change
to the inlined hard rules or the listing needs a new package version.

Format: portable Agent Plugins package (root `plugin.json` with the Agent Plugins 1.0.0 schema,
skills discovered from `skills/`, OpenAI listing fields under `extensions.com.openai.interface`),
per https://developers.openai.com/plugins/build/plugins and
https://developers.openai.com/plugins/deploy/submission (read 2026-10-09).

## Build
The repo keeps the owner name out of tracked files, so the template uses placeholders
(`{{REPO_OWNER}}`, `{{DEVELOPER_NAME}}`, `{{CATEGORY}}`), filled only at build time:

    python scripts/build_chatgpt_plugin.py --owner <github owner> --developer-name "<publisher>" --category "<dashboard category>"

Output goes to `dist/` (not committed): the filled plugin folder and `sg-cards-guide-<version>.zip`.

## Versioning
- `plugin.json` `version` (semver) changes only when the package changes: skill text, listing or assets.
- The skill states the minimum `Rules version` it was built against. The manifest schema is closed,
  so this is not a manifest field. Rules changes don't need a new package unless they change a hard
  rule that the skill inlines.

## Before submission (owner)
- OpenAI Platform org access and verified publisher identity; the category title from the dashboard.
- Listing URLs are optional for skills-only packages, but hosting the privacy policy and terms is
  still recommended. Their wording must match the skill's memory section.
- Run `test-cases.md` against a local install.

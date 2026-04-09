---
name: sync-chatgpt-deep-research-to-repo
description: >-
  End-to-end workflow to sync ChatGPT Project Deep Research PDFs into this git
  repo and refresh README indexes. Use when the user asks to download or sync
  Deep Research PDFs from ChatGPT via Playwright.
---

# Sync ChatGPT Deep Research PDFs into this repo

## When to use

The user wants **Playwright** (typically `user-playwright` MCP) to pull **Deep Research** PDFs out of **ChatGPT Projects** into the repository and keep **README** indexes up to date.

## Read first

1. Repository agent guide: [`AGENTS.md`](../../AGENTS.md) — includes **`deep-research-download-log.json`** (last run + per-conversation PDF state).
2. In order:
   - [`../chatgpt-playwright-login-and-projects/SKILL.md`](../chatgpt-playwright-login-and-projects/SKILL.md)
   - [`../chatgpt-deep-research-pdf-download/SKILL.md`](../chatgpt-deep-research-pdf-download/SKILL.md)
   - [`../research-readme-pdf-index/SKILL.md`](../research-readme-pdf-index/SKILL.md)

## Execution order

1. **Session**: Open ChatGPT via **user-playwright** MCP; complete login handoff if needed; list all Projects.
2. **Per project**: Create or reuse `<repo>/<sanitized_project_name>/`; enumerate threads with Deep Research; for each thread, export PDF **through MCP** (see PDF skill), save under that folder, then run `scripts/sync_chatgpt_deep_research_pdfs.py record ...` to update `deep-research-download-log.json`.
3. **README**: Run `uv run python scripts/sync_chatgpt_deep_research_pdfs.py update-readmes` (optionally `--only <folder>`) so each `README.md` PDF index matches files on disk.
4. **Root README**: Update [`../../README.md`](../../README.md) only if the project-folder layout or high-level description changed.

## Done criteria

- Every new PDF appears under the correct project folder (saved via MCP, not the Python script).
- `deep-research-download-log.json` `conversations` entries match what you did (`record` helper).
- No orphan table rows; every PDF listed in that folder’s README exists.
- Human was prompted if auth or UI blocked automation.

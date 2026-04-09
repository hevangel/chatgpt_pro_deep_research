# Agent instructions: sync ChatGPT Deep Research PDFs

This repository holds Deep Research exports organized like **ChatGPT Projects**: each project becomes a **top-level folder** whose name matches the ChatGPT project (with filesystem-safe characters). PDFs for that project live inside that folder. Each folder’s `README.md` includes an **index table** of synced PDFs.

## In-scope ChatGPT projects (download / sync only these)

When syncing Deep Research PDFs from ChatGPT into this repo, **only** process these four projects (in this order is fine). **Do not** export or `record` threads from other ChatGPT projects unless the owner explicitly expands scope.

| # | ChatGPT project (typical name) | Repo folder (`--folder` / `project_folder`) |
|---|--------------------------------|---------------------------------------------|
| 1 | Engineering | `engineering` |
| 2 | Investing | `investing` |
| 3 | Philosophy | `philosophy` |
| 4 | Random ideas | `random_ideas` |

Other top-level folders in the repo (if any) are **out of scope** for routine agent sync: leave them unchanged and do not pull new PDFs into them from ChatGPT unless instructed.

## How PDFs get here (primary)

**Downloads are driven by an agent (or human) using the `user-playwright` MCP** in Cursor: navigate ChatGPT, open each Deep Research thread, use **Export → PDF** (or equivalent), and save the file under the correct project folder in this repo. The Python script **does not** open a browser or download PDFs.

### Browser tooling: Playwright MCP only

- **Always use the Playwright MCP** (`user-playwright`): `browser_navigate`, `browser_wait_for`, `browser_snapshot`, `browser_click`, `browser_run_code` (for `waitForEvent('download')` + `saveAs` into the repo), etc.
- **Do not use Cursor’s built-in / internal browser MCP** (`cursor-ide-browser`) for ChatGPT Deep Research export in this repo. It does not match the documented download flow, iframe handling is different, and it is easy to diverge from the skills. If only the internal browser appears enabled, **stop and enable `user-playwright`**, then continue.

**Playwright MCP gotchas (brief):**

- In `browser_run_code`, the MCP sandbox may not expose Node `setTimeout` / `timers/promises`. Use **`page.evaluate((ms) => new Promise((r) => setTimeout(r, ms)), ms)`** for delays inside snippets, or use the **`browser_wait_for`** tool between steps.
- **`Export`** must use **`exact: true`** (or the snapshot-driven click that resolves to that locator). A loose `name: 'Export'` match can mis-click when multiple similar controls exist.
- If the Deep Research iframe still shows **in-progress / “Researching…”**, there is **no Export** yet—poll, wait, or come back later; do not treat that as a selector bug.
- When **two** `internal://deep-research` iframes appear, **`Export` / `Export to PDF` often live in the second** (`nth(1)`). Prefer scanning all matching iframes for `Export to PDF` after opening the menu.

After saving a PDF (or skipping a thread), update `deep-research-download-log.json` with the helper CLI (see below).

## Local Python helpers (no browser)

**Script:** `scripts/sync_chatgpt_deep_research_pdfs.py` — inventory scan, README tables, log records, small utilities. No Playwright dependency.

```bash
cd /path/to/chatgpt_pro_deep_research
uv sync
uv run python scripts/sync_chatgpt_deep_research_pdfs.py inventory
uv run python scripts/sync_chatgpt_deep_research_pdfs.py update-readmes
uv run python scripts/sync_chatgpt_deep_research_pdfs.py update-readmes --only investing
uv run python scripts/sync_chatgpt_deep_research_pdfs.py record --conversation-id <uuid> \
  --folder engineering --outcome downloaded --pdf-filename "Report Title.pdf"
uv run python scripts/sync_chatgpt_deep_research_pdfs.py record --conversation-id <uuid> \
  --folder philosophy --outcome skipped_no_deep_research
uv run python scripts/sync_chatgpt_deep_research_pdfs.py conv-id "https://chatgpt.com/g/.../c/<uuid>"
uv run python scripts/sync_chatgpt_deep_research_pdfs.py match-title --folder engineering --title "Partial title"
uv run python scripts/sync_chatgpt_deep_research_pdfs.py projects
uv run python scripts/sync_chatgpt_deep_research_pdfs.py resolve-slug g-p-6910100b17ac819181e66c047f880ffb-engineering
```

Use **`match-title`** before exporting when you want to skip re-downloading if a PDF on disk already matches the report heading.

## Download log JSON (root)

**File:** `deep-research-download-log.json` (repo root, **gitignored**). See [`deep-research-download-log.example.json`](deep-research-download-log.example.json) for the same shape with placeholder UUIDs.

The helper script **creates and updates** this file:

- **`last_run`**: `started_at`, `finished_at` (UTC), optional `helper_command` (`inventory` | `update-readmes`), optional `only_folder` when a command scoped one project.
- **`pdf_inventory`**: snapshot of **`*.pdf`** under each configured project folder (`indexed_at`, `item_count`, `items[]` with `relative_path`, `bytes`, etc.). Refreshed by `inventory`, `update-readmes`, and `record`.
- **`conversations`**: map of **ChatGPT conversation UUID** → record with:
  - **`outcome`**: `downloaded` | `skipped_no_deep_research` | `export_timeout` | `error` | `legacy_import`
  - **`project_folder`**: repo folder name (must be one of the **in-scope** folders: `engineering`, `investing`, `philosophy`, `random_ideas`)
  - For **`downloaded`**: `pdf_filename`, `pdf_relative_path` (e.g. `investing/Report.pdf`)
  - **`updated_at`**: when this record was last written
  - **`detail`**: optional short message for errors / timeouts

**Skip rules:** conversations with outcome **`downloaded`**, **`skipped_no_deep_research`**, or **`legacy_import`** are treated as settled for planning (agents still use MCP to verify). **`export_timeout`** and **`error`** can be retried. To **force a redownload**, delete that conversation’s entry from `conversations`. If you still use the old `.deep-research-sync-state.json`, it is **migrated once** into the new log when the new file does not exist yet.

## What you use (in-editor / MCP)

- **Playwright (`user-playwright`) — required for this workflow:** `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_press_key`, `browser_wait_for`, `browser_tabs`, `browser_run_code`, etc. Prefer snapshots before structural clicks; refresh the snapshot after navigation or UI changes.
- **Not for Deep Research PDF sync:** `cursor-ide-browser` (Cursor Simple Browser). Do not substitute it for `user-playwright` here.
- **Skills** — quick entry: `[skills/sync-chatgpt-deep-research-to-repo/SKILL.md](skills/sync-chatgpt-deep-research-to-repo/SKILL.md)`. Detailed steps (read in order when doing a full sync):
  1. `[skills/chatgpt-playwright-login-and-projects/SKILL.md](skills/chatgpt-playwright-login-and-projects/SKILL.md)`
  2. `[skills/chatgpt-deep-research-pdf-download/SKILL.md](skills/chatgpt-deep-research-pdf-download/SKILL.md)`
  3. `[skills/research-readme-pdf-index/SKILL.md](skills/research-readme-pdf-index/SKILL.md)`

## End-to-end workflow (checklist)

```text
[ ] 1. Confirm workspace root is this repo. Read deep-research-download-log.json if present.
[ ] 2. Open ChatGPT in Playwright MCP; if login or 2FA is required, stop and ask the human to finish, then continue.
[ ] 3. Work only the four in-scope projects: engineering, investing, philosophy, random_ideas (see table above). Ignore other ChatGPT projects.
[ ] 4. For each in-scope project (1→4):
    [ ] a. Open project; list threads with Deep Research.
    [ ] b. For each thread: optional match-title helper to skip if PDF already on disk.
    [ ] c. Export PDF via MCP; save under <repo>/<project_folder>/ with a clear filename.
    [ ] d. Run: record --conversation-id ... --folder ... --outcome downloaded --pdf-filename "..."
    [ ] e. If not Deep Research: record with outcome skipped_no_deep_research.
[ ] 5. uv run python scripts/sync_chatgpt_deep_research_pdfs.py update-readmes (and inventory if you want a fresh pdf_inventory).
[ ] 6. Optionally update root README.md if project list or high-level structure changed.
```

## Repository layout rules


| ChatGPT                       | On disk                             |
| ----------------------------- | ----------------------------------- |
| Project name (display string) | Folder `<repo>/<sanitized_name>/`   |
| Deep Research PDFs            | `<repo>/<sanitized_name>/*.pdf`     |
| Human-readable list           | `<repo>/<sanitized_name>/README.md` |


If a ChatGPT project name matches an **existing** domain folder (case-insensitive), e.g. `Engineering` and `engineering/`, use that existing directory instead of creating a duplicate.

**Sanitization** (must be stable and reversible enough for humans): trim; replace `\ / : * ? " < > |` with `-`; collapse repeated `-`; trim trailing dots and spaces on Windows. If two projects collide after sanitization, append a short suffix (`-2`, `-3`).

## When to stop and ask the human

- Login, captcha, SSO, or verification is required.
- ChatGPT UI changed so selectors in the skills no longer match: capture a snapshot, note the mismatch, and ask for a quick UI confirmation or updated labels.
- Downloads fail repeatedly (network, permissions, or MCP download path). Report the last error and where the file was expected.

## Security

- Do not paste session tokens or cookies into the repo.
- PDFs may contain sensitive content; only commit what the repository owner expects.


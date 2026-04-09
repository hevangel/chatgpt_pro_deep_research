---
name: chatgpt-deep-research-pdf-download
description: >-
  Locates Deep Research reports in ChatGPT threads and saves them as PDF via
  Export → PDF inside the deep_research sandbox (user-playwright MCP). After
  saving, use scripts/sync_chatgpt_deep_research_pdfs.py record (local helper)
  to update deep-research-download-log.json.
---

# ChatGPT: Deep Research PDF download

## What you are looking for

In a thread that ran **Deep Research**, the UI typically includes a distinct **report** or **artifact** block (long document, citations, headings). Export is usually under a **share** or **overflow** menu on that report, with an action labeled like **Download as PDF**, **Export**, or **PDF**.

Labels change; always use the **current** `browser_snapshot` text and roles to pick the right control.

## High-level click path

1. Open the thread from the project thread list (click ref from latest snapshot).
2. `browser_wait_for` content settle; `browser_snapshot`.
3. Scroll the main conversation pane until the Deep Research **report** is visible (use `browser_run_code` with `page.mouse.wheel` or scroll into view if needed).
4. Open the report’s **share / more / export** menu (icon near the report header or top-right of the card—match snapshot).
5. Click **Download as PDF** (or equivalent wording).

## Iframe detail (important)

The report UI lives under `iframe[src*="deep_research"]` (MCP snapshots may show `iframe[title="internal://deep-research"]`). The **Export** control is usually in that frame’s **inner document** (often the first child frame). Prefer **`browser_snapshot`** and **`browser_click`** with refs from the latest snapshot; use `browser_run_code` when you need `waitForEvent('download')` and `download.saveAs(path)`.

After **Export**, a **`[role="menu"]`** often lists **Copy contents**, **Export to Markdown**, **Export to Word**, **Export to PDF**. If the PDF row is localized, match **`/pdf/i`** on menu buttons or use the **last** menu button when the order matches that pattern.

## Playwright download (MCP `browser_run_code`)

Use `browser_run_code` so the download is captured reliably. Set the save path to an **absolute path** under the repo project folder, e.g. Windows: `C:/proj/chatgpt_pro_deep_research/engineering/My_Report.pdf`. Do not rely on Node `require('fs')` in MCP snippets unless your environment supports it; `download.saveAs` accepts a string path.

Local **Python does not** perform downloads; it only helps with inventory, README tables, and log records (`AGENTS.md`).

Pattern (adapt frame chain and selectors from live snapshot):

```javascript
async (page) => {
  const base = 'C:/proj/chatgpt_pro_deep_research/<project_folder>/';
  // Open thread URL first (outside this snippet).
  const inner = page.frameLocator('iframe[title="internal://deep-research"]'); // or src*=deep_research
  const root = inner.frameLocator('#root'); // if snapshot shows #root; else use child frame from snapshot
  await root.getByRole('button', { name: 'Export' }).click({ force: true });
  await page.waitForTimeout(800);
  const menu = root.locator('[role="menu"]');
  await menu.waitFor({ state: 'visible', timeout: 35000 });
  let pdf = menu.getByRole('button', { name: /pdf/i });
  if ((await pdf.count()) === 0) pdf = menu.getByRole('button').last();
  const [download] = await Promise.all([
    page.waitForEvent('download', { timeout: 300000 }),
    pdf.click({ force: true, timeout: 180000 }),
  ]);
  const name = download.suggestedFilename().replace(/[\\/:*?"<>|]/g, '-');
  await download.saveAs(base + name);
  return { saved: base + name };
}
```

Notes:

- If the menu is nested, perform **two** steps: open menu (`click`), then `waitForEvent('download')` + click PDF in a second `browser_run_code` or use `browser_click` between steps with fresh snapshots.
- If `waitForEvent` times out, re-snapshot: labels vary (**Export to PDF**, **Download PDF**, localized text).

## If MCP download path is restricted

Some environments save to a default downloads directory. If `saveAs` fails or file appears elsewhere:

1. Search the MCP/browser documentation or default download directory for the newest `.pdf`.
2. Move the file into `<repo>/<project_folder>/` using shell commands in the workspace.

## De-duplication

Before saving, list existing `*.pdf` in the target folder. If a file with the same name exists, compare size or append `_2`, `_3` before `.pdf`.

## After each successful PDF

1. Run the local helper (from repo root):  
   `uv run python scripts/sync_chatgpt_deep_research_pdfs.py record --conversation-id <uuid> --folder <folder> --outcome downloaded --pdf-filename "<file>.pdf"`  
   Use `conv-id` subcommand on the thread URL if you need the UUID.
2. Refresh the folder README table: `uv run python scripts/sync_chatgpt_deep_research_pdfs.py update-readmes --only <folder>` (or `update-readmes` for all).
3. Keep human-readable **title** and **project** notes for the README index skill if you edit prose manually.
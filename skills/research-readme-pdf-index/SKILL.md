---

## name: research-readme-pdf-index
description: >-
  Maintains README.md files that index Deep Research PDFs per folder. Use when
  updating project folders after syncing ChatGPT PDFs into this repository.

# Research repo: README PDF index

## Which README to edit

- **Per project folder**: `<repo>/<project_folder>/README.md` — required index of PDFs in that folder.
- **Root** `README.md`: optional; update only if the set of project folders or the repo description should change.

## Folder naming

Match ChatGPT **project display name** to a single directory under the repo root:

1. Trim leading/trailing whitespace.
2. Replace characters `\ / : * ? " < > |` with `-`.
3. Collapse multiple `-` into one.
4. On Windows, strip trailing `.` and spaces from the folder name.
5. If the folder already exists with different casing, normalize to the existing directory name on disk to avoid duplicates.

## README structure for a project folder

Use this template (keep sections in this order unless the file already has a longer introduction—then insert **Deep research PDF index** after the intro).

```markdown
# <Project display name>

Short description of the project (optional).

## Deep research PDF index

| PDF file | Title / topic | Last synced (approx.) |
|----------|---------------|------------------------|
| `example-report.pdf` | Example title from thread or heading | 2026-04-06 |

## Other notes

(Optional) Links to related markdown notes in this folder.
```

Rules:

- One table row per `.pdf` in the same directory as the README.
- **PDF file** column: backtick-wrapped filename only (not full path).
- **Title / topic**: prefer ChatGPT thread title; else first heading inside the report; else filename stem.
- **Last synced**: ISO date `YYYY-MM-DD` from user_info or local date when the agent ran.
- Sort rows alphabetically by PDF filename unless the human prefers chronological (then sort by sync date descending and state that in a one-line note).

## Updating an existing README

1. Read the current `README.md`.
2. If a `## Deep research PDF index` section exists, replace the table **body** to match **actual** `*.pdf` files currently in the folder (scan the directory).
3. If the section is missing, add it before any generic placeholder content, or merge with existing “Key Reports” lists by moving PDF-specific rows into the table.
4. Do not remove unrelated markdown the user cares about unless asked; prefer **adding** the index section.

## Consistency check

After editing, the folder should satisfy:

- Every `*.pdf` has a table row.
- Every table row references a file that exists on disk


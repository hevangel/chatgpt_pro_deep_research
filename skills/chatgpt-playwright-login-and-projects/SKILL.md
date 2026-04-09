---

## name: chatgpt-playwright-login-and-projects
description: >-
  Opens ChatGPT in Playwright, handles login handoff, and enumerates Projects
  from the sidebar. Use when syncing ChatGPT Deep Research PDFs or navigating
  ChatGPT Projects with the user-playwright MCP.

# ChatGPT: Playwright session and Projects

## Preconditions

- Playwright MCP is available (`browser_navigate`, `browser_snapshot`, `browser_click`, etc.).
- The human can complete authentication if the session is not already logged in.

## Open ChatGPT

1. `browser_navigate` to `https://chatgpt.com` (fallback: `https://chat.openai.com` if redirected or region-specific).
2. `browser_wait_for` a short settle (e.g. 2–3s) if the UI is still hydrating.
3. `browser_snapshot` and inspect for:
  - Logged-in home (sidebar, new chat, project list).
  - Login or interstitial (email, Google, Microsoft, etc.).

## Login handoff

If not logged in:

1. Tell the human to complete sign-in and any 2FA in the automated browser window.
2. Poll with `browser_snapshot` until the main logged-in layout appears.
3. Do not record credentials, cookies, or tokens in git or chat logs beyond what the MCP already manages.

## Find Projects in the UI

ChatGPT’s exact DOM changes often. **Do not rely on brittle CSS selectors** unless verified from the current snapshot.

1. In the snapshot, locate the **sidebar** region and labels such as **Projects**, **Project**, or a list of user-defined project names.
2. If projects are collapsed, click the disclosure control (chevron or “Projects” header) from the snapshot `ref`, then take a **fresh** `browser_snapshot`.
3. Enumerate **every project name** visible. If the list scrolls:
  - Scroll the sidebar container (`browser_run_code` or UI scroll) and re-snapshot until no new names appear.
4. Output a numbered list for the orchestrating agent: `project_display_name → planned repo folder name` (apply sanitization from `AGENTS.md` or from the README index skill).

## Open a project

1. Click the project entry from the latest snapshot (use the element `ref`).
2. After navigation or pane change, `browser_snapshot` again.
3. Confirm you are inside that project (title in header, filtered thread list, or project-specific empty state).

## Failure modes

- **No Projects section**: snapshot shows layout without projects—ask the human whether they use Projects or only library chats; may need different navigation (e.g. “Library”, search).
- **Stale refs**: always use refs from the **most recent** snapshot after any action.
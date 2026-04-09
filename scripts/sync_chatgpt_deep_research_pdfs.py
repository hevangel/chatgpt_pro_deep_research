"""
Local helpers for ChatGPT Deep Research PDFs in this repo.

PDF export is done by the human or by an agent using the user-playwright MCP
(browser_snapshot, browser_click, browser_run_code, etc.), not by this script.

This CLI updates deep-research-download-log.json, rescans on-disk PDFs, refreshes
README tables, and offers small utilities (conversation id from URL, title match).

Usage (from repo root):
    uv run python scripts/sync_chatgpt_deep_research_pdfs.py inventory
    uv run python scripts/sync_chatgpt_deep_research_pdfs.py update-readmes
    uv run python scripts/sync_chatgpt_deep_research_pdfs.py update-readmes --only engineering
    uv run python scripts/sync_chatgpt_deep_research_pdfs.py record --conversation-id <uuid> \\
        --folder engineering --outcome downloaded --pdf-filename "Report.pdf"
    uv run python scripts/sync_chatgpt_deep_research_pdfs.py conv-id "https://chatgpt.com/.../c/<uuid>"
    uv run python scripts/sync_chatgpt_deep_research_pdfs.py match-title --folder engineering --title "Some title"
    uv run python scripts/sync_chatgpt_deep_research_pdfs.py projects
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_LOG_PATH = REPO_ROOT / "deep-research-download-log.json"
LEGACY_STATE_PATH = REPO_ROOT / ".deep-research-sync-state.json"

SKIP_OUTCOMES = frozenset(
    {"downloaded", "skipped_no_deep_research", "legacy_import"},
)
RECORD_OUTCOMES = frozenset(
    {
        "downloaded",
        "skipped_no_deep_research",
        "export_timeout",
        "error",
        "legacy_import",
    },
)


def _configure_stdio_utf8() -> None:
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_log_structure(raw: dict) -> dict:
    raw.setdefault("schema_version", 1)
    raw.setdefault("last_run", {})
    raw.setdefault("conversations", {})
    raw.setdefault("pdf_inventory", {})
    if not isinstance(raw["conversations"], dict):
        raw["conversations"] = {}
    return raw


def refresh_pdf_inventory(log: dict) -> None:
    """Scan project folders for *.pdf (not .playwright-mcp) and store in log."""
    ts = _utc_now_iso()
    items: list[dict] = []
    for proj in PROJECTS:
        d = REPO_ROOT / proj.folder
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.pdf")):
            rel = p.relative_to(REPO_ROOT).as_posix()
            items.append(
                {
                    "relative_path": rel,
                    "project_folder": proj.folder,
                    "pdf_filename": p.name,
                    "bytes": p.stat().st_size,
                    "indexed_at": ts,
                }
            )
    log["pdf_inventory"] = {
        "indexed_at": ts,
        "item_count": len(items),
        "items": items,
        "note": "Project folders only; excludes .playwright-mcp and other paths.",
    }


def normalize_title_for_match(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def match_pdf_on_disk(out_dir: Path, report_title: str) -> str | None:
    """Return existing PDF filename if report title matches a file on disk."""
    if not report_title or len(report_title.strip()) < 4:
        return None
    tn = normalize_title_for_match(report_title)
    candidates = list(out_dir.glob("*.pdf"))
    if not candidates:
        return None
    stems = [(p.name, normalize_title_for_match(p.stem)) for p in candidates]
    stem_texts = [s[1] for s in stems if s[1]]
    if not stem_texts:
        return None
    close = difflib.get_close_matches(tn, stem_texts, n=1, cutoff=0.72)
    if close:
        for name, sn in stems:
            if sn == close[0]:
                return name
    for name, sn in stems:
        if len(tn) >= 16 and (tn[:24] in sn or sn[:24] in tn):
            return name
    return None


def load_log() -> dict:
    if DOWNLOAD_LOG_PATH.is_file():
        raw = json.loads(DOWNLOAD_LOG_PATH.read_text(encoding="utf-8"))
        return ensure_log_structure(raw)
    conversations: dict = {}
    if LEGACY_STATE_PATH.is_file():
        old = json.loads(LEGACY_STATE_PATH.read_text(encoding="utf-8"))
        ts = _utc_now_iso()
        for cid in old.get("completed_ids", []):
            conversations[cid] = {
                "outcome": "legacy_import",
                "note": "Imported from .deep-research-sync-state.json; delete entry to reprocess.",
                "updated_at": ts,
            }
    return {
        "schema_version": 1,
        "last_run": {},
        "conversations": conversations,
    }


def save_log(data: dict) -> None:
    DOWNLOAD_LOG_PATH.write_text(
        json.dumps(data, indent=2, sort_keys=False),
        encoding="utf-8",
    )


def should_skip_conversation(log: dict, conversation_id: str) -> bool:
    rec = log["conversations"].get(conversation_id)
    if not rec:
        return False
    return rec.get("outcome") in SKIP_OUTCOMES


def record_conversation(
    log: dict,
    conversation_id: str,
    project_folder: str,
    outcome: str,
    **fields: object,
) -> None:
    entry = {
        "outcome": outcome,
        "project_folder": project_folder,
        "updated_at": _utc_now_iso(),
        **fields,
    }
    log["conversations"][conversation_id] = entry
    save_log(log)


@dataclass(frozen=True)
class ProjectConfig:
    folder: str
    slug: str


PROJECTS: list[ProjectConfig] = [
    ProjectConfig("engineering", "g-p-6910100b17ac819181e66c047f880ffb-engineering"),
    ProjectConfig("philosophy", "g-p-694826876454819180f7af3d6b0defbf-philosophy"),
    ProjectConfig("investing", "g-p-69116408c2888191a9b33bfa3251b99d-investing"),
    ProjectConfig("random_thoughts", "g-p-693dd6071c2c8191a3549a4489cbaf77-random-ideas"),
    ProjectConfig("寫文", "g-p-69115f2b41fc8191b1f4ee09a66c4ca6-xie-wen"),
]

SLUG_TO_FOLDER: dict[str, str] = {p.slug: p.folder for p in PROJECTS}


def sanitize_filename(name: str) -> str:
    for c in '\\/:*?"<>|':
        name = name.replace(c, "-")
    return name.strip()


def conv_id_from_url(url: str) -> str:
    m = re.search(r"/c/([a-f0-9-]{36})$", url.split("?")[0].rstrip("/"))
    if not m:
        raise ValueError(f"bad conversation url: {url}")
    return m.group(1)


def update_readme_pdf_table(folder: Path, sync_date: str) -> None:
    readme = folder / "README.md"
    if not readme.is_file():
        return
    lines = readme.read_text(encoding="utf-8").splitlines(keepends=True)
    out: list[str] = []
    i = 0
    pdfs = sorted(folder.glob("*.pdf"))
    while i < len(lines):
        line = lines[i]
        if line.rstrip("\n\r") == "## Deep research PDF index":
            out.append(line)
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if nxt.startswith("## ") and not nxt.startswith("###"):
                    break
                i += 1
            out.append("\n")
            out.append("| PDF file | Title / topic | Last synced (approx.) |\n")
            out.append("|----------|---------------|------------------------|\n")
            if not pdfs:
                out.append("| *(none yet)* | | |\n")
            else:
                for p in pdfs:
                    stem = p.stem.replace("_", " ")
                    out.append(f"| `{p.name}` | {stem} | {sync_date} |\n")
            out.append("\n")
            continue
        out.append(line)
        i += 1
    readme.write_text("".join(out), encoding="utf-8")


def cmd_inventory(_args: argparse.Namespace) -> int:
    log = load_log()
    started = _utc_now_iso()
    refresh_pdf_inventory(log)
    n = log.get("pdf_inventory", {}).get("item_count", 0)
    log["last_run"] = {
        "started_at": started,
        "finished_at": _utc_now_iso(),
        "helper_command": "inventory",
    }
    save_log(log)
    print(f"Wrote {DOWNLOAD_LOG_PATH} with pdf_inventory ({n} files).")
    return 0


def cmd_update_readmes(args: argparse.Namespace) -> int:
    log = load_log()
    started = _utc_now_iso()
    sync_date = args.date or date.today().isoformat()
    projects = PROJECTS
    if args.only:
        projects = [p for p in PROJECTS if p.folder == args.only]
        if not projects:
            print(f"Unknown project folder: {args.only}", file=sys.stderr)
            return 2
    for proj in projects:
        update_readme_pdf_table(REPO_ROOT / proj.folder, sync_date)
    refresh_pdf_inventory(log)
    log["last_run"] = {
        "started_at": started,
        "finished_at": _utc_now_iso(),
        "helper_command": "update-readmes",
        "only_folder": args.only,
    }
    save_log(log)
    print("README PDF indexes updated where README.md exists.")
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    cid = args.conversation_id.strip()
    if len(cid) != 36:
        print("conversation-id must be a 36-char UUID", file=sys.stderr)
        return 2
    outcome = args.outcome
    if outcome not in RECORD_OUTCOMES:
        print(f"outcome must be one of: {sorted(RECORD_OUTCOMES)}", file=sys.stderr)
        return 2
    if outcome == "downloaded" and not args.pdf_filename:
        print("--pdf-filename is required when outcome is downloaded", file=sys.stderr)
        return 2
    folder = args.folder
    if not any(p.folder == folder for p in PROJECTS):
        print(
            f"Unknown folder {folder!r}; expected one of: {[p.folder for p in PROJECTS]}",
            file=sys.stderr,
        )
        return 2

    log = load_log()
    fields: dict[str, object] = {}
    if args.detail:
        fields["detail"] = args.detail
    if args.note:
        fields["note"] = args.note
    if outcome == "downloaded":
        name = sanitize_filename(args.pdf_filename)
        fields["pdf_filename"] = name
        fields["pdf_relative_path"] = f"{folder}/{name}"
    record_conversation(log, cid, folder, outcome, **fields)
    refresh_pdf_inventory(log)
    save_log(log)
    print(f"Recorded {cid} -> {outcome} ({folder})")
    return 0


def cmd_conv_id(args: argparse.Namespace) -> int:
    try:
        print(conv_id_from_url(args.url.strip()))
        return 0
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2


def cmd_match_title(args: argparse.Namespace) -> int:
    folder = args.folder
    if not any(p.folder == folder for p in PROJECTS):
        print(
            f"Unknown folder {folder!r}; expected one of: {[p.folder for p in PROJECTS]}",
            file=sys.stderr,
        )
        return 2
    out_dir = REPO_ROOT / folder
    hit = match_pdf_on_disk(out_dir, args.title)
    if not hit:
        print("(no close PDF filename match)", file=sys.stderr)
        return 1
    print(hit)
    return 0


def cmd_projects(args: argparse.Namespace) -> int:
    rows = [{"folder": p.folder, "slug": p.slug} for p in PROJECTS]
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0
    for p in PROJECTS:
        print(f"{p.folder}\t{p.slug}")
    return 0


def cmd_resolve_slug(args: argparse.Namespace) -> int:
    slug = args.slug.strip()
    hit = SLUG_TO_FOLDER.get(slug)
    if not hit:
        print(f"Unknown slug (not in PROJECTS): {slug}", file=sys.stderr)
        return 2
    print(hit)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_inv = sub.add_parser("inventory", help="Scan project folders; refresh pdf_inventory in the log.")
    p_inv.set_defaults(func=cmd_inventory)

    p_rm = sub.add_parser("update-readmes", help="Rewrite ## Deep research PDF index in each README.md.")
    p_rm.add_argument(
        "--only",
        metavar="FOLDER",
        help="Only this project folder (e.g. engineering, 寫文)",
    )
    p_rm.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="Date column in the table (default: today)",
    )
    p_rm.set_defaults(func=cmd_update_readmes)

    p_rec = sub.add_parser("record", help="Append/update one conversation row in the download log.")
    p_rec.add_argument("--conversation-id", required=True, help="ChatGPT conversation UUID")
    p_rec.add_argument(
        "--folder",
        required=True,
        help="Repo folder name (e.g. engineering, investing, 寫文)",
    )
    p_rec.add_argument(
        "--outcome",
        required=True,
        choices=sorted(RECORD_OUTCOMES),
    )
    p_rec.add_argument(
        "--pdf-filename",
        help="Required if outcome is downloaded (as saved under the project folder)",
    )
    p_rec.add_argument("--detail", help="Optional short error/timeout message")
    p_rec.add_argument("--note", help="Optional note")
    p_rec.set_defaults(func=cmd_record)

    p_cid = sub.add_parser("conv-id", help="Print conversation UUID from a chatgpt.com .../c/<uuid> URL.")
    p_cid.add_argument("url")
    p_cid.set_defaults(func=cmd_conv_id)

    p_mt = sub.add_parser(
        "match-title",
        help="Print an existing PDF filename if report title fuzzy-matches a file stem (skip re-download).",
    )
    p_mt.add_argument("--folder", required=True)
    p_mt.add_argument("--title", required=True)
    p_mt.set_defaults(func=cmd_match_title)

    p_pr = sub.add_parser("projects", help="List configured folder names and ChatGPT project slugs.")
    p_pr.add_argument("--json", action="store_true", help="JSON array instead of TSV lines")
    p_pr.set_defaults(func=cmd_projects)

    p_rs = sub.add_parser("resolve-slug", help="Print repo folder name for a g-p-... ChatGPT slug.")
    p_rs.add_argument("slug")
    p_rs.set_defaults(func=cmd_resolve_slug)

    return parser


def main() -> None:
    _configure_stdio_utf8()
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()

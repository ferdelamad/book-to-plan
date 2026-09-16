#!/usr/bin/env python3
"""Scan book-to-plan files for commitments that have come due.

A plan file is Markdown and stays hand-editable; this reads it without
owning it. Chapter blocks start with `## Ch <N> — <title>` and carry
`**Status:**` and `**Review on:**` lines.

Usage:
  due.py [paths...]            report due commitments (default: cwd)
  due.py --notify [paths...]   also fire one macOS notification
  due.py --json [paths...]     machine-readable output
  due.py --lint [paths...]     check plans for inconsistencies
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

OPEN_STATES = {"committed"}  # "due" is derived from the date, never stored
KNOWN_STATES = {"committed", "done", "partial", "skipped", "dropped"}
RESOLVED_STATES = {"done", "partial"}
CHAPTER_RE = re.compile(r"^##\s+Ch\s+([\w.]+)\s*[—-]\s*(.+?)\s*$", re.M)
# A field value runs until the next bold field, the next heading, or a blank
# line followed by either — plan files are hand-wrapped, so values span lines.
def _field(name: str) -> re.Pattern:
    return re.compile(
        rf"^\*\*{name}:\*\*[ \t]*(.*?)(?=\n\s*\n|\n\*\*|\n#{{2,3}} |\Z)",
        re.M | re.S)


FIELD_RE = {
    "status": re.compile(r"^\*\*Status:\*\*\s*(\S+)", re.M),
    "review": re.compile(r"^\*\*Review on:\*\*\s*(\d{4}-\d{2}-\d{2})", re.M),
    "commitment": _field("Commitment"),
    "takeaway": _field("Takeaway"),
}
CHAPTERS_RE = re.compile(r"^chapters:\s*(\d+)\s*/\s*(\d+)", re.M)
BOOK_RE = re.compile(r"^book:\s*(.+?)\s*$", re.M)


def parse_plan(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    if "**Commitment:**" not in text:
        return None  # not a plan file

    book_match = BOOK_RE.search(text)
    book = book_match.group(1) if book_match else os.path.basename(path)

    # Split on chapter headings, keeping each block with its heading.
    bounds = [(m.start(), m.group(1), m.group(2)) for m in CHAPTER_RE.finditer(text)]
    chapters = []
    for i, (start, num, title) in enumerate(bounds):
        end = bounds[i + 1][0] if i + 1 < len(bounds) else len(text)
        block = text[start:end]
        has_log = "### Log" in block
        fields = {}
        for key, rx in FIELD_RE.items():
            m = rx.search(block)
            fields[key] = " ".join(m.group(1).split()) if m else None
        chapters.append({"chapter": num, "title": title,
                         "has_log": has_log, **fields})
    counts = CHAPTERS_RE.search(text)
    return {"path": path, "book": book, "chapters": chapters,
            "counts": (int(counts.group(1)), int(counts.group(2)))
                      if counts else None}


def collect(paths: list[str]) -> list[str]:
    found: list[str] = []
    for p in paths or ["."]:
        if os.path.isdir(p):
            found += sorted(glob.glob(os.path.join(p, "**", "*-plan.md"),
                                      recursive=True))
        elif os.path.isfile(p):
            found.append(p)
    return found


def lint(paths: list[str]) -> int:
    """Check that hand-edited plans still say what they mean."""
    problems: list[str] = []
    for path in collect(paths):
        plan = parse_plan(path)
        if not plan:
            continue

        def flag(ch: dict, msg: str) -> None:
            problems.append(f"{path}: Ch {ch['chapter']} — {msg}")

        for ch in plan["chapters"]:
            state = (ch["status"] or "").lower()
            if not state:
                flag(ch, "no Status")
            elif state not in KNOWN_STATES:
                flag(ch, f"unknown Status {ch['status']!r} "
                         f"(expected one of {', '.join(sorted(KNOWN_STATES))})")
            if state in RESOLVED_STATES:
                if not ch["takeaway"]:
                    flag(ch, f"{state} but no Takeaway — the takeaway is "
                             "written after the action, and it is the point")
            if ch["commitment"] and not ch["review"] and state in OPEN_STATES:
                flag(ch, "commitment with no Review on — an intention, "
                         "not a commitment")
            if ch["review"] and not ch["commitment"]:
                flag(ch, "Review on with no Commitment")
            if not ch["has_log"]:
                flag(ch, "no ### Log section — state changes go unrecorded")

        # `chapters: N / M` counts chapters worked through, not commitments
        # completed — progress through the book must not go down when a
        # commitment is skipped.
        worked = len(plan["chapters"])
        if plan["counts"] and plan["counts"][0] != worked:
            problems.append(
                f"{path}: frontmatter says {plan['counts'][0]} chapter(s) "
                f"worked through but {worked} chapter block(s) exist")

    if not problems:
        print("All plans consistent.")
        return 0
    print(f"{len(problems)} problem(s):\n")
    for item in problems:
        print(f"  {item}")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--notify", action="store_true")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--today", default=None, help="override date (testing)")
    ap.add_argument("--lint", action="store_true",
                    help="check plan files for inconsistencies")
    args = ap.parse_args()

    if args.lint:
        return lint(args.paths)

    today = args.today or dt.date.today().isoformat()
    due, upcoming, undated = [], [], []

    for path in collect(args.paths):
        plan = parse_plan(path)
        if not plan:
            continue
        for ch in plan["chapters"]:
            if (ch["status"] or "").lower() not in OPEN_STATES:
                continue
            row = {"book": plan["book"], "path": path, **ch}
            if not ch["review"]:
                undated.append(row)
            elif ch["review"] <= today:
                due.append(row)
            else:
                upcoming.append(row)

    due.sort(key=lambda r: r["review"])

    if args.as_json:
        print(json.dumps({"today": today, "due": due,
                          "upcoming": upcoming, "undated": undated},
                         indent=2))
        return 1 if (due or undated) else 0  # same signal as text mode

    def report_undated() -> None:
        if not undated:
            return
        print(f"{len(undated)} commitment(s) with no review date "
              f"(an intention, not yet a commitment):\n")
        for r in undated:
            print(f"  [unscheduled] {r['book']} — Ch {r['chapter']}: {r['title']}")
            print(f"     {r['commitment']}")
            print(f"     {r['path']}\n")

    if not due:
        n = len(upcoming)
        nxt = min((u["review"] for u in upcoming), default=None)
        print(f"Nothing due as of {today}."
              + (f" {n} commitment(s) open, next review {nxt}." if n else ""))
        print()
        report_undated()
        return 1 if undated else 0

    print(f"{len(due)} commitment(s) due as of {today}:\n")
    for r in due:
        overdue = (dt.date.fromisoformat(today)
                   - dt.date.fromisoformat(r["review"])).days
        age = "due today" if overdue == 0 else f"{overdue}d overdue"
        print(f"  [{age}] {r['book']} — Ch {r['chapter']}: {r['title']}")
        print(f"     {r['commitment']}")
        print(f"     {r['path']}\n")

    report_undated()

    if args.notify:
        first = due[0]
        others = len(due) - 1 + len(undated)
        extra = f" (+{others} more)" if others else ""
        body = f"Ch {first['chapter']}: {first['commitment']}"[:160] + extra
        # Pass text as argv rather than interpolating it into the script:
        # commitments contain em dashes, quotes and apostrophes, and any
        # escaping scheme that survives both the shell and AppleScript is a
        # bug waiting to happen.
        script = (
            "on run {body, ttl, sub}\n"
            "  display notification body with title ttl subtitle sub"
            ' sound name "Ping"\n'
            "end run"
        )
        subprocess.run(
            ["osascript", "-e", script, body, "book-to-plan",
             first["book"][:60]],
            check=False)

    return 1  # non-zero signals "action needed", useful in shell pipelines


if __name__ == "__main__":
    sys.exit(main())

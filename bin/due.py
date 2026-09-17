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
  due.py --deep [paths...]     recurse fully (default: one level down)
  due.py --stale-after N       days a commitment waits before its plan
                               reads as stale (default 14, 0 disables)
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
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---", re.S)
UPDATED_RE = re.compile(r"^updated:\s*(\d{4}-\d{2}-\d{2})", re.M)
PLAN_STATUS_RE = re.compile(r"^status:\s*(\S+)", re.M)

# How long a commitment can sit past its review date, with nobody coming
# back to the plan, before the silence is the thing worth reporting. Two
# weeks is past the point where another overdue count tells the reader
# anything they do not already know.
STALE_AFTER_DAYS = 14
DORMANT_PLAN_STATES = {"completed", "abandoned"}


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
    # `updated` and `status` are frontmatter-only: a chapter carries its own
    # **Status:** line, and searching the whole file would pick that up.
    fm = FRONTMATTER_RE.match(text)
    head = fm.group(1) if fm else ""
    updated = UPDATED_RE.search(head)
    plan_status = PLAN_STATUS_RE.search(head)
    return {"path": path, "book": book, "chapters": chapters,
            "updated": updated.group(1) if updated else None,
            "status": plan_status.group(1).lower() if plan_status else None,
            "counts": (int(counts.group(1)), int(counts.group(2)))
                      if counts else None}


def stale_entry(plan: dict, open_rows: list[dict], today: str,
                threshold: int) -> dict | None:
    """A plan the reader has stopped coming back to.

    Not "the file is old": a commitment reviewed three weeks out leaves the
    file untouched for three weeks and nothing is wrong. Stale means the plan
    asked for the reader on some date, they did not come, and that was
    `threshold` days ago — measured from the oldest waiting commitment, and
    only while the plan has not been edited since that date.

    At that point another overdue count is telling them what they already
    know. How long they have been gone is the thing they do not.

    Silent when the plan is finished, when nothing is open, or when there is
    no `updated:` to measure against; the linter reports that last case
    rather than this guessing at it.
    """
    if threshold <= 0 or not open_rows or not plan["updated"]:
        return None
    if plan["status"] in DORMANT_PLAN_STATES:
        return None

    overdue = sorted(r["review"] for r in open_rows
                     if r["review"] and r["review"] <= today)
    if overdue:
        waiting_since = overdue[0]
    elif any(not r["review"] for r in open_rows):
        # An intention nobody ever dated waits from the last edit instead.
        waiting_since = plan["updated"]
    else:
        return None  # everything open is still ahead of its review date

    if plan["updated"] > waiting_since:
        return None  # they have been back since it came due

    try:
        days = (dt.date.fromisoformat(today)
                - dt.date.fromisoformat(waiting_since)).days
    except ValueError:
        return None
    if days < threshold:
        return None
    return {"book": plan["book"], "path": plan["path"],
            "updated": plan["updated"], "days": days,
            "open": len(open_rows),
            "oldest_review": overdue[0] if overdue else None}


def collect(paths: list[str], deep: bool = False) -> list[str]:
    """Find plan files, without walking an entire home directory.

    A directory is searched at its own level and one level down, which
    covers `~/book-plans` and a repo with plans in a subfolder. `--deep`
    opts into full recursion for anyone who has filed them deeper.
    """
    patterns = ["*-plan.md", os.path.join("*", "*-plan.md")]
    if deep:
        patterns = [os.path.join("**", "*-plan.md")]
    found: list[str] = []
    for p in paths or ["."]:
        if os.path.isdir(p):
            for pattern in patterns:
                found += glob.glob(os.path.join(p, pattern), recursive=deep)
        elif os.path.isfile(p):
            found.append(p)
    # Same plan reachable by two paths should be reported once.
    seen: dict[str, str] = {}
    for f in found:
        seen.setdefault(os.path.realpath(f), f)
    return sorted(seen.values())


def lint(paths: list[str], deep: bool = False) -> int:
    """Check that hand-edited plans still say what they mean."""
    problems: list[str] = []
    for path in collect(paths, deep):
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

        if not plan["updated"] and any(
                (ch["status"] or "").lower() in OPEN_STATES
                for ch in plan["chapters"]):
            problems.append(
                f"{path}: no `updated:` in frontmatter — a plan with open "
                "commitments needs one, or going quiet cannot be detected")

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
    ap.add_argument("--deep", action="store_true",
                    help="recurse fully instead of one level down")
    ap.add_argument("--stale-after", type=int, default=STALE_AFTER_DAYS,
                    metavar="N", dest="stale_after",
                    help="days a commitment waits before its plan reads as "
                         f"stale (default {STALE_AFTER_DAYS}, 0 disables)")
    args = ap.parse_args()

    if args.lint:
        return lint(args.paths, args.deep)

    today = args.today or dt.date.today().isoformat()
    due, upcoming, undated, stale = [], [], [], []

    for path in collect(args.paths, args.deep):
        plan = parse_plan(path)
        if not plan:
            continue
        open_rows = []
        for ch in plan["chapters"]:
            if (ch["status"] or "").lower() not in OPEN_STATES:
                continue
            row = {"book": plan["book"], "path": path, **ch}
            open_rows.append(row)
            if not ch["review"]:
                undated.append(row)
            elif ch["review"] <= today:
                due.append(row)
            else:
                upcoming.append(row)
        entry = stale_entry(plan, open_rows, today, args.stale_after)
        if entry:
            stale.append(entry)

    due.sort(key=lambda r: r["review"])
    stale.sort(key=lambda s: -s["days"])

    if args.as_json:
        print(json.dumps({"today": today, "due": due, "upcoming": upcoming,
                          "undated": undated, "stale": stale}, indent=2))
        return 1 if (due or undated or stale) else 0  # as in text mode

    # A stale plan speaks for its own commitments: listing them again under
    # a day count is the noise that made the reader stop looking.
    quiet = {s["path"] for s in stale}
    visible_due = [r for r in due if r["path"] not in quiet]
    visible_undated = [r for r in undated if r["path"] not in quiet]

    def report_undated() -> None:
        if not visible_undated:
            return
        print(f"{len(visible_undated)} commitment(s) with no review date "
              f"(an intention, not yet a commitment):\n")
        for r in visible_undated:
            print(f"  [unscheduled] {r['book']} — Ch {r['chapter']}: {r['title']}")
            print(f"     {r['commitment']}")
            print(f"     {r['path']}\n")

    def report_stale() -> None:
        if not stale:
            return
        print(f"{len(stale)} plan(s) gone quiet:\n")
        for s in stale:
            print(f"  [stale] {s['book']} — waiting {s['days']} days, "
                  f"last touched {s['updated']}")
            detail = f"     {s['open']} commitment(s) still open"
            if s["oldest_review"]:
                detail += f", oldest review was due {s['oldest_review']}"
            print(detail + ".")
            print("     Counting the days late stopped being useful here. "
                  "The honest options are")
            print("     to restart the plan, drop it, or revisit the week "
                  "shape it was built for.")
            print(f"     {s['path']}\n")

    def notify() -> None:
        """One notification, for the single most useful thing to say."""
        if stale:
            # Waking someone at nine to say a commitment is 37 days overdue
            # tells them nothing. That the plan has gone quiet is the message.
            s = stale[0]
            others = len(stale) - 1
            book = s["book"]
            body = (f"Waiting {s['days']} days, {s['open']} still open. "
                    "Restart it, drop it, or revisit the week shape.")
        elif due:
            first = due[0]
            others = len(due) - 1 + len(undated)
            book = first["book"]
            body = f"Ch {first['chapter']}: {first['commitment']}"[:160]
        else:
            return
        if others:
            body += f" (+{others} more)"
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
            ["osascript", "-e", script, body, "book-to-plan", book[:60]],
            check=False)

    report_stale()

    if visible_due:
        print(f"{len(visible_due)} commitment(s) due as of {today}:\n")
        for r in visible_due:
            overdue = (dt.date.fromisoformat(today)
                       - dt.date.fromisoformat(r["review"])).days
            age = "due today" if overdue == 0 else f"{overdue}d overdue"
            print(f"  [{age}] {r['book']} — Ch {r['chapter']}: {r['title']}")
            print(f"     {r['commitment']}")
            print(f"     {r['path']}\n")
    elif not stale:
        n = len(upcoming)
        nxt = min((u["review"] for u in upcoming), default=None)
        print(f"Nothing due as of {today}."
              + (f" {n} commitment(s) open, next review {nxt}." if n else ""))
        print()

    report_undated()

    if args.notify:
        notify()

    # non-zero signals "action needed", useful in shell pipelines
    return 1 if (due or undated or stale) else 0


if __name__ == "__main__":
    sys.exit(main())

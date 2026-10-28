#!/usr/bin/env python3
"""Where each goal stands, kept by the business (`/done`, one word per goal).

WHY THIS EXISTS
    The Self as Code standard 6.2 and ADR-136 Rule 3: the owner's plan sends a
    goal down with an id, the business keeps one row per id in goals.md, and
    only the status and its date go back up. Until 28 October 2026 nothing on
    the business side ever asked for that status, so a goal seeded 'not
    started' stayed so for good, and the owner's check-in read true but never
    read progress. This is the business's moment: at /done, once a goal's
    last word is a week old, the session asks for one word and writes it here.

WHAT IT DOES
    show    Every goal in context-core/strategic-identity/**/goals.md: id,
            status, date, days since.
    due     The goals whose last word is --days old or more (7 by default),
            not done and not dropped, each with what this repo saved since:
            how many commits and the last date. Says so when nothing is due.
    set     One goal's status and today's date, nothing else:
            `set <id> <status>`. Status is one of the five. The statement is
            never edited here; it changes in the owner's plan and is sent
            again.

WHAT NEVER HAPPENS
    Nothing is committed here; /done saves goals.md with the rest. Nothing is
    read from, or written to, the owner's private repo. Only Status and
    Updated ever change, and only on the row named.

Usage:
    python3 scripts/oac-goals.py show [--json]
    python3 scripts/oac-goals.py due [--days 7] [--json] [--quiet]
    python3 scripts/oac-goals.py set <goal id> "<status>"
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

BASE = Path("context-core") / "strategic-identity"
GOALS = "goals.md"
# The same three as self-as-code-split.py and the session brief, which read
# what this writes. The split does not ship in a business pack, so they live
# here too; test_oac_goals.py keeps the three readers agreeing.
GOAL_RE = re.compile(r"\[goal:\s*([^\]]+)\]")
STATUSES = ("not started", "on track", "at risk", "done", "dropped")
CLOSED = ("done", "dropped")
SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|$")
UPDATED_RE = re.compile(r"^updated:.*$", re.M)
DEFAULT_DAYS = 7


class Row(NamedTuple):
    file: Path
    line: int
    gid: str
    cell: str        # the Goal cell as written, id and statement
    status: str
    updated: str


def fail(msg: str, code: int = 2) -> None:
    print(f"oac-goals: {msg}", file=sys.stderr)
    raise SystemExit(code)


def goal_files(root: Path) -> list[Path]:
    base = root / BASE
    if not base.is_dir():
        return []
    return [f for f in [base / GOALS, *sorted(base.glob(f"*/{GOALS}"))] if f.is_file()]


def rows(root: Path) -> list[Row]:
    out: list[Row] = []
    for f in goal_files(root):
        for n, ln in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines()):
            s = ln.strip()
            if not s.startswith("|") or SEPARATOR_RE.match(s):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) < 3:
                continue
            m = GOAL_RE.search(cells[0])
            if not m:
                continue
            out.append(Row(f, n, m.group(1).strip(), cells[0], cells[1].lower(), cells[2]))
    return out


def statement(cell: str) -> str:
    return GOAL_RE.sub("", cell).strip()


def date_of(s: str) -> _dt.date | None:
    try:
        return _dt.date.fromisoformat(s.strip()[:10])
    except ValueError:
        return None


def norm_status(s: str) -> str:
    return re.sub(r"[\s_-]+", " ", s.strip().lower())


def saves_since(root: Path, day: _dt.date | None) -> tuple[int, str | None] | None:
    """Commits in this repo after `day` (the day after the last word), as a
    count and the newest date. None when this is not a git repo."""
    since = (day + _dt.timedelta(days=1)).isoformat() if day else "1970-01-01"
    try:
        r = subprocess.run(["git", "-C", str(root), "log", f"--since={since}", "--format=%cs"],
                           capture_output=True, text=True)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    dates = r.stdout.split()
    return len(dates), (dates[0] if dates else None)


def due(root: Path, days: int, today: _dt.date) -> list[dict]:
    out: list[dict] = []
    for r in rows(root):
        if r.status in CLOSED:
            continue
        d = date_of(r.updated)
        age = (today - d).days if d else None
        if d and age < days:
            continue
        ev = saves_since(root, d)
        out.append({"id": r.gid, "statement": statement(r.cell), "status": r.status, "updated": r.updated,
                    "days": age, "saves": ev[0] if ev else None, "last_save": ev[1] if ev else None,
                    "file": r.file.relative_to(root).as_posix()})
    return out


def set_status(root: Path, gid: str, status: str, today: _dt.date) -> Row:
    st = norm_status(status)
    if st not in STATUSES:
        fail(f"'{status}' is not a status. One of: {', '.join(STATUSES)}")
    all_rows = rows(root)
    found = [r for r in all_rows if r.gid == gid]
    if not found:
        known = [r.gid for r in all_rows]
        fail(f"no goal called '{gid}' here." + (f" The goals here: {', '.join(known)}" if known
                                                else " Nothing has been sent here yet."))
    r = found[0]
    lines = r.file.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    nl = "\n" if lines[r.line].endswith("\n") else ""
    lines[r.line] = f"| {r.cell} | {st} | {today.isoformat()} |{nl}"
    new = "".join(lines)
    if new.startswith("---\n"):
        end = new.find("\n---", 4)
        if end > 0:
            new = UPDATED_RE.sub(f"updated: {today.isoformat()}", new[:end], count=1) + new[end:]
    r.file.write_text(new, encoding="utf-8")
    return Row(r.file, r.line, r.gid, r.cell, st, today.isoformat())


def _days(s: str, today: _dt.date) -> str:
    d = date_of(s)
    if not d:
        return "no date"
    n = (today - d).days
    return "today" if n <= 0 else f"{n} day{'s' if n != 1 else ''}"


def print_show(root: Path, today: _dt.date, as_json: bool) -> None:
    all_rows = rows(root)
    if as_json:
        print(json.dumps([{"id": r.gid, "statement": statement(r.cell), "status": r.status, "updated": r.updated,
                           "file": r.file.relative_to(root).as_posix()} for r in all_rows], indent=2))
        return
    if not all_rows:
        print("  no goal has been sent here yet. The owner shares one from their own repo with /sac.")
        return
    print(f"  {len(all_rows)} goal{'s' if len(all_rows) != 1 else ''} here")
    w_id = max(len(r.gid) for r in all_rows) + 2
    for r in all_rows:
        print(f"  {r.gid.ljust(w_id)}{r.status.ljust(13)}{r.updated.ljust(12)}{_days(r.updated, today).ljust(10)}"
              f"{statement(r.cell)}")


def print_due(items: list[dict], days: int, as_json: bool, quiet: bool) -> None:
    if quiet:
        print(len(items))
        return
    if as_json:
        print(json.dumps(items, indent=2))
        return
    if not items:
        print(f"  every goal here has had a word in the last {days} days. Nothing to ask.")
        return
    print(f"  {len(items)} goal{'s' if len(items) != 1 else ''} with no word for {days} days or more")
    for i in items:
        when = f"on {i['updated']}, {i['days']} days ago" if i["days"] is not None else "with no date"
        if i["saves"] is None:
            saved = "saves here not counted (not a git repo)"
        elif i["saves"] == 0:
            saved = "nothing saved here since"
        else:
            saved = f"{i['saves']} save{'s' if i['saves'] != 1 else ''} here since, the last on {i['last_save']}"
        print(f"  {i['id']}   {i['statement']}")
        print(f"    last word '{i['status']}' {when}; {saved}")
        print(f"    one word: python3 scripts/oac-goals.py set {i['id']} \"<{' | '.join(STATUSES)}>\"")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Where each goal stands, kept by this business.")
    ap.add_argument("--root", default=".", help="the business's repo (default: here)")
    ap.add_argument("--today", help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show", help="every goal, its status and its date")
    s.add_argument("--json", action="store_true")
    d = sub.add_parser("due", help="the goals whose last word is a week old or more")
    d.add_argument("--days", type=int, default=DEFAULT_DAYS)
    d.add_argument("--json", action="store_true")
    d.add_argument("--quiet", action="store_true", help="the count only")
    st = sub.add_parser("set", help="one goal's status, dated today")
    st.add_argument("goal_id")
    st.add_argument("status")
    ns = ap.parse_args(argv)

    root = Path(ns.root).resolve()
    today = _dt.date.fromisoformat(ns.today) if ns.today else _dt.date.today()
    if ns.cmd == "show":
        print_show(root, today, ns.json)
    elif ns.cmd == "due":
        print_due(due(root, ns.days, today), ns.days, ns.json, ns.quiet)
    else:
        r = set_status(root, ns.goal_id, ns.status, today)
        print(f"  {r.gid}: {r.status}, {r.updated}. Written to {r.file.relative_to(root).as_posix()}; /done saves it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

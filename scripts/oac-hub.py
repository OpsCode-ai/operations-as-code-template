#!/usr/bin/env python3
"""One business repo, two laptops: the hub on GitHub, and each person's inbox.

WHY THIS EXISTS
    Two people from one business arrive with files and systems on both laptops
    (Adam, 13 Oct 2026: 'that needed to be consolidated'). The business repo
    is the hub, made on GitHub before the day. Each founder clones it, works on
    their own branch, and /done merges. Each laptop's files come in through the
    chaos step into inbox/<person>/ on that person's branch, so nothing
    collides, and file dates are kept. Spokes for staff come later, from the
    builder OpsCode's own spoke uses. The Melbourne plan, O1 item 5; ADR-122's
    install order, step 3 (chaos) and step 5 (GitHub).

VERBS
    create [--owner ORG]   Make the private repo on GitHub from this folder and
                           push main. Once, on the first laptop, after the
                           install committed.
    invite <github-user>   Add the second person with push access.
    join <owner/repo> [DIR]  The second laptop: clone the hub, make
                           team/<handle>/, switch to that person's branch.
    branch                 Today's branch for this person, <handle>/<date>,
                           made or switched to. /start and /done use it when
                           more than one person works here.
    inbox <path>...        Copy files or folders into inbox/<handle>/, dates
                           kept, the original never moved; a row goes into
                           systems/chaos.md. On main with two people, it moves
                           to today's branch first.
    who                    Who works here, the remote, the branch, the rule.

WHAT IT NEVER DOES
    Move an original. Push to main when more than one person works here. Make
    a public repo. Run without gh signed in: it says what to do instead.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

INBOX = Path("inbox")
CHAOS = Path("systems") / "chaos.md"
BIG = 95 * 1024 * 1024  # GitHub refuses a file over 100 MB; stop short of it
CHAOS_HEAD = """---
title: "Chaos: where the files were, and what came in"
type: report
audience: internal
status: active
lifecycle: living
updated: {today}
topics: [operations]
tags: [oac, chaos, inbox]
---

# Chaos: where the files were, and what came in

Every place this business's files lived, and what has been copied into the
repo so far. Copies only: the originals stay where other tools point at them.
Sort from `inbox/` into `context-core/` and `systems/` as you go; a file that
has been sorted is deleted from the inbox, never from where it came.

| Where it was | Copied to | When | Who | Still points at the original |
|---|---|---|---|---|
"""


def run(*args: str, cwd: Path | None = None, check: bool = False) -> subprocess.CompletedProcess:
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"{' '.join(args[:3])} failed:\n  {(r.stderr or r.stdout).strip()[:400]}")
    return r


def git(root: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    return run("git", "-C", str(root), *args, check=check)


def handle(root: Path) -> str:
    uj = root / ".claude" / "user.json"
    if uj.is_file():
        try:
            h = json.loads(uj.read_text(encoding="utf-8")).get("team_member", "")
            if h:
                return str(h).strip().lower()
        except ValueError:
            pass
    name = git(root, "config", "user.name").stdout.strip()
    first = re.sub(r"[^a-z0-9]+", "", name.split()[0].lower()) if name else ""
    return first or "me"


def people(root: Path) -> list[str]:
    team = root / "team"
    if not team.is_dir():
        return []
    return sorted(p.name for p in team.iterdir() if p.is_dir() and not p.name.startswith("."))


def current_branch(root: Path) -> str:
    return git(root, "branch", "--show-current").stdout.strip()


def remote_url(root: Path) -> str:
    return git(root, "remote", "get-url", "origin").stdout.strip()


def gh_ready() -> str | None:
    """None when gh is installed and signed in, else the one line to say."""
    if shutil.which("gh") is None:
        return "GitHub's command line tool (gh) is not installed. Install it in a plain terminal window: macOS `brew install gh`, Windows `winget install --id GitHub.cli`, otherwise cli.github.com. Then run this again."
    if run("gh", "auth", "status").returncode != 0:
        return "Not signed in to GitHub. In a new, plain terminal window (not this one), type `gh auth login`, choose GitHub.com, HTTPS, yes, log in with a web browser. Then run this again."
    return None


def today_branch(root: Path) -> str:
    return f"{handle(root)}/{_dt.date.today().isoformat()}"


def on_branch(root: Path) -> str:
    """Today's branch for this person, made or switched to. Returns its name."""
    want = today_branch(root)
    if current_branch(root) == want:
        return want
    if git(root, "rev-parse", "--verify", "--quiet", want).returncode == 0:
        git(root, "switch", "-q", want, check=True)
    else:
        git(root, "switch", "-q", "-c", want, check=True)
    return want


# ── create, invite, join ─────────────────────────────────────────────────────

def cmd_create(root: Path, owner: str | None) -> int:
    why = gh_ready()
    if why:
        print(why)
        return 1
    if git(root, "rev-parse", "--git-dir").returncode != 0:
        print("this folder is not a git repository yet. The install does `git init -b main` first.")
        return 1
    if remote_url(root):
        print(f"this repo already has a copy on GitHub: {remote_url(root)}. Nothing to make.")
        return 1
    if git(root, "status", "--porcelain").stdout.strip():
        print("there are uncommitted changes. Commit them first (the install's 'day one' commit), then run this again.")
        return 1
    name = root.resolve().name
    full = f"{owner}/{name}" if owner else name
    r = run("gh", "repo", "create", full, "--private", "--source", str(root), "--remote", "origin", "--push")
    if r.returncode != 0:
        print(f"GitHub refused to make {full}:\n  {(r.stderr or r.stdout).strip()[:400]}")
        return 1
    v = run("gh", "repo", "view", "--json", "visibility,url", "-q", ".visibility + \" \" + .url", cwd=root).stdout.strip()
    if not v.upper().startswith("PRIVATE"):
        print(f"made {full}, but GitHub reports it as {v or 'unknown'}. Make it private before anyone else sees it: gh repo edit --visibility private")
        return 1
    print(f"made the hub, private: {v.split(' ', 1)[1] if ' ' in v else full}")
    print(f"next: python3 scripts/oac-hub.py invite <their GitHub user>, then they run: python3 scripts/oac-hub.py join {full if owner else '<owner>/' + name}")
    return 0


def name_with_owner(root: Path) -> str | None:
    r = run("gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner", cwd=root)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def cmd_invite(root: Path, user: str) -> int:
    why = gh_ready()
    if why:
        print(why)
        return 1
    if not re.match(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$", user):
        print(f"'{user}' is not a GitHub username (letters, digits and hyphens, up to 39).")
        return 1
    nwo = name_with_owner(root)
    if not nwo:
        print("this repo has no copy on GitHub yet. Run `python3 scripts/oac-hub.py create` first.")
        return 1
    r = run("gh", "api", "-X", "PUT", f"repos/{nwo}/collaborators/{user}", "-f", "permission=push")
    if r.returncode != 0:
        print(f"GitHub refused the invite for {user}:\n  {(r.stderr or r.stdout).strip()[:400]}")
        return 1
    print(f"invited {user} to {nwo} with push access. They accept the email from GitHub, then run:")
    print(f"  python3 scripts/oac-hub.py join {nwo}")
    return 0


def cmd_join(nwo: str, dest: Path | None) -> int:
    why = gh_ready()
    if why:
        print(why)
        return 1
    if not re.match(r"^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$", nwo):
        print(f"'{nwo}' is not an owner/repo name.")
        return 1
    dest = (dest or Path.cwd() / nwo.split("/", 1)[1]).resolve()
    if dest.exists():
        print(f"{dest} already exists. Pick another folder with the second argument, or open that one.")
        return 1
    r = run("gh", "repo", "clone", nwo, str(dest))
    if r.returncode != 0:
        print(f"could not clone {nwo}:\n  {(r.stderr or r.stdout).strip()[:400]}")
        return 1
    h = handle(dest)
    logs = dest / "team" / h / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / ".gitkeep").touch()
    branch = on_branch(dest)
    git(dest, "add", "--", f"team/{h}")
    git(dest, "commit", "-q", "-m", f"Add: {h} joins the hub", "--", f"team/{h}")
    print(f"joined {nwo} at {dest}")
    print(f"  your folder: team/{h}/, your branch: {branch}")
    print("  next: open Claude Code there, run /start, then /oac. /done merges your branch.")
    return 0


# ── branch, inbox, who ───────────────────────────────────────────────────────

def cmd_branch(root: Path) -> int:
    b = on_branch(root)
    print(f"on {b}")
    return 0


def _unique(p: Path) -> Path:
    if not p.exists():
        return p
    n = 2
    while True:
        cand = p.with_name(f"{p.stem}-{n}{p.suffix}") if p.suffix and not p.is_dir() else p.with_name(f"{p.name}-{n}")
        if not cand.exists():
            return cand
        n += 1


def _too_big(src: Path) -> list[Path]:
    if src.is_file():
        return [src] if src.stat().st_size > BIG else []
    return [p for p in src.rglob("*") if p.is_file() and p.stat().st_size > BIG]


def cmd_inbox(root: Path, paths: list[str]) -> int:
    h = handle(root)
    if len(people(root)) > 1 and current_branch(root) in ("main", "master", ""):
        b = on_branch(root)
        print(f"two people work here, so this goes on your branch: {b}")
    dest_dir = root / INBOX / h
    dest_dir.mkdir(parents=True, exist_ok=True)
    chaos = root / CHAOS
    if not chaos.is_file():
        chaos.parent.mkdir(parents=True, exist_ok=True)
        chaos.write_text(CHAOS_HEAD.format(today=_dt.date.today().isoformat()), encoding="utf-8")
    rows = []
    for raw in paths:
        src = Path(raw).expanduser()
        if not src.exists():
            print(f"skipped, not found: {raw}")
            continue
        try:
            if src.resolve().is_relative_to(root.resolve()):
                print(f"skipped, already inside this repo: {raw}")
                continue
        except AttributeError:  # python < 3.9
            pass
        big = _too_big(src)
        if big:
            print(f"skipped, {big[0].name} is over 95 MB and GitHub refuses files that size: {raw}")
            continue
        dest = _unique(dest_dir / src.name)
        if src.is_dir():
            shutil.copytree(src, dest, copy_function=shutil.copy2)
            n = sum(1 for p in dest.rglob("*") if p.is_file())
            what = f"{n} file{'s' if n != 1 else ''}"
        else:
            shutil.copy2(src, dest)
            what = "1 file"
        rel = dest.relative_to(root).as_posix()
        rows.append(f"| `{src.resolve()}` | `{rel}` | {_dt.date.today().isoformat()} | {h} | yes, left in place |")
        print(f"copied {what}: {raw} -> {rel} (dates kept, original left in place)")
    if rows:
        with chaos.open("a", encoding="utf-8") as f:
            f.write("\n".join(rows) + "\n")
        print(f"{len(rows)} row{'s' if len(rows) != 1 else ''} added to {CHAOS.as_posix()}")
        print("next: /done saves it; sort from the inbox into context-core/ and systems/ as you go")
        return 0
    print("nothing copied")
    return 1


def cmd_who(root: Path) -> int:
    ps = people(root)
    print(f"you: {handle(root)}")
    print(f"people here: {', '.join(ps) if ps else 'nobody in team/ yet'}")
    print(f"on GitHub: {remote_url(root) or 'no copy yet (python3 scripts/oac-hub.py create)'}")
    print(f"branch: {current_branch(root) or '(none)'}")
    if len(ps) > 1:
        print("rule: more than one person, so each works on their own branch and /done merges it")
    else:
        print("rule: one person, so main is fine; the day a second person joins, branches start")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="One business repo, two laptops: the hub and each person's inbox.")
    ap.add_argument("--root", default=".", help="the business repo (default: here)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create", help="make the private repo on GitHub from this folder")
    c.add_argument("--owner", help="a GitHub organisation to own it (default: your account)")
    i = sub.add_parser("invite", help="add the second person with push access")
    i.add_argument("user")
    j = sub.add_parser("join", help="the second laptop: clone the hub and start your branch")
    j.add_argument("repo", help="owner/repo")
    j.add_argument("dir", nargs="?", type=Path)
    sub.add_parser("branch", help="today's branch for you, made or switched to")
    b = sub.add_parser("inbox", help="copy files in, dates kept, originals untouched")
    b.add_argument("paths", nargs="+")
    sub.add_parser("who", help="who works here, the remote, the branch, the rule")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    if a.cmd == "create":
        return cmd_create(root, a.owner)
    if a.cmd == "invite":
        return cmd_invite(root, a.user)
    if a.cmd == "join":
        return cmd_join(a.repo, a.dir)
    if a.cmd == "branch":
        return cmd_branch(root)
    if a.cmd == "inbox":
        return cmd_inbox(root, a.paths)
    return cmd_who(root)


if __name__ == "__main__":
    sys.exit(main())

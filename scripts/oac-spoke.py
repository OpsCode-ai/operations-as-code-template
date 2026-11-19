#!/usr/bin/env python3
"""A team's part of the business brain: one private repo per team (ADR-140).

WHY THIS EXISTS
    GitHub has no folder permissions: anyone who can read a repo can read all
    of it. So the business brain (the hub) stays with the owners, and each team
    works in a spoke, a separate private repo that holds only the folders the
    owners chose for it. OpsCode does this for its own builders (ADR-134);
    this is the same pattern inside a customer's business, run by the owners on
    their own laptops, never by OpsCode. First needed for a customer's
    private day, 20 Nov 2026.

WHAT A SPOKE HOLDS
    - every pack file the business never edited (the tools, the commands),
      checked byte for byte against .oac/pack-manifest.json. A pack file the
      business filled in, like README.md or standards/brand.md, holds business
      content and stays in the brain;
    - the folders and files its spec lists, at the same paths;
    - team/<name>/ for each person in the team;
    - the company's vision for staff, context-core/strategic-identity/for-the-team.md,
      and the team's own goals, context-core/strategic-identity/teams/<team>/,
      every time, without being listed. Each team goal names the company goal
      it serves, and oac-goals.py rolls them up in the brain;
    - its own README.md, CLAUDE.md, .oac/manifest.yml and a release record.
    It is built from what is saved and shared (origin/main, or main before the
    brain is on GitHub), never from unsaved work.

THE GATE
    Kept back, and listed: anything marked `audience: owner`, .env files,
    specs/spokes/, inbox/, other people's team/ folders, this laptop's own
    .claude/ files, and the rest of the vision folder
    (context-core/strategic-identity/), which can hold money and plans to sell:
    a file or folder in it crosses only when the spec names it there.
    Refused, so nothing goes: a known kind of secret, a word from the spec's
    block_terms, or a gitleaks finding when gitleaks is installed.

A SPOKE IS A DEPARTMENT OR A PERSON
    Draw it as a circle around the brain, with a name and a job title or
    description (Adam, 19 Nov 2026, after Christchurch). A department spoke
    holds the people in that department. A person spoke holds one person: a
    CFO, say, whose spoke only they and the owners see. An AI spoke is one AI
    role, an AI marketer say: its instructions go in as
    .claude/agents/<name>.md, and its people are the ones who check its work.
    The owners are in every spoke: `invite` adds everyone with direct access
    to the brain. `/spoke` turns 'we need a marketing department' into a plan.

THE SPEC
    specs/spokes/<team>.yml in the brain, so staff never see who is in which
    team. `plan` writes it:
        spoke: mine
        kind: department                 # or person, or ai
        title: "Acme Mining: the mine"
        description: "Runs the mine and the haul roads"
        github: ""                       # set by create
        people:
          - {name: "Jane Smith", github: "jane-smith"}
        paths: ["systems/processes/mine/", "context-core/voice/"]
        block_terms: []

VERBS
    plan [<team> --kind department|person --description "..."
          --people "Name:github-user" ... --paths a/ b ...]
                        With no team: the spokes so far and the brain's
                        folders. With one: writes or updates its spec.
    check <team>        Build it in a temporary folder and gate it. Says what
                        would cross and what is kept back. Changes nothing.
    create <team> [--owner ORG] [--name REPO]
                        Build, gate, make the private repo on GitHub (under
                        the brain's own owner unless --owner says otherwise)
                        and its folder beside the brain: <brain>-spokes/<team>.
    invite <team> [github-user ...]
                        Push access, never admin. No names: everyone in the
                        spec, and the brain's owners, so they see every spoke.
    release <team> [--push]
                        Bring the brain's latest into the spoke. Refuses while
                        the team has changes the brain has not taken yet.
                        Commits on this laptop; --push sends it to GitHub.
    pull-back <team>    The team's changes and new files come into this
                        folder of the brain, for an owner to read and save
                        with /done. Never overwrites a file the brain also
                        changed: that is reported, and left for a person.
    list                Every spoke, who is in it, where it lives.

WHAT IT NEVER DOES
    Add anyone to the brain. Make a public repo. Delete a file the team added.
    Overwrite the brain's own changes. Install anything: Python, git and gh
    only, no admin rights.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:
    print("oac-spoke: needs PyYAML. Install it for you only, no admin rights: python -m pip install --user pyyaml",
          file=sys.stderr)
    sys.exit(2)

PY = "python" if os.name == "nt" else "python3"
SELF = f"{PY} scripts/oac-spoke.py"
SPECS = Path("specs") / "spokes"
RECORD = ".oac/spoke-release.json"
PACK_MANIFEST = ".oac/pack-manifest.json"
NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
GH_USER = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
KINDS = ("department", "person", "ai")
KIND_WORDS = {"department": "a department", "person": "a person", "ai": "an AI"}

# An AI role's spoke carries its instructions as a Claude Code agent. It
# drafts; a named person checks; nothing leaves on its own (ADR-140 rule 20).
AGENT_MD = """---
name: {spoke}
description: "{title}: an AI role in this business. {description_q}It drafts, a person checks, and nothing goes out on its own."
---

# {title}

You are an AI role in this business{description_s}

## How you work

- Read `context-core/strategic-identity/for-the-team.md` first: where the
  company is heading.
- Your goals are in `context-core/strategic-identity/teams/{spoke}/goals.md`.
  Every piece of work serves one of them. Say which.
- Work only from what is in this repo. The rest of the business stays with its
  owners, so never guess what else they hold.
- Before anything you make, read `vision.md`, `standards/brand.md` and
  `context-core/voice/` when they are here, and follow them.
- Draft, then show a person below. Nothing is sent, posted or published until
  they say yes.
- Write down what you did, and why, in `team/{spoke}/`, so the people who
  check your work can follow it.

## Who checks your work

{checkers}
"""
BIG = 95 * 1024 * 1024
FROM_SELF = "context-core/strategic-identity/from-self-as-code.md"
VISION = "context-core/strategic-identity/"
FOR_TEAM = VISION + "for-the-team.md"


def goals_dir(team: str) -> str:
    return f"{VISION}teams/{team}/"


TEAM_GOALS = """---
title: "The {team} team's goals"
type: report
audience: team
status: active
updated: {today}
topics: [operations]
tags: [goals, team, {team}]
---

# The {team} team's goals

Three goals for the next 90 days. Each one is a number and a date, and serves
one company goal from `for-the-team.md`, named as `[serves: <its id>]`. The
team gives each goal one word at `/done` once a week, and the owners see it in
the brain's roll-up.

<!-- A row looks like this, one per goal, ids starting with the team's name:
| [goal: {team}-1] What, the number, by when [serves: <company goal id>] | not started | {today} |
-->

| Goal | Status | Updated |
|---|---|---|
"""

# The spoke writes these itself. A spec may not list them.
TOOL_OWNED = {"README.md", "CLAUDE.md", ".oac/manifest.yml", RECORD, PACK_MANIFEST}

# Never released, even under a listed folder. Each entry: (prefix or exact, why).
NEVER = [
    ("specs/spokes/", "who is in which team stays in the brain"),
    ("inbox/", "the inbox is unsorted, so anything could be in it"),
    (".oac/", "the spoke writes its own"),
    (".claude/user.json", "this laptop's own file"),
    (".claude/settings.local.json", "this laptop's own file"),
    (".claude/checkpoint.json", "this laptop's own file"),
    (".git/", "git's own"),
]

SECRETS = [
    ("a private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("an AWS key", re.compile(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])")),
    ("a GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})")),
    ("a Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("a Stripe live key", re.compile(r"\b[rs]k_live_[A-Za-z0-9]{20,}")),
    ("an Anthropic key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("an OpenAI key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}")),
    ("a Google key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}")),
]

SPEC_HEAD = """# One team's part of the brain (ADR-140). Read by scripts/oac-spoke.py.
# It lives in the brain, never in the spoke, so staff never see who is in
# which team. paths: folders end in '/'. block_terms: words that must never
# reach this team; a release that finds one is refused.
"""

SPOKE_MANIFEST = """# OaC manifest for a spoke: one team's part of a business brain (ADR-140).
# Made by scripts/oac-spoke.py in the brain. Check this repo any time with:
#   {py} scripts/oac-validate.py .

oac_version: "{oac_version}"
plane: business
spoke_of: "{hub}"
spoke: {spoke}
profiles: [pack]

types: {{}}
topics: []
exempt:
  - path: .claude/
    reason: The command install, not authored content.
  - path: scripts/
    reason: Tooling, not authored content.
  - path: specs/
    reason: The published standard, carried as reference.
"""

SPOKE_GITIGNORE = """.DS_Store
node_modules/
.env
.env.*
*.log

# Local to this machine, never shared
.claude/user.json
.claude/settings.local.json
.claude/checkpoint.json
"""

SPOKE_README = """---
title: "{title}"
type: index
audience: team
---

# {title}

{about}Your spoke of the business brain. It holds the folders you need. The
rest of the brain stays with the owners, who can see this spoke too.

## Getting started

1. Say yes to GitHub's invite. It is in your email.
2. Join it from your own private space:
   `{py} scripts/oac-hub.py join {github}`
3. Open the folder it made, then type `/start`. Finish with `/done`.

## How your work gets back to the brain

`/done` saves and shares your work here. An owner brings it into the brain,
reads it, and saves it there. What the owners change comes back to you the
next time you `/start`.

Never put a password, a key, or anything private about a person in here.
"""

SPOKE_CLAUDE_MD = """---
title: "{title}: how this repo works"
type: guide
audience: team
---

# {title}

{about}This is a spoke: one {kind}'s part of a business brain. It holds only
the folders the owners chose for it, at the same paths as in the brain. The
owners can see it. The brain holds the rest, and nothing here can see it, so never guess what
is in it. When something needs the whole business's view, say to ask an owner.

- Work as in any Operations as Code repo: `/start`, then `/done`.
- New work goes in the folder it belongs in, or in `team/<your name>/`.
- An owner brings this team's changes into the brain and reads them first.
"""


# ── small helpers ────────────────────────────────────────────────────────────

def _load_hub_tools():
    """oac-hub.py's gh check and branch helpers, loaded by path: one copy.
    No __pycache__ left in the brain's scripts/ to show up as unsaved."""
    sys.dont_write_bytecode = True
    path = Path(__file__).with_name("oac-hub.py")
    spec = importlib.util.spec_from_file_location("oac_hub", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hubtools = _load_hub_tools()


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def norm_sha(data: bytes) -> str:
    """sha256 with Windows line endings folded, so a checkout that turned LF
    into CRLF is not mistaken for a change. Binary files are hashed as they are."""
    if b"\0" not in data[:8000]:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def raw_sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(p: Path) -> str:
    return norm_sha(p.read_bytes())


def under(path: str, prefix: str) -> bool:
    """For the never list: an entry ending in '/' is a folder, else one file."""
    return path == prefix.rstrip("/") or (prefix.endswith("/") and path.startswith(prefix))


def covers(listed: str, path: str) -> bool:
    """A spec path covers itself and, as a folder, everything under it."""
    stem = listed.rstrip("/")
    return path == stem or path.startswith(stem + "/")


def handle_of(person: dict) -> str:
    """The team folder name: what oac-hub.py join makes from a first name."""
    h = str(person.get("handle") or "").strip().lower()
    if h:
        return h
    first = str(person.get("name") or "").split()[:1]
    return re.sub(r"[^a-z0-9]+", "", first[0].lower()) if first else ""


def main_folder(root: Path) -> Path:
    """The brain's main folder, even when run from a session folder."""
    r = git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    common = Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else root / ".git"
    return common.parent if common.name == ".git" else root


def nwo_from_url(url: str) -> str | None:
    m = re.search(r"github\.com[:/]+([A-Za-z0-9-]+/[A-Za-z0-9._-]+?)(?:\.git)?/?$", url.strip())
    return m.group(1) if m else None


def hub_nwo(root: Path) -> str | None:
    url = git(root, "remote", "get-url", "origin").stdout.strip()
    if url and nwo_from_url(url):
        return nwo_from_url(url)
    if shutil.which("gh"):
        return hubtools.name_with_owner(root)
    return None


# ── the spec ─────────────────────────────────────────────────────────────────

def spec_file(root: Path, team: str) -> Path:
    return root / SPECS / f"{team}.yml"


def path_problem(p: str) -> str | None:
    """Why a spec path is not allowed, or None."""
    if not p or p.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", p) or ".." in Path(p).parts:
        return "must be a path inside the brain, like systems/processes/"
    if p in TOOL_OWNED:
        return "the spoke writes its own"
    if p == FROM_SELF:
        return None                                    # named exactly: allowed
    if p.rstrip("/") == VISION.rstrip("/"):
        return ("the vision folder can hold money and plans to sell. Name the files to share instead; "
                "for-the-team.md and the team's goals go every time")
    if p.rstrip("/") == "team" or p.startswith("team/"):
        return "team folders come with the people in the spec, one each"
    if os.path.basename(p.rstrip("/")).startswith(".env"):
        return "an .env file holds keys"
    for prefix, why in NEVER:
        if under(p, prefix) or (prefix.endswith("/") and p.rstrip("/") == prefix.rstrip("/")):
            return why
    if p.rstrip("/") in ("", ".") or p == "/":
        return "that is the whole brain"
    return None


def load_spec(root: Path, team: str) -> dict:
    if not NAME.match(team):
        sys.exit(f"'{team}' is not a team name: lower case letters, digits and hyphens, like mine or office.")
    f = spec_file(root, team)
    if not f.is_file():
        sys.exit(f"no spoke called '{team}' yet. Make its plan first: {SELF} plan {team} --people ... --paths ...")
    try:
        sp = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        sys.exit(f"{f.relative_to(root).as_posix()} is not valid YAML: {e}")
    sp.setdefault("spoke", team)
    sp["kind"] = str(sp.get("kind") or "department").strip().lower()
    if sp["kind"] not in KINDS:
        sys.exit(f"specs/spokes/{team}.yml: kind is '{sp['kind']}'. It is department, person or ai.")
    sp["description"] = str(sp.get("description") or "").strip()
    sp["people"] = [p for p in (sp.get("people") or []) if isinstance(p, dict) and p.get("name")]
    sp["paths"] = [str(p).strip()[2:] if str(p).strip().startswith("./") else str(p).strip()
                   for p in (sp.get("paths") or [])]
    sp["block_terms"] = [str(t) for t in (sp.get("block_terms") or []) if str(t).strip()]
    bad = [f"{p}: {why}" for p in sp["paths"] for why in [path_problem(p)] if why]
    if bad:
        sys.exit(f"specs/spokes/{team}.yml lists paths a spoke never gets:\n  " + "\n  ".join(bad))
    return sp


def write_spec(root: Path, sp: dict) -> Path:
    f = spec_file(root, sp["spoke"])
    f.parent.mkdir(parents=True, exist_ok=True)
    q = json.dumps
    people = "\n".join(
        "  - {" + ", ".join(f"{k}: {q(str(v))}" for k, v in p.items() if v not in (None, "")) + "}"
        for p in sp["people"]) or "  []"
    lines = [SPEC_HEAD.rstrip("\n"),
             f"spoke: {sp['spoke']}",
             f"kind: {sp.get('kind') or 'department'}",
             f"title: {q(sp.get('title') or '')}",
             f"description: {q(sp.get('description') or '')}",
             f"github: {q(sp.get('github') or '')}",
             "people:" + ("\n" + people if sp["people"] else " []"),
             f"paths: [{', '.join(q(p) for p in sp['paths'])}]",
             f"block_terms: [{', '.join(q(t) for t in sp['block_terms'])}]"]
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f


def set_spec_github(root: Path, team: str, nwo: str) -> None:
    f = spec_file(root, team)
    text = f.read_text(encoding="utf-8")
    line = f"github: {json.dumps(nwo)}"
    if re.search(r"(?m)^github:.*$", text):
        text = re.sub(r"(?m)^github:.*$", line, text, count=1)
    else:
        text = text.rstrip("\n") + "\n" + line + "\n"
    f.write_text(text, encoding="utf-8")


# ── reading the brain as saved and shared ───────────────────────────────────

def source_ref(root: Path) -> tuple[str, str]:
    """(ref, note). origin/main when the brain is on GitHub, else main."""
    if git(root, "remote", "get-url", "origin").returncode == 0:
        f = git(root, "fetch", "-q", "origin", "main")
        if git(root, "rev-parse", "--verify", "-q", "origin/main").returncode == 0:
            note = "" if f.returncode == 0 else " (GitHub could not be reached, so from the last copy this laptop has)"
            return "origin/main", note
    for ref in ("main", "master", "HEAD"):
        if git(root, "rev-parse", "--verify", "-q", ref).returncode == 0:
            return ref, " (the brain is not on GitHub yet, so from this laptop's main)"
    sys.exit("the brain has nothing saved yet. Save day one first.")


def tree(root: Path, ref: str) -> dict[str, tuple[str, int]]:
    """{path: (blob sha, size)} for every plain file at ref."""
    r = subprocess.run(["git", "-C", str(root), "ls-tree", "-r", "-z", "-l", ref], capture_output=True)
    if r.returncode != 0:
        sys.exit(f"could not read {ref}: {r.stderr.decode(errors='replace').strip()[:300]}")
    out = {}
    for entry in r.stdout.split(b"\0"):
        if not entry:
            continue
        meta, path = entry.split(b"\t", 1)
        mode, kind, sha, size = meta.split()
        if kind == b"blob" and mode in (b"100644", b"100755"):
            out[path.decode("utf-8", "surrogateescape")] = (sha.decode(), int(size))
    return out


def read_blobs(root: Path, shas: list[str]) -> dict[str, bytes]:
    """Raw bytes, as saved: no line-ending conversion on the way out."""
    if not shas:
        return {}
    p = subprocess.Popen(["git", "-C", str(root), "cat-file", "--batch"],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    got = {}
    for sha in dict.fromkeys(shas):
        p.stdin.write(sha.encode() + b"\n")
        p.stdin.flush()
        head = p.stdout.readline().split()
        size = int(head[2])
        got[sha] = p.stdout.read(size)
        p.stdout.read(1)
    p.stdin.close()
    p.wait()
    return got


def owner_only(data: bytes) -> bool:
    """A markdown file whose frontmatter says audience: owner (or the old 'adam')."""
    text = data[:6000].decode("utf-8", "replace").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---", 4)
    m = re.search(r"(?m)^audience:\s*['\"]?([A-Za-z]+)", text[4:end if end > 0 else len(text)])
    return bool(m) and m.group(1).lower() in ("owner", "adam")


# ── build ────────────────────────────────────────────────────────────────────

class Build:
    def __init__(self):
        self.files: dict[str, tuple[bytes, str]] = {}      # path -> (bytes, source: hub | pack | spoke)
        self.kept: list[tuple[str, str]] = []              # (path, why) under a listed folder, kept back
        self.edited_pack: list[str] = []                   # pack files the business filled in
        self.unmatched: list[str] = []                     # spec paths with nothing behind them
        self.rev = ""
        self.ref = ""
        self.note = ""


def vision_shared(path: str, sp: dict) -> bool:
    """A file in the vision folder crosses only when named there: the page
    for staff, this team's goals, or a path the spec lists inside the folder."""
    if path == FOR_TEAM or covers(goals_dir(sp["spoke"]), path):
        return True
    return any(covers(p, path) for p in sp["paths"]
               if p.startswith(VISION) and p.rstrip("/") != VISION.rstrip("/"))


def spoke_handles(sp: dict) -> set[str]:
    """The team/ folders this spoke owns: one per person, and the AI role's own."""
    hs = {h for h in (handle_of(p) for p in sp["people"]) if h}
    if sp.get("kind") == "ai":
        hs.add(sp["spoke"])
    return hs


def never_reason(path: str, sp: dict, handles: set[str], releasing: bool = True) -> str | None:
    """Why a file never goes to this spoke. Pull-back passes releasing=False:
    a team's own new page in the vision folder may come up for the owners."""
    if path in TOOL_OWNED:
        return "the spoke writes its own"
    if path == FROM_SELF and FROM_SELF not in sp["paths"]:
        return "from your Self as Code plan: list this exact file to share it"
    if releasing and path.startswith(VISION) and not vision_shared(path, sp):
        return "in the vision folder: name it in the plan to share it"
    if os.path.basename(path).startswith(".env"):
        return "an .env file holds keys"
    if path.startswith("team/"):
        who = path.split("/")[1] if path.count("/") >= 1 else ""
        if who not in handles:
            return "someone else's team folder"
    for prefix, why in NEVER:
        if under(path, prefix):
            return why
    return None


def build(root: Path, sp: dict) -> Build:
    b = Build()
    b.ref, b.note = source_ref(root)
    b.rev = git(root, "rev-parse", b.ref).stdout.strip()
    files = tree(root, b.ref)
    if PACK_MANIFEST not in files:
        sys.exit("this brain has no .oac/pack-manifest.json, so its pack is too old to make a spoke from. "
                 f"Upgrade it first: {PY} scripts/oac-upgrade.py --from <the newer pack> --apply")
    manifest_bytes = read_blobs(root, [files[PACK_MANIFEST][0]])[files[PACK_MANIFEST][0]]
    pack = (json.loads(manifest_bytes.decode("utf-8")).get("files") or {})
    hub_manifest = files.get(".oac/manifest.yml")
    if hub_manifest:
        mtext = read_blobs(root, [hub_manifest[0]])[hub_manifest[0]].decode("utf-8", "replace")
        if re.search(r"(?m)^spoke_of:", mtext):
            sys.exit("this is a spoke, not the brain. Spokes are made from the brain.")
        m = re.search(r"(?m)^oac_version:\s*['\"]?([0-9.]+)", mtext)
        oac_version = m.group(1) if m else "1.13"
    else:
        oac_version = "1.13"

    handles = spoke_handles(sp)
    team_prefixes = [f"team/{h}/" for h in sorted(handles)]
    listed = list(sp["paths"]) + team_prefixes + [FOR_TEAM, goals_dir(sp["spoke"])]
    matched = {p: False for p in sp["paths"]}

    want: dict[str, str] = {}                              # path -> source
    for path, (sha, size) in sorted(files.items()):
        hits = [p for p in listed if covers(p, path)]
        for p in hits:
            if p in matched:
                matched[p] = True
        why = never_reason(path, sp, handles)
        if hits:
            if why:
                if path not in TOOL_OWNED:
                    b.kept.append((path, why))
                continue
            if size > BIG:
                b.kept.append((path, "over 95 MB, and GitHub refuses files that size"))
                continue
            want[path] = "hub"
        elif path in pack and path not in TOOL_OWNED:
            want[path] = "pack"                        # kept only if its bytes are the pack's own
    blobs = read_blobs(root, [files[p][0] for p in want])
    for path, source in want.items():
        data = blobs[files[path][0]]
        if source == "hub" and path.endswith(".md") and owner_only(data):
            b.kept.append((path, "marked audience: owner"))
            continue
        if source == "pack":
            if norm_sha(data) != (pack[path] or {}).get("sha256") and raw_sha(data) != (pack[path] or {}).get("sha256"):
                b.edited_pack.append(path)
                continue
        b.files[path] = (data, source)
    b.unmatched = [p for p, ok in matched.items() if not ok]
    if FOR_TEAM not in b.files:
        b.unmatched.insert(0, FOR_TEAM + " (the team's page about the company)")

    hub = hub_nwo(root) or main_folder(root).name
    github = sp.get("github") or "<owner>/<this repo>"
    title = sp.get("title") or f"The {sp['spoke']} team"
    about = f"{sp['description'].rstrip('.')}.\n\n" if sp.get("description") else ""
    if sp.get("kind") == "ai":
        about += ("An AI role works here. Its instructions are in `.claude/agents/" + sp["spoke"]
                  + ".md`. The people in this spoke check its work before anything goes out.\n\n")
    spoke_written = {
        ".oac/manifest.yml": SPOKE_MANIFEST.format(py=PY, oac_version=oac_version, hub=hub, spoke=sp["spoke"]),
        "README.md": SPOKE_README.format(title=title, py=PY, github=github, about=about),
        "CLAUDE.md": SPOKE_CLAUDE_MD.format(title=title, about=about, kind=sp.get("kind") or "department"),
        PACK_MANIFEST: manifest_bytes.decode("utf-8"),
    }
    if ".gitignore" not in b.files:
        spoke_written[".gitignore"] = SPOKE_GITIGNORE
    if sp.get("kind") == "ai":
        desc = sp.get("description", "").rstrip(".")
        checkers = "\n".join(f"- {p['name']}" for p in sp["people"]) or "- (nobody named yet: ask an owner)"
        spoke_written[f".claude/agents/{sp['spoke']}.md"] = AGENT_MD.format(
            spoke=sp["spoke"], title=title, checkers=checkers,
            description_q=(desc.replace('"', "'") + ". ") if desc else "",
            description_s=(f": {desc}." if desc else "."))
    for path, text in spoke_written.items():
        b.files[path] = (text.encode("utf-8"), "spoke")
    record = {
        "spoke": sp["spoke"],
        "hub": hub,
        "hub_rev": b.rev,
        "built_from": b.ref,
        "files": {p: {"sha256": norm_sha(d), "source": s} for p, (d, s) in sorted(b.files.items())},
    }
    b.files[RECORD] = ((json.dumps(record, indent=2) + "\n").encode("utf-8"), "spoke")
    return b


def term_regex(term: str) -> re.Pattern:
    """'Project Kiwi' matches 'project kiwi', 'project-kiwi' and 'project_kiwi'."""
    words = [w for w in re.split(r"[-_. ]+", term.lower()) if w]
    body = r"[-_. ]*".join(re.escape(w) for w in words)
    return re.compile(r"(?<![a-z0-9])" + body + r"(?![a-z0-9])", re.I)


def gate(b: Build, sp: dict) -> tuple[list[str], list[str]]:
    """(refusals, notes). The brain's own files and the spoke's are scanned;
    the pack's untouched files are the published pack, gated at its release."""
    refuse, notes = [], []
    terms = [(t, term_regex(t)) for t in sp["block_terms"]]
    for path, (data, source) in sorted(b.files.items()):
        if source == "pack" or len(data) > 2 * 1024 * 1024 or b"\0" in data[:8000]:
            continue
        text = data.decode("utf-8", "replace")
        for what, rx in SECRETS:
            for m in rx.finditer(text):
                refuse.append(f"{path}:{text.count(chr(10), 0, m.start()) + 1}: looks like {what}")
        for t, rx in terms:
            for m in rx.finditer(text):
                refuse.append(f"{path}:{text.count(chr(10), 0, m.start()) + 1}: names '{t}', a blocked word")
    if shutil.which("gitleaks"):
        with tempfile.TemporaryDirectory(prefix="spoke-gate-") as tmp:
            for path, (data, source) in b.files.items():
                if source != "pack":
                    t = Path(tmp) / path
                    t.parent.mkdir(parents=True, exist_ok=True)
                    t.write_bytes(data)
            r = subprocess.run(["gitleaks", "dir", tmp, "--no-banner", "--redact"], capture_output=True, text=True)
            if r.returncode != 0 and "unknown command" in (r.stderr + r.stdout).lower():
                r = subprocess.run(["gitleaks", "detect", "--no-git", "-s", tmp, "--no-banner", "--redact"],
                                   capture_output=True, text=True)
            if r.returncode != 0:
                tail = ((r.stdout + r.stderr).strip().splitlines() or ["a leak"])[-1]
                refuse.append(f"gitleaks: {tail}")
    else:
        notes.append("gitleaks is not installed, so only the built-in secret check ran")
    return refuse, notes


def report(b: Build, sp: dict) -> None:
    hub_files = [p for p, (_, s) in b.files.items() if s == "hub"]
    pack_files = [p for p, (_, s) in b.files.items() if s == "pack"]
    print(f"spoke '{sp['spoke']}', built from {b.ref} {b.rev[:8]}{b.note}")
    print(f"  crosses: {len(hub_files)} file{'s' if len(hub_files) != 1 else ''} from the brain, "
          f"{len(pack_files)} pack files (the tools), and the spoke's own README, CLAUDE.md and manifest")
    by_top: dict[str, int] = {}
    for p in hub_files:
        parts = p.split("/")
        top = "/".join(parts[:2]) + "/" if len(parts) > 2 else (parts[0] + "/" if len(parts) == 2 else p)
        by_top[top] = by_top.get(top, 0) + 1
    for top, n in sorted(by_top.items()):
        print(f"    {top}  {n}")
    if b.kept:
        print(f"  kept back: {len(b.kept)}")
        for p, why in b.kept[:30]:
            print(f"    {p}  ({why})")
        if len(b.kept) > 30:
            print(f"    ... and {len(b.kept) - 30} more")
    if b.edited_pack:
        print(f"  stays in the brain: {len(b.edited_pack)} pack file{'s' if len(b.edited_pack) != 1 else ''} "
              "this business filled in")
        for p in b.edited_pack[:10]:
            print(f"    {p}")
        if len(b.edited_pack) > 10:
            print(f"    ... and {len(b.edited_pack) - 10} more")
    for p in b.unmatched:
        print(f"  note: '{p}' is listed but the brain's {b.ref} has nothing there yet")


def build_and_gate(root: Path, sp: dict) -> Build | None:
    b = build(root, sp)
    report(b, sp)
    refuse, notes = gate(b, sp)
    for n in notes:
        print(f"  note: {n}")
    if refuse:
        print(f"GATE: {len(refuse)} finding{'s' if len(refuse) != 1 else ''}. Nothing was released.")
        for f in refuse[:40]:
            print(f"  {f}")
        print("Fix it in the brain (or take the folder off the spec), save it, then run this again.")
        return None
    print("gate: clean")
    return b


def write_tree(b: Build, dest: Path) -> None:
    for path, (data, _) in b.files.items():
        t = dest / path
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_bytes(data)


# ── the spoke's folder on this laptop ────────────────────────────────────────

def spoke_dir(root: Path, team: str) -> Path:
    hub = main_folder(root)
    return hub.parent / f"{hub.name}-spokes" / team


def ensure_clone(root: Path, sp: dict) -> Path | None:
    d = spoke_dir(root, sp["spoke"])
    if (d / ".git").exists():
        return d
    if not sp.get("github"):
        print(f"the '{sp['spoke']}' spoke has not been made yet: {SELF} create {sp['spoke']}")
        return None
    why = hubtools.gh_ready()
    if why:
        print(why)
        return None
    d.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["gh", "repo", "clone", sp["github"], str(d)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"could not get {sp['github']} onto this laptop:\n  {(r.stderr or r.stdout).strip()[:400]}")
        return None
    print(f"got {sp['github']} onto this laptop at {d}")
    return d


def catch_up(d: Path) -> str | None:
    """Fast-forward the spoke's folder to GitHub. None when fine, else why not."""
    if git(d, "status", "--porcelain").stdout.strip():
        return f"{d} has unsaved changes. The spoke's folder on this laptop is only for releases; save or remove them first."
    if "origin" not in git(d, "remote").stdout.split():
        return None
    git(d, "fetch", "-q", "origin")
    if git(d, "rev-parse", "--verify", "-q", "origin/main").returncode != 0:
        return None
    if git(d, "merge", "--ff-only", "-q", "origin/main").returncode != 0:
        return f"{d} and GitHub have split. Sort that out by hand first (ask Claude to show you both)."
    return None


def read_record(d: Path) -> dict:
    try:
        return json.loads((d / RECORD).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def tracked(d: Path) -> list[str]:
    return [p for p in git(d, "ls-files", "-z").stdout.split("\0") if p]


def commit(d: Path, message: str) -> bool:
    git(d, "add", "-A")
    if not git(d, "status", "--porcelain").stdout.strip():
        return False
    r = git(d, "commit", "-q", "--no-verify", "-m", message)
    if r.returncode != 0:
        msg = (r.stderr or r.stdout).strip()
        if "who you are" in msg.lower() or "user.email" in msg.lower():
            sys.exit("git does not know your name yet. Tell it once:\n"
                     "  git config --global user.name \"Your Name\"\n"
                     "  git config --global user.email you@example.com")
        sys.exit(f"could not save the release: {msg[:400]}")
    return True


# ── verbs ────────────────────────────────────────────────────────────────────

def parse_person(raw: str) -> dict:
    name, _, user = raw.partition(":")
    p = {"name": name.strip()}
    if user.strip():
        p["github"] = user.strip()
    return p


def cmd_plan(root: Path, team: str | None, people: list[str] | None, paths: list[str] | None,
             title: str | None, block: list[str] | None, kind: str | None = None,
             description: str | None = None) -> int:
    if not team:
        specs = sorted((root / SPECS).glob("*.yml")) if (root / SPECS).is_dir() else []
        print("spokes so far: " + (", ".join(s.stem for s in specs) if specs else "none yet"))
        counts: dict[str, int] = {}
        for p in git(root, "ls-files", "-z").stdout.split("\0"):
            if not p or "/" not in p or p.split("/")[0] in (".claude", ".githooks", ".oac", "scripts", "specs"):
                continue                                   # the tools: every spoke gets them anyway
            parts = p.split("/")
            key = parts[0] + "/" + (parts[1] + "/" if len(parts) > 2 else "")
            counts[key] = counts.get(key, 0) + 1
        print("the brain's folders, with how many saved files each holds:")
        for k, n in sorted(counts.items()):
            flag = "" if path_problem(k) is None else "  (never in a spoke)"
            print(f"  {k}  {n}{flag}")
        print(f"next: {SELF} plan <team> --people \"Name:github-user\" ... --paths <folder>/ ...")
        return 0
    if not NAME.match(team):
        print(f"'{team}' is not a team name: lower case letters, digits and hyphens, like mine or office.")
        return 1
    f = spec_file(root, team)
    sp = load_spec(root, team) if f.is_file() else {"spoke": team, "kind": "department", "title": "",
                                                       "description": "", "github": "",
                                                       "people": [], "paths": [], "block_terms": []}
    if kind is not None:
        if kind not in KINDS:
            print(f"'{kind}' is not a kind of spoke. It is department, person or ai.")
            return 1
        sp["kind"] = kind
    if description is not None:
        sp["description"] = description.strip()
    if title is not None:
        sp["title"] = title
    if people is not None:
        sp["people"] = [parse_person(x) for x in people if x.strip()]
    if paths is not None:
        clean = []
        for p in paths:
            p = p.strip().replace("\\", "/")
            p = p[2:] if p.startswith("./") else p
            if p and (root / p).is_dir() and not p.endswith("/"):
                p += "/"
            clean.append(p)
        sp["paths"] = list(dict.fromkeys(clean))
    if block is not None:
        sp["block_terms"] = [t for t in block if t.strip()]
    bad = [f"{p}: {why}" for p in sp["paths"] for why in [path_problem(p)] if why]
    if bad:
        print("these can never go in a spoke, so nothing was written:\n  " + "\n  ".join(bad))
        return 1
    for p in sp["people"]:
        if p.get("github") and not GH_USER.match(p["github"]):
            print(f"'{p['github']}' is not a GitHub username (letters, digits and hyphens), so nothing was written.")
            return 1
    if not sp.get("title"):
        sp["title"] = f"The {team} team"
    if sp["kind"] == "ai" and not sp["people"]:
        print("an AI role needs at least one person who checks its work. Name them with --people.")
        return 1
    if sp["kind"] == "person" and len(sp["people"]) != 1:
        print(f"a person spoke is for one person; this plan names {len(sp['people'])}. "
              "Make it a department, or name one person.")
        return 1
    out = write_spec(root, sp)
    print(f"wrote {out.relative_to(root).as_posix()}: {KIND_WORDS[sp['kind']]} spoke, {len(sp['people'])} "
          f"{'person' if len(sp['people']) == 1 else 'people'}, {len(sp['paths'])} path{'s' if len(sp['paths']) != 1 else ''}")
    for p in sp["paths"]:
        if not (root / p).exists():
            print(f"  note: '{p}' is not in the brain yet")
    missing = [p["name"] for p in sp["people"] if not p.get("github")]
    if missing:
        print(f"  still to get: a GitHub username for {', '.join(missing)}")
    goals = root / goals_dir(team) / "goals.md"
    if not goals.exists():
        goals.parent.mkdir(parents=True, exist_ok=True)
        goals.write_text(TEAM_GOALS.format(team=team, today=_dt.date.today().isoformat()), encoding="utf-8")
        print(f"  started {goals.relative_to(root).as_posix()}: the team writes its three goals there")
    print(f"  every spoke also gets {FOR_TEAM}, the company's vision for staff, and its own goals")
    print("  the owners see every spoke: invite adds them")
    if not sp.get("description"):
        print(f"  no description yet: add a job title or what it does with --description")
    if not (root / FOR_TEAM).exists():
        print(f"  {FOR_TEAM} is not written yet. Ask Claude: 'Write {FOR_TEAM}: our vision on one page "
              "for all staff, and the company goals they should know, each with its [goal: id]. Leave out "
              "money, pay and any plan to sell. Show me before saving.'")
    print(f"next: save it with /done, then {SELF} check {team}")
    return 0


def cmd_check(root: Path, team: str) -> int:
    sp = load_spec(root, team)
    return 0 if build_and_gate(root, sp) else 1


def cmd_create(root: Path, team: str, owner: str | None, name: str | None) -> int:
    sp = load_spec(root, team)
    if sp.get("github"):
        print(f"the '{team}' spoke is already made: {sp['github']}. To send it the brain's latest: {SELF} release {team} --push")
        return 1
    why = hubtools.gh_ready()
    if why:
        print(why)
        return 1
    d = spoke_dir(root, team)
    hub = main_folder(root)
    repo = name or f"{re.sub(r'-ops$', '', hub.name)}-{team}"
    if owner is None:
        nwo = hub_nwo(root)
        owner = nwo.split("/")[0] if nwo else None
    if owner is None:                                      # the brain is not on GitHub: your own account
        owner = subprocess.run(["gh", "api", "user", "-q", ".login"], capture_output=True, text=True).stdout.strip() or None
    full = f"{owner}/{repo}" if owner else repo
    sp["github"] = full                                    # so the spoke's README names the right repo
    resume = (d / ".git").exists() and (d / RECORD).is_file() and "origin" not in git(d, "remote").stdout.split()
    if d.exists() and any(d.iterdir()) and not resume:
        print(f"{d} already exists. Move it aside, or ask Claude what is in it, then run this again.")
        return 1
    if resume:
        print(f"picking up where the last try stopped: {d} is saved but not on GitHub yet")
    else:
        b = build_and_gate(root, sp)
        if not b:
            return 1
        d.mkdir(parents=True, exist_ok=True)
        write_tree(b, d)
        if git(d, "init", "-q", "-b", "main").returncode != 0:
            git(d, "init", "-q")
            git(d, "checkout", "-q", "-b", "main")
        commit(d, f"Release from the brain ({b.rev[:8]})")
    r = subprocess.run(["gh", "repo", "create", full, "--private", "--source", str(d), "--remote", "origin", "--push"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"GitHub refused to make {full}:\n  {(r.stderr or r.stdout).strip()[:400]}")
        print(f"The spoke is saved at {d}. Run this again to finish; it picks up from there.")
        return 1
    v = subprocess.run(["gh", "repo", "view", full, "--json", "visibility", "-q", ".visibility"],
                       capture_output=True, text=True).stdout.strip()
    if v.upper() != "PRIVATE":
        print(f"made {full}, but GitHub reports it as {v or 'unknown'}. Make it private now: gh repo edit {full} --visibility private")
        return 1
    nwo = nwo_from_url(git(d, "remote", "get-url", "origin").stdout) or full
    if "/" not in nwo:
        nwo = subprocess.run(["gh", "repo", "view", full, "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                             capture_output=True, text=True).stdout.strip() or full
    set_spec_github(root, team, nwo)
    print(f"made the '{team}' spoke, private: {nwo}")
    print(f"  its folder on this laptop: {d}")
    print(f"  wrote github: {nwo} into specs/spokes/{team}.yml. Save it with /done.")
    print(f"next: {SELF} invite {team}   (everyone in the plan with a GitHub username)")
    return 0


def brain_owners(root: Path) -> list[str]:
    """Everyone with direct access to the brain. The brain is owners only
    (ADR-140 rule 1), so these are the owners, and they see every spoke."""
    nwo = hub_nwo(root)
    if not nwo:
        return []
    r = subprocess.run(["gh", "api", f"repos/{nwo}/collaborators?affiliation=direct", "--jq", ".[].login"],
                       capture_output=True, text=True)
    return [u.strip() for u in r.stdout.splitlines() if u.strip() and GH_USER.match(u.strip())] if r.returncode == 0 else []


def cmd_invite(root: Path, team: str, users: list[str]) -> int:
    sp = load_spec(root, team)
    if not sp.get("github"):
        print(f"the '{team}' spoke has not been made yet: {SELF} create {team}")
        return 1
    why = hubtools.gh_ready()
    if why:
        print(why)
        return 1
    known = {str(p.get("github") or "").lower() for p in sp["people"]}
    owners: list[str] = []
    if not users:
        users = [p["github"] for p in sp["people"] if p.get("github")]
        owners = brain_owners(root)
        if not users and not owners:
            print(f"nobody in specs/spokes/{team}.yml has a GitHub username yet. Add them with plan, or name them here.")
            return 1
    me = subprocess.run(["gh", "api", "user", "-q", ".login"], capture_output=True, text=True).stdout.strip().lower()
    seen = {me} if me else set()
    queue = []
    for u in users + owners:
        if u.lower() not in seen:
            seen.add(u.lower())
            queue.append(u)
    owner_set = {o.lower() for o in owners}
    failed = 0
    for u in queue:
        if not GH_USER.match(u):
            print(f"  '{u}' is not a GitHub username, skipped")
            failed += 1
            continue
        r = subprocess.run(["gh", "api", "-X", "PUT", f"repos/{sp['github']}/collaborators/{u}", "-f", "permission=push"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  GitHub refused the invite for {u}: {(r.stderr or r.stdout).strip()[:300]}")
            failed += 1
            continue
        if u.lower() in owner_set and u.lower() not in known:
            extra = " (an owner of the brain)"
        elif u.lower() in known:
            extra = ""
        else:
            extra = f" (not in specs/spokes/{team}.yml: add them to the plan so their team folder comes too)"
        print(f"  invited {u}{extra}")
    print(f"they say yes to GitHub's email, then join from their private space: {PY} scripts/oac-hub.py join {sp['github']}")
    return 1 if failed else 0


def cmd_release(root: Path, team: str, push: bool) -> int:
    sp = load_spec(root, team)
    d = ensure_clone(root, sp)
    if not d:
        return 1
    why = catch_up(d)
    if why:
        print(why)
        return 1
    b = build_and_gate(root, sp)
    if not b:
        return 1
    rec = read_record(d)
    old = rec.get("files") or {}
    waiting = []
    for p, h in old.items():
        if h.get("source") != "hub" or not (d / p).is_file():
            continue
        now = file_sha(d / p)
        new = norm_sha(b.files[p][0]) if p in b.files else None
        if now != h.get("sha256") and now != new:
            waiting.append(p)
    # A file the team added that the brain now also has, but different: no
    # record says who changed it, so a person decides, never this tool.
    in_spoke = set(tracked(d))
    for p, (data, _) in b.files.items():
        if p != RECORD and p not in old and p in in_spoke and file_sha(d / p) != norm_sha(data):
            waiting.append(p)
    if waiting:
        for p in waiting:
            print(f"waiting: {p} (changed by the team, not in the brain yet)")
        print(f"The team's work comes first: {SELF} pull-back {team}, save it in the brain with /done, then release. "
              "Nothing was released.")
        return 1
    removed = []
    for p, h in old.items():
        if p not in b.files and (d / p).is_file() and file_sha(d / p) == h.get("sha256"):
            (d / p).unlink()
            removed.append(p)
    for p, (data, source) in b.files.items():
        t = d / p
        if source != "hub" and t.is_file() and p in old and file_sha(t) not in (old[p].get("sha256"), norm_sha(data)):
            print(f"  replaced: {p} (a tool file changed in the spoke)")
    write_tree(b, d)
    for p in removed:
        print(f"  removed: {p} (no longer in the brain or the plan)")
    if commit(d, f"Release from the brain ({b.rev[:8]})"):
        print(f"released into {d}")
    else:
        print("nothing has changed since the last release")
    if push:
        r = git(d, "push", "-q", "-u", "origin", "main")
        if r.returncode != 0:
            print(f"could not send it to GitHub: {(r.stderr or r.stdout).strip()[:300]}")
            return 1
        print(f"sent to GitHub: {sp.get('github') or 'origin'}. The team gets it at their next /start.")
    else:
        print(f"nothing has left this laptop. To send it: {SELF} release {team} --push")
    return 0


def cmd_pull_back(root: Path, team: str) -> int:
    sp = load_spec(root, team)
    d = ensure_clone(root, sp)
    if not d:
        return 1
    why = catch_up(d)
    if why:
        print(why)
        return 1
    rec = read_record(d)
    if not rec.get("files"):
        print(f"{d} has no {RECORD}, so it is not a spoke this brain released.")
        return 1
    if len(hubtools.people(root)) > 1 and hubtools.current_branch(root) in ("main", "master", ""):
        print(f"more than one person works in the brain, so this goes on your branch: {hubtools.on_branch(root)}")
    handles = spoke_handles(sp)
    copied, conflicts, notes = [], [], []
    for p, h in sorted(rec["files"].items()):
        if h.get("source") != "hub":
            continue
        sf, hf = d / p, root / p
        if not sf.is_file():
            notes.append(f"{p}: deleted in the spoke. Left in the brain; delete it there if that is right.")
            continue
        s = file_sha(sf)
        if s == h.get("sha256"):
            continue                                       # the team did not touch it
        if hf.is_file() and file_sha(hf) == s:
            continue                                       # already pulled back
        if not hf.is_file() or file_sha(hf) != h.get("sha256"):
            conflicts.append(f"{p}: changed in the spoke and in the brain since the release. Merge it by hand.")
            continue
        shutil.copyfile(sf, hf)
        copied.append(p)
    added = [p for p in tracked(d) if p not in rec["files"] and p != RECORD]
    for p in added:
        why = never_reason(p, sp, handles, releasing=False)
        hf = root / p
        if why and p.startswith("team/") and p.count("/") >= 2:
            conflicts.append(f"{p}: a team folder for '{p.split('/')[1]}', who is not in this team's plan. "
                             f"Add them to specs/spokes/{team}.yml (or set their handle), then pull back again.")
        elif why:
            conflicts.append(f"{p}: added in the spoke, but it is a kind of file a spoke never shares back ({why}). Look at it by hand.")
        elif hf.is_file():
            if file_sha(hf) != file_sha(d / p):
                conflicts.append(f"{p}: added in the spoke, and the brain has a different file there. Merge it by hand.")
        else:
            hf.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(d / p, hf)
            copied.append(p + "  (new)")
    for p in copied:
        print(f"pulled back: {p}")
    for n in notes:
        print(f"note: {n}")
    for c in conflicts:
        print(f"CONFLICT: {c}")
    if not copied and not conflicts:
        print(f"nothing new from the '{team}' spoke since the release")
    elif copied:
        print("Read the changes in the brain (ask Claude to show you), then save them with /done. "
              f"Then {SELF} release {team} --push, so the team has the brain's latest.")
        new_outside = [p for p in added if not any(under(p, x if x.endswith('/') else x) for x in sp["paths"])
                       and not p.startswith("team/")]
        for p in new_outside:
            print(f"  note: {p} is outside the team's listed folders. Add its folder to the plan to keep it in the spoke.")
    return 1 if conflicts else 0


def cmd_list(root: Path) -> int:
    specs = sorted((root / SPECS).glob("*.yml")) if (root / SPECS).is_dir() else []
    if not specs:
        print(f"no spokes yet. Start with: {SELF} plan")
        return 0
    for f in specs:
        sp = load_spec(root, f.stem)
        d = spoke_dir(root, f.stem)
        rec = read_record(d) if (d / RECORD).is_file() else {}
        names = ", ".join(p["name"] for p in sp["people"]) or "nobody yet"
        print(f"{f.stem}: {sp.get('title') or ''} ({sp['kind']})")
        if sp.get("description"):
            print(f"  what it is: {sp['description']}")
        print(f"  people: {names}")
        print(f"  folders: {', '.join(sp['paths']) or 'none yet'}")
        print(f"  on GitHub: {sp.get('github') or 'not made yet'}")
        print(f"  on this laptop: {d if d.exists() else 'not here'}"
              + (f", last release from {rec.get('hub_rev', '')[:8]}" if rec else ""))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="A team's part of the business brain: one private repo per team (ADR-140).")
    ap.add_argument("--root", default=".", help="the brain (default: here)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan", help="the spokes so far, or write one team's plan")
    p.add_argument("team", nargs="?")
    p.add_argument("--people", nargs="*", help='"Full Name:github-user", one per person')
    p.add_argument("--paths", nargs="*", help="folders (ending in /) and files this team gets")
    p.add_argument("--title")
    p.add_argument("--block", nargs="*", help="words that must never reach this team")
    p.add_argument("--kind", choices=KINDS, help="a department, one person, or an AI role")
    p.add_argument("--description", help="a job title, or what the department does")
    for verb, helptext in (("check", "build and gate it, change nothing"),
                           ("pull-back", "bring the team's changes into this folder of the brain")):
        s = sub.add_parser(verb, help=helptext)
        s.add_argument("team")
    c = sub.add_parser("create", help="make the spoke, private, on GitHub")
    c.add_argument("team")
    c.add_argument("--owner", help="a GitHub organisation (default: the brain's own owner)")
    c.add_argument("--name", help="the repo's name (default: <brain>-<team>)")
    i = sub.add_parser("invite", help="push access for the team")
    i.add_argument("team")
    i.add_argument("users", nargs="*")
    r = sub.add_parser("release", help="bring the brain's latest into the spoke")
    r.add_argument("team")
    r.add_argument("--push", action="store_true", help="send it to GitHub too")
    sub.add_parser("list", help="every spoke, who is in it, where it lives")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    if git(root, "rev-parse", "--git-dir").returncode != 0:
        print(f"{root} is not the brain's folder. Run this in the business repo.")
        return 1
    if a.cmd == "plan":
        return cmd_plan(root, a.team, a.people, a.paths, a.title, a.block, a.kind, a.description)
    if a.cmd == "check":
        return cmd_check(root, a.team)
    if a.cmd == "create":
        return cmd_create(root, a.team, a.owner, a.name)
    if a.cmd == "invite":
        return cmd_invite(root, a.team, a.users)
    if a.cmd == "release":
        return cmd_release(root, a.team, a.push)
    if a.cmd == "pull-back":
        return cmd_pull_back(root, a.team)
    return cmd_list(root)


if __name__ == "__main__":
    sys.exit(main())

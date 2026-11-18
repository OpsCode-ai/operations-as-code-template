#!/usr/bin/env python3
"""Keep this business's Operations as Code framework current from the OAC brain.

The OAC brain (opscode-hq ADR-125 Rule 5, ADR-129 Rule 2) serves the business
method by version at brain.opscode.ai/oac: what an /oac session says, in plain
words, and the words of every session (/start, /done, /oac help). This brings
the newest version down into `.oac/oac-framework.md`, the saved copy the
session reads, and never breaks a session: out of reach, the saved copy stands.

    python3 scripts/oac-brain.py fetch              # newest version, or keep the saved one
    python3 scripts/oac-brain.py version            # which version is saved
    python3 scripts/oac-brain.py section start      # one section of the saved copy (start, done, help, ...)
    python3 scripts/oac-brain.py next               # where the business goes next, from the brain
    python3 scripts/oac-brain.py next --show        # what `next` would send, sending nothing
    python3 scripts/oac-brain.py key | connect | headers   # as sac-brain.py; the same key opens both

This is sac-brain.py with the business brain's settings: the same code, so the
two never drift. The pack ships both files side by side.

What leaves the laptop: `next` sends which of the register's three tables
exist and whole numbers (how many processes run by hand, how many have a
file, how many files of the direction are still seeds, how many goals are due
a word), never a row, a name or a line anyone wrote. `--show` prints the
exact object first.

Settings, from the environment or this repo's `.env` (never committed):

    SAC_BRAIN_KEY   this install's key, from OpsCode
    OAC_BRAIN_URL   default https://brain.opscode.ai/oac
"""
from __future__ import annotations

import importlib.util
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str):
    path = HERE / name
    spec = importlib.util.spec_from_file_location(name.replace("-", "_").replace(".py", ""), path)
    mod = importlib.util.module_from_spec(spec)
    # Registered first: a dataclass in the loaded file looks its module up by name.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


sac = _load("sac-brain.py")

CACHE = Path(".oac") / "oac-framework.md"
REGISTER = Path("systems") / "register.md"
TEAM = Path("systems") / "team.md"
SHARED = Path("context-core") / "strategic-identity" / "from-self-as-code.md"
CONTEXT_CORE = Path("context-core")
PROCESS_LINK_RE = re.compile(r"\]\(\s*(?:\./)?processes/[^)]+\)")


def _optional(name: str):
    try:
        return _load(name) if (HERE / name).is_file() else None
    except Exception:
        return None


def _rows(table_body: str, reg) -> list[list[str]]:
    rows: list[list[str]] = []
    for _headers, body_rows in reg.tables(table_body):
        rows += body_rows
    return rows


def _cell(headers: list[str], row: list[str], name: str, reg) -> str:
    for i, h in enumerate(headers):
        if reg.normalise(h) == name and i < len(row):
            return row[i]
    return ""


def register_counts(root: Path, closed: list[str]) -> dict:
    """The register's tables by name, and the whole numbers the brain may
    take from it. Never a row."""
    out: dict = {"headings_present": []}
    path = root / REGISTER
    if not path.is_file():
        return out
    reg = _optional("systems-register.py")
    text = path.read_text(encoding="utf-8", errors="replace")
    fv = sac.version_of(text)
    if fv:
        out["framework_version"] = fv
    present = []
    for h in closed:
        if re.search(rf"^## {re.escape(h)}\s*$", text, re.M | re.I):
            present.append(h)
    out["headings_present"] = present
    if reg is None:
        return out
    try:
        errors, counts = reg.audit(path)
        out["register_problems"] = len(errors)
        runs = counts.get("runs", {})
        out["processes_manual"] = runs.get("manual", 0)
        out["processes_semi"] = runs.get("semi", 0)
        out["processes_automated"] = runs.get("automated", 0)
        via = counts.get("connects_via", {})
        out["connections"] = via.get("api", 0) + via.get("mcp", 0)
        found = reg.sections(text)
        software = places = processes = written = 0
        for name, body in found.items():
            for headers, rows in reg.tables(body):
                if name == "software":
                    software += len(rows)
                elif name == "where the work lives":
                    places += len(rows)
                elif name == "processes":
                    processes += len(rows)
                    for row in rows:
                        if PROCESS_LINK_RE.search(_cell(headers, row, "process", reg)):
                            written += 1
        out["software"], out["places"], out["processes"], out["processes_written"] = software, places, processes, written
    except Exception:
        pass
    return out


def direction_counts(root: Path) -> dict:
    """How many files of the direction are seeds, drafts and confirmed, by
    their `status:` line (no status means seeded). Never a line of them."""
    folder = root / CONTEXT_CORE
    if not folder.is_dir():
        return {}
    seeded = drafted = confirmed = 0
    for p in sorted(folder.rglob("*.md")):
        if p.name in ("fill-map.md", "from-self-as-code.md", "goals.md"):
            continue
        try:
            head = re.match(r"\A---\n(.*?)\n---\n", p.read_text(encoding="utf-8", errors="replace"), re.S)
        except Exception:
            continue
        m = re.search(r"^status:\s*[\"']?([a-z-]+)", head.group(1), re.M) if head else None
        status = m.group(1) if m else "seeded"
        if status == "seeded":
            seeded += 1
        elif status == "confirmed":
            confirmed += 1
        else:
            drafted += 1
    return {"direction_seeded": seeded, "direction_drafted": drafted, "direction_confirmed": confirmed}


def goal_counts(root: Path, today: date) -> dict:
    goals = _optional("oac-goals.py")
    if goals is None:
        return {}
    try:
        rows = goals.rows(root)
        by = {}
        for r in rows:
            s = goals.norm_status(getattr(r, "status", "") or "")
            by[s] = by.get(s, 0) + 1
        return {
            "goals": len(rows),
            "goals_due": len(goals.due(root, 7, today)),
            "goals_red": by.get("at risk", 0),
            "goals_amber": by.get("not started", 0),
            "goals_green": by.get("on track", 0) + by.get("done", 0),
        }
    except Exception:
        return {}


def people_count(root: Path) -> dict:
    path = root / TEAM
    if not path.is_file():
        return {}
    reg = _optional("systems-register.py")
    if reg is None:
        return {}
    try:
        n = 0
        for _h, rows in reg.tables(path.read_text(encoding="utf-8", errors="replace")):
            n += len(rows)
        return {"people": n}
    except Exception:
        return {}


def days_since_note(root: Path) -> dict:
    brief = _optional("oac-session-brief.py")
    if brief is None:
        return {}
    try:
        since = brief.days_since_note(root, brief.handle(root))
    except Exception:
        return {}
    return {"days_since_note": min(since, 9999)} if since is not None else {}


def progress(root: Path) -> dict:
    """Where the business is. The register's table names and whole numbers,
    never a row, a name or a line anyone wrote."""
    today = date.today()
    have, _v = sac.saved(root, OAC)
    closed = sac.plan_headings(have.decode("utf-8", "replace")) if have else []
    out: dict = {"today": today.isoformat()}
    out.update(register_counts(root, closed))
    out["shared"] = 1 if (root / SHARED).is_file() else 0
    out.update(direction_counts(root))
    out.update(goal_counts(root, today))
    out.update(people_count(root))
    out.update(days_since_note(root))
    return {k: v for k, v in out.items() if not isinstance(v, int) or (0 <= v <= 9999)}


OAC = sac.Brain(
    name="oac",
    default_url="https://brain.opscode.ai/oac",
    url_env="OAC_BRAIN_URL",
    cache=CACHE,
    header="OAC-Framework",
    server="oac-brain",
    helper="python3 scripts/oac-brain.py headers",
    script="oac-brain.py",
    progress=progress,
)


def main(argv: list[str] | None = None) -> int:
    return sac.main(argv, brain=OAC)


if __name__ == "__main__":
    sys.exit(main())

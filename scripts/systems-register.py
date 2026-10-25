#!/usr/bin/env python3
"""Read and check a systems register against the OaC `systems` profile.

    python3 code/scripts/systems-register.py --check
    python3 code/scripts/systems-register.py --baseline
    python3 code/scripts/systems-register.py --baseline --json

WHY THIS EXISTS
    `specs/oac-vocabulary.yml` says of the systems profile: "No source: yet, no
    reader ships." Nothing has ever read a register except one grep inside the
    session briefing, counting manual rows.

    That is exactly how the profile broke the first time. Filling the register
    on 12 September found a spec bug: a **bolded** enum cell defeats the grep
    the whole profile rests on, so `| **manual** |` counts as nothing and the
    number that is supposed to sell the next engagement quietly reads low. The
    fix went into 1.8 as 'a closed cell carries the BARE value'. A rule with no
    checker is a rule that gets broken again.

    This is the checker. It is also what makes the register usable at install
    time: the three closed columns are the only machine-readable thing in the
    profile, and the install has to trust them.

WHAT IT CHECKS
    Three closed columns, found by header name, case-insensitively:

        connects_via   api | mcp | scrape | none
        runs           manual | semi | automated
        call           keep | automate | build | replace | retire

    A cell must carry the bare value. Bold, code ticks, or a trailing note are
    all errors, because every consumer of this profile is a grep. Any column
    the profile does not recognise is free text and is never checked. A missing
    section means it was not captured, which the spec calls out as 'never an
    error'.

WHAT IT DOES NOT DO
    It does not invent rows, judge the calls, or care whether `Cost/mo` is
    filled. An empty cost column is a gap against a source nobody has
    connected, not a fault in the document.

Standard: specs/oac-file-format.md section 7. Decision: ADR-118.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# The profile's three closed columns. Keys are the normalised header name.
CLOSED = {
    "connects via": ("connects_via", ("api", "mcp", "scrape", "none")),
    "connects_via": ("connects_via", ("api", "mcp", "scrape", "none")),
    "runs": ("runs", ("manual", "semi", "automated")),
    "call": ("call", ("keep", "automate", "build", "replace", "retire")),
}
SECTIONS = ("software", "where the work lives", "processes")
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.M)
SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|$")


def normalise(h: str) -> str:
    return re.sub(r"\s+", " ", h.strip().strip("*` ").lower())


def split_row(line: str) -> list[str]:
    """Cells of a GFM table row, without the leading and trailing pipes."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def sections(text: str) -> dict[str, str]:
    """Body of each recognised level-two section, keyed by normalised name."""
    out: dict[str, str] = {}
    marks = [(m.start(), normalise(m.group(1)), m.end())
             for m in H2_RE.finditer(text)]
    for i, (_, name, end) in enumerate(marks):
        stop = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        if name in SECTIONS:
            out[name] = text[end:stop]
    return out


def tables(body: str) -> list[tuple[list[str], list[list[str]]]]:
    """Every GFM table in a section, as (headers, rows)."""
    found: list[tuple[list[str], list[list[str]]]] = []
    lines = body.splitlines()
    i = 0
    while i < len(lines) - 1:
        line, nxt = lines[i].strip(), lines[i + 1].strip()
        if line.startswith("|") and SEPARATOR_RE.match(nxt):
            headers = split_row(line)
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(split_row(lines[j]))
                j += 1
            found.append((headers, rows))
            i = j
            continue
        i += 1
    return found


def audit(path: Path) -> tuple[list[str], dict[str, dict[str, int]]]:
    """Errors, and the counts per closed column."""
    errors: list[str] = []
    counts: dict[str, dict[str, int]] = {}
    text = path.read_text(encoding="utf-8", errors="replace")

    found = sections(text)
    if not found:
        errors.append("no recognised section: expected one of "
                      + ", ".join(f"'## {s}'" for s in SECTIONS))
        return errors, counts

    for name, body in found.items():
        for headers, rows in tables(body):
            closed_at = {}
            for idx, h in enumerate(headers):
                key = normalise(h)
                if key in CLOSED:
                    closed_at[idx] = CLOSED[key]
            for row in rows:
                for idx, (col, legal) in closed_at.items():
                    if idx >= len(row):
                        errors.append(
                            f"{name}: a row is short of the '{col}' column: "
                            f"{' | '.join(row)[:60]}")
                        continue
                    raw = row[idx]
                    bare = normalise(raw)
                    bucket = counts.setdefault(col, {})
                    if bare in legal:
                        if raw.strip() != bare:
                            errors.append(
                                f"{name}: '{col}' cell is not bare: {raw!r}. "
                                "Emphasis and ticks defeat the grep this "
                                "profile rests on (ADR-118).")
                        bucket[bare] = bucket.get(bare, 0) + 1
                    elif raw.strip() == "":
                        bucket["(empty)"] = bucket.get("(empty)", 0) + 1
                    else:
                        errors.append(
                            f"{name}: '{col}' has {raw!r}, which is not one of "
                            + "/".join(legal))
    return errors, counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=".", help="repo to read")
    ap.add_argument("--check", action="store_true",
                    help="validate against the profile. The default")
    ap.add_argument("--baseline", action="store_true",
                    help="print the counts that make the register worth keeping")
    ap.add_argument("--json", action="store_true", help="machine-readable")
    a = ap.parse_args()

    reg = Path(a.root).resolve() / "systems" / "register.md"
    if not reg.is_file():
        if a.json:
            print(json.dumps({"present": False}))
        else:
            print(f"\n  no systems register at {reg}")
            print("  a business plane wants one (ADR-118); a self plane does not\n")
        return 0 if a.json else 1

    errors, counts = audit(reg)

    if a.json:
        print(json.dumps({"present": True, "errors": errors, "counts": counts},
                         indent=2))
        return 1 if errors else 0

    print(f"\n  systems register: {reg}")

    if a.baseline or not a.check:
        runs = counts.get("runs", {})
        total = sum(runs.values())
        if total:
            print(f"\n  {total} process(es) recorded")
            for value in ("manual", "semi", "automated"):
                n = runs.get(value, 0)
                mark = "  <- the number to watch" if value == "manual" and n else ""
                print(f"    {value:<10} {n}{mark}")
        call = counts.get("call", {})
        if call:
            print("\n  calls made")
            for value, n in sorted(call.items(), key=lambda kv: -kv[1]):
                print(f"    {value:<10} {n}")
        via = counts.get("connects_via", {})
        if via:
            reachable = sum(n for v, n in via.items() if v in ("api", "mcp"))
            print(f"\n  {reachable} system(s) an agent can reach"
                  f" ({via.get('api', 0)} api, {via.get('mcp', 0)} mcp)")

    if errors:
        print(f"\n  {len(errors)} problem(s):")
        for e in errors:
            print(f"    - {e}")
        print()
        return 1

    print("\n  clean against the systems profile\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

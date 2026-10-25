#!/usr/bin/env python3
"""Pre-commit check: owner-audience markdown never enters the shared repo.

ADR-111 hard rule: anything `audience: owner` (old spelling `adam`) belongs
in the operator's personal ops repo ({first}-{last}-ops), never here. This
check reads every STAGED markdown blob (the same judge-the-index approach
as the frontmatter check) and blocks the commit if one declares an owner
audience.

Exempt paths, where owner-audience frontmatter is legitimate because the
files ship INTO another repo rather than living in this one:
  - code/plans-pages/*/pack/   (customer pack material)
  - templates/                 (scaffolds and examples)

Exit 0 = clean, 1 = blocked. Run by .githooks/pre-commit.
"""
from __future__ import annotations

import re
import subprocess
import sys

EXEMPT = re.compile(r"^(code/plans-pages/[^/]+/pack/|templates/)")
OWNER = re.compile(r"^audience:\s*[\"']?(owner|adam)\b", re.M)


def staged_paths() -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [p for p in out.splitlines() if p.endswith(".md")]


def staged_blob(path: str) -> str:
    r = subprocess.run(["git", "show", f":{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def main() -> int:
    offenders = []
    for path in staged_paths():
        if EXEMPT.match(path):
            continue
        text = staged_blob(path)
        # Only judge the frontmatter block, not prose that quotes the rule.
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        front = text[: end if end != -1 else len(text)]
        if OWNER.search(front):
            offenders.append(path)

    if not offenders:
        return 0

    print("❌ BLOCKED: owner-audience document(s) staged in the shared repo (ADR-111)")
    for p in offenders:
        print(f"   {p}")
    print()
    print("Anything `audience: owner` belongs in your personal ops repo")
    print("({first}-{last}-ops), never in a shared Operations as Code repo -")
    print("every collaborator can read the whole tree.")
    print()
    print("Fix: move the file to your personal repo (no repo yet? run")
    print("  python3 code/scripts/setup-personal-ops-repo.py --check )")
    print("or, if the audience is wrong, change it to internal/team/public.")
    print("See decisions/111-private-information-and-the-personal-ops-repo.md")
    return 1


if __name__ == "__main__":
    sys.exit(main())

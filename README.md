---
title: "Operations as Code: this business"
type: index
audience: internal
---

# Operations as Code: this business

One repo. What the business runs on, and what it is aiming at, written down
where an agent can read it and a person can check it.

- `CLAUDE.md`: read first, every session
- `systems/register.md`: what runs today. Fill it with `/oac`
- `context-core/`: what the business is aiming at. Each folder has a README
  that says what goes in it
- `decisions/`: choices already made
- `team/`: one folder per person, the continuity logs `/start` and `/done` keep
- `inbox/`: one folder per person for the files that came off each laptop.
  Copies, never originals; sort from here as you go
- `INSTALL.md`: how this folder became a repo, and the prompt that did it
- `STATUSLINE.md`: the Claude Code statusline every operator runs
- `WORKING.md`: sessions, continuity, checkpoints, worktrees
- `MODES.md`: SAC, OAC and AIDLC, and which commands belong to each
- `scripts/oac-upgrade.py`: take a newer pack without losing what you wrote. `WORKING.md` says how
- `.claude/`: the commands

Start with `/install`, then `/oac`. Every session after that: `/start`
first, `/done` last.

## How this works

**What you see when you open it.** Claude Code shows a message at the top,
and it changes. The first time: Operations as Code, one command, the loop.
After that: a manifest of where things stand, what moved since your last
session, where you left off, the manual count, what is open. It is written
into `.claude/settings.json` by `scripts/oac-session-brief.py --announce
--write` at the end of every session, so the next open is current. The
bottom line of the screen says `OAC`, read from `.oac/manifest.yml`. If it
says `SAC` you are in a self plane; if it says nothing you are outside an
OpsCode repo.

**One door.** `/oac` is the only command you need for the method. It runs the
install order as a conversation, then writes what the business runs on, then
what it is aiming at, then one process at a time. Each part is shown to you
and written on your yes. You never choose a path, and you never run a script.
Typed again later, it does the next thing, not the first one again.

**The loop.** `/start` reads where you left off, `/done` commits by path,
pushes, and writes your continuity note. Nothing lands without both.

**When the pack moves.** Download the new zip, unzip it beside this repo, and
run `python3 scripts/oac-upgrade.py --from <that folder> --apply`. It adds
what is new and never writes what you wrote. `WORKING.md` has the detail.

**When you want to build software.** OpsCode's build tools (AI-DLC by AWS
Labs, with OpsCode's additions) are an add-on for a business that wants to
build software. They are not in this pack. When that day comes they are
installed then, and they start from the register and the Context Core you
wrote here. `MODES.md` says more.

---
title: "CLAUDE.md: this business, written down"
type: guide
audience: internal
---

# CLAUDE.md: this business, written down

This file is the first thing Claude Code reads, every session. It says what
this repo is, how it is shaped, and the rules that keep it honest.

> Run `/install` on first open, then `/oac`. Files marked
> `status: seeded` are first passes: **every file here is meant to be
> altered.** The structure ships ready; the content is yours.

## What this repo is

The Operations as Code repo for one business: a **business plane**. It has two
halves, and the test that settles which half a thing belongs in is simple. If
two people can disagree about it, it is Context Core. If you can go and look,
it is systems.

| Half | Folder | Question it answers |
|---|---|---|
| Systems | `systems/` | What does this business run on today? Software, where the work lives, the repeated processes and which ones still run by hand |
| Context Core | `context-core/` | What is this business aiming at, and for whom? Identity, offer, voice, customers, market |

`decisions/` sits beside both: the record of choices already made, so a later
session never re-debates a settled one.

## Where your own identity lives

Not here. You ran Self as Code in your **self plane**, a private repo of your
own. What you chose to share from it arrives in
`context-core/strategic-identity/` as short statements, by your decision, and
nothing else crosses. Anyone who works in this business can read this repo;
that is the point of it, and the reason your identity stays in the other one.

## Rules

1. **Every document carries frontmatter**: `title`, `type`, `audience`, at
   least. Lists in flow style (`topics: [a, b]`). Check with
   `python3 scripts/oac-validate.py .`
2. **Nothing `audience: owner` is ever written here.** That value belongs to a
   self plane. If something is personal, it goes in yours.
3. **Never invent a business fact.** A price, a process, a supplier, a number.
   If it is not written down yet, mark it `TO FILL IN` and ask.
4. **Bare values in the register's closed columns.** `| manual |`, never
   `| **manual** |`. A grep counts them, and emphasis makes a row invisible.
5. **AU English, plain language, no em dashes, no AI clichés.**

## The commands

| Command | When |
|---|---|
| `/install` | First open. Reads the shape, validates, reports the fill-map |
| `/oac` | The one door. The install order (validate from Self as Code, software, team, the chaos exercise, connectors, GitHub), then the register, the Context Core and process capture, each shown to you and written on your yes. Typed again later it does the next thing, not the first thing again |
| `/start` | Every session. Reads your continuity log, the register count, the git state |
| `/done` | Every session. Validates, writes your continuity log, commits by path, pushes |
| `/task-bridge` | Any time you step away mid-thought |
| `/create-adr` | A decision worth not debating twice |
| `/build-log` | After a substantial build |

`/start` and `/done` are not optional. They are the loop that means any
session on any machine picks up where the last one stopped. `team/` holds
the logs, one folder per person.

## When you want to build software

Not in this pack. OpsCode's build tools are an add-on for the day this
business wants to build software; they are installed then, and they start from
the register and the Context Core you wrote here. `MODES.md` says more.

## The git hook

`.githooks/pre-commit` runs on every commit: a secret scan when gitleaks is
installed, the owner-audience rule, and the frontmatter check. It is enabled
by `git config core.hooksPath .githooks`, which the installer prompt does.
When it blocks, it says why. Fix that; do not add `--no-verify`.

## The statusline, and the briefing

`STATUSLINE.md` explains the line at the bottom of Claude Code and how to
install it. Every OpsCode operator runs the same one. Install once per
machine: `python3 scripts/install-oac-statusline.py`.

Every session opens with a short briefing (`scripts/oac-session-brief.py`, a
SessionStart hook): what moved since yesterday, what you left off, who else
worked and where, the register count, and the suggested focus when your log
has none. Read it before you type.

`WORKING.md` is how we work: the `/start`, `/task-bridge`, `/done` loop,
`/checkpoint` and `notable-plans/` for a build bigger than one session, and
worktrees from the day a second session touches this repo. `MODES.md`
explains the word in capitals on the statusline, `SAC`, `OAC` or
`AIDLC`: what each mode is for, which repo it lives in, and which commands
belong to it. The statusline also logs each session's usage on your machine;
`python3 scripts/oac-usage-report.py --write` turns that into
`team/<you>/usage.md`, which `/done` refreshes.

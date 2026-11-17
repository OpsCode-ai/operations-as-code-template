---
title: "What this business's repo makes"
type: spec
audience: internal
status: seeded
---

# What this business's repo makes

One file that says what gets made from this repo, how often, and how it all
looks. Everything made for the business reads this first.

## The look

The look lives in one place: `standards/brand.md`. How the business sounds is
`context-core/voice/`. Change either there, never in one output. Until the
look is written, anything made here is plain black on white.

## What gets made

| What | What it shows | Reads | How often | Kept at |
|---|---|---|---|---|
| The dashboard | the business on one page: what it runs on, what still runs by hand, where each goal stands, what moved this week | `systems/register.md`, `context-core/strategic-identity/goals.md`, `team/*/current.md` | any time | `.oac/dashboard.html` |
| The owner's word on each goal | where every goal the owner sent here stands | `context-core/strategic-identity/goals.md` | at `/done`, once a goal's last word is a week old | the file itself |
| The weekly report | what moved, what is blocked, which goals changed | the logs in `team/`, `systems/`, git | Friday | `team/<handle>/reports/` |
| A proposal | what a buyer is offered, every line traced to its source | `standards/transcript-to-proposal-standard.md` | when one is sent | the engagement's folder |
| An email | one ask, in the business's voice | `context-core/voice/`, `standards/outputs/email.md` | as sent | `context-core/correspondence/` |

Add a row when the business wants something else made. Nothing here is made
until someone asks for it. This file is the list.

## The rules every output follows

- One file that opens in a browser. Nothing loaded from the web, so it works
  with no internet.
- The business's look, from `standards/brand.md`. Its words, from
  `context-core/voice/`.
- The page for its kind under `standards/outputs/` says how it is checked.
- Every number says where it came from. Anything that cannot be grounded is
  marked, never guessed.
- Made for this business, not off the shelf. Never the look every AI tool
  makes: the purple fade, the same rounded cards, the same font on every
  page, code font for ordinary words, boxes inside boxes.

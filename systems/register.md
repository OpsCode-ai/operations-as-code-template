---
title: "Systems register"
type: reference
audience: internal
status: seeded
lifecycle: living
version: 1.0
last_updated: 2026-09-12
summary: "What this business runs on today: the software, where the work lives, and the processes. What is true right now, not what we are aiming at."
topics: [tooling, operations]
tags: [oac, systems-register, seeded]
---

# Systems register

This is what the business runs on **today**. Not the plan, not the goal. The
tools you pay for, the places your work actually sits, and the jobs that get
done over and over.

It sits beside the Context Core on purpose. The Context Core holds what you are
aiming at and who you serve, and reasonable people can argue about it. This file
holds things you can go and check. If two people disagree about something here,
one of them is wrong and you can find out which.

Standard: [OaC File Format 1.8](https://opscode.ai/spec), profile `systems`.

## How to fill it

**You do not fill this in from memory.** Memory misses about half the tools and
all of the cheap ones. Go and look:

1. Your bank or card statement for the last three months. Every subscription is
   in there.
2. The apps open on your machine right now, and the tabs you keep pinned.
3. Your password manager, if you use one. That list is usually the best one.

Ask Claude Code to read those and draft the rows. Then correct it. Correcting a
draft takes ten minutes; a blank table takes an hour and never gets done.

## The three columns that have to be exact

Everything else is free text. These three are closed lists, because they get
counted:

| Column | Write one of | What it means |
|---|---|---|
| `Connects via` | `api` · `mcp` · `scrape` · `none` | How your AI could reach it |
| `Runs` | `manual` · `semi` · `automated` | Who or what does the work now |
| `Call` | `keep` · `automate` · `build` · `replace` · `retire` | What you decided to do about it |

**`Runs` is the one that matters most.** Count the manual rows today and write
the number down. That number going down is the whole point of the work.

**Write the value plain.** `manual`, not `**manual**`. Bolding it to make it
stand out breaks the counting, which is the only reason the column is closed.

**`Call` is a decision, not a wish.** Leave it `keep` until you have actually
decided. A register where everything says `automate` tells you nothing.

For `Connects via`, work down the list and stop at the first yes: does it have
an API, does it have an MCP, can a browser tool sign in and read it, or is it
`none`.

Here is the shape. Yours will look like this once it is filled:

```markdown
| System | What it does | Owner | Cost/mo | Connects via | Call |
|---|---|---|---|---|---|
| Xero | invoices and payroll | Jane | $70 | api | automate |
| ClickUp | job tracking | Sam | $120 | mcp | replace |
```

---

## Software

Every tool the business pays for or leans on. One row each.

*TO FILL IN [source: extract]. Draft from the statement, the app switcher and
the password manager, then correct it.*

| System | What it does | Owner | Cost/mo | Connects via | Call |
|---|---|---|---|---|---|

## Where the work lives

Every place files or records actually sit. Include the messy ones: a laptop
desktop, a shared drive nobody owns, a personal email account. Those are the
rows that explain why things go missing.

*TO FILL IN [source: head-only]. Nobody can extract this one. It is the
whiteboard exercise.*

| Place | What's in it | Owner | Connects via |
|---|---|---|---|

## Processes

The jobs that happen again and again. Start with the ones that happen weekly or
monthly, and the ones that only you can do.

*TO FILL IN [source: transcript]. These surface as you talk through the
business, so let sessions fill it rather than sitting down to write it.*

| Process | Cadence | Runs | Owner | Systems | Call |
|---|---|---|---|---|---|

---

## What this is not

**Not a wish list.** A row goes in when it is true today. What you are planning
belongs in a decision record or a project.

**Not the strategy.** Who you sell to, what you charge and how you talk belong
in the Context Core.

**Not a place for passwords.** Name the tool and who owns it. Never the login.
Credentials live in a password manager, and this file is in git.

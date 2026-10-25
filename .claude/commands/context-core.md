---
title: "/context-core: the business's direction, drafted from evidence"
type: guide
audience: internal
summary: "The second stage of /oac, the plain way: fill the Context Core from what already exists, every draft naming its sources, then bring the operator only the gaps that live in nobody's files but their head. Starts from what Self as Code shared. Records, never confirms. The same method the opscode-oac-context-core stage runs on the engine, with the operator's yes in place of the gate."
topics: [operations, onboarding]
tags: [oac, command, context-core, adr-125, adr-130]
---

# /context-core: the business's direction, drafted from evidence

`/oac` runs this once the register exists. It can also be typed on its own.
The register is what you can go and look at. The Context Core is what two
people could disagree about: what the business is, who it serves, what it
charges and why, how it sounds, where it is going. Written down with a source,
in the operator's words, so the disagreement happens on a page and not in a
meeting.

A pack ships `context-core/` as folders with READMEs and marked gaps. Most of
those gaps are not in the operator's head. They are in a proposal, a price
list, the website, the register, or in what Self as Code shared. Close those
first. Bring the operator only what is head-only, three at most in a session.

## Before anything: where you are

```bash
grep '^plane:' .oac/manifest.yml
python3 scripts/systems-register.py --baseline
```

`plane: self` means stop: a Context Core describes a business, and this is
someone's own repo. Say so and point at the business repo. No register means
the audit has not run yet: `/oac` starts there. Otherwise carry on.

Say nothing about planes, engines or stages to the operator. Say 'your
business's direction'.

## Step 0: read what is already true, in this order

1. `context-core/strategic-identity/from-self-as-code.md`, when it exists.
   The lines the owner chose to share from their own Self as Code: the kind
   of business, who it serves, how long it has run and how many people, what
   it runs on, what to build first, the six-month target. It is the top of
   the core and it is not yours to edit. Never ask what it already answers.
   When it is missing, note that nothing has been shared yet and carry on.
2. `systems/register.md` and `systems/team.md`. The Software table answers
   hosting and tooling; the team table answers `organisation/`; the Processes
   table answers half of `operations/`. Anything the register answers is not
   a gap.
3. `context-core/README.md`, then every folder README under `context-core/`.
   They say what belongs in each folder and what state it is in.
4. The business's own website, and any document the operator already has
   open: a proposal, a price list, a client email thread.

## Step 1: the fill map

Walk every file under `context-core/` and `decisions/`. Read its `status`
(`seeded`, `draft` or `confirmed`; no status means `seeded`). Write
`context-core/fill-map.md` with one table:

`File | Status | What is missing | Best source`

`Best source` is closed:

| Value | Meaning |
|---|---|
| `self-as-code` | `from-self-as-code.md` already says it |
| `register` | the systems register or `systems/team.md` already answers it |
| `existing-docs` | a document the business already has answers it: a quote, a contract, a proposal, a client email |
| `system` | a tool holds it and it can be pulled: the CRM, the accounts, the job manager |
| `web` | the business's own website or a supplier's answers it |
| `transcript` | a session or call already in `context-core/voice-stream/` or `meetings/` answers it |
| `head-only` | it exists nowhere written |

Then the count per source, and the head-only gaps ranked by how much the
business is blocked without them. A report, not a to-do avalanche. Its
frontmatter: `type: report`, `audience: internal`, `generated: true`,
`derived_from:` the files it read.

## Step 2: draft from evidence, cheapest source first

- `self-as-code`: the shared lines seed `strategic-identity/` and
  `business/what-it-is.md`. Quote them. Do not reword them.
- `register`: `organisation/org-today.md` is the team table in prose with a
  reporting line; hosting and tooling in `operations/` is the Software table,
  filtered. Cite the register by section.
- `existing-docs`: ask for the document by name, once, then read it. A price
  list answers `value-offers/`; a proposal answers `business/`; a client
  thread answers `voice/`.
- `system`: pull it only through a connected tool (the register's `Connects
  via` says which). If it is `none`, the gap stays open and the map says why.
- `web`: read the pages the operator names. What a visitor can already read
  is not head-only.
- `transcript`: a landed session or call often answers messaging and voice
  better than any interview would.

Every draft is a complete document at its path under `context-core/`, with
frontmatter: `title`, a `type` from the vocabulary, `audience: internal`,
`status: draft`, `version` (bumped, or `1.0` for a new file), `updated`,
`generated: true`, and `sources:` or `derived_from:` naming where each claim
came from (OaC spec 3.10; rule 7). **A sentence with no source does not go
in.** A fact you cannot ground is marked `TO FILL IN` with its best source,
never guessed.

The identity test, in reverse: a cost, a cadence or a tool name that turns up
while you read is a register row, not a Context Core sentence. Put it under
`## Register amendments` in the fill map and leave it out of the draft.

## Step 3: show it, then write it

Before writing a file, show the operator what it will say and where its lines
came from, and ask: does this stand? On yes, write it at its path at `status:
draft`, never `confirmed`, and add one line to `CHANGELOG.md`: the date, the
file, what changed, the source. On no, change it or drop it. Only the operator
marks a file `confirmed`, and only after reading it back. You record; you
never confirm.

## Step 4: the head-only gaps, three at most

Ask in the operator's own words, and ask for the story, not the field: 'tell
me about the last job where the budget went wrong' gets a costing judgement;
'what is your costing judgement' gets a shrug. Write each answer as they said
it, tidy the grammar and nothing else, with `sources: ['the operator,
<date>']`. Their voice is the asset. Show it, then write it, as in step 3.

Everything you did not get to goes under `## Left for the operator` in the
fill map: the file, the gap, the source, and the one question that would
close it. That section is the next session's opening move.

## Step 5: check and close

```bash
python3 scripts/oac-validate.py .
python3 scripts/check-grounding.py --staged
```

Then say, in plain words: how many gaps the evidence closed, how many you
asked about, and what is left and where. Commit the drafts by path.

## Where the engine is installed

In a repo with OpsCode's build tools installed and the doctor clean, `/oac`
runs this same method as the `opscode-oac-context-core` stage, with a
reviewer and a gate. This file is the method without the engine. They do not
differ in what they write, or in what they refuse to write.

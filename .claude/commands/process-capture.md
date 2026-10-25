---
title: "/process-capture: one manual process, written down by watching it"
type: guide
audience: internal
summary: "The third stage of /oac, the plain way: take one manual or semi row from the register, watch the operator do it once, and write it down as systems/processes/<slug>.md with Prerequisites, Steps, Verification and The call, then link the row. One row per run. If Self as Code shared a 'build first' line, that is the row. The same method the opscode-oac-process-capture stage runs on the engine, with the operator's yes in place of the gate."
topics: [operations, onboarding]
tags: [oac, command, process-capture, sop, adr-125]
---

# /process-capture: one manual process, written down by watching it

The register has one number that matters: how many processes still run by
hand. This takes one of them and writes it down, so the next person, or the
next agent, can run it without asking. Writing it down does not move the
number. It is the step before the number can move, because nothing can be
automated that nobody can describe.

One row per run. Three written from a blank page is an hour of typing that
produces three documents nobody reads. One, captured by watching it happen,
is twenty minutes and it is true.

## Before anything

```bash
grep '^plane:' .oac/manifest.yml
python3 scripts/systems-register.py --baseline
```

`plane: self` means stop: processes belong to a business. No register means
the audit has not run yet: `/oac` starts there. Say nothing about planes,
engines or stages to the operator. Say 'the next process'.

## Step 0: pick the row

List the `## Processes` rows whose `Runs` is `manual` or `semi` and whose
`Process` cell does not yet link to a file under `systems/processes/`.
Suggest one, with the reason, and let the operator choose. The default is the
one that costs most: minutes times cadence. **If Self as Code shared a 'build
first' line** ('if your AI could take one thing off your plate in this
business'), that is the row, and say so: it is the first thing this
business's AI does for them. Never pick silently. The operator is about to
spend twenty minutes on it.

## Step 1: watch it, do not ask about it

Have the operator do the process once, now, with the real tools, while you
write down each step as it happens. 'Show me' beats 'tell me': a described
process misses the check nobody thinks of as a step, and the workaround
everybody thinks of as normal. For each step capture who or what does it, the
tool, the exact click or command, the input, the output, and the decision if
there is one. Time it.

Where evidence of earlier runs exists, read it: the last three invoices, the
sent folder, the commits, the export. Two runs that differ are a decision
point the operator did not mention.

## Step 2: write the procedure

`systems/processes/<slug>.md`, the slug being the process name in kebab case.
Frontmatter:

- `title`, `type: standard`, `audience: internal`, `status: draft`,
  `lifecycle: living`, `version: 1.0`, `updated`, `summary`, `topics` and
  `tags` in flow style
- `process:` the register row's `Process` cell, exactly, so a grep joins them
- `cadence`, `runs`, `owner` and `systems` copied from the row, bare values
- `time_minutes:` what you measured, not what the operator estimated
- `generated: true` and `sources: ['watched with <name>, <date>']`, plus any
  evidence you read (rule 7)

Then the body, in this order:

- **Purpose**: one sentence, why the business does this at all
- **`## Prerequisites`**: a checklist of access, tools and inputs. Everything
  the operator had open before step one
- **`## Steps`**: numbered. Each step names the tool, the exact action, and
  what you see when it worked. A decision is written as a step with its
  branches, not as a note
- **`## Verification`**: how you know the whole thing worked, and what to
  check when it did not
- **`## The call`**: `keep`, `automate`, `build`, `replace` or `retire`, with
  the reason now that the process is in front of you. If the call is
  `automate`, say what it would need: which of the row's systems connect via
  `api` or `mcp`, and which are `none`. A process whose every system is `none`
  is not honestly `automate` yet; say `build` or `keep`, and say why

Australian English, plain words, the operator's names for things. A new hire
reads this on their first morning.

## Step 3: show it, write it, link the row

Read it back to the operator, step by step. On their yes, write the file.
Then in `systems/register.md` link the `Process` cell:
`[Process name](processes/<slug>.md)`. The checker reads the closed columns
by header and ignores the rest, so a link in the `Process` cell is safe.
Revisit `Runs` and `Call` with the thing in front of you, and change them only
if reality changed. Bare values, always. One line in `CHANGELOG.md`.

Say this out loud: **the manual count moves when the process stops being
manual, not when it is written down.** A written procedure is the
precondition, and the register is honest about the difference.

```bash
python3 scripts/systems-register.py --check
python3 scripts/systems-register.py --baseline
```

The baseline reads the same as before unless `Runs` changed. If it moved and
the process did not stop being manual, the row is wrong. Commit by path, then
say what the next `/oac` will do.

## Where the engine is installed

In a repo with OpsCode's build tools installed and the doctor clean, `/oac`
runs this same method as the `opscode-oac-process-capture` stage, with a
reviewer and a gate. They write the same file.

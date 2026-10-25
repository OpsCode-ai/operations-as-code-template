---
title: "/oac: Operations as Code, the one door"
type: guide
audience: internal
summary: "The one command for Operations as Code in a business repo. It looks at where the repo is, then runs the next stage: the install order and the register (what the business runs on), the Context Core (what it is aiming at, drafted from evidence), or process capture (one manual process, written down by watching it). The plain way, each file shown first and written on the operator's yes; on the engine where one is installed. It starts from what Self as Code shared, never from blank. Typed again, it does the next stage."
topics: [operations, onboarding]
tags: [oac, command, door, adr-125]
---

# /oac: Operations as Code, the one door

Type `/oac`. That is the whole instruction for the operator.

## Where you are, then the next stage

Look before you ask anything:

```bash
grep '^plane:' .oac/manifest.yml
python3 scripts/systems-register.py --baseline
ls context-core/strategic-identity/from-self-as-code.md 2>/dev/null
```

| What you find | What runs |
|---|---|
| `plane: self` | Stop. This is someone's own repo; the door there is `/sac`, and it runs first |
| No register | The install order, then the register: the `ops-audit` command (steps 0 to 5, then the three tables) |
| A register, and `context-core/` still seeded (any file at `status: seeded`, or a folder README that says it is empty) | The `context-core` command: the business's direction, drafted from evidence |
| A register with a `manual` or `semi` row whose `Process` cell links to no file under `systems/processes/` | The `process-capture` command: one process, watched and written |
| None of those | Say where things stand: the manual count, what is drafted, what is left for the operator. Offer `process-capture` for the next row |

Run exactly one stage per `/oac`, then stop and say what the next `/oac` will
do. Any arguments pass straight through to the stage that runs. The operator
never chooses a path.

## Start from Self as Code, never from blank

When `context-core/strategic-identity/from-self-as-code.md` exists, every
stage reads it first. It holds the lines the owner chose to share from their
own Self as Code: the kind of business, how long it has run and how many
people, what it runs on, what to build first, the six-month target. Those
lines shape the repo:

- the kind of business (a trade, a service, a product, property) sets which
  Context Core folders matter first and which questions are worth asking;
- 'runs on' seeds the Software table, as rows to confirm, not to type again;
- 'how many people' seeds `systems/team.md`;
- 'what to build first' is the first process to capture, and the first thing
  this business's AI does for them;
- the six-month target is the top of `strategic-identity/`.

Never ask again what it already says. When it is missing, carry on; nothing
depends on it. A business repo never reads anyone's private repo. It reads
only what their sharing step put here.

## How to speak

Plain words. Never say plane, engine, stage, scope, routing or beat to the
operator. Say 'your business repo', 'your own repo', 'the next part'. Every
file a stage writes is shown first and written on their yes, and it names
where every line came from or marks the gap (rule 7). The register stays what
you can go and look at; if two people could disagree about a line, it belongs
in the Context Core.

## Where the engine is installed

In a repo with OpsCode's build tools installed and `/aidlc --doctor` clean
(the hub, or a business that chose to build software), the same three stages
run on the engine through the `opscode-oac-operations` skill, with a reviewer
and a gate each. The operator still types `/oac` and never chooses. Check:

```bash
test -f .claude/tools/aidlc-utility.ts && command -v bun >/dev/null && bun .claude/tools/aidlc-utility.ts doctor 2>&1 | tail -1
```

`0 failed` means invoke that skill and stop reading this file. Anything else
means the plain way above. Packs ship with no engine, so in a pack it is
always the plain way.

**Run this in a business repo only**, a shared repo named `business-ops`. The
bottom line of the screen says `OAC` when you are in one. In your own repo the
door is `/sac`, and it runs first.

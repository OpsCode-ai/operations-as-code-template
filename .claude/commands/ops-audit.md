---
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
description: The Operations as Code install for one business, in the fixed order ADR-122 set - validate from Self as Code, software, team, the chaos exercise, connectors, GitHub. Writes systems/register.md.
---

# /ops-audit - what does this business run on

One job: turn 'we should automate more' into a number that moves, by writing
down the systems, the places work lives, and the processes, with three closed
columns a grep can count.

This pack runs with no engine: the install order as a conversation, then
the register, team and chaos files, the Context Core and process capture,
the plain way, each shown to the operator and written on their yes.

## Which path runs the audit: decided for you

The install order below (steps 0 to 5) always runs here, as a conversation,
because it has to happen before the engine can be configured. The audit
itself, the three tables, can run two ways, and you pick by looking, at the
point where the tables would begin and again as soon as the engine has been
installed:

```bash
test -f .claude/tools/aidlc-utility.ts && command -v bun >/dev/null && bun .claude/tools/aidlc-utility.ts doctor 2>&1 | tail -1
```

- **The engine is installed and the doctor reports `0 failed`**: invoke the
  `opscode-oac-operations` skill and stop reading this file. That runs the
  ops-audit stage with a reviewer, a gate and the register sensor, then the
  Context Core stage, then process capture. It writes the same
  `systems/register.md` as below, and more.
- **Anything else**: carry on with this file and write the tables the plain
  way. The next `/oac` then runs the `context-core` command, and the one
  after it `process-capture`, the plain way too. Say in one line which path
  you took and why, in plain words: no 'engine' to the operator.

The operator types `/oac` and never chooses. If they ask, the answer is: 'the
engine when it is there, the plain method when it is not'.

## Why this comes first

AI-DLC ships `CLAUDE_CODE_USE_BEDROCK=1`, an AWS region and four Bedrock model
pins in its default settings. Correct for an AWS shop, and silently wrong for a
business on Cloudflare or straight Anthropic: it re-routes model traffic to a
provider they may have no credentials for, and it fails at runtime rather than
at install.

OpsCode only knew to strip all six because we know our own systems. **Nobody can
configure this harness correctly without first writing down what the business
runs on.** That is the whole argument for the systems register, and it is why
the install and the audit are one conversation (ADR-118, ADR-120).

## Before you ask anything

```bash
python3 scripts/systems-register.py --baseline
```

Three outcomes:

- **A register exists and is clean.** Report the baseline and ask what has
  changed. Do not start again. Extend.
- **A register exists with problems.** Fix those first, and say what was wrong.
  The commonest is a bolded enum cell, which reads as zero to every consumer.
- **No register.** This is a first audit. Continue below.

Then check the plane, and read what Self as Code shared:

```bash
grep '^plane:' .oac/manifest.yml
cat context-core/strategic-identity/from-self-as-code.md 2>/dev/null
```

**`plane: self` means stop.** A systems register is a property of an operation
and a self plane is not one. Say so, and point at the business plane instead.
The self plane's own manifest already says this in a comment; do not argue with
it.

## The install order (ADR-122)

Fixed on a whiteboard three days before the first Build Day, and it is the
order because of who sits in the room: two people from one business, side by
side, one of whom must not see the other's financials. Self as Code has already
run, per person. This is the business half, and it runs at one laptop per
business.

| Step | What | Shape |
|---|---|---|
| 0 | **Validate from Self as Code.** Which venture is this, what is the website, confirm. When `context-core/strategic-identity/from-self-as-code.md` exists, read it first and start from it, never from blank: the kind of business, how long it has run and how many people, what it runs on, what to build first, the six-month target. Confirm the venture from it. Its 'runs on' line becomes the first Software rows (step 1, to confirm), its people line the first team rows (step 2), and its 'build first' line the first process to capture; note it for the Processes table. Never ask again what it already says. If two people share this business, this is where the second one moves to the first one's laptop | question |
| 1 | **Software.** What runs the business. This is the `## Software` table below. List, do not install or connect | question |
| 2 | **Team.** How many, who, who is responsible for what. Then the future: what roles the business needs next. That question is where AI staff and graduates enter | question |
| 3 | **Chaos.** Every place the business's files live: downloads, desktop, a Drive, SharePoint, someone else's laptop. Then **create copies** into the one operational folder. Never move an original; moving breaks what other tools point at. Teach copying a file path here, because they will do it again at home. With two laptops, each person runs `python3 scripts/oac-hub.py inbox <path>...` on their own laptop: it copies into `inbox/<their handle>/` with dates kept, writes the row in `systems/chaos.md`, and puts the work on their own branch so nothing collides | exercise |
| 4 | **Connectors.** Which of the listed software gets wired in now. Gmail, Google Calendar and Drive connect through claude.ai's own connectors and show up in Claude Code after a restart; Microsoft 365 reads on the day and writes only after their admin consents. The guided steps are below. One register row per connection | wiring |
| 5 | **GitHub.** The business repo is the hub. On the first laptop, after the day-one commit, `python3 scripts/oac-hub.py create` makes it on GitHub, private, and pushes; then `invite <their GitHub user>` for each other founder. On the second laptop, `python3 scripts/oac-hub.py join <owner>/<repo>` clones it, makes their `team/` folder and their branch. From then on each person works on their own branch and `/done` merges it. Make the hub before the day where you can | wiring |

Steps 0 to 2 are questions and go fast. Step 3 is hands-on and is where the
value is felt. Steps 4 and 5 are wiring. Record which model
provider the business runs on at step 1 anyway; the harness install that comes
later needs that answer and nothing else.

**Team is written beside the register, not into it.** `systems/team.md`, one
row per person: name, role, responsible for, and a `future` section for the
roles that do not exist yet. It is outside the `systems` profile's three
tables, so `systems-register.py` does not check it. That is a candidate for a
profile amendment, not a reason to bend the profile now.

**Chaos is written as a list, then acted on.** `systems/chaos.md`: where each
body of files lives, whether it has been copied in yet, and what still points
at the original. `oac-hub.py inbox` writes those rows for the copies it makes. The take-home prompt goes at the bottom, in their words:
*find the location of files X, create a copy, and put them in Y.*

**One repo per umbrella.** A business with several ventures under one entity
gets one repo named for the entity, a folder per venture, so the operations
manager reaches all of them. Splitting a venture into its own repo is a later,
taught move. The self plane already lists the ventures, so the structure is
known before the repo exists.

## Connecting email and calendar (step 4)

The connectors are Anthropic's own, switched on at claude.ai and inherited by
Claude Code: no key, no `.env`, no script. Guide it; do not do it for them.

1. **Ask which they run on.** The Software table already says: Google
   Workspace (Gmail) or Microsoft 365 (Outlook). Anything else, a Fastmail or
   a cPanel mailbox, is `none` for now; say so.
2. **Google.** Have them open claude.ai in the browser, then Settings, then
   Connectors, and connect Gmail, Google Calendar and Google Drive with the
   business account. Then fully restart Claude Code. Check with `/mcp`: the
   three show up as `claude_ai_Gmail`, `claude_ai_Google_Calendar` and
   `claude_ai_Google_Drive`. Prove it in one minute: list today's calendar,
   and read the latest email thread's subject. Say what it cannot do: download
   an attachment.
3. **Microsoft 365.** The same place, Microsoft 365, with their work account; a
   personal Outlook.com cannot connect. Reads work on the day: mail threads,
   the calendar, SharePoint and OneDrive files. Sending mail and changing the
   calendar need the write tools, which their Microsoft admin consents to, and
   that step is for Team and Enterprise plans. Say 'reads today, writes after
   your admin says yes'. Never more.
4. **Write the rows.** One Software row per connection with `Connects via:
   mcp`, and a 'Where the work lives' row for the inbox and the calendar.
   Outlook gets the note 'read-only until admin consent'.

OpsCode keeps what each connector can and cannot do, with the date it was last
checked, in its connection registry; the coach has it. Promise nothing in a
room that is not written there.

## The three tables, and nothing else

Write only `systems/register.md`. One optional level-two section per table, in
this order. A section you did not capture is simply absent, which the spec calls
out as never an error. Do not invent rows to fill a table.

### `## Software` - one row per tool

```
| System | What it does | Owner | Cost/mo | Connects via | Call |
```

`Connects via` is closed: `api`, `mcp`, `scrape`, `none`. It is the column that
says what an agent can actually reach, so answer it honestly. A tool with a
dashboard and no API is `none`, however modern it looks.

### `## Where the work lives` - one row per place files or records sit

Repos, drives, inboxes, CRMs, spreadsheets that matter. This is the table people
skip and then spend a month rediscovering.

### `## Processes` - one row per repeated thing

```
| Process | Cadence | Runs | Owner | Systems | Call |
```

`Runs` is closed: `manual`, `semi`, `automated`. **This is the measurement the
whole register exists for.** `manual` is the number to watch, and everything an
Automate phase claims shows up here or it did not happen.

`Call` is closed on both tables: `keep`, `automate`, `build`, `replace`,
`retire`. Make the call now, while the thing is in front of you. An audit with
no calls is an inventory.

## How to ask

Cadence, not interrogation. Work one table at a time and reflect back what you
heard before moving on.

- **Start from evidence, not from a blank page.** Read what is already there:
  `context-core/strategic-identity/from-self-as-code.md` first, then
  `reference/api-connection-registry.md` if it exists, `crontab -l`, the repo's
  own scripts, any `.env.example`. Ask about what you found. 'I can see a
  Supabase project and an hourly cron. What else runs on a schedule?' beats
  'list your systems'.
- **One question at a time.** Use AskUserQuestion when the answer is a choice
  from a closed column, and plain conversation otherwise.
- **Take 'I do not know' as an answer.** `?` in a cost cell is a gap against a
  source nobody has connected. It is honest, and the register says so.
- **Do not let them describe the future.** This table is the as-is. If two
  people could disagree about it, it belongs in the Context Core, not here.
  If you can go and look, it belongs here.

## Writing it

Frontmatter per the OaC spec: `title`, `type: reference`, `audience: internal`,
`status`, `lifecycle: living`, `updated`, plus `topics` and `tags` in flow
style.

**Closed cells carry the bare value.** `| manual |`, never `| **manual** |`.
Emphasis defeats the grep the profile rests on, and this is a rule with a
checker now, so it will be caught either way.

Open with a short `## The baseline` block giving the counts, so the document
leads with the number rather than burying it. Then verify:

```bash
python3 scripts/systems-register.py --check
```

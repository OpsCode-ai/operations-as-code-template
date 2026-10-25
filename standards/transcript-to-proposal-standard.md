---
title: "Transcript to proposal standard"
type: standard
version: "1.0"
audience: team
status: active
lifecycle: living
date: 2026-10-08
summary: "A proposal is assembled from the record, not written from memory. Every input is listed in a ledger before a word is written, and every quoted line on the finished document traces back to one of them."
topics: [sales, operations-as-code, provenance]
tags: [oac, standard, proposal, transcripts, source-ledger, grounding]
references: [./grounding-standard.md]
---

# Transcript to proposal standard

**A proposal is assembled from the record, not written from memory.**

Before a word is written, every input is listed in a ledger. Every quoted line
in the finished document traces back to one of those inputs. The ledger lives
beside the proposal and is checked by a machine.

This applies to anything you send a buyer that quotes them back to themselves:
a proposal, a quote, a scope of work, a statement of work, a pitch.

## Why bother

You already record your calls. You already keep notes. The gap is that nobody
can tell, afterwards, which sentence in the proposal came from which call.

That matters for one reason above all others. **A proposal quotes people.**
Everything else you write describes things. A proposal puts sentences inside
quotation marks and attaches a name to them, and then the buyer forwards it to
people you have never met. It is the highest-risk document you produce and
usually the first thing a buyer sees you build.

The failure is quiet. Someone remembers a line roughly, writes it down
confidently, and nothing in any spell check or tone check will ever flag it.

## The five steps

### 1. List the sources before writing

Not while writing. Not after. Your inputs usually sit in four places:

- Recordings and their transcripts, wherever your capture puts them
- Call notes and meeting summaries in the customer's folder
- Email and chat with that customer
- Your own records: what you have agreed, what you charge, who they are

### 2. The record beats the transcript

A transcript is evidence of what somebody said. Your records are the record of
what is true. Where they disagree, your records win, or you settle it before
the document goes out.

Three things a transcript is never the source for:

- **Who somebody is.** Their role, their title, what they have signed
- **A number.** Price, headcount, dates, volumes. A figure said out loud in a
  meeting is a recollection. Find where it is written down
- **Anything about a third party** who was not in the room

What a transcript is the best source for is their own words for their own
problem. Use it for that and you are safe.

### 3. Write the ledger

`{customer folder}/proposal-sources.md`, before the proposal. Two tables.

```markdown
---
title: "Acme proposal: where every claim came from"
type: report
audience: internal
status: active
date: 2026-10-08
summary: "Every input behind the Acme proposal, and the quote each one carries."
topics: [sales, provenance]
tags: [proposal, source-ledger]
---

## Sources

| id | kind | date | where | used for |
|---|---|---|---|---|
| call-first | recording | 2026-09-14 | recordings:2026-09-14-acme-discovery.md | Their own words for the problem |
| notes-acme | record | 2026-10-01 | customers/acme/notes.md | Who is deciding, and the dates |

## Quotes

| quote | source | as said |
|---|---|---|
| We lose a day a week to this. | call-first | we're probably losing a day a week to it |
| You will own it, not rent it. | ours | |
```

- **id** is what the quotes table points at
- **kind** is one of `recording`, `transcript`, `chat`, `email`, `record`, `page`
- **where** is a path in this repo, or `store:ref` for anything outside it. A
  recording that lives outside the repo stays outside it. Point at it; do not
  copy it in
- **used for** says what it gave you. If that is blank, it was not a source
- **ours** in the source column means it is your own line, not a quotation. A
  pull quote is often something you wrote, and saying so is honest
- **as said** is their actual words where you tightened them for the page. A
  quotation is what they said. Tidying it is normal; hiding that you tidied it
  is not

### 4. Write the proposal

Its frontmatter carries, in flow style:

```yaml
generated: true
sources: [proposal-sources.md]
```

### 5. Check it

```bash
python3 scripts/check-proposal-sources.py customers/acme/proposal.md
```

It refuses four things: a quote in the document that is in no ledger entry, a
quote attributed to a source in this repo that does not contain it, a ledger
row pointing at a file that is not there, and a row with no 'used for'.

What it cannot do is check a quote against a recording that lives outside the
repo, which is most of them. That is the hole. The `as said` column is the
record a person can check by hand.

## A note on quotation marks

The checker treats every blockquote, and every quoted span of six or more
words, as a quotation that needs a source. A shorter quoted phrase is usually
a term of art, so it is left alone. Change the line with `--quote-words` if
your writing runs differently.

## Related

- [grounding-standard.md](grounding-standard.md), the general rule this applies
  to one document
- `scripts/check-proposal-sources.py`

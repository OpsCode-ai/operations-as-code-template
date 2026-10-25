---
title: "/install: First-run pass over this repo"
type: guide
audience: internal
---

# /install: First-run pass over this repo

Run this the first time this repo is opened, and again any time you want the
fill-map refreshed. It changes nothing; it reports.

## The run

1. **Read the shape.** `CLAUDE.md` first, then `README.md`, then
   `context-core/README.md`, then every folder README under `context-core/`.
2. **Check the format.** Run `python3 scripts/oac-validate.py .` and report the
   conformance level and the top three things it flags. Do not fix them yet.
3. **Build the fill-map.** Walk every file in `context-core/`, `systems/` and
   `decisions/`. Read the frontmatter `status`. Produce one table: file,
   status (`seeded` / `confirmed` / missing), one line on what would fill it.
4. **Classify every gap by its best source**, so the operator sees the split
   between what an agent can fetch and what only they know:
   - **head-only**: written nowhere. It is in the founder's head. Most of the
     valuable gaps are this kind, which is the point.
   - **existing-docs**: a document, quote, contract or email already answers it.
   - **system**: a tool the business runs holds it and it can be pulled.
   - **web**: the business's own website or a supplier's answers it.
5. **Rank the head-only gaps** by how much the business is blocked without
   them. Top three get attention; the rest get a table row.
6. **State the standing rule, out loud:** every file in this repo is meant to
   be altered. When the operator says something new about the method, a cost,
   a supplier or a customer, it gets written down here, not remembered.
7. **Offer the first move.** Report the split, then say plainly: the next step
   is `/oac`, which writes what the business runs on today.

## Rules

- Never mark a file `confirmed` yourself. The operator confirms; you record.
- The fill-map is a report, not a to-do avalanche.
- **Never invent a business fact.** If it is head-only, mark it and ask.

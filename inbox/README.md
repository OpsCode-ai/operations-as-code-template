---
title: "Inbox"
type: index
audience: internal
---

# Inbox

One folder per person, for the files that came off each laptop in the chaos
exercise: `inbox/<handle>/`. Copies, never originals.
`python3 scripts/oac-hub.py inbox <path>...` puts them here with their dates
kept and writes a row in `systems/chaos.md` saying where each one came from.

Sort from here into `context-core/` and `systems/` as you go. A file that has
been sorted is deleted from the inbox, never from where it came. Two people
never write in the same inbox folder, so nothing collides.

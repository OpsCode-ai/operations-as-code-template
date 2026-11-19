---
title: "/spoke: A new department, a person or an AI role"
type: guide
audience: internal
---

# /spoke: A new department, a person or an AI role

One job: turn 'we need a marketing department' into a part of this business
with the right people in it, and nothing it should not see.

A spoke is a circle around this business's brain. It comes in three kinds:

- **A department:** the people who do one part of the work.
- **A person:** one person's own spoke, seen only by them and the owners. A
  CFO, say.
- **An AI role:** an AI that does one job, an AI marketer say, with named
  people who check its work before anything goes out.

The owners are in every spoke. The brain itself stays with the owners.

## When to offer it

When someone here talks about a new department or team, someone joining, or
an AI doing a job ('we need a marketing department', 'Jo starts in accounts
on Monday', 'can an AI do our social posts?'), offer this in one line: what it
would make, and 'want me to set it up?'

## Who decides

Spokes are made in the brain, and only the owners and the admins they choose
are in the brain. So only they make spokes. Nobody else has to approve it, and
no pull request is needed: what protects the business is what never leaves
the brain.

## In a spoke: ask for one

If `.oac/manifest.yml` says `spoke:`, this is a spoke, and spokes are made in
the brain. Don't make one. Write the request instead, so the owners see it:

1. Ask what they need and why, in a sentence or two, and who would be in it.
2. Write it to `team/<their first name>/requests/<YYYY-MM-DD>-<short name>.md`,
   with frontmatter (`title`, `type: note`, `audience: team`).
3. Say: 'Saved. Type /done. The owners see it the next time they open the
   brain.'

## Picking up

If `specs/spokes/<name>.yml` already exists for the one they mean, read it
and go to the step it has reached: no `github:` yet means it has not been
made, so check it and make it.

## The questions

One at a time. Short answers are fine.

1. Its name, short, like `marketing`.
2. A department, one person, or an AI role?
3. In one line: what it does, or the person's job title. For an AI role, the
   job it does, like 'writes the monthly newsletter and the social posts'.
4. Who is in it, with their GitHub usernames. For an AI role: who checks its
   work.
5. Which folders of the brain it needs. Show them first:
   `python3 scripts/oac-spoke.py plan` lists the brain's folders. Suggest only
   what the job needs. Anything not named stays with the owners. Money, pay
   and the vision folder are never suggested; the owners name them if they
   want to.

## Then

1. **Write the plan.**
   `python3 scripts/oac-spoke.py plan <name> --kind <department|person|ai> --description "<what it does>" --people "Full Name:github-user" ... --paths <folder>/ ...`
   It also starts the spoke's goals file. On Windows, `python`, not `python3`.
2. **Save it.** Say: 'Type /done to save the plan to the brain, then /spoke
   again, and I'll make it.' The spoke is built from what is saved, never from
   what is not.
3. **Show what it would see.** `python3 scripts/oac-spoke.py check <name>`.
   Say, in plain words, what crosses, what is kept back and why. Wait for a
   yes.
4. **Make it and invite its people.** `python3 scripts/oac-spoke.py create <name>`,
   then `python3 scripts/oac-spoke.py invite <name>`. Say who got an invite:
   its people, and the owners.
5. **Tell them how to join.** Each person says yes to GitHub's email, then
   joins from their own private space with the join line the tool printed.

For an AI role, add: its instructions are in `.claude/agents/<name>.md` in the
spoke. The people who check its work open the spoke and ask for work, like
'Use the marketing agent to draft this month's newsletter.' It drafts. They
decide.

## Adding or moving someone

'Add Jo to marketing': plan it again with the whole list of people, `/done`,
then `python3 scripts/oac-spoke.py invite <name> <their GitHub username>`.

## Never

- Never put anyone in the brain itself. Owners only.
- Never make a spoke without the owners' yes after the check.
- Never let an AI role send, post or publish on its own.

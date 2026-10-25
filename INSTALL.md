---
title: "Install: Operations as Code"
type: guide
audience: internal
---

# Install: Operations as Code

Ten minutes. One repo, for one business, shared with the people who work in it.

You already ran Self as Code in your own private repo. This is the second
package: the business, written down. Where two people share a business, do
this once, at one laptop; the second person joins through GitHub afterwards.
If you ran `/sac deploy` in your private repo, this repo already exists and is
already seeded, so skip to step 4.

## Steps

1. On GitHub, open `https://github.com/OpsCode-ai/operations-as-code-pack` and press **Use this template**,
   then **Create a new repository**. Name it after the business, ending in
   `-ops` (`acme-ops`), and choose **Private**. Or, in a terminal with GitHub's
   tool signed in:
   ```bash
   gh repo create acme-ops --template OpsCode-ai/operations-as-code-pack --private --clone
   ```
2. Get it onto your computer if the line above did not: the green **Code**
   button on your new repository's page, then **Open with GitHub Desktop**, or
   copy the address and `git clone` it into `~`.
3. Open Claude Code in that folder and paste the installer prompt below.
4. When it says it is done, restart Claude Code, run `/install`, then `/oac`.

**Done looks like:** the folder has a git history, its copy on GitHub is
private, the bottom line of Claude Code says `OAC`, typing `oac` in a new
Terminal window opens this folder with Claude Code running, `/install` has
shown you a fill-map, and `/oac` has written `systems/register.md` with a
manual-process count you can say out loud.

---

## The installer prompt (paste everything below into Claude Code, running in the folder)

Hi Claude. OpsCode's Operations as Code template made this repo on GitHub for
my business, and it is sitting in this folder. Do these steps in order and tell
me what you did after each one.

1. **Verify the layout.** Confirm this folder contains `CLAUDE.md`,
   `README.md`, `CHANGELOG.md`, `INSTALL.md`, `STATUSLINE.md`, `MODES.md`,
   `.oac/`, `.claude/commands/`, `.githooks/`, `scripts/`, `specs/`,
   `decisions/`, `systems/`, `team/` and `context-core/`. If anything is
   missing, stop and tell me.
2. **Check the copy is private.** Run `gh repo view --json visibility -q
   .visibility`. Only `PRIVATE` lets you go on; otherwise tell me how to fix
   it (`gh repo edit --visibility private`). If `gh` is not signed in, tell me
   to sign in from a new, plain terminal window and wait.
3. **Name the business, and me.** Ask me the business name, then put it into
   the `title` of `README.md` and `CLAUDE.md` where they say 'this business'.
   Ask me my first name and create `team/<firstname>/` with an empty `logs/`
   folder inside it (put a `.gitkeep` in `logs/`). Ask me the name of my own
   private repo (it ends in `-ops`) and put it in `.oac/manifest.yml` as
   `parent_operation`. If I do not have one yet, leave the placeholder and
   tell me.
4. **Turn the hook on and save day one.** Run
   `git config core.hooksPath .githooks`, then commit everything as
   `Operations as Code: day one` and push. If the hook warns that gitleaks is
   not installed, tell me the install command for my platform and carry on.
5. **Install the bottom line.** `python3 scripts/install-oac-statusline.py`
   and report what it did.
6. **Install the one word.** `bash scripts/install-shortcuts.sh` and tell me
   what it printed. From then on, a new Terminal window and the word `oac`
   opens this folder with Claude Code running.
7. **Run the validator.** `python3 scripts/oac-validate.py .` Report the
   conformance level and the top three things it flags. Do not fix them yet.
8. **Read `CLAUDE.md`** and give me a three-line summary of what this repo is
   for and what its two halves are.
9. **Tell me you are done**, and what happens next, in order: Claude Code may
   ask me to approve this project's settings, and I should approve them; then
   I fully restart Claude Code; then I run `/install`, then `/oac`. To invite
   the other person in my business, `python3 scripts/oac-hub.py invite <their
   GitHub user>`; they join with `python3 scripts/oac-hub.py join <owner>/<repo>`.
   To get back here any day, I open a new Terminal window and type `oac`.
   Every session after that starts with `/start` and ends with `/done`.

Do not edit any other file contents during this install. Install only.

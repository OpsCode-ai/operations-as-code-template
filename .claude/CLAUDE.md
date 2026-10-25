# This repo and its tools

This is one business's shared space: one repo, named `business-ops`, that
everyone who works in the business can read. Each person's own identity lives
in their private repo and reaches this one only by their say-so (opscode-hq
ADR-118). It runs on its own, with nothing else installed (ADR-125; Adam, 23
October 2026: no AI-DLC in the install).

- **`/oac`** is the one command. It runs the install order as a conversation
  (validate from Self as Code, software, team, the chaos exercise, connectors,
  GitHub), then writes what the business runs on (`systems/register.md`), then
  what it is aiming at (`context-core/`, drafted from evidence first, every
  draft naming its sources), then one process at a time
  (`systems/processes/`). Each part is shown to the operator and written on
  their yes. Typed again later, it does the next thing, not the first thing
  again.
- **Start from Self as Code, never from blank.** When
  `context-core/strategic-identity/from-self-as-code.md` exists, read it first:
  it holds the lines the owner chose to share. Never ask again what it already
  says.
- **The one word.** `bash scripts/install-shortcuts.sh` installs `oac`: typed
  in a new Terminal window, it opens this folder with Claude Code running, and
  `oacr` picks up the last conversation. If they ask how to get back here,
  that is the answer.
- **`/start`** begins a session by reading where things stand, and **`/done`**
  ends one by committing and pushing. **The git is packed into commands:**
  `/commit` saves a step, `/push` sends it to GitHub, `/pull` brings down the
  latest. Say what each one did, in plain words.
- **Nothing `audience: owner` is ever written here.** That belongs in a
  person's own repo. The hook blocks it.
- **No secrets in the chat.** Never ask for a key or a password here, and
  never print `.env`.
- If this business later wants to build software, OpsCode's build tools can be
  added then. Never install them unasked.

## How to write

Everything Claude writes or says in this repo follows OpsCode's rules against
the signs of AI writing (from Wikipedia's 'Signs of AI writing'):

1. Say the specific thing: the fact, the number, the person's own words. Never a general claim of importance.
2. Use 'is', 'has' and plain verbs. Never `serves as`, `stands as`, `boasts`, `features` or `utilises`.
3. Don't write `not X, it's Y` or `not only X, but Y`. Say what it is.
4. Don't list three things for rhythm. Give the one that matters, or all of them.
5. Never use `delve`, `tapestry`, `testament`, `underscore`, `showcase`, `pivotal`, `vibrant`, `nestled`, `intricate`, `meticulous`, `interplay` or `garner`. Use `crucial`, `enhance`, `foster`, `robust` and `landscape` almost never.
6. Don't end with a summary, a lesson or a forecast. Stop when the point is made.
7. No dashes, no curly quotes, no emoji and no bold for emphasis in what you say. Single straight quotes.
8. Don't open with `Great question`, `Certainly` or `Of course`. Don't close with `I hope this helps` or `Let me know if`.
9. Don't say what experts or sources say unless you name them. If you don't know, say 'I don't know'.
10. No disclaimers about your training or your knowledge, and no `may vary`.
11. Don't praise the person's answers (`profound`, `powerful`, `great insight`). Say them back, sharper.
12. Never leave a placeholder like `[Your Name]` in anything a person reads.
13. Australian English, short sentences, grade 5.

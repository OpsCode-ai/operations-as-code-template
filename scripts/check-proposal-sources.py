#!/usr/bin/env python3
"""check-proposal-sources.py - does this proposal say where every claim on it
came from, and does the source actually say that.

A proposal is assembled from the record, not written from memory. This reads
the proposal, reads its source ledger, and refuses the four ways that goes
wrong:

  1. A quote on the page that is in no ledger entry. Somebody wrote it from
     memory, or lifted it from a source nobody wrote down.

  2. A quote attributed to a source that is IN THE REPO AND DOES NOT CONTAIN
     IT. That is a paraphrase presented as a quotation, which is the most
     expensive kind of error on a page a buyer forwards.

  3. A ledger row pointing at a repo path that does not exist.

  4. A ledger row with no 'used for'. Nobody can tell whether it was read or
     just listed, so it is not a source.

What counts as a quote: every blockquote, and every quoted span of six or more
words. A short quoted phrase is usually a term of art, not a quotation, and
checking those turns the whole thing into noise. Raise or lower it with
--quote-words.

A source outside the repo (a recording in the voice inbox, an email) is written
`store:ref` and is never verified, by design. It is outside the repo on
purpose. That is a real hole and the standard says so: read the transcript.

Usage
    python3 code/scripts/check-proposal-sources.py engagements/aws/proposal.md
    python3 code/scripts/check-proposal-sources.py <page> --ledger <ledger.md>
    python3 code/scripts/check-proposal-sources.py --engagement aws

Exit codes
    0  nothing found, or findings are warnings only
    1  at least one error

Decision: ADR-131. Standard: brand/standards/transcript-to-proposal-standard.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("check-proposal-sources: needs pyyaml (pip install pyyaml)\n")
    sys.exit(0)  # fail open, same as every other OaC rail


def _find_repo() -> Path:
    """Walk up for the repo root. In HQ this sits at code/scripts/; in a
    customer pack it sits at scripts/. A marker beats counting parents, which
    is wrong in one of the two layouts whichever number you pick."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / ".oac").is_dir() or (candidate / ".git").exists():
            return candidate
    return here.parents[2] if len(here.parents) > 2 else here.parent


REPO = _find_repo()
LEDGER_NAME = "proposal-sources.md"
FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
# A built page has no frontmatter, so it names its ledger the way a page can.
META_SOURCES_RE = re.compile(
    r'<meta\s+name=["\']oac-sources["\']\s+content=["\']([^"\']+)["\']', re.I
)

SOURCE_COLUMNS = ["id", "kind", "date", "where", "used for"]
QUOTE_COLUMNS = ["quote", "source"]
OPTIONAL_QUOTE_COLUMNS = ["as said"]
KINDS = {"recording", "transcript", "chat", "email", "record", "page"}

# A pull quote is not always a quotation. Our own line, written for the page
# and set in a blockquote because it is the sentence we want remembered, is
# marked `ours`. It needs no source, and the run prints how many there are,
# because a page that is mostly our own voice is worth seeing.
OURS = "ours"

# A quoted span. Curly pairs, straight doubles, and single quotes where the
# apostrophe inside a word (I've, Courtney's) must not close the span. Lifted
# from check-grounding.py, where it is already proven against this repo.
QUOTED_RE = re.compile(
    "\u201c[^\u201d]{0,600}\u201d"
    '|"[^"]{0,600}"'
    r"|(?<![A-Za-z])'(?:[^']|'(?=[A-Za-z])){0,600}'(?![A-Za-z])"
)
MD_BLOCKQUOTE_RE = re.compile(r"^[ \t]*>[ \t]?(.*)$", re.M)
HTML_BLOCKQUOTE_RE = re.compile(r"<blockquote\b[^>]*>(.*?)</blockquote>", re.S | re.I)
HTML_SAID_RE = re.compile(r'<[a-z]+[^>]*class="[^"]*\bsaid\b[^"]*"[^>]*>(.*?)</[a-z]+>', re.S | re.I)
HTML_CITE_RE = re.compile(r"<cite\b[^>]*>.*?</cite>", re.S | re.I)
HTML_P_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.S | re.I)
TAG_RE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
ANYTAG_RE = re.compile(r"<[^>]+>")
SRT_TIME_RE = re.compile(r"^\s*(\d+\s*$|\d\d:\d\d:\d\d[,.]\d+\s*-->)", re.M)
WORD_RE = re.compile(r"[a-z0-9]+")


class Finding:
    def __init__(self, path, line, level, rule, message):
        self.path, self.line, self.level = path, line, level
        self.rule, self.message = rule, message

    def __str__(self):
        return f"{self.path}:{self.line}: [{self.level}] {self.rule}: {self.message}"


def rel(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def normalise(text: str) -> str:
    """Words only, lowercase, single spaces. Enough to survive a line break in
    an srt, a smart quote, and a comma somebody tidied up on the way to the
    page; not enough to let an invented sentence through."""
    return " ".join(WORD_RE.findall(text.lower()))


def frontmatter(raw: str) -> dict:
    m = FM_RE.match(raw)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def declared_sources(raw: str) -> list[str]:
    """Where this artefact says its ledger is: frontmatter for a document, a
    meta tag for a built page."""
    out = []
    meta = frontmatter(raw)
    for key in ("sources", "derived_from"):
        value = meta.get(key)
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, list):
            out += [str(v) for v in value]
    out += META_SOURCES_RE.findall(raw)
    return out


def visible_text(raw: str, is_html: bool) -> str:
    if not is_html:
        return raw
    body = TAG_RE.sub(" ", raw)
    return ANYTAG_RE.sub(" ", body)


def line_of(raw: str, needle: str, default: int = 1) -> int:
    i = raw.find(needle)
    return raw.count("\n", 0, i) + 1 if i >= 0 else default


# ---------------------------------------------------------------- the ledger

def parse_table(body: str, heading: str, columns: list[str], optional: list[str] | None = None):
    """Pull one pipe table out of the section under `heading`.

    Returns (rows, error). A row is a dict keyed by the declared columns. The
    header row has to carry every column the format requires, so a ledger with
    a missing column fails here rather than silently dropping a field.
    """
    m = re.search(
        rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S
    )
    if not m:
        return [], f"no '## {heading}' section"

    lines = [ln.strip() for ln in m.group(1).splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return [], f"'## {heading}' carries no table"

    def cells(ln):
        # backticks round a path are formatting, and they also keep the
        # ai-writing checker off a filename, so strip them rather than make
        # people choose between two checkers
        return [c.strip().strip("`").strip() for c in ln.strip().strip("|").split("|")]

    header = [c.lower() for c in cells(lines[0])]
    missing = [c for c in columns if c not in header]
    if missing:
        return [], f"'## {heading}' table is missing column(s): {', '.join(missing)}"

    wanted = list(columns) + [c for c in (optional or []) if c in header]
    rows = []
    for ln in lines[2:]:  # row 1 is the header, row 2 the ---|--- separator
        c = cells(ln)
        if len(c) < len(header):
            c += [""] * (len(header) - len(c))
        row = {name: c[header.index(name)] for name in wanted}
        for name in (optional or []):
            row.setdefault(name, "")
        rows.append(row)
    return rows, None


def find_ledger(proposal: Path, declared) -> Path | None:
    """The ledger named in frontmatter, else the one beside the proposal, else
    the one in the engagement folder the proposal sits under."""
    for value in declared:
        candidate = Path(str(value))
        for base in (proposal.parent, REPO):
            p = (base / candidate).resolve()
            if p.name == LEDGER_NAME and p.exists():
                return p
    beside = proposal.parent / LEDGER_NAME
    if beside.exists():
        return beside
    for parent in proposal.resolve().parents:
        p = parent / LEDGER_NAME
        if p.exists():
            return p
        if parent == REPO:
            break
    return None


def read_source_text(where: str) -> tuple[str | None, str | None]:
    """Return (normalised text, error) for a ledger 'where' that is a repo path.

    An out-of-repo `store:ref` returns (None, None): nothing to read and
    nothing wrong with that."""
    if ":" in where and not where.startswith(("./", "../", "/")):
        head = where.split(":", 1)[0]
        if "/" not in head:  # store:ref, e.g. voice-inbox:hidock/...
            return None, None
    p = (REPO / where).resolve()
    if not p.exists():
        return None, f"path does not exist: {where}"
    if p.is_dir():
        return None, f"path is a directory, name the file: {where}"
    raw = p.read_text(errors="replace")
    raw = SRT_TIME_RE.sub(" ", raw)
    if p.suffix.lower() in {".html", ".htm"}:
        raw = visible_text(raw, True)
    return normalise(raw), None


# ---------------------------------------------------------------- the quotes

def quotes_on_page(raw: str, is_html: bool, min_words: int) -> list[str]:
    """Every blockquote, plus every quoted span long enough to be a quotation
    rather than a term of art. Returned as written, de-duplicated, in order."""
    found: list[str] = []

    def spoken(inner: str) -> list[str]:
        """The quotation inside a blockquote, without its attribution.

        A <cite> is who said it, not what they said, and a blockquote that
        wraps its words in <p> means the quotation is the paragraphs. Taking
        the whole element instead gives you the quote with the caption glued
        on the end, which then matches nothing in the ledger."""
        inner = HTML_CITE_RE.sub(" ", inner)
        paras = HTML_P_RE.findall(inner)
        parts = paras or [inner]
        return [ANYTAG_RE.sub(" ", p) for p in parts]

    if is_html:
        for m in HTML_BLOCKQUOTE_RE.finditer(raw):
            found += spoken(m.group(1))
        for m in HTML_SAID_RE.finditer(raw):
            found += spoken(m.group(1))
        prose = visible_text(raw, True)
    else:
        for m in MD_BLOCKQUOTE_RE.finditer(raw):
            if m.group(1).strip():
                found.append(m.group(1))
        prose = FM_RE.sub("", raw)

    for m in QUOTED_RE.finditer(prose):
        span = m.group(0)[1:-1].strip()
        if len(WORD_RE.findall(span.lower())) >= min_words:
            found.append(span)

    seen, out = set(), []
    for q in found:
        key = normalise(q)
        if key and key not in seen:
            seen.add(key)
            out.append(" ".join(q.split()))
    return out


# ---------------------------------------------------------------- the checks

def check(proposal: Path, ledger_path: Path | None, min_words: int) -> list[Finding]:
    findings: list[Finding] = []
    raw = proposal.read_text(errors="replace")
    is_html = proposal.suffix.lower() in {".html", ".htm"}
    meta = frontmatter(raw)
    pr = rel(proposal)

    declared = declared_sources(raw)

    # The gated build has its content encrypted, so every quote in the ledger
    # looks stale and nothing on the page looks unsourced. Say so instead of
    # printing ten misleading warnings.
    if is_html and "__bootBoard" in raw:
        return [Finding(
            pr, 1, "note", "gated",
            "this is the gated build and its content is encrypted, so there is "
            "nothing here to check. Run it against the page source instead",
        )]

    if is_html and not declared:
        findings.append(Finding(
            pr, 1, "warn", "declaration",
            'a built page names its ledger with '
            '<meta name="oac-sources" content="...">, so the artefact itself '
            "says where to look",
        ))

    if not is_html:
        gen = meta.get("generated")
        if gen is not True and str(gen).strip().lower() != "true":
            findings.append(Finding(
                pr, 1, "error", "declaration",
                "a proposal declares `generated: true`. It is assembled from "
                "the record by this system, and saying so is what makes "
                "`sources:` required (OaC 1.12 s3.10)",
            ))
        if not declared:
            findings.append(Finding(
                pr, 1, "error", "declaration",
                "no `sources:` and no `derived_from:`. Name the ledger",
            ))

    if ledger_path is None:
        findings.append(Finding(
            pr, 1, "error", "ledger",
            f"no {LEDGER_NAME} found beside the proposal or in its engagement "
            "folder. The ledger is written before the proposal, not after",
        ))
        return findings

    lr = rel(ledger_path)
    body = ledger_path.read_text(errors="replace")
    sources, err = parse_table(body, "Sources", SOURCE_COLUMNS)
    if err:
        findings.append(Finding(lr, 1, "error", "ledger", err))
    quote_rows, qerr = parse_table(body, "Quotes", QUOTE_COLUMNS, OPTIONAL_QUOTE_COLUMNS)

    by_id: dict[str, dict] = {}
    for row in sources:
        sid = row["id"]
        ln = line_of(body, f"| {sid} ", 1)
        if not sid:
            findings.append(Finding(lr, ln, "error", "ledger", "a source row with no id"))
            continue
        if sid in by_id:
            findings.append(Finding(lr, ln, "error", "ledger", f"duplicate source id: {sid}"))
            continue
        by_id[sid] = row

        if not row["used for"].strip():
            findings.append(Finding(
                lr, ln, "error", "ledger",
                f"source '{sid}' has no 'used for'. Nobody can tell whether it "
                "was read or just listed, so it is not a source",
            ))
        kind = row["kind"].strip().lower()
        if kind and kind not in KINDS:
            findings.append(Finding(
                lr, ln, "warn", "ledger",
                f"source '{sid}' has kind '{kind}', which is not one of "
                f"{', '.join(sorted(KINDS))}",
            ))
        where = row["where"].strip()
        if not where:
            findings.append(Finding(lr, ln, "error", "ledger", f"source '{sid}' has no 'where'"))
            continue
        text, werr = read_source_text(where)
        if werr:
            findings.append(Finding(lr, ln, "error", "ledger", f"source '{sid}': {werr}"))
        row["_text"] = text

        if ":" in where and "/" not in where.split(":", 1)[0]:
            ref = where.split(":", 1)[1]
            if (REPO / ref).exists():
                findings.append(Finding(
                    lr, ln, "error", "ledger",
                    f"source '{sid}' is written as an outside store but '{ref}' "
                    "is a path in this repo. Point at the path, or the ledger "
                    "hides that the material was copied in",
                ))

    page_quotes = quotes_on_page(raw, is_html, min_words)
    if page_quotes and qerr:
        findings.append(Finding(lr, 1, "error", "ledger", qerr))
        return findings

    ledger_quotes = {}
    ours = 0
    for row in quote_rows:
        q = row["quote"].strip().strip("\u201c\u201d\"'")
        sid = row["source"].strip()
        said = row.get("as said", "").strip().strip("\u201c\u201d\"'")
        ln = line_of(body, row["quote"][:40], 1) if row["quote"] else 1
        if not q:
            continue
        ledger_quotes[normalise(q)] = (q, sid, said, ln)
        if sid == OURS:
            ours += 1
            if said:
                findings.append(Finding(
                    lr, ln, "warn", "ledger",
                    f"'{q[:50]}' is marked {OURS} and also carries an 'as said'. "
                    "It is one or the other",
                ))
            continue
        if sid and sid not in by_id:
            findings.append(Finding(
                lr, ln, "error", "ledger",
                f"quote points at source '{sid}', which is not in the sources table",
            ))
        if not sid:
            findings.append(Finding(
                lr, ln, "error", "ledger",
                f"quote with no source: {q[:60]}. If it is our own line, say {OURS}",
            ))

    for q in page_quotes:
        key = normalise(q)
        if key not in ledger_quotes:
            findings.append(Finding(
                pr, line_of(raw, q[:40]), "error", "unsourced-quote",
                f"quoted on the page and in no ledger entry: '{q[:80]}'",
            ))
            continue
        _, sid, said, ln = ledger_quotes[key]
        if sid == OURS:
            continue
        row = by_id.get(sid)
        if not row:
            continue
        text = row.get("_text")
        if text is None:
            continue  # outside the repo, nothing to check it against
        # 'as said' is the source's own words where the page tightened them.
        # Check what was said, not what was printed, or every tidied quote
        # fails and the check gets switched off.
        target = normalise(said) if said else key
        if target not in text:
            what = "as said" if said else "quoted"
            findings.append(Finding(
                lr, ln, "error", "misquote",
                f"'{(said or q)[:70]}' is attributed to '{sid}' and "
                f"{row['where']} does not contain it ({what}). That is a "
                "paraphrase presented as a quotation",
            ))

    on_page = {normalise(q) for q in page_quotes}
    for key, (q, sid, said, ln) in ledger_quotes.items():
        if key not in on_page:
            findings.append(Finding(
                lr, ln, "warn", "stale-ledger",
                f"ledger carries a quote the page does not: '{q[:60]}'",
            ))

    if page_quotes:
        findings.append(Finding(
            pr, 1, "note", "count",
            f"{len(page_quotes)} quote(s) on the page, {ours} marked {OURS}",
        ))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("proposal", nargs="?", type=Path, help="the proposal markdown or page")
    ap.add_argument("--ledger", type=Path, help=f"the {LEDGER_NAME} to check it against")
    ap.add_argument("--engagement", help="an engagement slug, to check its proposal")
    ap.add_argument("--quote-words", type=int, default=6,
                    help="a quoted span this long or longer is a quotation (default 6)")
    ap.add_argument("--quiet", action="store_true", help="print findings only")
    args = ap.parse_args()

    proposal = args.proposal
    if proposal is None and args.engagement:
        folder = REPO / "engagements" / args.engagement
        for name in ("proposal.md", f"{args.engagement}-proposal.md"):
            if (folder / name).exists():
                proposal = folder / name
                break
        if proposal is None:
            print(f"check-proposal-sources: no proposal found in {rel(folder)}")
            return 1
    if proposal is None:
        ap.error("name a proposal, or pass --engagement")
    if not proposal.is_file():
        print(f"check-proposal-sources: no such file: {proposal}")
        return 1

    ledger = args.ledger
    if ledger is None:
        ledger = find_ledger(proposal, declared_sources(proposal.read_text(errors="replace")))
    elif not ledger.exists():
        print(f"check-proposal-sources: no such ledger: {ledger}")
        return 1

    findings = check(proposal, ledger, args.quote_words)
    for f in findings:
        print(f)

    errors = sum(1 for f in findings if f.level == "error")
    warnings = sum(1 for f in findings if f.level == "warn")
    if not args.quiet:
        where = rel(ledger) if ledger else "no ledger"
        print(
            f"\ncheck-proposal-sources: {rel(proposal)} against {where}, "
            f"{errors} error(s), {warnings} warning(s)"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

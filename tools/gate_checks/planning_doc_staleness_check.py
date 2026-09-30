#!/usr/bin/env python3
"""Report-only sweep: planning docs whose claimed status ("idea" / "ready, schedule later") is
stale against `tickets/done/` (TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR).

Same shape as `doc_staleness_check.py` / `epic_staleness_check.py`: `find_stale_planning_docs()`
returns a list of `Finding`s, never raises a verdict, never edits a doc, and the CLI always exits 0
(a finding is information for a person or agent to resolve, not a failure).

What it looks at, under `docs/plans/` (the `archive/` subtree is skipped):
- **Structured signal (primary):** frontmatter `status: idea`. The doc's identity text is its file name
  and H1.
- **Text heuristic (secondary):** a heading containing "ready, schedule later" (its own wording in
  `standalone_items.md`). The identity text is that heading. A heading that already says
  SHIPPED / CLOSED / "was:" is treated as resolved and skipped.

What it matches against: `tickets/done/**/TCK-*.md`. A done ticket matches an item when the ticket
id's slug (the part after the date), minus generic words, has >= 3 tokens and at least 75% of them
appear in the item's identity text, and the ticket is dated on or after the doc (a ticket closed before
the doc was written cannot be the work the doc describes). That is a title/keyword match, deliberately conservative and
inherently fuzzy: no structured back-link from a ticket to the planning doc it traces to exists, so
expect false negatives (and the occasional coincidence). A done ticket closed by a `## Disposition`
(STALE-PREMISE, WONT-DO, ...) did not ship anything and is never matched.

A person judges whether the shipped ticket covers the whole idea or only part; this tool only
points. Resolution convention it recommends (see the ticket's Implementation Notes): a fully
shipped idea doc moves to `docs/plans/archive/` with `status: historical`; a shipped item inside a
still-active doc gets an inline dated note on its heading.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from validate_frontmatter import extract_frontmatter  # noqa: E402

_SCHEDULE_LATER = re.compile(r"ready[\s,—\-]*schedule\s+later", re.IGNORECASE)
_RESOLVED_HEADING = re.compile(r"\b(shipped|closed|was:)", re.IGNORECASE)
_STOP = {
    "the", "and", "for", "with", "from", "into", "not", "never", "always", "only", "check",
    "fix", "add", "hotfix", "standard", "epic", "ticket", "tickets", "tck", "tests", "test",
    "doc", "docs", "update", "make", "use", "when", "after", "before", "that", "this", "new",
}


class Finding(NamedTuple):
    doc_path: str
    matched_ticket_id: str
    matched_text: str  # the doc text that matched (heading or title)
    signal: str  # "status: idea" | "ready, schedule later"


def _tokens(text: str) -> set[str]:
    out = set()
    for tok in re.split(r"[^a-z0-9]+", text.lower()):
        if len(tok) < 3 or tok.isdigit() or tok in _STOP:
            continue
        out.add(tok[:-1] if tok.endswith("s") and len(tok) > 3 else tok)
    return out


def _slug_tokens(ticket_id: str) -> set[str]:
    return _tokens(re.sub(r"^TCK-\d{8}-", "", ticket_id))


def _done_ticket_ids(done_dir: Path) -> dict[str, Path]:
    return {p.stem: p for p in sorted(done_dir.rglob("TCK-*.md"))}


def _has_disposition(path: Path) -> bool:
    try:
        return re.search(r"^## Disposition\s*$", path.read_text(encoding="utf-8"), re.MULTILINE) is not None
    except OSError:
        return True  # unreadable: do not claim it shipped


def _id_date(ticket_id: str) -> str:
    m = re.match(r"TCK-(\d{8})-", ticket_id)
    return m.group(1) if m else ""


def _match(identity: str, done: dict[str, Path], doc_date: str = "") -> list[str]:
    ident = _tokens(identity)
    hits = []
    for tid, path in done.items():
        slug = _slug_tokens(tid)
        if len(slug) < 3:
            continue
        if doc_date and _id_date(tid) < doc_date:
            continue
        if len(slug & ident) / len(slug) >= 0.75 and not _has_disposition(path):
            hits.append(tid)
    return hits


def _doc_date(fm: dict) -> str:
    return re.sub(r"\D", "", str(fm.get("date", "")))[:8]


def _candidates(plans_dir: Path):
    """Yield (path, identity_text, matched_text, signal, doc_date) for each planning-doc claim."""
    for path in sorted(plans_dir.rglob("*.md")):
        if "archive" in path.relative_to(plans_dir).parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fm = extract_frontmatter(text) or {}
        headings = re.findall(r"^#{1,3} +(.+)$", text, re.MULTILINE)
        if str(fm.get("status", "")).strip() == "idea":
            h1 = next((h for h in headings), path.stem)
            yield path, " ".join([path.stem, h1]), h1, "status: idea", _doc_date(fm)
        for h in headings:
            if _SCHEDULE_LATER.search(h) and not _RESOLVED_HEADING.search(h):
                yield path, h, h, "ready, schedule later", _doc_date(fm)


def find_stale_planning_docs(
    plans_dir: Path = Path("docs/plans"), done_dir: Path = Path("tickets/done")
) -> list[Finding]:
    """Read-only. Returns findings sorted by doc path then ticket id; never raises for missing
    directories (returns [])."""
    if not plans_dir.is_dir() or not done_dir.is_dir():
        return []
    done = _done_ticket_ids(done_dir)
    findings = []
    for path, identity, matched, signal, doc_date in _candidates(plans_dir):
        for tid in _match(identity, done, doc_date):
            findings.append(Finding(str(path), tid, matched, signal))
    return sorted(findings)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--plans-dir", default="docs/plans")
    parser.add_argument("--done-dir", default="tickets/done")
    args = parser.parse_args(argv)
    findings = find_stale_planning_docs(Path(args.plans_dir), Path(args.done_dir))
    if not findings:
        print("No planning docs with a stale claimed status found.")
        return 0
    print(f"{len(findings)} possible stale planning-doc claim(s) - review, do not auto-edit:")
    for f in findings:
        print(f"- {f.doc_path}\n    claims: {f.matched_text!r} ({f.signal})\n    likely shipped as: {f.matched_ticket_id}")
    return 0  # report-only: never a failing exit


if __name__ == "__main__":
    sys.exit(main())

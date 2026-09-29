#!/usr/bin/env python3
"""
Reports open tickets (`tickets/todos/**/TCK-*.md`, `tickets/inprogress/TCK-*.md`) that overlap a
given ticket or concern, for TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER.

Every automated duplicate check before this tool looked only at closed work (`tickets/working_log.csv`,
`docs/REGISTRY.yaml`) or, on the ticket-scoper's own new-ticket path, at `tickets/` without
`todos/`. A real miss: rpg-feature-planning's hand-authored wave ticket overlapped the already-open
`TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` and nothing flagged it (see this ticket's
own investigation.md for the fixture that reproduces the pair, since the real wave ticket isn't on
this branch or main).

Reads `tickets/todos/`/`tickets/inprogress/` live from disk on every call -- no index, so a ticket
written a minute ago is included (Out of Scope: adding open tickets to the `search_docs` index,
which is rebuilt only on doc changes and would reintroduce the same staleness this tool exists to
remove).

Two signals, either one triggers a hit (loose by design -- this is advisory, and false positives
are preferred over misses per this ticket's own Assumptions):
  (a) exact intersection between the query's code-area paths and a candidate's own
      `## Related Code Areas` paths (parsed via `parse_related_code_areas` -- the strongest,
      most deterministic signal);
  (b) >= 2 shared "distinctive terms" (lowercase, alphanumeric, length >= 5, minus a small
      stopword list) between the query's title+summary and a candidate's own title+Request
      Summary.

Body sections are parsed with the canonical parser (`tools/generate_registry.py::parse_body_section`
/ `parse_related_code_areas`, the same ones `tools/epic_folder_status.py` reuses), never a
hand-rolled regex.

**Advisory only. Always exits 0 and never classifies anything as a duplicate itself** -- it reports
candidates; a human or calling agent judges whether a hit is a real duplicate. Callers must route
hits to an informational field (`related_context`/`related_ticket`), never `conflicts`/
`is_duplicate`.

Usage:
  python3 tools/open_ticket_overlap.py --ticket-path tickets/todos/TCK-EXAMPLE.md
  python3 tools/open_ticket_overlap.py --title "..." --summary "..." --code-area src/foo.py [--code-area ...]
  python3 tools/open_ticket_overlap.py --ticket-path PATH --todos-root PATH --inprogress-root PATH  # tests
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from generate_registry import (  # noqa: E402
    parse_body_section,
    parse_related_code_areas,
    _strip_frontmatter,
)
from validate_frontmatter import extract_frontmatter  # noqa: E402

_REPO_ROOT = _TOOLS_DIR.parent
_DEFAULT_TODOS_ROOT = _REPO_ROOT / "tickets" / "todos"
_DEFAULT_INPROGRESS_ROOT = _REPO_ROOT / "tickets" / "inprogress"

_MIN_TERM_LEN = 5
_MIN_SHARED_TERMS = 2
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "about", "above", "after", "again", "against", "already", "always", "another", "around",
    "because", "before", "being", "below", "between", "could", "doesn", "doing", "during",
    "every", "first", "found", "from", "have", "having", "here", "into", "itself", "never",
    "other", "over", "should", "since", "still", "such", "than", "that", "their", "them",
    "then", "there", "these", "they", "this", "those", "through", "under", "until", "very",
    "were", "what", "when", "where", "which", "while", "with", "would",
}


def _distinctive_terms(text: str) -> set:
    return {
        tok for tok in _TOKEN_RE.findall(text.lower())
        if len(tok) >= _MIN_TERM_LEN and tok not in _STOPWORDS
    }


def _load_ticket(path: Path) -> Optional[dict]:
    """Returns {ticket_id, title, summary, code_areas} for a real ticket file, or None if it has
    no parseable `ticket_id` (frontmatter missing/malformed -- skipped, never guessed)."""
    text = path.read_text(encoding="utf-8")
    fm = extract_frontmatter(text) or {}
    ticket_id = fm.get("ticket_id")
    if not ticket_id:
        return None
    body = _strip_frontmatter(text)
    code_areas_text = parse_body_section(body, "Related Code Areas")
    return {
        "ticket_id": ticket_id,
        "path": str(path),
        "title": parse_body_section(body, "Title"),
        "summary": parse_body_section(body, "Request Summary"),
        "code_areas": parse_related_code_areas(code_areas_text),
    }


def find_overlapping_open_tickets(
    query_title: str,
    query_summary: str,
    query_code_areas: list,
    query_ticket_id: Optional[str] = None,
    todos_root: Path = _DEFAULT_TODOS_ROOT,
    inprogress_root: Path = _DEFAULT_INPROGRESS_ROOT,
) -> list:
    """Returns a list of `{ticket_id, path, matched_code_areas, matched_terms}` for every open
    ticket under `todos_root`/`inprogress_root` (recursive -- covers `tickets/todos/<folder>/`
    epics) that overlaps the query on either signal. Excludes any candidate whose own `ticket_id`
    equals `query_ticket_id`. Never raises on a malformed candidate file -- skipped, not guessed."""
    query_terms = _distinctive_terms(f"{query_title} {query_summary}")
    query_code_area_set = set(query_code_areas)

    candidates = []
    for root in (todos_root, inprogress_root):
        if root.exists():
            candidates.extend(sorted(root.rglob("TCK-*.md")))

    hits = []
    for path in candidates:
        loaded = _load_ticket(path)
        if loaded is None:
            continue
        if query_ticket_id is not None and loaded["ticket_id"] == query_ticket_id:
            continue

        matched_code_areas = sorted(query_code_area_set & set(loaded["code_areas"]))
        candidate_terms = _distinctive_terms(f"{loaded['title']} {loaded['summary']}")
        matched_terms = sorted(query_terms & candidate_terms)

        if matched_code_areas or len(matched_terms) >= _MIN_SHARED_TERMS:
            hits.append({
                "ticket_id": loaded["ticket_id"],
                "path": loaded["path"],
                "matched_code_areas": matched_code_areas,
                "matched_terms": matched_terms,
            })

    return hits


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticket-path", type=Path, default=None,
                         help="Load title/summary/code-areas/ticket_id from a real ticket file.")
    parser.add_argument("--title", default=None)
    parser.add_argument("--summary", default=None)
    parser.add_argument("--code-area", action="append", default=[], dest="code_areas",
                         help="Repeatable. A code-area path to match against.")
    parser.add_argument("--ticket-id", default=None,
                         help="Excludes a candidate with this exact ticket_id. Ignored if "
                              "--ticket-path is given (its own ticket_id is used instead).")
    parser.add_argument("--todos-root", type=Path, default=_DEFAULT_TODOS_ROOT)
    parser.add_argument("--inprogress-root", type=Path, default=_DEFAULT_INPROGRESS_ROOT)
    args = parser.parse_args(argv)

    if args.ticket_path is not None:
        loaded = _load_ticket(args.ticket_path)
        if loaded is None:
            print(json.dumps([]))
            return 0
        title, summary, code_areas, ticket_id = (
            loaded["title"], loaded["summary"], loaded["code_areas"], loaded["ticket_id"],
        )
    else:
        title, summary, code_areas, ticket_id = (
            args.title or "", args.summary or "", args.code_areas, args.ticket_id,
        )

    hits = find_overlapping_open_tickets(
        query_title=title,
        query_summary=summary,
        query_code_areas=code_areas,
        query_ticket_id=ticket_id,
        todos_root=args.todos_root,
        inprogress_root=args.inprogress_root,
    )
    print(json.dumps(hits, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

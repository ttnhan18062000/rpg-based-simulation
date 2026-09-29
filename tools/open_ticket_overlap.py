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

**Scoring (peer review finding, TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER review
round 2): a plain "either signal fires" boolean was measured against the real 82-ticket open corpus
and found unusable -- an average of 70.9/81 possible hits per query, with shared-term counts up to
15 on pure noise (ordinary prose like "actually"/"confirmed"/"different"), no separation from the
real pair. Replaced with a weighted, ranked score:**
  - exact code-area path intersection: `_CODE_AREA_WEIGHT` (10.0) per matched path -- the
    strongest, most deterministic signal, so it dominates;
  - term overlap: each shared "distinctive term" (lowercase, alphanumeric, length >= 5, minus a
    small stopword list) contributes its own IDF weight (`ln(n_docs / doc_freq)`, computed fresh
    each call over the *candidate corpus itself* -- a term in almost every open ticket scores
    near 0, a term unique to a handful of tickets scores high). No corpus-wide stopword hand-list
    was added on top of IDF -- IDF already suppresses generic report-style vocabulary
    proportionally, and the calibration test below confirms it's sufficient against the real
    corpus without further tuning.
  - results are ranked by total score, descending, and capped to the top `top_n` (default 5) --
    the cap, not an absolute score threshold, is what actually bounds output size (score
    distributions are corpus/query-dependent, so a fixed absolute cutoff isn't robust across
    different queries; only candidates with `score > min_score` are considered before capping,
    excluding literal zero-overlap entries).

`tests/tools/test_open_ticket_overlap_real_corpus.py` measures this against the *real*
`tickets/todos/`+`tickets/inprogress/` tree (not just synthetic fixtures): median hit count per
real ticket stays small, and the B0 fixture ranks the real
`TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` #1 both with and without code areas
(the latter is the concern-investigator call shape, which never has code areas to give).

Body sections are parsed with the canonical parser (`tools/generate_registry.py::parse_body_section`
/ `parse_related_code_areas`, the same ones `tools/epic_folder_status.py` reuses), never a
hand-rolled regex.

**Advisory only. Always exits 0, on every input including an empty/missing/unreadable
`--ticket-path` (peer review finding: a directory or nonexistent path previously raised and exited
1) -- fails open with an empty result and a stderr warning rather than crashing. Never classifies
anything as a duplicate itself** -- it reports candidates; a human or calling agent judges whether
a hit is a real duplicate. Callers must route hits to an informational field
(`related_context`/`related_ticket`), never `conflicts`/`is_duplicate`.

Usage:
  python3 tools/open_ticket_overlap.py --ticket-path tickets/todos/TCK-EXAMPLE.md
  python3 tools/open_ticket_overlap.py --title "..." --summary "..." --code-area src/foo.py [--code-area ...]
  python3 tools/open_ticket_overlap.py --ticket-path PATH --todos-root PATH --inprogress-root PATH  # tests
"""
from __future__ import annotations

import argparse
import json
import math
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
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "about", "above", "after", "again", "against", "already", "always", "another", "around",
    "because", "before", "being", "below", "between", "could", "doesn", "doing", "during",
    "every", "first", "found", "from", "have", "having", "here", "into", "itself", "never",
    "other", "over", "should", "since", "still", "such", "than", "that", "their", "them",
    "then", "there", "these", "they", "this", "those", "through", "under", "until", "very",
    "were", "what", "when", "where", "which", "while", "with", "would",
}

_CODE_AREA_WEIGHT = 10.0
_DEFAULT_TOP_N = 5
_DEFAULT_MIN_SCORE = 0.0  # excludes only literal zero-overlap candidates; top_n bounds output size


def _distinctive_terms(text: str) -> set:
    return {
        tok for tok in _TOKEN_RE.findall(text.lower())
        if len(tok) >= _MIN_TERM_LEN and tok not in _STOPWORDS
    }


def _build_doc_freq(candidate_term_sets: list) -> dict:
    """term -> number of candidate documents containing it, over the corpus being scanned this
    call (not a persisted/global corpus -- always fresh, matching the tool's own no-index,
    live-disk design)."""
    df: dict = {}
    for terms in candidate_term_sets:
        for t in terms:
            df[t] = df.get(t, 0) + 1
    return df


def _idf(term: str, doc_freq: dict, n_docs: int) -> float:
    """`ln(n_docs / doc_freq[term])`, clamped to >= 0. A term in every candidate scores 0 (no
    distinguishing power); a term unique to one candidate scores `ln(n_docs)`, the maximum."""
    if n_docs <= 1:
        return 0.0
    freq = doc_freq.get(term, 0)
    if freq <= 0:
        return math.log(n_docs)
    return max(0.0, math.log(n_docs / freq))


def _load_ticket(path: Path) -> Optional[dict]:
    """Returns {ticket_id, title, summary, code_areas} for a real ticket file, or None if it has
    no parseable `ticket_id` (frontmatter missing/malformed) OR the path can't be read at all --
    missing, a directory, or a permission error (peer review finding: `--ticket-path ""` resolves
    to `.`, a directory, and previously raised `IsADirectoryError` uncaught, breaking the
    always-exits-0 contract). Never guessed, never raises -- a read failure is reported to stderr
    and treated the same as "no ticket found here"."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"WARNING: open_ticket_overlap could not read {path!r}: {e}", file=sys.stderr)
        return None
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
    top_n: int = _DEFAULT_TOP_N,
    min_score: float = _DEFAULT_MIN_SCORE,
) -> list:
    """Returns up to `top_n` `{ticket_id, path, score, matched_code_areas, matched_terms}` dicts,
    ranked by `score` descending, for open tickets under `todos_root`/`inprogress_root` (recursive
    -- covers `tickets/todos/<folder>/` epics) that score above `min_score`. Excludes any
    candidate whose own `ticket_id` equals `query_ticket_id`. See module docstring for the scoring
    formula and why it replaced a plain boolean "either signal fires" check."""
    query_terms = _distinctive_terms(f"{query_title} {query_summary}")
    query_code_area_set = set(query_code_areas)

    candidate_paths = []
    for root in (todos_root, inprogress_root):
        if root.exists():
            candidate_paths.extend(sorted(root.rglob("TCK-*.md")))

    candidates = []
    for path in candidate_paths:
        loaded = _load_ticket(path)
        if loaded is None:
            continue
        if query_ticket_id is not None and loaded["ticket_id"] == query_ticket_id:
            continue
        loaded["terms"] = _distinctive_terms(f"{loaded['title']} {loaded['summary']}")
        candidates.append(loaded)

    n_docs = len(candidates)
    doc_freq = _build_doc_freq([c["terms"] for c in candidates])

    scored = []
    for cand in candidates:
        matched_code_areas = sorted(query_code_area_set & set(cand["code_areas"]))
        matched_terms = sorted(query_terms & cand["terms"])
        term_score = sum(_idf(t, doc_freq, n_docs) for t in matched_terms)
        area_score = _CODE_AREA_WEIGHT * len(matched_code_areas)
        total_score = area_score + term_score
        if total_score > min_score:
            scored.append({
                "ticket_id": cand["ticket_id"],
                "path": cand["path"],
                "score": round(total_score, 3),
                "matched_code_areas": matched_code_areas,
                "matched_terms": matched_terms,
            })

    scored.sort(key=lambda h: h["score"], reverse=True)
    return scored[:top_n]


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
    parser.add_argument("--top-n", type=int, default=_DEFAULT_TOP_N)
    parser.add_argument("--min-score", type=float, default=_DEFAULT_MIN_SCORE)
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
        top_n=args.top_n,
        min_score=args.min_score,
    )
    print(json.dumps(hits, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

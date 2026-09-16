"""Related Code Areas index health + close-time premise-staleness sweep
(TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE, Option A).

That ticket's own Decision (2026-09-15) chose to repair `docs/REGISTRY.yaml` rather than build a
second full-text scanner: widen `generate_registry.py::parse_related_code_areas()` to recognize
plain, non-backtick-quoted path bullets (done separately in that file), and extend the registry's
own ticket walk to index `tickets/todos/`/`tickets/inprogress/`, not only `tickets/done/` (also
done there). This module is the "mechanism that consumes the index" the Decision explicitly left
open as the implementer's own design call -- built as a sibling `tools/gate_checks/*.py` module
per this batch's own established convention, not wired into `.claude/workflows/implement-ticket.js`
directly (a bigger, separate decision left to its own ticket if wanted, not silently absorbed
here).

**Two related tools, both reading the now-repaired registry, not re-deriving citations
independently:**

1. `compute_open_ticket_citation_resolution_rate()` -- measures citation resolution accuracy
   across the real open-ticket population. **This used to also gate on the rate (a ratchet floor,
   `CITATION_RESOLUTION_FLOOR`); that gate was removed by TCK-20260916-CITATION-RESOLUTION-FLOOR-
   DEMOTE (2026-09-16). Do not rebuild it.** The floor broke `main`'s CI on 2026-09-16: closing
   `TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE` (an ordinary, legitimate ticket
   closure) shrank the open-ticket population 83 -> 82, which by itself moved the rate 96.1% ->
   96.0% -- no citation text changed, no broken reference was introduced. The denominator here is
   "currently open tickets," which moves on every ticket close/open regardless of citation
   quality, so a threshold over this rate fires on ordinary activity rather than on regression --
   the same inverted-signal shape as the deleted sidecar-attribution floor (see that module's own
   docstring, and TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE's Decision section, for
   the full precedent this follows). The measurement itself stays: it is genuinely useful reported
   context (see this module's own advisory sweep output and any report that surfaces it), just not
   something to block on.

2. `find_potentially_stale_open_tickets(touched_paths)` -- the actual close-time sweep: given the
   set of file paths a closing ticket's own diff touched, return open tickets whose declared
   Related Code Areas citations overlap. **Advisory only, per this ticket's own Scope** ("a shared
   file does not prove an invalidated claim") -- candidates for a human/agent to check, never an
   automatic block. Citations are compared after stripping a trailing `::Symbol` or `:line[-line]`
   reference suffix, so a citation like `src/foo.py::Bar.method` still matches a touched
   `src/foo.py`. Unaffected by the floor's removal above -- it never gated on anything.

Mirrors the batch's own `check_*()` shape where it applies: `List[dict]` (`{"status":
"PASS"|"FAIL", "evidence": "..."}`), `MARKER:` + `json.dumps(result)` stdout contract in
`__main__`.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable, List

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REGISTRY_PATH = _REPO_ROOT / "docs" / "REGISTRY.yaml"

_PATH_LIKE_EXTENSIONS = (
    ".py", ".md", ".yaml", ".yml", ".json", ".js", ".ts", ".tsx", ".html", ".css", ".csv", ".txt",
)


def _looks_like_path(token: str) -> bool:
    """Mirrors generate_registry.py's own identically-named heuristic exactly (contains "/" or
    ends in a known extension). Needed here because `related_code_areas` can also contain
    backtick-quoted inline CODE-SYMBOL references in ordinary prose (e.g. a bullet reading
    "`SocialBondUpdate` gains a new field") -- `parse_related_code_areas()` extracts every
    backtick-quoted token unconditionally, by design, matching its pre-existing, unchanged
    behavior for real path citations. Filtering by shape here (not there) is what keeps a citation
    accuracy measurement honest: an inline symbol reference was never meant to resolve as a file
    path, and counting it as a "citation" that "fails to resolve" would silently and substantially
    inflate this check's own false-positive rate -- confirmed directly: an earlier, unfiltered
    version of this measurement read 90.3% (299/331) against the real corpus; filtering to only
    path-shaped citations (matching TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE's
    own investigation.md Measurement 3 methodology exactly) reads 96.1% (299/311) instead -- same
    numerator, smaller and more honest denominator.
    """
    return "/" in token or token.endswith(_PATH_LIKE_EXTENSIONS)


def _strip_symbol_line_suffix(citation: str) -> str:
    """Best-effort strip of a trailing '::Symbol' or ':line[-line,...]' reference suffix some
    citations use to point at a specific symbol or line range within a real file, so the base path
    itself can be checked/matched independent of that suffix."""
    citation = citation.split("::")[0]
    citation = re.sub(r":\d[\d,\-]*$", "", citation)
    return citation.strip()


def load_open_ticket_entries(registry_path: Path = None) -> List[dict]:
    """Load docs/REGISTRY.yaml (or a supplied path -- tests inject a synthetic file instead) and
    return only the ticket entries whose own path is under tickets/todos/ or tickets/inprogress/."""
    import yaml as _yaml

    path = registry_path if registry_path is not None else _REGISTRY_PATH
    if not path.exists():
        return []
    entries = _yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return [
        e for e in entries
        if e.get("type") == "ticket"
        and (e.get("path", "").startswith("tickets/todos/") or e.get("path", "").startswith("tickets/inprogress/"))
    ]


def compute_open_ticket_citation_resolution_rate(
    entries: List[dict] = None, root: Path = None,
) -> "tuple[float, int, int]":
    """Returns (rate_pct, resolved_count, total_count) -- what fraction of open-ticket Related
    Code Areas citations resolve to a real path on disk today. A citation containing a glob/brace-
    expansion placeholder (e.g. `agent-monitoring/data/*/runs.jsonl`) is excluded from both the
    numerator and denominator -- it was never meant to resolve to one literal path."""
    if entries is None:
        entries = load_open_ticket_entries()
    root = root if root is not None else _REPO_ROOT

    total = 0
    resolved = 0
    for e in entries:
        for area in e.get("related_code_areas") or []:
            path = _strip_symbol_line_suffix(area)
            if not _looks_like_path(path):
                continue
            if "*" in path or "{" in path:
                continue
            total += 1
            if (root / path).exists():
                resolved += 1

    rate = round(100 * resolved / total, 1) if total else 100.0
    return rate, resolved, total


def find_potentially_stale_open_tickets(
    touched_paths: Iterable[str], entries: List[dict] = None,
) -> List[dict]:
    """The close-time consumption mechanism itself: given the paths a closing ticket's own diff
    touched, return open-ticket registry entries whose Related Code Areas citations overlap with
    any of them. Advisory only -- these are candidates for a human/agent to check, not an
    automatic failure (see this module's own docstring)."""
    if entries is None:
        entries = load_open_ticket_entries()

    touched = set(touched_paths)
    candidates = []
    for e in entries:
        normalized_areas = {
            _strip_symbol_line_suffix(a) for a in (e.get("related_code_areas") or [])
        }
        overlap = normalized_areas & touched
        if overlap:
            candidates.append({
                "ticket_id": e.get("ticket_id"),
                "path": e.get("path"),
                "title": e.get("title"),
                "overlapping_paths": sorted(overlap),
            })
    return candidates


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--touched-paths", nargs="*", default=None,
        help=(
            "Run the close-time sweep against these paths instead of the health-ratchet check "
            "(e.g. the output of `git status --porcelain` for a ticket about to close)."
        ),
    )
    args = parser.parse_args(argv)

    if args.touched_paths is not None:
        result = find_potentially_stale_open_tickets(args.touched_paths)
        print("MARKER:" + json.dumps(result))
        return 0

    rate, resolved, total = compute_open_ticket_citation_resolution_rate()
    result = [{
        "status": "PASS",
        "evidence": f"open-ticket Related Code Areas citation resolution rate {rate}% ({resolved}/{total})",
    }]
    print("MARKER:" + json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())

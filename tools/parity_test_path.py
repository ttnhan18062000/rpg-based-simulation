"""Shared `test_path` citation parser for the parity ledger.

Extracted from `tools/gate_checks/mechanics_auditor_static.py`
(TCK-20260705-GATE-DET-MECHANICS-AUDITOR) so `tools/parity_index.py` and
`tools/gate_checks/mechanics_auditor_static.py` parse `test_path` through the same function
instead of two independently-maintained regexes (TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT).
Before this split, `parity_index.py`'s own narrower `_TEST_PATH_DECLARED_RE` accepted only a single
path with at most one `::` level and rejected everything else (backtick-wrapped paths,
comma/`+`/`;`-joined multi-citations, and multi-level node-ids like `path.py::Class::method`) --
those citations were invisible to the derived index's `test_refs` table and its `absent_file`
health check, so a stale citation among them went undetected. `mechanics_auditor_static.py` still
re-imports this module's names directly (not a copy) so the two call sites can never diverge again.

Stays path-level: this module classifies and splits citations, it does not decide whether a symbol
inside a file exists. Symbol-level verification remains `mechanics_auditor_static.check_test_path`'s
job (it runs pytest on the parsed node-id).
"""

import re

_BACKTICK_FULL_RE = re.compile(r"^`([^`]+)`$")
# `,`/`+`/`;` split with optional surrounding whitespace, OR a single `|` with REQUIRED
# whitespace on both sides -- added by TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL for
# INFRA-221/STRAT-236's genuine ` | `-delimited multi-citations. A bare `|` (no whitespace
# requirement) was checked against the real corpus first and found unsafe: INFRA-405's test_path
# contains a literal `|| true` (a shell operator quoted inside prose, not a citation delimiter --
# confirmed the only other `|` occurrence anywhere in the corpus). `\s+\|\s+` never matches either
# `|` inside `||` (neither has whitespace on both immediate sides), so it splits the two genuine
# pipe-delimited entries correctly while leaving `|| true` untouched.
_DELIM_SPLIT_RE = re.compile(r"\s*[,+;]\s*|\s+\|\s+")
_NODE_ID_RE = re.compile(r"^[\w./\-]+\.py(::[\w \[\]./:\-]+)?$")

# A bare directory citation (e.g. `tests/unit/lab/`), added by
# TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS: `check_test_path()` in
# mechanics_auditor_static.py already handles this shape correctly with zero changes needed
# there -- it resolves citations via plain `Path.exists()` (true for directories) and invokes
# `pytest <citation> -x -q` (a directory is a completely normal pytest argument that runs every
# test file inside it). The gap was purely this module's own regex never having accepted the
# shape. Requires a trailing `/` specifically (not just "no `.py` extension") to stay
# unambiguous against a malformed/truncated file path that simply forgot `.py`.
_DIR_RE = re.compile(r"^[\w./\-]+/$")


def _strip_full_backtick(s: str) -> str:
    match = _BACKTICK_FULL_RE.match(s)
    return match.group(1) if match else s


def _matches_citation_shape(candidate: str) -> bool:
    return bool(_NODE_ID_RE.match(candidate) or _DIR_RE.match(candidate))


def parse_test_path_citations(raw) -> "tuple[list[str] | None, str | None]":
    """Parse a ledger entry's raw `test_path` string into a list of invocable citations.

    Returns (citations, None) on success, or (None, error) on a hard-FAIL/unparseable case. Never
    raises. Handles the legacy shapes found in the real ledger (investigation.md's format
    survey): clean node-id, single backtick-wrapped, comma/`+`/`;`/` | `-joined multi-citation,
    and unparseable parenthetical-annotated prose.
    """
    if raw is None or not str(raw).strip():
        return (None, "test_path is null/missing")

    stripped = str(raw).strip()
    parts = _DELIM_SPLIT_RE.split(stripped)

    if len(parts) > 1:
        resolved = []
        for part in parts:
            candidate = _strip_full_backtick(part.strip())
            if not _matches_citation_shape(candidate):
                return (
                    None,
                    "unparseable test_path (multi-citation candidate but one segment did not "
                    f"resolve to a clean path): {raw!r}",
                )
            resolved.append(candidate)
        return (resolved, None)

    candidate = _strip_full_backtick(stripped)
    if _matches_citation_shape(candidate):
        return ([candidate], None)

    return (None, f"unparseable test_path: {raw!r}")

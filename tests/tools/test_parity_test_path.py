"""Tests for tools/parity_test_path.py (TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT Step 1).

Covers the four legacy `test_path` shapes documented in investigation.md's format survey, the
two-level node-id regression this ticket fixes for `parity_index.py`, and the equivalence
guarantee that `mechanics_auditor_static.parse_test_path_citations` is the same object as this
module's -- not an independently-maintained copy that could drift again.
"""

import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from parity_test_path import parse_test_path_citations  # noqa: E402


def test_clean_node_id_parses_to_single_citation():
    citations, err = parse_test_path_citations("tests/unit/test_x.py::test_y")

    assert err is None
    assert citations == ["tests/unit/test_x.py::test_y"]


def test_single_backtick_wrapped_path_is_unwrapped():
    citations, err = parse_test_path_citations("`tests/unit/test_x.py::test_y`")

    assert err is None
    assert citations == ["tests/unit/test_x.py::test_y"]


def test_multi_citation_delimiters_all_split_correctly():
    for raw in (
        "tests/a.py::test_1, tests/b.py::test_2",
        "tests/a.py::test_1 + tests/b.py::test_2",
        "tests/a.py::test_1; tests/b.py::test_2",
    ):
        citations, err = parse_test_path_citations(raw)
        assert err is None, raw
        assert citations == ["tests/a.py::test_1", "tests/b.py::test_2"], raw


def test_pipe_delimiter_with_surrounding_whitespace_splits_correctly():
    """TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL: INFRA-221/STRAT-236's real shape --
    ` | `-joined multi-citation, previously unparseable."""
    raw = "tests/a.py::test_1 | tests/b.py::test_2 | tests/c.py::test_3"
    citations, err = parse_test_path_citations(raw)
    assert err is None, raw
    assert citations == ["tests/a.py::test_1", "tests/b.py::test_2", "tests/c.py::test_3"]


def test_doubled_pipe_with_no_surrounding_whitespace_is_not_treated_as_a_delimiter():
    """Confirmed against the real corpus (TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL):
    INFRA-405's test_path contains a literal `|| true` (a shell operator quoted inside prose,
    the only other `|` occurrence anywhere in the ledger) -- a bare `|` delimiter would have
    incorrectly split it into empty/garbage fragments. `\\s+\\|\\s+` requires whitespace on both
    immediate sides of the pipe, which neither `|` inside `||` has, so it's never treated as a
    delimiter here. (This entry is still correctly unparseable overall -- its pre-existing comma-
    delimited parenthetical annotations already broke it before this fix, and still do; this test
    only pins that the pipe change itself introduces no NEW incorrect split.)"""
    raw = "tests/x.py::test_a (works, mostly); command not suffixed with swallowing || true"
    citations, err = parse_test_path_citations(raw)
    assert err is not None
    assert citations is None

    # Directly confirms the delimiter regex itself never treats either `|` inside `||` as a
    # split point -- isolates the claim from the comma-splitting this fixture also triggers.
    from parity_test_path import _DELIM_SPLIT_RE
    doubled_pipe_only = "left side || right side"
    assert _DELIM_SPLIT_RE.split(doubled_pipe_only) == [doubled_pipe_only], (
        "a doubled pipe with no surrounding whitespace must never be split"
    )


def test_unparseable_prose_returns_none_and_error():
    raw = "`tests/tools/test_x.py` (indirectly via `Y` and `Z` flow)"

    citations, err = parse_test_path_citations(raw)

    assert citations is None
    assert raw in err


def test_two_level_node_id_is_accepted():
    """Regression case: parity_index.py's old `_TEST_PATH_DECLARED_RE` rejected a two-level
    node-id (only `[\\w_]+` was allowed after `::`, so a second `::` broke the match). The shared
    parser here already handles it -- this pins that behavior so the index's adoption of the
    shared parser doesn't silently regress it."""
    citations, err = parse_test_path_citations("tests/x.py::TestClass::test_method")

    assert err is None
    assert citations == ["tests/x.py::TestClass::test_method"]


def test_bare_directory_citation_is_accepted():
    """TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS: a bare directory (`tests/unit/lab/`)
    is a completely normal pytest argument -- check_test_path() in mechanics_auditor_static.py
    already handles it correctly via plain Path.exists() and `pytest <citation> -x -q`, both of
    which work fine for a directory. The only gap was this module's own regex never accepting
    the shape; this pins the fix."""
    citations, err = parse_test_path_citations("tests/unit/lab/")

    assert err is None
    assert citations == ["tests/unit/lab/"]


def test_directory_citation_without_trailing_slash_is_still_unparseable():
    """A path with no `.py` extension and no trailing `/` stays rejected -- accepting it would
    make an accidentally-truncated file path (someone dropped `.py` by mistake) silently look
    like a deliberate directory citation instead of the malformed citation it actually is."""
    citations, err = parse_test_path_citations("tests/unit/lab")

    assert citations is None
    assert "tests/unit/lab" in err


def test_directory_citation_participates_in_multi_citation_lists():
    citations, err = parse_test_path_citations("tests/unit/lab/; tests/unit/api/test_x.py::test_y")

    assert err is None
    assert citations == ["tests/unit/lab/", "tests/unit/api/test_x.py::test_y"]


def test_null_and_empty_test_path_are_unparseable_not_crashes():
    for raw in (None, "", "   "):
        citations, err = parse_test_path_citations(raw)
        assert citations is None
        assert "null/missing" in err


def test_mechanics_auditor_static_reimports_same_function_object():
    from gate_checks import mechanics_auditor_static
    import parity_test_path

    assert mechanics_auditor_static.parse_test_path_citations is parity_test_path.parse_test_path_citations

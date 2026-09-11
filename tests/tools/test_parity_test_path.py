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


def test_null_and_empty_test_path_are_unparseable_not_crashes():
    for raw in (None, "", "   "):
        citations, err = parse_test_path_citations(raw)
        assert citations is None
        assert "null/missing" in err


def test_mechanics_auditor_static_reimports_same_function_object():
    from gate_checks import mechanics_auditor_static
    import parity_test_path

    assert mechanics_auditor_static.parse_test_path_citations is parity_test_path.parse_test_path_citations

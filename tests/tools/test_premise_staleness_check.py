"""Tests for tools/gate_checks/premise_staleness_check.py
(TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE, Option A).
"""
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_GATE_CHECKS_DIR = _TOOLS_DIR / "gate_checks"
for _dir in (str(_TOOLS_DIR), str(_GATE_CHECKS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from premise_staleness_check import (  # noqa: E402
    CITATION_RESOLUTION_FLOOR,
    _looks_like_path,
    _strip_symbol_line_suffix,
    check_related_code_areas_health,
    compute_open_ticket_citation_resolution_rate,
    find_potentially_stale_open_tickets,
    load_open_ticket_entries,
)


def _entry(path, related_code_areas=None, ticket_id=None, title=""):
    return {
        "type": "ticket",
        "path": path,
        "ticket_id": ticket_id or path,
        "title": title,
        "related_code_areas": related_code_areas or [],
    }


# ---------------------------------------------------------------------------
# _strip_symbol_line_suffix / _looks_like_path
# ---------------------------------------------------------------------------

def test_strip_symbol_suffix_removes_double_colon_reference():
    assert _strip_symbol_line_suffix("src/foo.py::Bar.method") == "src/foo.py"


def test_strip_symbol_suffix_removes_line_number_reference():
    assert _strip_symbol_line_suffix("src/foo.py:42") == "src/foo.py"


def test_strip_symbol_suffix_removes_line_range_reference():
    assert _strip_symbol_line_suffix("src/foo.py:68-92,102-133") == "src/foo.py"


def test_strip_symbol_suffix_no_change_for_plain_path():
    assert _strip_symbol_line_suffix("src/foo.py") == "src/foo.py"


def test_looks_like_path_true_for_slash_or_extension():
    assert _looks_like_path("src/foo.py")
    assert _looks_like_path("Legend.tsx")


def test_looks_like_path_false_for_bare_symbol():
    assert not _looks_like_path("SocialBondUpdate")
    assert not _looks_like_path("DECAY_INTERVAL")


# ---------------------------------------------------------------------------
# load_open_ticket_entries
# ---------------------------------------------------------------------------

def test_load_open_ticket_entries_filters_by_path_prefix(tmp_path):
    registry = tmp_path / "REGISTRY.yaml"
    registry.write_text(
        "- type: ticket\n  path: tickets/done/TCK-A.md\n  ticket_id: TCK-A\n"
        "- type: ticket\n  path: tickets/todos/TCK-B.md\n  ticket_id: TCK-B\n"
        "- type: ticket\n  path: tickets/inprogress/TCK-C.md\n  ticket_id: TCK-C\n"
        "- type: doc\n  path: docs/foo.md\n",
        encoding="utf-8",
    )
    entries = load_open_ticket_entries(registry)
    assert {e["ticket_id"] for e in entries} == {"TCK-B", "TCK-C"}


def test_load_open_ticket_entries_missing_file_returns_empty(tmp_path):
    assert load_open_ticket_entries(tmp_path / "does-not-exist.yaml") == []


# ---------------------------------------------------------------------------
# compute_open_ticket_citation_resolution_rate / check_related_code_areas_health
# ---------------------------------------------------------------------------

def test_resolution_rate_100_when_all_citations_exist(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("", encoding="utf-8")
    entries = [_entry("tickets/todos/TCK-A.md", ["src/foo.py"])]
    rate, resolved, total = compute_open_ticket_citation_resolution_rate(entries, root=tmp_path)
    assert (rate, resolved, total) == (100.0, 1, 1)


def test_resolution_rate_drops_when_citation_missing(tmp_path):
    entries = [_entry("tickets/todos/TCK-A.md", ["src/does_not_exist.py"])]
    rate, resolved, total = compute_open_ticket_citation_resolution_rate(entries, root=tmp_path)
    assert (rate, resolved, total) == (0.0, 0, 1)


def test_resolution_rate_ignores_non_path_shaped_citations(tmp_path):
    # Bare inline code-symbol references (no slash, no known extension) must not count against
    # the denominator at all -- they were never meant to be file citations.
    entries = [_entry("tickets/todos/TCK-A.md", ["SocialBondUpdate", "DECAY_INTERVAL"])]
    rate, resolved, total = compute_open_ticket_citation_resolution_rate(entries, root=tmp_path)
    assert total == 0
    assert rate == 100.0


def test_resolution_rate_ignores_glob_placeholders(tmp_path):
    entries = [_entry("tickets/todos/TCK-A.md", ["agent-monitoring/data/*/runs.jsonl"])]
    rate, resolved, total = compute_open_ticket_citation_resolution_rate(entries, root=tmp_path)
    assert total == 0


def test_resolution_rate_with_no_citations_at_all_is_100(tmp_path):
    entries = [_entry("tickets/todos/TCK-A.md", [])]
    rate, resolved, total = compute_open_ticket_citation_resolution_rate(entries, root=tmp_path)
    assert (rate, resolved, total) == (100.0, 0, 0)


def test_health_check_passes_at_or_above_floor(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("", encoding="utf-8")
    entries = [_entry("tickets/todos/TCK-A.md", ["src/foo.py"])]
    results = check_related_code_areas_health(entries, root=tmp_path, floor=50.0)
    assert results[0]["status"] == "PASS"


def test_health_check_fails_when_below_floor(tmp_path):
    entries = [_entry("tickets/todos/TCK-A.md", ["src/does_not_exist.py"])]
    results = check_related_code_areas_health(entries, root=tmp_path, floor=50.0)
    assert results[0]["status"] == "FAIL"
    assert "dropped below the ratchet floor" in results[0]["evidence"]


def test_ceiling_may_only_increase_never_used_to_paper_over_a_regression():
    assert CITATION_RESOLUTION_FLOOR == 96.1, (
        "CITATION_RESOLUTION_FLOOR changed -- if this is because the registry's own accuracy "
        "genuinely improved, raise this value to match (never lower it to paper over a regression)"
    )


def test_real_corpus_is_at_or_above_the_ratchet_floor():
    results = check_related_code_areas_health()
    assert results[0]["status"] == "PASS", f"real corpus dropped below the floor: {results[0]}"


# ---------------------------------------------------------------------------
# find_potentially_stale_open_tickets (the close-time sweep)
# ---------------------------------------------------------------------------

def test_sweep_finds_overlapping_open_ticket():
    entries = [_entry(
        "tickets/todos/TCK-A.md", ["src/foo.py", "src/bar.py"], ticket_id="TCK-A", title="A",
    )]
    candidates = find_potentially_stale_open_tickets(["src/foo.py"], entries)
    assert len(candidates) == 1
    assert candidates[0]["ticket_id"] == "TCK-A"
    assert candidates[0]["overlapping_paths"] == ["src/foo.py"]


def test_sweep_no_overlap_returns_empty():
    entries = [_entry("tickets/todos/TCK-A.md", ["src/foo.py"], ticket_id="TCK-A")]
    candidates = find_potentially_stale_open_tickets(["src/unrelated.py"], entries)
    assert candidates == []


def test_sweep_matches_across_symbol_suffix():
    # A citation with a trailing ::Symbol reference still matches a touched bare path.
    entries = [_entry("tickets/todos/TCK-A.md", ["src/foo.py::Bar.method"], ticket_id="TCK-A")]
    candidates = find_potentially_stale_open_tickets(["src/foo.py"], entries)
    assert len(candidates) == 1


def test_sweep_multiple_tickets_only_overlapping_ones_returned():
    entries = [
        _entry("tickets/todos/TCK-A.md", ["src/foo.py"], ticket_id="TCK-A"),
        _entry("tickets/todos/TCK-B.md", ["src/unrelated.py"], ticket_id="TCK-B"),
    ]
    candidates = find_potentially_stale_open_tickets(["src/foo.py"], entries)
    assert [c["ticket_id"] for c in candidates] == ["TCK-A"]


def test_sweep_is_advisory_never_raises_on_large_overlap():
    entries = [_entry("tickets/todos/TCK-A.md", [f"src/f{i}.py" for i in range(50)], ticket_id="TCK-A")]
    candidates = find_potentially_stale_open_tickets([f"src/f{i}.py" for i in range(50)], entries)
    assert len(candidates) == 1  # one ticket, however many overlapping paths -- never an exception


def test_real_corpus_sweep_finds_a_match_when_touching_a_live_open_tickets_own_citation():
    # Deliberately does not hardcode which ticket_id must appear -- the open-ticket corpus churns
    # constantly (a ticket this test once hardcoded moved to tickets/done/ the same session that
    # wrote it, breaking the test on its very first real regression run). Instead: pick a real,
    # currently-open ticket's own first real citation at test-run time, touch exactly that path,
    # and confirm the sweep finds that same ticket -- proves real end-to-end integration against
    # the live registry without pinning to any one ticket's own transient lifecycle.
    entries = load_open_ticket_entries()
    with_areas = [e for e in entries if e.get("related_code_areas")]
    if not with_areas:
        import pytest
        pytest.skip("no open ticket with any Related Code Areas content exists right now")
    target = with_areas[0]
    touched_path = _strip_symbol_line_suffix(target["related_code_areas"][0])
    candidates = find_potentially_stale_open_tickets([touched_path])
    ticket_ids = {c["ticket_id"] for c in candidates}
    assert target["ticket_id"] in ticket_ids


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------

def test_cli_default_mode_prints_health_check_marker_output():
    result = subprocess.run(
        [sys.executable, str(_GATE_CHECKS_DIR / "premise_staleness_check.py")],
        cwd=str(_REPO_ROOT), capture_output=True, text=True,
    )
    assert "MARKER:" in result.stdout
    assert '"status":' in result.stdout
    assert result.returncode == 0


def test_cli_touched_paths_mode_prints_sweep_marker_output():
    # Uses a synthetic, never-real touched path -- the point of this test is CLI wiring/output
    # shape (MARKER: + valid JSON), not whether any particular real ticket is found (that's
    # test_real_corpus_sweep_finds_a_match_when_touching_a_live_open_tickets_own_citation's job,
    # and hardcoding a specific real ticket_id here proved fragile against corpus churn).
    result = subprocess.run(
        [sys.executable, str(_GATE_CHECKS_DIR / "premise_staleness_check.py"),
         "--touched-paths", "src/this/path/does/not/exist/anywhere.py"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True,
    )
    assert "MARKER:" in result.stdout
    assert result.returncode == 0


def test_makefile_wires_premise_staleness_check():
    makefile_text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "premise-staleness-check:" in makefile_text
    assert "premise_staleness_check.py" in makefile_text
    assert "premise-staleness-check" in makefile_text.splitlines()[0], (
        ".PHONY line must declare the new target"
    )

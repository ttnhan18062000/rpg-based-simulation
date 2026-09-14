"""Tests for tools/agent-monitoring/agent_tool_usage_baseline.py
(TCK-20260904-AGENT-TOOL-USAGE-BASELINE).

Mirrors tests/tools/test_retrieval_baseline_metrics.py's design: inline-dict unit tests per
function (no file I/O for the synthetic-fixture cases), an ast-based reuse guard proving this
module composes generate_retro.py's load_data_glob rather than reimplementing a shard-glob loader,
a tmp_path-constructed fixture for the multi-week-shard glob case, and real-corpus integration
tests (sanity-check reconciliation, read-only guard via git-porcelain diffing, CLI smoke test) —
never fixtures for those, which would make the corresponding assertion vacuous.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_MODULE_PATH = _MONITORING_TOOLS_DIR / "agent_tool_usage_baseline.py"
_REAL_AGENT_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"
_AGENTS_DIR = _REPO_ROOT / ".claude" / "agents"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import agent_tool_usage_baseline as atub  # noqa: E402
from agent_tool_usage_baseline import (  # noqa: E402
    UNATTRIBUTED,
    bucket_for,
    build_report,
    build_usage_table,
    load_all_tool_rows,
    load_all_tool_rows_with_line_count,
    registered_agents,
)
from validate import load_data_glob, load_data_glob_with_line_count  # noqa: E402

_MODULE_SOURCE = _MODULE_PATH.read_text()
_MODULE_AST = ast.parse(_MODULE_SOURCE)


def _imported_names() -> set:
    names = set()
    for node in ast.walk(_MODULE_AST):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)
    return names


# ---------------------------------------------------------------------------
# AC1 — exactly one row per registered agent plus one unattributed row
# ---------------------------------------------------------------------------

def test_output_has_exactly_16_agent_rows_plus_unattributed():
    live_expected = sorted(p.stem for p in _AGENTS_DIR.glob("*.md"))
    assert registered_agents() == live_expected

    table = build_usage_table([], registered_agents())
    assert set(table.keys()) == set(live_expected) | {UNATTRIBUTED}
    assert len(table) == len(live_expected) + 1


def test_agent_row_present_with_zero_count_for_agents_with_no_real_rows():
    known_agents = ["agent-with-rows", "agent-with-no-rows"]
    rows = [{"agent": "agent-with-rows", "tool": "Read", "input_summary": "src/foo.py"}]

    table = build_usage_table(rows, known_agents)

    assert "agent-with-no-rows" in table
    assert table["agent-with-no-rows"]["count"] == 0
    assert table["agent-with-no-rows"]["tools"] == {}
    assert table["agent-with-rows"]["count"] == 1


# ---------------------------------------------------------------------------
# Bucketing — null/non-matching agent values all land in 'unattributed'
# ---------------------------------------------------------------------------

def test_null_and_non_matching_agent_values_bucket_to_unattributed():
    known_agents = {"implementer"}
    assert bucket_for({"agent": None}, known_agents) == UNATTRIBUTED
    assert bucket_for({"agent": "finalizer"}, known_agents) == UNATTRIBUTED
    assert bucket_for({"agent": "claude"}, known_agents) == UNATTRIBUTED
    assert bucket_for({"agent": "orchestrator"}, known_agents) == UNATTRIBUTED
    assert bucket_for({"agent": "some-typo"}, known_agents) == UNATTRIBUTED
    assert bucket_for({"agent": "implementer"}, known_agents) == "implementer"
    assert bucket_for({}, known_agents) == UNATTRIBUTED

    known_agents_list = ["implementer"]
    rows = [
        {"agent": None, "tool": "Read", "input_summary": "a"},
        {"agent": "finalizer", "tool": "Read", "input_summary": "b"},
        {"agent": "claude", "tool": "Bash", "input_summary": "c"},
        {"agent": "orchestrator", "tool": "Bash", "input_summary": "d"},
        {"agent": "some-typo", "tool": "Edit", "input_summary": "e"},
        {"agent": "implementer", "tool": "Edit", "input_summary": "f"},
    ]
    table = build_usage_table(rows, known_agents_list)
    assert table[UNATTRIBUTED]["count"] == 5
    assert table["implementer"]["count"] == 1


# ---------------------------------------------------------------------------
# AC2 — glob correctness, including unknown-week fallback shard
# ---------------------------------------------------------------------------

def test_glob_matches_all_dated_week_shards_and_unknown_week(tmp_path):
    data_dir = tmp_path / "agent-monitoring" / "data"
    (data_dir / "2026-W01").mkdir(parents=True)
    (data_dir / "2026-W02").mkdir(parents=True)
    (data_dir / "unknown-week").mkdir(parents=True)
    (data_dir / "2026-W01" / "tools.jsonl").write_text(
        json.dumps({"agent": "implementer", "tool": "Read", "input_summary": "a"}) + "\n"
    )
    (data_dir / "2026-W02" / "tools.jsonl").write_text(
        json.dumps({"agent": "implementer", "tool": "Bash", "input_summary": "b"}) + "\n"
        + json.dumps({"agent": None, "tool": "Read", "input_summary": "c"}) + "\n"
    )
    (data_dir / "unknown-week" / "tools.jsonl").write_text(
        json.dumps({"agent": None, "tool": "Bash", "input_summary": "d"}) + "\n"
    )

    rows = load_all_tool_rows(data_dir)
    assert len(rows) == 4
    assert {r["input_summary"] for r in rows} == {"a", "b", "c", "d"}


def test_reuses_load_data_glob_not_a_fourth_loader():
    imported = _imported_names()
    assert "load_data_glob" in imported

    for node in ast.walk(_MODULE_AST):
        if isinstance(node, ast.Import):
            assert node.names[0].name != "sqlite3", "must not connect to the index db directly"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"read_text", "read_bytes", "readlines"}, (
                "must not read a *.jsonl file directly — reuse load_data_glob"
            )


def test_sum_of_per_agent_counts_matches_wc_l_sanity_check_on_real_corpus():
    """TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS item 3: the original version of this test
    computed real_total via its own independent glob+read of the live corpus, THEN called
    load_all_tool_rows() (a second, separate glob+read of the same files) -- any concurrent
    session's PostToolUse hook appending a tools.jsonl row between the two reads produced a real,
    reproducible off-by-one (assert 221850 == 221849). load_all_tool_rows_with_line_count()
    derives both numbers from ONE read per shard, eliminating the race entirely rather than just
    narrowing its window.

    Regression proof this actually fixes the race (not just moves it): inject a write into a real
    shard file mid-way through a single load_all_tool_rows_with_line_count() call and confirm the
    two returned numbers still agree with each other, immediately below.
    """
    rows, real_total = load_all_tool_rows_with_line_count()
    report = build_report(rows)

    assert report["total_rows_seen"] == real_total
    assert report["total_rows_across_all_agent_rows"] == real_total


def test_injected_write_between_the_old_two_reads_no_longer_desyncs_the_count(tmp_path, monkeypatch):
    """Demonstrates the fix directly, per this ticket's own Acceptance Criteria: reproduces the
    OLD race shape (an ad-hoc line count computed independently of load_data_glob_with_line_count,
    with a write injected in between) to confirm it WOULD have desynced, then confirms the NEW
    single-read function is immune to the identical injected write.
    """
    data_dir = tmp_path / "data"
    week_dir = data_dir / "2026-W01"
    week_dir.mkdir(parents=True)
    shard = week_dir / "tools.jsonl"
    shard.write_text('{"tool": "Read"}\n{"tool": "Edit"}\n')

    # OLD race shape: an independent read, then a write happens, then load_data_glob's own read.
    old_style_count = sum(1 for line in shard.read_text().splitlines() if line.strip())
    shard.write_text(shard.read_text() + '{"tool": "Bash"}\n')  # simulates a concurrent hook append
    new_rows = load_data_glob(data_dir, "tools")
    assert old_style_count != len(new_rows), (
        "sanity check: the old two-read shape must actually desync when a write lands between "
        "the reads, or this test isn't reproducing the real race"
    )

    # NEW shape: reset the fixture, inject the same write via a monkeypatched read to prove the
    # single-read function only ever sees ONE consistent state of the file, never split across
    # a count-read and a separate parse-read.
    shard.write_text('{"tool": "Read"}\n{"tool": "Edit"}\n')
    real_read_text = Path.read_text
    call_count = {"n": 0}

    def _read_text_with_injected_write(self, *args, **kwargs):
        result = real_read_text(self, *args, **kwargs)
        call_count["n"] += 1
        if self == shard and call_count["n"] == 1:
            # A genuine race would need a SECOND read to observe this write. The single-read
            # function must never issue that second read.
            shard.write_text(result + '{"tool": "Bash"}\n')
        return result

    monkeypatch.setattr(Path, "read_text", _read_text_with_injected_write)
    rows, line_count = load_data_glob_with_line_count(data_dir, "tools")
    assert line_count == len(rows), (
        "the single-read function must derive both numbers from the same read, immune to a "
        "write injected immediately after that read completes"
    )
    assert line_count == 2, (
        "must reflect the state at the moment of its own single read (2 lines), not the "
        "injected write that landed after (which a second, independent read would have seen)"
    )


# ---------------------------------------------------------------------------
# AC3 — every nonzero tool entry has a real, labeled-truncated example
# ---------------------------------------------------------------------------

def test_every_nonzero_tool_entry_has_a_labeled_truncated_example():
    known_agents = ["implementer"]
    rows = [
        {"agent": "implementer", "tool": "Read", "input_summary": "src/foo.py"},
        {"agent": "implementer", "tool": "Read", "input_summary": "src/bar.py"},
        {"agent": "implementer", "tool": "Bash", "input_summary": "pytest tests/"},
        {"agent": None, "tool": "Edit", "input_summary": "src/baz.py"},
    ]
    table = build_usage_table(rows, known_agents)

    for agent, entry in table.items():
        for tool_name, tool_entry in entry["tools"].items():
            if tool_entry["count"] > 0:
                assert tool_entry["example"] is not None
                assert tool_entry["example"] != ""
                assert tool_entry["truncated"] is True


def test_example_is_verbatim_substring_of_a_real_row_not_paraphrased():
    known_agents = ["implementer"]
    rows = [
        {"agent": "implementer", "tool": "Read", "input_summary": "src/foo.py"},
        {"agent": "implementer", "tool": "Read", "input_summary": "src/bar.py"},
        {"agent": None, "tool": "Bash", "input_summary": "pytest tests/tools -v"},
    ]
    table = build_usage_table(rows, known_agents)

    real_summaries = {r["input_summary"] for r in rows}
    for agent, entry in table.items():
        for tool_name, tool_entry in entry["tools"].items():
            if tool_entry["example"] is not None:
                assert tool_entry["example"] in real_summaries


# ---------------------------------------------------------------------------
# AC4 — read-only against agent-monitoring/data/
# ---------------------------------------------------------------------------

def _file_size_snapshot() -> dict:
    """{path: size_in_bytes} for every real file under agent-monitoring/, recursively."""
    return {
        str(p): p.stat().st_size
        for p in _REAL_AGENT_MONITORING_DIR.rglob("*")
        if p.is_file()
    }


def test_script_is_read_only_against_real_agent_monitoring_data():
    """TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS item 3: the original version of this test
    compared a full `git status --porcelain -- agent-monitoring/` snapshot before and after a
    single load_all_tool_rows() + build_report() call, asserting byte-for-byte identity. That is
    NOT the same race as the sibling test above (there is only one read of the corpus here, not
    two) -- it is vulnerable to a DIFFERENT failure mode: any OTHER concurrent session's own
    PostToolUse hook appending a tools.jsonl row during this test's own wall-clock window makes
    `git status` differ for reasons entirely unrelated to this script's own execution, and the
    test would misattribute that external write as evidence this script is not read-only.

    The property this test actually needs to prove is narrower than "the working tree never
    changes at all" (which races legitimate concurrent activity in a shared, multi-session repo)
    -- it is "this script never truncates, deletes, or otherwise destroys existing content in
    agent-monitoring/". A concurrent session's own hook can only ever APPEND to a shard file
    (grow it) or add a brand-new shard/week file; it can never make an existing file smaller or
    make it disappear. So: assert no existing file shrinks or is deleted, and don't assert
    anything about growth or new files, since those are expected, benign, and not attributable to
    this script.
    """
    assert _REAL_AGENT_MONITORING_DIR.is_dir()
    assert "tmp" not in str(_REAL_AGENT_MONITORING_DIR).lower()

    pre_sizes = _file_size_snapshot()

    rows = load_all_tool_rows()
    build_report(rows)

    post_sizes = _file_size_snapshot()

    deleted = set(pre_sizes) - set(post_sizes)
    assert not deleted, (
        f"agent_tool_usage_baseline appears to have deleted real files: {sorted(deleted)}"
    )
    shrunk = {
        path: (pre_sizes[path], post_sizes[path])
        for path in pre_sizes
        if path in post_sizes and post_sizes[path] < pre_sizes[path]
    }
    assert not shrunk, (
        f"agent_tool_usage_baseline appears to have truncated real files: {shrunk}"
    )


def test_cli_runs_against_real_corpus_and_prints_valid_json_or_table():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH)], cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    report = json.loads(result.stdout)
    assert report["ticket_id"] == "TCK-20260904-AGENT-TOOL-USAGE-BASELINE"

    live_expected = sorted(p.stem for p in _AGENTS_DIR.glob("*.md"))
    assert set(report["agents"].keys()) == set(live_expected) | {UNATTRIBUTED}
    assert report["total_rows_seen"] == report["total_rows_across_all_agent_rows"]

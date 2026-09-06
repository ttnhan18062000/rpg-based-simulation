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
    registered_agents,
)

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
    real_total = sum(
        1
        for shard in (_REAL_AGENT_MONITORING_DIR / "data").glob("*/tools.jsonl")
        for line in shard.read_text().splitlines()
        if line.strip()
    )

    rows = load_all_tool_rows()
    report = build_report(rows)

    assert report["total_rows_seen"] == real_total
    assert report["total_rows_across_all_agent_rows"] == real_total


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

def _porcelain_snapshot() -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    return result.stdout


def test_script_is_read_only_against_real_agent_monitoring_data():
    assert _REAL_AGENT_MONITORING_DIR.is_dir()
    assert "tmp" not in str(_REAL_AGENT_MONITORING_DIR).lower()

    pre_porcelain = _porcelain_snapshot()

    rows = load_all_tool_rows()
    build_report(rows)

    post_porcelain = _porcelain_snapshot()
    assert pre_porcelain == post_porcelain, (
        "agent_tool_usage_baseline mutated agent-monitoring/: "
        f"pre={pre_porcelain!r} post={post_porcelain!r}"
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

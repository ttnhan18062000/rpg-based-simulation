"""Tests for tools/agent-monitoring/skill_usage_metric.py
(TCK-20260805-SKILL-USAGE-METRIC).

Mirrors tests/tools/test_retrieval_baseline_metrics.py's design: synthetic-fixture unit tests for
the counting logic itself, plus an integration test against the REAL agent-monitoring/ corpus —
never a tmp_path copy for the live-corpus assertion, which would make it vacuous. The live-corpus
test independently re-derives counts via its own separate regex pass (not by calling the function
under test twice) so it can catch a real bug in the function, not just confirm self-agreement.
"""
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_MODULE_PATH = _MONITORING_TOOLS_DIR / "skill_usage_metric.py"
_REAL_AGENT_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"
# Post-TCK-20260903-MONITORING-DATA-MIGRATION unified weekly layout: real tools.jsonl shards live
# under agent-monitoring/data/<ISO-week>/tools.jsonl, not the legacy agent-monitoring/tools/
# tools-*.jsonl path (that directory no longer exists).
_REAL_DATA_DIR = _REAL_AGENT_MONITORING_DIR / "data"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from skill_usage_metric import build_skill_usage_section  # noqa: E402

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
# Reuse-not-reimplement guard
# ---------------------------------------------------------------------------

def test_reuses_generate_retro_loader_not_a_second_loader():
    imported = _imported_names()
    # DEFAULT_TOOLS_FILE is directory-valued (TCK-20260903-MONITORING-DATA-CONSUMERS-CORE), so
    # this module reuses generate_retro.py's multi-week-aware load_data_glob() rather than the
    # literal-file-only load_jsonl() (TCK-20260904-HOTFIX-RETRIEVAL-TOOLS-CONSUMERS-DEAD-
    # CONSTANTS — a bare load_jsonl(DEFAULT_TOOLS_FILE) raises IsADirectoryError).
    assert "load_data_glob" in imported
    assert "DEFAULT_TOOLS_FILE" in imported


def test_never_calls_json_loads_on_input_summary():
    """input_summary is a Python dict-repr string, not JSON — json.loads() on it raises
    json.JSONDecodeError. AST guard: no json.loads(...) call exists anywhere in this module
    (the module's own docstring/comments legitimately mention the string "json.loads" in prose
    explaining why it's NOT used — a substring check would false-positive on that)."""
    for node in ast.walk(_MODULE_AST):
        if isinstance(node, ast.Call):
            func = node.func
            is_json_loads = (
                isinstance(func, ast.Attribute)
                and func.attr == "loads"
                and isinstance(func.value, ast.Name)
                and func.value.id == "json"
            )
            assert not is_json_loads, "json.loads(...) call found — must use regex extraction instead"


def test_does_not_import_generate_retro_tag_breakdown_internals():
    imported = _imported_names()
    assert "compute_retro_metrics" not in imported
    assert "tag_breakdown_skill" not in imported


# ---------------------------------------------------------------------------
# Synthetic-fixture unit tests
# ---------------------------------------------------------------------------

def test_counts_skill_invocations_by_name():
    tools = [
        {"tool": "Skill", "run_id": "TCK-A", "input_summary": "{'skill': 'graphify', 'args': None}"},
        {"tool": "Skill", "run_id": "TCK-A", "input_summary": "{'skill': 'graphify', 'args': None}"},
        {"tool": "Skill", "run_id": "TCK-B", "input_summary": "{'skill': 'implement-ticket', 'args': None}"},
        {"tool": "Bash", "run_id": "TCK-A", "input_summary": "{'command': 'ls'}"},
    ]
    report = build_skill_usage_section(tools)
    assert report["per_skill"] == {"graphify": 2, "implement-ticket": 1}
    assert report["total_skill_invocations"] == 3
    assert report["unparseable"] == 0


def test_none_run_id_buckets_under_unattributed():
    tools = [{"tool": "Skill", "run_id": None, "input_summary": "{'skill': 'graphify'}"}]
    report = build_skill_usage_section(tools)
    assert report["per_skill_per_run"]["graphify"] == {"unattributed": 1}


def test_missing_run_id_key_also_buckets_under_unattributed():
    tools = [{"tool": "Skill", "input_summary": "{'skill': 'graphify'}"}]
    report = build_skill_usage_section(tools)
    assert report["per_skill_per_run"]["graphify"] == {"unattributed": 1}


def test_unparseable_input_summary_counted_not_dropped_not_crashed():
    tools = [
        {"tool": "Skill", "run_id": "TCK-A", "input_summary": "not a dict repr at all"},
        {"tool": "Skill", "run_id": "TCK-A", "input_summary": "{'other_key': 'value'}"},
    ]
    report = build_skill_usage_section(tools)
    assert report["unparseable"] == 2
    assert report["total_skill_invocations"] == 2
    assert report["per_skill"] == {}


def test_empty_input_produces_empty_report_not_error():
    report = build_skill_usage_section([])
    assert report["total_skill_invocations"] == 0
    assert report["unparseable"] == 0
    assert report["per_skill"] == {}


def test_derivation_string_present_and_non_fabricated():
    report = build_skill_usage_section([])
    assert "derivation" in report
    assert "json.loads" in report["derivation"]  # documents why it's NOT used


# ---------------------------------------------------------------------------
# Live-corpus integration test — independent re-derivation, not a stale fixture
# ---------------------------------------------------------------------------

def _independently_derive_counts() -> dict:
    """A deliberately separate implementation of the same extraction, so this test can catch a
    real bug in build_skill_usage_section rather than just confirming it agrees with itself."""
    counts: dict = {}
    pattern = re.compile(r"'skill':\s*'([^']*)'")
    for shard in sorted(_REAL_DATA_DIR.glob("*/tools.jsonl")):
        with open(shard, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("tool") != "Skill":
                    continue
                m = pattern.search(rec.get("input_summary", ""))
                if m:
                    counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    return counts


def test_live_corpus_matches_independently_derived_counts():
    from generate_retro import DEFAULT_TOOLS_FILE, load_data_glob
    tools = load_data_glob(DEFAULT_TOOLS_FILE, "tools")
    report = build_skill_usage_section(tools)
    expected = _independently_derive_counts()
    assert report["per_skill"] == expected
    # Correct-data assertion, not just "doesn't crash": the real corpus spans multiple
    # agent-monitoring/data/<ISO-week>/ shards, so a nonzero count here proves the full
    # multi-week corpus was actually read, not silently truncated to one shard.
    assert report["total_skill_invocations"] > 0


def test_cli_runs_against_real_corpus_and_prints_json():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH)], cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    report = json.loads(result.stdout)
    assert set(report.keys()) == {
        "total_skill_invocations", "unparseable", "per_skill", "per_skill_per_run", "derivation",
    }


def test_causes_zero_diff_on_real_corpus():
    from generate_retro import DEFAULT_TOOLS_FILE, load_data_glob

    def _porcelain():
        return subprocess.run(
            ["git", "status", "--porcelain", "--", "agent-monitoring/"],
            cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
        ).stdout

    pre = _porcelain()
    tools = load_data_glob(DEFAULT_TOOLS_FILE, "tools")
    build_skill_usage_section(tools)
    post = _porcelain()
    assert pre == post, f"skill_usage_metric mutated agent-monitoring/: pre={pre!r} post={post!r}"


# ---------------------------------------------------------------------------
# TCK-20260904-HOTFIX-RETRIEVAL-TOOLS-CONSUMERS-DEAD-CONSTANTS — dedicated cross-week fixture,
# proving main()'s tool-loading correctly aggregates multiple ISO-week folders (not just that the
# real corpus happens to work).
# ---------------------------------------------------------------------------

def test_load_data_glob_reads_across_multiple_week_folders(tmp_path):
    from generate_retro import load_data_glob

    data_dir = tmp_path / "agent-monitoring" / "data"
    (data_dir / "2026-W01").mkdir(parents=True)
    (data_dir / "2026-W02").mkdir(parents=True)
    (data_dir / "2026-W01" / "tools.jsonl").write_text(
        json.dumps({"tool": "Skill", "run_id": "TCK-A", "input_summary": "{'skill': 'graphify'}"}) + "\n"
    )
    (data_dir / "2026-W02" / "tools.jsonl").write_text(
        json.dumps(
            {"tool": "Skill", "run_id": "TCK-B", "input_summary": "{'skill': 'implement-ticket'}"}
        )
        + "\n"
    )

    tools = load_data_glob(data_dir, "tools")
    report = build_skill_usage_section(tools)
    assert report["total_skill_invocations"] == 2
    assert report["per_skill"] == {"graphify": 1, "implement-ticket": 1}

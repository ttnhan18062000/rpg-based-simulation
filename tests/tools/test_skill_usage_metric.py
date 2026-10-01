"""Tests for tools/agent-monitoring/skill_usage_metric.py
(TCK-20260805-SKILL-USAGE-METRIC).

Mirrors tests/tools/test_retrieval_baseline_metrics.py's design: synthetic-fixture unit tests for
the counting logic itself, plus a frozen-fixture corpus test with literal expected counts (so the result never depends on
which shards a branch carries), and smoke tests against the REAL agent-monitoring/ corpus.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_MODULE_PATH = _MONITORING_TOOLS_DIR / "skill_usage_metric.py"
_REAL_AGENT_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"

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
# Frozen-fixture corpus test (TCK-20260930-SKILL-USAGE-METRIC-LIVE-CORPUS-TEST-FROZEN-FIXTURE).
# The previous version counted Skill rows in the live agent-monitoring/data/ shards, so any branch
# that carried its own shard with a Skill row changed the expected count. The fixture below is a
# hand-written tree covering both shard shapes; the expected counts are literals, not derived from
# the production glob, so file discovery is checked independently of the code under test.
# ---------------------------------------------------------------------------

def _write_shard(path: Path, skills: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [{"tool": "Bash", "run_id": "TCK-X", "input_summary": "{'command': 'ls'}"}]
    rows += [
        {"tool": "Skill", "run_id": "TCK-X", "input_summary": f"{{'skill': '{name}', 'args': None}}"}
        for name in skills
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


@pytest.fixture
def frozen_corpus(tmp_path):
    data_dir = tmp_path / "agent-monitoring" / "data"
    _write_shard(data_dir / "2026-W01" / "tools.jsonl", ["graphify", "graphify"])  # bare canonical shape
    _write_shard(data_dir / "2026-W01" / "some-branch.tools.jsonl", ["implement-ticket"])  # per-branch shape
    _write_shard(data_dir / "2026-W02" / "tools.jsonl", ["graphify"])
    _write_shard(data_dir / "2026-W02" / "other-branch.tools.jsonl", ["create-tickets", "graphify"])
    return data_dir


def test_frozen_corpus_counts_both_shard_shapes(frozen_corpus):
    from generate_retro import load_data_glob
    report = build_skill_usage_section(load_data_glob(frozen_corpus, "tools"))
    # Literal oracle: 2 bare W01 + 1 branch W01 + 1 bare W02 + 2 branch W02. A loader that drops
    # either shard shape produces a different total.
    assert report["per_skill"] == {"graphify": 4, "implement-ticket": 1, "create-tickets": 1}
    assert report["total_skill_invocations"] == 6
    assert report["unparseable"] == 0


def test_frozen_corpus_result_ignores_live_shards(frozen_corpus, tmp_path):
    from generate_retro import load_data_glob
    before = build_skill_usage_section(load_data_glob(frozen_corpus, "tools"))
    # A new shard elsewhere (a different data dir) must not change the fixture's result.
    _write_shard(tmp_path / "elsewhere" / "2026-W03" / "x.tools.jsonl", ["graphify"])
    after = build_skill_usage_section(load_data_glob(frozen_corpus, "tools"))
    assert before == after


def test_live_corpus_loads_nonempty():
    # Smoke only: the real multi-week corpus is readable and has Skill rows. No count is pinned,
    # because the count legitimately changes with every branch that carries its own shard.
    from generate_retro import DEFAULT_TOOLS_FILE, load_data_glob
    report = build_skill_usage_section(load_data_glob(DEFAULT_TOOLS_FILE, "tools"))
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

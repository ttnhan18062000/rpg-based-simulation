"""Tests for tools/pr_impact_report.py
(TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR).

Mirrors tests/tools/test_code_health_impact.py's fixture-graph/injected-
affected_runner/_requires_graphify conventions — every test below uses a
fixture graph.json-shaped dict and an injected affected_runner unless it is
the one @_requires_graphify-marked Makefile end-to-end test.
"""

import inspect
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import code_health_impact as chi  # noqa: E402
import pr_impact_report as pir  # noqa: E402

_REPO_ROOT = Path(__file__).parent.parent.parent

_GRAPHIFY_AVAILABLE = shutil.which("graphify") is not None and (
    _REPO_ROOT / "graphify-out" / "graph.json"
).exists()
_requires_graphify = pytest.mark.skipif(
    not _GRAPHIFY_AVAILABLE,
    reason="graphify CLI and/or graphify-out/graph.json not available in this environment",
)


# ---------------------------------------------------------------------------
# Fixture graph.json-shaped data (mirrors test_code_health_impact.py's own)
# ---------------------------------------------------------------------------


def _make_graph(nodes, links):
    return {"nodes": nodes, "links": links}


def _fake_graph_two_symbols():
    nodes = [
        {"id": "foo_bar", "label": "bar.py", "file_type": "code",
         "source_file": "src/foo/bar.py", "source_location": "L1"},
        {"id": "foo_bar_widget", "label": "Widget", "file_type": "code",
         "source_file": "src/foo/bar.py", "source_location": "L10"},
        {"id": "foo_bar_helper", "label": "helper()", "file_type": "code",
         "source_file": "src/foo/bar.py", "source_location": "L40"},
        {"id": "other_consumer", "label": "consumer.py", "file_type": "code",
         "source_file": "src/foo/consumer.py", "source_location": "L1"},
    ]
    links = [
        {"source": "foo_bar", "target": "foo_bar_widget", "relation": "contains"},
        {"source": "foo_bar", "target": "foo_bar_helper", "relation": "contains"},
    ]
    return _make_graph(nodes, links)


def _resolved_affected_runner(symbol, depth, graph_path):
    if symbol == "Widget":
        return "Affected nodes for Widget\n- consumer.py [imports] src/foo/consumer.py:L1\n"
    if symbol == "helper()":
        return "Affected nodes for helper()\n- other.py [calls] src/foo/other.py:L1\n"
    raise AssertionError(f"unexpected symbol {symbol}")


def _degraded_no_match_affected_runner(symbol, depth, graph_path):
    return f"No unique node match for {symbol}\n"


# ---------------------------------------------------------------------------
# 1. build_pr_impact_report — batching / failure isolation
# ---------------------------------------------------------------------------


def test_multi_path_batch_report_includes_all_requested_paths():
    graph = _fake_graph_two_symbols()
    report = pir.build_pr_impact_report(
        _REPO_ROOT,
        ["src/foo/bar.py", "src/foo/consumer.py"],
        graph=graph,
        registry_entries=[],
        affected_runner=_resolved_affected_runner,
    )
    assert report["target_paths"] == ["src/foo/bar.py", "src/foo/consumer.py"]
    assert [e["target_path"] for e in report["entries"]] == ["src/foo/bar.py", "src/foo/consumer.py"]
    assert all(e["status"] == "ok" for e in report["entries"])


def test_one_degraded_or_failing_path_does_not_abort_the_whole_batch():
    graph = _fake_graph_two_symbols()

    def raising_runner(symbol, depth, graph_path):
        raise RuntimeError("boom")

    report = pir.build_pr_impact_report(
        _REPO_ROOT,
        ["src/foo/bar.py", "src/foo/consumer.py"],
        graph=graph,
        registry_entries=[],
        affected_runner=raising_runner,
    )
    entries_by_path = {e["target_path"]: e for e in report["entries"]}
    assert entries_by_path["src/foo/bar.py"]["status"] == "failed"
    assert entries_by_path["src/foo/bar.py"]["report"] is None
    assert "boom" in entries_by_path["src/foo/bar.py"]["error"]
    # consumer.py has zero symbols -> find_dependents never calls affected_runner,
    # so it must succeed even though bar.py's runner raises.
    assert entries_by_path["src/foo/consumer.py"]["status"] == "ok"
    assert entries_by_path["src/foo/consumer.py"]["report"]["dependents_degraded"] is True

    # Separately: a degraded-but-successful path must also not abort the batch.
    degraded_report = pir.build_pr_impact_report(
        _REPO_ROOT,
        ["src/foo/bar.py", "src/foo/consumer.py"],
        graph=graph,
        registry_entries=[],
        affected_runner=_degraded_no_match_affected_runner,
    )
    degraded_entries = {e["target_path"]: e for e in degraded_report["entries"]}
    assert degraded_entries["src/foo/bar.py"]["status"] == "ok"
    assert degraded_entries["src/foo/bar.py"]["report"]["dependents_degraded"] is True
    assert degraded_entries["src/foo/consumer.py"]["status"] == "ok"


def test_report_generator_does_not_reimplement_impact_computation():
    graph = _fake_graph_two_symbols()
    report = pir.build_pr_impact_report(
        _REPO_ROOT,
        ["src/foo/bar.py"],
        graph=graph,
        registry_entries=[],
        affected_runner=_resolved_affected_runner,
    )
    directly_computed = chi.build_impact_report(
        _REPO_ROOT,
        "src/foo/bar.py",
        graph=graph,
        registry_entries=[],
        affected_runner=_resolved_affected_runner,
    )
    assert report["entries"][0]["report"] == directly_computed


# ---------------------------------------------------------------------------
# 2. format_pr_impact_report — all 13 fields, degradation conditional
# ---------------------------------------------------------------------------


def test_report_generator_renders_all_13_real_fields_from_build_impact_report():
    graph = _fake_graph_two_symbols()
    report = pir.build_pr_impact_report(
        _REPO_ROOT,
        ["src/foo/bar.py"],
        graph=graph,
        registry_entries=[],
        affected_runner=_resolved_affected_runner,
    )
    formatted = pir.format_pr_impact_report(report)
    item = report["entries"][0]["report"]
    expected_keys = {
        "target_path", "subsystem", "dependents", "dependents_degraded",
        "dependents_degradation_reason", "resolved_symbols", "unresolved_symbols",
        "required_tests", "required_tests_registry_hit_count", "architecture_rules",
        "churn_lines_changed", "edge_degree", "criticality_tier",
    }
    assert set(item.keys()) == expected_keys

    assert item["target_path"] in formatted
    assert item["subsystem"] in formatted
    assert "src/foo/consumer.py" in formatted  # resolved dependent
    assert "False" in formatted  # dependents_degraded
    assert "Widget" in formatted  # resolved_symbols
    assert str(item["required_tests_registry_hit_count"]) in formatted
    assert str(item["edge_degree"]) in formatted
    assert item["criticality_tier"] in formatted


def test_report_preserves_dependents_degraded_and_reason_verbatim():
    graph = _fake_graph_two_symbols()
    report = pir.build_pr_impact_report(
        _REPO_ROOT,
        ["src/foo/consumer.py"],  # zero-symbols degradation path
        graph=graph,
        registry_entries=[],
        affected_runner=lambda *a: (_ for _ in ()).throw(AssertionError("must not be called")),
    )
    item = report["entries"][0]["report"]
    assert item["dependents_degraded"] is True
    assert item["dependents_degradation_reason"] is not None

    formatted = pir.format_pr_impact_report(report)
    assert "True" in formatted
    assert item["dependents_degradation_reason"] in formatted


def test_report_preserves_unresolved_symbols_list_verbatim():
    graph = _fake_graph_two_symbols()

    def partial_runner(symbol, depth, graph_path):
        if symbol == "Widget":
            return "No unique node match for Widget\n"
        return "Affected nodes for helper()\n- other.py [calls] src/foo/other.py:L1\n"

    report = pir.build_pr_impact_report(
        _REPO_ROOT,
        ["src/foo/bar.py"],
        graph=graph,
        registry_entries=[],
        affected_runner=partial_runner,
    )
    item = report["entries"][0]["report"]
    assert item["dependents_degraded"] is False
    assert item["unresolved_symbols"] == ["Widget"]

    formatted = pir.format_pr_impact_report(report)
    assert "Widget" in formatted


def test_report_does_not_silently_drop_degradation_fields_when_absent():
    graph = _fake_graph_two_symbols()
    report = pir.build_pr_impact_report(
        _REPO_ROOT,
        ["src/foo/bar.py"],
        graph=graph,
        registry_entries=[],
        affected_runner=_resolved_affected_runner,
    )
    item = report["entries"][0]["report"]
    assert item["dependents_degraded"] is False
    assert item["dependents_degradation_reason"] is None
    assert item["unresolved_symbols"] == []

    formatted = pir.format_pr_impact_report(report)
    assert "None" not in formatted
    assert "null" not in formatted


def test_report_includes_discovery_triage_aid_framing_verbatim():
    graph = _fake_graph_two_symbols()
    report = pir.build_pr_impact_report(
        _REPO_ROOT,
        ["src/foo/bar.py"],
        graph=graph,
        registry_entries=[],
        affected_runner=_resolved_affected_runner,
    )
    assert report["framing_note"] == pir.FRAMING_NOTE
    formatted = pir.format_pr_impact_report(report)
    assert pir.FRAMING_NOTE in formatted

    round_tripped = json.loads(json.dumps(report))
    assert round_tripped["framing_note"] == pir.FRAMING_NOTE


def test_report_generator_output_is_well_formed_markdown_when_markdown_mode_requested():
    graph = _fake_graph_two_symbols()
    report = pir.build_pr_impact_report(
        _REPO_ROOT,
        ["src/foo/bar.py", "src/foo/consumer.py"],
        graph=graph,
        registry_entries=[],
        affected_runner=_resolved_affected_runner,
    )
    formatted = pir.format_pr_impact_report(report)
    assert "## src/foo/bar.py" in formatted
    assert "## src/foo/consumer.py" in formatted
    assert isinstance(formatted, str)


# ---------------------------------------------------------------------------
# 3. JSON mode / no-aggregate-score guard
# ---------------------------------------------------------------------------


def test_report_generator_output_is_valid_json_when_json_mode_requested():
    graph = _fake_graph_two_symbols()
    report = pir.build_pr_impact_report(
        _REPO_ROOT,
        ["src/foo/bar.py"],
        graph=graph,
        registry_entries=[],
        affected_runner=_resolved_affected_runner,
    )
    round_tripped = json.loads(json.dumps(report))
    assert round_tripped == report


def _collect_keys(obj, collected):
    if isinstance(obj, dict):
        for key, value in obj.items():
            collected.add(key)
            _collect_keys(value, collected)
    elif isinstance(obj, list):
        for value in obj:
            _collect_keys(value, collected)


def test_report_output_has_no_aggregate_or_combined_score_field():
    graph = _fake_graph_two_symbols()
    report = pir.build_pr_impact_report(
        _REPO_ROOT,
        ["src/foo/bar.py"],
        graph=graph,
        registry_entries=[],
        affected_runner=_resolved_affected_runner,
    )
    all_keys = set()
    _collect_keys(report, all_keys)
    denylist_substrings = ("score", "overall", "combined", "summary", "health_score")
    for key in all_keys:
        lowered = key.lower()
        for banned in denylist_substrings:
            assert banned not in lowered, f"key {key!r} matches denylisted substring {banned!r}"

    formatted = pir.format_pr_impact_report(report)
    for banned in denylist_substrings:
        assert banned not in formatted.lower()


# ---------------------------------------------------------------------------
# 4. Architecture guard — no import of codebase_health_snapshot
# ---------------------------------------------------------------------------


def test_report_generator_has_no_import_of_codebase_health_snapshot_module():
    source = (_TOOLS_DIR / "pr_impact_report.py").read_text(encoding="utf-8")
    assert "import codebase_health_snapshot" not in source
    assert "from codebase_health_snapshot" not in source


# ---------------------------------------------------------------------------
# 5. CLI
# ---------------------------------------------------------------------------


def test_cli_accepts_multiple_target_paths(monkeypatch, capsys):
    graph = _fake_graph_two_symbols()

    def fake_build_pr_impact_report(repo_root, target_paths, **kwargs):
        return {
            "target_paths": list(target_paths),
            "entries": [
                {"target_path": p, "status": "ok",
                 "report": chi.build_impact_report(
                     repo_root, p, graph=graph, registry_entries=[],
                     affected_runner=_resolved_affected_runner,
                 ), "error": None}
                for p in target_paths
            ],
            "framing_note": pir.FRAMING_NOTE,
        }

    monkeypatch.setattr(pir, "build_pr_impact_report", fake_build_pr_impact_report)
    exit_code = pir.main(["src/foo/bar.py", "src/foo/consumer.py"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "src/foo/bar.py" in captured.out
    assert "src/foo/consumer.py" in captured.out


# ---------------------------------------------------------------------------
# 6. Makefile end-to-end (real repo, real graphify)
# ---------------------------------------------------------------------------


@_requires_graphify
def test_make_target_runs_successfully_against_real_repo():
    result = subprocess.run(
        ["make", "codebase-health-pr-impact", "ARGS=src/observability/reporter.py"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "src/observability/reporter.py" in result.stdout
    assert "criticality_tier" in result.stdout

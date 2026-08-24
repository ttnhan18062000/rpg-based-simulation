"""Tests for tools/code_health_impact.py
(TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND).

Coverage-honesty requirement (matches this repo's established convention, e.g.
tests/tools/test_codebase_health_baseline.py's own docstring): every check the
tool claims to compute has at least one fixture proving it computes correctly,
not just that it runs without error.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import code_health_impact as chi  # noqa: E402
import codebase_health_baseline as chb  # noqa: E402

_REPO_ROOT = Path(__file__).parent.parent.parent

# graphify (the CLI binary, not just graphify-out/graph.json) is a locally-installed
# dev tool -- confirmed absent from requirements.txt/pyproject.toml/any CI workflow,
# and graphify-out/ is entirely gitignored (never committed). The 4 real-path tests
# below invoke the real `graphify affected` subprocess against the real graph.json,
# both of which are only present in an environment that has separately run
# `graphify update .` -- not a fresh CI checkout. This mirrors the existing skip
# pattern for `tools/search_mcp.py`'s tests (skipped when the knowledge index isn't
# built) rather than requiring graphify as a new CI dependency for what is,
# by design, an on-demand-only developer/agent tool.
_GRAPHIFY_AVAILABLE = shutil.which("graphify") is not None and (
    _REPO_ROOT / "graphify-out" / "graph.json"
).exists()
_requires_graphify = pytest.mark.skipif(
    not _GRAPHIFY_AVAILABLE,
    reason="graphify CLI and/or graphify-out/graph.json not available in this environment",
)


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _init_repo(tmp_path):
    _git(["init", "-q"], tmp_path)
    _git(["config", "user.email", "test@example.com"], tmp_path)
    _git(["config", "user.name", "Test"], tmp_path)


def _commit(tmp_path, message):
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", message], tmp_path)


# ---------------------------------------------------------------------------
# Fixture graph.json-shaped data
# ---------------------------------------------------------------------------


def _make_graph(nodes, links):
    return {"nodes": nodes, "links": links}


def _fake_graph_two_symbols():
    """One file (src/foo/bar.py) that `contains` two symbols: a class and a
    free function — mirrors the real state.py/dirty.py shape confirmed live
    (multiple symbols directly `contains`-linked from one file node)."""
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


# ---------------------------------------------------------------------------
# 1. Path -> symbol-node resolution
# ---------------------------------------------------------------------------


def test_find_file_node_resolves_by_source_file_and_basename():
    graph = _fake_graph_two_symbols()
    node = chi.find_file_node(graph, "src/foo/bar.py")
    assert node is not None
    assert node["id"] == "foo_bar"


def test_find_file_node_returns_none_for_unindexed_path():
    graph = _fake_graph_two_symbols()
    assert chi.find_file_node(graph, "src/nowhere/missing.py") is None


def test_resolve_defined_symbols_finds_both_contained_symbols():
    graph = _fake_graph_two_symbols()
    file_node = chi.find_file_node(graph, "src/foo/bar.py")
    symbols = chi.resolve_defined_symbols(graph, file_node)
    assert set(symbols) == {"Widget", "helper()"}


def test_resolve_defined_symbols_ignores_other_files_contains_edges():
    graph = _fake_graph_two_symbols()
    file_node = chi.find_file_node(graph, "src/foo/consumer.py")
    # consumer.py node has no outgoing `contains` edges in this fixture.
    assert chi.resolve_defined_symbols(graph, file_node) == []


# ---------------------------------------------------------------------------
# 2. Multi-symbol aggregation / dedup
# ---------------------------------------------------------------------------


def test_find_dependents_aggregates_and_dedupes_across_symbols():
    graph = _fake_graph_two_symbols()

    def fake_affected_runner(symbol, depth, graph_path):
        if symbol == "Widget":
            return (
                "Affected nodes for Widget\n"
                "- consumer.py [imports] src/foo/consumer.py:L1\n"
                "- other.py [imports] src/foo/other.py:L1\n"
            )
        if symbol == "helper()":
            # Overlaps with Widget's consumer.py — must not double-count.
            return (
                "Affected nodes for helper()\n"
                "- consumer.py [calls] src/foo/consumer.py:L5\n"
                "- third.py [imports] src/foo/third.py:L1\n"
            )
        raise AssertionError(f"unexpected symbol {symbol}")

    result = chi.find_dependents(
        graph, "src/foo/bar.py", affected_runner=fake_affected_runner
    )

    assert result["dependents"] == {
        "src/foo/consumer.py", "src/foo/other.py", "src/foo/third.py",
    }
    assert result["degraded"] is False
    assert result["unresolved_symbols"] == []


def test_find_dependents_excludes_target_path_itself():
    graph = _fake_graph_two_symbols()

    def fake_affected_runner(symbol, depth, graph_path):
        return "Affected nodes for X\n- bar.py [calls] src/foo/bar.py:L20\n"

    result = chi.find_dependents(
        graph, "src/foo/bar.py", affected_runner=fake_affected_runner
    )
    assert "src/foo/bar.py" not in result["dependents"]


# ---------------------------------------------------------------------------
# 3. Zero-resolvable-symbols / no-unique-match degradation
# ---------------------------------------------------------------------------


def test_find_dependents_degrades_gracefully_for_zero_symbol_file():
    graph = _fake_graph_two_symbols()

    def fake_affected_runner(symbol, depth, graph_path):
        raise AssertionError("must not call affected when there are no symbols")

    result = chi.find_dependents(
        graph, "src/foo/consumer.py", affected_runner=fake_affected_runner
    )

    assert result["dependents"] == set()
    assert result["degraded"] is True
    assert result["degradation_reason"] is not None
    assert "src/foo/consumer.py" in result["degradation_reason"]


def test_find_dependents_degrades_gracefully_for_no_unique_node_match():
    graph = _fake_graph_two_symbols()

    def fake_affected_runner(symbol, depth, graph_path):
        return f"No unique node match for {symbol}\n"

    result = chi.find_dependents(
        graph, "src/foo/bar.py", affected_runner=fake_affected_runner
    )

    assert result["dependents"] == set()
    assert result["degraded"] is True
    assert set(result["unresolved_symbols"]) == {"Widget", "helper()"}


def test_find_dependents_not_degraded_when_only_some_symbols_ambiguous():
    graph = _fake_graph_two_symbols()

    def fake_affected_runner(symbol, depth, graph_path):
        if symbol == "Widget":
            return "No unique node match for Widget\n"
        return "Affected nodes for helper()\n- other.py [calls] src/foo/other.py:L1\n"

    result = chi.find_dependents(
        graph, "src/foo/bar.py", affected_runner=fake_affected_runner
    )

    assert result["degraded"] is False
    assert result["unresolved_symbols"] == ["Widget"]
    assert result["dependents"] == {"src/foo/other.py"}


def test_parse_affected_output_ignores_non_matching_lines():
    output = (
        "Affected nodes for X\n"
        "Relations: calls, uses\n"
        "Depth: 2\n"
        "- Foo [calls] src/a/b.py:L12\n"
    )
    assert chi.parse_affected_output(output) == {"src/a/b.py"}


# ---------------------------------------------------------------------------
# 4. Mixed-shape related_code_areas resolution
# ---------------------------------------------------------------------------


def test_registry_bare_symbol_name_resolves_via_label_index():
    graph = _fake_graph_two_symbols()
    label_index = chi.build_label_index(graph)
    basename_index = chi.build_basename_index(graph)

    # Bare symbol name, not a path — the real-world shape investigation.md
    # found in ~47% of non-empty related_code_areas entries.
    resolved = chi.resolve_registry_value_paths("Widget", label_index, basename_index)
    assert resolved == {"src/foo/bar.py"}


def test_registry_entry_matches_target_via_bare_symbol():
    graph = _fake_graph_two_symbols()
    label_index = chi.build_label_index(graph)
    basename_index = chi.build_basename_index(graph)

    matches = chi.registry_entry_matches_target(
        ["Widget", "tests/unit/foo/test_bar.py"], "src/foo/bar.py", label_index, basename_index
    )
    assert matches is True


def test_required_tests_from_registry_collects_test_paths_from_matching_entries():
    graph = _fake_graph_two_symbols()
    label_index = chi.build_label_index(graph)
    basename_index = chi.build_basename_index(graph)

    registry_entries = [
        {"path": "tickets/done/TCK-EXAMPLE.md",
         "related_code_areas": ["Widget", "tests/unit/foo/test_bar.py"]},
        {"path": "tickets/done/TCK-UNRELATED.md",
         "related_code_areas": ["src/somewhere/else.py", "tests/unit/else/test_else.py"]},
    ]

    required_tests = chi.required_tests_from_registry(
        registry_entries, "src/foo/bar.py", label_index, basename_index
    )
    assert required_tests == {"tests/unit/foo/test_bar.py"}


def test_required_tests_from_registry_resolves_bare_filename_via_basename_index():
    graph = _fake_graph_two_symbols()
    label_index = chi.build_label_index(graph)
    basename_index = chi.build_basename_index(graph)

    # Bare filename (no directory), the other confirmed real shape.
    registry_entries = [
        {"path": "tickets/done/TCK-EXAMPLE-2.md",
         "related_code_areas": ["bar.py", "tests/unit/foo/test_bar_alt.py"]},
    ]

    required_tests = chi.required_tests_from_registry(
        registry_entries, "src/foo/bar.py", label_index, basename_index
    )
    assert required_tests == {"tests/unit/foo/test_bar_alt.py"}


def test_normalize_registry_value_strips_symbol_and_line_suffixes():
    assert chi.normalize_registry_value("src/foo/bar.py::Widget.method()") == "src/foo/bar.py"
    assert chi.normalize_registry_value("src/foo/bar.py:120-140") == "src/foo/bar.py"
    assert chi.normalize_registry_value("src/foo/bar.py") == "src/foo/bar.py"


# ---------------------------------------------------------------------------
# 5. Empty related_code_areas degradation
# ---------------------------------------------------------------------------


def test_required_tests_from_registry_handles_empty_related_code_areas():
    graph = _fake_graph_two_symbols()
    label_index = chi.build_label_index(graph)
    basename_index = chi.build_basename_index(graph)

    registry_entries = [
        {"path": "tickets/done/TCK-NO-AREAS.md", "related_code_areas": []},
        {"path": "tickets/done/TCK-NO-FIELD.md"},
    ]

    required_tests = chi.required_tests_from_registry(
        registry_entries, "src/foo/bar.py", label_index, basename_index
    )
    assert required_tests == set()


def test_build_impact_report_degrades_gracefully_with_no_registry_hits():
    graph = _fake_graph_two_symbols()

    def fake_affected_runner(symbol, depth, graph_path):
        return "No unique node match for X\n"

    report = chi.build_impact_report(
        _REPO_ROOT,  # real git repo; "src/foo/bar.py" is fictitious so churn is 0
        "src/foo/bar.py",
        graph=graph,
        registry_entries=[],
        affected_runner=fake_affected_runner,
    )
    assert report["required_tests"] == []
    assert report["dependents"] == []
    assert report["dependents_degraded"] is True
    # Must not crash formatting either.
    formatted = chi.format_impact_report(report)
    assert "src/foo/bar.py" in formatted
    assert "none" in formatted.lower()


# ---------------------------------------------------------------------------
# 6 & 7. Real-path smoke tests
# ---------------------------------------------------------------------------


@_requires_graphify
def test_real_path_pipeline_includes_kernel_as_dependent():
    report = chi.build_impact_report(_REPO_ROOT, "src/engine/pipeline.py")
    assert "src/engine/kernel.py" in report["dependents"]
    assert "src/engine/scenario_checkpoint.py" in report["dependents"]
    assert report["dependents_degraded"] is False
    assert report["criticality_tier"] in ("high", "medium", "low")


@_requires_graphify
def test_real_path_pipeline_kernel_visible_in_formatted_output_not_just_internal_data():
    # Regression guard for a real bug found during independent Test-phase
    # verification: report["dependents"] containing "src/engine/kernel.py" is
    # necessary but not sufficient -- pipeline.py has 622 total / 68 same-
    # subsystem dependents, and a plain alphabetical sort put kernel.py past
    # position 100, invisible in format_impact_report's truncated human-facing
    # summary even though the AC test above passed. Same-subsystem-first
    # sorting (sort_dependents_src_first) plus a wider truncation window fixed
    # this -- this test locks in the fix against the actual printed text, not
    # just the internal data structure the AC test above already covers.
    #
    # TCK-20260823-HOTFIX-CODE-HEALTH-IMPACT-APPLY-PY-STALE-DEPENDENT: the
    # second-dependent example used here was updated from
    # "src/engine/apply.py" to "src/engine/scenario_checkpoint.py" because
    # apply.py no longer has any import relationship (direct or within the
    # tool's affected-depth) to pipeline.py -- the original narrative above
    # about the truncation-window fix is still accurate, only the specific
    # example path was stale.
    report = chi.build_impact_report(_REPO_ROOT, "src/engine/pipeline.py")
    formatted = chi.format_impact_report(report)
    assert "src/engine/kernel.py" in formatted
    assert "src/engine/scenario_checkpoint.py" in formatted


def test_sort_dependents_src_first_prioritizes_same_subsystem():
    deps = {
        "src/other_pkg/z_file.py",
        "src/engine/a_file.py",
        "tests/unit/engine/test_a.py",
        "src/engine/z_file.py",
    }
    result = chi.sort_dependents_src_first(deps, "src/engine/pipeline.py")
    assert result == [
        "src/engine/a_file.py",
        "src/engine/z_file.py",
        "src/other_pkg/z_file.py",
        "tests/unit/engine/test_a.py",
    ]


@_requires_graphify
def test_real_path_low_centrality_profile_generalizes():
    # A real path with a markedly different (low churn, low centrality)
    # profile than src/engine/pipeline.py, to prove the command isn't
    # special-cased to the one file it was designed against.
    report = chi.build_impact_report(_REPO_ROOT, "src/observability/reporter.py")

    assert report["criticality_tier"] == "low"
    assert report["churn_lines_changed"] < 200
    assert report["edge_degree"] < 100
    # This file has real, resolvable dependents (unlike the ambiguous-label
    # degrade case) — proving the non-degraded aggregation path also
    # generalizes beyond pipeline.py.
    assert report["dependents_degraded"] is False


@_requires_graphify
def test_make_target_runs_successfully_against_real_repo():
    result = subprocess.run(
        ["make", "codebase-health-impact", "ARGS=src/observability/reporter.py"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "Change-Impact Report: src/observability/reporter.py" in result.stdout
    assert "Criticality tier:" in result.stdout


# ---------------------------------------------------------------------------
# 8. compute_churn_lines_changed's new target_pathspec parameter
# ---------------------------------------------------------------------------


def test_compute_churn_target_pathspec_scopes_to_smaller_number(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "small.py").write_text("x = 1\n" * 3, encoding="utf-8")
    (tmp_path / "src" / "big.py").write_text("y = 2\n" * 3, encoding="utf-8")
    _commit(tmp_path, "init both files")

    (tmp_path / "src" / "big.py").write_text("y = 2\n" * 50, encoding="utf-8")
    _commit(tmp_path, "grow big.py a lot")

    repo_wide_churn = chb.compute_churn_lines_changed(tmp_path)
    scoped_churn = chb.compute_churn_lines_changed(
        tmp_path, target_pathspec="src/small.py"
    )

    assert scoped_churn < repo_wide_churn, (
        "Scoping to a specific path must produce a smaller number than the "
        "repo-wide aggregate when other files changed more."
    )
    assert scoped_churn == 3  # 3 insertions from src/small.py's own commit


def test_compute_churn_target_pathspec_defaults_to_repo_wide():
    # Backward-compatibility: the default must behave exactly like the old
    # hardcoded "." pathspec — build_report()'s own call site relies on this.
    default_call = chb.compute_churn_lines_changed(_REPO_ROOT)
    explicit_dot_call = chb.compute_churn_lines_changed(_REPO_ROOT, target_pathspec=".")
    assert default_call == explicit_dot_call

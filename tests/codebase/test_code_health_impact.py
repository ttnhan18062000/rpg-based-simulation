"""Tests for codebase/reports/code_health_impact.py
(TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND).

Coverage-honesty requirement (matches this repo's established convention, e.g.
tests/codebase/test_codebase_health_baseline.py's own docstring): every check the
tool claims to compute has at least one fixture proving it computes correctly,
not just that it runs without error.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from codebase.reports import code_health_impact as chi
from codebase.reports import codebase_health_baseline as chb

_REPO_ROOT = Path(__file__).parent.parent.parent

# graphify (the CLI binary, not just graphify-out/graph.json) is a locally-installed
# dev tool -- confirmed absent from pyproject.toml/any CI workflow,
# and graphify-out/ is entirely gitignored (never committed). Only the one
# end-to-end smoke test below (test_make_target_runs_successfully_against_real_repo)
# invokes the real `graphify affected` against the real graph.json, so only it
# needs an environment that has separately run `graphify update .`; it is skipped
# without one. The other former real-path tests are fixture-based
# (TCK-20261004-CODE-HEALTH-IMPACT-TESTS-LOCAL-ENV) and run everywhere. This mirrors
# the existing skip pattern for `tools/search_mcp.py`'s tests (skipped when the
# knowledge index isn't built) rather than requiring graphify as a new CI
# dependency for what is, by design, an on-demand-only developer/agent tool.
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
        {"path": "agent-working/tickets/done/TCK-EXAMPLE.md",
         "related_code_areas": ["Widget", "tests/unit/foo/test_bar.py"]},
        {"path": "agent-working/tickets/done/TCK-UNRELATED.md",
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
        {"path": "agent-working/tickets/done/TCK-EXAMPLE-2.md",
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
        {"path": "agent-working/tickets/done/TCK-NO-AREAS.md", "related_code_areas": []},
        {"path": "agent-working/tickets/done/TCK-NO-FIELD.md"},
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


def _pipeline_fixture_graph():
    """pipeline.py with two defined symbols, shaped like graph.json."""
    nodes = [
        {"id": "pipeline", "label": "pipeline.py", "file_type": "code",
         "source_file": "src/engine/pipeline.py", "source_location": "L1"},
        {"id": "pipeline_run", "label": "run_phases()", "file_type": "code",
         "source_file": "src/engine/pipeline.py", "source_location": "L10"},
        {"id": "pipeline_cls", "label": "Pipeline", "file_type": "code",
         "source_file": "src/engine/pipeline.py", "source_location": "L50"},
    ]
    links = [
        {"source": "pipeline", "target": "pipeline_run", "relation": "contains"},
        {"source": "pipeline", "target": "pipeline_cls", "relation": "contains"},
    ]
    return _make_graph(nodes, links)


def _pipeline_fixture_affected(symbol, depth, graph_path):
    """Stand-in for `graphify affected`: many unrelated dependents that sort
    alphabetically BEFORE src/engine/ (src/aaa_*, tests/), the target's own
    subsystem, and the two files the regression guard names.  120 + 30 + 2
    dependents is well past the 40-entry display window, so only the
    same-subsystem-first sort keeps kernel.py visible."""
    lines = [f"- helper [code] src/aaa_other/mod_{i:03d}.py:L1" for i in range(120)]
    lines += [f"- helper [code] src/engine/a_sibling_{i:02d}.py:L1" for i in range(30)]
    lines += [
        "- Kernel [code] src/engine/kernel.py:L5",
        "- Checkpoint [code] src/engine/scenario_checkpoint.py:L7",
    ]
    return "\n".join(lines) + "\n"


def _pipeline_fixture_repo(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "src" / "engine").mkdir(parents=True)
    (tmp_path / "src" / "engine" / "pipeline.py").write_text("x = 1\n", encoding="utf-8")
    _commit(tmp_path, "init pipeline")
    return tmp_path


def test_fixture_pipeline_includes_kernel_as_dependent(tmp_path):
    # Fixture twin of the former real-graph test: same properties, no local
    # graphify graph or full git history needed
    # (TCK-20261004-CODE-HEALTH-IMPACT-TESTS-LOCAL-ENV).
    report = chi.build_impact_report(
        _pipeline_fixture_repo(tmp_path),
        "src/engine/pipeline.py",
        graph=_pipeline_fixture_graph(),
        registry_entries=[],
        affected_runner=_pipeline_fixture_affected,
    )
    assert "src/engine/kernel.py" in report["dependents"]
    assert "src/engine/scenario_checkpoint.py" in report["dependents"]
    assert report["dependents_degraded"] is False
    assert report["criticality_tier"] in ("high", "medium", "low")


def test_fixture_pipeline_kernel_visible_in_formatted_output_not_just_internal_data(tmp_path):
    # Regression guard for a real bug found during independent Test-phase
    # verification: report["dependents"] containing "src/engine/kernel.py" is
    # necessary but not sufficient -- pipeline.py has hundreds of dependents,
    # and a plain alphabetical sort put kernel.py past position 100, invisible
    # in format_impact_report's truncated human-facing summary even though the
    # internal-data test above passed. Same-subsystem-first sorting
    # (sort_dependents_src_first) plus a wider truncation window fixed this --
    # this test locks in the fix against the actual printed text.
    #
    # Moved onto a fixture graph by TCK-20261004-CODE-HEALTH-IMPACT-TESTS-LOCAL-ENV:
    # the fixture's 120 src/aaa_other/* dependents sort before src/engine/*
    # alphabetically, so reverting to a plain sort pushes kernel.py to position
    # 150 and fails this test, as the real graph did.
    report = chi.build_impact_report(
        _pipeline_fixture_repo(tmp_path),
        "src/engine/pipeline.py",
        graph=_pipeline_fixture_graph(),
        registry_entries=[],
        affected_runner=_pipeline_fixture_affected,
    )
    assert len(report["dependents"]) > 100
    formatted = chi.format_impact_report(report)
    assert "src/engine/kernel.py" in formatted
    assert "src/engine/scenario_checkpoint.py" in formatted
    assert "src/aaa_other/mod_119.py" not in formatted  # truncated, not dumped


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


def test_fixture_low_centrality_profile_generalizes(tmp_path):
    # A path with a markedly different (low churn, low centrality) profile than
    # the pipeline fixture, to prove the command isn't special-cased to one
    # file. Fixture-based (TCK-20261004-CODE-HEALTH-IMPACT-TESTS-LOCAL-ENV): the
    # former real-graph version depended on each worktree's local graph.
    _init_repo(tmp_path)
    (tmp_path / "src" / "observability").mkdir(parents=True)
    (tmp_path / "src" / "observability" / "reporter.py").write_text("x = 1\n", encoding="utf-8")
    _commit(tmp_path, "init reporter")

    graph = _make_graph(
        [
            {"id": "rep", "label": "reporter.py", "file_type": "code",
             "source_file": "src/observability/reporter.py", "source_location": "L1"},
            {"id": "rep_cls", "label": "Reporter", "file_type": "code",
             "source_file": "src/observability/reporter.py", "source_location": "L5"},
        ],
        [{"source": "rep", "target": "rep_cls", "relation": "contains"}],
    )

    def fake_affected(symbol, depth, graph_path):
        return "- consumer [code] src/observability/runner.py:L3\n"

    report = chi.build_impact_report(
        tmp_path,
        "src/observability/reporter.py",
        graph=graph,
        registry_entries=[],
        affected_runner=fake_affected,
    )
    assert report["criticality_tier"] == "low"
    assert report["churn_lines_changed"] < 200
    assert report["edge_degree"] < 100
    # Real, resolvable dependents (unlike the ambiguous-label degrade case) --
    # proves the non-degraded aggregation path also generalizes.
    assert report["dependents"] == ["src/observability/runner.py"]
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


def test_compute_churn_target_pathspec_defaults_to_repo_wide(tmp_path):
    # Backward-compatibility: the default must behave exactly like the old
    # hardcoded "." pathspec -- build_report()'s own call site relies on this.
    # Runs on a small temporary repository: over the real repository on a full
    # local clone this exceeded the 60 s resource budget
    # (TCK-20261004-CODE-HEALTH-IMPACT-TESTS-LOCAL-ENV).
    _init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n" * 4, encoding="utf-8")
    _commit(tmp_path, "init a")
    (tmp_path / "src" / "b.py").write_text("y = 2\n" * 7, encoding="utf-8")
    _commit(tmp_path, "add b")

    default_call = chb.compute_churn_lines_changed(tmp_path)
    explicit_dot_call = chb.compute_churn_lines_changed(tmp_path, target_pathspec=".")
    assert default_call == explicit_dot_call
    assert default_call == 11

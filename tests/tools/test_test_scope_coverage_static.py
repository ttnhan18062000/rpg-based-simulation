"""Tests for tools/gate_checks/test_scope_coverage_static.py
(TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP).

Coverage-honesty requirement: this must reproduce the exact real incident it was built to catch
(a tools/retrieval_cache.py change with a pytest_command that never mentions tests/tools/) and
prove the fixed check flags it, not just exercise the function in the abstract.

No pytest marker — must not be discovered by `pytest tests/ -m "architecture"` (that lane guards
`src/` architecture, a different domain from this agent-workflow-hygiene module) — mirrors
test_architecture_reviewer_static.py's own convention.
"""

import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.test_scope_coverage_static import (  # noqa: E402
    check_test_scope_coverage,
    expected_test_dirs_for,
)


# ---------------------------------------------------------------------------
# expected_test_dirs_for — pure mapping
# ---------------------------------------------------------------------------


def test_flat_tools_file_maps_to_tests_tools():
    assert expected_test_dirs_for("tools/retrieval_cache.py") == "tests/tools/"
    assert expected_test_dirs_for("tools/knowledge_gateway_redaction.py") == "tests/tools/"


def test_agent_monitoring_hyphenated_dir_maps_to_tests_tools():
    assert expected_test_dirs_for("tools/agent-monitoring/generate_retro.py") == "tests/tools/"


def test_gate_checks_dir_maps_to_tests_tools():
    assert expected_test_dirs_for("tools/gate_checks/architecture_reviewer_static.py") == "tests/tools/"


def test_agent_codex_subdir_maps_to_same_name_mirror():
    assert (
        expected_test_dirs_for("tools/agent_codex_live_transport/transport.py")
        == "tests/agent_codex_live_transport/"
    )
    assert (
        expected_test_dirs_for("tools/agent_codex_pilot_orchestration/orchestrator.py")
        == "tests/agent_codex_pilot_orchestration/"
    )


def test_src_subsystem_maps_to_tests_unit():
    assert expected_test_dirs_for("src/combat/resolver.py") == "tests/unit/combat/"
    assert expected_test_dirs_for("src/worldassembly/assembler.py") == "tests/unit/worldassembly/"


def test_unrecognized_src_subsystem_returns_none_not_a_guess():
    # "not_a_real_subsystem" isn't in the documented src/ subsystem list -- must not fabricate
    # a tests/unit/not_a_real_subsystem/ path that doesn't exist.
    assert expected_test_dirs_for("src/not_a_real_subsystem/thing.py") is None


def test_docs_and_ticket_paths_return_none():
    assert expected_test_dirs_for("docs/mechanics/01_entity_anatomy.md") is None
    assert expected_test_dirs_for("tickets/done/TCK-1.md") is None


def test_tools_subpath_with_no_rule_returns_none_not_tests_tools_fallback():
    # A tools/ path that is neither a flat *.py file, agent-monitoring/gate_checks, nor a known
    # agent_codex/orchestration/replay mirror subdir must not silently default to tests/tools/ --
    # that would mask genuinely unmapped directories instead of surfacing them for a future map
    # update.
    assert expected_test_dirs_for("tools/search/some_new_subdir/thing.py") is None


# ---------------------------------------------------------------------------
# check_test_scope_coverage — the real incident reproduction
# ---------------------------------------------------------------------------


def test_reproduces_the_real_incident_flat_tools_change_uncovered():
    """The exact real failure mode: TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-
    USAGE-DASHBOARD changed tools/retrieval_cache.py; its Test phase's pytest_command named only
    the specific new test files it wrote inside tests/tools/, never the whole directory, and two
    pre-existing tests there (not in that named subset) broke undetected. Prove the fixed check
    flags this exact shape — including the trap where the command string technically contains
    "tests/tools/" as a path *prefix* of those named files, which a naive substring check would
    have wrongly treated as full coverage."""
    files_changed = [
        "tools/retrieval_cache.py",
        "src/api/agent_ops_dashboard/models.py",
        "tests/tools/test_agent_ops_dashboard_stats.py",
        "tests/tools/test_retrieval_cache.py",
    ]
    # Mirrors the real incident: the reported command covered only the new tests it wrote (named
    # individually, not the bare directory), and a src/api/ subsystem -- never the whole
    # tests/tools/ directory tools/retrieval_cache.py itself maps to.
    pytest_command = "pytest tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_retrieval_cache.py tests/unit/api/ -v"

    results = check_test_scope_coverage(files_changed, pytest_command)

    tools_dir_results = [r for r in results if r["condition"] == "test_scope_covers:tests/tools/"]
    assert len(tools_dir_results) == 1
    assert tools_dir_results[0]["status"] == "FAIL"
    assert "tools/retrieval_cache.py" in tools_dir_results[0]["evidence"]


def test_passes_when_tools_dir_genuinely_covered():
    files_changed = ["tools/retrieval_cache.py"]
    pytest_command = "pytest tests/tools/ -v"

    results = check_test_scope_coverage(files_changed, pytest_command)

    assert len(results) == 1
    assert results[0]["status"] == "PASS"


def test_fails_when_only_specific_files_within_dir_are_named_not_bare_dir():
    # Deliberately strict (see module docstring): a command listing individual files inside
    # tests/tools/ instead of the bare directory does NOT count as covering it, even though the
    # directory string technically appears as a path prefix -- this is the exact trap the real
    # incident fell into and the check must not repeat.
    files_changed = ["tools/retrieval_cache.py"]
    pytest_command = "pytest tests/tools/test_retrieval_cache.py -v"

    results = check_test_scope_coverage(files_changed, pytest_command)

    assert results[0]["status"] == "FAIL"


def test_multiple_files_mapping_to_same_dir_only_report_once():
    files_changed = ["tools/retrieval_cache.py", "tools/knowledge_gateway_redaction.py"]
    pytest_command = "pytest tests/unit/core/ -v"  # tests/tools/ missing for both

    results = check_test_scope_coverage(files_changed, pytest_command)

    tools_dir_results = [r for r in results if r["condition"] == "test_scope_covers:tests/tools/"]
    assert len(tools_dir_results) == 1
    assert tools_dir_results[0]["status"] == "FAIL"


def test_unmapped_files_produce_no_results_not_false_pass_or_fail():
    files_changed = ["docs/mechanics/01_entity_anatomy.md", "tickets/done/TCK-1.md"]
    pytest_command = "pytest tests/unit/core/ -v"

    results = check_test_scope_coverage(files_changed, pytest_command)

    assert results == []


def test_empty_pytest_command_fails_every_mapped_file():
    files_changed = ["tools/retrieval_cache.py"]

    results = check_test_scope_coverage(files_changed, "")

    assert len(results) == 1
    assert results[0]["status"] == "FAIL"


def test_src_and_tools_changes_together_check_both_independently():
    files_changed = ["src/combat/resolver.py", "tools/retrieval_cache.py"]
    pytest_command = "pytest tests/unit/combat/ -v"  # covers src/ but not tools/

    results = check_test_scope_coverage(files_changed, pytest_command)

    by_dir = {r["condition"]: r["status"] for r in results}
    assert by_dir["test_scope_covers:tests/unit/combat/"] == "PASS"
    assert by_dir["test_scope_covers:tests/tools/"] == "FAIL"

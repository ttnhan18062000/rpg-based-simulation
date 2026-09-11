"""Architecture guard for the Knowledge Gateway MCP removal: the package no longer exists anywhere
in the repo, neither at its original `tools/` paths (archived by
TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE) nor at `tools/archive/` (hard-deleted by
TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY). Only the extracted, gateway-independent
`write_path_guard.py` remainder survives.
"""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_ARCHIVE_DIR = _TOOLS_DIR / "archive"

_ARCHIVED_FILENAMES = [
    "knowledge_gateway_mcp.py",
    "knowledge_gateway_router.py",
    "knowledge_gateway_packet_assembly.py",
    "knowledge_gateway_cache.py",
    "knowledge_gateway_redaction.py",
    "start_knowledge_gateway_mcp.sh",
]


def test_gateway_modules_archived_not_present_at_old_paths():
    for filename in _ARCHIVED_FILENAMES:
        old_path = _TOOLS_DIR / filename
        assert not old_path.exists(), f"expected {old_path} to no longer exist (archived)"


def test_gateway_modules_no_longer_exist_at_archive_location():
    for filename in _ARCHIVED_FILENAMES:
        archived_path = _ARCHIVE_DIR / filename
        assert not archived_path.exists(), f"expected {archived_path} to be hard-deleted, not archived"


def test_write_path_guard_exists_and_is_not_archived():
    """The extracted, gateway-independent module must exist at a stable, non-archived location."""
    assert (_TOOLS_DIR / "write_path_guard.py").exists()
    assert not (_ARCHIVE_DIR / "write_path_guard.py").exists()


_MEASUREMENT_TOOLING_FILENAMES = [
    "kgmcp_baseline_corpus.py",
    "kgmcp_baseline_runner.py",
    "kgmcp_phase5_repeated_demand_measurement_runner.py",
]

_REMOVED_MEASUREMENT_FIXTURES = [
    "kgmcp_phase1_baseline_comparison_results.json",
    "kgmcp_phase2_baseline_recomparison_results.json",
    "kgmcp_phase3_pilot_acceptance_measurement_results.json",
    "kgmcp_phase4_warm_direct_tool_comparison_results.json",
    "kgmcp_measurement_baseline_corpus_results.json",
    "kgmcp_phase5_events_investigate_snapshot.json",
    "kgmcp_phase5_working_log_snapshot.json",
]

_RETAINED_MEASUREMENT_FIXTURES = [
    "kgmcp_phase4_direct_tool_comparison_results.json",
    "kgmcp_phase5_repeated_demand_measurement_results.json",
]


def test_kgmcp_measurement_modules_no_longer_exist():
    for filename in _MEASUREMENT_TOOLING_FILENAMES:
        path = _TOOLS_DIR / "agent-monitoring" / filename
        assert not path.exists(), f"expected {path} to no longer exist (removed measurement tooling)"


def test_orphaned_kgmcp_fixtures_removed_retained_fixtures_present():
    fixtures_dir = _REPO_ROOT / "tests" / "tools" / "fixtures"
    for filename in _REMOVED_MEASUREMENT_FIXTURES:
        path = fixtures_dir / filename
        assert not path.exists(), f"expected {path} to no longer exist (removed measurement fixture)"
    for filename in _RETAINED_MEASUREMENT_FIXTURES:
        path = fixtures_dir / filename
        assert path.exists(), f"expected {path} to still exist (live tests/docs/ consumer)"

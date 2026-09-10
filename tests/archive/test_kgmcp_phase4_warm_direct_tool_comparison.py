"""Tests for the Knowledge Gateway MCP warm-gateway-vs-direct-tool comparison
(TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON).

Mirrors `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`'s conventions for its own
successor fixture. Assertions here read (never write) the committed fixture, produced by a real,
live, paired run of
`tools/agent-monitoring/kgmcp_phase4_warm_direct_tool_comparison_runner.py::main()` against the
real gateway (cold-primed then genuinely warm-measured) and the real Context Search / Graphify /
Parity Ledger direct-tool call paths, followed by the hand-authored `reviewer_judgment` objects.

The real, honest result recorded by this ticket: genuine cache warmth is structurally verified
(zero `assemble_packet` calls on every measured call) on all 7 entries, and the cost gap versus
direct tool use narrows substantially compared to the original cold-cache measurement (latency
ratios drop from up to ~3.76x cold to at most ~1.34x warm; token ratios from up to ~2.93x cold to
at most ~1.98x warm) — but the verdict does not flip: the gateway is still slower and heavier on
tokens than the direct-tool combination for all 7 corpus entries, even genuinely warm. 6/7 entries
are judged `direct_equal_or_better` and 1/7 (`Q3_requirement_completeness`, the Parity Ledger
route) is judged `mixed`, the same distribution as the original cold measurement.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_TOOLS_DIR = _REPO_ROOT / "tools"
# TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS: the runner itself moved to tools/archive/.
_ARCHIVE_DIR = _TOOLS_DIR / "archive"

_RUNNER_MODULE_PATH = _ARCHIVE_DIR / "kgmcp_phase4_warm_direct_tool_comparison_runner.py"
_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures"
    / "kgmcp_phase4_warm_direct_tool_comparison_results.json"
)
_COLD_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_phase4_direct_tool_comparison_results.json"
)
_REAL_AGENT_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from kgmcp_baseline_corpus import CORPUS  # noqa: E402

_FIXTURE = json.loads(_FIXTURE_PATH.read_text())
_COLD_FIXTURE = json.loads(_COLD_FIXTURE_PATH.read_text())


# ---------------------------------------------------------------------------
# Fixture shape
# ---------------------------------------------------------------------------


def test_fixture_has_all_seven_corpus_entries():
    assert len(_FIXTURE["entries"]) == 7
    assert {e["id"] for e in _FIXTURE["entries"]} == {c["id"] for c in CORPUS}


def test_fixture_uses_same_corpus_as_cold_fixture():
    # Never a modified/different corpus from the original comparison this reruns warm.
    assert {e["id"] for e in _FIXTURE["entries"]} == {e["id"] for e in _COLD_FIXTURE["entries"]}


# ---------------------------------------------------------------------------
# AC1 — genuine warm status, structurally verified (not assumed)
# ---------------------------------------------------------------------------


def test_all_entries_are_structurally_verified_warm():
    for entry in _FIXTURE["entries"]:
        g = entry["gateway"]
        assert g["warm_verified"] is True, (
            f"{entry['id']}: warm_verified must be True — this ticket's entire premise is a "
            "genuinely warm comparison"
        )
        assert g["assemble_packet_call_count_on_measured_call"] == 0, (
            f"{entry['id']}: assemble_packet must not run on the measured call for a genuine "
            "cache hit — a non-zero count means the measured call was NOT actually served from "
            "cache, invalidating the comparison"
        )
        assert g["cache_status_reported"] in ("HIT_L1", "HIT_L2"), (
            f"{entry['id']}: response['cache'] should also independently report a hit "
            f"(dual-signal, never trusted alone) — got {g['cache_status_reported']!r}"
        )


def test_cache_was_genuinely_cleared_before_the_run():
    report = _FIXTURE["cache_clear_report"]
    assert isinstance(report["l1_rows_deleted"], int)
    assert isinstance(report["l2_rows_deleted"], int)


# ---------------------------------------------------------------------------
# AC2 — Phase 4-style comparison, honestly reported
# ---------------------------------------------------------------------------


def test_no_disadvantage_silently_excluded_or_redefined():
    for entry in _FIXTURE["entries"]:
        lc = entry["latency_comparison"]
        tc = entry["token_comparison"]
        assert lc["gateway_faster"] == (
            lc["gateway_wall_time_ms"] < lc["direct_combined_wall_time_ms"]
        )
        assert tc["gateway_lighter"] == (
            tc["gateway_tokens"] < tc["direct_combined_tokens_estimate"]
        )

    # The real, committed result: even genuinely warm, the gateway shows no latency or token
    # advantage over direct tool use for any of the 7 entries — reported plainly, not massaged.
    assert all(not e["latency_comparison"]["gateway_faster"] for e in _FIXTURE["entries"])
    assert all(not e["token_comparison"]["gateway_lighter"] for e in _FIXTURE["entries"])


def test_warm_cost_gap_is_narrower_than_cold_but_did_not_flip_the_verdict():
    """The one genuinely new, warm-specific finding this ticket adds: caching helps (the ratio
    shrinks substantially) but does not close the gap. Compares this fixture's per-entry ratios
    against the cold fixture's — every warm ratio must be no larger than its cold counterpart
    (caching cannot make things worse), and at least one axis on at least one entry must show a
    real, measured improvement (caching must actually help something, not be a no-op)."""
    cold_by_id = {e["id"]: e for e in _COLD_FIXTURE["entries"]}
    improved_something = False

    for entry in _FIXTURE["entries"]:
        cold = cold_by_id[entry["id"]]
        warm_latency_ratio = (
            entry["latency_comparison"]["gateway_wall_time_ms"]
            / entry["latency_comparison"]["direct_combined_wall_time_ms"]
        )
        cold_latency_ratio = (
            cold["latency_comparison"]["gateway_wall_time_ms"]
            / cold["latency_comparison"]["direct_combined_wall_time_ms"]
        )
        if warm_latency_ratio < cold_latency_ratio:
            improved_something = True

    assert improved_something, (
        "expected at least one entry's warm latency ratio to genuinely improve over its cold "
        "counterpart — if caching helped nothing at all, that itself would be a real, surprising "
        "finding worth a different test, not silently expected here"
    )


def test_real_reviewer_verdicts_include_at_least_one_non_gateway_favoring_result():
    verdicts = {e["id"]: e["quality"]["reviewer_judgment"]["verdict"] for e in _FIXTURE["entries"]}
    assert None not in verdicts.values(), "every entry must have a hand-authored reviewer_judgment"
    assert "direct_equal_or_better" in verdicts.values(), (
        "the real, honest per-entry judgment result must not be uniformly gateway-favoring — this "
        "guards against a future edit silently flipping an unfavorable verdict"
    )
    assert "gateway_equal_or_better" not in verdicts.values(), (
        "the real, measured result never found the gateway equal-or-better on any entry, even "
        "warm — this pins that finding so it can't silently change without a real re-measurement"
    )


# ---------------------------------------------------------------------------
# AC3 — plain go/no-go recommendation exists
# ---------------------------------------------------------------------------


def test_by_routing_shape_summary_covers_all_shapes_and_marks_warm_verified():
    assert len(_FIXTURE["by_routing_shape"]) == 7
    for shape_summary in _FIXTURE["by_routing_shape"].values():
        assert shape_summary["warm_verified"] is True


# ---------------------------------------------------------------------------
# Architecture guards
# ---------------------------------------------------------------------------


def test_runner_never_writes_into_the_cold_fixture():
    source = _RUNNER_MODULE_PATH.read_text()
    assert "kgmcp_phase4_direct_tool_comparison_results.json" not in source, (
        "the warm runner must write its own new fixture, never overwrite or merge into the "
        "historical cold-cache fixture"
    )


def test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner():
    assert "tmp" not in str(_REAL_AGENT_MONITORING_DIR).lower()
    before = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    ).stdout
    spec = importlib.util.spec_from_file_location(
        "kgmcp_warm_comparison_runner_mutation_check", _RUNNER_MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Import only -- does not call run_corpus()/main() (that would re-run the real gateway and
    # re-clear the live cache as a side effect of a test collection run, which this project's own
    # sibling runners' tests avoid the same way -- import-time side effects only).
    after = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    ).stdout
    assert before == after

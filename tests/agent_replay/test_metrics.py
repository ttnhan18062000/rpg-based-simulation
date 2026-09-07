"""Tests for tools/agent_replay/metrics.py (TCK-20260907-FILTERED-REPLAY-EVAL-PILOT, AC #6)."""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from agent_replay.metrics import compare_repeatability, compute_metrics  # noqa: E402
from agent_replay.pilot_isolation import IsolationEvidence  # noqa: E402


def test_metrics_computation_produces_all_3_tiers():
    run1_flags = {
        "TCK-A": {"M2": True},
        "TCK-B": {"M2": False},
    }
    run2_flags = {
        "TCK-A": {"M2": True},
        "TCK-B": {"M2": False},
    }
    isolation_evidence = IsolationEvidence(
        held=True, pre_porcelain="", post_porcelain="", violation=None
    )
    timing_data = {
        "wall_clock_s": {"run1": 0.01, "run2": 0.01},
        "work_volume": {"run1_phases": 8, "run2_phases": 8},
    }

    metrics = compute_metrics(run1_flags, run2_flags, isolation_evidence, timing_data)

    assert isinstance(metrics.primary_repeatability_pct, float)
    assert metrics.primary_repeatability_pct == 100.0
    assert metrics.safety_isolation_held is True
    assert isinstance(metrics.safety_evidence, str) and metrics.safety_evidence
    assert metrics.efficiency_wall_clock_s == {"run1": 0.01, "run2": 0.01}
    assert metrics.efficiency_work_volume == {"run1_phases": 8, "run2_phases": 8}


def test_metrics_repeatability_comparison_detects_a_real_discrepancy():
    run1_flags = {"TCK-A": {"M2": True}, "TCK-B": {"M2": False}}
    run2_flags = {"TCK-A": {"M2": False}, "TCK-B": {"M2": False}}  # disagrees on TCK-A

    result = compare_repeatability(run1_flags, run2_flags)

    assert result.repeatable is False
    assert "TCK-A:M2" in result.disagreements
    assert result.per_defect_class_agreement["M2"] is False


def test_metrics_repeatability_comparison_reports_repeatable_when_all_agree():
    run1_flags = {"TCK-A": {"M2": True, "M3": False}}
    run2_flags = {"TCK-A": {"M2": True, "M3": False}}

    result = compare_repeatability(run1_flags, run2_flags)

    assert result.repeatable is True
    assert result.disagreements == []

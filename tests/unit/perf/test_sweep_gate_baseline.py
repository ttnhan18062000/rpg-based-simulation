"""The committed sweep-gate baseline (TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS): `src gate` and `compare-sweep` can parse it and its tick cost is comparable."""
from __future__ import annotations

import json
from pathlib import Path

from src.observability.reporting.baseline_comparator import tick_cost_incomparable_reason
from src.observability.reporting.baseline_generator import BaselineConfig

LATEST = Path(__file__).resolve().parents[3] / "docs" / "observability" / "baselines" / "latest.json"


def test_latest_json_is_a_baseline_config_the_gate_can_validate() -> None:
    data = json.loads(LATEST.read_text(encoding="utf-8"))
    baseline = BaselineConfig.model_validate(data)
    assert baseline.artifact_schema_version == "baseline_v1" and baseline.accepted_run_count >= 5 and not baseline.is_weak_baseline
    assert "tick_compute_ms_p95" in baseline.metrics


def test_latest_json_has_a_comparable_tick_cost_accounting() -> None:
    assert tick_cost_incomparable_reason(json.loads(LATEST.read_text(encoding="utf-8"))) is None


def test_the_deleted_matrix_files_are_gone_and_only_latest_json_is_a_baseline_here() -> None:
    assert sorted(p.name for p in LATEST.parent.glob("*.json")) == ["latest.json"]

"""Integration tests for demo_escort_pack — E63D acceptance criteria.

Verifies that ESCORT_DIGNITARY was added via the feature pack mechanism without
modifying any file under src/engine/ or src/domains/.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.domains.feature_packs.balance_spec import (
    BalanceExperimentRunner,
    BalanceExperimentSpec,
)
from src.domains.feature_packs.loader import FeaturePackLoader
from src.domains.feature_packs.profile import RuntimeProfile


PACK_DIR = Path("content/packs")


@pytest.mark.integration
def test_new_quest_type_via_manifest_no_engine_changes():
    """ESCORT_DIGNITARY must be registered solely from content/packs/; no src/ modifications."""
    profile = RuntimeProfile(active_pack_names=["demo_escort_pack"])
    registries = FeaturePackLoader.load(profile, PACK_DIR)

    assert "adventure_routing" in registries, "adventure_routing registry must exist after loading demo pack"
    cls = registries["adventure_routing"].lookup("ESCORT_DIGNITARY")
    assert cls is not None

    # Confirm the generator lives under content/, not src/
    import inspect
    module_file = inspect.getfile(cls)
    assert "content/packs" in module_file.replace("\\", "/"), (
        f"EscortDignitaryGenerator must be defined under content/packs/, got: {module_file}"
    )
    assert "src/engine" not in module_file and "src/domains" not in module_file, (
        "ESCORT_DIGNITARY generator must not reside in src/engine/ or src/domains/"
    )


@pytest.mark.integration
def test_balance_experiment_spec_evaluates_demo_pack():
    """BalanceExperimentRunner evaluates demo pack against a metric snapshot."""
    # Simulate a metric snapshot as would be produced by a post-run analysis pass
    snapshot = {
        "route_distribution": {
            "ESCORT_DIGNITARY": 0.30,
            "RECOVER": 0.35,
            "GATHER_RESOURCE": 0.20,
        },
        "mean_score": 0.62,
    }

    spec = BalanceExperimentSpec(
        metric_path="route_distribution.ESCORT_DIGNITARY",
        baseline_pack="demo_escort_pack",
        threshold=0.1,
        tolerance=0.05,
    )

    result = BalanceExperimentRunner.run(spec, snapshot)
    assert result.passed, (
        f"Expected ESCORT_DIGNITARY share >= {spec.threshold - spec.tolerance:.2f}, "
        f"got {result.measured:.2f}"
    )
    assert result.measured == pytest.approx(0.30)


@pytest.mark.integration
def test_balance_experiment_below_threshold_fails():
    """Runner correctly returns failed result when metric is below threshold."""
    snapshot = {"route_distribution": {"ESCORT_DIGNITARY": 0.02}}
    spec = BalanceExperimentSpec(
        metric_path="route_distribution.ESCORT_DIGNITARY",
        baseline_pack="demo_escort_pack",
        threshold=0.1,
    )
    result = BalanceExperimentRunner.run(spec, snapshot)
    assert not result.passed

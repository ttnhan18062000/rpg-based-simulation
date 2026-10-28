"""Pins GenerateSimulationSetupWorkflow._format_review_pack's output byte for byte on a fixed input.

Written before the review-pack template moved into a module-level helper
(TCK-20261019-SEMGREP-BASELINE-FINDINGS-IN-SRC-TRIAGE) and kept as the guard that the move changed no text.
"""
from __future__ import annotations

import hashlib
from types import SimpleNamespace

from src.lab.workflows.generate_simulation_setup import GenerateSimulationSetupWorkflow


def _fixed_inputs() -> dict:
    request = SimpleNamespace(user_goal="raise hunger pressure", mode="draft", constraints={"budget_profile": "ci_small"})
    world_spec = SimpleNamespace(
        world_id="world_pin_01",
        topology=SimpleNamespace(width=32, height=24),
        regions=[SimpleNamespace(id="r1", type="plains", bounds=(0, 0, 15, 23)), SimpleNamespace(id="r2", type="forest", bounds=(16, 0, 31, 23))],
        entities=[SimpleNamespace(id="g1", role="villager", count=12)],
        resources=[SimpleNamespace(id="n1", resource_type="berry", count=5), SimpleNamespace(id="n2", resource_type="wood", count=3)],
    )
    scenario_spec = SimpleNamespace(
        scenario_id="scen_pin_01",
        intent=SimpleNamespace(primary_goal="starvation_wave"),
        allowed_anomalies=["famine"],
        required_signals=SimpleNamespace(metrics=["deaths", "food_stock"]),
    )
    experiment_spec = SimpleNamespace(run=SimpleNamespace(ticks=500, seeds=[42, 43]), observability=SimpleNamespace(mode="summary"))
    return {
        "request": request,
        "world_spec": world_spec,
        "scenario_spec": scenario_spec,
        "experiment_spec": experiment_spec,
        "duplication_report": {"world_matches": ["a"], "scenario_matches": []},
        "world_val": {"status": "VALID", "errors": []},
        "scenario_val": {"status": "INVALID", "errors": ["missing goal"]},
        "experiment_val": {"status": "VALID", "errors": []},
        "budget_report": {
            "status": "OK", "run_count": 2, "total_ticks": 1000, "expected_runtime_minutes": 1.5,
            "expected_artifact_mb": 0.25, "warnings": [], "blocked_reasons": [],
        },
        "context_pack": {},
    }


# sha256 of the output produced by the pre-move code on _fixed_inputs() (recorded 2026-10-28).
EXPECTED_SHA256 = "91074739448031a33ca00c8889962c0dcdaacdfe5fec8e78e6b031426815a7ff"


def test_review_pack_output_is_byte_identical_on_a_fixed_input() -> None:
    """The review pack text is unchanged, byte for byte, on a fixed input."""
    workflow = GenerateSimulationSetupWorkflow.__new__(GenerateSimulationSetupWorkflow)
    text = workflow._format_review_pack(**_fixed_inputs())
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == EXPECTED_SHA256
    assert text.startswith("# Simulation Generation Review Pack\n")
    assert "- **Status**: Duplicate keys/keywords detected: 1" in text

"""AC #3 hand-orchestrated metamorphic validation for species hostility.

TCK-20260831-RACE-RELATIONS-MATRIX, Step 12. Per the plan's explicit, user-approved
resolution of investigation.md's Risk #1: `MutationLabOrchestrator.run_mutation_lab()` /
`MutationEngine.apply_mutations` structurally cannot target content-catalog files
(`target.split(".")[0]` must resolve against `WorldSpec`/`ScenarioSpec` model fields, and
`species_relations.yaml` lives entirely outside both). This test bypasses that pipeline
entirely and hand-orchestrates the same validation `MetamorphicRuleEngine.evaluate_rules()`
provides: physically swap the on-disk `data/content/social/species_relations.yaml` wolf<->human
entries between a no-entry baseline and a `hostility: "high"` variant, run the real
`unit_faction_tension` corpus world (human town_council population + wolf wild_beast_pack
population, "already proven population-stable to 2000 ticks") via
`ScenarioLabOrchestrator.run_lab()` directly for each variant, compute a real
`combat_engagement_rate` from each run's `simulation_events.jsonl`'s real
`combat_engagement_started` events (NOT `run_report.json`, which has no such field), and
call the real `MetamorphicRuleEngine.evaluate_rules()` directly against the resulting
`variant_metrics`.

Does not extend MutationEngine or any shared lab infrastructure — stays self-contained to
this ticket's own validation, per the plan's explicit scope guard.
"""
import json
import os
import shutil

import pytest

from src.worldbuilding.repository import WorldRepository
from src.lab.repository import ScenarioRepository, ExperimentRepository, LabRunRepository
from src.lab.orchestrator import ScenarioLabOrchestrator
from src.lab.schema import ScenarioSpec, ExperimentSpec, ExpectedRelationshipSpec
from src.lab.metamorphic import MetamorphicRuleEngine

SPECIES_RELATIONS_PATH = "data/content/social/species_relations.yaml"
SCENARIO_ID = "species_hostility_metamorphic_check"
EXPERIMENT_ID = "species_hostility_metamorphic_check_experiment"
SEEDS = [201, 202, 203]
TICKS = 200

SCENARIO_DIR = f"data/scenarios/{SCENARIO_ID}"
EXPERIMENT_DIR = f"data/experiments/{EXPERIMENT_ID}"
LAB_RUN_BASELINE = "data/lab_runs/species_hostility_baseline"
LAB_RUN_HIGH = "data/lab_runs/species_hostility_high"


def _strip_wolf_human_entries(content: str) -> str:
    """Removes the wolf_to_human / human_to_wolf blocks, leaving every other authored
    entry (including every other pair) untouched -- the 'no-entry baseline' variant."""
    blocks = content.split("\n\n")
    kept = [
        b for b in blocks
        if 'id: "wolf_to_human"' not in b and 'id: "human_to_wolf"' not in b
    ]
    return "\n\n".join(kept)


def _set_wolf_human_high(content: str) -> str:
    """The 'compared' variant: wolf<->human hostility overwritten to 'high' both ways."""
    stripped = _strip_wolf_human_entries(content)
    addition = (
        "\n\n"
        '- id: "wolf_to_human"\n'
        '  source_species: "wolf"\n'
        '  target_species: "human"\n'
        '  relationship_model: "predator_prey"\n'
        "  axes:\n"
        '    hostility: "high"\n'
        "\n"
        '- id: "human_to_wolf"\n'
        '  source_species: "human"\n'
        '  target_species: "wolf"\n'
        '  relationship_model: "predator_prey"\n'
        "  axes:\n"
        '    hostility: "high"\n'
    )
    return stripped + addition


def _count_combat_engagements(lab_run_id: str) -> int:
    total = 0
    for seed in SEEDS:
        run_id = f"run_{lab_run_id}_seed_{seed}"
        path = os.path.join("data", "lab_runs", lab_run_id, "runs", run_id, "simulation_events.jsonl")
        assert os.path.isfile(path), f"Missing simulation_events.jsonl for {run_id}"
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event = json.loads(line)
                if event.get("event_type") == "combat_engagement_started":
                    total += 1
    return total


def _cleanup_created_dirs():
    for d in (SCENARIO_DIR, EXPERIMENT_DIR, LAB_RUN_BASELINE, LAB_RUN_HIGH):
        if os.path.exists(d):
            shutil.rmtree(d)
    # ScenarioRepository/ExperimentRepository/LabRunRepository each write their own
    # top-level index JSON (scenario_index.json / experiment_index.json /
    # lab_runs_index.json) directly under data/scenarios, data/experiments,
    # data/lab_runs -- one level up from the per-item directories removed above.
    # None of data/scenarios/, data/experiments/, data/lab_runs/ existed before this
    # test ran (confirmed: not gitignored, no git history, absent from the main
    # checkout), so remove the leftover index files and the now-empty parent
    # directories this test alone created.
    for parent_dir in ("data/scenarios", "data/experiments", "data/lab_runs"):
        if os.path.isdir(parent_dir) and not os.listdir(parent_dir):
            os.rmdir(parent_dir)
        elif os.path.isdir(parent_dir):
            for leftover in os.listdir(parent_dir):
                if leftover.endswith("_index.json"):
                    os.remove(os.path.join(parent_dir, leftover))
            if not os.listdir(parent_dir):
                os.rmdir(parent_dir)


@pytest.mark.slow
@pytest.mark.resource_budget_large
def test_species_hostility_increase_does_not_decrease_combat_engagement_rate():
    with open(SPECIES_RELATIONS_PATH, "r", encoding="utf-8") as f:
        original_content = f.read()

    _cleanup_created_dirs()

    world_repo = WorldRepository("data/worlds")
    scenario_repo = ScenarioRepository("data/scenarios")
    experiment_repo = ExperimentRepository("data/experiments")
    lab_run_repo = LabRunRepository("data/lab_runs")

    scenario_spec = ScenarioSpec(
        schema_version="scenariospec.v1",
        scenario_id=SCENARIO_ID,
        name="Species Hostility Metamorphic Check",
        world_id="unit_faction_tension",
        scenario_type="sandbox",
        intent={"primary_goal": "species_hostility_metamorphic_check"},
        expected_behavior={},
        required_signals={"metrics": [], "events": [], "cognition": []},
    )
    scenario_repo.save_scenario(scenario_spec)

    experiment_spec = ExperimentSpec(
        schema_version="experimentspec.v1",
        experiment_id=EXPERIMENT_ID,
        scenario_id=SCENARIO_ID,
        experiment_type="single_run",
        run={"ticks": TICKS, "seeds": SEEDS, "repeat_count": 1, "max_parallel_runs": 1},
        observability={
            "mode": "STANDARD", "record_events": True,
            "record_metric_windows": True, "record_cognition": False,
        },
        analysis={
            "run_post_analysis": True, "generate_report": True,
            "run_mining": False, "compare_baseline": False,
        },
        retention={"keep_raw_events": True, "keep_reports": True, "max_artifact_mb": 500},
        budgets={"max_runtime_minutes": 60, "max_total_artifact_mb": 2000},
    )
    experiment_repo.save_experiment(experiment_spec)

    try:
        # Baseline variant: no wolf<->human species_relations entries at all.
        with open(SPECIES_RELATIONS_PATH, "w", encoding="utf-8") as f:
            f.write(_strip_wolf_human_entries(original_content))

        baseline_orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
        baseline_orchestrator.run_lab(EXPERIMENT_ID, lab_run_id="species_hostility_baseline")
        baseline_engagements = _count_combat_engagements("species_hostility_baseline")
        baseline_rate = baseline_engagements / (TICKS * len(SEEDS))

        # Compared variant: wolf<->human hostility overwritten to "high" both directions.
        with open(SPECIES_RELATIONS_PATH, "w", encoding="utf-8") as f:
            f.write(_set_wolf_human_high(original_content))

        high_orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
        high_orchestrator.run_lab(EXPERIMENT_ID, lab_run_id="species_hostility_high")
        high_engagements = _count_combat_engagements("species_hostility_high")
        high_rate = high_engagements / (TICKS * len(SEEDS))

        variant_metrics = {
            "baseline": {"combat_engagement_rate": baseline_rate, "run_count": len(SEEDS)},
            "high_hostility": {"combat_engagement_rate": high_rate, "run_count": len(SEEDS)},
        }
        spec = ExpectedRelationshipSpec(
            id="species_hostility_engagement_check",
            type="monotonic_non_decreasing",
            metric="combat_engagement_rate",
            baseline_variant="baseline",
            compared_variant="high_hostility",
        )
        results = MetamorphicRuleEngine.evaluate_rules([spec], variant_metrics)

        assert len(results) == 1
        result = results[0]
        assert not (baseline_rate == 0.0 and high_rate == 0.0), (
            "Degenerate zero/zero engagement rate in both variants -- would indicate the "
            "metric extraction produced a hollow result, not real evidence."
        )
        assert result.status == "PASSED", (
            f"Increasing wolf<->human species hostility decreased combat_engagement_rate: "
            f"baseline={baseline_rate}, high_hostility={high_rate}, message={result.message}"
        )
    finally:
        with open(SPECIES_RELATIONS_PATH, "w", encoding="utf-8") as f:
            f.write(original_content)
        with open(SPECIES_RELATIONS_PATH, "r", encoding="utf-8") as f:
            restored_content = f.read()
        assert restored_content == original_content, (
            "data/content/social/species_relations.yaml was not restored to its authored state "
            "after the metamorphic validation run."
        )
        _cleanup_created_dirs()

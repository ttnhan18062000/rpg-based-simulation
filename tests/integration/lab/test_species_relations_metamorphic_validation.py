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

Rescope (TCK-20261007-SPECIES-HOSTILITY-METAMORPHIC-ENGAGEMENT-CHECK-RED-SINCE-6E7EF56EC, 2026-10-07):
the old 3-seed run on the stock layout was underpowered (it failed by chance about 1 run in 4), and the
lab path was not deterministic at a fixed SHA. Three changes, all test-scoped (pytest monkeypatch), no
src/ or data/ change; the assertion keeps its exact form (pooled high rate >= pooled baseline rate, no
tolerance band):

1. Pinned governor. The lab path builds `Kernel` without a governor, so `Kernel.__init__` takes the
   default `src.engine.governor.ResourceGovernor`, whose mode follows host load (the load sensitivity
   parked under TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2). Unpinned, the same seeds at
   the same SHA gave 115 vs 140 in one run and 122 vs 141 in another. The test swaps in a governor
   pinned to NORMAL with a no-op `force_mode` (as `_PinnedNormalGovernor` in
   tests/integration/campaigns/test_catalog_entity_spawn_wiring.py), which removes host speed from the
   outcome: two runs at one SHA give identical per-seed counts.
2. Contact-rich layout, per rpg-planner's ruling (a) of 2026-10-07: the relation "raising declared
   hostility never lowers engagement" is a claim about pairs that meet, and a run where wolves and
   humans never meet carries no evidence either way. On the stock layout the wolf den
   (70,30,105,70) is about 30 tiles from `hometown` (10,10,40,40), beyond the perception radius of 10
   (Manhattan, ENTITY_TARGET_PERCEPTION_RADIUS), and most seeds never made contact. The test's
   `load_world` override moves only the `wolf_den` region to (41,30,48,40), next to the town, with its
   `wolf_den_nest` place at (44,35); factions, faction-level declarations, populations and the species
   mutation are unchanged and still go through WorldValidator and the compiler. No leash applies (the
   compiler sets no home_position/leash_radius).
3. Sample size. Measured at ae3352361ea77ee3545612d1de3748be19ac321e on 2026-10-07, pinned, contact
   layout, 200 ticks: seeds 301-340 gave a mean per-seed difference (high - baseline) of +14.5, SD
   8.54, SE 1.35, z 10.7, with no negative seed; seeds 301-310 (the fixed list used here) give baseline
   17, high 137, mean +12.0, SD 8.98, SE 2.84, z 4.23. The normal-approximation chance of a false fail
   at the measured effect is far below 1%; 10 seeds also leave margin if the effect halves.

The non-vacuity guard (`baseline > 0` pooled, and at least `MIN_BASELINE_SEEDS_WITH_CONTACT` baseline
seeds with an engagement; measured 4 of 10, guard 4 - 2) is NOT an effect check: it only stops the
assertion from passing vacuously (0 >= 0) if the layout stops producing contact, for example after a
change to spawning or perception semantics.
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
import src.engine.governor as governor_module
from src.core.governance import RuntimeMode

SPECIES_RELATIONS_PATH = "data/content/social/species_relations.yaml"
SCENARIO_ID = "species_hostility_metamorphic_check"
EXPERIMENT_ID = "species_hostility_metamorphic_check_experiment"
SEEDS = list(range(301, 311))  # fixed in advance; see the module docstring for the sizing
TICKS = 200
MIN_BASELINE_SEEDS_WITH_CONTACT = 2  # measured 4 of 10 at ae3352361 (pinned, contact layout), minus 2
CONTACT_WOLF_DEN_BOUNDS = (41, 30, 48, 40)  # next to hometown (10,10,40,40), within perception radius 10
CONTACT_WOLF_DEN_NEST = (44, 35)

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


class _PinnedNormalGovernor(governor_module.ResourceGovernor):
    """Pins NORMAL so the outcome does not depend on host speed (TCK-20260822 load sensitivity)."""

    def _get_indicated_mode(self, profile, signals):
        return RuntimeMode.NORMAL

    def force_mode(self, mode, status, current_tick):
        return None  # the mid-tick wall-clock throttle must not flip the mode either


def _contact_rich_load_world(original_load_world):
    """`WorldRepository.load_world` with the wolf den moved next to the town (ruling (a)); other worlds untouched."""

    def load_world(self, world_id):
        spec = original_load_world(self, world_id)
        if world_id != "unit_faction_tension":
            return spec
        regions = []
        for region in spec.regions:
            if region.id == "wolf_den":
                places = [
                    place.model_copy(update={"position": CONTACT_WOLF_DEN_NEST}) if place.id == "wolf_den_nest" else place
                    for place in region.places
                ]
                region = region.model_copy(update={"bounds": CONTACT_WOLF_DEN_BOUNDS, "places": places})
            regions.append(region)
        assert any(r.id == "wolf_den" for r in regions), "unit_faction_tension no longer has a wolf_den region"
        return spec.model_copy(update={"regions": regions})

    return load_world


def _engagements_per_seed(lab_run_id: str) -> dict:
    counts = {}
    for seed in SEEDS:
        run_id = f"run_{lab_run_id}_seed_{seed}"
        path = os.path.join("data", "lab_runs", lab_run_id, "runs", run_id, "simulation_events.jsonl")
        assert os.path.isfile(path), f"Missing simulation_events.jsonl for {run_id}"
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and json.loads(line).get("event_type") == "combat_engagement_started":
                    count += 1
        counts[seed] = count
    return counts


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
def test_species_hostility_increase_does_not_decrease_combat_engagement_rate(monkeypatch):
    # Test-scoped: Kernel.__init__ imports its default governor from this module lazily, and the lab
    # orchestrator loads its world through WorldRepository.load_world (see the module docstring).
    monkeypatch.setattr(governor_module, "ResourceGovernor", _PinnedNormalGovernor)
    monkeypatch.setattr(WorldRepository, "load_world", _contact_rich_load_world(WorldRepository.load_world))

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
        baseline_per_seed = _engagements_per_seed("species_hostility_baseline")
        baseline_engagements = sum(baseline_per_seed.values())
        baseline_rate = baseline_engagements / (TICKS * len(SEEDS))

        # Compared variant: wolf<->human hostility overwritten to "high" both directions.
        with open(SPECIES_RELATIONS_PATH, "w", encoding="utf-8") as f:
            f.write(_set_wolf_human_high(original_content))

        high_orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
        high_orchestrator.run_lab(EXPERIMENT_ID, lab_run_id="species_hostility_high")
        high_per_seed = _engagements_per_seed("species_hostility_high")
        high_engagements = sum(high_per_seed.values())
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
        print(f"species metamorphic per-seed engagements: baseline={baseline_per_seed} high={high_per_seed}")
        # Non-vacuity guard, not an effect check: the relation is about pairs that meet (ruling (a)).
        seeds_with_contact = sum(1 for count in baseline_per_seed.values() if count > 0)
        assert baseline_engagements > 0 and seeds_with_contact >= MIN_BASELINE_SEEDS_WITH_CONTACT, (
            f"The contact-rich layout no longer produces wolf/human contact in the baseline run "
            f"({seeds_with_contact} of {len(SEEDS)} seeds engaged, per seed {baseline_per_seed}); the assertion "
            f"below would pass vacuously. Re-check the layout override against spawn and perception rules."
        )
        assert not (baseline_rate == 0.0 and high_rate == 0.0), (
            "Degenerate zero/zero engagement rate in both variants -- would indicate the "
            "metric extraction produced a hollow result, not real evidence."
        )
        assert result.status == "PASSED", (
            f"Increasing wolf<->human species hostility decreased combat_engagement_rate: "
            f"baseline={baseline_rate}, high_hostility={high_rate}, message={result.message}; "
            f"per seed baseline={baseline_per_seed}, high={high_per_seed}"
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

"""Metamorphic validation for species hostility: raising declared species hostility never lowers the engagement rate of the pair it governs.

TCK-20260831-RACE-RELATIONS-MATRIX, Step 12; re-pointed by TCK-20261011-SPECIES-HOSTILITY-METAMORPHIC-TEST-USES-A-PAIR-SPECIES-RELATIONS-STILL-GOVERNS.

The pair. Wolves are wild creatures (`hostility.is_wild_creature`, decision 47): appraisal decides whom they fight, and `species_relations` never
reaches them, so a wolf<->human variant would hold trivially (the 'high' variant changes nothing the kernel reads). The relation now uses a pair that
`species_relations` still governs: a town_council human and a merchant_league human of the real `unit_faction_tension` world (two different factions,
the same people-kind species, neutral at faction level). The baseline is the authored file (it has no human<->human row); the compared variant appends a
`human_to_human` row of hostility "high", which `RelationProjectionService.project_relation` escalates to an enemy label for two different factions.

Non-vacuity guard (`_pair_hostility_input`): before the engagement rates are compared, the test asserts that the 'high' variant CHANGES the hostility
input the kernel reads for the pair (the faction-semantics verdict `hostility.faction_hostile` makes: False in the baseline, True in the high variant),
and that neither member is a wild creature. If a later rule takes the pair out of `species_relations`, the test fails loudly instead of passing for
the wrong reason. The hungry-wolf appraisal check lives in its own unit test (tests/unit/engine/test_hungry_wolf_hunts_prey_it_out_bands.py).

Hand-orchestrated, as before: `MutationLabOrchestrator` cannot target content-catalog files, so the test swaps the on-disk
`data/content/social/species_relations.yaml` between the two variants, runs the real world via `ScenarioLabOrchestrator.run_lab()` for each, counts
`combat_engagement_started` events between the two factions' humans from each run's `simulation_events.jsonl`, and calls the real
`MetamorphicRuleEngine.evaluate_rules()`. The governor is pinned to NORMAL (`PinnedNormalGovernor`) so host speed does not decide the outcome. The
assertion keeps its form (pooled high rate >= pooled baseline rate, no tolerance band); the engagement counts per seed are printed.
"""
import json
import os
import shutil
from dataclasses import replace

import pytest

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.lab.repository import ScenarioRepository, ExperimentRepository, LabRunRepository
from src.lab.orchestrator import ScenarioLabOrchestrator
from src.lab.schema import ScenarioSpec, ExperimentSpec, ExpectedRelationshipSpec
from src.lab.metamorphic import MetamorphicRuleEngine
import src.engine.governor as governor_module
from tests.helpers.kernel_pinning import PinnedNormalGovernor

SPECIES_RELATIONS_PATH = "data/content/social/species_relations.yaml"
SCENARIO_ID = "species_hostility_metamorphic_check"
EXPERIMENT_ID = "species_hostility_metamorphic_check_experiment"
GUARD_SEED = 301  # the seed whose compiled entities the input guard reads
SEEDS = list(range(301, 311))  # fixed in advance; see the module docstring for the sizing
TICKS = 200

SCENARIO_DIR = f"data/scenarios/{SCENARIO_ID}"
EXPERIMENT_DIR = f"data/experiments/{EXPERIMENT_ID}"
LAB_RUN_BASELINE = "data/lab_runs/species_hostility_baseline"
LAB_RUN_HIGH = "data/lab_runs/species_hostility_high"


def _set_human_pair_high(content: str) -> str:
    """The 'compared' variant: a human<->human species row of hostility "high" appended. The authored file has no human<->human row, so the baseline is
    the file as authored; the pair it governs is two different factions of the same people-kind species (town_council and merchant_league)."""
    return content.rstrip("\n") + (
        "\n\n"
        '- id: "human_to_human"\n'
        '  source_species: "human"\n'
        '  target_species: "human"\n'
        '  relationship_model: "people_pair"\n'
        "  axes:\n"
        '    hostility: "high"\n'
    )


def _pair_hostility_input(seed: int) -> bool:
    """What the kernel's hostility test reads for the chosen pair: the faction semantics verdict (`hostility.faction_hostile`'s own call) of a
    town_council human toward a merchant_league human, with their species in the context, from the species_relations file as it is on disk now.
    Neither is a wild creature, so species_relations (not appraisal) governs the pair."""
    from src.content_semantics.faction import get_faction_semantics_service, reset_faction_semantics_service
    from src.content_semantics.relation import RelationContext
    from src.engine.hostility import is_wild_creature
    from tests.helpers.scenario import compile_world

    reset_faction_semantics_service()
    state = compile_world("unit_faction_tension", seed)
    by_faction = {}
    for ent in state.entities.values():
        props = ent.identity.properties or {}
        if props.get("species_id") == "human":
            by_faction.setdefault(props.get("faction_id"), ent)
    council, merchant = by_faction["town_council"], by_faction["merchant_league"]
    assert not is_wild_creature(council) and not is_wild_creature(merchant), "the chosen pair must not be wild creatures (appraisal would govern it)"
    context = RelationContext(distance=3.0, combat_engaged=False, source_species="human", target_species="human")
    return bool(get_faction_semantics_service().is_hostile_compat("town_council", "merchant_league", context))


def _is_pair_engagement(event: dict) -> bool:
    """True for an engagement between a town_council human and a merchant_league human, in either direction (wolf engagements are not counted)."""
    payload = event.get("payload") or {}
    pair = set()
    for key in ("attacker_snapshot", "defender_snapshot"):
        snap = payload.get(key) or {}
        pair.add((snap.get("species_id"), snap.get("faction_id")))
    return pair == {("human", "town_council"), ("human", "merchant_league")}


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
                if not line:
                    continue
                event = json.loads(line)
                if event.get("event_type") == "combat_engagement_started" and _is_pair_engagement(event):
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
    monkeypatch.setattr(governor_module, "ResourceGovernor", PinnedNormalGovernor)

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
        # Baseline variant: the file as authored (no human<->human row).
        baseline_hostile = _pair_hostility_input(GUARD_SEED)

        baseline_orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
        baseline_orchestrator.run_lab(EXPERIMENT_ID, lab_run_id="species_hostility_baseline")
        baseline_per_seed = _engagements_per_seed("species_hostility_baseline")
        baseline_engagements = sum(baseline_per_seed.values())
        baseline_rate = baseline_engagements / (TICKS * len(SEEDS))

        # Compared variant: a human<->human row of hostility "high".
        with open(SPECIES_RELATIONS_PATH, "w", encoding="utf-8") as f:
            f.write(_set_human_pair_high(original_content))
        high_hostile = _pair_hostility_input(GUARD_SEED)
        # Non-vacuity guard: the 'high' variant must change the hostility input the kernel reads for this pair.
        assert (baseline_hostile, high_hostile) == (False, True), (
            f"The 'high' variant no longer changes the hostility input for the town_council/merchant_league human pair "
            f"(baseline {baseline_hostile}, high {high_hostile}): species_relations does not govern this pair any more, so the "
            f"engagement comparison below would hold for the wrong reason. Pick a pair species_relations still governs."
        )

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
        # The input guard above is the non-vacuity guard. This only stops a hollow metric (no engagement of the pair in either variant).
        assert not (baseline_rate == 0.0 and high_rate == 0.0), (
            "Zero engagements of the pair in both variants even though the hostility input differs: the pair never meets in this layout, "
            "so the comparison carries no evidence. Re-check spawn and perception for town_council and merchant_league."
        )
        assert result.status == "PASSED", (
            f"Increasing human<->human species hostility decreased combat_engagement_rate: "
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

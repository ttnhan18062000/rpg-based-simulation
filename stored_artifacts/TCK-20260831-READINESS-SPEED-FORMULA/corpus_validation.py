"""Throwaway pre/post-code corpus validation for TCK-20260831-READINESS-SPEED-FORMULA, Step 6.

Not a permanent tests/ file -- a pre-change/post-change code split cannot be a permanent
CI-running test (matches METAMORPHIC-LAB-PILOT / RACE-RELATIONS-MATRIX precedent).

Design (see plan.md Step 6 for full reasoning -- this is the resolved design, not re-derived
here):
  - Variant axis is PRE/POST CODE, not intra-run agility cohort-split. An intra-run
    elder-vs-non-elder comparison would conflate LifeStage.ELDER's pre-existing
    "combat": 0.5 goal-multiplier confound with the new readiness_speed effect. Pre/post-code
    holds AI behavior identical across both runs -- the confound cancels out.
  - Metric window restricted to tick >= 7000 (the earliest an entity that started at
    age_ticks=0 can be ELDER, per LifeStageService.get_stage_for_age()), because the only real,
    durable, population-scale agility divergence from the default (5) in any corpus run today is
    the elder cohort's one-time agility_delta=-int(attrs.agility*0.3) decay
    (compute_elder_attribute_update(), src/domains/demographics/cohort.py:107-109). Before an
    entity exists in that window, both variants are bit-identical (agility=5 either way).
  - Metric: elder_window_damage_rate = count(event_type == "combat_damage", tick >= 7000) / 2500
    (window width), averaged across 3 seeds, for each variant.
  - Relationship: monotonic_non_increasing. The formula is symmetric (Step 1), but the only real
    corpus population it currently affects moves agility DOWN (elder decay, 5 -> 4), never up --
    so the real, expected corpus-observable direction here is a decrease from baseline
    (pre-code, flat readiness_speed=10.0 for everyone) to compared (post-code, elder entities
    regen readiness 10% slower -> fewer readiness-gated attacks land in the window).
  - observability.mode is pinned explicitly to "STANDARD" (-> ObservabilityMode.NORMAL). Left
    unset it silently falls back to LIGHT; "LONG_RUN" is the other, equally wrong, gated mode.
    Both LIGHT and LONG_RUN suppress non-lethal combat_damage events
    (src/observability/event_shapers.py:224), which is exactly what this script's metric
    depends on (routine, non-lethal damage ticks, not just kills). This was an explicit
    architecture-review finding on this plan -- do not regress it.

Variant execution order (both variants run against the SAME on-disk world/scenario/experiment
specs and the SAME 3 seeds -- only the src/ code differs):
  1. COMPARED variant runs first, against the code currently in the working tree (Steps 1-2
     already landed at the point this script runs).
  2. `git stash push` on exactly the two files Steps 1-2 touched
     (src/progression/leveling.py, src/engine/apply.py) reverts them to HEAD (pre-ticket,
     i.e. the BASELINE code) without touching any other uncommitted change (new tests, docs).
  3. BASELINE variant runs against that reverted code.
  4. `git stash pop` restores the compared (fixed) code so the working tree is left exactly as
     it was before this script ran.
"""
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.getcwd())

from src.worldbuilding.repository import WorldRepository
from src.lab.repository import ScenarioRepository, ExperimentRepository, LabRunRepository
from src.lab.orchestrator import ScenarioLabOrchestrator
from src.lab.schema import ScenarioSpec, ExperimentSpec, ExpectedRelationshipSpec
from src.lab.metamorphic import MetamorphicRuleEngine

WORLD_ID = "unit_faction_tension"
SCENARIO_ID = "readiness_speed_elder_window_check"
EXPERIMENT_ID = "readiness_speed_elder_window_check_experiment"
SEEDS = [301, 302, 303]
TICKS = 9500
WINDOW_START = 7000
WINDOW_WIDTH = TICKS - WINDOW_START  # 2500

SCENARIO_DIR = f"data/scenarios/{SCENARIO_ID}"
EXPERIMENT_DIR = f"data/experiments/{EXPERIMENT_ID}"
LAB_RUN_BASELINE = "data/lab_runs/readiness_speed_baseline"
LAB_RUN_COMPARED = "data/lab_runs/readiness_speed_compared"

STASH_FILES = ["src/progression/leveling.py", "src/engine/apply.py"]


def _cleanup_created_dirs():
    for d in (SCENARIO_DIR, EXPERIMENT_DIR, LAB_RUN_BASELINE, LAB_RUN_COMPARED):
        if os.path.exists(d):
            shutil.rmtree(d)
    for parent_dir in ("data/scenarios", "data/experiments", "data/lab_runs"):
        if os.path.isdir(parent_dir) and not os.listdir(parent_dir):
            os.rmdir(parent_dir)
        elif os.path.isdir(parent_dir):
            for leftover in os.listdir(parent_dir):
                if leftover.endswith("_index.json"):
                    os.remove(os.path.join(parent_dir, leftover))
            if not os.listdir(parent_dir):
                os.rmdir(parent_dir)


def _elder_window_damage_rate(lab_run_id: str) -> float:
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
                if event.get("event_type") == "combat_damage" and event.get("tick", -1) >= WINDOW_START:
                    total += 1
    return (total / WINDOW_WIDTH) / len(SEEDS)


def _run_variant(lab_run_id: str) -> float:
    world_repo = WorldRepository("data/worlds")
    scenario_repo = ScenarioRepository("data/scenarios")
    experiment_repo = ExperimentRepository("data/experiments")
    lab_run_repo = LabRunRepository("data/lab_runs")
    orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
    orchestrator.run_lab(EXPERIMENT_ID, lab_run_id=lab_run_id, confirm=True)
    return _elder_window_damage_rate(lab_run_id)


def main():
    _cleanup_created_dirs()

    scenario_repo = ScenarioRepository("data/scenarios")
    experiment_repo = ExperimentRepository("data/experiments")

    scenario_spec = ScenarioSpec(
        schema_version="scenariospec.v1",
        scenario_id=SCENARIO_ID,
        name="Readiness Speed Elder Window Check",
        world_id=WORLD_ID,
        scenario_type="sandbox",
        intent={"primary_goal": "readiness_speed_elder_window_check"},
        expected_behavior={},
        required_signals={"metrics": [], "events": [], "cognition": []},
    )
    scenario_repo.save_scenario(scenario_spec)

    obs_spec = {
        "mode": "STANDARD", "record_events": True,
        "record_metric_windows": True, "record_cognition": False,
    }
    assert obs_spec["mode"] == "STANDARD", "observability.mode must be pinned to STANDARD"

    experiment_spec = ExperimentSpec(
        schema_version="experimentspec.v1",
        experiment_id=EXPERIMENT_ID,
        scenario_id=SCENARIO_ID,
        experiment_type="single_run",
        run={"ticks": TICKS, "seeds": SEEDS, "repeat_count": 1, "max_parallel_runs": 1},
        observability=obs_spec,
        analysis={
            "run_post_analysis": True, "generate_report": True,
            "run_mining": False, "compare_baseline": False,
        },
        retention={"keep_raw_events": True, "keep_reports": True, "max_artifact_mb": 500},
        budgets={"max_runtime_minutes": 60, "max_total_artifact_mb": 2000},
    )
    experiment_repo.save_experiment(experiment_spec)

    # Literal, script-level confirmation of the observability mode pin -- checked here, not
    # just trusted from a printed PASSED result (architecture-review requirement).
    saved_experiment = experiment_repo.load_experiment(EXPERIMENT_ID)
    assert saved_experiment.observability.mode == "STANDARD", (
        f"observability.mode resolved to {saved_experiment.observability.mode!r}, not 'STANDARD' "
        "-- would silently gate off non-lethal combat_damage events."
    )
    from src.lab.orchestrator import ScenarioLabOrchestrator as _SLO
    from src.observability.config import ObservabilityMode
    resolved_mode = _SLO._resolve_obs_mode(saved_experiment.observability.mode)
    assert resolved_mode == ObservabilityMode.NORMAL, (
        f"_resolve_obs_mode('STANDARD') resolved to {resolved_mode}, expected ObservabilityMode.NORMAL"
    )
    print(f"[confirmed] observability.mode == 'STANDARD' -> resolves to {resolved_mode}")

    try:
        # 1. COMPARED variant: current working-tree code (Steps 1-2 already landed).
        compared_rate = _run_variant("readiness_speed_compared")
        print(f"[compared] elder_window_damage_rate = {compared_rate}")

        # 2. Revert Steps 1-2's two files to HEAD (pre-ticket / baseline code) only.
        subprocess.run(
            ["git", "stash", "push", "-m", "readiness_speed corpus baseline stash", "--"] + STASH_FILES,
            check=True,
        )
        try:
            baseline_rate = _run_variant("readiness_speed_baseline")
            print(f"[baseline] elder_window_damage_rate = {baseline_rate}")
        finally:
            # 3. Restore the compared (fixed) code unconditionally.
            subprocess.run(["git", "stash", "pop"], check=True)

        variant_metrics = {
            "baseline": {"elder_window_damage_rate": baseline_rate, "run_count": len(SEEDS)},
            "compared": {"elder_window_damage_rate": compared_rate, "run_count": len(SEEDS)},
        }
        spec = ExpectedRelationshipSpec(
            id="readiness_speed_elder_window_check",
            type="monotonic_non_increasing",
            metric="elder_window_damage_rate",
            baseline_variant="baseline",
            compared_variant="compared",
        )
        results = MetamorphicRuleEngine.evaluate_rules([spec], variant_metrics)
        result = results[0]

        degenerate = (baseline_rate == 0.0 and compared_rate == 0.0)
        print(f"[result] status={result.status} message={getattr(result, 'message', None)}")
        print(f"[result] degenerate_zero_zero={degenerate}")

        if degenerate:
            print("DEGENERATE RESULT -- baseline and compared both zero. Not accepting as PASSED "
                  "evidence without widening the window/run length per plan.md Step 6 point 6.")
            sys.exit(2)

        assert result.status == "PASSED", (
            f"readiness_speed elder-window check FAILED: baseline={baseline_rate}, "
            f"compared={compared_rate}, message={result.message}"
        )
        print("PASSED")
    finally:
        _cleanup_created_dirs()


if __name__ == "__main__":
    main()

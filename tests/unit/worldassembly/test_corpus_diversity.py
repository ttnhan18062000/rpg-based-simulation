"""Corpus-diversity regression guards for TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS.

These tests protect the shape/content diversity this ticket added to the SimQ
calibration world corpus:

1. ``test_entity_count_band`` — the 5 newly-anchored worlds keep the entity-count
   shape they were chosen to fill (docs/simulation_quality/eval_matrix_results.md).
2. ``test_population_stability`` — permanent regression guard for the early-tick
   population-collapse bug (Finding 3, stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-
   WORLD-CORPUS/investigation.md): every world must keep >=60% of its starting
   entity count alive at every 50-tick checkpoint through 300 ticks.
3. ``test_hazard_kind_completeness`` — every non-zero-hazard region must either
   declare ``hazard_kind`` or have every populating archetype's faction declare a
   matching ``hazard_immunities`` entry (the native-endurance mechanism from
   TCK-20260701-HAZARD-NATIVE-IMMUNITY, docs/mechanics/05_world_evolution.md §3).
4. ``test_module_family_anchored`` — the 10 previously-never-anchored world
   modules this ticket brought into the anchored corpus stay anchored, leaving
   only ``moon_cult_ruins`` outside any anchored world's module list.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

pytestmark = pytest.mark.worldassembly

REPO_ROOT = Path(__file__).resolve().parents[3]
WORLDS_ROOT = REPO_ROOT / "data" / "worlds"
FIXTURE_PATH = REPO_ROOT / "tests" / "simulation_quality" / "fixtures" / "grade_anchors.json"

# The 5 worlds this ticket anchored, and the entity-count band each was chosen to
# fill (docs/simulation_quality/eval_matrix_results.md /
# stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/plan.md Step 4 table).
# (low, high) inclusive; high=None means open-ended (">50").
ANCHORED_WORLD_BANDS: dict[str, tuple[int, int | None]] = {
    "frontier_extended": (51, None),
    "frontier_living_world": (35, 50),
    "wilderness_survival": (0, 19),
    "highland_traverse": (0, 19),
    "swamp_border_world": (20, 35),
}

POPULATION_STABILITY_WORLDS = list(ANCHORED_WORLD_BANDS.keys())

# The 10 modules Step 4 brought into the anchored corpus for the first time.
# ``moon_cult_ruins`` is the only module deliberately left unanchored (out of
# scope — see plan.md Step 4 "Scope boundary").
NEWLY_ANCHORED_MODULES = [
    "forest_warden_grove",
    "orc_clan_territory",
    "undead_battlefield",
    "survivor_camp_shelter",
    "forest_deep_ecology",
    "mountain_pass",
    "river_crossing",
    "nomadic_herd",
    "settled_quarter",
    "sunken_swamp_border",
]
STILL_UNANCHORED_MODULE = "moon_cult_ruins"


def _load_compile_report(world_id: str) -> dict[str, Any]:
    path = WORLDS_ROOT / world_id / "world_compile_report.json"
    if not path.exists():
        pytest.skip(f"No compile report for '{world_id}' at {path} — run resolve+compile first.")
    return json.loads(path.read_text())


def _load_resolved_spec(world_id: str) -> dict[str, Any]:
    path = WORLDS_ROOT / world_id / "resolved" / "world.resolved.yaml"
    if not path.exists():
        pytest.skip(f"No resolved spec for '{world_id}' at {path} — run resolve first.")
    return yaml.safe_load(path.read_text())


def _world_modules(world_id: str) -> list[str]:
    """Return the list of module ids a world's world.yaml composes.

    Handles both authoring shorthands seen in data/worlds/*/world.yaml:
    a flat ``modules: [str, ...]`` list, or a ``module_refs: [{module_id: str}, ...]``
    list.
    """
    raw = yaml.safe_load((WORLDS_ROOT / world_id / "world.yaml").read_text())
    if "modules" in raw:
        return list(raw["modules"])
    return [ref["module_id"] for ref in raw.get("module_refs", [])]


def _anchored_world_ids() -> set[str]:
    """Every world_id with >=1 entry in grade_anchors.json (strip _seed{N}_{ticks}t)."""
    anchors = json.loads(FIXTURE_PATH.read_text())
    world_ids = set()
    for key in anchors:
        if key.startswith("_"):
            continue
        # run_key format: "{world_id}_seed{N}_{ticks}t"
        base = key.rsplit("_seed", 1)[0]
        world_ids.add(base)
    return world_ids


# ---------------------------------------------------------------------------
# 1. Entity-count band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("world_id", list(ANCHORED_WORLD_BANDS.keys()))
def test_entity_count_band(world_id: str) -> None:
    report = _load_compile_report(world_id)
    entity_count = report["entity_count"]
    low, high = ANCHORED_WORLD_BANDS[world_id]
    assert entity_count >= low, (
        f"{world_id}: entity_count={entity_count} fell below its chosen band floor {low}"
    )
    if high is not None:
        assert entity_count <= high, (
            f"{world_id}: entity_count={entity_count} exceeded its chosen band ceiling {high}"
        )


# ---------------------------------------------------------------------------
# 2. Population stability (>=60% alive floor, 300 ticks, seed 42)
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.parametrize("world_id", POPULATION_STABILITY_WORLDS)
def test_population_stability(world_id: str) -> None:
    """Regression guard for Finding 3's early-tick collapse (investigation.md).

    Drives Kernel.tick_once() for 300 ticks at seed 42, sampling alive_count at
    every 50-tick checkpoint. Floor: alive_count >= 60% of the starting
    entity_count at every checkpoint.
    """
    from src.worldbuilding.repository import WorldRepository
    from src.worldbuilding.compiler import WorldCompiler
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG
    from src.config.profiles import PROD_SMALL

    seed = 42
    repo = WorldRepository(str(WORLDS_ROOT))
    spec = repo.load_world(world_id)
    state, report = WorldCompiler.compile(spec, seed)
    starting = report["entity_count"]
    floor = 0.6 * starting

    rng = DeterministicRNG(seed)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=rng, flags={"no_frame_pacing": True})
    try:
        for tick in range(1, 301):
            kernel.tick_once()
            if tick % 50 == 0:
                alive = sum(1 for e in kernel._state.entities.values() if e.combat.alive)
                assert alive >= floor, (
                    f"{world_id}: population collapsed at tick {tick} — "
                    f"alive={alive}/{starting} ({alive / starting:.1%}), floor is 60% ({floor:.1f})"
                )
    finally:
        try:
            kernel.shutdown()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 3. Hazard-kind completeness
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("world_id", list(ANCHORED_WORLD_BANDS.keys()))
def test_hazard_kind_completeness(world_id: str) -> None:
    """Every region with hazard_level > 0 must declare hazard_kind.

    This is the native-endurance mechanism's prerequisite (TCK-20260701-HAZARD-
    NATIVE-IMMUNITY): without hazard_kind, no faction's hazard_immunities can ever
    match, and hazard-drain applies unconditionally, reproducing Finding 3's
    population-collapse pattern.
    """
    spec = _load_resolved_spec(world_id)
    for region in spec.get("regions", []):
        hazard_level = region.get("hazard_level", 0.0) or 0.0
        if hazard_level > 0:
            assert region.get("hazard_kind"), (
                f"{world_id}: region '{region.get('id')}' has hazard_level={hazard_level} "
                f"but no hazard_kind — native/immune populations would take unconditional drain."
            )


# ---------------------------------------------------------------------------
# 4. Module-family anchoring
# ---------------------------------------------------------------------------

def test_module_family_anchored() -> None:
    anchored_worlds = _anchored_world_ids()
    covered_modules: set[str] = set()
    for world_id in anchored_worlds:
        covered_modules.update(_world_modules(world_id))

    for module_id in NEWLY_ANCHORED_MODULES:
        assert module_id in covered_modules, (
            f"module '{module_id}' should now be anchored (via one of {sorted(anchored_worlds)}) "
            "but does not appear in any anchored world's module list."
        )

    assert STILL_UNANCHORED_MODULE not in covered_modules, (
        f"'{STILL_UNANCHORED_MODULE}' was expected to remain the sole unanchored module "
        "(see plan.md Step 4 scope boundary) — it now appears in an anchored world's "
        "module list, so this test's exclusion list is stale and should be updated."
    )

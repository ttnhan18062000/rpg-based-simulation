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
    # new — TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS: 3 stress-tier worlds filling the
    # corpus's named scale-diversity gaps (docs/simulation_quality/corpus_tier_taxonomy.md).
    "crowded_frontier": (35, 50),
    "resource_dense_basin": (20, 35),
    "frontier_marches": (51, None),
}

# unit_faction_tension / unit_information_source (TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-
# FACTION-INFO) are unit-tier isolation worlds, not part of the 5-world ANCHORED_WORLD_BANDS
# regression-tier band set — they are added only to the population-stability guard, per
# that ticket's plan.md Step 5 (do not fork a new test file; do not add them to
# ANCHORED_WORLD_BANDS, whose entity-count-band/hazard-kind tests are out of this ticket's scope).
#
# dungeon_crawl / sandbox_world / generated_frontier_3_42 / urban_political
# (TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP) were compiled corpus worlds that
# never carried population-stability coverage at all — not anchored-tier (ANCHORED_WORLD_BANDS),
# not unit-tier. Added here for the same reason: out of scope to fold them into
# ANCHORED_WORLD_BANDS (entity-count-band anchoring is a separate concern).
POPULATION_STABILITY_WORLDS = list(ANCHORED_WORLD_BANDS.keys()) + [
    "unit_faction_tension",
    "unit_information_source",
    "unit_selfmodel_pilot",
    "hero_guild_routing",
    "dungeon_crawl",
    "sandbox_world",
    "generated_frontier_3_42",
    "urban_political",
]

# All 10 worlds' distinct-populated-faction counts, verified against
# staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md §2 and re-confirmed by
# TCK-20260704-SIMQ-CORPUS-SCALE-METRIC's own recompile cross-check (investigation.md §3).
EXPECTED_DISTINCT_POPULATED_FACTIONS: dict[str, int] = {
    "wilderness_survival": 2,
    "sandbox_world": 3,
    "highland_traverse": 3,
    "urban_political": 4,
    "dungeon_crawl": 4,
    "swamp_border_world": 4,
    "simq_routing_test": 5,
    "frontier_living_world": 6,
    "generated_frontier_3_42": 7,
    "frontier_extended": 9,
    # new — TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS (re-confirmed against each world's own
    # world_compile_report.json, not eyeballed from world.yaml).
    "crowded_frontier": 6,
    "resource_dense_basin": 4,
    "frontier_marches": 9,
}

# The 10 modules Step 4 (of the corpus-uplift ticket this constant originates from) brought
# into the anchored corpus for the first time. ``moon_cult_ruins`` was deliberately left
# unanchored at that time (out of that ticket's scope — see plan.md Step 4 "Scope boundary")
# because it was unique to generated_frontier_3_42, which had no grade_anchors.json entries of
# its own yet. TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS anchored that world for the
# first time, which anchors moon_cult_ruins as a side effect — it is now included below instead
# of tracked as the sole holdout. No module in the corpus remains unanchored as of that ticket.
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
    "moon_cult_ruins",
]

# Genuine pre-existing population-collapse defects surfaced by adding coverage for these worlds
# (TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP is coverage-only and out of scope for the
# content/config fix) — root-cause fix tracked separately at
# TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE. Remove each entry once that ticket lands its fix.
KNOWN_POPULATION_COLLAPSE_WORLDS: dict[str, str] = {
    "dungeon_crawl": (
        "alive=14/32 (43.8%) at tick 50, floor 60% (19.2) — early-tick collapse "
        "(TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE)"
    ),
    "urban_political": (
        "alive=17/30 (56.7%) at tick 300, floor 60% (18.0) — late-tick erosion "
        "(TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE)"
    ),
}

# Same population-stability gap (TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP) also
# left test_hazard_kind_completeness's coverage at just the 8 ANCHORED_WORLD_BANDS worlds. This
# list is deliberately kept separate from ANCHORED_WORLD_BANDS — folding these 4 worlds into
# ANCHORED_WORLD_BANDS would also pull them into test_entity_count_band's entity-count-band
# anchoring, which is out of this ticket's scope.
HAZARD_KIND_COMPLETENESS_WORLDS = list(ANCHORED_WORLD_BANDS.keys()) + [
    "dungeon_crawl",
    "sandbox_world",
    "generated_frontier_3_42",
    "urban_political",
]


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
# 1b. Distinct populated factions (TCK-20260704-SIMQ-CORPUS-SCALE-METRIC)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "world_id,expected", list(EXPECTED_DISTINCT_POPULATED_FACTIONS.items())
)
def test_distinct_populated_factions(world_id: str, expected: int) -> None:
    report = _load_compile_report(world_id)
    assert "distinct_populated_factions" in report, (
        f"{world_id}: world_compile_report.json missing 'distinct_populated_factions' — "
        "recompile with the updated WorldCompiler."
    )
    assert report["distinct_populated_factions"] == expected, (
        f"{world_id}: distinct_populated_factions={report['distinct_populated_factions']} "
        f"!= expected {expected} (staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/"
        "investigation.md §2)"
    )


# ---------------------------------------------------------------------------
# 2. Population stability (>=60% alive floor, 300 ticks, seed 42)
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.parametrize(
    "world_id",
    [
        pytest.param(
            world_id,
            marks=pytest.mark.xfail(
                strict=False, reason=KNOWN_POPULATION_COLLAPSE_WORLDS[world_id]
            ),
        )
        if world_id in KNOWN_POPULATION_COLLAPSE_WORLDS
        else world_id
        for world_id in POPULATION_STABILITY_WORLDS
    ],
)
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

@pytest.mark.parametrize("world_id", HAZARD_KIND_COMPLETENESS_WORLDS)
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

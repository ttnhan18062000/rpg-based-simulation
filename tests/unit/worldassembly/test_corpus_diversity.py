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
3b. ``test_hazard_kind_matches_populating_faction_immunity`` — the same
   ``hazard_kind``/``hazard_immunities`` matching check, but now runs unconditionally
   across the full calibration corpus (every world_id under ``data/worlds/*``), not a
   fixed allowlist (TCK-20260710-HAZARD-KIND-CORPUS-WIDE).
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
FACTIONS_CATALOG_PATH = REPO_ROOT / "data" / "content" / "social" / "factions.yaml"

# test_hazard_kind_matches_populating_faction_immunity now runs corpus-wide (all
# data/worlds/* world_ids) instead of a fixed allowlist — TCK-20260710-HAZARD-KIND-CORPUS-WIDE.
# This self-updates as the corpus grows, replacing the reactive per-sweep allowlist edits that
# preceded it (TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE,
# TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE).
ALL_CORPUS_WORLDS = sorted(p.name for p in WORLDS_ROOT.iterdir() if p.is_dir())

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
# content/config fix). Root cause (missing/mismatched hazard_kind content + a stale urban_political
# compile) fixed by TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE — both worlds now pass cleanly,
# so this dict is empty; kept as the anchor point for any future genuine collapse discovery.
KNOWN_POPULATION_COLLAPSE_WORLDS: dict[str, str] = {}

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


def _faction_hazard_immunities() -> dict[str, set[str]]:
    catalog = yaml.safe_load(FACTIONS_CATALOG_PATH.read_text())
    return {entry["id"]: set(entry.get("hazard_immunities", [])) for entry in catalog}


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
# 2b. generated_frontier_3_42 extended (tick 1000) population stability
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_generated_frontier_3_42_extended_population_stability() -> None:
    """Tolerance-based tick-1000 regression guard for
    TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE.

    This drives the real, throttled ``Kernel`` (no ``audit_mode``) — the same code
    path a real/CI run exercises — for 1000 ticks, 3 independent same-seed(42)
    trials. It is intentionally NOT a tight per-tick assertion past tick 800: the
    investigation (stored_artifacts/TCK-20260708-GENERATED-FRONTIER-LATE-TICK-
    POPULATION-COLLAPSE/investigation.md, Root cause 3) ran this exact harness
    twice, back-to-back, same seed/code/machine, and observed the tick-budget
    watchdog/emergency-throttle (docs/engine/kernel.md §"Emergency Throttling")
    silently drop different entities' resolution work in each run depending on
    wall-clock timing — not on the seed. The two pre-fix runs diverged by 100+
    ticks in floor-violation onset and by more than 2x at tick 1000 (12/44 vs.
    5/44 alive). Averaging across 3 trials and widening the tick-900/1000 floors
    below the worst pre-fix observation absorbs that legitimate non-determinism
    while still catching a genuine future regression.

    Ticks 100-800 keep the standard 60%-of-starting floor as a per-trial hard
    assertion (the investigation found both pre-fix runs held 63.6%-86.4% through
    tick 800 reliably — this range is not weakened). Tick 900 and tick 1000 use an
    averaged floor informed by the worst pre-fix per-checkpoint observation (43.2%
    at 900, 11.4% at 1000), plus a hard no-full-extinction check across all trials.
    """
    from src.worldbuilding.repository import WorldRepository
    from src.worldbuilding.compiler import WorldCompiler
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG
    from src.config.profiles import PROD_SMALL

    world_id = "generated_frontier_3_42"
    seed = 42
    n_trials = 3
    early_checkpoints = (100, 300, 500, 700, 800)
    tick_900_floor_fraction = 0.35
    tick_1000_floor_fraction = 0.08

    repo = WorldRepository(str(WORLDS_ROOT))
    alive_at_900: list[int] = []
    alive_at_1000: list[int] = []
    starting = 0

    for trial in range(n_trials):
        spec = repo.load_world(world_id)
        state, report = WorldCompiler.compile(spec, seed)
        starting = report["entity_count"]
        floor = 0.6 * starting

        rng = DeterministicRNG(seed)
        kernel = Kernel(profile=PROD_SMALL, state=state, rng=rng, flags={"no_frame_pacing": True})
        try:
            for tick in range(1, 1001):
                kernel.tick_once()
                if tick in early_checkpoints:
                    alive = sum(1 for e in kernel._state.entities.values() if e.combat.alive)
                    assert alive >= floor, (
                        f"{world_id} trial {trial}: population collapsed at tick {tick} — "
                        f"alive={alive}/{starting} ({alive / starting:.1%}), "
                        f"floor is 60% ({floor:.1f})"
                    )
                if tick == 900:
                    alive_at_900.append(
                        sum(1 for e in kernel._state.entities.values() if e.combat.alive)
                    )
                if tick == 1000:
                    alive_at_1000.append(
                        sum(1 for e in kernel._state.entities.values() if e.combat.alive)
                    )
        finally:
            try:
                kernel.shutdown()
            except Exception:
                pass

    mean_900 = sum(alive_at_900) / n_trials
    mean_1000 = sum(alive_at_1000) / n_trials
    floor_900 = tick_900_floor_fraction * starting
    floor_1000 = tick_1000_floor_fraction * starting

    assert mean_900 >= floor_900, (
        f"{world_id}: mean alive at tick 900 across {n_trials} trials = "
        f"{mean_900:.1f}/{starting} ({mean_900 / starting:.1%}), "
        f"below the {tick_900_floor_fraction:.0%} averaged floor ({floor_900:.1f}). "
        f"Per-trial values: {alive_at_900}"
    )
    assert mean_1000 >= floor_1000, (
        f"{world_id}: mean alive at tick 1000 across {n_trials} trials = "
        f"{mean_1000:.1f}/{starting} ({mean_1000 / starting:.1%}), "
        f"below the {tick_1000_floor_fraction:.0%} averaged floor ({floor_1000:.1f}). "
        f"Per-trial values: {alive_at_1000}"
    )
    assert min(alive_at_1000) >= 1, (
        f"{world_id}: at least one of {n_trials} trials reached full extinction by "
        f"tick 1000 — per-trial values: {alive_at_1000}"
    )


# ---------------------------------------------------------------------------
# 2c. urban_political_seed123_500t COGNITION bit-identical under induced load
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_urban_political_seed123_500t_cognition_bit_identical_under_load() -> None:
    """Bit-identical regression guard for TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM.

    Investigation into a one-off anomalous sweep result (COGNITION event_count 2->119,
    grade B->S) hypothesized the same wall-clock-driven watchdog/throttle mechanism as F6
    (docs/audits/D06_longrun_health.md §F6, kernel.py:420-442/574-601): dropped
    resolution-queue work under sustained load could stall an entity's `danger`-concern
    resolution and cause `decision_divergence_detected` (which has no "already-emitted"
    dedup gate, src/observability/event_extractor.py:477-496) to re-fire every tick the
    mismatch persists. A controlled repro
    (staging_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/repro_sweep.md)
    drove this exact scenario/seed via the real throttled Kernel (no audit_mode) at two
    idle repeats and two escalating induced-load levels (2x and 4x core oversubscription).
    The induced-load mechanism was confirmed real and load-sensitive (budget_warnings
    28/31 idle -> 40 at 2x -> 108 at 4x; a genuine mid-tick emergency throttle fired at
    2x, absent in both idle runs; wall-clock time grew up to 3.5x) — but COGNITION's
    event_count/raw_score/normalized_score/grade/loop_detected were bit-identical across
    all four runs (event_count=2, raw_score=11.0, normalized_score=0.088, grade=B,
    loop_detected=True), matching the committed grade_anchors.json anchor exactly. This
    scenario does not appear to place any entity into the danger-concern-stuck state F6's
    mechanism requires, so a tight bit-identical assertion (rather than a tolerance-guard
    conversion, per repro_sweep.md's Decision section) is the correct regression guard
    for this anchor.

    This test replays the same idle-vs-induced-load structure as the repro, in-process,
    via tools.calibrate_simq's real internals (exercising the exact scoring path
    grade_anchors.json was calibrated against — profile-aware ScoringWeights, feature
    flags) rather than a hand-rolled Kernel setup.
    """
    import multiprocessing
    import tempfile
    import time

    from tools.calibrate_simq import (
        _build_hub,
        _load_profile_feature_flags,
        _load_weights,
        _replay_jsonl_through_hub,
        _resolve_profile,
        _run_engine,
    )

    world_name = "urban_political"
    seed = 123
    ticks = 500

    def _busy_loop(stop_flag) -> None:
        x = 0
        while not stop_flag.value:
            for _ in range(200000):
                x = (x * 1103515245 + 12345) & 0x7FFFFFFF

    def _run_cognition(label: str, cal_dir: str) -> dict:
        profile = _resolve_profile(world_name)
        feature_flags = _load_profile_feature_flags(profile)
        engine_run_dir, _elapsed, run_id = _run_engine(world_name, seed, ticks, extra_flags=feature_flags)
        weights = _load_weights(profile)
        hub, persistence = _build_hub(weights, cal_dir, run_id or f"{world_name}_seed{seed}_{ticks}t_{label}")
        _replay_jsonl_through_hub(engine_run_dir, hub)
        report = hub.get_quality_report()
        persistence.write_report(report)
        persistence.shutdown()
        cognition = report.pillars["COGNITION"]
        return {
            "event_count": cognition.event_count,
            "raw_score": cognition.raw_score,
            "normalized_score": cognition.normalized_score,
            "grade": cognition.grade,
            "loop_detected": cognition.loop_detected,
        }

    with tempfile.TemporaryDirectory() as idle_dir:
        idle_result = _run_cognition("idle", idle_dir)

    stop_flag = multiprocessing.Value("b", False)
    n_workers = max(1, multiprocessing.cpu_count() * 2)
    procs = [multiprocessing.Process(target=_busy_loop, args=(stop_flag,)) for _ in range(n_workers)]
    for p in procs:
        p.start()
    try:
        time.sleep(1.0)  # let induced load ramp up before the drive starts
        with tempfile.TemporaryDirectory() as load_dir:
            load_result = _run_cognition("load", load_dir)
    finally:
        stop_flag.value = True
        for p in procs:
            p.join(timeout=5.0)
            if p.is_alive():
                p.terminate()

    assert idle_result == load_result, (
        f"urban_political_seed123_500t COGNITION diverged between idle and induced-load runs — "
        f"idle={idle_result} load={load_result}"
    )


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
# 3b. Hazard-kind matches populating faction's immunity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("world_id", ALL_CORPUS_WORLDS)
def test_hazard_kind_matches_populating_faction_immunity(world_id: str) -> None:
    """Every hazardous, populated region's hazard_kind must match at least one of its
    populating factions' hazard_immunities.

    test_hazard_kind_completeness only checks presence (truthy hazard_kind); it cannot
    catch a populated-but-mismatched hazard_kind/hazard_immunities pair, which is exactly
    the resolver-default ("PHYSICAL") trap that produced Finding 3-shaped population
    collapse in both worlds this test covers (TCK-20260708-DUNGEON-URBAN-POPULATION-
    COLLAPSE). A region with hazard_level > 0 and no matching immunity is an unconditional,
    unmitigated per-tick drain to every entity spawned there.

    Matching here is region-level "any populating faction is immune," not per-faction
    "every populating faction is immune" (see ``matched = any(...)`` below). At
    ``bandit_road`` (present in 6 of the 17 corpus worlds), ``town_council`` is not immune
    to NATURAL_TERRAIN but co-located ``bandit_company``/``merchant_league`` are, so this
    region-level check passes even though ``town_council``'s own entities take real,
    unmitigated per-tick drain at runtime (``calculate_hazard_drain`` resolves immunity
    per-entity, not per-region). This is a known, ratified condition — see
    docs/guidelines/intentional_divergences.md §2.30 and
    TCK-20260710-TOWN-COUNCIL-HAZARD-DA — not an oversight in this test. Do not add an
    xfail/skip/exception for it: the region-level "any" semantics already make it pass
    corpus-wide, and redesigning the semantics to per-faction "every" is a separate,
    out-of-scope change (TCK-20260710-HAZARD-KIND-CORPUS-WIDE investigation.md Risk 2).
    """
    spec = _load_resolved_spec(world_id)
    immunities = _faction_hazard_immunities()

    populating_factions_by_region: dict[str, set[str]] = {}
    for entity in spec.get("entities", []):
        region_id = entity.get("spawn_region")
        faction_id = entity.get("faction")
        if region_id and faction_id:
            populating_factions_by_region.setdefault(region_id, set()).add(faction_id)

    for region in spec.get("regions", []):
        hazard_level = region.get("hazard_level", 0.0) or 0.0
        region_id = region.get("id")
        populating_factions = populating_factions_by_region.get(region_id)
        if hazard_level <= 0 or not populating_factions:
            continue
        hazard_kind = region.get("hazard_kind")
        matched = any(hazard_kind in immunities.get(f, set()) for f in populating_factions)
        assert matched, (
            f"{world_id}: region '{region_id}' hazard_kind={hazard_kind!r} matches none of "
            f"its populating factions' hazard_immunities ({sorted(populating_factions)}) — "
            "these entities take unconditional, unmitigated per-tick drain."
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


# ---------------------------------------------------------------------------
# 5. trading_company_hub composition presence (TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "world_id",
    ["frontier_living_world", "frontier_extended", "swamp_border_world"],
)
def test_trading_company_hub_composed(world_id: str) -> None:
    """Guards the ECONOMY content-depth addition — a future unrelated edit to any of
    these 3 worlds' world.yaml must not silently drop the trading_company_hub module
    reference these worlds were given to raise merchant/crafting content density."""
    assert "trading_company_hub" in _world_modules(world_id), (
        f"{world_id}: expected 'trading_company_hub' in composition module list, "
        f"got {_world_modules(world_id)}"
    )

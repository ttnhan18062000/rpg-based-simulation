import sys
import math
import inspect
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd()))

import pytest
from src.core.state import AuthoritativeState, BuildingState, ResourceNodeState
from src.core.dirty import DirtySet
from src.core.builder import V2EntityBuilder
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.hard_law_monitor import HardLawMonitor, HardLawViolationError
from src.engine.runtime_status import RuntimeStatus

def test_hard_law_monitor_individual_laws():
    # 1. Test LAW-HP-NONNEGATIVE
    e1 = V2EntityBuilder(1).combat(hp=-5, alive=True).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: e1})
    dirty = DirtySet(combat_entities={1})
    violations = HardLawMonitor.check(state, dirty)
    assert len(violations) == 1
    assert violations[0].law_id == "LAW-HP-NONNEGATIVE"
    assert violations[0].entity_id == 1

    # Test that dead entity with negative HP does NOT violate HP law
    e1_dead = V2EntityBuilder(1).combat(hp=-5, alive=False).build()
    state_dead = AuthoritativeState(tick=1, seed=42, entities={1: e1_dead})
    violations_dead = HardLawMonitor.check(state_dead, dirty)
    assert len(violations_dead) == 0

    # 2. Test LAW-READINESS-NONNEGATIVE
    e2 = V2EntityBuilder(2).combat(readiness=-1.5, alive=True).build()
    state2 = AuthoritativeState(tick=1, seed=42, entities={2: e2})
    dirty2 = DirtySet(combat_entities={2})
    violations2 = HardLawMonitor.check(state2, dirty2)
    assert len(violations2) == 1
    assert violations2[0].law_id == "LAW-READINESS-NONNEGATIVE"

    # 3. Test LAW-GOLD-NONNEGATIVE
    e3 = V2EntityBuilder(3).inventory(gold=-50).build()
    state3 = AuthoritativeState(tick=1, seed=42, entities={3: e3})
    dirty3 = DirtySet(inventory_entities={3})
    violations3 = HardLawMonitor.check(state3, dirty3)
    assert len(violations3) == 1
    assert violations3[0].law_id == "LAW-GOLD-NONNEGATIVE"

    # 4. Test LAW-STAMINA-NONNEGATIVE
    e4 = V2EntityBuilder(4).stamina(current=-10.0).build()
    state4 = AuthoritativeState(tick=1, seed=42, entities={4: e4})
    dirty4 = DirtySet(biological_entities={4})
    violations4 = HardLawMonitor.check(state4, dirty4)
    assert len(violations4) == 1
    assert violations4[0].law_id == "LAW-STAMINA-NONNEGATIVE"

    # 5. Test LAW-POSITION-FINITE
    e5 = V2EntityBuilder(5).location(float('nan'), 10.0).build()
    state5 = AuthoritativeState(tick=1, seed=42, entities={5: e5})
    dirty5 = DirtySet(movement_entities={5})
    violations5 = HardLawMonitor.check(state5, dirty5)
    assert len(violations5) == 1
    assert violations5[0].law_id == "LAW-POSITION-FINITE"


def test_hard_law_occupancy_collision():
    # Construct two solid alive entities on the same tile (5, 5)
    e1 = V2EntityBuilder(1).location(5.2, 5.8).combat(alive=True).build()
    e2 = V2EntityBuilder(2).location(5.4, 5.1).combat(alive=True).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: e1, 2: e2})
    
    # Dirty movement entities
    dirty = DirtySet(movement_entities={1, 2})
    
    violations = HardLawMonitor.check(state, dirty)
    # We should detect the collision violation
    assert len(violations) >= 1
    assert any(v.law_id == "LAW-OCCUPANCY-COLLISION" for v in violations)


def test_observability_modes_and_kernel_integration(request):
    # ObservabilityConfig's override mode is class-level global state -- reset it on exit
    # so a DEBUG override set below doesn't leak into later tests/modules run in the same
    # pytest process (found via a real CI cross-file collision with test_metrics_export.py,
    # TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL).
    request.addfinalizer(ObservabilityConfig.clear_all_overrides)

    # Set config to OFF mode
    ObservabilityConfig.set_override_mode(ObservabilityMode.OFF)
    assert ObservabilityConfig.get_mode() == ObservabilityMode.OFF

    e1 = V2EntityBuilder(1).combat(hp=-5, alive=True).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: e1})
    dirty = DirtySet(combat_entities={1})

    # OFF mode should run checks but not fail
    violations = HardLawMonitor.check(state, dirty)
    assert len(violations) == 1

    # Test Kernel integration under LIGHT mode
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)

    status = RuntimeStatus()
    # Mock status/kernel checking
    class MockKernel:
        def __init__(self):
            self._state = state
            self._status = status
        
        def _run_hard_law_checks(self, dirty_set):
            from src.observability.config import ObservabilityConfig, ObservabilityMode
            from src.observability.hard_law_monitor import HardLawMonitor, HardLawViolationError

            mode = ObservabilityConfig.get_mode()
            if mode == ObservabilityMode.OFF:
                return

            violations = HardLawMonitor.check(self._state, dirty_set)
            if not violations:
                return

            if not hasattr(self._status, "cumulative_violations"):
                self._status.cumulative_violations = {}
            if not hasattr(self._status, "hard_law_violations"):
                self._status.hard_law_violations = []

            self._status.hard_law_violations.extend(violations)
            self._status.last_hard_law_violation_tick = self._state.tick

            for v in violations:
                self._status.cumulative_violations[v.law_id] = self._status.cumulative_violations.get(v.law_id, 0) + 1

            if mode in (ObservabilityMode.DEBUG, ObservabilityMode.CERTIFICATION):
                raise HardLawViolationError(violations)

    mk = MockKernel()
    mk._run_hard_law_checks(dirty)
    # Under LIGHT mode, it should record to status without raising
    assert len(status.hard_law_violations) == 1
    assert status.cumulative_violations["LAW-HP-NONNEGATIVE"] == 1

    # Under DEBUG mode, it should raise HardLawViolationError
    ObservabilityConfig.set_override_mode(ObservabilityMode.DEBUG)

    with pytest.raises(HardLawViolationError) as exc_info:
        mk._run_hard_law_checks(dirty)
    assert "LAW-HP-NONNEGATIVE" in str(exc_info.value)


# --- TCK-20260716-PLACELEGAL-HARDLAW: check_initial_placement() ---------------------------


def test_check_initial_placement_full_population_scan_unit():
    # Unconditional scan: signature takes only `state`, no DirtySet.
    sig = inspect.signature(HardLawMonitor.check_initial_placement)
    assert list(sig.parameters.keys()) == ["state"]

    e1 = V2EntityBuilder(1).location(8.0, 8.0).combat(alive=True).build()
    e2 = V2EntityBuilder(2).location(8.0, 8.0).combat(alive=True).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: e1, 2: e2})

    violations = HardLawMonitor.check_initial_placement(state)
    assert len(violations) == 1
    assert violations[0].law_id == "LAW-SPAWN-OCCUPANCY"
    assert violations[0].severity == "ERROR"
    assert {violations[0].entity_id, violations[0].details["colliding_object_id"]} == {1, 2}


def test_check_initial_placement_covers_buildings_and_resource_nodes_unit():
    entity = V2EntityBuilder(1).location(5.0, 5.0).combat(alive=True).build()
    building_on_entity = BuildingState(id=20000, kind="shop", position=(5.0, 5.0))
    building_alone = BuildingState(id=20001, kind="inn", position=(9.0, 9.0))
    resource_on_building = ResourceNodeState(
        id=10000, kind="ore", position=(9.0, 9.0), yields_item="ore",
        remaining_charges=5, max_charges=5, required_ticks=10
    )
    state = AuthoritativeState(
        tick=0, seed=1,
        entities={1: entity},
        buildings={20000: building_on_entity, 20001: building_alone},
        resource_nodes={10000: resource_on_building},
    )

    violations = HardLawMonitor.check_initial_placement(state)
    by_tile = {v.details["tile"]: v for v in violations}

    entity_vs_building = by_tile[(5, 5)]
    assert entity_vs_building.details["object_kind"] == "entity"
    assert entity_vs_building.details["colliding_object_kind"] == "building"

    building_vs_resource = by_tile[(9, 9)]
    assert building_vs_resource.details["object_kind"] == "building"
    assert building_vs_resource.details["colliding_object_kind"] == "resource_node"


def test_check_initial_placement_reuses_verify_occupancy_wall_terrain_unit():
    entity = V2EntityBuilder(1).location(3.0, 3.0).combat(alive=True).build()
    state = AuthoritativeState(
        tick=0, seed=1,
        entities={1: entity},
        terrain={(3, 3): "WALL"},
    )

    violations = HardLawMonitor.check_initial_placement(state)
    assert len(violations) == 1
    assert violations[0].law_id == "LAW-SPAWN-OCCUPANCY"
    assert violations[0].details["object_kind"] == "entity"
    assert violations[0].details["reason"] == "PATH_NOT_FOUND"


@pytest.mark.regression
def test_seed42_entity6_entity14_tile_27_38_collision():
    """
    Regression test for TCK-20260716-PLACELEGAL-HARDLAW.

    WorldCompiler.compile() never validated spawn placement against terrain or
    occupancy. Compiling `unit_information_density` at seed=42 deterministically
    spawns entities 6 and 14 on the identical tile (27, 38) — reproduced here
    directly from a fresh compile, not from stored run data (data/runs/ is
    routinely cleaned and no longer holds the original evidence run).

    Originating evidence: docs/plans/idea_placement_legality_check.md,
    experiments/placement_integrity/PROPOSAL.md.
    """
    from src.worldbuilding.repository import WorldRepository
    from src.worldbuilding.compiler import WorldCompiler

    repo = WorldRepository("data/worlds")
    spec = repo.load_world("unit_information_density")
    state, _ = WorldCompiler.compile(spec, seed=42)

    violations = HardLawMonitor.check_initial_placement(state)
    spawn_violations = [v for v in violations if v.law_id == "LAW-SPAWN-OCCUPANCY"]
    assert len(spawn_violations) == 1

    v = spawn_violations[0]
    assert v.severity == "ERROR"
    assert v.details["tile"] == (27, 38)
    assert v.details["object_kind"] == "entity"
    assert {v.entity_id, v.details["colliding_object_id"]} == {6, 14}


def test_seed137_and_seed999_no_initial_placement_violations():
    """
    Negative control: proves check_initial_placement() does not over-fire on
    ordinary compiled content.

    NOTE (see plan.md Deviations): the originally proposed negative-control
    world/seeds (unit_information_density/source/selfmodel_pilot at seeds 137
    and 999) turned out NOT to be collision-free once checked with this
    full-population scan — they were only confirmed clear of the *specific*
    entity-6/entity-14 pair from the seed-42 regression above; each produces a
    different entity-pair collision at those seeds. `wilderness_survival` is
    empirically confirmed collision-free across seeds 42, 137, and 999 and is
    used here instead to prove the check isn't over-firing on genuinely clean
    content.
    """
    from src.worldbuilding.repository import WorldRepository
    from src.worldbuilding.compiler import WorldCompiler

    repo = WorldRepository("data/worlds")
    for seed in (42, 137, 999):
        spec = repo.load_world("wilderness_survival")
        state, _ = WorldCompiler.compile(spec, seed=seed)
        violations = HardLawMonitor.check_initial_placement(state)
        spawn_violations = [v for v in violations if v.law_id == "LAW-SPAWN-OCCUPANCY"]
        assert spawn_violations == [], f"seed {seed} produced unexpected violations: {spawn_violations}"


# --- Anti-drift guards ----------------------------------------------------------------------


def test_check_occupancy_signature_unchanged():
    sig = inspect.signature(HardLawMonitor.check_occupancy)
    assert list(sig.parameters.keys()) == ["state", "dirty_set"]

    state = AuthoritativeState(tick=1, seed=1, entities={})
    assert HardLawMonitor.check_occupancy(state, None) == []
    assert HardLawMonitor.check_occupancy(state, DirtySet()) == []


def test_no_autocorrect_on_violation():
    e1 = V2EntityBuilder(1).location(5.0, 5.0).combat(alive=True).build()
    e2 = V2EntityBuilder(2).location(5.0, 5.0).combat(alive=True).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: e1, 2: e2})

    positions_before = {eid: ent.navigation.position for eid, ent in state.entities.items()}
    violations = HardLawMonitor.check_initial_placement(state)
    assert len(violations) == 1
    positions_after = {eid: ent.navigation.position for eid, ent in state.entities.items()}
    assert positions_before == positions_after


def test_severity_is_always_error_for_new_law():
    e1 = V2EntityBuilder(1).location(5.0, 5.0).combat(alive=True).build()
    e2 = V2EntityBuilder(2).location(5.0, 5.0).combat(alive=True).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: e1, 2: e2})

    violations = HardLawMonitor.check_initial_placement(state)
    assert violations
    assert all(v.severity == "ERROR" for v in violations)


def test_conservation_law_not_introduced():
    e1 = V2EntityBuilder(1).location(5.0, 5.0).combat(alive=True).build()
    e2 = V2EntityBuilder(2).location(5.0, 5.0).combat(alive=True).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: e1, 2: e2})

    violations = HardLawMonitor.check_initial_placement(state)
    assert all(not v.law_id.startswith("CONSERVATION") for v in violations)

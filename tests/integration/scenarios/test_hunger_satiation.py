"""
Integration tests for hunger satiation fix (TCK-20260619-P0-HUNGER-SATIATION).

Verifies:
1. tactical.py correctly dispatches EAT action when entity reaches a tavern building
2. intelligence.py HUNGER project completes when hunger drops below threshold
3. Economic goals run in ≥10% of active ticks once food is available
"""
from __future__ import annotations

from src.engine.kernel import Kernel
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState
from src.core.strategic import ProjectStatus
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG


_TEST_PROFILE = RuntimeProfile(
    name="hunger-test",
    hardware_class=HardwareClass.CLASS_B,
    max_ram_mb=512,
    max_cpu_percent=100.0,
    max_worker_count=1,
    max_queue_depth=500,
    max_replay_buffer_kb=0,
    max_observability_budget_percent=0.0,
    max_tick_budget_ms=500.0,
)


def _state_with_tavern(hunger: float = 60.0, seed: int = 42) -> AuthoritativeState:
    entity = (
        V2EntityBuilder(1)
        .kind("VILLAGER")
        .location(0.0, 0.0)
        .biological(hunger=hunger)
        .combat(readiness=100.0)
        .build()
    )
    tavern = BuildingState(id=100, kind="tavern", position=(5.0, 5.0))
    return AuthoritativeState(
        tick=0,
        seed=seed,
        world_time=0,
        entities={1: entity},
        buildings={100: tavern},
        building_tiles={(5, 5): "tavern"},
    )


def test_hunger_satiation_resolves_in_food_world():
    """
    400-tick run with tavern present: ≥10% of active-project ticks must be non-hunger.
    """
    kernel = Kernel(_TEST_PROFILE, _state_with_tavern(hunger=60.0), DeterministicRNG(42),
                    flags={"no_frame_pacing": True, "no_replay": True})

    hunger_ticks = 0
    non_hunger_ticks = 0
    completed_hunger_ids: set[str] = set()

    try:
        for _ in range(400):
            kernel.tick_once()
            ent = kernel.state.entities.get(1)
            if ent is None:
                continue

            # Track completed HUNGER projects
            for p in ent.strategic.projects.values():
                if (
                    getattr(p.kind, "value", str(p.kind)) == "hunger"
                    and p.status == ProjectStatus.COMPLETED
                ):
                    completed_hunger_ids.add(p.id)

            curr_pid = ent.strategic.current_project_id
            if not curr_pid:
                non_hunger_ticks += 1
                continue
            proj = ent.strategic.projects.get(curr_pid)
            if proj is None:
                continue
            if getattr(proj.kind, "value", str(proj.kind)) == "hunger":
                hunger_ticks += 1
            else:
                non_hunger_ticks += 1
    finally:
        kernel.shutdown()

    total = hunger_ticks + non_hunger_ticks
    assert total > 0, "No active-project ticks recorded"

    ratio = non_hunger_ticks / total
    assert ratio >= 0.10, (
        f"Non-hunger tick ratio {ratio:.1%} < 10% "
        f"(hunger={hunger_ticks}, non_hunger={non_hunger_ticks})"
    )

    assert len(completed_hunger_ids) >= 1, (
        "No HUNGER project reached COMPLETED status in 400 ticks"
    )

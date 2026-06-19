"""
tests/integration/scenarios/test_entity_differentiation.py

E11-C: 400-tick differentiation test harness.

Verifies that:
  1. All entities at spawn have unique personality vectors (test_no_identical_personality_vectors_at_spawn).
  2. Top-bravery-quartile heroes take combat_engage routes at >= 2x the rate of
     bottom-bravery-quartile heroes over 400 ticks (test_bravery_quartile_combat_rate_2x).

Ticket: TCK-20260619-E11C-DIFF-HARNESS
"""

import pytest
from collections import defaultdict
from dataclasses import replace

from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.schema import WorldSpec
from src.core.strategic import GoalKind

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

TICKS = 400
SEED = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_differentiation_spec() -> WorldSpec:
    """
    Return a WorldSpec with 8 heroes + 4 monsters all placed in the same
    'arena' region (bounds [0, 0, 32, 32]) so they are within the
    CombatEngageScorer perception radius of 10.0 from tick 0.

    A second 'village' region satisfies topology minimum requirements.
    Do NOT use sandbox_world — it has only 3 heroes, too few for quartile math.
    """
    raw_spec = {
        "schema_version": "worldspec.v1",
        "world_id": "differentiation_arena",
        "name": "Differentiation Arena",
        "topology": {
            "width": 64,
            "height": 64,
            "coordinate_system": "grid",
        },
        "regions": [
            {
                "id": "arena",
                "type": "wilderness",
                "bounds": [0, 0, 32, 32],
                "terrain": "GRASS",
            },
            {
                "id": "village",
                "type": "town",
                "bounds": [33, 33, 63, 63],
                "terrain": "GRASS",
            },
        ],
        "factions": [
            {"id": "heroes", "type": "civilian"},
            {"id": "monsters", "type": "hostile"},
        ],
        "entities": [
            {
                "id": "heroes_group",
                "count": 8,
                "role": "hero",
                "faction": "heroes",
                "spawn_region": "arena",
            },
            {
                "id": "monsters_group",
                "count": 4,
                "role": "monster",
                "faction": "monsters",
                "spawn_region": "arena",
            },
        ],
        "resources": [],
        "buildings": [],
        "quests": [],
    }
    return WorldSpec.model_validate(raw_spec)


def _test_profile() -> RuntimeProfile:
    """
    RuntimeProfile for the 400-tick differentiation run.
    CLASS_B hardware, single worker, no observability overhead, no replay I/O.
    """
    return RuntimeProfile(
        name="differentiation-test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=500,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=200.0,
    )


# ---------------------------------------------------------------------------
# Test 1: Unique personality vectors at spawn (strict pass)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_no_identical_personality_vectors_at_spawn():
    """
    AC-1: Every entity compiled from the differentiation spec must have a
    distinct (greed, bravery, sociability, industry) personality tuple.

    This is a strict-pass test — no xfail allowed.
    Requires E11A: PersonalityComponent is seeded with distinct values.
    """
    spec = _build_differentiation_spec()
    state, _report = WorldCompiler.compile(spec, seed=SEED)

    seen: dict[tuple, int] = {}
    for eid, ent in state.entities.items():
        p = ent.identity.personality
        vec = (p.greed, p.bravery, p.sociability, p.industry)
        if vec in seen:
            pytest.fail(
                f"Entity {eid} has duplicate personality vector {vec} "
                f"(first seen on entity {seen[vec]})"
            )
        seen[vec] = eid

    assert len(seen) == len(state.entities), (
        f"Expected {len(state.entities)} unique personality vectors, "
        f"got {len(seen)}"
    )


# ---------------------------------------------------------------------------
# Test 2: Bravery quartile → 2× combat_engage rate (xfail until E11D)
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.integration
def test_bravery_quartile_combat_rate_2x():
    """
    AC-2: After 400 ticks, the top-bravery-quartile heroes must take
    combat_engage routes at >= 2x the rate of the bottom-bravery-quartile.

    Strict-pass test (E11D confirmed 4.92× ratio at SEED=42, TICKS=400 — bravery coefficient 0.6, caution coefficient 0.8).
    Baseline (SEED=42, TICKS=400): 4.92× ratio achieved with bravery coeff=0.6

    Anti-drift notes:
    - Uses current_project_id → projects[id].kind per tick (not post-hoc scan).
    - Does NOT use transaction_trace (economic data, not goal-selection).
    - Does NOT use entity_timeline_store (20-event cap overflows at 400 ticks).
    - Does NOT enable audit_mode (unbounded transaction_trace accumulation).
    - Uses no_frame_pacing=True to suppress kernel tick-padding sleep (200ms/tick
      × 400 ticks = 80s would exceed the 60s conftest medium budget).
    """
    # Step 1: Compile world
    spec = _build_differentiation_spec()
    initial_state, _report = WorldCompiler.compile(spec, seed=SEED)

    # Step 2: Enable combat and adventure feature flags on initial state.
    # Both flags default to OFF in FeatureFlagManager; they must be set here.
    # pipeline.py reads state.feature_flags and applies them via FeatureFlagManager.set_flag_mode().
    initial_state = replace(
        initial_state,
        feature_flags={
            "ENABLE_COMBAT_ENGAGEMENT": "ON",
            "ENABLE_ADVENTURE_ROUTING": "ON",
        },
    )

    # Step 3: Per-entity tick-level histogram of active project kind.
    # project_kind_history[entity_id] = list of GoalKind.value strings (or None) per tick.
    project_kind_history: dict[int, list[str | None]] = defaultdict(list)

    # Step 4: Construct kernel and run tick loop
    rng = DeterministicRNG(SEED)
    kernel = Kernel(_test_profile(), initial_state, rng, flags={"no_replay": True, "no_frame_pacing": True})

    try:
        for _ in range(TICKS):
            kernel.tick_once()
            # Sample current project kind for every entity this tick.
            # Must be inside the loop: current_project_id reflects the live per-tick choice.
            for eid, ent in kernel.state.entities.items():
                cur_proj_id = ent.strategic.current_project_id
                if cur_proj_id and cur_proj_id in ent.strategic.projects:
                    kind = ent.strategic.projects[cur_proj_id].kind
                    project_kind_history[eid].append(
                        kind.value if hasattr(kind, "value") else str(kind)
                    )
                else:
                    project_kind_history[eid].append(None)

        final_state = kernel.state
    finally:
        kernel.shutdown()

    # Step 5: Quartile computation and assertion

    # Filter to alive heroes only
    hero_entities = [
        ent
        for ent in final_state.entities.values()
        if ent.kind.lower() == "hero" and ent.combat.alive
    ]

    assert len(hero_entities) >= 4, (
        f"Expected at least 4 alive hero entities for quartile math, "
        f"got {len(hero_entities)}. Check E11A prerequisite."
    )

    # Sort by bravery ascending
    hero_entities.sort(key=lambda e: e.identity.personality.bravery)

    n = len(hero_entities)
    q_size = max(1, n // 4)
    bottom_quartile = hero_entities[:q_size]
    top_quartile = hero_entities[n - q_size:]

    combat_engage_value = GoalKind.COMBAT_ENGAGE.value  # "combat_engage"

    def combat_engage_rate(entity_list: list) -> float:
        """Fraction of ticks where the entity's active project was COMBAT_ENGAGE."""
        total_ticks = 0
        combat_ticks = 0
        for ent in entity_list:
            history = project_kind_history[ent.id]
            total_ticks += len(history)
            combat_ticks += sum(1 for k in history if k == combat_engage_value)
        return combat_ticks / max(1, total_ticks)

    bottom_rate = combat_engage_rate(bottom_quartile)
    top_rate = combat_engage_rate(top_quartile)

    # Diagnostic gate: if bottom_rate is 0 the flags or proximity did not work
    assert bottom_rate > 0, (
        f"Bottom-quartile combat_engage rate is 0 after {TICKS} ticks. "
        f"Check ENABLE_COMBAT_ENGAGEMENT flag and entity proximity in arena region."
    )

    assert top_rate >= 2.0 * bottom_rate, (
        f"Top-quartile combat_engage rate ({top_rate:.4f}) is less than "
        f"2x bottom-quartile rate ({bottom_rate:.4f}). "
        f"Calibration required (TCK-20260619-E11D-SCORING-CAL)."
    )

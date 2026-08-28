from src.core.builder import V2EntityBuilder
from src.core.models.inventory import ItemStack
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.engine.cadence import SystemCadence
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem
from src.systems.strategic_systems.redirection import StrategicRedirectionSystem


def _entity_with_items(entity_id: int, x: float, y: float):
    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(x, y)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .inventory(items=[ItemStack(item_id="iron_ore", quantity=1)])
        .build()
    )


def test_routine_blocker_pass_targets_nearest_town_tile_not_arbitrary_iter():
    """StrategicIntelligenceSystem's routine-blocker return-to-town fallback (inside
    fused_strategic_pass) must pick the town tile nearest to the requesting entity, not an
    arbitrary set-iteration-order pick (TCK-20260824-TOWN-CENTER-POINTER-FIX). An entity near
    (70, 70) with a far cluster near (10, 10) and a near cluster near (70, 70) must be routed to
    the near cluster.

    cadence.strategic_intelligence is set high enough (with tick/entity_id chosen so
    should_run(...) is False) to skip real strategic-intent scoring for this tick -- isolating
    the return-to-town fallback under test from unrelated goal-scoring outcomes -- while
    concern_evaluation stays at its default cadence of 1 so the routine pass still runs its full
    body rather than the unrelated fast-path shortcut.
    """
    entity = _entity_with_items(1, 70.0, 70.0)
    town_tiles = {(10, 10), (70, 70)}
    state = AuthoritativeState(
        tick=5, seed=1, entities={1: entity}, town_tiles=town_tiles, town_center=(0.0, 0.0)
    )
    cadence = SystemCadence(strategic_intelligence=10)
    assert (state.tick + 1) % cadence.strategic_intelligence != 0  # should_run(...) is False

    result = StrategicIntelligenceSystem.fused_strategic_pass(state, StateUpdate(), cadence)

    nav = result.entity_updates[1].navigation
    assert nav is not None and nav.target_set == (70.0, 70.0), (
        f"expected nearest town tile (70.0, 70.0), got {nav.target_set if nav else None}"
    )


def test_redirection_and_routine_blocker_single_town_world_unaffected():
    """For a world with exactly one town region (today's dominant case), the nearest-tile fix
    produces the same target as the pre-fix arbitrary pick did -- proving the fix is additive for
    the single-town case, not just correct for the new multi-town case, for both
    StrategicRedirectionSystem.enforce() and StrategicIntelligenceSystem's routine-blocker
    pass."""
    town_tiles = {(5, 5)}

    redir_entity = _entity_with_items(1, 40.0, 40.0)
    # tick=9, entity_id=1: default SystemCadence.strategic_intelligence=10, so
    # (9 + 1) % 10 == 0 and this entity's redirection pass actually runs on this tick.
    redir_state = AuthoritativeState(
        tick=9, seed=1, entities={1: redir_entity}, town_tiles=town_tiles, town_center=(0.0, 0.0)
    )
    redir_result = StrategicRedirectionSystem.enforce(redir_state, StateUpdate())
    redir_nav = redir_result.entity_updates[1].navigation
    assert redir_nav is not None and redir_nav.target_set == (5.0, 5.0)

    intel_entity = _entity_with_items(2, 40.0, 40.0)
    intel_state = AuthoritativeState(
        tick=5, seed=1, entities={2: intel_entity}, town_tiles=town_tiles, town_center=(0.0, 0.0)
    )
    cadence = SystemCadence(strategic_intelligence=10)
    assert (intel_state.tick + 2) % cadence.strategic_intelligence != 0
    intel_result = StrategicIntelligenceSystem.fused_strategic_pass(intel_state, StateUpdate(), cadence)
    intel_nav = intel_result.entity_updates[2].navigation
    assert intel_nav is not None and intel_nav.target_set == (5.0, 5.0)

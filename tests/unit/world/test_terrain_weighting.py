import pytest
from src.core.state import (
    AuthoritativeState, EntityState, CombatComponent, NavigationComponent,
)
from src.engine.movement import MovementSystem
from src.core.enums import ReasonCode
from src.core.movement_modes import MovementMode

def test_terrain_readiness_rejection():
    """
    The readiness pre-check is the plain move cost only (D75): a mountain tile (cost 4.0) no longer multiplies it, because terrain cost is
    TIME (the step takes four ticks, see test_terrain_cost_is_time.py). Entity move_cost is 10.0.
    Readiness 20.0 covers 10.0, so the step onto the mountain is allowed (it used to be refused against 40.0);
    readiness 5.0 does not, so the plain check still refuses on any terrain.
    """
    from src.core.builder import V2EntityBuilder

    def _step(readiness):
        entity = (V2EntityBuilder(1).kind("hero").location(1, 0).combat(readiness=readiness)
            .combat(move_cost=10.0, alive=True).navigation(movement_mode=MovementMode.WANDER).build())
        # Block sidesteps with WALLS to force the checked move
        state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, terrain={(1, 1): "mountain"},
                                   blocked_tiles={(2, 0), (0, 0), (1, -1)})
        return MovementSystem.resolve_move(state, entity, (1, 1))[1]

    allowed = _step(20.0)
    assert allowed.moved_this_tick is True
    assert allowed.new_position == (1, 1)

    refused = _step(5.0)
    assert refused.moved_this_tick is False
    assert refused.new_position is None
    assert refused.navigation.failure_reason == ReasonCode.ACTION_EXHAUSTION

def test_terrain_readiness_success():
    """
    Test that movement into high-cost terrain succeeds if readiness is sufficient.

    TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE (docs/guidelines/
    intentional_divergences.md Section 2.38): a successful move no longer costs readiness at
    all -- readiness is a pure attack-eligibility gate, stamina is the sole movement-fatigue
    resource. verify_movement_legality()'s own smaller readiness PRE-CHECK (readiness >=
    move_cost, exercised by test_terrain_readiness_rejection above) was left untouched, but the
    real hp_delta-equivalent readiness COST on a successful move was removed.
    """
    terrain = {(1, 1): "mountain"}
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(1, 0)
        .combat(readiness=100.0)
        .combat(move_cost=10.0, alive=True)
        .navigation(movement_mode=MovementMode.WANDER)
        .build())
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        terrain=terrain
    )
    
    target_pos = (1, 1)
    updates = MovementSystem.resolve_move(state, entity, target_pos)
    
    ent_upd = updates[1]
    assert ent_upd.moved_this_tick is True
    assert ent_upd.new_position == (1, 1)
    assert ent_upd.readiness_delta == 0.0

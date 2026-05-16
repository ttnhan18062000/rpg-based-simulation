import pytest
from src.core.state import (
    EntityState, RegionState, AuthoritativeState, CombatComponent,
    NavigationComponent, LifecycleComponent, IdentityComponent,
    BiologicalComponent, StrategicComponent, SocialComponent
)
from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate
from src.core.enums import ReasonCode
from src.engine.apply import ApplyPath
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.legality import LegalityServiceV2

def make_hero(eid: int, pos=(5.0, 5.0), hp=100):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(eid)
        .kind("HERO")
        .location(pos[0], pos[1])
        .combat(hp=hp, max_hp=100)
        .combat(alive=True)
        .combat(readiness=100.0)
        .build())

def test_regional_hazard_drain():
    """Verify that entities in high hazard regions take passive HP damage."""
    # Region from (0,0) to (10,10) with hazard 0.5
    region = RegionState(id="volcano", name="Volcano", bounds=(0, 0, 10, 10), hazard_level=0.5)
    
    # Entity at (5,5) with 100 HP
    hero = make_hero(1, pos=(5.0, 5.0), hp=100)
    
    state = AuthoritativeState(tick=100, seed=42, 
                               regions={"volcano": region},
                               entities={1: hero})
    
    update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, update)
    # Apply one tick
    next_state = ApplyPath.apply_generation(state, refined, 101, 101)
    
    # damage = hazard(0.5) * 10 * (1 + calamity(0.0)) = 5
    assert next_state.entities[1].combat.hp == 95

def test_regional_suppression_blocks_sabotage_directly():
    """
    Law:
        SABOTAGE is illegal inside a suppressed region.

    This tests the real legality rule directly, without assuming the pipeline
    rewrites TaskUpdate.payload_set.
    """
    region = RegionState(
        id="holy_city",
        name="Holy City",
        bounds=(0, 0, 10, 10),
        suppression_active=True,
    )

    hero = make_hero(1, pos=(5.0, 5.0))

    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"holy_city": region},
        entities={1: hero},
    )

    legal, reason = LegalityServiceV2.verify_action_legality(
        hero,
        "SABOTAGE",
        state,
    )

    assert legal is False
    assert reason == ReasonCode.REGIONAL_SUPPRESSION or reason == "REGIONAL_SUPPRESSION"
    
def test_regional_suppression_blocks_sabotage_pipeline_integration():
    """
    Pipeline integration law:
        A suppressed SABOTAGE action should be rejected/audited by the
        authoritative pipeline.

    Important:
        The pipeline should not need to mutate TaskUpdate.payload_set to prove
        failure. RejectionEvent is the cleaner authoritative audit surface.
    """
    region = RegionState(
        id="holy_city",
        name="Holy City",
        bounds=(0, 0, 10, 10),
        suppression_active=True,
    )

    hero = make_hero(1, pos=(5.0, 5.0))

    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"holy_city": region},
        entities={1: hero},
    )

    task_upd = TaskUpdate(
        work_kind_set="ENTITY_ACT",
        payload_set={
            "action": "SABOTAGE",
            "target_id": 99,
        },
    )

    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                task=task_upd,
            )
        }
    )

    refined = AuthoritativeApplyPipeline.refine(state, update)

    assert any(
        ev.actor_id == 1
        and ev.action_kind == "SABOTAGE"
        and ev.reason in (ReasonCode.REGIONAL_SUPPRESSION, "REGIONAL_SUPPRESSION")
        for ev in refined.rejection_events
    )

def test_regional_suppression_allows_attack():
    """Verify that ATTACK is NOT blocked (only strategic actions like SABOTAGE/RECRUIT)."""
    region = RegionState(id="holy_city", name="Holy City", bounds=(0, 0, 10, 10), suppression_active=True)
    
    hero = make_hero(1, pos=(5.0, 5.0))
    state = AuthoritativeState(tick=100, seed=42, 
                               regions={"holy_city": region},
                               entities={1: hero})
    
    # Try to ATTACK
    task_upd = TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 2})
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, task=task_upd)})
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Should NOT be blocked by verify_action_legality (it might fail later for target=None, but not suppression)
    ent_upd = refined.entity_updates[1]
    assert ent_upd.task.payload_set.get("reason") != "REGIONAL_SUPPRESSION"

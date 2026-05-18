# Compliance IDs: COMB-283, COMB-284, COMB-285, COMB-286, COMB-287, COMB-288, COMB-289, PROG-105
"""
Combat legality matrix and authoritative outcome tests.
- RPG-0012: melee_adjacency_parity
- RPG-0013: ranged_los_obstruction
- RPG-0014: aoe_splash_rules
- RPG-0019: simultaneous_multi_attack_reward_limit
- RPG-1656: authoritative_combat_resolution
- [RPG-AUTH-002] Every gameplay side effect is represented as a typed update bucket.
- [RPG-AUTH-003] Action legality is verified by the kernel before any side effect is calculated.
- [RPG-COMBAT-003] Tactical modifiers are handled deterministically.
- [RPG-COMBAT-004] AoE and Multi-target attacks resolve as separate atomic sub-intents.
- Logic ID: COMB-283 (Combat tests cover melee legality)
- Logic ID: COMB-284 (Combat tests cover ranged legality)
- Logic ID: COMB-285 (Combat tests cover AoE legality)
- Logic ID: COMB-286 (Combat tests cover invalid target rejection)
- Logic ID: COMB-287 (Combat tests cover dead target rejection)
"""
import pytest
from dataclasses import replace
from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, 
    CombatComponent, SocialComponent, NavigationComponent, 
    BiologicalComponent, StrategicComponent, LifecycleComponent
)
from src.core.enums import EntityRole
from src.core.movement_modes import MovementMode
from src.engine.combat import CombatResolutionSystem
from src.engine.legality import LegalityServiceV2

def create_mock_entity(id, faction="HERO_FACTION", role=EntityRole.HERO, pos=(0,0), hp=100, range=1, readiness=100.0):
    from src.core.builder import V2EntityBuilder
    from src.core.enums import Faction
    
    # Map string faction to enum
    if isinstance(faction, Faction):
        f_enum = faction
    else:
        mapping = {
            "HERO_FACTION": Faction.HERO_GUILD,
            "HERO": Faction.HERO_GUILD,
            "MONSTER": Faction.MONSTER_HORDE,
            "MONSTER_HORDE": Faction.MONSTER_HORDE,
            "NEUTRAL": Faction.NEUTRAL
        }
        f_enum = mapping.get(str(faction).upper(), Faction.HERO_GUILD)
    
    builder = (V2EntityBuilder(id)
              .kind("ACTOR")
              .location(*pos)
              .identity(role=role, faction=f_enum)
              .combat(hp=hp, max_hp=100, atk=10, attack_range=range, alive=hp > 0,
                      readiness=readiness)
              .biological(hunger=0.0, sleep_debt=0.0)
              .lifecycle(active=True))
    
    return builder.build()

@pytest.fixture
def base_state():
    return AuthoritativeState(tick=100, seed=42)

def test_melee_matrix(base_state):
    """M1-M4: Melee adjacency and range limits."""
    attacker = create_mock_entity(1, pos=(10, 10), range=1)
    
    # M1: Target at dist 1 (North)
    target_n = create_mock_entity(2, pos=(10, 11), faction="MONSTER")
    state = replace(base_state, entities={1: attacker, 2: target_n})
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target_n, state)
    assert is_legal, f"Melee North should be legal: {reason}"
    
    # M2: Target at dist 2 (Straight North)
    target_far = create_mock_entity(3, pos=(10, 12), faction="MONSTER")
    state = replace(base_state, entities={1: attacker, 3: target_far})
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target_far, state)
    assert not is_legal
    assert reason == "OUT_OF_RANGE"
    
    # M3: Same position (dist 0) - Should be legal for combat if they overlap?
    # Actually, Manhattan dist 0 is < range 1.
    target_same = create_mock_entity(4, pos=(10, 10), faction="MONSTER")
    state = replace(base_state, entities={1: attacker, 4: target_same})
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target_same, state)
    assert is_legal # Range 0 is <= Range 1.
    
    # M4: Diagonal (dist 2)
    target_diag = create_mock_entity(5, pos=(11, 11), faction="MONSTER")
    state = replace(base_state, entities={1: attacker, 5: target_diag})
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target_diag, state)
    assert not is_legal
    assert reason == "OUT_OF_RANGE"

def test_ranged_and_los(base_state):
    """R1-R5: Ranged limits and LOS obstructions."""
    attacker = create_mock_entity(1, pos=(10, 10), range=5)
    
    # R1: Max range (5)
    target_edge = create_mock_entity(2, pos=(15, 10), faction="MONSTER")
    state = replace(base_state, entities={1: attacker, 2: target_edge})
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target_edge, state)
    assert is_legal
    
    # R2: Max range + 1 (6)
    target_past = create_mock_entity(3, pos=(16, 10), faction="MONSTER")
    state = replace(base_state, entities={1: attacker, 3: target_past})
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target_past, state)
    assert not is_legal
    assert reason == "OUT_OF_RANGE"
    
    # R3: WALL obstruction
    # LegalityServiceV2.has_line_of_sight checks state.terrain
    state_wall = replace(base_state, 
        entities={1: attacker, 2: target_edge},
        terrain={(12, 10): "WALL"}
    )
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target_edge, state_wall)
    assert not is_legal
    assert reason == "LOS_OBSTRUCTED"
    
    # R4: Building obstruction
    from src.core.state import BuildingState
    bldg = BuildingState(id=1, kind="WALL", position=(13, 10), hp=100)
    state_bldg = replace(base_state, 
        entities={1: attacker, 2: target_edge},
        buildings={1: bldg}
    )
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target_edge, state_bldg)
    assert not is_legal
    assert reason == "LOS_OBSTRUCTED"

def test_aoe_and_friendly_fire(base_state):
    """A1-A5: AoE center and splash rules."""
    attacker = create_mock_entity(1, pos=(10, 10), range=5, faction="HERO")
    
    # A1: Center in range
    is_legal, reason = LegalityServiceV2.verify_aoe_legality(attacker, (13, 10), base_state)
    assert is_legal
    
    # A2: Center out of range
    is_legal, reason = LegalityServiceV2.verify_aoe_legality(attacker, (16, 10), base_state)
    assert not is_legal
    assert reason == "OUT_OF_RANGE"
    
    # A4: Friendly Fire in AoE (Authoritative verification)
    ally = create_mock_entity(2, pos=(14, 10), faction="HERO")
    enemy = create_mock_entity(3, pos=(12, 10), faction="MONSTER")
    state = replace(base_state, entities={1: attacker, 2: ally, 3: enemy})
    
    # Resolve AoE at (13,10) with radius 2
    updates = CombatResolutionSystem.resolve_aoe_attack(attacker, (13, 10), 2, state)
    attacker_up = updates[attacker.id]
    assert attacker_up.outcome_kind != "REJECTED"
    
    # Verify splash intents
    # V2: Ally is excluded from splash intents (FF Safety)
    assert len(attacker_up.simultaneous_intents) == 2 # Primary + Enemy 3
    intent = attacker_up.simultaneous_intents[0]
    assert intent.splash_radius == 2
    assert intent.splash_damage > 0
    
    # Note: Application of splash is done in ApplyPath, which we verified hits everyone.
    # We should confirm if AoE center targeting an ally is rejected.
    is_legal_ally, reason = LegalityServiceV2.verify_attack_legality(attacker, ally, state)
    assert not is_legal_ally
    assert reason == "FRIENDLY_FIRE_ILLEGAL"

def test_state_invariants(base_state):
    """S1-S5: Dead/Inactive/Self rejections."""
    # S1: Dead attacker
    attacker_dead = create_mock_entity(1, hp=0, pos=(10,10))
    target = create_mock_entity(2, pos=(11, 10), faction="MONSTER")
    state = replace(base_state, entities={1: attacker_dead, 2: target})
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker_dead, target, state)
    assert not is_legal
    assert reason == "ATTACKER_INCAPACITATED"
    
    # S2: Dead target
    attacker = create_mock_entity(1, hp=100, pos=(10,10))
    target_dead = create_mock_entity(2, pos=(11, 10), hp=0, faction="MONSTER")
    state = replace(base_state, entities={1: attacker, 2: target_dead})
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target_dead, state)
    assert not is_legal
    assert reason == "TARGET_INCAPACITATED"
    
    # S3: Readiness block
    attacker_tired = create_mock_entity(1, readiness=50.0, pos=(10,10))
    state = replace(base_state, entities={1: attacker_tired, 2: target})
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker_tired, target, state)
    assert not is_legal
    assert reason == "INSUFFICIENT_READINESS"
    
    # S4: Opportunity Attack bypass
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker_tired, target, state, is_opportunity_attack=True)
    assert is_legal, f"OA should bypass readiness, but failed with: {reason}"
    
    # S5: Self attack
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, attacker, state)
    assert not is_legal
    assert reason == "SELF_ATTACK_ILLEGAL"

def test_reward_atomicity(base_state):
    """V1-V3: Reward emission only on death."""
    attacker = create_mock_entity(1, pos=(10, 10))
    
    # V1: Non-lethal
    target_tanky = create_mock_entity(2, pos=(11, 10), hp=1000, faction="MONSTER", role=EntityRole.MONSTER)
    state = replace(base_state, entities={1: attacker, 2: target_tanky})
    update = CombatResolutionSystem.resolve_attack(attacker, target_tanky, state)
    assert update.outcome_kind == "SURVIVE"
    # V2: Rewards are in resource_transfers
    assert len(update.resource_transfers) == 0
    
    # V2: Lethal
    target_weak = create_mock_entity(3, pos=(11, 10), hp=1, faction="MONSTER", role=EntityRole.MONSTER)
    state_lethal = replace(base_state, entities={1: attacker, 3: target_weak})
    update_kill = CombatResolutionSystem.resolve_attack(attacker, target_weak, state_lethal)
    assert update_kill.outcome_kind == "KILL"
    assert len(update_kill.resource_transfers) >= 2
    # Find XP transfer
    xp_transfer = next((t for t in update_kill.resource_transfers if t.xp_reward > 0), None)
    assert xp_transfer is not None, "XP transfer missing"
    
    # Find Gold transfer
    gold_transfer = next((t for t in update_kill.resource_transfers if t.gold_delta > 0), None)
    assert gold_transfer is not None, "Gold transfer missing"
    
    # Trace consistency
    assert update_kill.trace["FINAL_ATK_MULT"] > 0
    assert "STAMINA_EXHAUSTION" not in update_kill.trace # Full stamina in mock

def test_los_complex_diagonal(base_state):
    """Verify simplified LoS in diagonal cases."""
    attacker = create_mock_entity(1, pos=(10, 10), range=5)
    target = create_mock_entity(2, pos=(12, 12), faction="MONSTER")
    
    # Path: (10,10) -> (11,10) -> (12,10) -> (12,11) -> (12,12)
    # The current has_line_of_sight algorithm moves X then Y.
    # So it checks (11,10), (12,10), (12,11).
    
    state_blocked = replace(base_state, 
        entities={1: attacker, 2: target},
        terrain={(12, 11): "WALL"}
    )
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state_blocked)
    assert not is_legal
    assert reason == "LOS_OBSTRUCTED"
    
def test_simultaneous_multi_attack_reward_limit(base_state):
    """V3: Verify that only the first legal killer gets the reward."""
    a1 = create_mock_entity(1, pos=(10, 10))
    a2 = create_mock_entity(2, pos=(11, 10))
    target = create_mock_entity(3, pos=(10.5, 10), hp=1, faction="MONSTER", role=EntityRole.MONSTER)
    
    state = replace(base_state, entities={1: a1, 2: a2, 3: target})
    
    # In the pipeline, entities are processed in order.
    # We'll simulate the pipeline's logic for sequential attacks in one tick.
    
    # 1. First attack
    is_legal_1, _ = LegalityServiceV2.verify_attack_legality(a1, target, state)
    assert is_legal_1
    update_1 = CombatResolutionSystem.resolve_attack(a1, target, state)
    assert update_1.outcome_kind == "KILL"
    assert len(update_1.resource_transfers) > 0
    assert update_1.resource_transfers[0].xp_reward > 0
    
    # Apply update_1 to target for the next check
    target_dead = replace(target, combat=replace(target.combat, hp=0, alive=False))
    state_after_1 = replace(state, entities={1: a1, 2: a2, 3: target_dead})
    
    # 2. Second attack
    is_legal_2, reason = LegalityServiceV2.verify_attack_legality(a2, target_dead, state_after_1)
    assert not is_legal_2
    assert reason == "TARGET_INCAPACITATED"

def test_combat_trace_consistency(base_state):
    """Verify that tactical modifiers are correctly recorded in the trace."""
    attacker = create_mock_entity(1, pos=(10, 10))
    target = create_mock_entity(2, pos=(11, 10), faction="MONSTER")
    
    # 1. High Ground
    state_hg = replace(base_state, 
        entities={1: attacker, 2: target},
        terrain={(10, 10): "HILL", (11, 10): "PLAIN"}
    )
    update_hg = CombatResolutionSystem.resolve_attack(attacker, target, state_hg)
    assert "HIGH_GROUND" in update_hg.trace
    assert update_hg.trace["HIGH_GROUND"] == CombatResolutionSystem.HIGH_GROUND_BONUS
    assert update_hg.trace["FINAL_ATK_MULT"] > 1.0
    
    # 2. Cover
    attacker_far = create_mock_entity(1, pos=(10, 10), range=5)
    target_far = create_mock_entity(2, pos=(12, 10), faction="MONSTER")
    state_cover = replace(base_state,
        entities={1: attacker_far, 2: target_far},
        terrain={(11, 10): "FOREST"}
    )
    update_cover = CombatResolutionSystem.resolve_attack(attacker_far, target_far, state_cover)
    assert "COVER_REDUCTION" in update_cover.trace
    assert update_cover.trace["COVER_REDUCTION"] == CombatResolutionSystem.COVER_REDUCTION
    assert update_cover.trace["FINAL_DEF_MULT"] > 1.0

def test_pipeline_simultaneous_attack_atomicity(base_state):
    """Verify that the pipeline prevents double-rewards in a single tick."""
    from src.engine.pipeline import AuthoritativeApplyPipeline
    from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate
    
    a1 = create_mock_entity(1, pos=(10, 10))
    a2 = create_mock_entity(2, pos=(11, 10))
    target = create_mock_entity(3, pos=(10.5, 10), hp=1, faction="MONSTER", role=EntityRole.MONSTER)
    
    state = replace(base_state, entities={1: a1, 2: a2, 3: target})
    
    # Both propose an ATTACK on target 3
    raw_upd = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 3})),
        2: EntityUpdate(entity_id=2, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 3}))
    })
    
    # Refine through pipeline
    refined = AuthoritativeApplyPipeline.refine(state, raw_upd)
    
    # Verify results
    upd_1 = refined.entity_updates[1]
    upd_2 = refined.entity_updates[2]
    
    # Attacker 1 should succeed
    assert upd_1.task.payload_set.get("outcome") == "SUCCESS"
    assert upd_1.identity.evolution_points_delta > 0
    
    # Attacker 2 should FAIL because Attacker 1 already killed it in the same refinement pass
    assert upd_2.task.payload_set.get("outcome") == "FAILURE"
    assert upd_2.task.payload_set.get("reason") == "TARGET_INCAPACITATED"

def test_aoe_splash_los_obstruction(base_state):
    """Verify that splash damage does not penetrate solid walls."""
    from src.engine.apply import ApplyPath
    from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate, CombatIntent
    
    attacker = create_mock_entity(1, pos=(10, 10))
    target = create_mock_entity(2, pos=(11, 10), faction="MONSTER")
    # Enemy behind a wall at (12, 10)
    enemy_behind_wall = create_mock_entity(3, pos=(13, 10), faction="MONSTER")
    
    state = replace(base_state, 
        entities={1: attacker, 2: target, 3: enemy_behind_wall},
        terrain={(12, 10): "WALL"}
    )
    
    # Simulate an AOE attack at (11, 10) with radius 2
    # In V2, ApplyPath handles splash based on simultaneous_intents in the update
    aoe_upd = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, combat=CombatUpdate(
            attacker_id=attacker.id,
            simultaneous_intents=[CombatIntent(
                attacker_id=attacker.id,
                damage=10,
                splash_radius=2,
                splash_damage=5
            )]
        ))
    })
    
    final_state = ApplyPath.apply_generation(state, aoe_upd)
    
    # Target 2 should take damage (direct or splash, depending on how it's handled)
    # Target 3 should NOT take damage because of the WALL at (12, 10)
    ent_3 = final_state.entities[3]
    assert ent_3.combat.hp == 100, f"Enemy behind wall should NOT take splash damage. HP: {ent_3.combat.hp}"

def test_multi_kill_aoe_rewards(base_state):
    """Verify that multiple kills in one AoE grant cumulative rewards."""
    from src.engine.pipeline import AuthoritativeApplyPipeline
    from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate
    from src.core.enums import EntityRole
    
    attacker = create_mock_entity(1, pos=(10, 10))
    m1 = create_mock_entity(2, pos=(11, 10), hp=1, faction="MONSTER", role=EntityRole.MONSTER)
    m1 = replace(m1, identity=replace(m1.identity, evolution_level=1))
    m2 = create_mock_entity(3, pos=(12, 10), hp=1, faction="MONSTER", role=EntityRole.MONSTER)
    m2 = replace(m2, identity=replace(m2.identity, evolution_level=1))
    
    state = replace(base_state, entities={1: attacker, 2: m1, 3: m2})
    
    # Attacker performs AOE_ATTACK targeting (11.5, 10) with radius 2
    # Note: We need the pipeline to support AOE_ATTACK action!
    raw_upd = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, task=TaskUpdate(
            work_kind_set="ENTITY_ACT", 
            payload_set={"action": "AOE_ATTACK", "target_pos": (11.5, 10), "radius": 2}
        ))
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, raw_upd)
    
    # Verify rewards
    upd_1 = refined.entity_updates[1]
    # Rewards for 2 monsters (lvl 1 -> 10 XP each) = 20 XP
    # The pipeline resolves ResourceTransferIntents into evolution_points_delta
    
    assert upd_1.task.payload_set.get("outcome") == "SUCCESS"
    assert upd_1.identity.evolution_points_delta >= 20, f"Expected at least 20 XP, got {upd_1.identity.evolution_points_delta}"

def test_simultaneous_aoe_same_target(base_state):
    """Verify that multiple AoEs hitting the same target correctly aggregate damage."""
    from src.engine.pipeline import AuthoritativeApplyPipeline
    from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate
    
    a1 = create_mock_entity(1, pos=(10, 10))
    a2 = create_mock_entity(2, pos=(12, 10))
    target = create_mock_entity(3, pos=(11, 10), hp=100, faction="MONSTER")
    
    state = replace(base_state, entities={1: a1, 2: a2, 3: target})
    
    # Both perform AOE_ATTACK targeting (11, 10) with radius 1
    raw_upd = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, task=TaskUpdate(
            work_kind_set="ENTITY_ACT", 
            payload_set={"action": "AOE_ATTACK", "target_pos": (11, 10), "radius": 1}
        )),
        2: EntityUpdate(entity_id=2, task=TaskUpdate(
            work_kind_set="ENTITY_ACT", 
            payload_set={"action": "AOE_ATTACK", "target_pos": (11, 10), "radius": 1}
        ))
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, raw_upd)
    
    # Target 3 should have two CombatUpdates merged
    upd_3 = refined.entity_updates[3]
    # Attacker 1 damage + Attacker 2 damage (splash or primary)
    # Both will hit as primary if target_pos is exact.
    # Base atk 10 vs default def 5 -> 4 damage each. Total 8.
    assert upd_3.combat.hp_delta <= -8, f"Expected aggregated damage from both hits, got {upd_3.combat.hp_delta}"

def test_aoe_sliding_state_awareness(base_state):
    """Verify that splash damage from an earlier action is seen by a later action in the same tick."""
    from src.engine.pipeline import AuthoritativeApplyPipeline
    from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate
    
    attacker = create_mock_entity(1, pos=(10, 10))
    victim = create_mock_entity(2, pos=(11, 10), hp=5, faction="MONSTER") # Low HP
    finisher = create_mock_entity(3, pos=(11, 11)) # Nearby hero
    
    state = replace(base_state, entities={1: attacker, 2: victim, 3: finisher})
    
    # 1. Attacker hits nearby spot with AoE, splash should kill victim
    # 2. Finisher tries to ATTACK victim
    raw_upd = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, task=TaskUpdate(
            work_kind_set="ENTITY_ACT", 
            payload_set={"action": "AOE_ATTACK", "target_pos": (10, 10), "radius": 1}
        )),
        3: EntityUpdate(entity_id=3, task=TaskUpdate(
            work_kind_set="ENTITY_ACT", 
            payload_set={"action": "ATTACK", "target_id": 2}
        ))
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, raw_upd)
    
    # Action 1 (AoE) should succeed and kill victim
    # Action 2 (Attack) should FAIL because victim is already dead in the sliding state
    upd_3 = refined.entity_updates[3]
    assert upd_3.task.payload_set.get("outcome") == "FAILURE"
    assert upd_3.task.payload_set.get("reason") == "TARGET_INCAPACITATED"

def test_skill_pipeline_validation(base_state):
    """
    Verify SKILL actions are correctly validated and routed by the pipeline.
    """
    from src.engine.pipeline import AuthoritativeApplyPipeline
    from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate
    from src.core.enums import EntityRole

    attacker = create_mock_entity(1, pos=(10, 10))

    attacker = replace(
        attacker,
        identity=replace(
            attacker.identity,
            learned_skills={"HEAVY_STRIKE"},
        ),
        stamina=replace(
            attacker.stamina,
            current=100.0,
        ),
    )

    target = create_mock_entity(
        2,
        pos=(11, 10),
        faction="MONSTER",
        role=EntityRole.MONSTER,
    )

    state = replace(
        base_state,
        entities={
            1: attacker,
            2: target,
        },
    )

    raw_upd = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                task=TaskUpdate(
                    work_kind_set="ENTITY_ACT",
                    payload_set={
                        "action": "SKILL",
                        "skill_id": "HEAVY_STRIKE",
                        "target_id": 2,
                    },
                ),
            )
        }
    )

    refined = AuthoritativeApplyPipeline.refine(state, raw_upd)

    payload = refined.entity_updates[1].task.payload_set
    assert payload.get("outcome") == "SUCCESS", payload

    attacker_cd = replace(
        attacker,
        identity=replace(
            attacker.identity,
            cooldowns={"HEAVY_STRIKE": 200},
        ),
    )

    state_cd = replace(
        base_state,
        entities={
            1: attacker_cd,
            2: target,
        },
    )

    refined_cd = AuthoritativeApplyPipeline.refine(state_cd, raw_upd)

    payload_cd = refined_cd.entity_updates[1].task.payload_set
    assert payload_cd.get("outcome") == "FAILURE"
    assert payload_cd.get("reason") in (
        "INSUFFICIENT_READINESS",
        "SKILL_ON_COOLDOWN",
        "ReasonCode.SKILL_ON_COOLDOWN",
    )

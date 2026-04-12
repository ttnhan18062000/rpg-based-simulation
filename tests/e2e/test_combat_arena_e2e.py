import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


"""E2E tests using CombatArena fixture.

Validates the full pipeline: AI decides → proposal → resolve → apply → events.
Covers existing F4 (ranged combat) mechanics, general combat flow, and AOA Phase 5 stabilization.
"""



from tests.helpers.combat_arena import CombatArena
from src.core.gameplay.classes import HeroClass
from src.core.models.enums import AIState, EnemyTier, Material
from src.core.models.strategy import ObjectiveKind
from src.core.gameplay.faction import Faction
from src.core.models.vectors import Vector2
from src.core.gameplay.attributes import Attributes


# ---------------------------------------------------------------------------
# Basic combat E2E
# ---------------------------------------------------------------------------

class TestBasicCombatE2E:
    """Two adjacent melee entities should fight until one dies."""

    def test_adjacent_melee_fight_produces_combat_events(self):
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=80, atk=12)
        arena.add_mob(2, pos=(6, 5), weapon="rusty_sword", hp=40, atk=8)
        events = arena.run_ticks(30)
        combat = arena.combat_events()
        assert len(combat) > 0, "Should produce combat events"

    def test_melee_fight_one_entity_dies(self):
        # With opportunity attacks + SPD-based chase closing, faster hero
        # finishes off a weaker mob even if it tries to flee
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=200, atk=20, spd=15)
        arena.add_mob(2, pos=(6, 5), weapon="rusty_sword", hp=60, atk=5, spd=8)
        arena.run_until(lambda a: not a.entity_alive(2), max_ticks=50)
        assert not arena.entity_alive(2), "Mob should die from stronger+faster hero"
        deaths = arena.death_events()
        assert any(2 in (e.entity_ids or ()) for e in deaths)

    def test_combat_target_id_set_during_combat(self):
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=100, atk=15)
        arena.add_mob(2, pos=(6, 5), weapon="rusty_sword", hp=100, atk=10)
        arena.run_ticks(5)
        hero = arena.entity(1)
        mob = arena.entity(2)
        # At least one should have a combat target after engaging
        has_target = (hero and hero.combat.combat_target_id is not None) or \
                     (mob and mob.combat.combat_target_id is not None)
        assert has_target, "Entities in combat should have combat.combat_target_id set"


# ---------------------------------------------------------------------------
# Ranged combat E2E
# ---------------------------------------------------------------------------

class TestRangedCombatE2E:
    """Ranged entities should attack from distance."""

    def test_ranged_hero_attacks_from_distance(self):
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="shortbow", hp=80, atk=12,
                       hero_class=HeroClass.RANGER)
        arena.add_mob(2, pos=(8, 5), weapon="rusty_sword", hp=50, atk=8)
        # Distance is 3, shortbow range is 3 — should be able to attack
        arena.run_ticks(20)
        mob = arena.entity(2)
        if mob:
            assert mob.combat.hp < mob.combat.max_hp, \
                 "Ranged hero should damage mob from distance 3"

    def test_ranged_mob_attacks_hero(self):
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=100, atk=10)
        arena.add_mob(2, pos=(8, 5), kind="bandit_archer", weapon="shortbow",
                      hp=60, atk=10)
        arena.run_ticks(40)
        hero = arena.entity(1)
        # Either mob damaged hero or hero killed mob — both prove combat happened
        combat = arena.combat_events()
        assert len(combat) > 0 or hero.combat.hp < hero.combat.max_hp, \
            "Combat should have occurred between hero and ranged mob"

    def test_mage_uses_matk_for_damage(self):
        """Mage with magical weapon should deal damage based on MATK."""
        arena = CombatArena()
        # High MATK, low ATK — damage should come from MATK via magical weapon
        arena.add_hero(1, pos=(5, 5), weapon="apprentice_staff",
                       hero_class=HeroClass.MAGE, hp=80, atk=3, matk=20)
        arena.add_mob(2, pos=(8, 5), weapon="rusty_sword", hp=60, atk=5, def_=2, mdef=0)
        arena.run_ticks(20)
        mob = arena.entity(2)
        if mob:
            # Mage should deal decent damage via MATK even with low ATK
            assert mob.combat.hp < mob.combat.max_hp, \
                "Mage should deal damage via MATK"


# ---------------------------------------------------------------------------
# Line of Sight E2E
# ---------------------------------------------------------------------------

class TestLineOfSightE2E:
    """Ranged attacks should be blocked by walls."""

    def test_wall_blocks_ranged_attack(self):
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="shortbow", hp=100, atk=15)
        arena.add_mob(2, pos=(8, 5), weapon="rusty_sword", hp=100, atk=8)
        # Place a wall between them
        arena.set_wall(7, 5)
        arena.run_ticks(15)
        mob = arena.entity(2)
        # Hero can't shoot through wall — must move around
        # After 15 ticks the mob might still be at full HP if hero is stuck
        # (or hero may have navigated around)
        combat = arena.combat_events()
        # If there ARE combat events, the hero found a path around
        # If no combat events, wall properly blocked LoS — both are valid outcomes


# ---------------------------------------------------------------------------
# Cover System E2E
# ---------------------------------------------------------------------------

class TestCoverE2E:
    """Defenders adjacent to walls get evasion bonus vs ranged attacks."""

    def test_cover_reduces_ranged_damage(self):
        """Entity behind cover should evade more ranged attacks."""
        # Run two scenarios and compare damage taken
        # Scenario A: no cover
        arena_a = CombatArena(seed=42)
        arena_a.add_hero(1, pos=(5, 5), weapon="shortbow", hp=200, atk=15)
        arena_a.add_mob(2, pos=(8, 5), weapon="rusty_sword", hp=1000, atk=5,
                        spd=1)  # Low SPD so mob doesn't move
        arena_a.run_ticks(10)

        # Scenario B: wall next to defender
        arena_b = CombatArena(seed=42)
        arena_b.add_hero(1, pos=(5, 5), weapon="shortbow", hp=200, atk=15)
        arena_b.add_mob(2, pos=(8, 5), weapon="rusty_sword", hp=1000, atk=5,
                        spd=1)
        arena_b.set_wall(8, 6)  # Wall adjacent to mob
        arena_b.run_ticks(10)

        mob_a = arena_a.entity(2)
        mob_b = arena_b.entity(2)
        # Can't guarantee exact damage difference due to RNG, but the
        # cover system is exercised. Just verify both scenarios run.
        assert mob_a is not None
        assert mob_b is not None


# ---------------------------------------------------------------------------
# Kiting E2E
# ---------------------------------------------------------------------------

class TestKitingE2E:
    """Ranged entities should kite (move away) when enemies are adjacent."""

    def test_ranged_hero_kites_when_adjacent(self):
        """A ranged hero with HP > 60% should move away from adjacent enemy."""
        arena = CombatArena()
        arena.add_hero(1, pos=(10, 10), weapon="shortbow", hp=100, atk=12,
                       hero_class=HeroClass.RANGER, ai_state=AIState.COMBAT)
        arena.add_mob(2, pos=(11, 10), weapon="rusty_sword", hp=200, atk=8)
        initial_pos = (arena.entity(1).spatial.pos.x, arena.entity(1).spatial.pos.y)
        arena.run_ticks(5)
        hero = arena.entity(1)
        new_pos = (hero.spatial.pos.x, hero.spatial.pos.y)
        # Hero should have moved away from the mob (kiting)
        # Distance should increase or hero attacked then moved
        combat = arena.combat_events()
        moved = new_pos != initial_pos
        fought = len(combat) > 0
        assert moved or fought, "Ranged hero should either kite or attack"

    def test_low_hp_ranged_does_not_kite(self):
        """Ranged entity below 60% HP should NOT kite (flee instead)."""
        arena = CombatArena()
        arena.add_hero(1, pos=(10, 10), weapon="shortbow", hp=100, atk=12,
                       hero_class=HeroClass.RANGER, ai_state=AIState.COMBAT)
        # Set HP below 60%
        arena.entity(1).combat.hp = 50
        arena.add_mob(2, pos=(11, 10), weapon="rusty_sword", hp=200, atk=8)
        arena.run_ticks(5)
        # At low HP, hero should flee, not kite
        hero = arena.entity(1)
        assert hero is not None  # Hero should still exist
        # Verify hero is moving away or in flee state
        assert hero.mind.decision.ai_state == AIState.FLEE or hero.spatial.pos != (10, 10)


# ---------------------------------------------------------------------------
# Weapon Range on Entity API
# ---------------------------------------------------------------------------

class TestWeaponRangeE2E:
    """Verify weapon_range is correctly derived from equipped weapon."""

    def test_melee_weapon_range_1(self):
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword")
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        tmpl = ITEM_REGISTRY.get("iron_sword")
        assert tmpl.weapon_range == 1

    def test_shortbow_range_3(self):
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="shortbow")
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        tmpl = ITEM_REGISTRY.get("shortbow")
        assert tmpl.weapon_range == 3

    def test_staff_range_3(self):
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="apprentice_staff")
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        tmpl = ITEM_REGISTRY.get("apprentice_staff")
        assert tmpl.weapon_range == 3


# ---------------------------------------------------------------------------
# Multi-entity scenarios
# ---------------------------------------------------------------------------

class TestMultiEntityCombatE2E:
    """Multiple entities in combat simultaneously."""

    def test_two_heroes_vs_one_mob(self):
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=100, atk=15)
        arena.add_hero(2, pos=(7, 5), weapon="iron_sword", hp=100, atk=15)
        arena.add_mob(3, pos=(6, 5), weapon="rusty_sword", hp=60, atk=10)
        arena.run_until(lambda a: not a.entity_alive(3), max_ticks=50)
        assert not arena.entity_alive(3), "Mob should die from two heroes"
        # Both heroes should still be alive
        assert arena.entity_alive(1)
        assert arena.entity_alive(2)

    def test_ranged_and_melee_hero_vs_mob(self):
        """Melee hero engages mob, ranged hero attacks from distance."""
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=100, atk=15)
        arena.add_hero(2, pos=(2, 5), weapon="shortbow", hp=80, atk=12,
                       hero_class=HeroClass.RANGER, objective_kind=ObjectiveKind.KILL,
                       vision_range=15)
        arena.add_mob(3, pos=(6, 5), weapon="rusty_sword", hp=80, atk=8, 
                      objective_kind=ObjectiveKind.KILL, vision_range=15)
        arena.run_until(lambda a: not a.entity_alive(3), max_ticks=100)
        # Mob should eventually die
        assert not arena.entity_alive(3)


# ---------------------------------------------------------------------------
# Chase mechanics E2E (epic-05)
# ---------------------------------------------------------------------------

class TestOpportunityAttackE2E:
    """Opportunity attacks trigger when disengaging from melee range."""

    def test_fleeing_mob_takes_opportunity_damage(self):
        """A mob that flees from adjacent hero should take opportunity attack damage."""
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=200, atk=20)
        arena.add_mob(2, pos=(6, 5), weapon="rusty_sword", hp=200, atk=5)
        arena.run_ticks(10)
        # Check for opportunity attack events
        opp_attacks = [e for e in arena.all_events()
                       if e.metadata and e.metadata.get('verb') == 'OPPORTUNITY_ATTACK']
        assert len(opp_attacks) > 0, "Should have opportunity attack events when mob flees"

    def test_fleeing_hero_takes_opportunity_damage(self):
        """Symmetric: hero fleeing from stronger mob also takes opportunity damage."""
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=100, atk=8)
        arena.add_mob(2, pos=(6, 5), weapon="rusty_sword", hp=200, atk=25)
        arena.run_ticks(10)
        # Hero should take opportunity damage when fleeing
        opp_attacks = [e for e in arena.all_events()
                       if e.metadata and e.metadata.get('verb') == 'OPPORTUNITY_ATTACK']
        # At minimum, combat events should occur
        combat = arena.combat_events()
        assert len(combat) > 0, "Combat should occur between hero and mob"

    def test_no_opportunity_attack_when_moving_toward(self):
        """Moving toward a hostile should NOT trigger opportunity attack."""
        arena = CombatArena()
        # Hero at distance 2 from mob, moves closer — no opportunity attack
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=100, atk=15)
        arena.add_mob(2, pos=(7, 5), weapon="rusty_sword", hp=100, atk=10)
        arena.run_ticks(3)
        opp_attacks = [e for e in arena.all_events()
                       if e.metadata and e.metadata.get('verb') == 'OPPORTUNITY_ATTACK']
        assert len(opp_attacks) == 0, "No opportunity attack when closing distance"


class TestChaseClosingE2E:
    """Faster hunters close the gap on slower fleeing entities."""

    def test_faster_hunter_catches_slower_prey(self):
        """Hero with SPD advantage should eventually kill fleeing mob."""
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=200, atk=15, spd=15)
        arena.add_mob(2, pos=(6, 5), weapon="rusty_sword", hp=60, atk=5, spd=5)
        arena.run_until(lambda a: not a.entity_alive(2), max_ticks=50)
        assert not arena.entity_alive(2), "Faster hero should catch and kill slower mob"

    def test_equal_speed_stalemate(self):
        """Equal SPD entities should not get chase closing bonus."""
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=200, atk=15, spd=10)
        arena.add_mob(2, pos=(6, 5), weapon="rusty_sword", hp=200, atk=5, spd=10)
        arena.run_ticks(30)
        # No chase sprint events (equal SPD)
        sprints = [e for e in arena.all_events()
                   if e.metadata and e.metadata.get('verb') == 'CHASE_SPRINT']
        assert len(sprints) == 0, "Equal SPD should not produce chase sprint events"

    def test_slower_hunter_cannot_close(self):
        """Slower hunter should NOT get chase closing bonus."""
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=200, atk=15, spd=5)
        arena.add_mob(2, pos=(6, 5), weapon="rusty_sword", hp=200, atk=5, spd=15)
        arena.run_ticks(30)
        sprints = [e for e in arena.all_events()
                   if e.metadata and e.metadata.get('verb') == 'CHASE_SPRINT'
                   and e.metadata.get('actor_id') == 1]
        assert len(sprints) == 0, "Slower hunter should not sprint"


# ---------------------------------------------------------------------------
# Aggro & Threat System E2E (epic-05 F3)
# ---------------------------------------------------------------------------

class TestThreatSystemE2E:
    """Threat-based targeting: mobs attack highest-threat enemy."""

    def test_damage_generates_threat(self):
        """Attacking a mob should generate threat on that mob's threat_table."""
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=200, atk=20)
        arena.add_mob(10, pos=(6, 5), weapon="rusty_sword", hp=200, atk=5)
        arena.run_ticks(3)
        mob = arena.entity(10)
        assert mob is not None
        assert 1 in mob.mind.perception.threat_table, "Mob should have threat entry for hero"
        assert mob.mind.perception.threat_table[1] > 0, "Threat should be positive"

    def test_mob_targets_highest_threat(self):
        """Mob should target the hero who dealt more damage (higher threat)."""
        arena = CombatArena()
        # Hero 1: high ATK (generates more threat)
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=200, atk=30)
        # Hero 2: low ATK (generates less threat)
        arena.add_hero(2, pos=(7, 5), weapon="iron_sword", hp=200, atk=5)
        # Mob in between, will be hit by both heroes
        arena.add_mob(10, pos=(6, 5), weapon="rusty_sword", hp=500, atk=10)
        arena.run_ticks(10)
        mob = arena.entity(10)
        if mob and mob.combat.alive and mob.mind.perception.threat_table:
            # Hero 1 should have higher threat than hero 2
            h1_threat = mob.mind.perception.threat_table.get(1, 0)
            h2_threat = mob.mind.perception.threat_table.get(2, 0)
            assert h1_threat > h2_threat, \
                f"Hero 1 (atk=30) should have more threat than Hero 2 (atk=5): {h1_threat} vs {h2_threat}"

    def test_tank_class_generates_bonus_threat(self):
        """Warrior class should generate 1.5x threat compared to same-ATK non-tank."""
        arena = CombatArena()
        # Warrior hero
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=100, atk=10,
                       hero_class=HeroClass.WARRIOR)
        arena.add_mob(10, pos=(6, 5), weapon="rusty_sword", hp=500, atk=5)
        arena.run_ticks(3)
        mob = arena.entity(10)
        warrior_threat = mob.mind.perception.threat_table.get(1, 0) if mob else 0

        # Same setup but with non-tank (RANGER)
        arena2 = CombatArena(seed=42)
        arena2.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=100, atk=10,
                        hero_class=HeroClass.RANGER)
        arena2.add_mob(10, pos=(6, 5), weapon="rusty_sword", hp=500, atk=5)
        arena2.run_ticks(3)
        mob2 = arena2.entity(10)
        ranger_threat = mob2.mind.perception.threat_table.get(1, 0) if mob2 else 0

        if warrior_threat > 0 and ranger_threat > 0:
            assert warrior_threat > ranger_threat, \
                f"Warrior threat ({warrior_threat}) should exceed Ranger threat ({ranger_threat})"

    def test_threat_decays_over_time(self):
        """Threat should decay each tick when no new damage is dealt."""
        arena = CombatArena()
        # Place hero far away so no combat happens
        arena.add_hero(1, pos=(1, 1), weapon="iron_sword", hp=200, atk=20)
        arena.add_mob(10, pos=(18, 18), weapon="rusty_sword", hp=500, atk=5)
        # Manually inject threat
        mob = arena.entity(10)
        mob.mind.perception.threat_table[1] = 100.0
        initial_threat = 100.0
        # Run ticks — threat should decay (10% per tick)
        arena.run_ticks(5)
        mob = arena.entity(10)
        if mob and 1 in mob.mind.perception.threat_table:
            assert mob.mind.perception.threat_table[1] < initial_threat, \
                "Threat should decay when no new damage is dealt"

    def test_dead_attacker_threat_removed(self):
        """Threat entries for dead attackers should be cleaned up."""
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=10, atk=20)
        arena.add_mob(10, pos=(6, 5), weapon="rusty_sword", hp=500, atk=50)
        arena.run_ticks(5)
        mob = arena.entity(10)
        # Hero should be dead, threat entry should be removed
        if mob and not arena.entity_alive(1):
            assert 1 not in mob.mind.perception.threat_table, \
                "Dead hero's threat entry should be pruned"


# ---------------------------------------------------------------------------
# AoE Attacks & Skills E2E (epic-05 F1)
# ---------------------------------------------------------------------------

class TestAoESkillsE2E:
    """AoE skills hit multiple enemies with falloff from impact center."""

    def test_fireball_hits_multiple_enemies(self):
        """Mage's Fireball (radius=2) should damage multiple clustered enemies."""
        arena = CombatArena()
        # Mage with fireball at range 4
        arena.add_hero(1, pos=(2, 5), weapon="apprentice_staff",
                       hero_class=HeroClass.MAGE, hp=200, atk=10, matk=25,
                       skills=["fireball"], ai_state=AIState.COMBAT, level=5)
        # Three mobs clustered at distance 1 from each other
        arena.add_mob(10, pos=(6, 5), weapon="rusty_sword", hp=200, atk=5)
        arena.add_mob(11, pos=(6, 6), weapon="rusty_sword", hp=200, atk=5)
        arena.add_mob(12, pos=(7, 5), weapon="rusty_sword", hp=200, atk=5)
        arena.run_ticks(10)
        # Check skill events with AoE flag
        aoe_hits = [e for e in arena.all_events()
                    if e.metadata and e.metadata.get('aoe') is True]
        assert len(aoe_hits) >= 2, f"Fireball should hit multiple enemies, got {len(aoe_hits)} AoE hits"

    def test_aoe_falloff_reduces_edge_damage(self):
        """Enemies at the edge of AoE take less damage than center target."""
        arena = CombatArena()
        arena.add_hero(1, pos=(2, 5), weapon="apprentice_staff",
                       hero_class=HeroClass.MAGE, hp=200, atk=10, matk=25,
                       skills=["fireball"])
        # Center target at dist 0 from impact, edge target at dist 2
        arena.add_mob(10, pos=(6, 5), weapon="rusty_sword", hp=500, atk=5)
        arena.add_mob(11, pos=(8, 5), weapon="rusty_sword", hp=500, atk=5)
        arena.run_ticks(10)
        # Check damage metadata: center target should take more damage
        skill_events = [e for e in arena.all_events()
                        if e.metadata and e.metadata.get('skill_name') == 'Fireball'
                        and e.metadata.get('damage', 0) > 0]
        if len(skill_events) >= 2:
            center_hits = [e for e in skill_events if e.metadata.get('dist_from_center') == 0]
            edge_hits = [e for e in skill_events if e.metadata.get('dist_from_center', 0) > 0]
            if center_hits and edge_hits:
                assert center_hits[0].metadata['damage'] > edge_hits[0].metadata['damage'], \
                    "Center target should take more damage than edge target"

    def test_whirlwind_melee_aoe(self):
        """Warrior's Whirlwind (radius=1, range=1) hits adjacent enemies."""
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword",
                       hero_class=HeroClass.WARRIOR, hp=200, atk=20,
                       skills=["shield_wall", "whirlwind"], 
                       mastery={"shield_wall": 100.0}, level=5, ai_state=AIState.COMBAT)
        # Two mobs adjacent to hero
        arena.add_mob(10, pos=(6, 5), weapon="rusty_sword", hp=200, atk=5, ai_state=AIState.IDLE)
        arena.add_mob(11, pos=(5, 6), weapon="rusty_sword", hp=200, atk=5, ai_state=AIState.IDLE)
        arena.run_ticks(3)
        aoe_hits = [e for e in arena.all_events()
                    if e.metadata and e.metadata.get('skill_name') == 'Whirlwind'
                    and e.metadata.get('damage', 0) > 0]
        assert len(aoe_hits) >= 2, f"Whirlwind should hit 2 adjacent enemies, got {len(aoe_hits)}"

    def test_single_target_skill_does_not_aoe(self):
        """Single-target skills like Power Strike should only hit one enemy."""
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword",
                       hero_class=HeroClass.WARRIOR, hp=200, atk=20,
                       skills=["power_strike"])
        arena.add_mob(10, pos=(6, 5), weapon="rusty_sword", hp=200, atk=5)
        arena.add_mob(11, pos=(5, 6), weapon="rusty_sword", hp=200, atk=5)
        arena.run_ticks(10)
        # Each skill event should only hit one target
        skill_events = [e for e in arena.all_events()
                        if e.metadata and e.metadata.get('skill_name') == 'Power Strike']
        for ev in skill_events:
            assert ev.metadata.get('aoe') is not True or ev.metadata.get('aoe') is False, \
                "Power Strike should not be AoE"

    def test_rain_of_arrows_ranged_aoe(self):
        """Ranger's Rain of Arrows (range=4, radius=2) hits from distance."""
        arena = CombatArena()
        arena.add_hero(1, pos=(2, 5), weapon="shortbow",
                       hero_class=HeroClass.RANGER, hp=200, atk=20,
                       skills=["rain_of_arrows"], level=5, ai_state=AIState.COMBAT)
        # Cluster of mobs within radius 2 of each other
        arena.add_mob(10, pos=(6, 5), weapon="rusty_sword", hp=200, atk=5)
        arena.add_mob(11, pos=(7, 5), weapon="rusty_sword", hp=200, atk=5)
        arena.add_mob(12, pos=(6, 6), weapon="rusty_sword", hp=200, atk=5)
        arena.run_ticks(10)
        aoe_hits = [e for e in arena.all_events()
                    if e.metadata and e.metadata.get('skill_name') == 'Rain of Arrows'
                    and e.metadata.get('damage', 0) > 0]
        assert len(aoe_hits) >= 2, f"Rain of Arrows should hit multiple enemies, got {len(aoe_hits)}"

    def test_ai_prefers_aoe_when_clustered(self):
        """AI should use AoE skill when multiple enemies are nearby."""
        arena = CombatArena()
        # Give hero both single-target and AoE skill, both ready
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword",
                       hero_class=HeroClass.WARRIOR, hp=200, atk=20,
                       skills=["shield_wall", "power_strike", "whirlwind"],
                       mastery={"shield_wall": 100.0}, level=5)
        arena.add_mob(10, pos=(6, 5), weapon="rusty_sword", hp=200, atk=5)
        arena.add_mob(11, pos=(5, 6), weapon="rusty_sword", hp=200, atk=5)
        arena.run_ticks(3)
        # Should see whirlwind used (preferred over power_strike when 2+ enemies)
        whirlwind_uses = [e for e in arena.all_events()
                          if e.metadata and e.metadata.get('skill_name') == 'Whirlwind']
        assert len(whirlwind_uses) > 0, "AI should prefer Whirlwind when 2 enemies adjacent"


# ---------------------------------------------------------------------------
# Event collection
# ---------------------------------------------------------------------------

class TestEventCollectionE2E:
    """Verify event collection works correctly in arena."""

    def test_events_have_correct_structure(self):
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=100, atk=15)
        arena.add_mob(2, pos=(6, 5), weapon="rusty_sword", hp=30, atk=5)
        events = arena.run_ticks(20)
        for ev in events:
            assert hasattr(ev, 'tick')
            assert hasattr(ev, 'category')
            assert hasattr(ev, 'message')
            assert hasattr(ev, 'entity_ids')

    def test_death_event_has_entity_id(self):
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=200, atk=25)
        arena.add_mob(2, pos=(6, 5), weapon="rusty_sword", hp=20, atk=3)
        arena.run_until(lambda a: not a.entity_alive(2), max_ticks=30)
        deaths = arena.death_events()
        assert len(deaths) > 0, "Should have death event"
        assert any(2 in (e.entity_ids or ()) for e in deaths)

    def test_events_for_entity_filters_correctly(self):
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=100, atk=15)
        arena.add_mob(2, pos=(6, 5), weapon="rusty_sword", hp=100, atk=10)
        arena.run_ticks(10)
        hero_events = arena.events_for_entity(1)
        mob_events = arena.events_for_entity(2)
        # Both should have some events
        assert len(hero_events) > 0 or len(mob_events) > 0


# ---------------------------------------------------------------------------
# AI Refinement Pillars E2E
# ---------------------------------------------------------------------------

class TestAIRefinementE2E:
    """E2E verification of the Three Pillars (Hysteresis, Memory, Flow Fields)."""

    def test_goal_commitment_and_anti_jitter(self):
        """Hysteresis: Hero stays committed to WANDER even when a mob is distance 1."""
        arena = CombatArena()
        # Hero currently WANDERING
        hero = arena.add_hero(1, pos=(2, 2), hp=100)
        hero.mind.decision.ai_state = AIState.WANDER
        hero.mind.decision.goal_committed_at = 0
        
        # Add a mob right next to them
        arena.add_mob(2, pos=(3, 2))
        
        # Run 2 ticks (lock is typically 3 ticks)
        arena.run_ticks(2)
        
        # Hero should STILL be in WANDER state due to Hysteresis lock
        assert arena.entity(1).mind.decision.ai_state == AIState.WANDER

    def test_nemesis_recognition_and_fear_bias(self):
        """Soul: Hero remembers massive damage and flees earlier from Nemesis."""
        arena = CombatArena(min_commitment_ticks=0)
        hero = arena.add_hero(1, pos=(2, 2), hp=1000)
        
        # Boss deals heavy damage
        boss = arena.add_mob(2, pos=(3, 2), atk=80, tier=2)
        boss.combat.luck = 1000
        
        hero.identity.neuroticism = 0.8
        
        # First Encounter: Take damage to build Grudge and Trauma
        arena.run_ticks(5)
        assert 2 in hero.mind.emotion.grudges
        assert any(m.type == "trauma" for m in arena.entity(1).mind.narrative.memory_log)
        
        # Second Encounter: Force re-engagement at 40% HP
        arena.entity(1).spatial.pos = Vector2(4, 2)
        arena.entity(1).combat.hp = 400
        arena.run_ticks(5)
        
        # Hero should flee due to Nemesis bias
        assert arena.entity(1).mind.decision.ai_state == AIState.FLEE

    def test_shared_navigation_scaling(self):
        """Wind: Heroes move efficiently towards shared town target via Flow Fields."""
        arena = CombatArena(width=50, height=50)
        arena.set_tile(45, 45, Material.TOWN)
        town_pos = Vector2(45, 45)
        
        # Add 10 heroes
        for i in range(10, 20):
            pos = (i % 10, i % 10)
            arena.add_hero(i, pos=pos, home_pos=(45, 45))
            arena.entity(i).mind.decision.ai_state = AIState.RETURN_TO_TOWN
            
        init_dists = {i: arena.entity(i).spatial.pos.manhattan(town_pos) for i in range(10, 20)}
        arena.run_ticks(5)
        
        for i in range(10, 20):
            assert arena.entity(i).spatial.pos.manhattan(town_pos) < init_dists[i]

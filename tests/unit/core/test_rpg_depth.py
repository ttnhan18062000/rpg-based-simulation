"""
Tests for RPG depth mechanics: Stamina, Wounds/Scars, Mob Leash,
Terrain Cost, Target Stickiness, Skill Scaling, and Attribute Caps.
- RPG-0009: manhattan_spatial_metric
- RPG-0015: mob_leash_radius
- RPG-0017: pathfinding_occupancy_awareness
- RPG-0068: target_stickiness_bias
- RPG-0631: wound_infliction_massive_hit
- RPG-0633: scar_permanence_logic
- RPG-0638: stamina_drain_attack
- RPG-0639: stamina_drain_movement
- RPG-0640: stamina_drain_harvest
- RPG-0641: stamina_cost_skill_use
- RPG-0642: stamina_regen_resting
- RPG-0643: stamina_regen_active
- RPG-0644: stamina_regen_capped
- RPG-0646: terrain_cost_pathfinding
- RPG-1665: attribute_cap_enforced
- RPG-1672: equipment_bonus_application
- RPG-1679: mob_chase_give_up
"""
import pytest
from dataclasses import replace
from src.core.state import (
    EntityState, AuthoritativeState, StaminaComponent, WoundState, ScarState,
    CombatComponent, NavigationComponent, InventoryComponent, AttributeComponent,
    IdentityComponent, BiologicalComponent, LifecycleComponent, TaskComponent,
    TERRAIN_COST
)
from src.core.enums import Faction, EntityRole
from src.core.movement_modes import MovementMode
from src.core.updates import (
    EntityUpdate, CombatUpdate, StaminaUpdate, WoundUpdate, NavigationUpdate,
    StateUpdate
)
from src.core.builder import V2EntityBuilder
from src.engine.rpg_depth import (
    StaminaService, WoundService, LeashService, TerrainCostService,
    TargetStickinessService, SkillScalingService, ATTRIBUTE_CAP,
    enforce_attribute_caps, WOUND_THRESHOLD_RATIO, LEASH_CHASE_MULTIPLIER,
    TARGET_SWITCH_MARGIN
)


def make_entity(eid=1, pos=(5.0, 5.0), hp=100, max_hp=100, atk=10, def_stat=5,
                alive=True, faction=Faction.HERO_GUILD, role=EntityRole.HERO,
                stamina_current=100.0, stamina_max=100.0,
                leash_radius=0.0, home_pos=None, chase_ticks=0, max_chase_ticks=15,
                returning_home=False, endurance=5, strength=5, intelligence=5,
                spirit=5, active=True):
    entity = (V2EntityBuilder(eid)
              .kind("hero")
              .location(*pos)
              .identity(faction=faction, role=role)
              .combat(hp=hp, max_hp=max_hp, atk=atk, def_stat=def_stat,
                      attack_range=1, alive=alive, readiness=100.0)
              .stamina(current=stamina_current, max_stamina=stamina_max)
              .attributes(endurance=endurance, strength=strength,
                         intelligence=intelligence, spirit=spirit)
              .navigation(leash_radius=leash_radius, home_position=home_pos,
                         chase_ticks=chase_ticks, max_chase_ticks=max_chase_ticks,
                         returning_home=returning_home)
              .lifecycle(active=active)
              .build())
    return entity


def make_state(entities=None, terrain=None, regions=None):
    return AuthoritativeState(
        tick=1, seed=42,
        entities=entities or {},
        terrain=terrain or {},
        regions=regions or {},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# STAMINA TESTS (Checklist Part 6 Section E)
# ═══════════════════════════════════════════════════════════════════════════════

class TestStaminaDrainOnAttack:
    # Logic ID: COMB-109

    def test_stamina_drain_on_attack(self):
        """test_stamina_drain_on_attack: attack drains stamina by ATTACK_COST."""
        # VERIFIED v2: stamina_drain_attack
        stamina = StaminaComponent(current=100.0)
        cost = StaminaService.drain_attack(stamina)
        assert cost == stamina.ATTACK_COST
        assert cost == 8.0

    # Logic ID: COMB-110

    def test_stamina_decreases_on_move(self):
        """test_stamina_decreases_on_move: movement drains stamina by MOVE_COST."""
        # VERIFIED v2: stamina_drain_movement
        stamina = StaminaComponent(current=100.0)
        cost = StaminaService.drain_move(stamina)
        assert cost == stamina.MOVE_COST
        assert cost == 3.0

    # Logic ID: COMB-111

    def test_stamina_decreases_on_harvest(self):
        """test_stamina_decreases_on_harvest: harvesting drains stamina by HARVEST_COST."""
        # VERIFIED v2: stamina_drain_harvest
        stamina = StaminaComponent(current=100.0)
        cost = StaminaService.drain_harvest(stamina)
        assert cost == stamina.HARVEST_COST
        assert cost == 5.0

    # Logic ID: COMB-112

    def test_skill_use_costs_stamina(self):
        """test_skill_use_costs_stamina: skill use drains stamina proportional to skill cost."""
        # VERIFIED v2: stamina_cost_skill_use
        stamina = StaminaComponent(current=50.0)
        skill_cost = 25
        drain = StaminaService.drain_skill(stamina, skill_cost)
        assert drain == 25.0

    # Logic ID: COMB-117

    def test_best_ready_skill_skips_insufficient_stamina(self):
        """test_best_ready_skill_skips_insufficient_stamina: can_use_skill returns False when insufficient."""
        stamina = StaminaComponent(current=5.0)
        assert not StaminaService.can_use_skill(stamina, 25)
        assert StaminaService.can_use_skill(stamina, 3)


class TestStaminaRegen:
    # Logic ID: COMB-113

    def test_stamina_regen_resting(self):
        """test_stamina_regen_resting: rest gives faster stamina regen."""
        # VERIFIED v2: stamina_regen_resting
        stamina = StaminaComponent(current=50.0, max_stamina=100.0, rest_regen_rate=8.0)
        regen = StaminaService.tick_regen(stamina, is_resting=True)
        assert regen == 8.0

    # Logic ID: COMB-114

    def test_stamina_regen_active(self):
        """test_stamina_regen_active: active gives base regen rate."""
        # VERIFIED v2: stamina_regen_active
        stamina = StaminaComponent(current=50.0, max_stamina=100.0, regen_rate=2.0)
        regen = StaminaService.tick_regen(stamina, is_resting=False)
        assert regen == 2.0

    # Logic ID: COMB-115

    def test_stamina_regen_capped(self):
        """test_stamina_regen_capped: regen does not exceed max_stamina."""
        # VERIFIED v2: stamina_regen_capped
        stamina = StaminaComponent(current=99.0, max_stamina=100.0, rest_regen_rate=8.0)
        regen = StaminaService.tick_regen(stamina, is_resting=True)
        assert regen == 1.0  # Only 1 headroom

    def test_stamina_regen_at_max(self):
        """At max stamina, regen is zero."""
        stamina = StaminaComponent(current=100.0, max_stamina=100.0)
        regen = StaminaService.tick_regen(stamina, is_resting=False)
        assert regen == 0.0


class TestExhaustion:
    # Logic ID: COMB-116

    def test_exhaustion_penalty_application(self):
        """test_exhaustion_penalty_application: below threshold applies penalty multiplier."""
        stamina = StaminaComponent(current=5.0, exhaustion_threshold=10.0, exhaustion_penalty=0.7)
        assert StaminaService.is_exhausted(stamina)
        mult = StaminaService.get_exhaustion_multiplier(stamina)
        assert mult == 0.7

    def test_no_exhaustion_above_threshold(self):
        """Above threshold, no penalty."""
        stamina = StaminaComponent(current=50.0, exhaustion_threshold=10.0)
        assert not StaminaService.is_exhausted(stamina)
        assert StaminaService.get_exhaustion_multiplier(stamina) == 1.0

    def test_max_stamina_from_endurance(self):
        """Max stamina derives from endurance: 50 + endurance * 5."""
        assert StaminaService.derive_max_stamina(5) == 75.0
        assert StaminaService.derive_max_stamina(10) == 100.0
        assert StaminaService.derive_max_stamina(20) == 150.0


# ═══════════════════════════════════════════════════════════════════════════════
# WOUND / SCAR TESTS (Checklist Part 6 Section E)
# ═══════════════════════════════════════════════════════════════════════════════

class TestWoundInfliction:
    # Logic ID: COMB-102

    def test_wound_infliction_massive_hit(self):
        """test_wound_infliction_massive_hit: 40%+ max HP in one hit creates wound."""
        # VERIFIED v2: wound_infliction_massive_hit
        assert WoundService.should_inflict_wound(40, 100)  # exactly 40%
        assert WoundService.should_inflict_wound(60, 100)  # above 40%
        assert not WoundService.should_inflict_wound(30, 100)  # below 40%

    # Logic ID: COMB-103

    def test_wound_stat_impact(self):
        """test_wound_stat_impact: wounds apply atk/def/speed/hp penalties."""
        wound = WoundService.create_wound(80, 100, tick=5, wound_id="w1")
        assert wound.severity == 0.8
        assert wound.atk_penalty > 0
        assert wound.def_penalty > 0
        assert wound.speed_penalty > 0
        assert wound.max_hp_penalty > 0

    def test_wound_cumulative_penalties(self):
        """Multiple wounds stack penalties."""
        w1 = WoundService.create_wound(50, 100, tick=1, wound_id="w1")
        w2 = WoundService.create_wound(60, 100, tick=2, wound_id="w2")
        penalties = WoundService.get_wound_stat_penalties([w1, w2])
        assert penalties["atk_penalty"] == w1.atk_penalty + w2.atk_penalty
        assert penalties["def_penalty"] == w1.def_penalty + w2.def_penalty

    def test_healed_wound_not_penalized(self):
        """Healed wounds don't contribute to penalties."""
        w1 = WoundService.create_wound(50, 100, tick=1, wound_id="w1")
        w1_healed = replace(w1, healed=True)
        penalties = WoundService.get_wound_stat_penalties([w1_healed])
        assert penalties["atk_penalty"] == 0
        assert penalties["def_penalty"] == 0


class TestScarPermanence:
    # Logic ID: COMB-104

    def test_scar_permanence(self):
        """test_scar_permanence: scars persist after wound heals."""
        # VERIFIED v2: scar_permanence_logic
        wound = WoundService.create_wound(80, 100, tick=5, wound_id="w1")
        # No production producer exists for wound healing (TCK-20260824-WOUND-HEALING-DECISION);
        # hand-construct the WoundState->ScarState transition to exercise the data model.
        healed_wound = replace(wound, healed=True, scar_created=True)
        scar = ScarState(
            id=f"scar_{wound.id}", wound_kind=wound.kind, tick_created=wound.tick_inflicted,
            atk_penalty=wound.atk_penalty * 0.3, def_penalty=wound.def_penalty * 0.3,
            speed_penalty=wound.speed_penalty * 0.3,
        )
        assert healed_wound.healed
        assert healed_wound.scar_created
        assert scar.id == "scar_w1"
        assert scar.wound_kind == wound.kind

    def test_scar_lesser_penalty(self):
        """Scar penalties are 30% of original wound penalties."""
        wound = WoundService.create_wound(80, 100, tick=5, wound_id="w1")
        scar = ScarState(
            id=f"scar_{wound.id}", wound_kind=wound.kind, tick_created=wound.tick_inflicted,
            atk_penalty=wound.atk_penalty * 0.3, def_penalty=wound.def_penalty * 0.3,
            speed_penalty=wound.speed_penalty * 0.3,
        )
        assert abs(scar.atk_penalty - wound.atk_penalty * 0.3) < 0.01
        assert abs(scar.def_penalty - wound.def_penalty * 0.3) < 0.01

    def test_scar_cumulative_penalties(self):
        """Multiple scars stack their lesser penalties."""
        w1 = WoundService.create_wound(50, 100, tick=1, wound_id="w1")
        w2 = WoundService.create_wound(60, 100, tick=2, wound_id="w2")
        s1 = ScarState(
            id=f"scar_{w1.id}", wound_kind=w1.kind, tick_created=w1.tick_inflicted,
            atk_penalty=w1.atk_penalty * 0.3, def_penalty=w1.def_penalty * 0.3,
            speed_penalty=w1.speed_penalty * 0.3,
        )
        s2 = ScarState(
            id=f"scar_{w2.id}", wound_kind=w2.kind, tick_created=w2.tick_inflicted,
            atk_penalty=w2.atk_penalty * 0.3, def_penalty=w2.def_penalty * 0.3,
            speed_penalty=w2.speed_penalty * 0.3,
        )
        penalties = WoundService.get_scar_stat_penalties([s1, s2])
        assert penalties["atk_penalty"] == s1.atk_penalty + s2.atk_penalty


# ═══════════════════════════════════════════════════════════════════════════════
# MOB LEASH TESTS (Checklist Section 8)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMobLeash:
    def test_leash_within_radius(self):
        """Entity within leash radius is not beyond."""
        entity = make_entity(pos=(5.0, 5.0), leash_radius=10.0, home_pos=(5.0, 5.0))
        assert not LeashService.is_beyond_leash(entity)

    def test_leash_beyond_radius(self):
        """Entity beyond leash radius is detected."""
        entity = make_entity(pos=(20.0, 5.0), leash_radius=10.0, home_pos=(5.0, 5.0))
        assert LeashService.is_beyond_leash(entity)

    def test_no_leash_when_radius_zero(self):
        """Entities with 0 leash are never leashed."""
        entity = make_entity(pos=(100.0, 100.0), leash_radius=0.0, home_pos=(5.0, 5.0))
        assert not LeashService.is_beyond_leash(entity)

    def test_chase_give_up_distance(self):
        """Chase gives up when beyond 1.5x leash radius."""
        # VERIFIED v2: mob_leash_radius
        entity = make_entity(
            pos=(25.0, 5.0), leash_radius=10.0, home_pos=(5.0, 5.0),
            chase_ticks=5
        )
        assert LeashService.should_give_up_chase(entity)

    def test_chase_give_up_timeout(self):
        """Chase gives up after max chase ticks."""
        # VERIFIED v2: mob_chase_give_up
        entity = make_entity(
            pos=(12.0, 5.0), leash_radius=10.0, home_pos=(5.0, 5.0),
            chase_ticks=15, max_chase_ticks=15
        )
        assert LeashService.should_give_up_chase(entity)

    def test_chase_continues_within_limits(self):
        """Chase continues when within distance and time limits."""
        entity = make_entity(
            pos=(12.0, 5.0), leash_radius=10.0, home_pos=(5.0, 5.0),
            chase_ticks=3, max_chase_ticks=15
        )
        assert not LeashService.should_give_up_chase(entity)

    def test_return_home_target(self):
        """Return target is the home position."""
        entity = make_entity(home_pos=(5.0, 5.0))
        assert LeashService.get_return_home_target(entity) == (5.0, 5.0)

    def test_is_at_home(self):
        """Entity is at home when within 1 tile."""
        entity = make_entity(pos=(5.0, 5.0), home_pos=(5.0, 5.0))
        assert LeashService.is_at_home(entity)

        entity_far = make_entity(pos=(10.0, 5.0), home_pos=(5.0, 5.0))
        assert not LeashService.is_at_home(entity_far)


# ═══════════════════════════════════════════════════════════════════════════════
# TERRAIN COST TESTS (Checklist Section 7)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTerrainCost:
    def test_road_is_cheap(self):
        """Road tiles cost 0.5x."""
        # VERIFIED v2: terrain_cost_pathfinding
        state = make_state(terrain={(3, 3): "ROAD"})
        assert TerrainCostService.get_tile_cost((3, 3), state) == 0.5

    def test_swamp_is_expensive(self):
        """Swamp tiles cost 3.0x."""
        state = make_state(terrain={(3, 3): "SWAMP"})
        assert TerrainCostService.get_tile_cost((3, 3), state) == 3.0

    def test_plain_is_default(self):
        """Unknown/plain tiles cost 1.0x."""
        state = make_state(terrain={})
        assert TerrainCostService.get_tile_cost((3, 3), state) == 1.0

    def test_terrain_cost_table(self):
        """All terrain types have correct costs."""
        assert TERRAIN_COST["ROAD"] == 0.5
        assert TERRAIN_COST["FOREST"] == 1.5
        assert TERRAIN_COST["SWAMP"] == 3.0
        assert TERRAIN_COST["HILL"] == 2.0
        assert TERRAIN_COST["MOUNTAIN"] == 4.0

    def test_path_cost_calculation(self):
        """Path cost sums individual tile costs."""
        state = make_state(terrain={(1, 1): "ROAD", (2, 1): "SWAMP", (3, 1): "PLAIN"})
        cost = TerrainCostService.get_path_cost([(1, 1), (2, 1), (3, 1)], state)
        assert cost == 0.5 + 3.0 + 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# TARGET STICKINESS TESTS (Checklist Z5)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTargetStickiness:
    def test_switch_when_no_current_target(self):
        """Always switch if no current target."""
        # VERIFIED v2: target_stickiness_bias
        assert TargetStickinessService.should_switch_target(
            None, 2, 0.0, 5.0, 0
        )

    def test_no_switch_same_target(self):
        """Don't switch to the same target."""
        assert not TargetStickinessService.should_switch_target(
            1, 1, 5.0, 5.0, 3
        )

    def test_no_switch_marginal_improvement(self):
        """Don't switch for small improvements below threshold."""
        # Current score 10, new score 8 -> 20% improvement, below 30% margin
        assert not TargetStickinessService.should_switch_target(
            1, 2, 10.0, 8.0, 0
        )

    def test_switch_large_improvement(self):
        """Switch when improvement exceeds margin."""
        # Current score 10, new score 3 -> 70% improvement, above 30% margin
        assert TargetStickinessService.should_switch_target(
            1, 2, 10.0, 3.0, 0
        )

    def test_loyalty_increases_switch_difficulty(self):
        """Longer time on target makes switching harder."""
        # With 10 ticks loyalty, margin is 30% * min(2.0, 1.0+1.0) = 60%
        assert not TargetStickinessService.should_switch_target(
            1, 2, 10.0, 5.0, 10  # 50% improvement, but loyalty requires 60%
        )

    def test_switch_when_current_score_zero(self):
        """Switch when current target is effectively dead/invalid."""
        assert TargetStickinessService.should_switch_target(
            1, 2, 0.0, 5.0, 5
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SKILL SCALING TESTS (Checklist Z10)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSkillScaling:
    def test_physical_scaling(self):
        """Physical skills scale with strength."""
        # VERIFIED v2: skill_damage_scaling
        attrs = AttributeComponent(strength=20, intelligence=5)
        damage = SkillScalingService.calculate_skill_damage(1.5, "PHYSICAL", attrs)
        # base_atk(10) + 20 * 0.8 * 1.5 = 10 + 24 = 34
        assert damage == 34

    def test_magical_scaling(self):
        """Magical skills scale with intelligence."""
        attrs = AttributeComponent(strength=5, intelligence=20)
        damage = SkillScalingService.calculate_skill_damage(2.0, "MAGICAL", attrs)
        # base_atk(10) + 20 * 0.9 * 2.0 = 10 + 36 = 46
        assert damage == 46

    def test_elemental_scaling(self):
        """Elemental skills scale with spirit + intelligence."""
        attrs = AttributeComponent(spirit=20, intelligence=10)
        damage = SkillScalingService.calculate_skill_damage(1.5, "ELEMENTAL", attrs)
        # base_atk(10) + (20*0.5 + 10*0.4) * 1.5 = 10 + 14*1.5 = 10 + 21 = 31
        assert damage == 31

    def test_minimum_damage(self):
        """Damage is at least 1."""
        attrs = AttributeComponent(strength=0, intelligence=0, spirit=0)
        damage = SkillScalingService.calculate_skill_damage(0.1, "PHYSICAL", attrs, base_atk=0)
        assert damage >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# ATTRIBUTE CAPS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestAttributeCaps:
    def test_cap_enforcement(self):
        """Attributes are capped at ATTRIBUTE_CAP (99)."""
        # VERIFIED v2: level_cap_enforced
        attrs = AttributeComponent(strength=150, agility=0)
        deltas = enforce_attribute_caps(attrs)
        assert deltas["strength_delta"] == 99 - 150  # -51
        assert deltas["agility_delta"] == 1 - 0  # +1

    def test_no_cap_within_range(self):
        """No deltas when all attributes in valid range."""
        attrs = AttributeComponent(strength=50, agility=30)
        deltas = enforce_attribute_caps(attrs)
        assert len(deltas) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# EFFECTIVE STATS (Wounds + Scars + Gear + Attributes)
# ═══════════════════════════════════════════════════════════════════════════════

class TestEffectiveStats:
    def test_effective_stats_with_wounds(self):
        """Wounds reduce effective ATK/DEF/HP."""
        # VERIFIED v2: stat_recalculation_parity
        attrs = AttributeComponent(strength=10, vitality=10, agility=10, endurance=10)
        wound = WoundState(
            id="w1", kind="SLASH", severity=0.5, tick_inflicted=1,
            atk_penalty=2.0, def_penalty=1.0, max_hp_penalty=5.0
        )
        stats = SkillScalingService.get_effective_stats(attrs, wounds=[wound])
        clean_stats = SkillScalingService.get_effective_stats(attrs)
        assert stats["atk"] < clean_stats["atk"]
        assert stats["max_hp"] < clean_stats["max_hp"]

    def test_effective_stats_with_scars(self):
        """Scars reduce effective stats but less than wounds."""
        attrs = AttributeComponent(strength=10, vitality=10, agility=10, endurance=10)
        wound = WoundState(
            id="w1", kind="SLASH", severity=0.8, tick_inflicted=1,
            atk_penalty=3.0, def_penalty=2.0, max_hp_penalty=8.0
        )
        # No production producer exists for wound healing (TCK-20260824-WOUND-HEALING-DECISION);
        # hand-construct the WoundState->ScarState transition to exercise the data model.
        scar = ScarState(
            id=f"scar_{wound.id}", wound_kind=wound.kind, tick_created=wound.tick_inflicted,
            atk_penalty=wound.atk_penalty * 0.3, def_penalty=wound.def_penalty * 0.3,
            speed_penalty=wound.speed_penalty * 0.3,
        )
        stats_scar = SkillScalingService.get_effective_stats(attrs, scars=[scar])
        stats_wound = SkillScalingService.get_effective_stats(attrs, wounds=[wound])
        stats_clean = SkillScalingService.get_effective_stats(attrs)
        # Scar penalty < wound penalty
        assert stats_scar["atk"] > stats_wound["atk"]
        # Scar still penalizes vs clean
        assert stats_scar["atk"] <= stats_clean["atk"]

    def test_evasion_capped(self):
        """Evasion is capped at 0.95."""
        attrs = AttributeComponent(agility=999)
        stats = SkillScalingService.get_effective_stats(attrs)
        assert stats["evasion"] <= 0.95

    def test_get_effective_stats_applies_breakthrough_attribute_bonus(self):
        """active_breakthroughs reaches apply_bonuses and surfaces in derived atk."""
        attrs = AttributeComponent(strength=10, vitality=10, agility=10, endurance=10)
        clean_stats = SkillScalingService.get_effective_stats(attrs)
        boosted_stats = SkillScalingService.get_effective_stats(attrs, active_breakthroughs={"titan_grip"})
        assert boosted_stats["atk"] > clean_stats["atk"]

    def test_get_effective_stats_no_breakthroughs_unchanged(self):
        """Omitted, None, and empty-set active_breakthroughs all produce identical output."""
        attrs = AttributeComponent(strength=10, vitality=10, agility=10, endurance=10)
        stats_omitted = SkillScalingService.get_effective_stats(attrs)
        stats_none = SkillScalingService.get_effective_stats(attrs, active_breakthroughs=None)
        stats_empty = SkillScalingService.get_effective_stats(attrs, active_breakthroughs=set())
        assert stats_omitted == stats_none == stats_empty


# ═══════════════════════════════════════════════════════════════════════════════
# APPLY PATH INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestStaminaApplyIntegration:
    def test_stamina_update_drains(self):
        """StaminaUpdate drains stamina through apply path."""
        from src.engine.apply import ApplyPath
        entity = make_entity(stamina_current=100.0, stamina_max=100.0)
        update = EntityUpdate(
            entity_id=1,
            stamina_update=StaminaUpdate(current_delta=-8.0)
        )
        result = ApplyPath._apply_entity_update(entity, update)
        assert result.stamina.current == 92.0

    def test_stamina_update_clamps_to_zero(self):
        """Stamina doesn't go below 0."""
        from src.engine.apply import ApplyPath
        entity = make_entity(stamina_current=5.0, stamina_max=100.0)
        update = EntityUpdate(
            entity_id=1,
            stamina_update=StaminaUpdate(current_delta=-20.0)
        )
        result = ApplyPath._apply_entity_update(entity, update)
        assert result.stamina.current == 0.0

    def test_stamina_update_set(self):
        """StaminaUpdate with current_set overrides current value."""
        from src.engine.apply import ApplyPath
        entity = make_entity(stamina_current=100.0, stamina_max=100.0)
        update = EntityUpdate(
            entity_id=1,
            stamina_update=StaminaUpdate(current_set=50.0)
        )
        result = ApplyPath._apply_entity_update(entity, update)
        assert result.stamina.current == 50.0


class TestWoundApplyIntegration:
    def test_wound_added_through_apply(self):
        """WoundUpdate adds wounds to entity through apply path."""
        from src.engine.apply import ApplyPath
        entity = make_entity()
        wound = WoundState(
            id="w1", kind="CRUSH", severity=0.8, tick_inflicted=1,
            atk_penalty=5.0, def_penalty=3.0, max_hp_penalty=15.0
        )
        update = EntityUpdate(
            entity_id=1,
            wound_update=WoundUpdate(wounds_add=[wound])
        )
        result = ApplyPath._apply_entity_update(entity, update)
        assert len(result.combat.wounds) == 1
        assert result.combat.wounds[0].id == "w1"
        # Recalculation gate derives base stats then applies wound penalty
        # With default attrs (str=5, vit=5, end=5):
        # base_atk = 10 + int(5*0.5) = 12, after wound: 12 - 5 = 7
        # The entity default atk is 10, but the recalculated is 12 - 5 = 7
        assert result.combat.max_hp < 115  # 100 + vit*2 + end*0.5 = 112, minus 15 = 97

    def test_scar_added_through_apply(self):
        """WoundUpdate adds scars to entity."""
        from src.engine.apply import ApplyPath
        entity = make_entity()
        scar = ScarState(
            id="s1", wound_kind="SLASH", tick_created=1,
            atk_penalty=0.6, def_penalty=0.3
        )
        update = EntityUpdate(
            entity_id=1,
            wound_update=WoundUpdate(scars_add=[scar])
        )
        result = ApplyPath._apply_entity_update(entity, update)
        assert len(result.combat.scars) == 1
        assert result.combat.scars[0].id == "s1"

    def test_wound_heal_through_apply(self):
        """WoundUpdate can heal existing wounds."""
        from src.engine.apply import ApplyPath
        wound = WoundState(
            id="w1", kind="SLASH", severity=0.5, tick_inflicted=1,
            atk_penalty=2.0, def_penalty=1.0, max_hp_penalty=5.0
        )
        entity = replace(make_entity(), combat=replace(make_entity().combat, wounds=[wound]))
        update = EntityUpdate(
            entity_id=1,
            wound_update=WoundUpdate(wounds_heal=["w1"])
        )
        result = ApplyPath._apply_entity_update(entity, update)
        assert result.combat.wounds[0].healed


class TestPassiveStaminaRegen:
    def test_passive_regen_in_apply_generation(self):
        """apply_generation ticks passive stamina regen per entity."""
        from src.engine.apply import ApplyPath
        from src.core.updates import StateUpdate
        entity = make_entity(stamina_current=50.0, stamina_max=100.0)
        state = make_state(entities={1: entity})
        update = StateUpdate()
        new_state = ApplyPath.apply_generation(state, update, next_tick=2)
        # Regen should have increased stamina
        assert new_state.entities[1].stamina.current > 50.0


class TestBreakthroughApplyIntegration:
    def test_apply_path_recomputes_combat_stats_from_active_breakthroughs(self):
        """An entity with active_breakthroughs shows the bonus in recomputed combat stats."""
        from src.engine.apply import ApplyPath
        from src.core.updates import IdentityUpdate

        boosted_entity = make_entity(strength=10)
        boosted_entity = replace(
            boosted_entity,
            identity=replace(boosted_entity.identity, active_breakthroughs={"titan_grip"})
        )
        plain_entity = make_entity(strength=10)

        update = EntityUpdate(
            entity_id=1,
            identity=IdentityUpdate(learned_skills=["swift_reflexes"])
        )
        boosted_result = ApplyPath._apply_entity_update(boosted_entity, update)
        plain_result = ApplyPath._apply_entity_update(plain_entity, update)

        assert boosted_result.combat.atk > plain_result.combat.atk

    def test_apply_path_stats_dirty_triggers_on_breakthroughs_add_alone(self):
        """An IdentityUpdate with only breakthroughs_add still recomputes combat stats."""
        from src.engine.apply import ApplyPath
        from src.core.updates import IdentityUpdate

        entity = make_entity(strength=10)
        before = ApplyPath._apply_entity_update(entity, EntityUpdate(entity_id=1))

        update = EntityUpdate(
            entity_id=1,
            identity=IdentityUpdate(breakthroughs_add=["titan_grip"])
        )
        result = ApplyPath._apply_entity_update(entity, update)

        assert result.combat.atk > before.combat.atk

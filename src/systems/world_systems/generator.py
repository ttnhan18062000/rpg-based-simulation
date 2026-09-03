# Compliance IDs: COMB-166, PROG-057, PROG-086, STRAT-145, STRAT-146, STRAT-147, SUB-001, TOWN-077, WORLD-005, WORLD-009, WORLD-010, WORLD-011, WORLD-012, WORLD-013, WORLD-014, WORLD-015, WORLD-016, WORLD-017, WORLD-018, WORLD-019, WORLD-044, WORLD-045, WORLD-046, WORLD-047, WORLD-050, WORLD-051
# Compliance IDs: PROG-057, STRAT-145, STRAT-146, STRAT-147, TOWN-077, WORLD-009, WORLD-010, WORLD-011, WORLD-012, WORLD-013, WORLD-014, WORLD-015, WORLD-016, WORLD-017, WORLD-018, WORLD-019, WORLD-051
from __future__ import annotations

from typing import Dict, List, Optional, TYPE_CHECKING, Any

from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, 
    AttributeComponent, CombatComponent, BiologicalComponent,
    LifecycleComponent, StrategicComponent, NavigationComponent,
    InteractionComponent, SocialComponent, TaskComponent,
    EquipmentComponent, AptitudeComponent, ItemStack, InventoryComponent
)
from src.core.enums import EntityRole, Faction, ActionType, Domain
from src.platform.rng import DeterministicRNG

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.systems.lifecycle_systems.genetics import GeneticProfile

class EntityGenerator:
    """
    Authoritative factory for creating new entity generations.
    Logic ID: WORLD-005 (Spawn rules are deterministic / seeded generator)
    """
    
    def __init__(self, seed: int):
        self.rng = DeterministicRNG(seed)
        self._last_id = 0
        
    def get_next_id(self) -> int:
        self._last_id += 1
        return self._last_id

    def spawn_hero(self, pos: tuple[float, float], state: AuthoritativeState | None = None, name: str = "Hero", difficulty_tier: int = 1) -> EntityState:
        """Spawn a new hero with role-specific base stats and difficulty-scaled starting power."""
        entity_id = self.get_next_id()
        
        from src.world.spawn_config import DIFFICULTY_TIERS
        mults = DIFFICULTY_TIERS.get(difficulty_tier, DIFFICULTY_TIERS[1])
        
        # Base stats (Legacy parity for testing)
        base_hp = 100 * mults.hp
        base_atk = 15 * mults.atk
        base_def = 5 * mults.def_stat
        base_gold = 50 * mults.gold
        
        tick = state.tick if state else 0
        evolution_level = self.rng.get_int(Domain.SPAWN, tick, entity_id, mults.level_min, mults.level_max)
        
        from src.core.builder import V2EntityBuilder
        return (V2EntityBuilder(entity_id)
            .kind("hero")
            .location(*pos)
            .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD, evolution_level=evolution_level)
            .combat(hp=int(base_hp), max_hp=int(base_hp), atk=int(base_atk), def_stat=int(base_def), readiness=100.0)
            .inventory(gold=int(base_gold))
            .build())

    def spawn_monster(self, pos: tuple[float, float], state: AuthoritativeState | None = None, kind: str = "monster", difficulty_tier: int = 1) -> EntityState:
        """Spawn a regular monster with difficulty-scaled stats."""
        entity_id = self.get_next_id()
        
        from src.world.spawn_config import DIFFICULTY_TIERS
        mults = DIFFICULTY_TIERS.get(difficulty_tier, DIFFICULTY_TIERS[1])
        
        tick = state.tick if state else 0
        evolution_level = self.rng.get_int(Domain.SPAWN, tick, entity_id, mults.level_min, mults.level_max)
        
        # Generic monster base (fallback)
        base_hp = 50 * mults.hp
        base_atk = 10 * mults.atk
        base_def = 5 * mults.def_stat
        base_gold = 10 * mults.gold
        
        from src.core.builder import V2EntityBuilder
        return (V2EntityBuilder(entity_id)
            .kind(kind)
            .location(*pos)
            .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, evolution_level=evolution_level)
            .navigation(home_position=pos, leash_radius=10.0)
            .combat(hp=int(base_hp), max_hp=int(base_hp), atk=int(base_atk), def_stat=int(base_def), readiness=100.0)
            .inventory(gold=int(base_gold))
            .build())

    def spawn_natural_creature_offspring(
        self, pos: tuple[float, float], state: AuthoritativeState | None = None,
        kind: str = "monster", difficulty_tier: int = 1, birth_tick: int = 0,
    ) -> EntityState:
        """Spawn a parentless same-kind offspring already aged near the CHILD->ADULT
        boundary with birth-record fields populated via the parentless
        V2EntityBuilder.birth_record() path (both parent ids None)."""
        entity_id = self.get_next_id()

        from src.world.spawn_config import DIFFICULTY_TIERS
        mults = DIFFICULTY_TIERS.get(difficulty_tier, DIFFICULTY_TIERS[1])

        tick = state.tick if state else 0
        evolution_level = self.rng.get_int(Domain.SPAWN, tick, entity_id, mults.level_min, mults.level_max)

        base_hp = 50 * mults.hp
        base_atk = 10 * mults.atk
        base_def = 5 * mults.def_stat
        base_gold = 10 * mults.gold

        from src.core.builder import V2EntityBuilder
        from src.core.state import LifeStage
        from src.world.camp import CampService
        short_clock_age = 3000 - CampService.CAMP_SPAWN_INTERVAL

        return (V2EntityBuilder(entity_id)
            .kind(kind)
            .location(*pos)
            .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE,
                      evolution_level=evolution_level, life_stage=LifeStage.CHILD)
            .navigation(home_position=pos, leash_radius=10.0)
            .combat(hp=int(base_hp), max_hp=int(base_hp), atk=int(base_atk), def_stat=int(base_def), readiness=100.0)
            .inventory(gold=int(base_gold))
            .lifecycle(age_ticks=short_clock_age)
            .birth_record(parent_a_entity_id=None, parent_b_entity_id=None, birth_tick=birth_tick, birth_city_id=None)
            .build())

    def spawn_magical_demonic_entity(
        self, pos: tuple[float, float], state: AuthoritativeState | None = None,
        kind: str = "magical_demonic_entity", difficulty_tier: int = 4, birth_tick: int = 0,
    ) -> EntityState:
        """Spawn a parentless magical/demonic entity directly at ADULT life stage (no
        CHILD->ADULT maturation clock), with birth-record fields populated via the
        parentless V2EntityBuilder.birth_record() path (both parent ids None)."""
        entity_id = self.get_next_id()

        from src.world.spawn_config import DIFFICULTY_TIERS
        mults = DIFFICULTY_TIERS.get(difficulty_tier, DIFFICULTY_TIERS[1])

        tick = state.tick if state else 0
        evolution_level = self.rng.get_int(Domain.SPAWN, tick, entity_id, mults.level_min, mults.level_max)

        base_hp = 50 * mults.hp
        base_atk = 10 * mults.atk
        base_def = 5 * mults.def_stat
        base_gold = 10 * mults.gold

        from src.core.builder import V2EntityBuilder
        return (V2EntityBuilder(entity_id)
            .kind(kind)
            .location(*pos)
            .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE,
                      evolution_level=evolution_level)
            .navigation(home_position=pos, leash_radius=10.0)
            .combat(hp=int(base_hp), max_hp=int(base_hp), atk=int(base_atk), def_stat=int(base_def), readiness=100.0)
            .inventory(gold=int(base_gold))
            .birth_record(parent_a_entity_id=None, parent_b_entity_id=None, birth_tick=birth_tick, birth_city_id=None)
            .build())

    def spawn_humanoid_offspring(
        self, pos: tuple[float, float], state: AuthoritativeState, kind: str,
        parent_a_id: int, parent_b_id: int, birth_tick: int, birth_city_id: Optional[int],
        parent_a_genetic_profile: Optional[GeneticProfile], parent_b_genetic_profile: Optional[GeneticProfile],
        parent_a_role: int, parent_b_role: int, difficulty_tier: int = 1,
    ) -> EntityState:
        """Spawn a real newborn humanoid offspring with tracked parent ids, an inherited
        GeneticProfile, and CHILD life stage at age_ticks=0 -- unlike
        spawn_natural_creature_offspring()'s fast-forwarded maturation clock, this path has no
        analogous "must appear battle-ready soon" requirement."""
        entity_id = self.get_next_id()

        from src.world.spawn_config import DIFFICULTY_TIERS
        mults = DIFFICULTY_TIERS.get(difficulty_tier, DIFFICULTY_TIERS[1])

        tick = state.tick if state else 0
        evolution_level = self.rng.get_int(Domain.SPAWN, tick, entity_id, mults.level_min, mults.level_max)

        base_hp = 50 * mults.hp
        base_atk = 10 * mults.atk
        base_def = 5 * mults.def_stat
        base_gold = 10 * mults.gold

        from src.core.builder import V2EntityBuilder
        from src.core.state import LifeStage

        return (V2EntityBuilder(entity_id)
            .kind(kind)
            .location(*pos)
            .identity(role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL,
                      evolution_level=evolution_level, life_stage=LifeStage.CHILD)
            .combat(hp=int(base_hp), max_hp=int(base_hp), atk=int(base_atk), def_stat=int(base_def), readiness=100.0)
            .inventory(gold=int(base_gold))
            .birth_record(
                parent_a_entity_id=parent_a_id, parent_b_entity_id=parent_b_id,
                birth_tick=birth_tick, birth_city_id=birth_city_id,
                parent_a_genetic_profile=parent_a_genetic_profile,
                parent_b_genetic_profile=parent_b_genetic_profile,
                parent_a_role=parent_a_role, parent_b_role=parent_b_role,
            )
            .build())

    def spawn_goblin(self, pos: tuple[float, float], state: AuthoritativeState | None = None, difficulty_tier: int = 1) -> EntityState:
        """Specialized goblin spawn with specific base stats for scaling tests."""
        entity_id = self.get_next_id()
        
        from src.world.spawn_config import DIFFICULTY_TIERS
        mults = DIFFICULTY_TIERS.get(difficulty_tier, DIFFICULTY_TIERS[1])
        
        tick = state.tick if state else 0
        evolution_level = self.rng.get_int(Domain.SPAWN, tick, entity_id, mults.level_min, mults.level_max)
        
        # Goblin base: 30 HP, 8 ATK, 2 DEF, 5 Gold
        base_hp = 30 * mults.hp
        base_atk = 8 * mults.atk
        base_def = 2 * mults.def_stat
        base_gold = 5 * mults.gold
        
        from src.core.builder import V2EntityBuilder
        return (V2EntityBuilder(entity_id)
            .kind("goblin")
            .location(*pos)
            .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, evolution_level=evolution_level)
            .navigation(home_position=pos, leash_radius=8.0)
            .combat(hp=int(base_hp), max_hp=int(base_hp), atk=int(base_atk), def_stat=int(base_def), readiness=100.0)
            .inventory(gold=int(base_gold))
            .build())

    def spawn_calamity(self, state: AuthoritativeState, kind: str, pos: tuple[float, float]) -> EntityState:
        """Spawn a massive World Boss (Calamity) with elite scaling."""
        entity_id = self.get_next_id()
        
        # Calamities are Tier 5 (implicit)
        hp = 5000 * (1.0 + state.maturity * 0.5)
        atk = 150 * (1.0 + state.maturity * 0.2)
        def_val = 100 * (1.0 + state.maturity * 0.2)
        
        from src.core.builder import V2EntityBuilder
        return (V2EntityBuilder(entity_id)
            .kind(kind)
            .location(*pos)
            .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, evolution_level=50 + state.maturity * 5)
            .combat(hp=int(hp), max_hp=int(hp), atk=int(atk), def_stat=int(def_val), readiness=100.0)
            .build())

    def spawn_stronghold(self, state: AuthoritativeState, pos: tuple[float, float]) -> EntityState:
        """Spawn a static stronghold building-entity."""
        entity_id = self.get_next_id()
        
        # Strongholds are very tough buildings
        hp = 10000 * (1.0 + state.maturity * 0.5)
        def_val = 50 * (1.0 + state.maturity * 0.2)
        
        from src.core.builder import V2EntityBuilder
        return (V2EntityBuilder(entity_id)
            .kind("stronghold")
            .location(*pos)
            .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, evolution_level=1)
            .combat(hp=int(hp), max_hp=int(hp), atk=0, def_stat=int(def_val), readiness=100.0)
            .build())

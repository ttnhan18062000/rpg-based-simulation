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

class EntityGenerator:
    """
    Authoritative factory for creating new entity generations.
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

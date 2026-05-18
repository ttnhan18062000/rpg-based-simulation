from __future__ import annotations
from dataclasses import replace
from typing import Any, Dict, List, Optional, Set

from src_legacy.core.state import (
    EntityState,
    IdentityComponent,
    CombatComponent,
    InventoryComponent,
    LifecycleComponent,
    BiologicalComponent,
    SocialComponent,
    NavigationComponent,
    InteractionComponent,
    TaskComponent,
    AptitudeComponent,
    AptitudeComponent,
    AttributeComponent,
    EquipmentComponent,
    EquipSlot,
    ItemStack
)
from src_legacy.core.strategic import StrategicComponent
from src_legacy.core.models.enums import EntityRole, Faction
from src_legacy.core.classes import CLASS_REGISTRY

class V2EntityBuilder:
    """
    Fluent builder for V2 EntityState construction.
    Maintains API parity with legacy EntityBuilder while producing frozen EntityState.
    """

    def __init__(self, entity_id: int, tick: int = 0) -> None:
        self._eid = entity_id
        self._tick = tick
        
        # Identity
        self._kind = "unknown"
        self._role = EntityRole.MONSTER
        self._faction = Faction.MONSTER_HORDE
        self._evolution_level = 1
        self._class_id = "NOVICE"
        self._learned_skills: Set[str] = set()
        self._starting_gear: Dict[str, str] = {}
        
        # Spatial
        self._pos = (0.0, 0.0)
        self._readiness = 0.0
        
        # Combat
        self._hp_base = 100
        self._atk_base = 10
        self._def_base = 5
        self._range = 1
        self._evasion = 0.05
        self._tactical_role = "VANGUARD"
        self._action_style = 0 # ActionStyle.BALANCED
        
        # Inventory
        self._max_slots = 16
        self._max_weight = 50
        self._gold = 0
        self._items: List[str] = []
        
        # Lifecycle / Biological
        self._age_ticks = 0
        self._is_permadeath = False
        
        # Attributes (Default 5 as per legacy)
        self._str = 5
        self._agi = 5
        self._vit = 5
        self._end = 5
        
        # Aptitudes
        self._str_apt = 1.0
        self._int_apt = 1.0
        self._agi_apt = 1.0
        self._vit_apt = 1.0
        self._end_apt = 1.0
        self._int = 5
        self._spi = 5
        self._wis = 5
        self._end = 5
        self._per = 5
        self._cha = 5
        
        # Components
        self._properties: Dict[str, Any] = {}

    def kind(self, k: str) -> V2EntityBuilder:
        self._kind = k
        return self

    def role(self, r: int | EntityRole) -> V2EntityBuilder:
        # Map legacy int roles to V2 Enums if possible
        if isinstance(r, int):
            try:
                self._role = EntityRole(r)
            except ValueError:
                # Fallback or keep as int if Enums differ
                self._role = r
        else:
            self._role = r
        return self

    def faction(self, f: int | Faction) -> V2EntityBuilder:
        if isinstance(f, int):
            try:
                self._faction = Faction(f)
            except ValueError:
                self._faction = f
        else:
            self._faction = f
        return self

    def at(self, pos: tuple[float, float] | list[float]) -> V2EntityBuilder:
        self._pos = tuple(pos)
        return self

    def readiness(self, val: float) -> V2EntityBuilder:
        self._readiness = val
        return self

    def with_class(self, class_id: str) -> V2EntityBuilder:
        if class_id in CLASS_REGISTRY:
            self._class_id = class_id
            defn = CLASS_REGISTRY[class_id]
            self._hp_base = defn.base_hp
            self._atk_base = defn.base_atk
            self._def_base = defn.base_def
            self._learned_skills = set(defn.starting_skills)
            self._starting_gear = dict(defn.starting_gear)
        return self

    def with_base_stats(self, hp: int = 100, atk: int = 10, def_stat: int = 5, 
                        range: int = 1, evasion: float = 0.05, 
                        tactical_role: str = "VANGUARD",
                        action_style: int = 0) -> V2EntityBuilder:
        self._hp_base = hp
        self._atk_base = atk
        self._def_base = def_stat
        self._range = range
        self._evasion = evasion
        self._tactical_role = tactical_role
        self._action_style = action_style
        return self

    def monster(self, race: str, tier: int = 0) -> V2EntityBuilder:
        """Helper for standard monster construction."""
        self._kind = f"{race}_{tier}" # e.g. goblin_0
        self._role = EntityRole.MONSTER
        self._faction = Faction.MONSTER_HORDE
        
        # Simple tier-based scaling
        self._hp_base = 50 + (tier * 50)
        self._atk_base = 5 + (tier * 5)
        self._def_base = 2 + (tier * 3)
        
        # Loadout mapping (Placeholder)
        if race == "goblin":
            if tier == 0:
                self._starting_gear = {"MAIN_HAND": "wooden_club"}
            elif tier == 1:
                self._starting_gear = {"MAIN_HAND": "iron_sword", "TORSO": "leather_armor"}
        
        return self

    def with_attributes(self, **kwargs) -> V2EntityBuilder:
        """Sets specific attribute values."""
        for k, v in kwargs.items():
            attr_name = f"_{k}"
            if hasattr(self, attr_name):
                setattr(self, attr_name, int(v))
        return self

    def with_aptitudes(self, **kwargs) -> V2EntityBuilder:
        """Sets specific aptitude values."""
        for k, v in kwargs.items():
            attr_name = f"_{k}_apt"
            if hasattr(self, attr_name):
                setattr(self, attr_name, float(v))
        return self

    def with_inventory(self, gold: int = 0, items: List[str] | None = None) -> V2EntityBuilder:
        self._gold = gold
        if items:
            self._items = list(items)
        return self

    def _recalc(self):
        """Mimics legacy recalc_derived_stats for initial build."""
        self._max_hp = self._hp_base + self._vit * 2 + int(self._end * 0.5)
        self._hp = self._max_hp # Built entities start at full health
        self._atk = self._atk_base + int(self._str * 0.5)
        self._def_stat = self._def_base + int(self._vit * 0.3)

    def build(self) -> EntityState:
        """Constructs the frozen EntityState."""
        self._recalc()
        return EntityState(
            id=self._eid,
            kind=self._kind,
            position=self._pos,
            readiness=self._readiness,
            identity=IdentityComponent(
                role=self._role,
                faction=self._faction,
                evolution_level=self._evolution_level,
                class_id=self._class_id,
                learned_skills=self._learned_skills,
                unspent_ap=0 # Starting entities have 0 unspent
            ),
            attributes=AttributeComponent(
                strength=self._str,
                agility=self._agi,
                vitality=self._vit,
                endurance=self._end,
                intelligence=self._int,
                spirit=self._spi,
                wisdom=self._wis,
                perception=self._per,
                charisma=self._cha
            ),
            combat=CombatComponent(
                hp=self._hp,
                max_hp=self._max_hp,
                atk=self._atk,
                def_stat=self._def_stat,
                range=self._range,
                evasion=self._evasion,
                tactical_role=self._tactical_role,
                action_style=self._action_style,
                alive=self._hp > 0
            ),
            inventory=InventoryComponent(
                max_slots=self._max_slots,
                max_weight=self._max_weight,
                gold=self._gold,
                items=[ItemStack(item_id=i, quantity=1) for i in self._items]
            ),
            lifecycle=LifecycleComponent(
                age_ticks=self._age_ticks,
                is_permadeath=self._is_permadeath
            ),
            equipment=EquipmentComponent(
                slots={EquipSlot(k): v for k, v in self._starting_gear.items()}
            ),
            aptitude=AptitudeComponent(
                learning_rate=self._int_apt,
                stamina_efficiency=self._vit_apt,
                str_apt=self._str_apt,
                vit_apt=self._vit_apt,
                end_apt=self._end_apt
            ),
            group_id=getattr(self, "_group_id", None),
            properties=self._properties
        )

    def group_id(self, g_id: Optional[int]) -> V2EntityBuilder:
        self._group_id = g_id
        return self

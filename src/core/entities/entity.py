"""Core data models: Vector2, Stats, Entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, ConfigDict, model_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass, rebuild_dataclass
from src.core.models.enums import AIState, DamageType, Element, EnemyTier, EntityRole, TraitType, HeroClass
from src.core.gameplay.faction import Faction

if TYPE_CHECKING:
    from src.core.gameplay.attributes import Attributes, AttributeCaps
    from src.core.gameplay.classes import SkillInstance
    from src.core.gameplay.effects import StatusEffect
    from src.core.gameplay.quests import Quest
    from src.api.schemas import EntitySlimSchema, EntitySchema, AttributeSchema, AttributeCapSchema, EffectSchema
    from src.core.models.base import Aspect
    from src.core.aspects.identity import IdentityAspect
    from src.core.aspects.spatial import SpatialAspect
    from src.core.aspects.combat import CombatAspect
    from src.core.aspects.inventory import InventoryAspect
    from src.core.aspects.progression import ProgressionAspect
    from src.core.aspects.mind import MindAspect


from src.core.entities.traits import TraitType
from src.core.models.vectors import Vector2, FloatVector2, DIRECTION_OFFSETS
from src.core.entities.stats import Stats
from src.core.entities.stats_proxy import StatsProxy

from src.core.models.world_objects import HomeStorage, TreasureChest, CorpseNode

class Entity(BaseModel):
    """A simulation entity — character, generator, or any world actor.
    
    Refactored to an Aspect-Oriented container.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    id: int
    kind: str
    next_act_at: int = 0
    
    # New Aspect Registry
    aspects: dict[str, Any] = Field(default_factory=dict)

    def __init__(self, id: Any = None, kind: Any = None, **data: Any) -> None:
        """Support positional arguments for backward compatibility.
        
        Usage:
            Entity(10, "hero", ...)
            Entity(id=10, kind="hero", ...)
        """
        # If the first arg is a dict, it's likely Pydantic's internal state
        if isinstance(id, dict) and not data:
            super().__init__(**id)
            return

        # Prepare final data dict for Pydantic
        final_data = dict(data)
        if id is not None:
            final_data["id"] = id
        if kind is not None:
            final_data["kind"] = kind
            
        # Coerce ID to int if it's a float
        if "id" in final_data and isinstance(final_data["id"], float):
            final_data["id"] = int(final_data["id"])
            
        super().__init__(**final_data)

    @model_validator(mode="before")
    @classmethod
    def _validate_before(cls, data: Any) -> Any:
        """Ensure core fields have correct types before Pydantic validation."""
        if isinstance(data, dict):
            if "id" in data and isinstance(data["id"], float):
                data["id"] = int(data["id"])
            if "next_act_at" in data and isinstance(data["next_act_at"], float):
                data["next_act_at"] = int(data["next_act_at"])
        return data

    def model_post_init(self, __context: Any) -> None:
        """Handle legacy constructor arguments and ensure aspects exist."""
        # Ensure all core aspects exist even if not provided
        if not self.aspects:
            from src.core.aspects.identity import IdentityAspect
            from src.core.aspects.spatial import SpatialAspect
            from src.core.aspects.combat import CombatAspect
            from src.core.aspects.inventory import InventoryAspect
            from src.core.aspects.progression import ProgressionAspect
            from src.core.aspects.mind import MindAspect
            self.aspects = {
                "identity": IdentityAspect(),
                "spatial": SpatialAspect(),
                "combat": CombatAspect(),
                "inventory": InventoryAspect(),
                "progression": ProgressionAspect(),
                "mind": MindAspect(),
            }
        
        # Ensure 'stats' proxy exists if needed and re-attach all aspects
        # Re-attach aspects to ensure parent pointers/references are correct
        for aspect in self.aspects.values():
            if hasattr(aspect, "on_attach"):
                aspect.on_attach(self)

        # Handle legacy constructor arguments
        extra_data = getattr(self, "__pydantic_extra__", {})
        if not extra_data:
            return

        # Simple auto-mapping to our property shims!
        for key, value in extra_data.items():
            # If we have a setter for this name (like pos.setter), then use it!
            # Since pydantic already put it in __pydantic_extra__, we just need to shift it
            if hasattr(self, key):
                try:
                    setattr(self, key, value)
                except AttributeError:
                    # Might be a read-only property or some other issue
                    pass

        # Re-export world objects for backward compatibility
        # These were extracted to world_objects.py to reduce models.py size.
        from src.core.models.world_objects import HomeStorage, TreasureChest, CorpseNode

    @property
    def identity(self) -> "IdentityAspect":
        return self.aspects["identity"]

    @property
    def faction(self) -> Any: return self.identity.faction
    @faction.setter
    def faction(self, val: Any): self.identity.faction = val

    @property
    def role(self) -> Any: return self.identity.role
    @role.setter
    def role(self, val: Any): self.identity.role = val

    @property
    def rarity(self) -> int: return self.identity.tier
    @rarity.setter
    def rarity(self, val: int): self.identity.tier = val

    @property
    def weakness(self) -> str: return self.identity.weakness
    @weakness.setter
    def weakness(self, val: str): self.identity.weakness = val

    @property
    def tier(self) -> int: return self.identity.tier
    @tier.setter
    def tier(self, val: int): self.identity.tier = val

    @property
    def hero_class(self) -> Any: return self.identity.hero_class
    @hero_class.setter
    def hero_class(self, val: Any): self.identity.hero_class = val

    @property
    def spatial(self) -> "SpatialAspect":
        return self.aspects["spatial"]

    @property
    def titles(self) -> list[str]: return self.identity.titles
    @titles.setter
    def titles(self, val: list[str]): self.identity.titles = val

    @property
    def combat(self) -> "CombatAspect":
        return self.aspects["combat"]

    @property
    def effects(self) -> list[Any]: return self.combat.effects
    @effects.setter
    def effects(self, val: list[Any]): self.combat.effects = val

    @property
    def mind(self) -> "MindAspect":
        return self.aspects["mind"]

    @property
    def consecutive_idle_ticks(self) -> int: return self.mind.consecutive_idle_ticks
    @consecutive_idle_ticks.setter
    def consecutive_idle_ticks(self, val: int): self.mind.consecutive_idle_ticks = val

    @property
    def boredom_multipliers(self) -> dict[str, float]: return self.mind.boredom_multipliers
    @boredom_multipliers.setter
    def boredom_multipliers(self, val: dict[str, float]): self.mind.boredom_multipliers = val

    @property
    def progression(self) -> "ProgressionAspect":
        return self.aspects["progression"]

    @property
    def level(self) -> int: return self.progression.level
    @level.setter
    def level(self, val: int): self.progression.level = val

    @property
    def veterancy_points(self) -> int: return self.progression.veterancy_points
    @veterancy_points.setter
    def veterancy_points(self, val: int): self.progression.veterancy_points = val

    @property
    def veterancy_rank(self) -> int: return self.progression.veterancy_rank
    @veterancy_rank.setter
    def veterancy_rank(self, val: int): self.progression.veterancy_rank = val

    @property
    def talents(self) -> list[str]: return self.progression.talents
    @talents.setter
    def talents(self, val: list[str]): self.progression.talents = val

    @property
    def quests(self) -> list[Any]: return self.progression.quests
    @quests.setter
    def quests(self, val: list[Any]): self.progression.quests = val

    @property
    def attributes(self) -> Any: return self.progression.attributes
    @attributes.setter
    def attributes(self, val: Any): self.progression.attributes = val

    @property
    def attribute_caps(self) -> Any: return self.progression.attribute_caps
    @attribute_caps.setter
    def attribute_caps(self, val: Any): self.progression.attribute_caps = val

    @property
    def skills(self) -> list[Any]: return self.progression.skills
    @skills.setter
    def skills(self, val: list[Any]): self.progression.skills = val

    @property
    def inventory(self) -> "InventoryAspect | None":
        return self.aspects.get("inventory")

    @inventory.setter
    def inventory(self, val: "InventoryAspect"):
        self.aspects["inventory"] = val

    # --- Spatial Shims ---
    @property
    def pos(self) -> Vector2: return self.spatial.pos
    @pos.setter
    def pos(self, val: Vector2): self.spatial.pos = val

    @property
    def region_id(self) -> str: return self.spatial.region_id
    @region_id.setter
    def region_id(self, val: str): self.spatial.region_id = val

    @property
    def current_region_id(self) -> str: return self.spatial.current_region_id
    @current_region_id.setter
    def current_region_id(self, val: str): self.spatial.current_region_id = val

    @property
    def home_pos(self) -> Vector2 | None: return self.spatial.home_pos
    @home_pos.setter
    def home_pos(self, val: Vector2 | None): self.spatial.home_pos = val

    @property
    def leash_radius(self) -> int: return self.spatial.leash_radius
    @leash_radius.setter
    def leash_radius(self, val: int): self.spatial.leash_radius = val

    @property
    def difficulty_tier(self) -> int: return self.spatial.difficulty_tier
    @difficulty_tier.setter
    def difficulty_tier(self, val: int): self.spatial.difficulty_tier = val

    # --- Derived Counters Shims ---
    
    @property
    def chase_ticks(self) -> int: return self.mind.chase_ticks
    @chase_ticks.setter
    def chase_ticks(self, val: int): self.mind.chase_ticks = val

    @property
    def consecutive_idle_ticks(self) -> int: return self.mind.consecutive_idle_ticks
    @consecutive_idle_ticks.setter
    def consecutive_idle_ticks(self, val: int): self.mind.consecutive_idle_ticks = val

    @property
    def engaged_ticks(self) -> int: return self.mind.engaged_ticks
    @engaged_ticks.setter
    def engaged_ticks(self, val: int): self.mind.engaged_ticks = val

    @property
    def combat_target_id(self) -> int | None: return self.combat.combat_target_id
    @combat_target_id.setter
    def combat_target_id(self, val: int | None): self.combat.combat_target_id = val

    @property
    def loot_progress(self) -> int: return self.combat.loot_progress
    @loot_progress.setter
    def loot_progress(self, val: int): self.combat.loot_progress = val

    @property
    def quests(self) -> list["Quest"]: return self.progression.quests
    @quests.setter
    def quests(self, val: list["Quest"]): self.progression.quests = val

    @property
    def terrain_memory(self) -> dict: return self.mind.terrain_memory
    @terrain_memory.setter
    def terrain_memory(self, val: dict): self.mind.terrain_memory = val

    @property
    def last_reason(self) -> str: return self.mind.last_reason
    @last_reason.setter
    def last_reason(self, val: str): self.mind.last_reason = val

    @property
    def hero_familiarity(self) -> dict[int, float]: return self.mind.hero_familiarity
    @hero_familiarity.setter
    def hero_familiarity(self, val: dict[int, float]): self.mind.hero_familiarity = val

    @property
    def boredom_multipliers(self) -> dict[str, float]: return self.mind.boredom_multipliers
    @boredom_multipliers.setter
    def boredom_multipliers(self, val: dict[str, float]): self.mind.boredom_multipliers = val

    @property
    def known_recipes(self) -> list[str]: return self.identity.known_recipes
    @known_recipes.setter
    def known_recipes(self, val: list[str]): self.identity.known_recipes = val

    @property
    def craft_target(self) -> str | None: return self.identity.craft_target
    @craft_target.setter
    def craft_target(self, val: str | None): self.identity.craft_target = val

    @property
    def entity_memory(self) -> list[dict]: return self.mind.entity_memory
    @entity_memory.setter
    def entity_memory(self, val: list[dict]): self.mind.entity_memory = val

    @property
    def home_storage(self) -> Any:
        inv = self.inventory
        return inv.home_storage if inv else None
    @home_storage.setter
    def home_storage(self, val: Any):
        inv = self.inventory
        if inv: inv.home_storage = val

    @property
    def inventory_aspect(self) -> "InventoryAspect" | None:
        return self.aspects.get("inventory")

    @property
    def stats(self) -> "StatsProxy":
        from .stats_proxy import StatsProxy
        return StatsProxy(self)

    @stats.setter
    def stats(self, value: Any):
        """Legacy setter for Stats object from builders."""
        from src.core.entities.stats import Stats
        if not isinstance(value, Stats):
            return
            
        # Combat Aspect
        c = self.combat
        c.hp = value.hp
        c.max_hp = value.max_hp
        c.atk = value.atk
        c.def_ = value.def_
        c.spd = value.spd
        c.luck = value.luck
        c.crit_rate = value.crit_rate
        c.crit_dmg = value.crit_dmg
        c.evasion = value.evasion
        c.matk = value.matk
        c.mdef = value.mdef
        if value.elem_vuln:
            c.elem_vuln = dict(value.elem_vuln)
        c.vision_range = value.vision_range
        c.loot_bonus = value.loot_bonus
        c.trade_bonus = value.trade_bonus
        c.interaction_speed = value.interaction_speed
        c.rest_efficiency = value.rest_efficiency
        c.hp_regen = value.hp_regen
        c.cooldown_reduction = value.cooldown_reduction
        
        # Progression Aspect
        p = self.progression
        p.level = value.level
        p.xp = value.xp
        p.xp_to_next = value.xp_to_next
        p.gold = value.gold
        p.fame = value.fame
        p.stamina = value.stamina
        p.max_stamina = value.max_stamina

    # --- Lifecycle ---
    
    def on_tick(self, tick: int) -> None:
        """Propagate tick to all aspects."""
        for aspect in self.aspects.values():
            aspect.on_tick(tick)


    def has_trait(self, trait: int) -> bool:
        """Check if entity has a specific TraitType."""
        return trait in self.identity.traits

    # --- Serialization (epic-05 api standardization) ---

    def _get_weapon_range(self) -> int:
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        inventory = self.aspects.get("inventory")
        if inventory and inventory.weapon:
            tmpl = ITEM_REGISTRY.get(inventory.weapon)
            if tmpl:
                return tmpl.weapon_range
        return 1

    def to_slim_schema(self, loot_duration: int = 3) -> "EntitySlimSchema":
        from src.api.schemas import EntitySlimSchema
        identity = self.aspects["identity"]
        spatial = self.aspects["spatial"]
        combat = self.aspects["combat"]
        mind = self.aspects["mind"]
        progression = self.aspects["progression"]
        
        return EntitySlimSchema(
            id=self.id,
            kind=self.kind,
            display_name=identity.display_name,
            x=spatial.pos.x,
            y=spatial.pos.y,
            hp=combat.hp,
            max_hp=combat.max_hp,
            state=mind.ai_state.name.lower(),
            level=progression.level,
            tier=identity.tier,
            faction=identity.faction.name.lower() if hasattr(identity.faction, "name") else str(identity.faction).lower(),
            weapon_range=self._get_weapon_range(),
            combat_target_id=combat.combat_target_id,
            loot_progress=combat.loot_progress,
            loot_duration=loot_duration,
        )

    def to_full_schema(self, loot_duration: int = 3) -> "EntitySchema":
        from src.api.schemas import EntitySchema, EffectSchema, QuestSchema
        identity = self.aspects["identity"]
        spatial = self.aspects["spatial"]
        combat = self.aspects["combat"]
        mind = self.aspects["mind"]
        progression = self.aspects["progression"]
        inventory = self.aspects.get("inventory")
        
        elem = self._elem_dmg()
        from src.core.models.enums import Element
        return EntitySchema(
            id=self.id,
            kind=self.kind,
            display_name=identity.display_name,
            x=spatial.pos.x,
            y=spatial.pos.y,
            hp=combat.hp,
            max_hp=combat.max_hp,
            atk=combat.atk,
            def_=combat.def_,
            spd=combat.spd,
            luck=combat.luck,
            crit_rate=combat.crit_rate,
            evasion=combat.evasion,
            matk=combat.matk,
            mdef=combat.mdef,
            level=progression.level,
            xp=progression.xp,
            xp_to_next=progression.xp_to_next,
            gold=progression.gold,
            tier=identity.tier,
            faction=identity.faction.name.lower() if hasattr(identity.faction, "name") else str(identity.faction).lower(),
            state=mind.ai_state.name.lower(),
            weapon=inventory.weapon if inventory else None,
            armor=inventory.armor if inventory else None,
            accessory=inventory.accessory if inventory else None,
            inventory_count=inventory.used_slots if inventory else 0,
            inventory_max_slots=inventory.max_slots if inventory else 0,
            inventory_items=list(inventory.items) if inventory else [],
            inventory_weight=round(inventory.current_weight, 1) if inventory else 0.0,
            inventory_max_weight=inventory.max_weight if inventory else 0.0,
            vision_range=combat.vision_range,
            terrain_memory={f"{k[0]},{k[1]}": v for k, v in mind.terrain_memory.items()},
            entity_memory=list(mind.entity_memory),
            goals=list(mind.goals),
            loot_progress=combat.loot_progress,
            loot_duration=loot_duration,
            known_recipes=list(identity.known_recipes),
            craft_target=identity.craft_target,
            stamina=progression.stamina,
            max_stamina=progression.max_stamina,
            attributes=self._serialize_attrs(),
            attribute_caps=self._serialize_caps(),
            hero_class=self._serialize_hero_class(),
            skills=[s.to_api_schema() for s in progression.skills],
            class_mastery=progression.class_mastery,
            active_effects=[
                EffectSchema(
                    effect_type=eff.effect_type.name.lower() if hasattr(eff.effect_type, "name") else str(eff.effect_type).lower(),
                    source=eff.source,
                    remaining_ticks=eff.remaining_ticks,
                    atk_mult=eff.atk_mult,
                    def_mult=eff.def_mult,
                    spd_mult=eff.spd_mult,
                    crit_mult=eff.crit_mult,
                    evasion_mult=eff.evasion_mult,
                    hp_per_tick=eff.hp_per_tick,
                )
                for eff in combat.effects
                if not eff.expired
            ],
            base_atk=combat.atk,
            base_def=combat.def_,
            base_spd=combat.spd,
            base_matk=combat.matk,
            base_mdef=combat.mdef,
            base_crit_rate=combat.crit_rate,
            base_evasion=combat.evasion,
            hp_regen=combat.hp_regen,
            cooldown_reduction=combat.cooldown_reduction,
            loot_bonus=combat.loot_bonus,
            trade_bonus=combat.trade_bonus,
            interaction_speed=combat.interaction_speed,
            rest_efficiency=combat.rest_efficiency,
            speed_delay_move=round(1.0 * (10.0 / combat.spd), 2) if combat.spd > 0 else 5.0,
            speed_delay_attack=round(0.9 * (10.0 / combat.spd), 2) if combat.spd > 0 else 5.0,
            speed_delay_skill=round(1.2 * (10.0 / combat.spd), 2) if combat.spd > 0 else 5.0,
            speed_delay_harvest=round(0.7 * (10.0 / combat.spd), 2) if combat.spd > 0 else 5.0,
            fire_dmg_mult=elem.fire_dmg_mult,
            ice_dmg_mult=elem.ice_dmg_mult,
            lightning_dmg_mult=elem.lightning_dmg_mult,
            dark_dmg_mult=elem.dark_dmg_mult,
            elem_vuln_fire=combat.elemental_vulnerability(Element.FIRE),
            elem_vuln_ice=combat.elemental_vulnerability(Element.ICE),
            elem_vuln_lightning=combat.elemental_vulnerability(Element.LIGHTNING),
            elem_vuln_dark=combat.elemental_vulnerability(Element.DARK),
            region_id=spatial.region_id,
            difficulty_tier=spatial.difficulty_tier,
            current_region_id=spatial.current_region_id,
            weapon_range=self._get_weapon_range(),
            combat_target_id=combat.combat_target_id,
            traits=list(identity.traits),
            home_storage_used=inventory.home_storage.used_slots if inventory and inventory.home_storage else 0,
            home_storage_max=inventory.home_storage.max_slots if inventory and inventory.home_storage else 0,
            home_storage_level=inventory.home_storage.level if inventory and inventory.home_storage else 0,
            quests=[
                QuestSchema(
                    quest_id=q.quest_id,
                    quest_type=q.quest_type.name.lower() if hasattr(q.quest_type, "name") else str(q.quest_type).lower(),
                    title=q.title,
                    description=q.description,
                    target_kind=q.target_kind,
                    target_x=q.target_pos.x if q.target_pos else None,
                    target_y=q.target_pos.y if q.target_pos else None,
                    target_count=q.target_count,
                    progress=q.progress,
                    completed=q.completed,
                    gold_reward=q.gold_reward,
                    xp_reward=q.xp_reward,
                )
                for q in progression.quests
            ],
        )


    def _elem_dmg(self):
        """Calculates elemental damage multipliers based on traits."""
        from src.core.models.enums import TraitType
        fire = 1.0; ice = 1.0; lightning = 1.0; dark = 1.0
        
        traits = self.identity.traits
        if TraitType.ELEMENTALIST in traits:
            fire += 0.2; ice += 0.2; lightning += 0.2
        if TraitType.ARCANE_GIFTED in traits:
            dark += 0.2
        if TraitType.SPIRIT_TOUCHED in traits:
            fire += 0.1; ice += 0.1; lightning += 0.1; dark += 0.1

        # Use a simple class to match the 'elem.X' access in to_full_schema
        class ElemDmg:
            def __init__(self, f, i, l, d):
                self.fire_dmg_mult = f
                self.ice_dmg_mult = i
                self.lightning_dmg_mult = l
                self.dark_dmg_mult = d
        return ElemDmg(fire, ice, lightning, dark)

    def _serialize_attrs(self):
        """Serializes RPG attributes to Schema."""
        if not self.progression or not self.progression.attributes:
            return None
        from src.api.schemas import AttributeSchema
        a = self.progression.attributes
        return AttributeSchema(
            str=a.str_, agi=a.agi, vit=a.vit, int=a.int_,
            spi=a.spi, wis=a.wis, end=a.end, per=a.per, cha=a.cha,
            str_frac=a._str_frac, agi_frac=a._agi_frac, vit_frac=a._vit_frac,
            int_frac=a._int_frac, spi_frac=a._spi_frac, wis_frac=a._wis_frac,
            end_frac=a._end_frac, per_frac=a._per_frac, cha_frac=a._cha_frac
        )

    def _serialize_caps(self):
        """Serializes attribute caps to Schema."""
        if not self.progression or not self.progression.attribute_caps:
            return None
        from src.api.schemas import AttributeCapSchema
        c = self.progression.attribute_caps
        return AttributeCapSchema(
            str_cap=c.str_cap, agi_cap=c.agi_cap, vit_cap=c.vit_cap,
            int_cap=c.int_cap, spi_cap=c.spi_cap, wis_cap=c.wis_cap,
            end_cap=c.end_cap, per_cap=c.per_cap, cha_cap=c.cha_cap
        )

    def _serialize_hero_class(self) -> str:
        """Returns the lower-case name of the hero class."""
        from src.core.models.enums import HeroClass
        try:
            # self.progression.hero_class is assumed to be the enum value (int)
            return HeroClass(self.progression.hero_class).name.lower()
        except (ValueError, TypeError, AttributeError):
            return "none"

    def _get_weapon_range(self) -> int:
        """Returns the effective weapon range."""
        if not self.inventory or not self.inventory.weapon:
            return 1
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        w = ITEM_REGISTRY.get(self.inventory.weapon)
        return getattr(w, "range", 1) if w else 1

    def copy(self) -> Entity:
        """Fast copy for snapshot generation.
        
        Uses shallow model_copy for aspects because the Snapshot will be 
        pickled (deep copied) before reaching worker threads.
        """
        new_aspects = {}
        for name, aspect in self.aspects.items():
            if hasattr(aspect, "model_copy"):
                # Shallow copy is much faster and safe here as pickle handles the deep copy later
                new_aspects[name] = aspect.model_copy(deep=False)
            elif hasattr(aspect, "copy"):
                new_aspects[name] = aspect.copy()
            else:
                import copy
                new_aspects[name] = copy.copy(aspect)

        new_ent = Entity(
            id=self.id,
            kind=self.kind,
            next_act_at=self.next_act_at,
            aspects=new_aspects
        )
        
        # Re-attach aspects to ensure parent pointers/references are correct
        for aspect in new_ent.aspects.values():
            if hasattr(aspect, "on_attach"):
                aspect.on_attach(new_ent)
                
        return new_ent

from src.core.models.inventory import Inventory
from src.core.models.world_objects import HomeStorage, TreasureChest, CorpseNode

from src.core.aspects.identity import IdentityAspect
from src.core.aspects.spatial import SpatialAspect
from src.core.aspects.combat import CombatAspect
from src.core.aspects.inventory import InventoryAspect
from src.core.aspects.progression import ProgressionAspect
from src.core.aspects.mind import MindAspect

# Resolve forward references for Pydantic
# Rebuild all models to resolve forward references in a safe order
Entity.model_rebuild()

IdentityAspect.model_rebuild()
SpatialAspect.model_rebuild()
CombatAspect.model_rebuild()
InventoryAspect.model_rebuild()
ProgressionAspect.model_rebuild()
MindAspect.model_rebuild()

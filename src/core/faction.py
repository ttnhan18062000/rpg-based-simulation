"""Faction system — data-driven relationships between entity groups.

Design:
  - Every entity belongs to exactly one Faction.
  - Relationships between factions are stored in a registry and looked up at
    runtime, so new factions can be added without touching AI or combat code.
  - Each faction owns a territory tile type (Material) where its members heal
    and intruders receive debuffs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, unique
from typing import TYPE_CHECKING

from src.core.enums import Material

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Faction identity
# ---------------------------------------------------------------------------

@unique
class Faction(IntEnum):
    """Named factions.  Extend this enum to add new groups."""

    HERO_GUILD = 0
    GOBLIN_HORDE = 1
    WOLF_PACK = 2
    BANDIT_CLAN = 3
    UNDEAD = 4
    ORC_TRIBE = 5
    CENTAUR_HERD = 6
    FROST_KIN = 7
    LIZARDFOLK = 8
    DEMON_HORDE = 9


# ---------------------------------------------------------------------------
# Relationship between two factions
# ---------------------------------------------------------------------------

@unique
class FactionRelation(IntEnum):
    """How two factions regard each other."""

    ALLIED = 0     # Will not attack; may cooperate
    NEUTRAL = 1    # Ignore each other (unless provoked)
    HOSTILE = 2    # Attack on sight


# ---------------------------------------------------------------------------
# Territory descriptor
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class TerritoryInfo:
    """Describes what a faction considers home turf."""

    tile: Material                  # The Material that is this faction's territory
    atk_debuff: float = 0.7        # Multiplier applied to intruder ATK
    def_debuff: float = 0.7        # Multiplier applied to intruder DEF
    spd_debuff: float = 0.85       # Multiplier applied to intruder SPD
    alert_radius: int = 6          # How far the intrusion alert propagates


# ---------------------------------------------------------------------------
# Faction registry — single source of truth
# ---------------------------------------------------------------------------

class FactionRegistry:
    """Data-driven registry mapping factions → territories and relations.

    Usage:
        reg = FactionRegistry.default()
        reg.relation(Faction.HERO_GUILD, Faction.GOBLIN_HORDE)  # → HOSTILE
        reg.territory_for(Faction.GOBLIN_HORDE)                 # → TerritoryInfo(CAMP, ...)
        reg.faction_for_kind("hero")                            # → Faction.HERO_GUILD
        reg.is_hostile(attacker_faction, defender_faction)       # → bool
        reg.owns_tile(Faction.HERO_GUILD, Material.TOWN)        # → True
    """

    __slots__ = ("_relations", "_territories", "_kind_map")

    def __init__(self) -> None:
        # (faction_a, faction_b) → FactionRelation  (order-independent)
        self._relations: dict[tuple[Faction, Faction], FactionRelation] = {}
        # faction → TerritoryInfo
        self._territories: dict[Faction, TerritoryInfo] = {}
        # entity kind string → faction
        self._kind_map: dict[str, Faction] = {}

    # -- builders --

    def set_relation(self, a: Faction, b: Faction, rel: FactionRelation) -> None:
        self._relations[(a, b)] = rel
        self._relations[(b, a)] = rel

    def set_territory(self, faction: Faction, info: TerritoryInfo) -> None:
        self._territories[faction] = info

    def register_kind(self, kind: str, faction: Faction) -> None:
        self._kind_map[kind] = faction

    # -- queries --

    def relation(self, a: Faction, b: Faction) -> FactionRelation:
        if a == b:
            return FactionRelation.ALLIED
        return self._relations.get((a, b), FactionRelation.NEUTRAL)

    def is_hostile(self, a: Faction, b: Faction) -> bool:
        return self.relation(a, b) == FactionRelation.HOSTILE

    def is_allied(self, a: Faction, b: Faction) -> bool:
        return self.relation(a, b) == FactionRelation.ALLIED

    def territory_for(self, faction: Faction) -> TerritoryInfo | None:
        return self._territories.get(faction)

    def faction_for_kind(self, kind: str) -> Faction | None:
        return self._kind_map.get(kind)

    def owns_tile(self, faction: Faction, mat: Material) -> bool:
        """Return True if *mat* is this faction's home territory tile."""
        info = self._territories.get(faction)
        return info is not None and info.tile == mat

    def tile_owner(self, mat: Material) -> Faction | None:
        """Return the faction that owns *mat*, or None."""
        for fac, info in self._territories.items():
            if info.tile == mat:
                return fac
        return None

    def is_home_territory(self, faction: Faction, mat: Material) -> bool:
        """Check if *mat* is home territory for *faction*."""
        return self.owns_tile(faction, mat)

    def is_enemy_territory(self, faction: Faction, mat: Material) -> bool:
        """Check if *mat* is territory of a hostile faction."""
        owner = self.tile_owner(mat)
        if owner is None:
            return False
        return self.is_hostile(faction, owner)

    # -- factory --

    @classmethod
    def default(cls) -> FactionRegistry:
        """Build the default registry with Hero Guild vs Goblin Horde."""
        reg = cls()

        # --- Relations: hero vs all hostile; most factions hostile to each other ---
        all_hostile = [
            Faction.GOBLIN_HORDE, Faction.WOLF_PACK, Faction.BANDIT_CLAN,
            Faction.UNDEAD, Faction.ORC_TRIBE, Faction.CENTAUR_HERD,
            Faction.FROST_KIN, Faction.LIZARDFOLK, Faction.DEMON_HORDE,
        ]
        for fac in all_hostile:
            reg.set_relation(Faction.HERO_GUILD, fac, FactionRelation.HOSTILE)
        # Inter-faction hostility (everyone fights everyone)
        for i, a in enumerate(all_hostile):
            for b in all_hostile[i + 1:]:
                reg.set_relation(a, b, FactionRelation.HOSTILE)
        # Exception: goblins and orcs are neutral
        reg.set_relation(Faction.GOBLIN_HORDE, Faction.ORC_TRIBE, FactionRelation.NEUTRAL)

        # --- Territories ---
        reg.set_territory(Faction.HERO_GUILD, TerritoryInfo(
            tile=Material.TOWN,
            atk_debuff=0.6, def_debuff=0.6, spd_debuff=0.8, alert_radius=6,
        ))
        reg.set_territory(Faction.GOBLIN_HORDE, TerritoryInfo(
            tile=Material.CAMP,
            atk_debuff=0.7, def_debuff=0.7, spd_debuff=0.85, alert_radius=6,
        ))
        reg.set_territory(Faction.WOLF_PACK, TerritoryInfo(
            tile=Material.FOREST,
            atk_debuff=0.8, def_debuff=0.8, spd_debuff=0.9, alert_radius=5,
        ))
        reg.set_territory(Faction.BANDIT_CLAN, TerritoryInfo(
            tile=Material.DESERT,
            atk_debuff=0.75, def_debuff=0.75, spd_debuff=0.85, alert_radius=6,
        ))
        reg.set_territory(Faction.UNDEAD, TerritoryInfo(
            tile=Material.SWAMP,
            atk_debuff=0.7, def_debuff=0.7, spd_debuff=0.8, alert_radius=7,
        ))
        reg.set_territory(Faction.ORC_TRIBE, TerritoryInfo(
            tile=Material.MOUNTAIN,
            atk_debuff=0.75, def_debuff=0.75, spd_debuff=0.85, alert_radius=6,
        ))
        reg.set_territory(Faction.CENTAUR_HERD, TerritoryInfo(
            tile=Material.GRASSLAND,
            atk_debuff=0.8, def_debuff=0.8, spd_debuff=0.9, alert_radius=8,
        ))
        reg.set_territory(Faction.FROST_KIN, TerritoryInfo(
            tile=Material.SNOW,
            atk_debuff=0.7, def_debuff=0.7, spd_debuff=0.8, alert_radius=6,
        ))
        reg.set_territory(Faction.LIZARDFOLK, TerritoryInfo(
            tile=Material.JUNGLE,
            atk_debuff=0.75, def_debuff=0.75, spd_debuff=0.85, alert_radius=5,
        ))
        reg.set_territory(Faction.DEMON_HORDE, TerritoryInfo(
            tile=Material.VOLCANIC,
            atk_debuff=0.65, def_debuff=0.65, spd_debuff=0.75, alert_radius=7,
        ))

        # --- Kind → faction mapping ---
        reg.register_kind("hero", Faction.HERO_GUILD)
        # Goblins
        reg.register_kind("goblin", Faction.GOBLIN_HORDE)
        reg.register_kind("goblin_scout", Faction.GOBLIN_HORDE)
        reg.register_kind("goblin_warrior", Faction.GOBLIN_HORDE)
        reg.register_kind("goblin_chief", Faction.GOBLIN_HORDE)
        # Wolves (forest)
        reg.register_kind("wolf", Faction.WOLF_PACK)
        reg.register_kind("dire_wolf", Faction.WOLF_PACK)
        reg.register_kind("alpha_wolf", Faction.WOLF_PACK)
        # Bandits (desert)
        reg.register_kind("bandit", Faction.BANDIT_CLAN)
        reg.register_kind("bandit_archer", Faction.BANDIT_CLAN)
        reg.register_kind("bandit_chief", Faction.BANDIT_CLAN)
        # Undead (swamp)
        reg.register_kind("skeleton", Faction.UNDEAD)
        reg.register_kind("zombie", Faction.UNDEAD)
        reg.register_kind("lich", Faction.UNDEAD)
        # Orcs (mountain)
        reg.register_kind("orc", Faction.ORC_TRIBE)
        reg.register_kind("orc_warrior", Faction.ORC_TRIBE)
        reg.register_kind("orc_warlord", Faction.ORC_TRIBE)
        # Centaurs (grassland)
        reg.register_kind("centaur", Faction.CENTAUR_HERD)
        reg.register_kind("centaur_lancer", Faction.CENTAUR_HERD)
        reg.register_kind("centaur_elder", Faction.CENTAUR_HERD)
        # Frost kin (snow)
        reg.register_kind("frost_wolf", Faction.FROST_KIN)
        reg.register_kind("frost_giant", Faction.FROST_KIN)
        reg.register_kind("frost_shaman", Faction.FROST_KIN)
        # Lizardfolk (jungle)
        reg.register_kind("lizard", Faction.LIZARDFOLK)
        reg.register_kind("lizard_warrior", Faction.LIZARDFOLK)
        reg.register_kind("lizard_chief", Faction.LIZARDFOLK)
        # Demons (volcanic)
        reg.register_kind("imp", Faction.DEMON_HORDE)
        reg.register_kind("hellhound", Faction.DEMON_HORDE)
        reg.register_kind("demon_lord", Faction.DEMON_HORDE)

        return reg

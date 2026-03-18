"""World Boss (Calamity) templates and definitions."""

from __future__ import annotations
from dataclasses import dataclass, field
from src.core.enums import Faction, HeroClass

@dataclass(frozen=True, slots=True)
class CalamityTemplate:
    """Blueprint for a world boss."""
    template_id: str
    name: str
    faction: Faction
    archetype: HeroClass
    stat_multiplier: float = 5.0
    legendary_loot: list[str] = field(default_factory=list)
    traits: list[int] = field(default_factory=list)
    description: str = ""

CALAMITY_TEMPLATES: dict[str, CalamityTemplate] = {
    "gorath": CalamityTemplate(
        template_id="gorath",
        name="Gorath the World-Breaker",
        faction=Faction.ORC_CLAN,
        archetype=HeroClass.CHAMPION,
        stat_multiplier=6.0,
        legendary_loot=["gorath_cleaver", "calamity_remnant"],
        traits=[0, 12, 14],  # AGGRESSIVE, BERSERKER, RESILIENT (manual map for now)
        description="A mountain-sized orc warlord whose mere footsteps crack the earth."
    ),
    "vexira": CalamityTemplate(
        template_id="vexira",
        name="Vexira the Soul-Weaver",
        faction=Faction.UNDEAD_HORDE,
        archetype=HeroClass.ARCHMAGE,
        stat_multiplier=5.0,
        legendary_loot=["vexira_fang", "calamity_remnant"],
        traits=[1, 13, 15],  # CAUTIOUS, TACTICAL, ARCANE_GIFTED
        description="An ancient lich queen who drains the life from entire regions."
    )
}

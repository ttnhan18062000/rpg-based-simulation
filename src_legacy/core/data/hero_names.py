"""Hero name generation tables and logic."""

from __future__ import annotations
from typing import TYPE_CHECKING
from src_legacy.core.models.enums import TraitType

if TYPE_CHECKING:
    from src_legacy.platform.rng import DeterministicRNG

# --- Name Tables ---

FIRST_NAMES = [
    "Kael", "Lyra", "Thorne", "Sera", "Aldric", "Mira", "Rowan", "Elowen",
    "Garrick", "Talia", "Caden", "Elara", "Bryn", "Sylas", "Vane", "Kira",
    "Joram", "Liora", "Finn", "Aria", "Corvus", "Lyza", "Torin", "Maia",
    "Rylan", "Eryn", "Kaelen", "Valer", "Zada", "Caelum", "Nyx", "Oberon"
]

TRAIT_TITLES = {
    TraitType.AGGRESSIVE: "the Fierce",
    TraitType.CAUTIOUS: "the Careful",
    TraitType.BRAVE: "the Bold",
    TraitType.COWARDLY: "the Craven",
    TraitType.BLOODTHIRSTY: "the Merciless",
    TraitType.GREEDY: "the Grasper",
    TraitType.GENEROUS: "the Kind",
    TraitType.CHARISMATIC: "the Bright",
    TraitType.LONER: "the Silent",
    TraitType.DILIGENT: "the Steadfast",
    TraitType.LAZY: "the Idle",
    TraitType.CURIOUS: "the Seeker",
    TraitType.BERSERKER: "the Wild",
    TraitType.TACTICAL: "the Sharp",
    TraitType.RESILIENT: "the Iron",
    TraitType.ARCANE_GIFTED: "the Mystic",
    TraitType.SPIRIT_TOUCHED: "the Pale",
    TraitType.ELEMENTALIST: "the Storm",
    TraitType.KEEN_EYED: "the Watcher",
    TraitType.OBLIVIOUS: "the Dreamer",
}

def generate_hero_name(rng: DeterministicRNG, eid: int, tick: int, traits: list[int]) -> str:
    """Generate a unique hero name based on RNG and traits.
    
    Format: "{first_name} {title}"
    """
    from src_legacy.core.models.enums import Domain
    
    # Pick a first name
    name_idx = rng.next_int(Domain.SPAWN, eid, tick, 0, len(FIRST_NAMES) - 1)
    first_name = FIRST_NAMES[name_idx]
    
    # Pick a title from traits (if any)
    title = ""
    if traits:
        # Sort to ensure determinism if traits list order varies (unlikely but safe)
        valid_traits = sorted([t for t in traits if t in TRAIT_TITLES])
        if valid_traits:
            trait_idx = rng.next_int(Domain.SPAWN, eid, tick + 1, 0, len(valid_traits) - 1)
            title = TRAIT_TITLES[valid_traits[trait_idx]]
            
    if title:
        return f"{first_name} {title}"
    return first_name

from __future__ import annotations

from typing import Optional, Tuple, Dict

from pydantic import BaseModel, ConfigDict

from src.core.enums import EntityRole, Faction


class ResolvedEntityRuntimeContract(BaseModel):
    """
    Boundary model between catalog resolution and runtime entity creation.

    All fields are derived from resolved catalog data. Profile references are
    string IDs only — not resolved profile objects — to keep this model
    decoupled from catalog internals. No enemy/ally source-truth fields are
    stored here.
    """

    model_config = ConfigDict(frozen=True)

    # --- Clean identity ---
    archetype_id: str
    race_id: str
    faction_id: str
    role_id: str
    profession_id: Optional[str] = None
    kind: str

    # --- Legacy projection only (optional; not source truth) ---
    legacy_role: Optional[EntityRole] = None
    legacy_faction: Optional[Faction] = None

    # --- Runtime combat values ---
    hp: int
    max_hp: int
    atk: int
    def_stat: int
    attack_range: int
    readiness: float

    # --- Inventory seed ---
    inventory_items: Dict[str, int]
    starting_gold: float

    # --- Traits and themes ---
    traits: Tuple[str, ...]
    themes: Tuple[str, ...]

    # --- Profile source IDs (string refs only) ---
    cognition_profile_id: Optional[str] = None
    drive_profile_id: Optional[str] = None
    need_profile_id: Optional[str] = None
    sense_profile_id: Optional[str] = None
    skill_profile_id: Optional[str] = None

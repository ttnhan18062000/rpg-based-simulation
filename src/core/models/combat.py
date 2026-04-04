from __future__ import annotations
from typing import Mapping, Any, TYPE_CHECKING
from pydantic import Field
from src.core.models.base import SimulationModel

class CombatTraceDetails(SimulationModel):
    """Deep details of a combat event (e.g., crit, evasion, overkill).
    
    AOA Pillar 2: Introspection. These fields enable detailed simulation 
    logging and frontend animation/UI feedback.
    """
    raw_damage: int = 0
    mitigated_damage: int = 0
    absorbed_damage: int = 0
    
    crit_multiplier: float = 1.0
    evasion_chance: float = 0.0
    elemental_mult: float = 1.0
    
    is_crit: bool = False
    is_evaded: bool = False
    is_parried: bool = False
    overkill: int = 0
    is_shattered: bool = False
    effect_triggers: list[str] = Field(default_factory=list)

class CombatTraceRecord(SimulationModel):
    """Authoritative record of a combat interaction.
    
    Used by both CombatAspect (history) and CombatTraceUpdate (intent) 
    to ensure architectural consistency and prevent circular dependencies.
    """
    tick: int
    attacker_id: int
    defender_id: int
    damage: int
    attacker_name: str = ""
    defender_name: str = ""
    skill_name: str = "attack"
    
    details: CombatTraceDetails = Field(default_factory=CombatTraceDetails)
    
    # Metadata for enriched events (e.g. coordinates, weapon kind)
    metadata: Mapping[str, Any] = Field(default_factory=dict)

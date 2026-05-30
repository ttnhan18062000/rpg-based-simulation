"""
src/domains/progression/schema.py
───────────────────────────────────────────────────────────────────────────────
Phase 6 — Progression and Reward Conversion schemas.
Frozen, immutable dataclasses.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Tuple, Mapping


class ConversionKind(str, Enum):
    EQUIP_ITEM = "EQUIP_ITEM"
    REPAIR_GEAR = "REPAIR_GEAR"
    SELL_LOOT = "SELL_LOOT"
    STORE_ITEM = "STORE_ITEM"
    CRAFT_ITEM = "CRAFT_ITEM"
    TRAIN_SKILL = "TRAIN_SKILL"
    ALLOCATE_AP = "ALLOCATE_AP"
    BUY_SUPPLY = "BUY_SUPPLY"
    BUY_UPGRADE = "BUY_UPGRADE"
    SAVE_FOR_LATER = "SAVE_FOR_LATER"
    ASK_ITEM_USE = "ASK_ITEM_USE"


@dataclass(frozen=True, slots=True)
class PossessionMeaning:
    """
    Subjective value interpretation of an inventory item.
    """
    item_id: str
    known_uses: Tuple[str, ...] = field(default_factory=tuple)
    estimated_value: float = 0.0
    keep_priority: float = 0.0
    sell_priority: float = 0.0
    equip_priority: float = 0.0
    craft_priority: float = 0.0
    reason: Optional[str] = None


@dataclass(frozen=True, slots=True)
class PossessionUnderstandingComponent:
    """
    Aggregated possession meaning records on an entity.
    """
    meanings: Mapping[str, PossessionMeaning] = field(default_factory=dict)
    last_evaluated_tick: int = 0


@dataclass(frozen=True, slots=True)
class GrowthGap:
    """
    Identified progression gap (weakness/lack).
    """
    key: str  # "weapon_gap" | "repair_gap" | "material_gap" | "gold_gap" | "level_gap"
    severity: float
    confidence: float
    reason: str
    candidate_resolution_tags: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class GrowthGapReport:
    """
    Identified gaps on the actor.
    """
    gaps: Tuple[GrowthGap, ...] = field(default_factory=tuple)
    dominant_gap: Optional[str] = None


@dataclass(frozen=True, slots=True)
class RewardEntry:
    """
    A ledger entry for recently gained XP, gold, or items.
    """
    tick: int
    kind: str  # "item" | "gold" | "xp"
    subject: str
    quantity: int | float = 1
    source: Optional[str] = None
    consumed_by_plan: bool = False


@dataclass(frozen=True, slots=True)
class RewardLedgerComponent:
    """
    Ledger component to track rewards in the conversion loop.
    """
    entries: Tuple[RewardEntry, ...] = field(default_factory=tuple)
    last_processed_tick: int = 0


@dataclass(frozen=True, slots=True)
class ConversionOption:
    """
    A single generated conversion choice.
    """
    kind: ConversionKind
    score: float
    expected_growth_delta: float
    cost_gold: int = 0
    requirements: Tuple[str, ...] = field(default_factory=tuple)
    blockers: Tuple[str, ...] = field(default_factory=tuple)
    reason: Optional[str] = None


@dataclass(frozen=True, slots=True)
class ProgressionDecisionResult:
    """
    Output decision of the conversion scoring loop.
    """
    entity_id: int
    selected: Tuple[ConversionOption, ...] = field(default_factory=tuple)
    trace: Dict[str, Any] = field(default_factory=dict)
    reason: Optional[str] = None

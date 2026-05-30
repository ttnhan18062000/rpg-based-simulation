"""
src/domains/progression/interpretation.py
───────────────────────────────────────────────────────────────────────────────
Phase 6 — RewardInterpretationService

Interprets the recent rewards against identified active growth gaps.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple

from src.core.state import EntityState, AuthoritativeState
from src.domains.progression.schema import RewardLedgerComponent, PossessionUnderstandingComponent, GrowthGapReport


@dataclass(frozen=True, slots=True)
class RewardMeaning:
    entry_index: int
    meaning: str
    priority: float
    suggested_conversion_tags: Tuple[str, ...] = field(default_factory=tuple)
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class RewardInterpretationReport:
    meanings: Tuple[RewardMeaning, ...] = field(default_factory=tuple)


class RewardInterpretationService:
    """
    Translates recent reward events into subjectively useful meanings.
    """

    @staticmethod
    def interpret(
        entity: EntityState,
        ledger: RewardLedgerComponent,
        possession: PossessionUnderstandingComponent,
        gaps: GrowthGapReport,
        state: AuthoritativeState,
    ) -> RewardInterpretationReport:
        meanings = []

        dominant = gaps.dominant_gap

        for idx, entry in enumerate(ledger.entries):
            if entry.consumed_by_plan:
                continue

            meaning_str = "unspecified"
            priority = 0.1
            tags = ()
            reason = "No active gap matches this reward."

            # Gold Reward Interpretation
            if entry.kind == "gold":
                if dominant == "repair_gap":
                    meaning_str = "can_repair_weapon"
                    priority = 0.9
                    tags = ("repair",)
                    reason = "Affords critical blacksmith repair to fix durability weakness."
                elif dominant == "weapon_gap":
                    meaning_str = "save_for_weapon_upgrade"
                    priority = 0.7
                    tags = ("save", "buy_upgrade")
                    reason = "Gold can fund weapon purchase/upgrade path."
                else:
                    meaning_str = "generic_savings"
                    priority = 0.4
                    tags = ("save",)
                    reason = "No urgent combat gaps. Save for safety."

            # Item Reward Interpretation
            elif entry.kind == "item":
                item_id = entry.subject
                pos_meaning = possession.meanings.get(item_id)
                
                # Check weapon upgrade fit
                is_weapon = item_id in ("iron_sword", "steel_sword", "rusted_sword")
                if is_weapon and pos_meaning and pos_meaning.equip_priority > 0.8:
                    meaning_str = "direct_weapon_upgrade"
                    priority = 0.95
                    tags = ("equip",)
                    reason = "Perfect upgrade to current main hand weapon."
                
                # Check known recipe material fit
                elif pos_meaning and pos_meaning.keep_priority > 0.8:
                    meaning_str = "recipe_material"
                    priority = 0.8
                    tags = ("keep", "craft")
                    reason = f"Essential material for active recipe: {pos_meaning.known_uses}."
                
                # Check ancient fragment fit
                elif item_id == "ancient_fragment":
                    meaning_str = "unknown_rare_item"
                    priority = 0.85
                    tags = ("ask", "store")
                    reason = "Ancient fragment might contain vital strategic clues. Seek guide info."

                else:
                    meaning_str = "sellable_loot"
                    priority = 0.6
                    tags = ("sell",)
                    reason = "Junk loot. Sell to resolve gold/upgrade gaps."

            # XP Reward Interpretation
            elif entry.kind == "xp":
                meaning_str = "unallocated_points"
                priority = 0.75
                tags = ("allocate",)
                reason = "XP enables level progression or AP allocation plans."

            meanings.append(RewardMeaning(
                entry_index=idx,
                meaning=meaning_str,
                priority=priority,
                suggested_conversion_tags=tags,
                reason=reason
            ))

        return RewardInterpretationReport(
            meanings=tuple(meanings)
        )

"""
src/domains/progression/resolver.py
───────────────────────────────────────────────────────────────────────────────
Phase 6 — ConversionIntentResolver

Maps subjective progression decisions to executable StrategicUpdates,
IdentityUpdates, or ActionIntents.
"""

from __future__ import annotations
from typing import Dict, Any

from src.core.state import EntityState, AuthoritativeState, ItemStack, EquipSlot
from src.core.updates import EntityUpdate, IdentityUpdate, EquipmentUpdate, TaskUpdate
from src.core.update_models.resources import ResourceTransferIntent
from src.domains.progression.schema import ConversionKind, ProgressionDecisionResult


class ConversionIntentResolver:
    """
    Translates selected conversion results into EntityUpdate payloads.
    """

    @staticmethod
    def resolve(
        entity: EntityState,
        decision: ProgressionDecisionResult,
        state: AuthoritativeState,
    ) -> EntityUpdate:
        update = EntityUpdate(entity_id=entity.id)

        if not decision.selected:
            return update

        selected = decision.selected[0]
        kind = selected.kind

        if kind == ConversionKind.EQUIP_ITEM:
            # Map EQUIP_ITEM to EquipmentUpdate
            # We assume iron_sword stack exists in inventory to equip
            update = EntityUpdate(
                entity_id=entity.id,
                equipment=EquipmentUpdate(
                    slot_updates={EquipSlot.MAIN_HAND: "iron_sword"}
                )
            )

        elif kind == ConversionKind.REPAIR_GEAR:
            # Map REPAIR_GEAR to Blacksmith Craft/Repair Task payload
            update = EntityUpdate(
                entity_id=entity.id,
                task=TaskUpdate(
                    work_kind_set="BLACKSMITH_REPAIR",
                    payload_set={"target_id": "town_blacksmith", "cost_gold": selected.cost_gold}
                )
            )

        elif kind == ConversionKind.CRAFT_ITEM:
            # Map CRAFT_ITEM to Blacksmith Craft intent payload
            update = EntityUpdate(
                entity_id=entity.id,
                task=TaskUpdate(
                    work_kind_set="BLACKSMITH_CRAFT",
                    payload_set={"recipe": "iron_sword"}
                )
            )

        elif kind == ConversionKind.SELL_LOOT:
            # Map SELL_LOOT to ResourceTransferIntent for Shop Sell
            intent = ResourceTransferIntent(
                source_id="town_shop",
                source_kind="SHOP_SELL",
                items_remove=[ItemStack("broken_mug", 5)],
                gold_delta=10,
                transfer_kind="SELL"
            )
            update = EntityUpdate(
                entity_id=entity.id,
                resource_transfers=[intent]
            )

        elif kind == ConversionKind.ALLOCATE_AP:
            # Known, intentional divergence (DEV-004, docs/guidelines/intentional_divergences.md):
            # this branch decrements unspent_ap but grants zero attribute delta. Currently unreachable
            # in any live run — ProgressionConversionPhase is gated by ENABLE_PROGRESSION_EVOLUTION
            # (FeatureMode.OFF, DEV-003).
            update = EntityUpdate(
                entity_id=entity.id,
                identity=IdentityUpdate(
                    unspent_ap_delta=-1
                )
            )

        elif kind == ConversionKind.ASK_ITEM_USE:
            # Map ASK_ITEM_USE to information querying Task Payload
            update = EntityUpdate(
                entity_id=entity.id,
                task=TaskUpdate(
                    work_kind_set="ASK_INFORMATION",
                    payload_set={"subject": "ancient_fragment", "target": "guide"}
                )
            )

        return update

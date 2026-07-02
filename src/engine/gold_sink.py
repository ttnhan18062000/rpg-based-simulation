# Compliance IDs: TOWN-179, TOWN-180
# TCK-20260619-E33C-GOLD-SINK
"""Gold Sink System — triggers fee/tax drains on INFLATION_SPIRAL alert windows.

Three mechanisms are applied at every WINDOW_SIZE tick boundary when the Gini
coefficient exceeds INFLATION_SPIRAL_GINI_THRESHOLD (0.7):

1. REPAIR_FEE  — equipment with durability < 50 % incurs a 1-gold-per-slot fee.
2. SERVICE_FEE — flat 1-gold surcharge per alive entity with gold > 0.
3. TAX         — 5 % wealth tax on entities above 1.5× the mean gold balance,
                 clamped to [1, 50] gold.

Conservation law (Chapter 03): all gold deductions are proposed via
ResourceTransferIntent and resolved through the authoritative pipeline
(ResourceTransactionSystem).  No gold is created or destroyed; the resolver
rejects intents where the entity lacks sufficient gold.
"""
from __future__ import annotations

import logging
from dataclasses import replace
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate
    from src.engine.cadence import SystemCadence

logger = logging.getLogger(__name__)

# Fee constants
_REPAIR_FEE_PER_SLOT: int = 1          # gold per degraded equipment slot
_SERVICE_FEE_FLAT: int = 1             # flat gold surcharge per entity
_TAX_RATE: float = 0.05                # fraction of gold taxed
_TAX_MIN: int = 1
_TAX_MAX: int = 50
_TAX_WEALTH_MULTIPLIER: float = 1.5   # entities above mean * multiplier are taxed


class GoldSinkSystem:
    """Governance-phase gold sink: drains excess gold during INFLATION_SPIRAL windows.

    Called from AuthoritativeApplyPipeline Phase 5 (Governance & Ecology).
    Only activates at WINDOW_SIZE tick boundaries when Gini > threshold.
    All gold transfers are proposed via ResourceTransferIntent and resolved by
    ResourceTransactionSystem — no direct state mutation.
    VERIFIED v2: gold_sink_conservation
    """

    @staticmethod
    def apply(state: "AuthoritativeState", update: "StateUpdate", cadence: "SystemCadence | None" = None) -> "StateUpdate":
        """Inject gold sink ResourceTransferIntents when INFLATION_SPIRAL is active.

        Returns the updated StateUpdate with intents appended to entity updates.
        Returns update unchanged when the sink condition is not met.
        """
        from src.economy.health_monitor import EconomyHealthMonitor
        from src.core.update_models.resources import ResourceTransferIntent
        from src.core.updates import EntityUpdate

        # Only fire at window-size boundaries (same cadence as EconomyHealthMonitor)
        snapshot = EconomyHealthMonitor.sample(state, state.tick)
        if snapshot is None:
            return update

        # Only fire on INFLATION_SPIRAL (gini > 0.7)
        if snapshot.gini_coefficient <= EconomyHealthMonitor.INFLATION_SPIRAL_GINI_THRESHOLD:
            return update

        alive_entities = [e for e in state.entities.values() if e.combat.alive]
        if not alive_entities:
            return update

        # Pre-compute mean gold for TAX threshold
        gold_values = [float(e.inventory.gold) for e in alive_entities]
        mean_gold = sum(gold_values) / len(gold_values) if gold_values else 0.0
        tax_threshold = mean_gold * _TAX_WEALTH_MULTIPLIER

        entity_updates = dict(update.entity_updates)
        total_gold_attempted: int = 0

        for entity in sorted(alive_entities, key=lambda e: e.id):
            intents: List[ResourceTransferIntent] = []
            entity_gold = entity.inventory.gold

            # --- Mechanism 1: REPAIR_FEE ---
            degraded_slots = GoldSinkSystem._count_degraded_slots(entity)
            if degraded_slots > 0 and entity_gold > 0:
                fee = min(degraded_slots * _REPAIR_FEE_PER_SLOT, entity_gold)
                intents.append(ResourceTransferIntent(
                    source_id="gold_sink",
                    source_kind="REPAIR_FEE",
                    gold_cost=fee,
                    gold_delta=0,
                    transfer_kind="FEE",
                ))
                total_gold_attempted += fee

            # --- Mechanism 2: SERVICE_FEE ---
            if entity_gold >= _SERVICE_FEE_FLAT:
                intents.append(ResourceTransferIntent(
                    source_id="gold_sink",
                    source_kind="SERVICE_FEE",
                    gold_cost=_SERVICE_FEE_FLAT,
                    gold_delta=0,
                    transfer_kind="FEE",
                ))
                total_gold_attempted += _SERVICE_FEE_FLAT

            # --- Mechanism 3: TAX ---
            if float(entity_gold) > tax_threshold and entity_gold > 0:
                tax = min(_TAX_MAX, max(_TAX_MIN, int(entity_gold * _TAX_RATE)))
                tax = min(tax, entity_gold)  # never exceed what entity has
                intents.append(ResourceTransferIntent(
                    source_id="gold_sink",
                    source_kind="TAX",
                    gold_cost=tax,
                    gold_delta=0,
                    transfer_kind="FEE",
                ))
                total_gold_attempted += tax

            if not intents:
                continue

            # Merge intents into entity update
            existing_upd = entity_updates.get(entity.id, EntityUpdate(entity_id=entity.id))
            merged_transfers = list(existing_upd.resource_transfers) + intents
            entity_updates[entity.id] = replace(existing_upd, resource_transfers=merged_transfers)

        if total_gold_attempted == 0:
            return update

        # Track sink cycle in global_resources counters (advisory, not conservation-critical)
        new_resource_updates = dict(update.resource_updates)
        new_resource_updates["metric_gold_sink_ticks"] = (
            new_resource_updates.get("metric_gold_sink_ticks", 0.0) + 1.0
        )
        new_resource_updates["metric_gold_sink_last_attempted"] = float(total_gold_attempted)

        logger.debug(
            "GoldSinkSystem tick=%d gini=%.4f attempted_drain=%d entities=%d",
            state.tick,
            snapshot.gini_coefficient,
            total_gold_attempted,
            len([e for e in alive_entities if entity_updates.get(e.id) is not None
                 and entity_updates[e.id].resource_transfers]),
        )

        return replace(
            update,
            entity_updates=entity_updates,
            resource_updates=new_resource_updates,
        )

    @staticmethod
    def _count_degraded_slots(entity) -> int:
        """Return the number of equipped slots with durability < 0.5 (50 %)."""
        durability = getattr(entity.equipment, "durability", {})
        slots = getattr(entity.equipment, "slots", {})
        if not slots or not durability:
            return 0
        degraded = sum(
            1 for slot in slots
            if durability.get(slot, 1.0) < 0.5
        )
        return degraded

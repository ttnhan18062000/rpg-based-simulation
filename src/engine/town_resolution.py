# Compliance IDs: TOWN-015, TOWN-018, TOWN-019
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Dict

from src.core.enums import Faction
from src.core.treasury import treasury_key
from src.core.updates import (
    BuildingUpdate,
    CombatUpdate,
    EntityUpdate,
    InventoryUpdate,
)

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, BuildingState
    from src.core.updates import StateUpdate
    from src.engine.cadence import SystemCadence

class TownResolutionSystem:
    """
    Authoritative handler for town territory resolution.
    Optimized v2: Uses spatial indexing and caches to avoid O(N*M) bottlenecks.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate, cadence: SystemCadence | None = None) -> StateUpdate:
        """
        Detect entities in town and apply general passive laws (Healing).
        Also handles regional taxation and maintenance.
        """
        from src.domains.world_emergence.schema import WorldEventCategory
        from src.engine.cadence import SystemCadence as DefaultCadence
        from src.engine.spatial_query import SpatialQueryService

        cadence = cadence or DefaultCadence()

        refined_entity_updates = dict(update.entity_updates)
        new_resource_updates = dict(update.resource_updates)
        refined_building_updates = dict(update.building_updates)

        # 1. Early exits
        has_town = len(state.town_tiles) > 0
        has_regions = len(state.regions) > 0

        if not has_town and not has_regions:
            return update

        # Economic Vacancy Signal consumer (TCK-20260903-ECONOMIC-VACANCY-SIGNAL, PP-20). Reads
        # the previous tick's already-applied, bounded window (src/engine/apply.py:335-338), same
        # one-tick-lag law as FactionAwarenessService.compute_tension_updates. Purely additive
        # metrics -- deliberately does not touch BuildingState.functional or gate
        # BlacksmithSystem.enforce, preserving TOWN-017's verified P0 parity entry.
        new_metric_counters = dict(update.metric_counters)
        for event in getattr(state, "recent_world_events", []):
            if event.category != WorldEventCategory.PRODUCTION_ROLE_VACATED:
                continue
            key = f"economic_vacancy_detected_region_{event.region_id}"
            new_metric_counters[key] = new_metric_counters.get(key, 0) + 1

        # 2. Constants & Caches
        PASSIVE_HEAL_AMT = 1
        is_tax_tick = (state.tick % (cadence.town_resolution * 2) == 0)
        
        # Pre-cache faction keys for faster resource lookup
        faction_keys: Dict[int, str] = {f: treasury_key(f) for f in Faction}  # RegionState.owner_faction_id is an int; one key scheme (src/core/treasury.py)
        
        # Pre-filter regions with effects
        regions_with_effects = [r for r in state.regions.values() if r.owner_faction_id is not None or r.suppression_active]
        has_regional_effects = len(regions_with_effects) > 0

        # 3. Entity Loop (Town & Regional Effects)
        # Optimization: Only process entities currently in town OR affected by regions
        # If it's a tax tick, we must check everyone in regions.
        from src.core.dirty import get_relevant_entity_ids
        if not is_tax_tick:
            candidate_ids = get_relevant_entity_ids(state, update, "town")
        else:
            candidate_ids = state.entities.keys()
        
        for e_id in candidate_ids:
            entity = state.entities.get(e_id)
            if not entity or not entity.combat.alive or not entity.lifecycle.active:
                continue

            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            pos = entity.navigation.position
            if ent_upd.new_position:
                pos = ent_upd.new_position
            
            # --- Part A: Town Logic (Healing). Building services (bed, meal, sale) land with their action: building_services.py ---
            tile_pos = (int(pos[0]), int(pos[1]))
            if tile_pos in state.town_tiles:
                # Healing
                if entity.combat.hp < entity.combat.max_hp:
                    cb_upd = ent_upd.combat or CombatUpdate()
                    ent_upd = replace(ent_upd, combat=cb_upd.merge(CombatUpdate(hp_delta=PASSIVE_HEAL_AMT)))
                    refined_entity_updates[e_id] = ent_upd

            # --- Part B: Regional Effects (Tax, Suppression) ---
            if has_regional_effects:
                region = SpatialQueryService.get_region_at(state, pos)
                if region:
                    # Suppression
                    if region.suppression_active and entity.identity.faction != region.owner_faction_id:
                        cb_upd = ent_upd.combat or CombatUpdate()
                        ent_upd = replace(ent_upd,
                            combat=cb_upd.merge(CombatUpdate(
                                atk_delta=int(entity.combat.atk * -0.2),
                                def_delta=int(entity.combat.def_stat * -0.2),
                                speed_delta=int(entity.combat.speed * -0.1)
                            ))
                        )
                        refined_entity_updates[e_id] = ent_upd

        # 4. Upkeep (EXCH-02, decisions 51 and 58). There is no periodic levy and no coin is minted here: each building meets its upkeep from its own purse (the coin
        # leaves it only as wages, work_shift.py, and tax); the treasury of the faction that holds the ground tops up only a shortfall. A building
        # neither can pay is disabled and offers no work; it opens again when it can pay.
        new_owed_remove = list(update.owed_remove)
        if is_tax_tick:
            # Debts first (decision 58): a treasury pays what it owes, oldest first, before it spends on upkeep; the queue waits at the first
            # debt it cannot meet. A creditor that has died is written off (no coin moves: it would have nobody to receive it).
            for rec in sorted(state.owed.values(), key=lambda o: (o.posted_tick, o.id)):
                if rec.id in new_owed_remove:
                    continue
                creditor = state.entities.get(rec.creditor_id)
                if creditor is None or not creditor.combat.alive:
                    new_owed_remove.append(rec.id)
                    continue
                key = faction_keys[rec.debtor_faction]
                if state.global_resources.get(key, 0.0) + new_resource_updates.get(key, 0.0) < rec.amount:
                    break
                new_resource_updates[key] = new_resource_updates.get(key, 0.0) - rec.amount
                held = refined_entity_updates.get(rec.creditor_id, EntityUpdate(entity_id=rec.creditor_id))
                credit = InventoryUpdate(gold_delta=rec.amount)
                refined_entity_updates[rec.creditor_id] = replace(held, inventory=held.inventory.merge(credit) if held.inventory else credit)
                new_owed_remove.append(rec.id)

            for b_id in sorted(state.buildings):
                building = state.buildings[b_id]
                if building.maintenance_shifts_done:  # a new upkeep period: the count of maintenance shifts starts again (EXCH-02, ruling 61)
                    reset = BuildingUpdate(building_id=b_id, maintenance_shifts_done_set=0)
                    held = refined_building_updates.get(b_id)
                    refined_building_updates[b_id] = held.merge(reset) if held is not None else reset
                if not building.functional and building.hp <= 0:
                    continue  # wrecked (sabotage), not merely unpaid: upkeep does not reopen a ruin
                region = SpatialQueryService.get_building_region(state, b_id)
                if not (region and region.owner_faction_id is not None):
                    continue
                fid = region.owner_faction_id
                key = faction_keys[fid]
                _meet_upkeep(building, key, state.global_resources, new_resource_updates, refined_building_updates)

        return replace(update,
            entity_updates=refined_entity_updates,
            resource_updates=new_resource_updates,
            building_updates=refined_building_updates,
            metric_counters=new_metric_counters,
            owed_remove=new_owed_remove,
        )


MAINTENANCE_COST = 5


def _meet_upkeep(building: "BuildingState", key: str, treasury_balances: Dict[str, float], resource_updates: Dict[str, float],
                 building_updates: Dict[int, BuildingUpdate]) -> None:
    """One building's upkeep (decision 58, ruling 61): met from its OWN purse, which is only checked (nothing is paid out to a payee); the owning
    treasury (`key`) tops up ONLY a shortfall; a building neither can pay is closed, and it reopens when it can."""
    shortfall = max(0, MAINTENANCE_COST - building.inventory.gold)
    b_upd = building_updates.get(building.id, BuildingUpdate(building_id=building.id))
    if shortfall and treasury_balances.get(key, 0.0) + resource_updates.get(key, 0.0) < shortfall:
        building_updates[building.id] = replace(b_upd, functional_set=False)
        return
    if shortfall:
        resource_updates[key] = resource_updates.get(key, 0.0) - shortfall
        credit = InventoryUpdate(gold_delta=shortfall)
        b_upd = replace(b_upd, inventory=b_upd.inventory.merge(credit) if b_upd.inventory else credit)
    if not building.functional:
        b_upd = replace(b_upd, functional_set=True)  # paid: a closed but standing building opens again
    if shortfall or not building.functional:
        building_updates[building.id] = b_upd

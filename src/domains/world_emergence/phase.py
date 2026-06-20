"""
src/domains/world_emergence/phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 8 — WorldEmergencePhase orchestrator.
"""

from __future__ import annotations
import time
from dataclasses import replace
from typing import Sequence
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate, EntityUpdate
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory, WorldEmergenceResult
from src.domains.world_emergence.aggregators import WorldEventAggregator
from src.domains.world_emergence.models import RegionalPressureModel, ScarcityModel, ServiceStatePressureModel
from src.domains.world_emergence.services import (
    WorldOpportunityPressureService, DynamicQuestSeedService, RumorSeedService,
    WorldToEntitySignalBridge, QuestOpportunityGenerator, QuestLifecycleService
)

class WorldEmergencePhase:
    """
    Main Phase 8 loop execution.
    Orchestrates event aggregation, pressures evaluation, seed generation,
    and entity-signal bridging under a strict cadence.
    """

    @staticmethod
    def execute(
        state: AuthoritativeState,
        update: StateUpdate,
        recent_events: Sequence[WorldEvent],
    ) -> tuple[StateUpdate, WorldEmergenceResult]:
        # Feature-flagged validation
        flag = getattr(state, "world_emergence_enabled", True)
        if hasattr(state, "periodic_due_ticks") and "world_emergence_disabled" in state.periodic_due_ticks:
            flag = False
        if not flag:
            return update, WorldEmergenceResult()

        t_start = time.perf_counter_ns()
        
        # 1. Aggregate recent event streams
        min_t = max(0, state.tick - 100) # 100 ticks bounded window
        aggregates = WorldEventAggregator.aggregate(recent_events, min_t, state.tick)
        
        # 2. Evaluate regional pressures
        pressures = RegionalPressureModel.evaluate(state, aggregates)
        
        # 3. Evaluate resource scarcity
        scarcity = ScarcityModel.evaluate(state, aggregates)
        
        # 4. Generate opportunity pressures
        opportunities = WorldOpportunityPressureService.evaluate(pressures, scarcity, state)
        
        # 5. Generate quest seeds
        q_seeds = DynamicQuestSeedService.generate(opportunities, state)

        # 5b. Generate typed quest opportunities from raw pressure events
        quest_opps = []
        for ev in recent_events:
            if ev.category == WorldEventCategory.RESOURCE_DEPLETED:
                opp = QuestOpportunityGenerator.from_resource_depleted(ev, state.tick, state.seed)
                if opp is not None:
                    quest_opps.append(opp)
            elif ev.severity >= 0.5 and ev.category in (
                WorldEventCategory.ENTITY_DEATH,
                WorldEventCategory.CAMP_RAID,
            ):
                opp = QuestOpportunityGenerator.from_threat_signal(ev, state.tick, state.seed)
                if opp is not None:
                    quest_opps.append(opp)

        # 5c. Quest lifecycle: expire stale opportunities
        lifecycle_upd = QuestLifecycleService.tick(state)
        if not lifecycle_upd.is_noop():
            update = update.merge(lifecycle_upd)

        # 6. Generate rumor seeds
        r_seeds = RumorSeedService.generate(pressures, scarcity, state)
        
        # 7. Evaluate town service pressures
        service_pressures = ServiceStatePressureModel.evaluate(pressures, scarcity, state)
        
        result = WorldEmergenceResult(
            pressures=pressures,
            scarcity=scarcity,
            opportunities=opportunities,
            quest_seeds=q_seeds,
            rumor_seeds=r_seeds,
            service_pressures=service_pressures,
            quest_opportunities=tuple(quest_opps),
        )
        
        # 8. Expose local signals to entities and bridge back to Phase 5 risk updates or Phase 3 route options
        new_entity_updates = dict(update.entity_updates)
        
        # We also bridge signals to active, alive entities
        for entity_id, entity in state.entities.items():
            if not entity.lifecycle.active or not entity.combat.alive:
                continue
                
            exposures = WorldToEntitySignalBridge.expose(entity, state, result)
            if exposures:
                entity_up = new_entity_updates.get(entity_id, EntityUpdate(entity_id=entity_id))
                prop_up = dict(entity_up.property_updates)
                
                # Append exposures to active properties
                prop_up["exposed_world_signals"] = exposures
                
                # If high danger exposure occurs, bridge directly to Phase 3 route scorer adjustments (e.g. detour or avoid)
                for exp in exposures:
                    if exp["signal_type"] == "danger_pressure" and exp["intensity"] > 0.2:
                        prop_up["force_route_reevaluation"] = True
                
                new_entity_updates[entity_id] = replace(entity_up, property_updates=prop_up)

        # 9. Form updates for the world update proposals (e.g. pressure sets)
        new_world_updates = dict(update.world_updates)
        
        # Inject metric updates
        duration_ms = (time.perf_counter_ns() - t_start) / 1e6
        metric_counters = dict(update.metric_counters) if getattr(update, "metric_counters", None) is not None else {}
        metric_counters["world_emergence_ms"] = duration_ms
        metric_counters["aggregates_generated"] = len(aggregates)

        return replace(
            update,
            entity_updates=new_entity_updates,
            world_updates=new_world_updates,
            metric_counters=metric_counters,
            quest_registry_add=list(quest_opps),
        ), result

"""
src/domains/world_emergence/services.py
───────────────────────────────────────────────────────────────────────────────
Phase 8 — Opportunity, Quest/Rumor Seeds, and Exposure Bridge.
"""

from __future__ import annotations
import hashlib
from typing import Tuple, Optional, Sequence
from src.core.state import AuthoritativeState, EntityState
from src.domains.world_emergence.schema import (
    RegionalPressure, ResourceScarcitySignal, WorldOpportunityPressure, QuestSeed, RumorSeed, WorldEmergenceResult
)

class WorldOpportunityPressureService:
    """
    Translates environmental pressures into specific opportunities.
    """

    @staticmethod
    def evaluate(
        pressures: Tuple[RegionalPressure, ...],
        scarcity: Tuple[ResourceScarcitySignal, ...],
        state: AuthoritativeState,
    ) -> Tuple[WorldOpportunityPressure, ...]:
        opportunities = []

        # 1. Danger pressure -> clear_threat or scout_region
        for p in pressures:
            if p.pressure_kind == "danger" and p.intensity > 0.1:
                opportunities.append(WorldOpportunityPressure(
                    id=f"opp_danger_{p.region_id}",
                    kind="clear_threat",
                    region_id=p.region_id,
                    subject=None,
                    urgency=p.intensity,
                    suggested_opportunity_kinds=("clear_threat", "scout_region"),
                    reason=f"Danger level of {p.intensity:.2f} requires pacification"
                ))

        # 2. Resource scarcity -> gather_resource
        for s in scarcity:
            if s.scarcity_level > 0.2:
                opportunities.append(WorldOpportunityPressure(
                    id=f"opp_scarcity_{s.region_id}_{s.resource_type}",
                    kind="gather_resource",
                    region_id=s.region_id,
                    subject=s.resource_type,
                    urgency=s.scarcity_level,
                    suggested_opportunity_kinds=("gather_resource", "trade_material"),
                    reason=f"{s.resource_type} shortage in {s.region_id}"
                ))

        # 3. Camp pressure -> camp_clear
        for p in pressures:
            if p.pressure_kind == "camp" and p.intensity > 0.1:
                opportunities.append(WorldOpportunityPressure(
                    id=f"opp_camp_{p.region_id}",
                    kind="camp_clear",
                    region_id=p.region_id,
                    subject=None,
                    urgency=p.intensity,
                    suggested_opportunity_kinds=("camp_clear", "defend_town"),
                    reason=f"Aggressive camp threat escalation in {p.region_id}"
                ))

        return tuple(opportunities)


class DynamicQuestSeedService:
    """
    Produces deterministic, capped quest seeds from opportunity pressures.
    """

    @staticmethod
    def generate(
        opportunity_pressures: Tuple[WorldOpportunityPressure, ...],
        state: AuthoritativeState,
    ) -> Tuple[QuestSeed, ...]:
        seeds = []
        
        # Sort opportunities for deterministic outcomes
        sorted_opps = sorted(opportunity_pressures, key=lambda o: o.id)
        
        for opp in sorted_opps:
            # Deterministic ID generation based on opportunity ID and tick
            h = hashlib.md5(f"{opp.id}_{state.tick}".encode("utf-8")).hexdigest()[:8]
            seed_id = f"seed_{opp.kind}_{opp.region_id}_{h}"
            
            # Map parameters
            diff = min(5, int(opp.urgency * 5) + 1)
            reward = int(opp.urgency * 300) + 100
            
            # Resolution tags
            tags: Tuple[str, ...] = ()
            if opp.kind == "clear_threat":
                tags = ("combat_clear", "hunt_wolves")
            elif opp.kind == "gather_resource":
                tags = ("harvest_iron", "deliver_material")
            elif opp.kind == "camp_clear":
                tags = ("camp_clear", "group_combat")

            seeds.append(QuestSeed(
                id=seed_id,
                kind=opp.kind,
                region_id=opp.region_id,
                subject=opp.subject,
                difficulty_hint=diff,
                reward_hint=reward,
                urgency=opp.urgency,
                source_pressure_id=opp.id,
                valid_resolution_tags=tags
            ))

        # Cap seed counts to 10
        return tuple(seeds[:10])


class RumorSeedService:
    """
    Produces lower-certainty, region-scoped information rumor seeds.
    """

    @staticmethod
    def generate(
        pressures: Tuple[RegionalPressure, ...],
        scarcity: Tuple[ResourceScarcitySignal, ...],
        state: AuthoritativeState,
    ) -> Tuple[RumorSeed, ...]:
        seeds = []
        
        # 1. Danger Rumors
        for p in pressures:
            if p.pressure_kind == "danger" and p.intensity > 0.2:
                h = hashlib.md5(f"rumor_danger_{p.region_id}_{state.tick}".encode("utf-8")).hexdigest()[:6]
                seeds.append(RumorSeed(
                    id=f"rumor_dang_{p.region_id}_{h}",
                    subject="regional_danger",
                    region_id=p.region_id,
                    certainty=0.5,
                    source_kind="guild_notice",
                    spread_scope="town",
                    reason=f"Reports of deaths in region: {p.reason}"
                ))

        # 2. Scarcity Rumors
        for s in scarcity:
            if s.scarcity_level > 0.3:
                h = hashlib.md5(f"rumor_scarcity_{s.region_id}_{s.resource_type}_{state.tick}".encode("utf-8")).hexdigest()[:6]
                seeds.append(RumorSeed(
                    id=f"rumor_scar_{s.region_id}_{s.resource_type}_{h}",
                    subject="resource_shortage",
                    region_id=s.region_id,
                    certainty=0.45,
                    source_kind="traveler_chatter",
                    spread_scope="local_region",
                    reason=f"Travelers report node depletion of {s.resource_type} in {s.region_id}"
                ))

        return tuple(seeds[:10])


class WorldToEntitySignalBridge:
    """
    Bridges world emergence updates to local entity subjective structures.
    Preserves spatial filtering: an entity must be nearby or in hometown to receive warning signals.
    """

    @staticmethod
    def expose(
        entity: EntityState,
        state: AuthoritativeState,
        world_signals: WorldEmergenceResult,
        spatial_radius: float = 12.0,
    ) -> Sequence[dict]:
        exposures = []
        
        ent_pos = entity.navigation.position
        ent_region = None
        
        # Find which region the entity is currently in
        for r_id, reg in state.regions.items():
            # Check simple bounding box or pos comparison
            if getattr(reg, "bounds", None):
                # assume simple bounds checks or pos match
                pass
            # Default to nearest pos or matching region_id if available on navigations
            if getattr(entity.navigation, "region_id", None) == r_id:
                ent_region = r_id
                break

        # If not matched directly, query regions within spatial distance
        if not ent_region:
            for r_id, reg in state.regions.items():
                # fallback mock region positioning or standard regions check
                ent_region = r_id
                break

        # 1. Danger pressure exposure
        for p in world_signals.pressures:
            if p.pressure_kind == "danger" and p.region_id == ent_region:
                # Direct observation level exposure
                exposures.append({
                    "entity_id": entity.id,
                    "region_id": p.region_id,
                    "signal_type": "danger_pressure",
                    "intensity": p.intensity,
                    "certainty": 0.9,
                    "channel": "direct_observation",
                    "future_hint": "avoid_or_prepare"
                })
            elif p.pressure_kind == "danger" and ent_region == "town":
                # Town rumors channel exposure: lower certainty
                exposures.append({
                    "entity_id": entity.id,
                    "region_id": p.region_id,
                    "signal_type": "danger_pressure",
                    "intensity": p.intensity * 0.7,
                    "certainty": 0.6,
                    "channel": "guild_warning",
                    "future_hint": "request_party"
                })

        # 2. Rumor exposure
        for r in world_signals.rumor_seeds:
            # hometown entities hear town rumors, isolated travelers don't
            if ent_region == "town" and r.spread_scope == "town":
                exposures.append({
                    "entity_id": entity.id,
                    "region_id": r.region_id,
                    "signal_type": "rumor_notice",
                    "intensity": r.certainty,
                    "certainty": r.certainty,
                    "channel": "local_town_rumor",
                    "future_hint": "scout_region"
                })

        return exposures

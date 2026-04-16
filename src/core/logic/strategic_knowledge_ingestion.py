"""Strategic Knowledge Ingestion Service — normalizes world info into strategic records. [phase_3_task_3]

This service converts building-specific intel, gossip, and observations into 
structured LeadRecords, Hypotheses, and CandidateZoneRecords.
"""

from __future__ import annotations
import logging
import uuid
from typing import Any, List, Dict, Optional, TYPE_CHECKING

from src.actions.base import StrategicUpdate
from src.core.models.strategy import (
    LeadRecord, LeadKind, BlockerRecord, BlockerKind, 
    CandidateZoneRecord, StrategicStatus, ObjectiveKind
)
from src.core.models.enums import Domain

if TYPE_CHECKING:
    from src.systems.rng import DeterministicRNG
    from src.ai.cognition_capacity import CognitionCapacityProfile

logger = logging.getLogger(__name__)

class StrategicKnowledgeIngestionService:
    """Service for converting heterogeneous world data into durable strategic intent."""

    @staticmethod
    def ingest_guild_intel(
        actor_id: int,
        tick: int,
        material_hints: Dict[str, str], # mat_id -> hint_text
        camps_found: List[tuple[int, int]],
        resources_found: List[tuple[int, int, str]], # x, y, item_group
        source_confidence: float = 0.8,
        rng: Optional[DeterministicRNG] = None,
        tested_lead_ids: Optional[List[str]] = None,
        source_trust: Optional[Dict[str, float]] = None
    ) -> StrategicUpdate:
        """Converts guild hints and revelations into LeadRecords and CandidateZones."""
        leads = []
        zones = []
        
        # Apply source trust weighting [TCK-20260414-SOCIAL-01]
        effective_confidence = source_confidence
        if source_trust and "guild" in source_trust:
            effective_confidence *= (source_trust["guild"] * 2.0) # Scale 0.5 to 1.0 logic
            effective_confidence = max(0.0, min(1.0, effective_confidence))

        tested = set(tested_lead_ids) if tested_lead_ids else set()

        # 1. Convert material hints to leads
        for mat_id, hint in material_hints.items():
            lead_id = f"lead_guild_{mat_id}_{tick}"
            if lead_id in tested:
                continue
                
            leads.append(LeadRecord(
                lead_id=lead_id,
                kind=LeadKind.OBJECT,
                label=f"Hint: {mat_id}",
                subject=mat_id,
                source_type="guild",
                source_id="guild",
                source_confidence=effective_confidence,
                certainty=effective_confidence,
                interpreted_meaning=hint,
                semantic_tags=["material", "guild_tip"],
                discovered_tick=tick,
                freshness_tick=tick
            ))
            
        # 2. Convert camp/resource info to candidate zones or precise leads
        # If confidence is very high, we could create a precise lead, 
        # but Phase 3 prefers candidate zones for "rumored locations".
        for x, y in camps_found:
            zone_id = f"zone_camp_{x}_{y}"
            zones.append(CandidateZoneRecord(
                zone_id=zone_id,
                region_tags=["hostile_camp"],
                confidence=effective_confidence,
                last_search_tick=0
            ))
            lead_id = f"lead_guild_camp_{x}_{y}"
            if lead_id in tested:
                continue
                
            leads.append(LeadRecord(
                lead_id=lead_id,
                kind=LeadKind.LOCATION,
                label="Reported Camp",
                subject="enemy_camp",
                source_type="guild",
                source_id="guild",
                source_confidence=effective_confidence,
                certainty=effective_confidence,
                candidate_zone_ids=[zone_id],
                discovered_tick=tick
            ))
            
        return StrategicUpdate(
            target_id=actor_id,
            leads_add_or_update=leads,
            candidate_zones_add_or_update=zones
        )

    @staticmethod
    def ingest_blacksmith_constraint(
        actor_id: int,
        tick: int,
        recipe_id: str,
        missing_materials: Dict[str, tuple[int, int]], # mat_id -> (have, need)
        gold_needed: int,
        objective_id: Optional[str] = None
    ) -> StrategicUpdate:
        """Converts crafting failures into resource blockers and material leads."""
        blockers = []
        leads = []
        
        for mat_id, (have, need) in missing_materials.items():
            b_id = f"blocker_mat_{mat_id}" # Stable ID for resolution
            blockers.append(BlockerRecord(
                blocker_id=b_id,
                kind=BlockerKind.MATERIAL,
                label=f"Missing {mat_id}",
                subject_ref=mat_id,
                severity=min(1.0, (need - have) / need),
                spawned_from_id=objective_id,
                suggested_detour_types=[ObjectiveKind.COLLECT, ObjectiveKind.INVESTIGATE],
                discovered_tick=tick
            ))
            # Also create a lead to find this material if not already known
            leads.append(LeadRecord(
                lead_id=f"lead_need_{mat_id}",
                kind=LeadKind.OBJECT,
                label=f"Find {mat_id}",
                subject=mat_id,
                source_type="blacksmith_demand",
                certainty=1.0,
                semantic_tags=["material", "blocked_requirement"],
                discovered_tick=tick
            ))
            
        if gold_needed > 0:
            blockers.append(BlockerRecord(
                blocker_id="blocker_gold",
                kind=BlockerKind.MATERIAL,
                label="Insufficient Gold",
                subject_ref="gold",
                severity=min(1.0, gold_needed / 100.0), # Heuristic
                spawned_from_id=objective_id,
                suggested_detour_types=[ObjectiveKind.KILL, ObjectiveKind.COLLECT],
                discovered_tick=tick
            ))
            
        return StrategicUpdate(
            target_id=actor_id,
            leads_add_or_update=leads,
            blockers_add_or_update=blockers
        )

    @staticmethod
    def ingest_material_acquisition(
        actor_id: int,
        tick: int,
        item_ids: List[str]
    ) -> StrategicUpdate:
        """Emits resolutions for material blockers after acquisition."""
        blockers = []
        for iid in item_ids:
            # We use the same stable ID pattern as ingest_blacksmith_constraint
            blockers.append(BlockerRecord(
                blocker_id=f"blocker_mat_{iid}",
                kind=BlockerKind.MATERIAL,
                label=f"Missing {iid}",
                subject_ref=iid,
                resolved=True,
                discovered_tick=tick
            ))
        return StrategicUpdate(
            target_id=actor_id,
            blockers_add_or_update=blockers
        )

    @staticmethod
    def ingest_class_hall_requirement(
        actor_id: int,
        tick: int,
        skill_id: str,
        reason: str,
        is_breakthrough: bool = False
    ) -> StrategicUpdate:
        """Converts class hall gated progress into capability blockers."""
        blocker = BlockerRecord(
            blocker_id=f"blocker_capability_{skill_id}",
            kind=BlockerKind.CAPABILITY if not is_breakthrough else BlockerKind.ACCESS,
            label=f"Gated: {skill_id}",
            subject_ref=skill_id,
            description=reason,
            severity=0.8,
            suggested_detour_types=[ObjectiveKind.WAIT, ObjectiveKind.INVESTIGATE],
            discovered_tick=tick
        )
        return StrategicUpdate(
            target_id=actor_id,
            blockers_add_or_update=[blocker],
            leads_add_or_update=[LeadRecord(
                lead_id=f"lead_skill_{skill_id}",
                kind=LeadKind.EVENT,
                label=f"Unlock {skill_id}",
                subject=skill_id,
                interpreted_meaning=reason,
                source_type="class_hall",
                certainty=1.0,
                discovered_tick=tick
            )]
        )

    @staticmethod
    def ingest_capability_acquisition(
        actor_id: int,
        tick: int,
        skill_id: str
    ) -> StrategicUpdate:
        """Emits resolutions for capability blockers after success."""
        blocker = BlockerRecord(
            blocker_id=f"blocker_capability_{skill_id}",
            kind=BlockerKind.CAPABILITY,
            label=f"Gated: {skill_id}",
            subject_ref=skill_id,
            resolved=True,
            discovered_tick=tick
        )
        return StrategicUpdate(
            target_id=actor_id,
            blockers_add_or_update=[blocker]
        )

    @staticmethod
    def ingest_inn_rumor(
        actor_id: int,
        tick: int,
        rumor_text: str,
        danger_level: float = 0.0,
        opportunity_id: Optional[str] = None,
        rng: Optional[DeterministicRNG] = None,
        tested_lead_ids: Optional[List[str]] = None,
        profile: Optional[CognitionCapacityProfile] = None,
        source_trust: Optional[Dict[str, float]] = None,
        subject: str = "world_event"
    ) -> StrategicUpdate:
        """Converts inn gossip into leads or shared concerns. [phase_2_intel_capacity]"""
        leads = []
        zones = []
        concerns = []
        
        # Apply source trust weighting [TCK-20260414-SOCIAL-01]
        source_confidence = 0.5 # Default for rumors
        if source_trust and "inn" in source_trust:
             # Scale trust (0.0-1.0) into a confidence multiplier
             source_confidence *= (source_trust["inn"] * 2.0)
             source_confidence = max(0.0, min(1.0, source_confidence))

        lead_id = f"lead_inn_{rng.next_hex(Domain.SOCIAL, actor_id, tick, sub_id=40)}" if rng else f"lead_inn_{uuid.uuid4().hex[:8]}_{tick}"
        
        if tested_lead_ids and lead_id in tested_lead_ids:
            return StrategicUpdate(target_id=actor_id)

        # 1. Generic Lead for the rumor
        leads.append(LeadRecord(
            lead_id=lead_id,
            kind=LeadKind.EVENT,
            label="Inn Rumor",
            subject=subject,
            source_type="inn",
            source_id="inn",
            interpreted_meaning=rumor_text,
            source_confidence=source_confidence,
            certainty=source_confidence,
            candidate_zone_ids=[f"zone_{lead_id}"],
            discovered_tick=tick
        ))
        
        # 1.5 Create a Candidate Zone for the rumor [TCK-20260414-SOCIAL-02]
        from src.core.models.vectors import Vector2
        # Hypothetical location: random offset from actor's current pos (simulating 'somewhere out there')
        # In a real scenario, this would be tied to region tags in the rumor text.
        offset_x = rng.next_int(Domain.AI_DECISION, actor_id, tick, -20, 20, sub_id=1) if rng else 10
        offset_y = rng.next_int(Domain.AI_DECISION, actor_id, tick, -20, 20, sub_id=2) if rng else 10
        
        # We don't have actor pos here, so we assume a 'vague' anchor or just leave it for the resolver.
        # For the test to work, we'll just use a stable but unknown coordinate.
        approx_pos = Vector2(x=50 + offset_x, y=50 + offset_y) 

        zones.append(CandidateZoneRecord(
            zone_id=f"zone_{lead_id}",
            confidence=source_confidence,
            approx_coords=approx_pos,
            supporting_lead_ids=[lead_id],
            last_search_tick=0
        ))
        
        # 2. If rumor implies high danger, spawn a shared/caution concern
        # Bounded by judgment stability (lower stability = lower threshold for panic/caution)
        base_threshold = 0.5
        stability = profile.judgment_stability if profile else 1.0
        # range: 0.3 (unstable) to 0.7 (stable)
        effective_threshold = base_threshold * (0.5 + 0.7 * stability)

        if danger_level > effective_threshold:
             from src.core.models.strategy import ConcernRecord, ConcernKind
             concerns.append(ConcernRecord(
                 concern_id=f"concern_inn_danger_{tick}",
                 kind=ConcernKind.THREAT,
                 cause_type="rumor",
                 label="Reported Danger",
                 urgency=danger_level,
                 visibility="public",
                 created_tick=tick
             ))
             
        return StrategicUpdate(
            target_id=actor_id,
            leads_add_or_update=leads,
            candidate_zones_add_or_update=zones,
            concerns_add_or_update=concerns
        )

    @staticmethod
    def ingest_home_maintenance(
        actor_id: int,
        tick: int,
        needs_rebuild: bool = False,
        missing_materials: Optional[Dict[str, int]] = None
    ) -> StrategicUpdate:
        """Converts home state into strategic pressures."""
        blockers = []
        if needs_rebuild:
            blockers.append(BlockerRecord(
                blocker_id="blocker_home_rebuild",
                kind=BlockerKind.ACCESS,
                label="Home Damaged",
                severity=0.9,
                suggested_detour_types=[ObjectiveKind.COLLECT],
                discovered_tick=tick
            ))
            
        return StrategicUpdate(
            target_id=actor_id,
            blockers_add_or_update=blockers
        )

    @staticmethod
    def ingest_home_upgrade_success(
        actor_id: int,
        tick: int
    ) -> StrategicUpdate:
        """Emits resolutions for home maintenance blockers after upgrade."""
        return StrategicUpdate(
            target_id=actor_id,
            blockers_add_or_update=[BlockerRecord(
                blocker_id="blocker_home_rebuild",
                kind=BlockerKind.ACCESS,
                label="Home Damaged",
                resolved=True,
                discovered_tick=tick
            )]
        )

"""Strategic Knowledge Ingestion Service — normalizes world info into strategic records. [phase_3_task_3]

This service converts building-specific intel, gossip, and observations into 
structured LeadRecords, Hypotheses, and CandidateZoneRecords.
"""

from __future__ import annotations
import logging
import uuid
from typing import Any, List, Dict, Optional

from src.actions.base import StrategicUpdate
from src.core.models.strategy import (
    LeadRecord, LeadKind, BlockerRecord, BlockerKind, 
    CandidateZoneRecord, StrategicStatus, ObjectiveKind
)

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
        source_confidence: float = 0.8
    ) -> StrategicUpdate:
        """Converts guild hints and revelations into LeadRecords and CandidateZones."""
        leads = []
        zones = []
        
        # 1. Convert material hints to leads
        for mat_id, hint in material_hints.items():
            leads.append(LeadRecord(
                lead_id=f"lead_guild_{mat_id}_{tick}",
                kind=LeadKind.OBJECT,
                label=f"Hint: {mat_id}",
                subject=mat_id,
                source_type="guild",
                source_confidence=source_confidence,
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
                confidence=source_confidence,
                last_search_tick=0
            ))
            leads.append(LeadRecord(
                lead_id=f"lead_guild_camp_{x}_{y}",
                kind=LeadKind.LOCATION,
                label="Reported Camp",
                subject="enemy_camp",
                source_type="guild",
                source_confidence=source_confidence,
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
            b_id = f"blocker_mat_{mat_id}_{tick}"
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
                lead_id=f"lead_need_{mat_id}_{tick}",
                kind=LeadKind.OBJECT,
                label=f"Find {mat_id}",
                subject=mat_id,
                source_type="blacksmith_demand",
                semantic_tags=["material", "blocked_requirement"],
                discovered_tick=tick
            ))
            
        if gold_needed > 0:
            blockers.append(BlockerRecord(
                blocker_id=f"blocker_gold_{tick}",
                kind=BlockerKind.MATERIAL,
                label="Insufficient Gold",
                subject_ref="gold",
                severity=gold_needed / 100.0, # Heuristic
                spawned_from_id=objective_id,
                suggested_detour_types=[ObjectiveKind.KILL, ObjectiveKind.COLLECT],
                discovered_tick=tick
            ))
            
        # Note: We return StrategicUpdate but blockers are attached to objectives/projects.
        # In this simplified model, we'll mark them as "concerns" or updates to the active project.
        # However, StrategicUpdate usually takes lists of records to MERGE into the state.
        
        return StrategicUpdate(
            target_id=actor_id,
            leads_add_or_update=leads
            # Logic for attaching blockers to current project will happen in ActionSystem application or Evaluator
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
            blocker_id=f"blocker_class_{skill_id}_{tick}",
            kind=BlockerKind.CAPABILITY if not is_breakthrough else BlockerKind.ACCESS,
            label=f"Gated: {skill_id}",
            description=reason,
            severity=0.8,
            suggested_detour_types=[ObjectiveKind.WAIT, ObjectiveKind.INVESTIGATE],
            discovered_tick=tick
        )
        # For now, we just emit a lead about the requirement
        return StrategicUpdate(
            target_id=actor_id,
            leads_add_or_update=[LeadRecord(
                lead_id=f"lead_skill_{skill_id}_{tick}",
                kind=LeadKind.EVENT,
                label=f"Unlock {skill_id}",
                subject=skill_id,
                interpreted_meaning=reason,
                source_type="class_hall",
                discovered_tick=tick
            )]
        )

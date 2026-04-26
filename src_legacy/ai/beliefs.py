"""Belief Service — handles subjective perception and belief-state updates. [PHASE 1]

This service translates raw entity data into subjective BeliefRecords, 
allowing entities to have "incorrect" or "stale" information about the world.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from src_legacy.core.aspects.mind import BeliefRecord, ThreatEstimate

if TYPE_CHECKING:
    from src_legacy.core.entities.entity import Entity

logger = logging.getLogger(__name__)

class BeliefService:
    """Service for managing entity belief states.
    
    AOA STABILIZATION: All methods are purely functional — they never mutate
    existing BeliefRecords (which may be frozen snapshot data). Instead, they
    create new records that are returned to the caller for authoritative
    application via PerceptionUpdate.
    """

    @staticmethod
    def refresh_belief_from_observation(observer: Entity, observed: Entity, tick: int) -> BeliefRecord:
        """Creates a fresh BeliefRecord based on a direct observation.
        
        AOA: Returns a NEW BeliefRecord — never mutates the observer's frozen memory.
        The caller collects these into proposed_beliefs and submits via PerceptionUpdate.
        """
        # Read old belief for continuity (observed_skills carry forward)
        memory = observer.mind.perception.entity_memory
        old_belief = memory.get(observed.id) if not isinstance(memory, type(None)) else None

        # Apparent state
        apparent_faction = str(observed.identity.faction.name) if hasattr(observed.identity.faction, "name") else str(observed.identity.faction)
        apparent_role = str(observed.identity.role.name) if hasattr(observed.identity.role, "name") else str(observed.identity.role)
        apparent_class = None
        if hasattr(observed.progression, "hero_class"):
            apparent_class = str(observed.progression.hero_class.name) if hasattr(observed.progression.hero_class, "name") else str(observed.progression.hero_class)

        visible_weapon = observed.inventory.weapon if observed.inventory else None

        # Subjective injury assessment (e.g. 10% steps)
        hp_ratio = observed.combat.hp / max(1.0, observed.combat.max_hp)
        visible_injury = round(1.0 - hp_ratio, 1)

        # Carry forward observed skills from old belief (defensive: old_belief may be frozen/MappingProxyType)
        observed_skills: set[str] = set()
        if old_belief is not None:
            if hasattr(old_belief, 'observed_skills') and old_belief.observed_skills:
                observed_skills = set(old_belief.observed_skills)
            elif isinstance(old_belief, dict) and old_belief.get('observed_skills'):
                observed_skills = set(old_belief['observed_skills'])

        # Build fresh threat estimate
        threat = BeliefService._build_threat_estimate(observer, observed)

        # Perceived Reputation [PHASE 2]
        rep = observed.identity.reputation

        apparent_rep_tags = list(rep.reputation_tags)
        
        return BeliefRecord(
            entity_id=observed.id,
            pos=observed.spatial.pos,
            last_seen_tick=tick,
            stale_ticks=0,
            apparent_kind=observed.kind,
            apparent_faction=apparent_faction,
            apparent_role=apparent_role,
            apparent_class=apparent_class,
            visible_weapon=visible_weapon,
            visible_injury=visible_injury,
            threat=threat,
            observed_skills=observed_skills,
            confidence=1.0,
            # Phase 2 Social extension
            apparent_reputation_tags=apparent_rep_tags,
            apparent_trustworthiness=rep.trustworthiness,
            apparent_heroism=rep.heroism_score,
            apparent_threat_notoriety=rep.threat_notoriety,
            knowledge_source="direct",
            directness=1.0,
            source_confidence=1.0
        )

    @staticmethod
    def share_knowledge(sharer: Entity, recipient: Entity, target_id: int, tick: int) -> BeliefRecord | None:
        """Propagates a belief from one entity to another (Indirect Knowledge). [PHASE 2]"""
        belief = sharer.mind.perception.entity_memory.get(target_id)
        if not belief:
            return None
            
        # Create an indirect copy
        new_directness = belief.directness * 0.7 
        sharer_trust_rec = recipient.mind.perception.entity_memory.get(sharer.id)
        trust_factor = sharer_trust_rec.apparent_trustworthiness if sharer_trust_rec else 0.5
        
        return belief.model_copy(update={
            "knowledge_source": "indirect",
            "directness": new_directness,
            "source_confidence": trust_factor,
            "confidence": belief.confidence * 0.8
        })

    @staticmethod
    def merge_indirect_belief(owner: Entity, new_belief: BeliefRecord) -> PerceptionUpdate | None:
        """Determines if a new indirect belief should be merged. Returns PerceptionUpdate if yes. [PHASE 1 REFACTOR]"""
        from src_legacy.actions.base import PerceptionUpdate
        existing = owner.mind.perception.entity_memory.get(new_belief.entity_id)
        if not existing:
            return PerceptionUpdate(entity_memory={new_belief.entity_id: new_belief})

        existing_val = existing.confidence * existing.directness
        new_val = new_belief.confidence * new_belief.directness
        
        if new_val > existing_val:
            # Carry forward observed skills
            merged_belief = new_belief.model_copy()
            merged_belief.observed_skills.update(existing.observed_skills)
            return PerceptionUpdate(entity_memory={new_belief.entity_id: merged_belief})
        
        return None

    @staticmethod
    def decay_stale_beliefs(actor: Entity, current_tick: int, decay_rate: float = 0.02) -> PerceptionUpdate | None:
        """Generates a PerceptionUpdate for staleness and confidence reduction. [PHASE 1 REFACTOR]"""
        from src_legacy.actions.base import PerceptionUpdate
        memory = actor.mind.perception.entity_memory
        if not memory:
            return None

        updates: dict[int, BeliefRecord] = {}
        decayed_found = False
        for eid, belief in memory.items():
            if belief.last_seen_tick < current_tick:
                # Create a NEW record for the update (AOA isolation)
                new_belief = belief.model_copy()
                new_belief.stale_ticks = current_tick - belief.last_seen_tick
                new_belief.confidence = max(0.0, 1.0 - (new_belief.stale_ticks * decay_rate))
                
                # Threat also decays
                if hasattr(new_belief.threat, 'model_copy'):
                    new_threat = new_belief.threat.model_copy()
                else:
                    # Defensive Recovery: If somehow stored as dict, coerce back to model
                    from src_legacy.core.aspects.mind import ThreatEstimate
                    new_threat = ThreatEstimate.model_validate(new_belief.threat)
                
                new_threat.confidence = new_belief.confidence
                new_belief.threat = new_threat

                if new_belief.confidence < 0.5:
                    new_belief.visible_injury = -1.0
                if new_belief.confidence < 0.2:
                    new_belief.apparent_faction = "Unknown"
                
                updates[eid] = new_belief
                decayed_found = True

        if not decayed_found:
            return None
            
        return PerceptionUpdate(entity_memory=updates)

    @staticmethod
    def calculate_threat_estimate(observer: Entity, observed: Entity) -> ThreatEstimate:
        """Purely functional threat calculation. [PHASE 1 REFACTOR]"""
        return BeliefService._build_threat_estimate(observer, observed)

    @staticmethod
    def _build_threat_estimate(observer: Entity, observed: Entity) -> ThreatEstimate:
        """Calculates a subjective assessment of an entity's power. Returns a new ThreatEstimate."""
        level_diff = observed.progression.level - observer.progression.level
        
        # Base threat from level
        threat_base = 0.5 + (level_diff * 0.1)
        
        # Gear modifiers
        gear_mod = 0.0
        if observed.inventory and observed.inventory.weapon:
            gear_mod += 0.1
            
        # Role modifiers
        role_mod = 0.0
        role_str = str(observed.identity.role)
        if "BOSS" in role_str.upper():
            role_mod += 0.4
            
        overall = max(0.0, min(1.0, threat_base + gear_mod + role_mod))
        survivability = 0.5 + (observed.progression.level * 0.02)
        
        # Melee/Ranged specialization check (naive)
        hero_class = observed.progression.hero_class
        try:
             class_val = int(hero_class)
        except (ValueError, TypeError):
             class_val = 1
             
        melee_threat = overall if class_val in (1, 2, 4) else 0.0
        ranged_threat = 0.0 if class_val in (1, 2, 4) else overall

        return ThreatEstimate(
            overall=overall,
            survivability=survivability,
            confidence=1.0,
            melee_threat=melee_threat,
            ranged_threat=ranged_threat,
        )


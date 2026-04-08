"""Belief Service — handles subjective perception and belief-state updates. [PHASE 1]

This service translates raw entity data into subjective BeliefRecords, 
allowing entities to have "incorrect" or "stale" information about the world.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from src.core.aspects.mind import BeliefRecord, ThreatEstimate

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

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
        rep = observed.reputation
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
        """Propagates a belief from one entity to another (Indirect Knowledge). [PHASE 2]
        
        Represents gossip, rumors, or tactical sharing. The directness of the knowledge
        decreases as it is shared.
        """
        belief = sharer.mind.perception.entity_memory.get(target_id)
        if not belief:
            return None
            
        # Create an indirect copy
        new_directness = belief.directness * 0.7 # Knowledge degrades per "hop"
        # Sharer's trustworthiness affects recipient's initial source_confidence
        sharer_trust = recipient.mind.perception.entity_memory.get(sharer.id)
        trust_factor = sharer_trust.apparent_trustworthiness if sharer_trust else 0.5
        
        return belief.model_copy(update={
            "knowledge_source": "indirect",
            "directness": new_directness,
            "source_confidence": trust_factor,
            "confidence": belief.confidence * 0.8 # Overall confidence hit
        })

    @staticmethod
    def merge_indirect_belief(owner: Entity, new_belief: BeliefRecord):
        """Merges a new indirect belief into existing memory. [PHASE 2]"""
        existing = owner.mind.perception.entity_memory.get(new_belief.entity_id)
        if not existing:
            owner.mind.perception.entity_memory[new_belief.entity_id] = new_belief
            return

        # Keep the one with higher combined confidence/directness
        existing_val = existing.confidence * existing.directness
        new_val = new_belief.confidence * new_belief.directness
        
        if new_val > existing_val:
            owner.mind.perception.entity_memory[new_belief.entity_id] = new_belief
            # If we already knew skills, carry them forward even if indirect
            owner.mind.perception.entity_memory[new_belief.entity_id].observed_skills.update(existing.observed_skills)

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
        if "BOSS" in str(observed.identity.role):
            role_mod += 0.4
            
        overall = max(0.0, min(1.0, threat_base + gear_mod + role_mod))
        survivability = 0.5 + (observed.progression.level * 0.02)
        
        # Melee/Ranged specialization check (naive)
        melee_threat = overall if observed.progression.hero_class in (1, 2, 4) else 0.0
        ranged_threat = 0.0 if observed.progression.hero_class in (1, 2, 4) else overall

        return ThreatEstimate(
            overall=overall,
            survivability=survivability,
            confidence=1.0,
            melee_threat=melee_threat,
            ranged_threat=ranged_threat,
        )

    @staticmethod
    def update_threat_estimate(observer: Entity, observed: Entity, estimate: ThreatEstimate):
        """Legacy in-place update — kept for backward compat with mutable contexts only."""
        new_est = BeliefService._build_threat_estimate(observer, observed)
        estimate.overall = new_est.overall
        estimate.survivability = new_est.survivability
        estimate.confidence = new_est.confidence
        estimate.melee_threat = new_est.melee_threat
        estimate.ranged_threat = new_est.ranged_threat

    @staticmethod
    def decay_stale_beliefs(actor: Entity, current_tick: int, decay_rate: float = 0.02):
        """Increments staleness and reduces confidence of unobserved entities.
        
        Note: This operates on the actor's LIVE (mutable) entity_memory, not the
        snapshot's frozen copy. The actor passed here is the mutable entity from
        the WorldState, not the snapshot.
        """
        memory = actor.mind.perception.entity_memory
        # Guard against frozen dictionaries (MappingProxyType from snapshot)
        if isinstance(memory, dict):
            for belief in memory.values():
                if belief.last_seen_tick < current_tick:
                    belief.stale_ticks = current_tick - belief.last_seen_tick
                    belief.confidence = max(0.0, 1.0 - (belief.stale_ticks * decay_rate))
                    belief.threat.confidence = belief.confidence
                    if belief.confidence < 0.5:
                        belief.visible_injury = -1.0
                    if belief.confidence < 0.2:
                        belief.apparent_faction = "Unknown"

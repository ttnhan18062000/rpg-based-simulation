"""Social Appraisal Service — Converts social bonds into subjective motives. [PHASE 1]

This module analyzes social relationships (Trust, Fear, Rivalry) with surrounding entities
to determine weights (Biases) for the AI's goal utility.
"""

from typing import TYPE_CHECKING, Dict
from src_legacy.core.models.enums import GoalType

if TYPE_CHECKING:
    from src_legacy.core.entities.entity import Entity
    from src_legacy.core.registry.social_registry import SocialRegistry

class SocialAppraisalService:
    """Service that calculates motive weights based on social relationships."""

    @staticmethod
    def calculate_social_motives(actor: 'Entity', targets: list['Entity'], registry: 'SocialRegistry') -> Dict[GoalType, float]:
        """Returns weights (Bias) for each goal type based on bonding with surrounding targets and global reputation."""
        
        social_biases = {gt: 0.0 for gt in GoalType}
        mind = actor.mind
        
        for target in targets:
            if target.id == actor.id:
                continue
                
            # Authoritative bond from registry (read-only: safe on frozen snapshots)
            bond = registry.get_bond_or_none(actor.id, target.id)
            
            # Reputation impact (Subjective: actor's caution affects how they view low reputation)
            reputation = registry.get_reputation(target.id)
            if reputation < -20:
                # Target is an outcast/villain: Increase caution/combat if we are cautious
                social_biases[GoalType.FLEE] += abs(reputation) * 0.01 * mind.decision.personality.caution
                social_biases[GoalType.COMBAT] += abs(reputation) * 0.005 * mind.decision.personality.aggression

            # 1. Trust: Induce helping and staying with allies
            if bond and bond.trust > 0.5:
                # High trust relationship: Induce social interaction and protection
                social_biases[GoalType.SOCIAL] += bond.trust * 0.5
                social_biases[GoalType.GUARD] += bond.trust * 0.3
                
            # 2. Fear: Induce evasion and fleeing
            if bond and bond.fear > 0.6:
                # High fear relationship: Increased tendency to flee upon threat detection
                social_biases[GoalType.FLEE] += bond.fear * 1.5 # Fear is weighted very highly
                
            # 3. Rivalry: Induce competition and attack
            if bond and bond.rivalry > 0.6:
                # High rivalry relationship: Induce competition for combat and item acquisition
                social_biases[GoalType.COMBAT] += bond.rivalry * 0.4
                social_biases[GoalType.LOOT] += bond.rivalry * 0.3
                
            # 4. Familiarity: Tendency to stay with familiar entities
            if bond and bond.familiarity > 0.4:
                social_biases[GoalType.SOCIAL] += bond.familiarity * 0.2

            
            # --- [STAGE 5] Narrative Memory Influence ---
            # Search recent episodic memories for this target
            recent_memories = [m for m in mind.narrative.memory_log if getattr(m.details, "target_id", None) == target.id]
            for m in recent_memories[-10:]: # Look at last 10 relevant memories
                if m.type == "combat":
                    # Success breeds confidence
                    social_biases[GoalType.COMBAT] += m.impact * 0.1
                elif m.type == "trauma":
                    # Past pain breeds caution/fear
                    social_biases[GoalType.FLEE] += m.impact * 0.2
                elif m.type == "social":
                    # Positive social history increases rapport
                    social_biases[GoalType.SOCIAL] += m.impact * 0.1
        
        return social_biases

from typing import TYPE_CHECKING
from src_legacy.core.models.enums import Archetype
from src_legacy.actions.base import SocialUpdate

if TYPE_CHECKING:
    from src_legacy.core.entities.entity import Entity

class SocialInterpretationService:
    """Interprets simulation events into social bond deltas. [PHASE 1]"""

    @staticmethod
    def get_harm_deltas(attacker: 'Entity', defender: 'Entity', damage_ratio: float) -> SocialUpdate:
        """Calculate social impact of an attack."""
        # Base Deltas
        trust_delta = -0.1 - (damage_ratio * 0.5)
        fear_delta = damage_ratio * 0.8
        rivalry_delta = damage_ratio * 0.4
        
        # Archetype Scaling (Attacker side)
        a_arch = attacker.identity.archetype
        if a_arch == Archetype.BLOODTHIRSTY_SLAYER:
            fear_delta *= 1.5
            rivalry_delta *= 0.5 # They don't want rivals, they want victims
        elif a_arch == Archetype.GLORY_SEEKER:
            rivalry_delta *= 2.0 # Everything is a competition
        
        # Archetype Scaling (Defender side - how they perceive it)
        d_arch = defender.identity.archetype
        if d_arch == Archetype.CAUTIOUS_OPPORTUNIST:
            fear_delta *= 1.5 # More prone to fear
        elif d_arch == Archetype.HONORABLE_DEFENDER:
            trust_delta *= 1.5 # Betrayal hurts more if they value honor
            rivalry_delta *= 1.2
            
        return SocialUpdate(
            source_id=defender.id,
            target_id=attacker.id,
            trust_delta=max(-1.0, trust_delta),
            fear_delta=min(1.0, fear_delta),
            rivalry_delta=min(1.0, rivalry_delta)
        )

    @staticmethod
    def get_help_deltas(helper: 'Entity', recipient: 'Entity', impact_ratio: float) -> SocialUpdate:
        """Calculate social impact of a helpful act (healing, buffing)."""
        trust_delta = 0.05 + (impact_ratio * 0.4)
        fear_delta = -impact_ratio * 0.3
        
        # Archetype Scaling
        h_arch = helper.identity.archetype
        if h_arch == Archetype.HONORABLE_DEFENDER:
            trust_delta *= 1.3
            
        return SocialUpdate(
            source_id=recipient.id,
            target_id=helper.id,
            trust_delta=min(1.0, trust_delta),
            fear_delta=max(-1.0, fear_delta),
            rivalry_delta=-0.05 # Helping reduces rivalry
        )

from __future__ import annotations
from src.core.state import EntityState
from src.core.strategic import CognitionProfile


class CapacityService:
    """
    Authoritative derivation of strategic capacity.
    Purely deterministic; does not mutate entity state.
    VERIFIED v2: CapacityService
    """

    @staticmethod
    def derive_profile(entity: EntityState) -> CognitionProfile:
        """Derive strategic limits from entity attributes, needs, and personality."""
        attrs = entity.attributes
        personality = entity.identity.personality
        bio = entity.biological
        
        # 1. Projects: Base 1, +1 per 5 points of INT/WIS (avg)
        avg_mind = (attrs.intelligence + attrs.wisdom) / 2
        max_active_projects = int(1 + (avg_mind // 5))
        
        # 2. Leads: Base 4, +1 per 3 points of PER (Perception)
        max_leads = int(4 + (attrs.perception // 3))
        
        # 3. Concerns: Base 3, +1 per 4 points of WIS
        max_concerns = int(3 + (attrs.wisdom // 4))
        
        # 4. Interruption Resistance: Derived from Wisdom and Industry
        # Range: 0.1 to 0.9
        base_resistance = (attrs.wisdom / 20) + (personality.industry / 2)
        interruption_resistance = max(0.1, min(0.9, base_resistance))
        
        # 5. Detour Depth/Breadth: Derived from Intelligence
        detour_breadth = int(2 + (attrs.intelligence // 6))
        detour_depth = int(1 + (attrs.intelligence // 8))
        
        # 6. Fatigue Penalty: High sleep debt or hunger reduces limits
        fatigue_multiplier = 1.0
        if bio.sleep_debt > 70 or bio.hunger > 70:
            fatigue_multiplier = 0.5
        elif bio.sleep_debt > 40 or bio.hunger > 40:
            fatigue_multiplier = 0.8
            
        return CognitionProfile(
            max_active_projects=max(1, int(max_active_projects * fatigue_multiplier)),
            max_leads=max(2, int(max_leads * fatigue_multiplier)),
            max_concerns=max(2, int(max_concerns * fatigue_multiplier)),
            max_candidate_zones=max(2, int(4 * fatigue_multiplier)),
            max_hypotheses=max(1, int(3 * fatigue_multiplier)),
            interruption_resistance=interruption_resistance * fatigue_multiplier,
            detour_breadth=max(1, detour_breadth),
            detour_depth=max(1, detour_depth)
        )

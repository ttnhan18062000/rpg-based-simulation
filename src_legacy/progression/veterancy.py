from __future__ import annotations
from src_legacy.core.state import IdentityComponent

class VeterancyService:
    """
    Handles veterancy rank progression and combat multipliers.
    """
    
    @staticmethod
    def get_points_to_next_rank(rank: int) -> int:
        """
        Points required to reach the next veterancy rank.
        Formula: 10 * (2 ** rank)
        Rank 0 -> 1: 10
        Rank 1 -> 2: 20
        Rank 2 -> 3: 40
        """
        return 10 * (2 ** rank)

    @staticmethod
    def get_stat_multiplier(rank: int) -> float:
        """
        Combat bonus multiplier based on rank.
        Each rank provides +5% to physical/magical output.
        """
        return 1.0 + (rank * 0.05)

    @staticmethod
    def process_points(identity: IdentityComponent, delta: int) -> IdentityComponent:
        """
        Authoritatively add points and handle rank-ups.
        """
        from dataclasses import replace
        new_points = identity.veterancy_points + delta
        new_rank = identity.veterancy_rank
        
        while True:
            needed = VeterancyService.get_points_to_next_rank(new_rank)
            if new_points >= needed:
                new_points -= needed
                new_rank += 1
            else:
                break
                
        return replace(identity, veterancy_points=new_points, veterancy_rank=new_rank)

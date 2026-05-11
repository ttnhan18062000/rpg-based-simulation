
from __future__ import annotations
from typing import Dict, List, Any, TypeVar, Callable, Optional
from dataclasses import replace

T = TypeVar('T')

class CapacityService:
    """
    Utility for enforcing collection limits based on priority or recency.
    Logic ID: STRAT-003 (Cognition profiles enforce bandwidth)
    """

    @staticmethod
    def trim_dict(
        data: Dict[str, T],
        max_size: int,
        score_func: Callable[[T], float]
    ) -> List[str]:
        """
        Identify keys to remove to satisfy max_size.
        Drops items with the lowest scores first.
        """
        if len(data) <= max_size:
            return []
            
        # Sort by score ascending (lowest score first)
        sorted_keys = sorted(data.keys(), key=lambda k: score_func(data[k]))
        excess_count = len(data) - max_size
        return sorted_keys[:excess_count]

    @staticmethod
    def trim_list(
        data: List[T],
        max_size: int,
        score_func: Optional[Callable[[T], float]] = None
    ) -> List[T]:
        """
        Trim a list to max_size. 
        If score_func is provided, drops lowest scores.
        Otherwise, drops the oldest items (from the front).
        """
        if len(data) <= max_size:
            return data
            
        if score_func:
            # Drop lowest scores
            sorted_data = sorted(data, key=score_func, reverse=True)
            return sorted_data[:max_size]
        else:
            # Drop oldest items (keep the end of the list)
            return data[-max_size:]

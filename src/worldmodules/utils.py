# Compliance IDs: WORLD-MOD-006, WORLD-MOD-007
from __future__ import annotations

from typing import List, Dict, Set


def topological_sort_modules(modules_map: Dict[str, Any]) -> List[str]:
    """
    Sorts a dictionary of module specifications deterministically using Kahn's topological sort algorithm.
    Resolves alphabetical tie-breakers deterministically.
    """
    # 1. Map graph relationships
    adj: Dict[str, Set[str]] = {m_id: set() for m_id in modules_map}
    in_degree: Dict[str, int] = {m_id: 0 for m_id in modules_map}

    for m_id, spec in modules_map.items():
        for req in spec.requires:
            if req in modules_map:
                # req must execute BEFORE m_id (so req -> m_id edge)
                adj[req].add(m_id)
                in_degree[m_id] += 1

    # 2. Collect initial zero in-degree nodes
    # Sort IDs alphabetically to remain deterministic
    zero_in_degree = [m_id for m_id, deg in in_degree.items() if deg == 0]
    zero_in_degree.sort()

    order: List[str] = []
    while zero_in_degree:
        curr = zero_in_degree.pop(0)
        order.append(curr)

        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                zero_in_degree.append(neighbor)
        
        # Sort again to ensure alphabetical ties remain deterministic
        zero_in_degree.sort()

    if len(order) != len(modules_map):
        raise ValueError("Circular dependency detected in structural world module graph.")

    return order

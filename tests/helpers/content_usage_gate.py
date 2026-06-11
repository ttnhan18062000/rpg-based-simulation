from __future__ import annotations

from typing import List

from src.content.matrix import CONTENT_USAGE_MATRIX
from src.content.reference_graph import FAMILY_TO_SHORT

ACTIVE_IMPL_STATES: frozenset = frozenset({"RESOLVED_PARTIALLY", "RUNTIME_AUTHORITATIVE"})

# Families whose records are consumed via implicit runtime mechanisms that do not
# produce reference graph edges, or are graph entry points (no inbound edges by design).
GRAPH_EXEMPT_SHORTS: frozenset = frozenset({
    "attribute", "element", "perspective", "projection",
    "defaults",
    "spawn_table",
    "composition",
    "scenario",
})


def collect_family_graph_violations(ref_graph) -> List[str]:
    """Return violation strings for active content families with no consumed records.

    A family is active if its ContentUsageMatrix entry has an implementation_state
    in ACTIVE_IMPL_STATES. A family is violated if it has nodes in the reference
    graph but none of them have any incoming edge.

    Per Option A (Phase 20-28 repair): YAML comment markers are never read here.
    Implementation status is determined solely from ContentUsageMatrix.
    """
    violations: List[str] = []
    for family_key, entry in CONTENT_USAGE_MATRIX.items():
        if entry.implementation_state not in ACTIVE_IMPL_STATES:
            continue
        short = FAMILY_TO_SHORT.get(family_key.replace("/", "."))
        if not short or short in GRAPH_EXEMPT_SHORTS:
            continue
        family_nodes = [nid for nid in ref_graph.nodes if nid.startswith(f"{short}:")]
        if not family_nodes:
            continue
        consumed = [nid for nid in family_nodes if ref_graph.is_record_used(nid)]
        if not consumed:
            violations.append(
                f"  {family_key} ({short}): {len(family_nodes)} records loaded, "
                f"none have any incoming reference graph edge"
            )
    return violations

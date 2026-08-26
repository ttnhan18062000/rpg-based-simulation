"""
src/domains/world_emergence/quest_grammar.py
───────────────────────────────────────────────────────────────────────────────
Runtime pre-emit grammar checks for QuestOpportunity admission into
quest_registry_add. Sibling to the build-time WORLD-REACH-001 gate
(src/worldbuilding/validator.py) — this gate runs against live
AuthoritativeState inside WorldEmergencePhase, not WorldSpec at build time.

Both predicates and the combinator are pure functions of their arguments:
no uuid(), no time/clock reads, no RNG, no state mutation. This preserves
QuestOpportunityGenerator's own documented read-only/deterministic contract
one call further down the same chain.
"""
from __future__ import annotations

from typing import Optional, Tuple

from src.core.models.quests import QuestOpportunity
from src.core.state import AuthoritativeState
from src.worldbuilding.reachability import is_reachable


def build_faction_territory_pool(state: AuthoritativeState) -> set[str]:
    """Faction IDs with at least one controlled region. Always a real set
    (never None) — a dissolved or unregistered faction is absent from this
    pool the same as one present with empty territory, by construction.
    """
    return {faction_id for faction_id, f in state.factions.items() if f.territory}


def check_faction_coherence(faction_source: Optional[str], state: AuthoritativeState) -> bool:
    """True if `faction_source` has territorial presence, or makes no claim at all
    (faction_source is None auto-passes — no faction claim to verify).
    """
    required = [faction_source] if faction_source else []
    pool = build_faction_territory_pool(state)
    return is_reachable(required, pool)


def _parse_fetch_resource_type(token: str) -> Optional[str]:
    """Only "fetch:<resource>:<qty>" tokens carry a resource-availability claim.
    Any other shape (e.g. "eliminate:<subject>:1") has nothing to verify here.
    """
    parts = token.split(":")
    if len(parts) >= 2 and parts[0] == "fetch":
        return parts[1]
    return None


def check_resource_availability(objective_chain: Tuple[str, ...], state: AuthoritativeState) -> bool:
    """True unless a fetch-token's resource type resolves to at least one matching
    node AND every matching node is fully depleted. No matching node at all is
    cannot-verify, not a violation — mirrors is_reachable's None-pool semantics.
    """
    for token in objective_chain:
        resource_type = _parse_fetch_resource_type(token)
        if resource_type is None:
            continue
        matching = [n for n in state.resource_nodes.values() if n.yields_item == resource_type]
        if matching and all(n.remaining_charges == 0 for n in matching):
            return False
    return True


def validate_quest_opportunity(opportunity: QuestOpportunity, state: AuthoritativeState) -> Optional[str]:
    """Returns a short rejection-reason code, or None if the opportunity is admissible."""
    if not check_faction_coherence(opportunity.faction_source, state):
        return "faction_zero_territory"
    if not check_resource_availability(opportunity.objective_chain, state):
        return "resource_depleted"
    return None

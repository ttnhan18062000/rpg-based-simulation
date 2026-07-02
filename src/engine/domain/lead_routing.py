"""
src/engine/domain/lead_routing.py
───────────────────────────────────────────────────────────────────────────────
Epic 4.2E — LeadKind routing for PERSON and CONCEPT leads.

Resolves the correct ObjectiveKind and target string for a given LeadState
based on its LeadKind.  Pure read-only decision logic; no state mutation.

Design:
  - Pure static class: reads lead, returns (ObjectiveKind, target) tuple.
  - No direct state writes.
  - Deterministic: depends only on lead state (no randomness).

Logic ID: E42E-002
"""
from __future__ import annotations

from src.core.strategic import LeadKind, LeadState, ObjectiveKind


class LeadRoutingSystem:
    """
    Resolves the routing objective for a lead based on its kind.

    PERSON leads: navigate to the entity identified by lead.subject (entity_id).
    CONCEPT leads: seek an InformationProvider that knows the concept domain.
    LOCATION / OBJECT / EVENT leads: navigate to the lead's detail or subject.

    Logic ID: E42E-002
    """

    @staticmethod
    def resolve_objective_kind(lead: LeadState) -> tuple[ObjectiveKind, str]:
        """
        Return (objective_kind, target) for routing a lead to an action.

        Args:
            lead: The LeadState to route.

        Returns:
            A tuple of (ObjectiveKind, target_string) where:
              - PERSON  → (INVESTIGATE, lead.subject)         # navigate to entity_id
              - CONCEPT → (ASK_INFORMATION, lead.subject)     # query nearest provider
              - LOCATION → (REACH_LOCATION, detail or subject)
              - OBJECT / EVENT → (INVESTIGATE, lead.subject)
        """
        if lead.kind == LeadKind.PERSON:
            # Navigate toward the entity identified by subject (entity_id string).
            # On arrival: success if entity found alive, contradiction if dead/moved.
            return (ObjectiveKind.INVESTIGATE, lead.subject)

        if lead.kind == LeadKind.CONCEPT:
            # Route to nearest InformationProvider whose knowledge_domains
            # includes the concept domain.  Standard paid transaction (E42C logic)
            # handles the actual query on arrival.
            return (ObjectiveKind.ASK_INFORMATION, lead.subject)

        if lead.kind == LeadKind.LOCATION:
            target = lead.detail if lead.detail else lead.subject
            return (ObjectiveKind.REACH_LOCATION, target)

        # OBJECT, EVENT, and any future unrecognised kinds
        return (ObjectiveKind.INVESTIGATE, lead.subject)

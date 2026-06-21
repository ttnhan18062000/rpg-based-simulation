"""
src/cognition/knowledge_model.py
───────────────────────────────────────────────────────────────────────────────
Phase 2 — KnowledgeModelService

Converts InformationProvider responses into entity-owned KnowledgeModelComponent.
Stateless, deterministic, read-only.

Critical invariant:
  Hidden world truth is NEVER injected.  Only what the provider returned in
  the InformationResponse is assimilated.  This preserves information opacity.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

from src.core.self_model import (
    KnowledgeFact,
    KnowledgeModelComponent,
    UnknownFact,
)

if TYPE_CHECKING:
    # Provider-side transfer object (NOT the entity-owned KnowledgeFact above)
    from src.world.providers.information import InformationResponse
    from src.core.state import EntityState


class KnowledgeModelService:
    """
    Assimilates InformationProvider responses into entity-owned knowledge.

    answer_kind mapping:
      "known"              → KnowledgeFact(s) with full certainty from response
      "partial"            → KnowledgeFact(s) where available + UnknownFact(s)
      "unknown"            → UnknownFact(s) only
      "insufficient_gold"  → nothing assimilated (entity could not pay)
    """

    @staticmethod
    def assimilate(
        entity: "EntityState",
        response: "InformationResponse",
        tick: int,
    ) -> KnowledgeModelComponent:
        """
        Merge an InformationResponse into an updated KnowledgeModelComponent.

        Starts from the entity's current knowledge and adds/updates entries.
        Does not remove existing knowledge.

        Args:
            entity:   The entity whose knowledge is being updated.
            response: The InformationResponse from a provider query.
            tick:     Current simulation tick.
        Returns:
            A new frozen KnowledgeModelComponent with merged knowledge.
        """
        current = entity.self_model.knowledge
        # Start from copies of existing dicts so we can extend them
        facts: Dict[str, KnowledgeFact] = dict(current.facts)
        unknowns: Dict[str, UnknownFact] = dict(current.unknowns)

        answer_kind = getattr(response, "answer_kind", "unknown")

        if answer_kind == "insufficient_gold":
            # Entity couldn't pay — nothing learned, but record intent to query
            # Don't modify anything; return current knowledge unchanged
            return current

        # ── Assimilate known facts from the response ──────────────────────────
        for provider_fact in getattr(response, "facts", ()):
            subject = getattr(provider_fact, "subject", "")
            fact_type = getattr(provider_fact, "fact_type", "")
            details = dict(getattr(provider_fact, "details", {}))
            certainty = getattr(response, "certainty", 1.0)
            source_id = getattr(response, "source_id", None)

            if subject:
                facts[subject] = KnowledgeFact(
                    subject=subject,
                    fact_type=fact_type,
                    details=details,
                    certainty=round(certainty, 4),
                    source_id=source_id,
                    recorded_tick=tick,
                )
                # If we now have a confirmed fact, remove any existing unknown for it
                unknowns.pop(subject, None)

        # ── Assimilate unknowns from the response ─────────────────────────────
        for unknown_subject in getattr(response, "unknowns", ()):
            if unknown_subject and unknown_subject not in facts:
                # Only record as unknown if we don't already have a confirmed fact
                reason = "provider_" + answer_kind  # "provider_partial" or "provider_unknown"
                unknowns[unknown_subject] = UnknownFact(
                    subject=unknown_subject,
                    reason=reason,
                    recorded_tick=tick,
                )

        # ── Assimilate leads as partial facts (low certainty) ─────────────────
        # Leads from providers are hints, not confirmed facts
        for lead in getattr(response, "suggested_leads", ()):
            lead_subject = getattr(lead, "subject", "")
            lead_detail = getattr(lead, "detail", "")
            lead_certainty = getattr(lead, "certainty", None)

            if lead_subject and lead_detail:
                # Convert lead certainty enum to float if needed
                lead_cert_float = _lead_certainty_to_float(lead_certainty)
                # Record as a low-confidence fact (a "lead fact")
                fact_key = f"lead.{lead_subject}"
                facts[fact_key] = KnowledgeFact(
                    subject=lead_subject,
                    fact_type="lead",
                    details={"hint": lead_detail},
                    certainty=round(lead_cert_float, 4),
                    source_id=getattr(response, "source_id", None),
                    recorded_tick=tick,
                )
                # The original subject is still unknown if we only have a lead
                # Do NOT remove the unknown for the original subject

        return KnowledgeModelComponent(
            facts=facts,
            unknowns=unknowns,
            last_updated_tick=tick,
        )


_STALENESS_DECAY_RATE: float = 0.0001
"""Certainty halves over 10 000 ticks (LEG-RPG-150 read-time staleness)."""


def effective_certainty(fact: "KnowledgeFact", current_tick: int) -> float:
    """
    Compute the effective certainty of a KnowledgeFact at read time,
    applying exponential-style staleness decay without mutating the frozen record.

    Formula (E42D):
        elapsed = max(0, current_tick - fact.recorded_tick)
        decay_factor = max(0.1, 1.0 - elapsed * _STALENESS_DECAY_RATE)
        effective = fact.certainty * decay_factor

    At tick 0 delta: no decay.
    At tick 5000 delta: decay_factor = 0.5, so effective = certainty * 0.5.
    At tick 10000+ delta: decay_factor floored at 0.1.
    """
    elapsed = max(0, current_tick - fact.recorded_tick)
    decay_factor = max(0.1, 1.0 - elapsed * _STALENESS_DECAY_RATE)
    return fact.certainty * decay_factor


def _lead_certainty_to_float(certainty: object) -> float:
    """Convert LeadCertainty enum or float to a 0..1 float."""
    if certainty is None:
        return 0.3
    if isinstance(certainty, float):
        return max(0.0, min(1.0, certainty))
    if isinstance(certainty, int):
        return max(0.0, min(1.0, certainty / 100.0))
    # Handle LeadCertainty enum by name
    name = getattr(certainty, "name", str(certainty)).upper()
    mapping = {
        "CONFIRMED": 1.0,
        "HIGH": 0.85,
        "PROBABLE": 0.70,
        "APPROXIMATE": 0.55,
        "VAGUE": 0.35,
        "RUMOR": 0.20,
        "UNKNOWN": 0.10,
    }
    return mapping.get(name, 0.3)

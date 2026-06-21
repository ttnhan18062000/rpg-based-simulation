"""
src/engine/pipeline_phases/lead_contradiction.py
───────────────────────────────────────────────────────────────────────────────
Epic 4.2D — Lead Contradiction + Belief Staleness Decay (phase half).

When an entity holds a non-EXHAUSTED lead whose destination is now inconsistent
with world state (depleted resource node, dead person target), this system:

  1. Marks the LeadState test_outcome="FAILURE", failure_count+1, certainty=EXHAUSTED.
  2. Decrements the originating InformationProvider's reliability_score by 0.1
     (floored at 0.1) via StateUpdate.information_providers_update.
  3. Regenerates an UnknownFact(subject=lead.subject, priority=0.7) so the
     InformationNeedDetector fires an INFORMATION_SEEKING project next tick.
  4. Returns a list of SimulationEvents (event_type="belief_contradiction") for
     the kernel/tests to record.

All durable mutations are represented as typed update records — no direct state
writes.  Deterministic: entities iterated in sorted id order, leads in sorted
id order.

Logic ID: E42D-001
"""
from __future__ import annotations

import logging
from dataclasses import replace
from typing import TYPE_CHECKING, List, Tuple

from src.core.strategic import LeadCertainty, LeadState
from src.core.updates import EntityUpdate, StateUpdate, StrategicUpdate
from src.observability.events import SimulationEvent

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState

_log = logging.getLogger(__name__)

_RELIABILITY_PENALTY: float = 0.1
_RELIABILITY_FLOOR: float = 0.1
_REPLANNING_PRIORITY: float = 0.7


def _is_lead_contradicted(lead: LeadState, state: "AuthoritativeState") -> bool:
    """
    Return True when the lead's claimed destination is now inconsistent with
    world state.

    Supported lead kinds:
      - "resource"  → resource node must exist and have remaining_charges > 0
      - "location"  → check if subject maps to a resource node key; if found,
                      apply the same charge check (location leads from providers
                      point to resource subjects)
      - "person"    → subject maps to an entity id; entity must be alive
      - Other kinds → not checked (not contradicted)

    The subject field may be a plain string like "moon_resin" or a namespaced
    key like "material.moon_resin.source".  We scan by partial match against
    resource node yields_item and entity ids.
    """
    lead_kind = lead.kind
    subject = lead.subject

    if lead_kind == "resource":
        # Look for a resource node where yields_item matches subject
        for node in state.resource_nodes.values():
            if node.yields_item == subject or subject in node.yields_item:
                return node.remaining_charges <= 0
        # Node not found — not contradicted (may not exist yet / different tick)
        return False

    if lead_kind == "location":
        # Treat location leads as pointing to a resource node by subject match
        for node in state.resource_nodes.values():
            if node.yields_item == subject or subject in node.yields_item:
                return node.remaining_charges <= 0
        # No matching node → not contradicted
        return False

    if lead_kind == "person":
        # Subject should be a numeric entity id string
        try:
            target_id = int(subject)
        except (ValueError, TypeError):
            return False
        target = state.entities.get(target_id)
        if target is None:
            return True  # Person gone from world
        return not getattr(target.combat, "alive", True)

    if lead_kind == "information":
        # Information leads from PaidInformationTransactionSystem — these are
        # not validated against world state here; contradiction comes from
        # failed search events (handled by BeliefContradictionService).
        return False

    return False


class LeadContradictionSystem:
    """
    Decision-only pipeline phase: detects contradicted leads and emits typed
    updates to mark failures, penalise providers, and trigger replanning.

    Called after entity positions are resolved (so we can check if an entity
    is at their lead's destination).

    VERIFIED v2: lead_contradiction_determinism
    """

    @staticmethod
    def enforce(
        state: "AuthoritativeState",
        update: StateUpdate,
    ) -> Tuple[StateUpdate, List[SimulationEvent]]:
        """
        Scan every alive entity's non-EXHAUSTED leads for world inconsistencies.

        Returns:
            (updated_state_update, simulation_events)
        """
        from src.core.self_model import KnowledgeModelComponent, UnknownFact

        entity_updates = dict(update.entity_updates)
        providers_update = dict(update.information_providers_update)
        events: List[SimulationEvent] = []

        # Iterate entities in deterministic order
        for entity in sorted(state.entities.values(), key=lambda e: e.id):
            if not getattr(entity.combat, "alive", False):
                continue
            if not getattr(entity.lifecycle, "active", True):
                continue

            strat = entity.strategic
            if not strat or not strat.leads:
                continue

            # Iterate leads in sorted order for determinism
            for lead_id in sorted(strat.leads):
                lead = strat.leads[lead_id]

                if lead.certainty == LeadCertainty.EXHAUSTED:
                    continue
                if lead.test_outcome == "FAILURE":
                    continue  # already marked failed

                if not _is_lead_contradicted(lead, state):
                    continue

                # ── Lead is contradicted ───────────────────────────────────

                # 1. Mark lead as failed
                failed_lead = replace(
                    lead,
                    certainty=LeadCertainty.EXHAUSTED,
                    tested=True,
                    test_outcome="FAILURE",
                    failure_count=lead.failure_count + 1,
                )

                # 2. Build StrategicUpdate for the failed lead
                strat_upd = StrategicUpdate(leads_add_or_update=[failed_lead])

                # 3. Generate new UnknownFact to trigger replanning next tick
                current_km = entity.self_model.knowledge
                new_unknowns = dict(current_km.unknowns)
                new_unknowns[lead.subject] = UnknownFact(
                    subject=lead.subject,
                    reason="lead_contradicted",
                    recorded_tick=state.tick,
                    priority=_REPLANNING_PRIORITY,
                )
                new_km = KnowledgeModelComponent(
                    facts=current_km.facts,
                    unknowns=new_unknowns,
                    last_updated_tick=state.tick,
                )
                from src.core.self_model import SelfModelBundle
                new_bundle = replace(entity.self_model, knowledge=new_km)

                # 4. Build EntityUpdate
                existing_ent_upd = entity_updates.get(
                    entity.id, EntityUpdate(entity_id=entity.id)
                )
                # Merge strategic update
                merged_strategic = (
                    existing_ent_upd.strategic.merge(strat_upd)
                    if existing_ent_upd.strategic is not None
                    else strat_upd
                )
                entity_updates[entity.id] = replace(
                    existing_ent_upd,
                    strategic=merged_strategic,
                    self_model_bundle_set=new_bundle,
                )

                # 5. Decrement provider reliability
                provider_id = lead.source_entity_id
                if provider_id is not None:
                    # Check current update dict first, then authoritative state
                    provider = providers_update.get(
                        provider_id,
                        state.information_providers.get(provider_id),
                    )
                    if provider is not None:
                        new_reliability = max(
                            _RELIABILITY_FLOOR,
                            provider.reliability_score - _RELIABILITY_PENALTY,
                        )
                        providers_update[provider_id] = replace(
                            provider, reliability_score=round(new_reliability, 4)
                        )

                # 6. Emit SimulationEvent
                event = SimulationEvent(
                    event_type="belief_contradiction",
                    event_category="strategy",
                    tick=state.tick,
                    severity="INFO",
                    source_system="lead_contradiction_system",
                    message=(
                        f"Entity {entity.id} lead '{lead_id}' contradicted: "
                        f"subject='{lead.subject}' was {lead.certainty.value}"
                    ),
                    entity_id=entity.id,
                    payload={
                        "lead_id": lead_id,
                        "provider_id": provider_id,
                        "subject": lead.subject,
                        "old_certainty": lead.certainty.value,
                        "failure_count": failed_lead.failure_count,
                    },
                )
                events.append(event)

                _log.debug(
                    "LeadContradictionSystem: entity=%d lead=%s subject=%s "
                    "provider=%s tick=%d",
                    entity.id,
                    lead_id,
                    lead.subject,
                    provider_id,
                    state.tick,
                )

        if not events and not providers_update and entity_updates == dict(update.entity_updates):
            return update, []

        updated = replace(
            update,
            entity_updates=entity_updates,
            information_providers_update=providers_update,
        )
        return updated, events

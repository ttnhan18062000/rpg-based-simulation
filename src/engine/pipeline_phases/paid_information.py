"""
src/engine/pipeline_phases/paid_information.py
───────────────────────────────────────────────────────────────────────────────
Epic 4.2C — Paid Information Transaction System.

When an entity with an active INFORMATION_SEEKING project is present alongside
a registered InformationProvider, this system emits a ResourceTransferIntent
(source_kind="INFORMATION_PURCHASE") that:
  - deducts gold proportional to provider reliability
  - carries a contingent StrategicUpdate delivering a LeadState + project removal

All gold deductions flow through the authoritative ResourceTransactionResolver
(conservation law: Chapter 03). No durable state is mutated here.

Logic ID: E42C-001
"""
from __future__ import annotations

import logging
from dataclasses import replace
from typing import TYPE_CHECKING

from src.core.strategic import (
    LeadCertainty,
    LeadState,
    ProjectKind,
    ProjectStatus,
    ObjectiveKind,
)
from src.core.updates import EntityUpdate, StrategicUpdate
from src.core.update_models.resources import ResourceTransferIntent

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate

_log = logging.getLogger(__name__)

# Cost formula constant: base_cost / reliability_score
_INFO_BASE_COST: int = 10
_MIN_RELIABILITY: float = 0.1


def _lead_certainty_for_reliability(reliability: float) -> LeadCertainty:
    """Map reliability score to LeadCertainty tier.

    reliability >= 0.8  → PRECISE    (high-quality provider)
    0.5 <= rel < 0.8    → APPROXIMATE (mid-range provider)
    rel < 0.5           → VAGUE       (low-reliability provider)
    """
    if reliability >= 0.8:
        return LeadCertainty.PRECISE
    if reliability >= 0.5:
        return LeadCertainty.APPROXIMATE
    return LeadCertainty.VAGUE


def _transaction_cost(reliability: float) -> int:
    """Compute gold cost: 10 / max(0.1, reliability), rounded down to int."""
    return int(_INFO_BASE_COST * (1.0 / max(_MIN_RELIABILITY, reliability)))


class PaidInformationTransactionSystem:
    """
    Decision-only phase: detects seeker-provider pairs and injects
    ResourceTransferIntents for downstream authoritative resolution.

    Called in pipeline Phase 6 (Economy & Evolution), before
    ResourceTransactionPhase so the resolver can enforce conservation law.

    VERIFIED v2: paid_information_conservation
    """

    @staticmethod
    def enforce(state: "AuthoritativeState", update: "StateUpdate") -> "StateUpdate":
        """
        For every alive entity with an active INFORMATION_SEEKING project:
          1. Find a registered InformationProvider (deterministic: min entity_id).
          2. Compute cost from provider.reliability_score.
          3. Derive LeadState certainty.
          4. Emit ResourceTransferIntent with contingent StrategicUpdate.

        Returns the StateUpdate with intents appended to entity updates.
        """
        providers = getattr(state, "information_providers", {})
        if not providers:
            return update

        entity_updates = dict(update.entity_updates)

        # Iterate seekers in sorted order for determinism
        for entity in sorted(state.entities.values(), key=lambda e: e.id):
            if not entity.combat.alive or not entity.lifecycle.active:
                continue

            # Find the active INFORMATION_SEEKING project
            seeking_project = None
            for proj in entity.strategic.projects.values():
                if (
                    proj.kind == ProjectKind.INFORMATION_SEEKING
                    and proj.status == ProjectStatus.ACTIVE
                ):
                    seeking_project = proj
                    break

            if seeking_project is None:
                continue

            # Find the best provider (deterministic: smallest entity_id,
            # skip self-provision)
            provider_record = None
            for pid in sorted(providers.keys()):
                if pid == entity.id:
                    continue
                provider_record = providers[pid]
                break

            if provider_record is None:
                continue

            provider_id = provider_record.entity_id
            reliability = provider_record.reliability_score

            cost = _transaction_cost(reliability)
            certainty = _lead_certainty_for_reliability(reliability)

            # Determine the subject being sought from the project's objective
            seeking_subject = "unknown"
            for obj in seeking_project.objectives:
                if obj.kind == ObjectiveKind.ASK_INFORMATION and obj.target:
                    seeking_subject = obj.target
                    break
            if not seeking_subject or seeking_subject == "unknown":
                # Fallback: derive from project id
                seeking_subject = seeking_project.id

            lead = LeadState(
                id=f"lead_info_{entity.id}_{provider_id}_{state.tick}",
                kind="information",
                subject=seeking_subject,
                certainty=certainty,
                source_entity_id=provider_id,
                discovered_tick=state.tick,
            )

            strategic_upd = StrategicUpdate(
                leads_add_or_update=[lead],
                projects_remove=[seeking_project.id],
            )

            intent = ResourceTransferIntent(
                source_id=provider_id,
                source_kind="INFORMATION_PURCHASE",
                gold_delta=0,
                gold_cost=cost,
                transfer_kind="INFORMATION_PURCHASE",
                strategic_upd=strategic_upd,
            )

            existing_upd = entity_updates.get(
                entity.id, EntityUpdate(entity_id=entity.id)
            )
            entity_updates[entity.id] = replace(
                existing_upd,
                resource_transfers=list(existing_upd.resource_transfers) + [intent],
            )

            _log.debug(
                "PaidInformationTransactionSystem: seeker=%d provider=%d "
                "reliability=%.2f cost=%d certainty=%s subject=%s tick=%d",
                entity.id,
                provider_id,
                reliability,
                cost,
                certainty.value,
                seeking_subject,
                state.tick,
            )

        if entity_updates == dict(update.entity_updates):
            return update

        return replace(update, entity_updates=entity_updates)

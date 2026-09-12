"""
src/engine/pipeline_phases/information_intent_execution.py
───────────────────────────────────────────────────────────────────────────────
Gives InformationBeliefPhase Branch B's routed ActionIntent (self-model
query-routing — "what don't I know, who might know it") a production call
site. Branch B stores its routed ActionIntent in EntityUpdate.pending_action_intent
(phase.py) but never executes it; this phase does, delegating to the existing
ActionIntentAdapter.execute() implementation.

Gated by ENABLE_INFORMATION_INTENT_EXECUTION, default OFF (see
docs/parity_ledger/infrastructure.yaml INFRA-270).

Logic ID: TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE

TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE:
previously Branch B stored the raw ActionIntent in intent_results (typed for IntentResult
only), and this phase stripped it back out before it could reach entity.identity
.latest_intent_results and crash every real reader of that field. Branch B now writes
to the dedicated pending_action_intent field instead, which no write path ever merges
toward latest_intent_results -- so there is nothing left to strip. If a future change
ever needs that stripping logic back, that is itself evidence a raw ActionIntent is
reaching intent_results again, and should be treated as a regression of this fix, not a
missing feature to restore.
"""
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from src.core.updates import EntityUpdate
from src.engine.intent.action_intent import ActionIntentAdapter

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


class InformationIntentExecutionPhase:
    """
    Executes the ActionIntent InformationBeliefPhase Branch B routed into
    EntityUpdate.pending_action_intent this tick.
    """

    @staticmethod
    def execute(state: "AuthoritativeState", update: "StateUpdate") -> "StateUpdate":
        refined_entity_updates = dict(update.entity_updates)

        for eid in sorted(update.entity_updates.keys()):
            ent_upd = update.entity_updates[eid]
            candidate = ent_upd.pending_action_intent
            if candidate is None:
                continue

            entity = state.entities.get(eid)
            if entity is None:
                continue

            refined_entity_updates[eid] = replace(refined_entity_updates[eid], pending_action_intent=None)

            adapter_updates = ActionIntentAdapter.execute(
                entity=entity,
                intent=candidate,
                current_tick=state.tick,
                neighbor_view=None,
                context=state,
            )
            for action_eid, action_upd in adapter_updates.items():
                existing_upd = refined_entity_updates.get(
                    action_eid, EntityUpdate(entity_id=action_eid)
                )
                refined_entity_updates[action_eid] = existing_upd.merge(action_upd)

        if refined_entity_updates == dict(update.entity_updates):
            return update

        return replace(update, entity_updates=refined_entity_updates)

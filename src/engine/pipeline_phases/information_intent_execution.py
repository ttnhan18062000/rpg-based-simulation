"""
src/engine/pipeline_phases/information_intent_execution.py
───────────────────────────────────────────────────────────────────────────────
Gives InformationBeliefPhase Branch B's routed ActionIntent (self-model
query-routing — "what don't I know, who might know it") a production call
site. Branch B stores a raw ActionIntent in EntityUpdate.intent_results
(phase.py:97-104) but never executes it; this phase does, delegating to the
existing ActionIntentAdapter.execute() implementation.

Gated by ENABLE_INFORMATION_INTENT_EXECUTION, default OFF (see
docs/parity_ledger/infrastructure.yaml INFRA-270).

Logic ID: TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE
"""
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from src.core.updates import EntityUpdate
from src.engine.intent.action_intent import ActionIntent, ActionIntentAdapter

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


class InformationIntentExecutionPhase:
    """
    Executes ActionIntent objects that InformationBeliefPhase Branch B routed
    into intent_results this tick.

    intent_results is declared List[IntentResult] (src/core/updates.py), an
    unrelated dataclass economy.py/patches.py also populate that field with —
    the isinstance(candidate, ActionIntent) filter below is mandatory, not
    incidental, to avoid misinterpreting those entries.
    """

    @staticmethod
    def execute(state: "AuthoritativeState", update: "StateUpdate") -> "StateUpdate":
        refined_entity_updates = dict(update.entity_updates)

        for eid in sorted(update.entity_updates.keys()):
            ent_upd = update.entity_updates[eid]
            if not ent_upd.intent_results:
                continue

            entity = state.entities.get(eid)
            if entity is None:
                continue

            candidates = [c for c in ent_upd.intent_results if isinstance(c, ActionIntent)]
            if not candidates:
                continue

            # Strip the raw, unresolved ActionIntent entries from this entity's own
            # intent_results BEFORE executing them. Without this, they survive unchanged
            # (EntityUpdate.merge() concatenates intent_results additively below), get
            # installed as entity.identity.latest_intent_results, and crash
            # StrategicWorkQueue.build() (reads .accepted unconditionally off every
            # entry, a field only real IntentResult objects have).
            remaining_results = [r for r in ent_upd.intent_results if not isinstance(r, ActionIntent)]
            refined_entity_updates[eid] = replace(refined_entity_updates[eid], intent_results=remaining_results)

            for candidate in candidates:
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

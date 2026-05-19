from __future__ import annotations
import time
import logging
from typing import Any, List, Optional
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.events import (
    SimulationEvent, CombatDamageEvent, CombatKillEvent,
    GoldTransactionEvent, QuestEvent, MovementEvent, LifecycleEvent
)

logger = logging.getLogger(__name__)

class EventExtractor:
    """Extracts curated low-volume SimulationEvents from state changes and committed updates."""
    @staticmethod
    def extract(
        prior_state: AuthoritativeState,
        current_state: AuthoritativeState,
        update: Any,
        mode: ObservabilityMode = ObservabilityMode.LIGHT
    ) -> List[SimulationEvent]:
        """Compares state transitions to produce semantic events matching volume policies."""
        if mode == ObservabilityMode.OFF:
            return []

        tick = current_state.tick
        now = time.time()
        events: List[SimulationEvent] = []

        # Optimization: Scoped comparison using dirty entity IDs
        dirty_entity_ids = update.entity_updates.keys() if (update and hasattr(update, "entity_updates")) else []
        if not dirty_entity_ids:
            dirty_entity_ids = current_state.entities.keys()

        for eid in dirty_entity_ids:
            entity = current_state.entities.get(eid)
            prior_ent = prior_state.entities.get(eid)

            # Despawn lifecycle
            if entity is None:
                if prior_ent is not None:
                    events.append(LifecycleEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        action="despawn", details={"kind": prior_ent.kind, "position": prior_ent.navigation.position}
                    ))
                continue

            # Spawn lifecycle
            if prior_ent is None:
                events.append(LifecycleEvent(
                    tick=tick, timestamp=now, entity_id=eid,
                    action="spawn", details={"kind": entity.kind, "position": entity.navigation.position}
                ))
                continue

            # Movement (exclusively low-volume for non-LIGHT/LONG_RUN modes)
            if prior_ent.navigation.position != entity.navigation.position:
                if mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
                    events.append(MovementEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        start_pos=prior_ent.navigation.position,
                        end_pos=entity.navigation.position
                    ))

            # Combat damage event
            hp_diff = entity.combat.hp - prior_ent.combat.hp
            if hp_diff < 0:
                is_lethal = (entity.combat.hp <= 0 or not entity.lifecycle.active)
                # Volumization rule: skip routine damage inside LIGHT or LONG_RUN mode unless lethal
                if is_lethal or mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
                    attacker_id = None
                    e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
                    if e_upd and getattr(e_upd, "combat_upd", None):
                        attacker_id = e_upd.combat_upd.attacker_id

                    events.append(CombatDamageEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        attacker_id=attacker_id, damage=int(-hp_diff),
                        is_lethal=is_lethal
                    ))

            # Kill events
            if prior_ent.lifecycle.active and not entity.lifecycle.active:
                killer_id = None
                e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
                if e_upd and getattr(e_upd, "combat_upd", None):
                    killer_id = e_upd.combat_upd.attacker_id

                events.append(CombatKillEvent(
                    tick=tick, timestamp=now, entity_id=eid,
                    killer_id=killer_id
                ))

            # Economy/Gold events (exclusively meaningful changes)
            gold_diff = entity.inventory.gold - prior_ent.inventory.gold
            if gold_diff != 0:
                # Volumization rule: ignore micro-trades (< 5.0 gold) in LIGHT mode
                if abs(gold_diff) >= 5.0 or mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
                    kind = "gain" if gold_diff > 0 else "loss"
                    events.append(GoldTransactionEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        amount=float(abs(gold_diff)), transaction_kind=kind
                    ))

            # Quest progress lifecycle events
            prior_projects = prior_ent.strategic.projects
            current_projects = entity.strategic.projects
            for qid, qstate in current_projects.items():
                prior_qstate = prior_projects.get(qid)
                if prior_qstate is None:
                    events.append(QuestEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        quest_id=qid, status="started"
                    ))
                elif prior_qstate.status != qstate.status:
                    events.append(QuestEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        quest_id=qid, status=str(qstate.status)
                    ))

        return events

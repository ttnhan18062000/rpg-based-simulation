"""
BehaviorEventNormalizer — Phase 22 async behavior normalization.

Converts raw SimulationEvent or ObservabilityEventEnvelope objects into
zero or more semantic BehaviorEvent objects.

Design rules (from Phase 22 spec):
- Runs outside the simulation hot path (async worker or post-run).
- Stateless: does not mutate raw events, does not require full world state.
- Deterministic: same input → same output.
- Unknown events are skipped or mapped to unknown_behavior explicitly.
- Links source event IDs for full traceability.
- Can be disabled by flag (caller responsibility).
"""
from __future__ import annotations

import logging
from typing import Sequence, Union

from src.observability.behavior.behavior_event import BehaviorEvent
from src.observability.behavior.normalization_context import BehaviorNormalizationContext
from src.observability.events import (
    CombatDamageEvent,
    CombatKillEvent,
    GoldTransactionEvent,
    LifecycleEvent,
    MovementEvent,
    ObservabilityEventEnvelope,
    QuestEvent,
    SimulationEvent,
)

log = logging.getLogger(__name__)

# Type alias for supported inputs
RawEvent = Union[SimulationEvent, ObservabilityEventEnvelope]


class BehaviorEventNormalizer:
    """
    Maps raw simulation events to semantic behavior events.

    The mapping table below is the canonical source of truth for
    Phase 22 behavior categorization:

    | Raw event type         | behavior_category    | behavior_family         |
    |------------------------|----------------------|-------------------------|
    | movement               | movement             | travel                  |
    | combat_damage          | combat               | engage                  |
    | combat_kill            | combat               | kill_or_defeat          |
    | quest_event (started)  | quest                | accept                  |
    | quest_event (progress) | quest                | progress                |
    | quest_event (completed)| quest                | complete                |
    | quest_event (failed)   | failure_response     | quest_failure           |
    | gold_transaction (buy/sell/reward) | trade | buy_sell_or_reward  |
    | lifecycle (level_up)   | progression          | level_up                |
    | lifecycle (spawn)      | world_response       | spawn                   |
    | lifecycle (despawn)    | world_response       | despawn                 |
    | unknown category       | unknown_behavior     | unknown                 |
    """

    # -----------------------------------------------------------------
    # Event category → normalization handler
    # -----------------------------------------------------------------
    _CATEGORY_HANDLERS: dict[str, str] = {
        "movement": "_normalize_movement",
        "combat": "_normalize_combat",
        "economy": "_normalize_economy",
        "quest": "_normalize_quest",
        "lifecycle": "_normalize_lifecycle",
        "resource": "_normalize_resource",
        "strategy": "_normalize_strategy",
        "social": "_normalize_social",
        "region": "_normalize_region",
    }

    def normalize_event(
        self,
        event: RawEvent,
        context: BehaviorNormalizationContext,
    ) -> tuple[BehaviorEvent, ...]:
        """
        Normalize a single raw event into zero or more BehaviorEvents.

        Returns an empty tuple when:
        - The event category is not normalizable.
        - The event type is explicitly skipped.
        """
        try:
            return self._dispatch(event, context)
        except Exception:  # pragma: no cover — defensive catch
            log.warning(
                "BehaviorEventNormalizer: unexpected error normalizing event_type=%s",
                getattr(event, "event_type", "?"),
                exc_info=True,
            )
            return ()

    def normalize_batch(
        self,
        events: Sequence[RawEvent],
        context: BehaviorNormalizationContext,
    ) -> tuple[BehaviorEvent, ...]:
        """Normalize a batch of raw events, returning all behavior events."""
        results: list[BehaviorEvent] = []
        for event in events:
            results.extend(self.normalize_event(event, context))
        return tuple(results)

    # -----------------------------------------------------------------
    # Dispatch
    # -----------------------------------------------------------------

    def _dispatch(
        self,
        event: RawEvent,
        context: BehaviorNormalizationContext,
    ) -> tuple[BehaviorEvent, ...]:
        """Route to the appropriate category handler."""
        category = getattr(event, "event_category", None)
        if not category:
            return ()

        handler_name = self._CATEGORY_HANDLERS.get(category)
        if not handler_name:
            return ()

        handler = getattr(self, handler_name, None)
        if handler is None:
            return ()

        return handler(event, context)

    # -----------------------------------------------------------------
    # Category handlers
    # -----------------------------------------------------------------

    def _normalize_movement(
        self,
        event: RawEvent,
        context: BehaviorNormalizationContext,
    ) -> tuple[BehaviorEvent, ...]:
        """MovementEvent → movement/travel."""
        run_id = _run_id(event, context)
        return (
            BehaviorEvent(
                run_id=run_id,
                tick=event.tick,
                entity_id=event.entity_id,
                behavior_category="movement",
                behavior_family="travel",
                action_type=event.event_type,
                source_event_ids=(_event_id(event),),
                subject=context.entity_subject_map.get(event.entity_id or -1),
                route_family=context.route_family_map.get(event.entity_id or -1),
                payload=_safe_payload(event),
            ),
        )

    def _normalize_combat(
        self,
        event: RawEvent,
        context: BehaviorNormalizationContext,
    ) -> tuple[BehaviorEvent, ...]:
        """CombatDamageEvent → combat/engage; CombatKillEvent → combat/kill_or_defeat."""
        run_id = _run_id(event, context)
        event_type = event.event_type

        if event_type == "combat_damage":
            payload = _safe_payload(event)
            outcome = "lethal" if payload.get("is_lethal") else "hit"
            return (
                BehaviorEvent(
                    run_id=run_id,
                    tick=event.tick,
                    entity_id=event.entity_id,
                    behavior_category="combat",
                    behavior_family="engage",
                    action_type=event_type,
                    outcome=outcome,
                    source_event_ids=(_event_id(event),),
                    target_id=payload.get("attacker_id"),
                    subject=context.entity_subject_map.get(event.entity_id or -1),
                    route_family=context.route_family_map.get(event.entity_id or -1),
                    payload=payload,
                ),
            )

        if event_type == "combat_kill":
            payload = _safe_payload(event)
            return (
                BehaviorEvent(
                    run_id=run_id,
                    tick=event.tick,
                    entity_id=event.entity_id,
                    behavior_category="combat",
                    behavior_family="kill_or_defeat",
                    action_type=event_type,
                    outcome="killed",
                    source_event_ids=(_event_id(event),),
                    target_id=payload.get("killer_id"),
                    subject=context.entity_subject_map.get(event.entity_id or -1),
                    route_family=context.route_family_map.get(event.entity_id or -1),
                    payload=payload,
                ),
            )

        return ()

    def _normalize_economy(
        self,
        event: RawEvent,
        context: BehaviorNormalizationContext,
    ) -> tuple[BehaviorEvent, ...]:
        """GoldTransactionEvent → trade/buy_sell_or_reward."""
        run_id = _run_id(event, context)
        payload = _safe_payload(event)
        # Prefer direct attribute (Pydantic model) over payload dict
        transaction_kind = getattr(event, "transaction_kind", None) or payload.get("transaction_kind") or event.event_type
        return (
            BehaviorEvent(
                run_id=run_id,
                tick=event.tick,
                entity_id=event.entity_id,
                behavior_category="trade",
                behavior_family="buy_sell_or_reward",
                action_type=event.event_type,
                outcome=str(transaction_kind),
                source_event_ids=(_event_id(event),),
                subject=context.entity_subject_map.get(event.entity_id or -1),
                route_family=context.route_family_map.get(event.entity_id or -1),
                payload=payload,
            ),
        )

    def _normalize_quest(
        self,
        event: RawEvent,
        context: BehaviorNormalizationContext,
    ) -> tuple[BehaviorEvent, ...]:
        """QuestEvent → quest/accept|progress|complete or failure_response/quest_failure."""
        run_id = _run_id(event, context)
        payload = _safe_payload(event)
        # Prefer direct attribute (Pydantic model) over payload dict
        status = getattr(event, "status", None) or payload.get("status") or ""

        if status == "failed":
            return (
                BehaviorEvent(
                    run_id=run_id,
                    tick=event.tick,
                    entity_id=event.entity_id,
                    behavior_category="failure_response",
                    behavior_family="quest_failure",
                    action_type=event.event_type,
                    outcome="failed",
                    source_event_ids=(_event_id(event),),
                    subject=context.entity_subject_map.get(event.entity_id or -1),
                    route_family=context.route_family_map.get(event.entity_id or -1),
                    payload=payload,
                ),
            )

        family_map = {
            "started": "accept",
            "progress": "progress",
            "completed": "complete",
        }
        family = family_map.get(status, "progress")
        return (
            BehaviorEvent(
                run_id=run_id,
                tick=event.tick,
                entity_id=event.entity_id,
                behavior_category="quest",
                behavior_family=family,
                action_type=event.event_type,
                outcome=status or None,
                source_event_ids=(_event_id(event),),
                subject=context.entity_subject_map.get(event.entity_id or -1),
                route_family=context.route_family_map.get(event.entity_id or -1),
                payload=payload,
            ),
        )

    def _normalize_lifecycle(
        self,
        event: RawEvent,
        context: BehaviorNormalizationContext,
    ) -> tuple[BehaviorEvent, ...]:
        """LifecycleEvent → progression/level_up or world_response/spawn|despawn."""
        run_id = _run_id(event, context)
        payload = _safe_payload(event)
        # Prefer direct attribute (Pydantic model) over payload dict
        action = getattr(event, "action", None) or payload.get("action") or ""

        if action == "level_up":
            return (
                BehaviorEvent(
                    run_id=run_id,
                    tick=event.tick,
                    entity_id=event.entity_id,
                    behavior_category="progression",
                    behavior_family="level_up",
                    action_type=event.event_type,
                    source_event_ids=(_event_id(event),),
                    subject=context.entity_subject_map.get(event.entity_id or -1),
                    payload=payload,
                ),
            )

        if action in ("spawn", "despawn"):
            return (
                BehaviorEvent(
                    run_id=run_id,
                    tick=event.tick,
                    entity_id=event.entity_id,
                    behavior_category="world_response",
                    behavior_family=action,
                    action_type=event.event_type,
                    source_event_ids=(_event_id(event),),
                    subject=context.entity_subject_map.get(event.entity_id or -1),
                    payload=payload,
                ),
            )

        # Other lifecycle actions — skip, don't produce unknown_behavior noise
        return ()

    def _normalize_resource(
        self,
        event: RawEvent,
        context: BehaviorNormalizationContext,
    ) -> tuple[BehaviorEvent, ...]:
        """Resource events → resource_gathering/gather."""
        run_id = _run_id(event, context)
        return (
            BehaviorEvent(
                run_id=run_id,
                tick=event.tick,
                entity_id=event.entity_id,
                behavior_category="resource_gathering",
                behavior_family="gather",
                action_type=event.event_type,
                source_event_ids=(_event_id(event),),
                subject=context.entity_subject_map.get(event.entity_id or -1),
                route_family=context.route_family_map.get(event.entity_id or -1),
                payload=_safe_payload(event),
            ),
        )

    def _normalize_strategy(
        self,
        event: RawEvent,
        context: BehaviorNormalizationContext,
    ) -> tuple[BehaviorEvent, ...]:
        """Strategy events → preparation/plan or information_seeking/evaluate."""
        run_id = _run_id(event, context)
        event_type = event.event_type
        if "plan" in event_type or "route" in event_type:
            family = "plan"
            category = "preparation"
        else:
            family = "evaluate"
            category = "information_seeking"

        return (
            BehaviorEvent(
                run_id=run_id,
                tick=event.tick,
                entity_id=event.entity_id,
                behavior_category=category,
                behavior_family=family,
                action_type=event_type,
                source_event_ids=(_event_id(event),),
                subject=context.entity_subject_map.get(event.entity_id or -1),
                payload=_safe_payload(event),
            ),
        )

    def _normalize_social(
        self,
        event: RawEvent,
        context: BehaviorNormalizationContext,
    ) -> tuple[BehaviorEvent, ...]:
        """Social events → cooperation/cooperate or avoidance/avoid."""
        run_id = _run_id(event, context)
        return (
            BehaviorEvent(
                run_id=run_id,
                tick=event.tick,
                entity_id=event.entity_id,
                behavior_category="cooperation",
                behavior_family="cooperate",
                action_type=event.event_type,
                source_event_ids=(_event_id(event),),
                subject=context.entity_subject_map.get(event.entity_id or -1),
                payload=_safe_payload(event),
            ),
        )

    def _normalize_region(
        self,
        event: RawEvent,
        context: BehaviorNormalizationContext,
    ) -> tuple[BehaviorEvent, ...]:
        """Region events → world_response/region_change."""
        run_id = _run_id(event, context)
        return (
            BehaviorEvent(
                run_id=run_id,
                tick=event.tick,
                entity_id=event.entity_id,
                behavior_category="world_response",
                behavior_family="region_change",
                action_type=event.event_type,
                source_event_ids=(_event_id(event),),
                subject=context.entity_subject_map.get(event.entity_id or -1),
                payload=_safe_payload(event),
            ),
        )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _event_id(event: RawEvent) -> str:
    """Extract a stable event ID from any supported event type."""
    return getattr(event, "event_id", "") or ""


def _run_id(event: RawEvent, context: BehaviorNormalizationContext) -> str:
    """Resolve the run_id, preferring the context's run_id."""
    return context.run_id or getattr(event, "run_id", None) or "unknown_run"


def _safe_payload(event: RawEvent) -> dict:
    """
    Extract a small payload dict from the event without copying full state.
    For envelope types, use the existing payload dict.
    For Pydantic model types, build a lightweight dict of known safe fields.
    """
    # ObservabilityEventEnvelope has a .payload mapping already
    if isinstance(event, ObservabilityEventEnvelope):
        return dict(event.payload)

    # SimulationEvent is Pydantic — extract the .payload dict directly.
    # We explicitly avoid calling .dict() / .model_dump() to prevent
    # accidentally copying large embedded objects.
    raw = getattr(event, "payload", None)
    if isinstance(raw, dict):
        return dict(raw)

    # Fallback: construct a minimal payload from known safe scalar fields
    payload: dict = {}
    for attr in ("status", "transaction_kind", "action", "amount", "is_lethal", "attacker_id", "killer_id"):
        val = getattr(event, attr, None)
        if val is not None:
            payload[attr] = val
    return payload

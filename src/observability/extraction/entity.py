"""The per-entity event sequence of one extract() call, in the order the old single method emitted it."""

from __future__ import annotations

from typing import Any

from src.observability.events import SimulationEvent
from src.observability.extraction.capability import capability_events
from src.observability.extraction.combat import (
    damage_events,
    hazard_drain_events,
    initiated_events,
    kill_events,
    near_death_events,
)
from src.observability.extraction.context import ExtractContext
from src.observability.extraction.contracts import contract_events
from src.observability.extraction.economy import gold_events, intent_result_events
from src.observability.extraction.leads import lead_events
from src.observability.extraction.lifecycle import movement_events
from src.observability.extraction.progression import (
    evolution_events,
    progression_events,
    xp_events,
)
from src.observability.extraction.quests import quest_events
from src.observability.extraction.social import group_events, social_memory_events
from src.observability.extraction.strategy import belief_events, route_events
from src.observability.extraction.vitals import vitals_events


def _agency_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """Agency, cognition and economy events derived from the entity's EntityUpdate."""
    events: list[SimulationEvent] = []
    update = ctx.update
    e_upd_ext = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
    if e_upd_ext is not None:
        events.extend(route_events(ctx, eid, e_upd_ext))
        events.extend(belief_events(ctx, eid, e_upd_ext))
        events.extend(intent_result_events(ctx, eid, entity, prior_ent, e_upd_ext))
        events.extend(hazard_drain_events(ctx, eid, e_upd_ext))
    return events


def entity_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """Every event of an entity present in both states, one domain after another."""
    events: list[SimulationEvent] = []
    events.extend(movement_events(ctx, eid, entity, prior_ent))
    events.extend(vitals_events(ctx, eid, entity, prior_ent))
    events.extend(damage_events(ctx, eid, entity, prior_ent))
    events.extend(kill_events(ctx, eid, entity, prior_ent))
    events.extend(initiated_events(ctx, eid, entity, prior_ent))
    events.extend(near_death_events(ctx, eid, entity, prior_ent))
    events.extend(xp_events(ctx, eid, entity, prior_ent))
    events.extend(evolution_events(ctx, eid, entity, prior_ent))
    events.extend(gold_events(ctx, eid, entity, prior_ent))
    events.extend(_agency_events(ctx, eid, entity, prior_ent))
    events.extend(lead_events(ctx, eid, entity, prior_ent))
    events.extend(group_events(ctx, eid, entity, prior_ent))
    events.extend(social_memory_events(ctx, eid, entity, prior_ent))
    events.extend(contract_events(ctx, eid, entity, prior_ent))
    events.extend(quest_events(ctx, eid, entity, prior_ent))
    events.extend(progression_events(ctx, eid, entity, prior_ent))
    events.extend(capability_events(ctx, eid, entity, prior_ent))
    return events

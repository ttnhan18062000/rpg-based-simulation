"""EventExtractor: the facade that turns a state transition into curated SimulationEvents; the per-domain code is in src/observability/extraction/."""
from __future__ import annotations

import time
from typing import Any, List

from src.core.state import AuthoritativeState
from src.core.strategic import ProjectStatus
from src.domains.commitment.abandonment import AbandonmentCategory, AbandonmentEvaluator
from src.domains.world_emergence.schema import WorldEventCategory
from src.observability.config import ObservabilityMode
from src.observability.divergence_episode import DivergenceEpisodes
from src.observability.entity_kind_constants import BOSS_ENTITY_KINDS, SPAWN_CADENCE_EXCLUDED_KINDS
from src.observability.events import SimulationEvent
from src.observability.extraction.combat import (
    NEAR_DEATH_THRESHOLD as _NEAR_DEATH_THRESHOLD,
)
from src.observability.extraction.combat import (
    real_combat_update as _real_combat_update,
)
from src.observability.extraction.context import ExtractContext
from src.observability.extraction.entity import entity_events
from src.observability.extraction.faction import (
    faction_extinct_events,
    faction_update_events,
)
from src.observability.extraction.leads import BELIEF_STALE_TICKS as _BELIEF_STALE_TICKS
from src.observability.extraction.leads import CERTAINTY_FLOAT as _CERTAINTY_FLOAT
from src.observability.extraction.leads import (
    NON_SURVIVAL_PROJECT_KINDS as _NON_SURVIVAL_PROJECT_KINDS,
)
from src.observability.extraction.lifecycle import despawn_events, spawn_events
from src.observability.extraction.progression import (
    XP_PLATEAU_TICKS as _XP_PLATEAU_TICKS,
)
from src.observability.extraction.resources import (
    conservation_events,
    ecology_events,
    resource_node_events,
    spawn_cadence_events,
)
from src.observability.extraction.strategy import rejection_cascade_events
from src.observability.extraction.world import (
    boss_spawn_events,
    calamity_events,
    region_update_events,
)
from src.systems.strategic_systems.intelligence import _MAX_CONSECUTIVE_REJECTIONS

# These private names are imported by src/observability/event_shapers.py and tests; they now live in src/observability/extraction/.
__all__ = ["BOSS_ENTITY_KINDS", "SPAWN_CADENCE_EXCLUDED_KINDS", "EventExtractor", "_BELIEF_STALE_TICKS", "_CERTAINTY_FLOAT", "_NEAR_DEATH_THRESHOLD", "_NON_SURVIVAL_PROJECT_KINDS", "_XP_PLATEAU_TICKS", "_real_combat_update"]


# Faction events from WorldEvent domain objects (PP-10/11)
_MILITARY_RESOLVED = frozenset({
    WorldEventCategory.TERRITORY_TRANSFERRED,
    WorldEventCategory.WAR_ENDED_EXHAUSTION,
})


def _abandonment_events(ctx: ExtractContext, eid: int, entity: Any, qid: Any, states: tuple[Any, Any]) -> list[SimulationEvent]:
    """commitment_abandoned for a project that turned ABANDONED (rollback path only); ``states`` is (prior_qstate, qstate)."""
    tick = ctx.tick
    _push_shapers_agency_active = ctx.push_shapers_agency_active
    events: list[SimulationEvent] = []
    prior_qstate, qstate = states
    # Agency: commitment_abandoned (behavioral classification, not just status
    # change — coexists with the QuestEvent above which becomes project_abandoned via
    # _TRANSLATE_CONDITIONAL in quality_hub.py) — generic to ANY project kind, keyed
    # on the generic ProjectStatus field, deliberately independent of the
    # QuestState-only gate above. Flag-gated (TCK-20260807-COMMITMENT-ABANDONED-PUSH-
    # MIGRATION-GAP): live behind AgencyShaper when ENABLE_PUSH_EVENT_SHAPERS_AGENCY is
    # "ON" (default); the branch below is the rollback path.
    if not _push_shapers_agency_active and prior_qstate is not None and (
            getattr(prior_qstate, "status", None) != ProjectStatus.ABANDONED
            and getattr(qstate, "status", None) == ProjectStatus.ABANDONED):
        _hp = getattr(getattr(entity, "combat", None), "hp", 100)
        _max_hp = getattr(getattr(entity, "combat", None), "max_hp", 100)
        _classification = AbandonmentEvaluator.evaluate_abandonment(
            _hp, _max_hp,
            is_party_in_combat=False,   # Q1: default; see plan decisions
            is_greed_driven=False,       # Q1: default; see plan decisions
        )
        if _classification.category != AbandonmentCategory.SURVIVAL:
            events.append(SimulationEvent(
                event_type="commitment_abandoned", event_category="strategy",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={
                    "entity_id": eid,
                    "project_id": qid,
                    "category": _classification.category.value,
                    "penalty": _classification.penalty,
                    "tick": tick,
                },
            ))
    return events


def _military_events(ctx: ExtractContext, we: Any, cat: Any) -> list[SimulationEvent]:
    """war_declared and military_conflict_resolved (rollback path only)."""
    tick = ctx.tick
    _push_shapers_active = ctx.push_shapers_active
    events: list[SimulationEvent] = []
    # war_declared/military_conflict_resolved specifically are migrated (FACTION), flag-
    # gated (TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION) — but this loop ALSO
    # produces world_emergence_event/narrative_milestone (NARRATIVE, out of migration
    # scope) below, which must stay fully unconditional. Only this if/elif is guarded, not
    # the whole loop.
    if _push_shapers_active:
        pass
    elif cat == WorldEventCategory.FACTION_WAR_DECLARED:
        events.append(SimulationEvent(
            event_type="war_declared", event_category="faction",
            tick=tick, entity_id=None, severity="CRITICAL",
            source_system="event_extractor", message="",
            payload={"faction_pair": str(getattr(we, "subject", ""))},
        ))
    elif cat in _MILITARY_RESOLVED:
        events.append(SimulationEvent(
            event_type="military_conflict_resolved", event_category="faction",
            tick=tick, entity_id=None, severity="WARNING",
            source_system="event_extractor", message="",
            payload={
                "subject": str(getattr(we, "subject", "")),
                "category": str(cat),
            },
        ))
    return events


def _emergence_events(ctx: ExtractContext, we: Any, cat: Any) -> list[SimulationEvent]:
    """world_emergence_event and the narrative_milestone war and sovereignty variants (rollback path only)."""
    tick = ctx.tick
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # NARRATIVE: world_emergence_event — one per WorldEvent in world_events_add (D1).
    # narrative_milestone (war/sovereignty variant) below too. Both migrated to
    # WorldDynamicsShaper — flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2), live when
    # ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this pair is the rollback path.
    # Only these two constructs are guarded, not the whole loop — the war_declared/
    # military_conflict_resolved if/elif above (Phase 1, ENABLE_PUSH_EVENT_SHAPERS) stays
    # independently gated by its own, separate flag, untouched here.
    if not _push_shapers_phase2_active:
        events.append(SimulationEvent(
            event_type="world_emergence_event",
            event_category="lifecycle",
            tick=tick,
            entity_id=None,
            severity="INFO",
            source_system="event_extractor",
            message="",
            payload={
                "category": str(cat) if cat else "",
                "region_id": str(getattr(we, "region_id", "") or ""),
                "subject": str(getattr(we, "subject", "") or ""),
            },
        ))

        # NARRATIVE: narrative_milestone — war and sovereignty (D2)
        if cat == WorldEventCategory.FACTION_WAR_DECLARED:
            events.append(SimulationEvent(
                event_type="narrative_milestone",
                event_category="lifecycle",
                tick=tick,
                entity_id=None,
                severity="WARNING",
                source_system="event_extractor",
                message="",
                payload={
                    "milestone": "first_war",
                    "subject": str(getattr(we, "subject", "") or ""),
                },
            ))
        elif cat == WorldEventCategory.SOVEREIGNTY_SHIFT:
            events.append(SimulationEvent(
                event_type="narrative_milestone",
                event_category="lifecycle",
                tick=tick,
                entity_id=None,
                severity="WARNING",
                source_system="event_extractor",
                message="",
                payload={
                    "milestone": "first_sovereignty_transfer",
                    "region_id": str(getattr(we, "region_id", "") or ""),
                },
            ))
    return events


def world_event_events(ctx: ExtractContext) -> list[SimulationEvent]:
    """Events derived from WorldEvent records added this tick."""
    update = ctx.update
    events: list[SimulationEvent] = []
    _world_evts = getattr(update, "world_events_add", None)
    if not isinstance(_world_evts, (list, tuple)):
        _world_evts = ()
    for we in _world_evts:
        cat = getattr(we, "category", None)
        events.extend(_military_events(ctx, we, cat))
        events.extend(_emergence_events(ctx, we, cat))
    return events


def _building_sabotaged_events(ctx: ExtractContext) -> list[SimulationEvent]:
    """building_sabotaged (rollback path only). Kept here: Kernel imports this module, so the Kernel import must stay local."""
    events: list[SimulationEvent] = []
    update = ctx.update
    tick = ctx.tick
    current_state = ctx.current_state
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    # World: building_sabotaged — building took sabotage damage (hp_delta < 0 discriminates
    # BuildingSabotageSystem.resolve() from town_resolution.py's insolvency writes, which only
    # ever set functional_set=False with no hp_delta). Flag-gated
    # (TCK-20260806-PUSH-CUTOVER-PHASE2), same rollback pattern.
    for b_id, b_upd in ([] if _push_shapers_phase2_active else (getattr(update, "building_updates", None) or {}).items()):
        if getattr(b_upd, "hp_delta", 0.0) is not None and getattr(b_upd, "hp_delta", 0.0) < 0:
            from src.engine.kernel import Kernel
            _region = Kernel.get_building_region(current_state, b_id) if current_state else None
            events.append(SimulationEvent(
                event_type="building_sabotaged", event_category="region",
                tick=tick, entity_id=None, severity="WARNING",
                source_system="event_extractor", message="",
                payload={"building_id": b_id, "hp_delta": b_upd.hp_delta,
                         "region_id": _region.id if _region else None},
            ))
    return events


def _resolve_push_flags(prior_state: AuthoritativeState) -> tuple[bool, bool, bool, bool]:
    """The four rollback flags (phase 1, phase 2, quest, agency), each True while its flag is "ON" (the default when unset)."""
    # TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION: COMBAT/ECONOMY/FACTION event
    # emission moved to src/observability/event_shapers.py's apply-layer shaper registry,
    # delivered live by Kernel._phase_observability() when this flag is "ON" (the default —
    # see FeatureFlagManager). The branches below stay in this file, flag-gated, as a real
    # rollback path: set ENABLE_PUSH_EVENT_SHAPERS to anything other than "ON" to restore
    # exact pre-cutover diffing behavior for these 3 domains. Default "ON" (not falling back
    # to the old path) when feature_flags is absent/doesn't override — matches
    # FeatureFlagManager's own new default, so an unconfigured run gets the current default
    # behavior, not a silent revert to pre-cutover diffing.
    _push_shapers_active = (getattr(prior_state, "feature_flags", None) or {}).get(
        "ENABLE_PUSH_EVENT_SHAPERS", "ON") == "ON"

    # Phase 2 cutover (TCK-20260806-PUSH-CUTOVER-PHASE2): same rollback pattern as
    # _push_shapers_active above, but on the SEPARATE ENABLE_PUSH_EVENT_SHAPERS_PHASE2 flag —
    # NOT the same flag reused, contrary to this epic's own original premise. Phase 2's
    # shapers live in a separate PHASE2_SHAPER_REGISTRY specifically because
    # ENABLE_PUSH_EVENT_SHAPERS already defaulted "ON" by the time Phase 2 began (Phase 1's
    # own cutover), so registering into the same registry/flag would have delivered
    # immediately with no SHADOW window — a real bug found and fixed during
    # TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY's own build. Default "ON" for the same reason
    # _push_shapers_active defaults "ON": this cutover ticket is what flips the *default*
    # (feature_flags.py), so an unconfigured run gets the new default behavior, not a silent
    # revert.
    _push_shapers_phase2_active = (getattr(prior_state, "feature_flags", None) or {}).get(
        "ENABLE_PUSH_EVENT_SHAPERS_PHASE2", "ON") == "ON"

    # Quest cutover (TCK-20260807-QUEST-EVENT-PUSH-MIGRATION): same rollback pattern as
    # _push_shapers_active/_push_shapers_phase2_active above, on its OWN
    # ENABLE_PUSH_EVENT_SHAPERS_QUEST flag — NOT the Phase 2 flag (already ON, would give no
    # SHADOW window, the same reason Phase 2 needed its own flag distinct from Phase 1's).
    # Gates ONLY the quest_event construction below, NOT commitment_abandoned (a separate,
    # not-yet-migrated signal, tracked by TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP).
    _push_shapers_quest_active = (getattr(prior_state, "feature_flags", None) or {}).get(
        "ENABLE_PUSH_EVENT_SHAPERS_QUEST", "ON") == "ON"

    # Agency cutover (TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP,
    # TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP): same rollback pattern as the
    # flags above, on its OWN ENABLE_PUSH_EVENT_SHAPERS_AGENCY flag — gates commitment_abandoned
    # and rejection_cascade_tick, the last 2 real push-migration gaps found in this file.
    _push_shapers_agency_active = (getattr(prior_state, "feature_flags", None) or {}).get(
        "ENABLE_PUSH_EVENT_SHAPERS_AGENCY", "ON") == "ON"
    return (_push_shapers_active, _push_shapers_phase2_active, _push_shapers_quest_active, _push_shapers_agency_active)


class EventExtractor:
    """Extracts curated low-volume SimulationEvents from state changes and committed updates."""

    # Per-run tracking for route novelty: entity_id → set of seen family strings.
    # NOT durable state — must be cleared at run start via reset_run_state().
    _seen_routing_families: dict[int, set[str]] = {}

    # Progression: entity_id → last tick XP was granted (for plateau detection)
    _last_xp_tick: dict[int, int] = {}
    # Entities already emitted progression_plateau this run
    _emitted_plateau: set[int] = set()
    # Leads already emitted as stale this run: entity_id → set of lead_ids
    _emitted_stale_leads: dict[int, set[str]] = {}
    # Social memory: (entity_id, other_entity_id) pairs already emitted this run
    _emitted_social_memory: set[tuple[int, int]] = set()
    # Contract milestones: "{contract_id}:{label}" keys already emitted this run
    _emitted_contract_milestones: set[str] = set()

    # Capability trend / life-arc coherence (TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE):
    # entity_id → last tick any of level/skills/gear/gold moved. Initialized to first-observed
    # tick (not 0) so an entity first seen mid-run isn't immediately treated as stalled.
    _last_capability_growth_tick: dict[int, int] = {}
    _emitted_capability_stalled: set[int] = set()

    _SOCIAL_MEMORY_THRESHOLD = 0.3  # minimum trust_history delta to emit
    _CONTRACT_MILESTONE_THRESHOLDS = ((0.25, "25%"), (0.50, "50%"), (0.75, "75%"))

    @classmethod
    def reset_run_state(cls) -> None:
        """Clear transient per-run state. Call at run start and in test teardown."""
        cls._seen_routing_families.clear()
        cls._last_xp_tick.clear()
        cls._emitted_plateau.clear()
        cls._emitted_stale_leads.clear()
        cls._emitted_social_memory.clear()
        cls._emitted_contract_milestones.clear()
        cls._last_capability_growth_tick.clear()
        cls._emitted_capability_stalled.clear()
        DivergenceEpisodes.reset_run_state()

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

        shapers, shapers_phase2, shapers_quest, shapers_agency = _resolve_push_flags(prior_state)
        tick = current_state.tick
        now = time.time()
        events: List[SimulationEvent] = []
        ctx = ExtractContext(
            prior_state=prior_state, current_state=current_state, update=update, mode=mode, tick=tick, now=now,
            push_shapers_active=shapers, push_shapers_phase2_active=shapers_phase2,
            push_shapers_quest_active=shapers_quest, push_shapers_agency_active=shapers_agency,
            max_consecutive_rejections=_MAX_CONSECUTIVE_REJECTIONS, run_state=EventExtractor,
            abandonment_events=_abandonment_events,
        )

        # Optimization: Scoped comparison using dirty entity IDs
        dirty_entity_ids = update.entity_updates.keys() if (update and hasattr(update, "entity_updates")) else []
        if not dirty_entity_ids:
            dirty_entity_ids = current_state.entities.keys()

        for eid in dirty_entity_ids:
            entity = current_state.entities.get(eid)
            prior_ent = prior_state.entities.get(eid)
            if entity is None:
                events.extend(despawn_events(ctx, eid, prior_ent))
                continue
            if prior_ent is None:
                events.extend(spawn_events(ctx, eid, entity))
                continue
            events.extend(entity_events(ctx, eid, entity, prior_ent))

        events.extend(rejection_cascade_events(ctx))
        events.extend(resource_node_events(ctx))
        events.extend(ecology_events(ctx))
        events.extend(spawn_cadence_events(ctx))
        events.extend(conservation_events(ctx, events))
        events.extend(region_update_events(ctx))
        events.extend(_building_sabotaged_events(ctx))
        events.extend(calamity_events(ctx))
        events.extend(boss_spawn_events(ctx))
        events.extend(faction_update_events(ctx))
        events.extend(world_event_events(ctx))
        events.extend(faction_extinct_events(ctx))
        return events

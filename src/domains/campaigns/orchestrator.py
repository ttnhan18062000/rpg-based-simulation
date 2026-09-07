"""
src/domains/campaigns/orchestrator.py
────────────────────────────────────────────────────────────────────────────────
CampaignOrchestrator — drives a sequence of episodes defined by a CampaignManifest.

Implements Epic 3.2C: multi-episode orchestration with carry-forward rules.

Carry-forward rules (all enabled by default via CarryForwardRules):
  - Entity XP, level, equipment, reputation → carried forward
  - Entity injury/alive state → entity.lifecycle.active (NOT combat.alive)
  - Dead entities (alive=False) → carried in persistent_entities but NOT spawned
  - Destroyed factions → FactionCarryForward(alive=False) → excluded from spawn
  - Surviving factions → tension/alive state carried forward

Episode RNG seed determinism: episode N uses seed = CampaignManifest.base_seed + N.
Both AuthoritativeState.seed and DeterministicRNG use this value (INFRA-101/102).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.scenarios.schema import SimulationScenarioDefinition
    from src.observability.event_recorder import EventRecorder

from src.domains.campaigns.state import (
    CampaignState,
    EntityCarryForward,
    EpisodeSummary,
    FactionCarryForward,
    NarrativeLedgerEntry,
)
from src.domains.campaigns.plan_revision import PlanRevisionService
from src.domains.campaigns.progression_plan import (
    ProgressionPlan,
    ProgressionPlanExporter,
    ProgressionPlanImporter,
)
from src.domains.campaigns.social_memory import (
    SocialMemoryRecord,
    SocialMemoryExporter,
    SocialMemoryImporter,
)
from src.domains.campaigns.grief_urgency import (
    GriefUrgencyImporter, ALLY_TRUST_THRESHOLD,
    NemesisRelationImporter, NEMESIS_EPISODE_COUNT, NEMESIS_INTERACTION_KINDS,
)
from src.domains.campaigns.state import GriefUrgencyModifier, NemesisRelation
from src.domains.culture.exporter import CultureDriftImporter
from src.domains.culture.settlement_personality import (
    SettlementPersonalityDescriptor,
    SettlementPersonalityService,
)


# ── Narrative significance map ────────────────────────────────────────────────
# Maps WorldEventCategory.value → (event_type, significance).
# Only categories listed here produce NarrativeLedgerEntry records.
# significance scale: quest_completed=0.7, entity_death=0.5, faction_shift=0.9
_SIGNIFICANCE_MAP: Dict[str, tuple] = {
    "ENTITY_DEATH":    ("entity_death",    0.5),
    "QUEST_COMPLETED": ("quest_completed", 0.7),
    "CAMP_CLEARED":    ("faction_shift",   0.9),
    "CAMP_RAID":       ("faction_shift",   0.6),
    "PARTY_ABANDONED": ("entity_death",    0.4),
    "QUEST_FAILED":          ("quest_completed", 0.3),
    # E53Bd: Diplomatic transition events
    "FACTION_WAR_DECLARED":  ("war_declared",   0.95),
    "FACTION_ALLIANCE_FORMED": ("alliance_formed", 0.80),
    "FACTION_PEACE_TREATY":  ("peace_treaty",   0.75),
    # E53Cc: Territory transfer event
    "TERRITORY_TRANSFERRED": ("territory_transferred", 0.85),
    # E53Cd: War exhaustion peace resolution
    "WAR_ENDED_EXHAUSTION": ("war_ended_exhaustion", 0.80),
    # E53Db: Siege onset and betrayal
    "SIEGE_BEGINS": ("siege_begins", 0.80),
    "BETRAYAL":     ("betrayal",     0.85),
}

# ── Types ─────────────────────────────────────────────────────────────────────


@dataclass
class CarryForwardRules:
    """Boolean toggles controlling which entity/faction data carries between episodes.

    All fields default to True (full carry-forward). Set to False to disable a
    specific category — e.g., carry_equipment=False for a permadeath campaign.
    """

    carry_xp: bool = True
    carry_level: bool = True
    carry_equipment: bool = True
    carry_reputation: bool = True
    carry_injury: bool = True  # alive=False entities carried but not spawned
    carry_faction_state: bool = True  # faction tension and alive status carried


@dataclass(frozen=True)
class CampaignManifest:
    """Orchestration-layer campaign definition.

    Distinct from the analysis-domain CampaignSpec in src/domains/campaigns/schema.py.
    CampaignManifest owns: the ordered episode sequence, the base RNG seed, and
    the carry-forward rule set.

    Episode seed derivation: episode N uses seed = base_seed + N (deterministic).
    """

    id: str
    episodes: List["SimulationScenarioDefinition"]
    base_seed: int = 0
    carry_forward_rules: CarryForwardRules = field(
        default_factory=CarryForwardRules
    )


# ── Orchestrator ───────────────────────────────────────────────────────────────


class CampaignOrchestrator:
    """Drives a sequence of episodes defined by a CampaignManifest.

    Owns one CampaignState across the full campaign lifetime.
    Each call to run_episode() runs episode N, extracts carry-forward data,
    updates CampaignState, and increments episode_index.

    Usage::

        manifest = CampaignManifest(id="my_campaign", episodes=[spec0, spec1, spec2])
        orchestrator = CampaignOrchestrator(manifest)
        summary0 = orchestrator.run_episode()   # episode 0
        summary1 = orchestrator.run_episode()   # episode 1
        assert len(orchestrator.state.episode_history) == 2
    """

    def __init__(
        self,
        manifest: CampaignManifest,
        event_recorder: Optional["EventRecorder"] = None,
    ) -> None:
        self._manifest = manifest
        self._event_recorder = event_recorder
        self._state = CampaignState(
            campaign_id=manifest.id,
            episode_index=0,
        )

    @property
    def state(self) -> CampaignState:
        """Current mutable CampaignState. Read-only property; do not replace."""
        return self._state

    def describe_settlement_personality(self, region_id: str) -> SettlementPersonalityDescriptor:
        """Pure read: settlement-personality signal for a region from carried-forward culture.

        Composes CultureDriftImporter.get_culture() + SettlementPersonalityService.describe().
        Does not read or mutate episode_index, persistent_entities, or narrative_ledger, and
        never calls _build_initial_state()/_advance_state() — this is a query over
        already-populated CampaignState.region_cultures, not an episode-boundary hook.
        """
        culture = CultureDriftImporter.get_culture(self._state, region_id)
        return SettlementPersonalityService.describe(culture)

    def run_episode(self) -> EpisodeSummary:
        """Run the current episode and return its summary.

        Raises RuntimeError if episode_index >= len(episodes).
        """
        idx = self._state.episode_index
        if idx >= len(self._manifest.episodes):
            raise RuntimeError(
                f"No more episodes: campaign '{self._manifest.id}' has "
                f"{len(self._manifest.episodes)} episode(s), "
                f"episode_index is {idx}."
            )

        spec = self._manifest.episodes[idx]
        episode_seed = self._manifest.base_seed + idx

        initial_state = self._build_initial_state(episode_seed)

        # Deferred import avoids circular import and module-level engine construction.
        from src.engine.scenario_runtime import ScenarioRuntimeService

        svc = ScenarioRuntimeService(
            spec, initial_state=initial_state, event_recorder=self._event_recorder
        )
        try:
            svc.start()
            episode_run_id = svc.run_id
            svc.flush_pending_grief_triggers()  # last-tick death: drain before final_state read
            final = svc.final_state  # AuthoritativeState after terminal tick
            completed_tick = svc.tick
        finally:
            svc.abort()  # Shuts down kernel worker threads; idempotent.

        summary = EpisodeSummary(
            episode_index=idx,
            completed_tick=completed_tick,
            run_id=episode_run_id or "",
        )
        self._advance_state(final, summary)
        return summary

    # ── state transitions ──────────────────────────────────────────────────────

    def _advance_state(
        self,
        final_state: "AuthoritativeState",
        summary: EpisodeSummary,
    ) -> None:
        """Update CampaignState from completed episode's final kernel state."""
        entity_cfs = self._extract_entity_carry_forwards(final_state)
        faction_cfs = self._extract_faction_carry_forwards(final_state)
        narrative_entries = self._extract_narrative_entries(final_state, summary.episode_index)
        social_memories = self._extract_social_memories(final_state, summary.episode_index)

        progression_plans = self._export_progression_plans(entity_cfs)

        self._state.persistent_entities.update(entity_cfs)
        self._state.persistent_factions.update(faction_cfs)
        self._state.episode_history.append(summary)
        self._state.narrative_ledger.extend(narrative_entries)
        self._emit_chronicle_events(narrative_entries, tick=getattr(summary, "completed_tick", 0))
        self._state.social_memories.update(social_memories)
        self._state.progression_plans.update(progression_plans)
        # E43F: grief urgency — detect new grief from entity_death entries, decay existing.
        self._advance_grief_urgencies(
            narrative_entries, summary.episode_index, tick=getattr(summary, "completed_tick", 0)
        )
        # E43G: nemesis relations — scan social memories for repeated antagonism.
        self._advance_nemesis_relations(
            summary.episode_index, tick=getattr(summary, "completed_tick", 0)
        )
        # Remove plans for entities that died this episode.
        dead_ids = [eid for eid, cf in entity_cfs.items() if not cf.alive]
        for eid in dead_ids:
            self._state.progression_plans.pop(eid, None)
        # E62B: derive and persist culture drift at episode boundary.
        from src.domains.culture.exporter import CultureDriftExporter
        from src.domains.chronicle.grouper import ChronicleGrouper
        _hierarchy = ChronicleGrouper().group(list(self._state.narrative_ledger))
        CultureDriftExporter.export(self._state, _hierarchy, summary.episode_index)
        # E62-FIDELITY: derive and persist chronicle-fidelity drift at the same episode boundary.
        from src.domains.fidelity.exporter import FidelityExporter
        FidelityExporter.export(self._state, _hierarchy, summary.episode_index)
        # E-FAME: derive and persist fame drift at the same episode boundary.
        from src.domains.fame.exporter import FameExporter
        FameExporter.export(self._state, _hierarchy, summary.episode_index)
        # E63-BELIEF: derive and persist per-clan belief institutions at the same
        # episode boundary, from real LegendFacts (just exported above) and real
        # Clan membership (final_state.clans, read-only).
        from src.domains.belief_institution.exporter import BeliefInstitutionExporter
        BeliefInstitutionExporter.export(
            self._state, _hierarchy, final_state.clans, summary.episode_index
        )
        self._state.episode_index += 1

    def _advance_grief_urgencies(
        self,
        new_entries: List[NarrativeLedgerEntry],
        episode_index: int,
        tick: int = 0,
    ) -> None:
        """Detect new grief from entity_death events and decay existing modifiers (E43F).

        1. Decay all existing grief_urgencies by decay_per_episode; remove when ≤ 0.
        2. For each new entity_death entry, find alive entities with trust_score > threshold
           toward the dead entity → create GriefUrgencyModifier for that entity.
           New entries overwrite decayed ones (fresh grief is never diminished).

        Emits grief_urgency_triggered only for newly-created modifiers (Step 2), not for
        every decayed-but-still-positive existing modifier (Step 1) — giving the
        episode-boundary path the same event visibility the mid-episode path gets from
        EventExtractor.detect_grief_triggers() (TCK-20260824-GRIEF-NEMESIS-REACHABILITY).
        """
        # Step 1 — decay existing grief
        decayed: Dict[int, GriefUrgencyModifier] = {}
        for eid, gum in self._state.grief_urgencies.items():
            new_urgency = round(gum.urgency - gum.decay_per_episode, 6)
            if new_urgency > 0.0:
                decayed[eid] = GriefUrgencyModifier(
                    entity_id=eid,
                    dead_ally_id=gum.dead_ally_id,
                    episode=gum.episode,
                    urgency=new_urgency,
                    decay_per_episode=gum.decay_per_episode,
                )

        # Step 2 — detect new grief from entity_death entries
        newly_created: Dict[int, GriefUrgencyModifier] = {}
        for entry in new_entries:
            if entry.event_type != "entity_death":
                continue
            try:
                dead_id = int(entry.subject_id)
            except (ValueError, TypeError):
                continue
            for eid, mem in self._state.social_memories.items():
                trust = mem.relationship_scores.get(dead_id, 0.0)
                if trust >= ALLY_TRUST_THRESHOLD:
                    urgency = round(min(1.0, trust * 0.8), 6)
                    gum = GriefUrgencyModifier(
                        entity_id=eid,
                        dead_ally_id=dead_id,
                        episode=episode_index,
                        urgency=urgency,
                    )
                    decayed[eid] = gum
                    newly_created[eid] = gum

        self._state.grief_urgencies = decayed
        self._emit_grief_urgency_events(newly_created, tick)

    def _emit_grief_urgency_events(
        self,
        modifiers: Dict[int, GriefUrgencyModifier],
        tick: int,
    ) -> None:
        """Emit grief_urgency_triggered for each newly-created modifier.

        No-op when event_recorder is None (production default when no recorder injected,
        and the case for a test double built via object.__new__() without __init__).
        """
        if getattr(self, "_event_recorder", None) is None:
            return
        for eid, gum in modifiers.items():
            self._emit_domain_event(
                event_type="grief_urgency_triggered",
                event_category="social",
                tick=tick,
                entity_id=eid,
                payload={
                    "dead_ally_id": gum.dead_ally_id,
                    "urgency": gum.urgency,
                },
            )

    def _advance_nemesis_relations(self, episode_index: int, tick: int = 0) -> None:
        """Detect nemesis relations from cumulative social memory interaction history (E43G).

        For each entity's SocialMemoryRecord, count distinct episodes where a negative
        interaction (kind in NEMESIS_INTERACTION_KINDS) occurred with the same other entity.
        If count >= NEMESIS_EPISODE_COUNT, add/update a NemesisRelation.

        Existing nemesis relations are retained unless the interaction count drops
        (which cannot happen — interaction_history is append-only). New relations
        are added; updated relations refresh strength and antagonism_count.

        Emits nemesis_relation_formed exactly once per newly-formed relation (not on
        every episode a pre-existing relation is merely refreshed).
        """
        from collections import defaultdict

        prior_relations = self._state.nemesis_relations
        new_relations: Dict[str, NemesisRelation] = dict(prior_relations)

        for eid, mem in self._state.social_memories.items():
            # Count distinct episodes per other_entity for negative interactions
            antagonism_episodes: Dict[int, set] = defaultdict(set)
            for rec in mem.interaction_history:
                if rec.kind in NEMESIS_INTERACTION_KINDS and rec.other_entity_id is not None:
                    antagonism_episodes[rec.other_entity_id].add(rec.episode)

            for antagonist_id, episodes in antagonism_episodes.items():
                count = len(episodes)
                if count >= NEMESIS_EPISODE_COUNT:
                    key = f"{eid}:{antagonist_id}"
                    strength = round(min(1.0, count * 0.4), 6)
                    new_relations[key] = NemesisRelation(
                        protagonist_id=eid,
                        antagonist_id=antagonist_id,
                        formation_episode=new_relations[key].formation_episode
                            if key in new_relations else episode_index,
                        antagonism_count=count,
                        strength=strength,
                    )

        newly_formed = {k: v for k, v in new_relations.items() if k not in prior_relations}
        self._state.nemesis_relations = new_relations
        for relation in newly_formed.values():
            self._emit_nemesis_event(relation, tick)

    def _emit_nemesis_event(self, relation: NemesisRelation, tick: int) -> None:
        """Emit nemesis_relation_formed for a newly-formed NemesisRelation.

        No-op when event_recorder is None (production default when no recorder injected,
        and the case for a test double built via object.__new__() without __init__).
        """
        if getattr(self, "_event_recorder", None) is None:
            return
        self._emit_domain_event(
            event_type="nemesis_relation_formed",
            event_category="social",
            tick=tick,
            entity_id=relation.protagonist_id,
            payload={
                "antagonist_id": relation.antagonist_id,
                "strength": relation.strength,
            },
        )

    def _emit_chronicle_events(
        self,
        entries: List[NarrativeLedgerEntry],
        tick: int,
    ) -> None:
        """Emit chronicle_entry_created to the event bus for each new ledger entry.

        No-op when event_recorder is None (production default when no recorder injected).
        """
        if self._event_recorder is None:
            return
        for entry in entries:
            self._emit_domain_event(
                event_type="chronicle_entry_created",
                event_category="lifecycle",
                tick=tick,
                entity_id=None,
                payload={
                    "entry_id": entry.entry_id,
                    "event_type": entry.event_type,
                    "significance": entry.significance,
                    "episode": entry.episode,
                    "subject_id": entry.subject_id,
                },
            )

    def _emit_domain_event(
        self,
        event_type: str,
        event_category: str,
        tick: int,
        entity_id: Optional[int],
        payload: Dict[str, Any],
    ) -> None:
        """Construct and record a base SimulationEvent envelope.

        Single shared import site for the domains -> observability pinned exception
        (tests/architecture/test_phase18_import_boundaries.py's
        _DOMAINS_OBSERVABILITY_PINNED) -- route all campaign-orchestrator event
        emission through here instead of adding new per-call-site imports.
        """
        from src.observability.events import SimulationEvent
        self._event_recorder.record(SimulationEvent(
            event_type=event_type,
            event_category=event_category,
            tick=tick,
            entity_id=entity_id,
            severity="INFO",
            source_system="campaign_orchestrator",
            message="",
            payload=payload,
        ))

    def _extract_entity_carry_forwards(
        self,
        state: "AuthoritativeState",
    ) -> Dict[int, EntityCarryForward]:
        """Extract EntityCarryForward for every entity in the final state.

        Uses entity.lifecycle.active (NOT entity.combat.alive) for the alive field.
        Equipment EquipSlot enum keys are stringified to match the declared
        EntityCarryForward.equipment format {"slots": {...}, "durability": {...}}.
        """
        rules = self._manifest.carry_forward_rules
        result: Dict[int, EntityCarryForward] = {}

        for entity_id, entity in state.entities.items():
            if rules.carry_equipment:
                slots = {
                    slot.name: item_id
                    for slot, item_id in entity.equipment.slots.items()
                }
                durability = {
                    slot.name: dur
                    for slot, dur in entity.equipment.durability.items()
                }
            else:
                slots = {}
                durability = {}

            result[entity_id] = EntityCarryForward(
                entity_id=entity_id,
                level=entity.identity.evolution_level if rules.carry_level else 1,
                xp=entity.identity.evolution_points if rules.carry_xp else 0,
                equipment={"slots": slots, "durability": durability},
                reputation=(
                    entity.social.public_reputation if rules.carry_reputation else 0.0
                ),
                alive=entity.lifecycle.active,  # lifecycle.active, NOT combat.alive
            )

        return result

    def _extract_faction_carry_forwards(
        self,
        state: "AuthoritativeState",
    ) -> Dict[str, FactionCarryForward]:
        """Synthesize FactionCarryForward by grouping entities by faction int.

        Faction alive = at least one entity with that faction int has lifecycle.active=True.
        Faction ID string: f"faction_{faction_int}".
        Tension defaults to 0.0 — E32D will enrich this from world pressure data.
        """
        if not self._manifest.carry_forward_rules.carry_faction_state:
            return {}

        faction_alive: Dict[int, bool] = {}
        for entity in state.entities.values():
            fac_int = entity.identity.faction
            if fac_int not in faction_alive:
                faction_alive[fac_int] = False
            if entity.lifecycle.active:
                faction_alive[fac_int] = True

        return {
            f"faction_{fac_int}": FactionCarryForward(
                faction_id=f"faction_{fac_int}",
                alive=alive,
                tension=0.0,  # E32D enriches from world pressure / regional trauma
            )
            for fac_int, alive in faction_alive.items()
        }

    def _extract_narrative_entries(
        self,
        final_state: "AuthoritativeState",
        episode_index: int,
    ) -> List[NarrativeLedgerEntry]:
        """Convert AuthoritativeState.recent_world_events to NarrativeLedgerEntry records.

        Only WorldEvent categories present in _SIGNIFICANCE_MAP are recorded.
        Each entry receives a deterministic entry_id for deduplication:
            "{episode_index}:{tick}:{event_type}:{subject_id}"

        Does not mutate CampaignState — returns a list for the caller to extend.
        """
        entries: List[NarrativeLedgerEntry] = []
        world_events = getattr(final_state, "recent_world_events", [])

        for world_event in world_events:
            # Resolve category to string key robustly (handles enum or raw string).
            cat = world_event.category
            key = cat.value if hasattr(cat, "value") else str(cat)

            if key not in _SIGNIFICANCE_MAP:
                continue

            event_type, significance = _SIGNIFICANCE_MAP[key]
            subject_id = world_event.subject or ""
            entry_id = f"{episode_index}:{world_event.tick}:{event_type}:{subject_id}"

            entries.append(NarrativeLedgerEntry(
                episode=episode_index,
                tick=world_event.tick,
                event_type=event_type,
                subject_id=subject_id,
                payload=dict(world_event.payload) if world_event.payload else {},
                significance=significance,
                entry_id=entry_id,
            ))

        return entries

    def _export_progression_plans(
        self,
        entity_cfs: Dict[int, "EntityCarryForward"],
    ) -> Dict[int, ProgressionPlan]:
        """Export ProgressionPlans for alive entities at episode end.

        Dead entities have their plans dropped (handled in _advance_state caller).
        Returns only plans for alive entities that have an existing plan.
        """
        result: Dict[int, ProgressionPlan] = {}
        for entity_id, cf in entity_cfs.items():
            current_plan = self._state.progression_plans.get(entity_id)
            exported = ProgressionPlanExporter.export(entity_id, current_plan, cf.alive)
            if exported is not None:
                result[entity_id] = exported
        return result

    def _extract_social_memories(
        self,
        final_state: "AuthoritativeState",
        episode_index: int,
    ) -> Dict[int, SocialMemoryRecord]:
        """Export social memory snapshots for all entities in the final state.

        Calls SocialMemoryExporter.export() for each entity. Records are stored
        in CampaignState.social_memories and consumed by the importer at the
        start of the next episode.

        Does not mutate CampaignState — returns a dict for the caller to update.
        """
        return {
            entity_id: SocialMemoryExporter.export(entity, episode_index)
            for entity_id, entity in final_state.entities.items()
        }

    def _build_initial_state(self, episode_seed: int) -> "AuthoritativeState":
        """Construct an AuthoritativeState seeded with carry-forward entity data.

        For episode 0 (no prior persistent_entities): returns a fresh
        AuthoritativeState(tick=0, seed=episode_seed).
        For episode N>0: reconstructs EntityState objects from EntityCarryForward
        snapshots and injects them into the new state.

        Only alive entities (lifecycle.active=True) are spawned in the new episode.
        Dead entities remain in persistent_entities for history but are not injected.
        """
        from dataclasses import replace as dc_replace

        from src.core.models.inventory import EquipSlot
        from src.core.state import AuthoritativeState, EntityState
        from src.core.updates import SocialUpdate
        from src.systems.social_systems.relationships import RelationshipService

        alive_carry_forwards = {
            eid: cf
            for eid, cf in self._state.persistent_entities.items()
            if cf.alive
        }

        if not alive_carry_forwards:
            # Episode 0 or no surviving entities — start fresh.
            return AuthoritativeState(tick=0, seed=episode_seed)

        # Reconstruct minimal EntityState objects from carry-forward snapshots.
        # Fields not captured in EntityCarryForward (e.g. combat state, position,
        # current HP) are left at EntityState defaults — the scenario's setup_tags
        # and world_composition govern spawn placement.
        entities: Dict[int, EntityState] = {}
        for eid, cf in alive_carry_forwards.items():
            base = EntityState(id=eid, kind="entity")

            # Apply carried identity fields.
            identity = dc_replace(
                base.identity,
                evolution_level=cf.level,
                evolution_points=cf.xp,
            )

            # Apply carried equipment (convert string keys back to EquipSlot enum).
            raw_slots = cf.equipment.get("slots", {})
            raw_dur = cf.equipment.get("durability", {})
            slots_enum = {
                EquipSlot[k]: v
                for k, v in raw_slots.items()
                if k in EquipSlot.__members__
            }
            durability_enum = {
                EquipSlot[k]: v
                for k, v in raw_dur.items()
                if k in EquipSlot.__members__
            }
            equipment = dc_replace(
                base.equipment,
                slots=slots_enum,
                durability=durability_enum,
            )

            # Apply carried reputation.
            social = RelationshipService.process_update(
                base.social, SocialUpdate(reputation_set=cf.reputation)
            )

            entities[eid] = dc_replace(
                base,
                identity=identity,
                equipment=equipment,
                social=social,
            )

        # Apply social memory import for entities that have a prior record.
        # SocialMemoryImporter.apply() merges trust history and reputation
        # additively — it does not overwrite fields set above.
        for eid, entity in list(entities.items()):
            if eid in self._state.social_memories:
                entities[eid] = SocialMemoryImporter.apply(
                    entity, self._state.social_memories[eid]
                )

        # Apply grief urgency modifiers (E43F): inject SOCIAL_THREAT concern for
        # entities grieving a dead ally from a prior episode.
        for eid, entity in list(entities.items()):
            if eid in self._state.grief_urgencies:
                entities[eid] = GriefUrgencyImporter.apply(
                    entity, self._state.grief_urgencies[eid]
                )

        # Apply nemesis relation blockers (E43G): inject SOCIAL BlockerState for
        # each nemesis relation where the entity is the protagonist, so that the
        # FORM_PARTY route generator can block party formation with the antagonist.
        for relation in self._state.nemesis_relations.values():
            eid = relation.protagonist_id
            if eid in entities:
                entities[eid] = NemesisRelationImporter.apply(entities[eid], relation)

        # Apply progression plan import: update milestone achieved flags based
        # on carried entity level. Updates CampaignState.progression_plans in-place.
        new_episode_index = self._state.episode_index
        for eid, cf in alive_carry_forwards.items():
            if eid in self._state.progression_plans:
                updated = ProgressionPlanImporter.import_plan(
                    eid,
                    self._state.progression_plans[eid],
                    new_episode_index,
                    cf.level,
                )
                self._state.progression_plans[eid] = updated

        # Generate initial plans for alive entities that have none yet.
        for eid, cf in alive_carry_forwards.items():
            if eid not in self._state.progression_plans:
                self._state.progression_plans[eid] = PlanRevisionService.generate_initial_plan(
                    eid, cf, new_episode_index
                )

        # Detect and apply trigger-based plan revisions (mentor dead, item unavailable).
        # Emits plan_revision NarrativeLedgerEntry when a trigger fires.
        existing_entry_ids = {e.entry_id for e in self._state.narrative_ledger}
        for eid, cf in alive_carry_forwards.items():
            if eid not in self._state.progression_plans:
                continue
            sm = self._state.social_memories.get(eid)
            plan = self._state.progression_plans[eid]
            revised, ledger_entry = PlanRevisionService.detect_and_revise(
                eid, plan, cf, sm, new_episode_index, self._state.persistent_entities
            )
            self._state.progression_plans[eid] = revised
            if ledger_entry is not None and ledger_entry.entry_id not in existing_entry_ids:
                self._state.narrative_ledger.append(ledger_entry)
                self._emit_chronicle_events([ledger_entry], tick=0)
                existing_entry_ids.add(ledger_entry.entry_id)

        # E43E: evaluate cross-episode social consequences at episode-entity-spawn time.
        # Read-only — evaluate_social_consequence() never mutates entities/campaign_state;
        # emitted via self._event_recorder.record() (SimulationEvent, not WorldEvent —
        # this constructor call has no StateUpdate/ApplyPath merge step available).
        from src.systems.social_systems.consequence_events import evaluate_social_consequence

        if self._event_recorder is not None:
            for eid in sorted(entities.keys()):
                entity = entities[eid]
                faction_id = f"faction_{entity.identity.faction}"
                for event in evaluate_social_consequence(entity, faction_id, self._state, tick=0):
                    self._event_recorder.record(event)

        # TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE: snapshot idea 56's region_cultures signal
        # into per-tick-reachable state at episode start -- the real bridge GroupPhase.resolve()
        # (the one live caller of LoyaltyDriftService.compute_loyalty_pressure() via
        # effective_defection_threshold()/check_defection()) has needed since TCK-20260905-
        # DRIFTING-LOYALTY-SIGNAL shipped it with an always-0.0 default. Sorted iteration per this
        # ticket's own AC4 determinism requirement -- feeds a plain dict keyed by region_id, not an
        # unsorted set/iteration order into any durable structure's own key order.
        from src.systems.social_systems.loyalty_drift import LoyaltyDriftService

        region_loyalty_pressure = {
            region_id: LoyaltyDriftService.compute_loyalty_pressure(self._state, region_id)
            for region_id in sorted(self._state.region_cultures.keys())
        }

        # TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE: snapshot region_cultures's own
        # CultureState objects (not a derived scalar, unlike region_loyalty_pressure above) so
        # AdventureGoalScorer.score() can feed a real Culture Drift bias branch into
        # AdventureRouteScorer.score()'s personality_bias term. Same sorted-iteration
        # determinism discipline as region_loyalty_pressure immediately above.
        region_culture_states = {
            region_id: self._state.region_cultures[region_id].culture
            for region_id in sorted(self._state.region_cultures.keys())
        }

        return AuthoritativeState(
            tick=0,
            seed=episode_seed,
            entities=entities,
            region_loyalty_pressure=region_loyalty_pressure,
            region_culture_states=region_culture_states,
        )

    # ── spawn helpers ──────────────────────────────────────────────────────────

    def _get_spawn_entities(self) -> Dict[int, EntityCarryForward]:
        """Return only alive entities from persistent state (for episode spawn)."""
        return {
            eid: cf
            for eid, cf in self._state.persistent_entities.items()
            if cf.alive
        }

    def _get_spawn_factions(self) -> Dict[str, FactionCarryForward]:
        """Return only alive factions from persistent state (for episode spawn)."""
        return {
            fid: cf
            for fid, cf in self._state.persistent_factions.items()
            if cf.alive
        }

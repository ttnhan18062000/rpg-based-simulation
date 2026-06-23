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
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.scenarios.schema import SimulationScenarioDefinition

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

    def __init__(self, manifest: CampaignManifest) -> None:
        self._manifest = manifest
        self._state = CampaignState(
            campaign_id=manifest.id,
            episode_index=0,
        )

    @property
    def state(self) -> CampaignState:
        """Current mutable CampaignState. Read-only property; do not replace."""
        return self._state

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

        svc = ScenarioRuntimeService(spec, initial_state=initial_state)
        try:
            svc.start()
            final = svc.final_state  # AuthoritativeState after terminal tick
            completed_tick = svc.tick
        finally:
            svc.abort()  # Shuts down kernel worker threads; idempotent.

        summary = EpisodeSummary(
            episode_index=idx,
            completed_tick=completed_tick,
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
        self._state.social_memories.update(social_memories)
        self._state.progression_plans.update(progression_plans)
        # Remove plans for entities that died this episode.
        dead_ids = [eid for eid, cf in entity_cfs.items() if not cf.alive]
        for eid in dead_ids:
            self._state.progression_plans.pop(eid, None)
        self._state.episode_index += 1

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
            social = dc_replace(
                base.social,
                public_reputation=cf.reputation,
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
                existing_entry_ids.add(ledger_entry.entry_id)

        return AuthoritativeState(tick=0, seed=episode_seed, entities=entities)

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

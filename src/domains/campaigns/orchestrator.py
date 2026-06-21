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
)


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

        self._state.persistent_entities.update(entity_cfs)
        self._state.persistent_factions.update(faction_cfs)
        self._state.episode_history.append(summary)
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

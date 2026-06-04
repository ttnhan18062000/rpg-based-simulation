# Compliance IDs: RPG-OPT-PHASE-GRAPH, PERF-016
from __future__ import annotations
from dataclasses import dataclass
from typing import Set, Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate
    from src.engine.cadence import SystemCadence


@dataclass(frozen=True)
class PhaseMetadata:
    """
    Defines the configuration, dirty domain requirements, cadence gating,
    and skip rules for an authoritative simulation phase.
    """
    name: str
    input_domains: Set[str]
    output_domains: Set[str]
    must_run_every_tick: bool = False
    can_skip_when_no_dirty: bool = True
    cadence_property: Optional[str] = None
    must_run_when_cadence_fires: bool = False
    """If True and cadence fires this tick, bypass dirty set short-circuit.
    Use for world-level phases (e.g. town_resolution) that process ALL entities
    on their scheduled tick regardless of entity-level dirty state."""


class PhaseDependencyGraph:
    """
    Encapsulates all 17 authoritative simulation phases.
    Evaluates execution and skip policies against expanded DirtySets and system cadences.
    Logic ID: RPG-OPT-PHASE-GRAPH (Milestone 16)
    """
    PHASES: Dict[str, PhaseMetadata] = {
        "compactor": PhaseMetadata("compactor", {"all"}, {"all"}, must_run_every_tick=True),
        "trust_boundary": PhaseMetadata("trust_boundary", {"all"}, {"all"}, must_run_every_tick=True),
        "actor_validity": PhaseMetadata("actor_validity", {"all"}, {"all"}, must_run_every_tick=True),
        "contracts": PhaseMetadata("contracts", {"social", "lifecycle"}, {"social", "inventory", "strategic"}),
        "blacksmith": PhaseMetadata("blacksmith", {"inventory", "movement", "town"}, {"inventory", "resource_updates"}),
        "action_routing": PhaseMetadata("action_routing", {"strategic", "movement"}, {"movement", "combat", "interaction"}),
        "position_swaps": PhaseMetadata("position_swaps", {"movement"}, {"movement"}),
        "movement_routing": PhaseMetadata("movement_routing", {"movement"}, {"movement", "navigation"}),
        "interaction_routing": PhaseMetadata("interaction_routing", {"movement", "strategic"}, {"interaction"}),
        "interaction_enforcement": PhaseMetadata("interaction_enforcement", {"inventory", "movement", "strategic"}, {"inventory", "resource_updates", "social"}),
        "building_sabotage": PhaseMetadata("building_sabotage", {"combat", "town", "buildings"}, {"building_updates", "social"}, cadence_property="building_sabotage", must_run_when_cadence_fires=True),
        "town_resolution": PhaseMetadata("town_resolution", {"town", "movement"}, {"world_updates", "social", "inventory"}, cadence_property="town_resolution", must_run_when_cadence_fires=True),
        "world_dynamics": PhaseMetadata("world_dynamics", {"all"}, {"all"}, must_run_every_tick=True),
        "quest_rewards": PhaseMetadata("quest_rewards", {"strategic", "inventory"}, {"reward", "identity", "inventory"}),
        "shop": PhaseMetadata("shop", {"inventory", "town"}, {"inventory", "resource_updates", "social"}),
        "resource_transactions": PhaseMetadata("resource_transactions", {"inventory", "strategic"}, {"inventory", "resource_updates"}),
        "evolution": PhaseMetadata("evolution", {"biological", "combat", "attributes", "inventory"}, {"identity", "attributes"}),
        "strategic_intelligence": PhaseMetadata("strategic_intelligence", {"strategic", "combat", "biological"}, {"strategic", "task", "navigation"}),
        "near_death_hardening": PhaseMetadata("near_death_hardening", {"combat", "biological", "lifecycle"}, {"combat", "attributes"}),
        "occupancy_resolution": PhaseMetadata("occupancy_resolution", {"movement"}, {"movement", "navigation"}),
        "lifecycle": PhaseMetadata("lifecycle", {"all"}, {"all"}, must_run_every_tick=True),
        "groups": PhaseMetadata("groups", {"social", "movement", "combat", "groups"}, {"social", "group_id_set", "strategic"}, must_run_every_tick=True),
        "capacity_enforcement": PhaseMetadata("capacity_enforcement", {"all"}, {"all"}, must_run_every_tick=True),
        
        # Phase 2-8 Enhanced RPG cognitive & world emergence loop integration
        "self_model": PhaseMetadata("self_model", {"strategic", "attributes"}, {"strategic"}),
        "information_belief": PhaseMetadata("information_belief", {"strategic", "social"}, {"strategic"}),
        "cooperation": PhaseMetadata("cooperation", {"social", "strategic"}, {"social", "strategic"}),
        "adventure_decision": PhaseMetadata("adventure_decision", {"strategic", "movement"}, {"strategic"}),
        "combat_engagement": PhaseMetadata("combat_engagement", {"combat", "movement"}, {"combat", "strategic"}),
        "progression_conversion": PhaseMetadata("progression_conversion", {"attributes", "combat"}, {"attributes"}),
        "world_emergence": PhaseMetadata("world_emergence", {"all"}, {"all"}, must_run_every_tick=True)
    }

    @staticmethod
    def should_run_phase(
        phase_name: str,
        state: AuthoritativeState,
        update: StateUpdate,
        cadence: Optional[SystemCadence] = None
    ) -> bool:
        """
        Determines whether a specific phase should be executed for the current tick.
        """
        if phase_name not in PhaseDependencyGraph.PHASES:
            return True

        phase = PhaseDependencyGraph.PHASES[phase_name]

        # 1. Full scan overrides
        if update.force_full_scan or getattr(state, "_force_full_scan", False):
            return True

        # 2. Must run unconditional phases
        if phase.must_run_every_tick:
            return True

        opt_profile = getattr(state, "_opt_profile", None)
        if opt_profile:
            if opt_profile.phase_skip_policy == "NEVER_SKIP":
                return True
            if opt_profile.phase_skip_policy == "CONSERVATIVE" and state.tick % 5 == 0:
                return True


        # 3. Cadence gating
        cadence_fired = False
        if phase.cadence_property and cadence:
            cadence_val = getattr(cadence, phase.cadence_property, 1)
            from src.engine.cadence import should_run
            if not should_run(state.tick, None, cadence_val):
                return False
            cadence_fired = True

        # 3b. If cadence fires and phase bypasses dirty check, run immediately
        if cadence_fired and phase.must_run_when_cadence_fires:
            return True

        # 4. Dirty set short-circuiting
        if update.dirty_set is None:
            return True

        ds = update.dirty_set

        has_dirty = False
        for domain in phase.input_domains:
            if domain == "movement" and ds.movement_entities: has_dirty = True
            elif domain == "combat" and ds.combat_entities: has_dirty = True
            elif domain == "inventory" and ds.inventory_entities: has_dirty = True
            elif domain == "strategic" and ds.strategic_entities: has_dirty = True
            elif domain == "social" and ds.social_entities: has_dirty = True
            elif domain == "lifecycle" and ds.lifecycle_entities: has_dirty = True
            elif domain == "biological" and ds.biological_entities: has_dirty = True
            elif domain == "attributes" and ds.attribute_entities: has_dirty = True
            elif domain == "town" and ds.town_entities: has_dirty = True
            elif domain == "buildings" and ds.building_ids: has_dirty = True
            elif domain == "groups" and ds.group_ids: has_dirty = True
            elif domain == "all" and ds.all_dirty_entities: has_dirty = True
            
            if has_dirty:
                break

        if not has_dirty and phase.can_skip_when_no_dirty:
            return False

        return True

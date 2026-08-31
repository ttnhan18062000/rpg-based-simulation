# Compliance IDs: PERF-016, STRAT-021
# Compliance IDs: SOC-045, SOC-136, STRAT-002, STRAT-003, STRAT-004, STRAT-005, STRAT-011, STRAT-050, STRAT-072, STRAT-079, STRAT-141, STRAT-148, STRAT-149, STRAT-184, STRAT-185, STRAT-186, STRAT-187, STRAT-189, STRAT-190, STRAT-196, STRAT-197, STRAT-198, STRAT-199, STRAT-200, STRAT-213, STRAT-217, STRAT-218, STRAT-234, SUB-024
# Compliance IDs: SOC-045, SOC-136, STRAT-050, STRAT-072, STRAT-079, STRAT-141, STRAT-148, STRAT-149, SUB-024
"""
Strategic Intelligence System.

Analyzes character outcomes to generate or resolve strategic markers.
Expanded in Phase 9 to support full directive/project/objective lifecycle,
interruption resistance, and cognition profile enforcement.

Covers:
- Part 1 §Strategic: Project switching uses interruption resistance / margin logic
- Part 1 §Strategic: Current project gets reservation/retention priority
"""
from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import ast
import logging

logger = logging.getLogger(__name__)

# Maximum consecutive intent failures before a stale project is abandoned.
# Rationale: D06 F3 observed 550K rejections/tick-1000 from projects that never
# make progress. N=20 caps per-project retry depth while still allowing transient
# failures to self-resolve. STRAT-234.
_MAX_CONSECUTIVE_REJECTIONS: int = 20

# Declared score ceiling for System A (AdventureRouteScorer) candidates/currents, used only to
# normalize the lock-bypass comparison below — not a hard clamp on AdventureRouteScorer's own
# output. Source: docs/mechanics/04_strategic_cognition.md §6.6 "Total non-blocked: 0.0 to ~2.9".
_ADVENTURE_ROUTE_SCORE_MAX: float = 2.9

# Declared score ceiling for System B (GoalRegistry) candidates/currents and for any kind not
# recognized as a real ProjectKind member (synthetic/test kinds default here — GoalRegistry is the
# universal per-entity baseline, the closer analogue for an unclassified score). Matches the scale
# the pre-existing "danger" bypass (score > 80) was already implicitly calibrated against.
#
# NOT a true hard ceiling: TownScorer (src/ai/goals/scorers.py) can reach ~200 and SleepScorer ~130
# (confirmed in investigation.md's own scorer survey). This constant is a calibration anchor
# continuing the pre-existing score>80 threshold, not a claim that no System B scorer exceeds it —
# a candidate from one of those two scorers can legitimately produce candidate_pct > 1.0, which is
# intentional (their real-world urgency is genuinely higher, so clearing the floor more easily is
# correct, not a bug) and does not break the comparison (no clamp exists; percentages simply aren't
# bounded to [0, 1] for these two scorers). Do not "fix" this by clamping or by raising the constant
# to 200 — that would only shift which System B scorers under-clear the floor instead.
_GOAL_UTILITY_SCORE_MAX: float = 100.0

# Generalized urgency floor for the lock-bypass gate, replacing the old `kind=='danger' and
# score > 80` special case. 0.8 == 80/100, the exact threshold the code already used before this
# ticket, expressed as a percentage of _GOAL_UTILITY_SCORE_MAX so it generalizes across kinds and
# both score systems. STRAT-186.
_INTERRUPTION_URGENCY_FLOOR_PCT: float = 0.8

# TCK-20260812-COMMITTED-INTENTION-SEQUENCE: fixed, mid-scale utility for a materialized
# CommittedIntention candidate -- above the 20.0 winner floor (intelligence.py:1412), below the
# 100.0 GoalKind scale ceiling (_GOAL_UTILITY_SCORE_MAX), so it competes as an ordinary
# mid-strength tier-5 candidate rather than a guaranteed winner or loser.
_COMMITTED_INTENTION_BASE_UTILITY: float = 50.0

if TYPE_CHECKING:
    from src.engine.cadence import SystemCadence

from src.core.state import EntityState, AuthoritativeState
from src.core.enums import EntityRole
from src.core.updates import (
    StrategicUpdate, InventoryUpdate, EntityUpdate, StateUpdate,
    CombatUpdate, BiologicalUpdate, IdentityUpdate
)
from src.engine.policy import GovernorPolicy
from src.core.strategic import (
    BlockerState, LeadState, LeadCertainty,
    ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus,
    CognitionProfile, ProjectKind, GoalKind
)
from src.engine.spatial_query import SpatialQueryService
from src.strategy.cognition_capacity import CapacityService
from src.core.inventory import InventoryService
from src.engine.cadence import should_run, SystemCadence
from src.core.movement_modes import MovementMode
from src.core.updates import NavigationUpdate, InteractionUpdate
from src.systems.world_systems.routine import RoutineService
from src.systems.world_systems.intake import ConcernIntakeSystem
from src.engine.domain_logic import SimulationDomainLogic
from src.ai.goals import GoalRegistry
from src.ai.goals.base import GoalScore
from src.ai.score_modifiers import ScoreModifierSystem
from src.domains.adventure.mapper import RouteToProjectMapper
from src.systems.party import PartyCoordinationSystem
from src.systems.strategic_systems.detour import DetourSuggestionSystem
from src.systems.strategic_systems.work_queue import StrategicWorkQueue
from src.core.dirty import get_dirty_set
from src.systems.strategic_systems.belief import BeliefCycleSystem
from src.systems.strategic_systems.town_targeting import nearest_town_tile

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState

# TCK-20260812-COMMITTED-INTENTION-SEQUENCE: the 10 pre-epic "generic" GoalKind values, each with
# a live registered scorer (src/ai/goals/__init__.py). Excludes ADVENTURE_ROUTE/SOCIAL_CONTRACT/
# REGION_STABILIZATION, which materialize through dedicated branches (:1440-1539) requiring
# synthetic metadata a committed intention has no legitimate way to populate -- MVP scope.
_COMMITTED_INTENTION_ELIGIBLE_KINDS = frozenset({
    GoalKind.HARVESTING, GoalKind.FATIGUE, GoalKind.HUNGER, GoalKind.SOCIAL,
    GoalKind.TOWN_RETURN, GoalKind.COMBAT_ENGAGE, GoalKind.COMBAT_RETREAT,
    GoalKind.RECOVER, GoalKind.RESOLVE_BLOCKER, GoalKind.GUILD,
})


def _score_scale_max(kind) -> float:
    """Return the declared score ceiling for the system that produced `kind`.

    Classification is by the *actual Python enum class* of `kind`, not its string value:
    ProjectKind.HARVESTING and GoalKind.HARVESTING (and ProjectKind.SOCIAL / GoalKind.SOCIAL)
    share identical string values (src/core/strategic.py:121-148) but are different enum classes.
    A value-based check (e.g. `kind in {v.value for v in ProjectKind}`) would silently misclassify
    System B candidates as System A for those two overlapping kinds — do not do that.

    Does not unify or alter the ProjectKind/GoalKind vocabulary split (out of scope, tracked under
    D22/C4) — it only reads the enum identity already present at each ProjectState construction
    site: mapper.py:96-107 always emits real ProjectKind members; intelligence.py's own
    GoalRegistry-sourced candidate (line ~1334) always emits real GoalKind members. Anything else
    (raw strings — "detour", test fixtures, any future third system) defaults to the
    GoalRegistry/universal-baseline scale.
    """
    if isinstance(kind, ProjectKind):
        return _ADVENTURE_ROUTE_SCORE_MAX
    return _GOAL_UTILITY_SCORE_MAX


def _threat_resolved(hero: EntityState, state: AuthoritativeState) -> bool:
    """
    Return True when the triggering threat for a survival lock is no longer active:
    entity HP has recovered above 80% AND no hostile entity is within interaction radius.

    Used as an early-release condition inside evaluate_project_switch()'s locked-branch gate
    so that entities are not held idle in a project lock after the threat passes. Relocated
    from src/domains/adventure/phase.py (TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION) to
    generalize beyond AdventureDecisionPhase's original sole-caller scope. STRAT-236.
    """
    hp_ratio = hero.combat.hp / max(1, hero.combat.max_hp)
    if hp_ratio <= 0.8:
        return False
    nearby_ids = SpatialQueryService.nearby_entities(state, hero.navigation.position, radius=10.0)
    has_hostile = any(
        eid != hero.id
        and (e := state.entities.get(eid)) is not None
        and e.combat.alive
        and e.identity.faction != hero.identity.faction
        for eid in nearby_ids
    )
    return not has_hostile


class StrategicIntelligenceSystem:
    """
    Analyzes character outcomes to generate or resolve strategic markers.
    Phase 9: Full strategic lifecycle management.
    Logic ID: STRAT-002 (Decision logic evaluates state / does not directly mutate)
    """

    @staticmethod
    def infer_blockers(
        entity: EntityState,
        last_task: str,
        last_payload: Dict[str, Any],
        navigation_failure: Optional[str] = None,
        current_project: Optional[ProjectState] = None
    ) -> StrategicUpdate:
        """
        Infer blockers based on recent failures.
        Logic ID: STRAT-191 (Blockers have kind)
        Logic ID: STRAT-192 (Blockers have subject/reference)
        Logic ID: STRAT-193 (Blockers have severity)
        Logic ID: STRAT-194 (Blockers have origin/spawned-from reference where useful)
        VERIFIED v2: strategic_blocker_inference
        """
        blockers = []
        
        # 1. Navigation Failure (ACCESS blocker)
        if navigation_failure in ("PATH_NOT_FOUND", "STUCK", "OSCILLATING"):
            target_pos = last_payload.get("target_position")
            if target_pos:
                subject = f"{target_pos}"
                kind = "access"
                blockers.append(BlockerState(
                    id=f"blocker_access_{int(target_pos[0])}_{int(target_pos[1])}",
                    kind=kind,
                    subject=subject,
                    severity=0.8
                ))
        
        # Phase 4: Congestion Blocker
        if entity.navigation.wait_count >= 5 or entity.navigation.oscillation_count >= 3:
             blockers.append(BlockerState(
                 id="blocker_congestion",
                 kind="access",
                 subject="congestion",
                 severity=0.5
             ))
        
        # 2. Material/Resource Failure (Interactions)
        if last_task == "ENTITY_ACT" and last_payload.get("action") == "INTERACT":
            target_id = last_payload.get("target_id")
            if target_id and current_project and current_project.kind == "harvesting":
                # Check for capacity failure in latest intent results
                capacity_fail = any(r.reason == "INSUFFICIENT_CAPACITY" or r.reason == "INVENTORY_FULL" for r in entity.identity.latest_intent_results)
                if capacity_fail:
                    blockers.append(BlockerState(
                        id="blocker_inventory_full",
                        kind="inventory",
                        subject="capacity",
                        severity=1.0
                    ))
                else:
                    blockers.append(BlockerState(
                        id=f"blocker_node_{target_id}",
                        kind="material",
                        subject="resource", 
                        severity=1.0
                    ))

        # 3. Transaction Failures (Generic)
        for result in entity.identity.latest_intent_results:
            if not result.accepted:
                if result.reason in ("INSUFFICIENT_CAPACITY", "INVENTORY_FULL"):
                     blockers.append(BlockerState(
                        id="blocker_inventory_full",
                        kind="inventory",
                        subject="capacity",
                        severity=1.0
                    ))
                elif result.reason == "OUT_OF_STOCK":
                    blockers.append(BlockerState(
                        id=f"blocker_out_of_stock_{result.source_id}",
                        kind="material",
                        subject="out_of_stock",
                        severity=1.0
                    ))
                elif result.reason == "LIQUIDITY_EXHAUSTED":
                    blockers.append(BlockerState(
                        id=f"blocker_liquidity_{result.source_id}",
                        kind="material",
                        subject="liquidity",
                        severity=1.0
                    ))
        
        if not blockers:
            return StrategicUpdate()
            
        # Deduplicate by ID
        unique_blockers = {}
        for b in blockers:
            unique_blockers[b.id] = b
            
        return StrategicUpdate(blockers_add_or_update=list(unique_blockers.values()))

    @staticmethod
    def generate_crafting_blockers(
        entity: EntityState,
        recipe_mats: Dict[str, int],
        gold_cost: int
    ) -> StrategicUpdate:
        """
        Produce a StrategicUpdate containing blockers for missing requirements.
        """
        blockers = []
        inv = entity.inventory

        for mat_id, needed in recipe_mats.items():
            have = sum((s.quantity if hasattr(s, "quantity") else 1) for s in inv.items if (s.item_id if hasattr(s, "item_id") else s) == mat_id)
            if have < needed:
                blockers.append(BlockerState(
                    id=f"blocker_mat_{mat_id}",
                    kind="material",
                    subject=mat_id,
                    severity=min(1.0, (needed - have) / needed),
                    target_quantity=needed
                ))

        if inv.gold < gold_cost:
            blockers.append(BlockerState(
                id="blocker_gold",
                kind="material",
                subject="gold",
                severity=min(1.0, (gold_cost - inv.gold) / gold_cost),
                target_quantity=gold_cost
            ))

        return StrategicUpdate(blockers_add_or_update=blockers)

    @staticmethod
    def fused_strategic_pass(
        state: AuthoritativeState,
        update: StateUpdate,
        cadence: SystemCadence = None
    ) -> StateUpdate:
        """
        Fused pass for strategic intelligence (Blockers, Concerns, Intents).
        Logic ID: STRAT-PERF-001 (Consolidated O(N) pass for strategic state)
        """
        cadence = cadence or SystemCadence()
        cad_val = cadence.strategic_intelligence

        refined_entity_updates = dict(update.entity_updates)

        def has_item(inventory, item_id: str, quantity: int = 1) -> bool:
            if item_id == "gold":
                return inventory.gold >= quantity
            for stack in inventory.items:
                sid = getattr(stack, "item_id", stack)
                if sid == item_id:
                    sqty = getattr(stack, "quantity", 1)
                    if sqty >= quantity:
                        return True
            return False

        has_hostiles_or_dead = getattr(state, "_has_hostiles_or_dead_cache", None)
        if has_hostiles_or_dead is None:
            first_fac = None
            has_diff = False
            has_dead = False
            for ent in state.entities.values():
                if not ent.combat.alive:
                    has_dead = True
                if first_fac is None:
                    first_fac = ent.identity.faction
                elif ent.identity.faction != first_fac:
                    has_diff = True
                if has_dead and has_diff:
                    break
            has_hostiles_or_dead = (has_diff or has_dead)
            try: object.__setattr__(state, "_has_hostiles_or_dead_cache", has_hostiles_or_dead)
            except: pass

        # Evaluation of routine blockers and concerns must run across candidate entities
        # Logic ID: PERF-006 (Dirty Entity Tracking for specific sub-phases, but routine pass is global)
        fast_hits = 0
        fast_misses = 0
        policy = getattr(update, "current_policy_set", None) or GovernorPolicy()
        candidate_ids = StrategicWorkQueue.build(
            state, update, get_dirty_set(update), 
            budget=policy.strategic_budget, 
            sweep_interval=policy.background_sweep_interval
        )
        for e_id in candidate_ids:
            entity = state.entities[e_id]
            # Early exit: Skip inactive/dead entities entirely
            if not entity.lifecycle.active or not entity.combat.alive:
                continue
            
            ent_upd = refined_entity_updates.get(e_id)
            has_existing_upd = ent_upd is not None
            strat_up = ent_upd.strategic if ent_upd else None
            
            pending_inventory = entity.inventory
            if ent_upd and ent_upd.inventory:
                pending_inventory = InventoryService.apply_update(entity.inventory, ent_upd.inventory)
            
            eval_concerns = should_run(state.tick, e_id, cadence.concern_evaluation)
            eval_intents = should_run(state.tick, e_id, cadence.strategic_intelligence)
            
            if not eval_concerns and not eval_intents and strat_up is None and not entity.strategic.blockers and not entity.strategic.leads:
                nav_changed = False
                proj_resolved = False
                curr_proj_id = entity.strategic.current_project_id
                project = None
                active_obj = None
                if curr_proj_id:
                    project = entity.strategic.projects.get(curr_proj_id)
                    if project and project.status == ProjectStatus.ACTIVE:
                        active_obj = next((o for o in project.objectives if o.id == project.active_objective_id), None)
                        if active_obj and active_obj.status == ObjectiveStatus.ACTIVE:
                            if active_obj.kind in ("craft", "collect") and has_item(pending_inventory, active_obj.target, 1):
                                proj_resolved = True
                            target_pos = getattr(active_obj, 'target_position', None)
                            if target_pos and entity.navigation.target != target_pos:
                                nav_changed = True
                if not nav_changed and not proj_resolved:
                    if not (curr_proj_id and project and project.status == ProjectStatus.ACTIVE and active_obj and getattr(active_obj, 'target_position', None) is not None):
                        town_target = nearest_town_tile(state.town_tiles, entity.navigation.position) or state.town_center
                        if len(pending_inventory.items) > 0 and entity.navigation.position != (0.0, 0.0) and town_target and entity.navigation.target != town_target:
                            if ent_upd:
                                refined_entity_updates[e_id] = replace(ent_upd,
                                    navigation=NavigationUpdate(target_set=town_target, movement_mode_set=MovementMode.REGROUP),
                                    interaction=InteractionUpdate(reset=True)
                                )
                            else:
                                refined_entity_updates[e_id] = EntityUpdate(
                                    entity_id=e_id,
                                    navigation=NavigationUpdate(target_set=town_target, movement_mode_set=MovementMode.REGROUP),
                                    interaction=InteractionUpdate(reset=True)
                                )
                    fast_hits += 1
                    continue
            fast_misses += 1

            if not has_existing_upd:
                ent_upd = EntityUpdate(entity_id=e_id)
            
            strat_up = strat_up or StrategicUpdate()
            
            # --- Belief confirmation / contradiction check ---
            from src.core.strategic import LeadCertainty
            for lead in list(entity.strategic.leads.values()):
                if lead.kind == "location" and lead.certainty != LeadCertainty.EXHAUSTED and not lead.tested:
                    try:
                        coords = tuple(map(float, lead.detail.split(',')))
                        px, py = entity.navigation.position
                        dist = ((px - coords[0])**2 + (py - coords[1])**2)**0.5
                        if dist < 1.0:
                            raw_neighbors = SimulationDomainLogic.get_neighbor_view(state, entity, radius=10.0)
                            hostiles = [n[1] for n in raw_neighbors if n[1].identity.faction != entity.identity.faction and n[1].combat.alive]
                            
                            if hostiles:
                                confirm_up = BeliefCycleSystem.process_observation(entity, lead.subject, lead.detail, state.tick)
                                updated_leads = [replace(l, id=lead.id, tested=True, test_outcome="SUCCESS") for l in confirm_up.leads_add_or_update]
                                updated_beliefs = [replace(b, id=f"belief_rumor_{lead.subject}_{lead.discovered_tick}") if b.source == "observation" else b for b in confirm_up.beliefs_add_or_update]
                                strat_up = strat_up.merge(StrategicUpdate(
                                    leads_add_or_update=updated_leads,
                                    beliefs_add_or_update=updated_beliefs
                                ))
                                logger.debug(
                                    f"[Tick {state.tick}] BeliefUpgraded: Entity {entity.id} verified threat at {lead.subject} "
                                    f"via direct observation. Certainty set to 1.0."
                                )
                            else:
                                contra_up = BeliefCycleSystem.apply_contradiction(entity, lead.id, "no_hostiles_found")
                                updated_leads = [replace(l, tested=True, test_outcome="FAILURE") for l in contra_up.leads_add_or_update]
                                strat_up = strat_up.merge(replace(contra_up, leads_add_or_update=updated_leads))
                                logger.debug(
                                    f"[Tick {state.tick}] BeliefContradicted: Entity {entity.id} observed no threat at {lead.subject}. "
                                    f"Contradiction count incremented."
                                )
                    except Exception as ex:
                        logger.error(f"Failed to check belief lead outcome: {ex}")

            # --- Blocker Inference ---
            current_proj_id = strat_up.current_project_id_set if strat_up.current_project_id_set is not None else entity.strategic.current_project_id
            current_proj = next((p for p in strat_up.projects_add_or_update if p.id == current_proj_id), None) or entity.strategic.projects.get(current_proj_id) if current_proj_id else None
            
            inferred_up = StrategicIntelligenceSystem.infer_blockers(
                entity,
                entity.task.work_kind,
                entity.task.payload,
                navigation_failure=entity.navigation.last_failure_reason,
                current_project=current_proj
            )
            
            new_additions = list(strat_up.blockers_add_or_update)
            if inferred_up.blockers_add_or_update:
                for b in inferred_up.blockers_add_or_update:
                    if b.id not in [x.id for x in new_additions]:
                        new_additions.append(b)
            
            strat_up = replace(strat_up, blockers_add_or_update=new_additions)
            removals = set(strat_up.blockers_remove)
            resolved_ids = set()
            for b_id, b in entity.strategic.blockers.items():
                if b_id in removals or b.resolved: continue
                if b.kind == "material" and has_item(pending_inventory, b.subject, b.target_quantity):
                    resolved_ids.add(b_id)
                elif b.kind == "access" and b.subject.startswith("("):
                    try:
                        coords = ast.literal_eval(b.subject)
                        if isinstance(coords, tuple) and len(coords) == 2:
                            dx = entity.navigation.position[0] - coords[0]
                            dy = entity.navigation.position[1] - coords[1]
                            if (dx*dx + dy*dy)**0.5 < 0.5: resolved_ids.add(b_id)
                    except: pass
                elif b.kind == "inventory" and b.subject == "capacity":
                    if len(pending_inventory.items) < pending_inventory.max_slots:
                        resolved_ids.add(b_id)
            
            for blocker in strat_up.blockers_add_or_update:
                if blocker.resolved: resolved_ids.add(blocker.id)

            project_upd = None
            current_proj_id = strat_up.current_project_id_set if strat_up.current_project_id_set is not None else entity.strategic.current_project_id
            if current_proj_id:
                project = next((p for p in strat_up.projects_add_or_update if p.id == current_proj_id), None) or entity.strategic.projects.get(current_proj_id)
                if project and project.status == ProjectStatus.ACTIVE:
                    obj_id = strat_up.current_objective_id_set if strat_up.current_objective_id_set is not None else project.active_objective_id
                    active_obj = next((o for o in project.objectives if o.id == obj_id), None)
                    if active_obj and active_obj.status == ObjectiveStatus.ACTIVE:
                        if not active_obj.blocker_ids:
                            all_blockers_resolved = False
                        else:
                            all_blockers_resolved = True
                            for b_id in active_obj.blocker_ids:
                                if b_id not in entity.strategic.blockers and b_id not in [b.id for b in strat_up.blockers_add_or_update]: continue
                                b_obj = entity.strategic.blockers.get(b_id)
                                # Check if resolved this tick or already resolved in state
                                if b_id not in resolved_ids and not (b_obj and b_obj.resolved):
                                    all_blockers_resolved = False; break
                        if active_obj.kind in ("craft", "collect") and has_item(pending_inventory, active_obj.target, 1):
                            all_blockers_resolved = True
                        if all_blockers_resolved:
                            new_obj = replace(active_obj, status=ObjectiveStatus.RESOLVED)
                            project_upd = replace(project, objectives=[new_obj if o.id == new_obj.id else o for o in project.objectives], status=ProjectStatus.COMPLETED)

            # (Update strat_up with results)
            new_additions = list(strat_up.blockers_add_or_update)
            for b_id in resolved_ids:
                found = False
                for i, b in enumerate(new_additions):
                    if b.id == b_id: new_additions[i] = replace(b, resolved=True); found = True; break
                if not found:
                    b_obj = entity.strategic.blockers.get(b_id)
                    if b_obj: new_additions.append(replace(b_obj, resolved=True))
            
            new_removals = list(set(strat_up.blockers_remove) | resolved_ids)
            new_projects = list(strat_up.projects_add_or_update)
            if project_upd: new_projects.append(project_upd)
            
            final_identity_upd = ent_upd.identity
            if project_upd and project_upd.status == ProjectStatus.COMPLETED:
                final_identity_upd = (final_identity_upd or IdentityUpdate()).merge(IdentityUpdate(craft_target=""))

            # Only replace if actual changes occurred
            if new_additions != list(strat_up.blockers_add_or_update) or \
               new_removals != list(strat_up.blockers_remove) or \
               new_projects != list(strat_up.projects_add_or_update) or \
               (project_upd and (strat_up.current_project_id_set == "" or strat_up.current_objective_id_set == "")):
                
                strat_up = replace(strat_up,
                    blockers_add_or_update=new_additions,
                    blockers_remove=new_removals,
                    projects_add_or_update=new_projects,
                    current_project_id_set="" if project_upd else strat_up.current_project_id_set,
                    current_objective_id_set="" if project_upd else strat_up.current_objective_id_set
                )
            
            # --- 2. Concerns ---
            concerns_to_add = list(strat_up.concerns_add_or_update)
            if should_run(state.tick, e_id, cadence.concern_evaluation):
                # Combine all routine evaluation logic
                routine_concerns = (
                    RoutineService.evaluate_biological_needs(entity, state.tick % 2400) +
                    RoutineService.evaluate_environmental_concerns(entity) +
                    RoutineService.evaluate_anchored_behavior(entity, state)
                )
                
                # Optimization: only evaluate salience if we have neighbors
                salience_concerns = []
                if has_hostiles_or_dead or entity.biological.hunger > 60.0:
                    neighbors = SimulationDomainLogic.get_neighbor_view(state, entity, radius=3.0)
                    salience_concerns = ConcernIntakeSystem.evaluate_salience(entity, neighbors, state)
                
                existing_concern_ids = set(entity.strategic.concerns.keys()) | {c.id for c in concerns_to_add}
                for c in routine_concerns + salience_concerns:
                    if c.id not in existing_concern_ids:
                        concerns_to_add.append(c)
                        existing_concern_ids.add(c.id)
            
            if concerns_to_add != list(strat_up.concerns_add_or_update):
                strat_up = replace(strat_up, concerns_add_or_update=concerns_to_add)

            # --- 3. Strategic Intents ---
            if should_run(state.tick, e_id, cadence.strategic_intelligence):
                temp_entity = entity
                active_blockers = {**entity.strategic.blockers}
                for b in strat_up.blockers_add_or_update:
                    active_blockers[b.id] = b
                if active_blockers != entity.strategic.blockers:
                    temp_entity = replace(entity, strategic=replace(entity.strategic, blockers=active_blockers))
                
                # Call original intent evaluation but with force=True to bypass its own cadence check
                # (since we already checked cadence here)
                intent_up = StrategicIntelligenceSystem.evaluate_strategic_intent(state, temp_entity, force=True, cadence=cadence)
                strat_up = strat_up.merge(intent_up)

            # --- 4. Capacity Enforcement (unconditional, every tick) ---
            # Enforces profile limits on leads, concerns, hypotheses, and projects.
            # Runs after all cognition items are accumulated so final removals are
            # applied before navigation decisions read from strat_up.
            # Logic ID: STRAT-012 (Cognition capacity is enforced unconditionally)
            capacity_up = DetourSuggestionSystem.enforce_bandwidth(entity, state.tick)
            if not capacity_up.is_noop():
                strat_up = strat_up.merge(capacity_up)

            # --- 5. Redirection (Bridge to Navigation) ---
            # (Hoisted logic from StrategicRedirectionSystem)
            
            has_nav_update = ent_upd.navigation and ent_upd.navigation.target_set is not None
            current_project_id = strat_up.current_project_id_set if strat_up.current_project_id_set is not None else entity.strategic.current_project_id
            
            active_blockers = [b for b_id, b in entity.strategic.blockers.items() if b_id not in new_removals and not b.resolved]
            active_blockers.extend([b for b in new_additions if b.id not in new_removals and not b.resolved])
            
            mat_blockers = [b for b in active_blockers if b.kind == "material" and not b.resolved]
            if mat_blockers:
                target_mat = mat_blockers[0].subject
                match_lead = next((l for l in entity.strategic.leads.values() if l.subject == target_mat and l.kind == 'location'), None)
                if match_lead:
                    try:
                        coords = tuple(map(float, match_lead.detail.split(',')))
                        if entity.navigation.target != coords:
                            has_nav_update = True
                            existing_nav = ent_upd.navigation or NavigationUpdate()
                            ent_upd = replace(ent_upd, navigation=replace(existing_nav, target_set=coords), interaction=InteractionUpdate(reset=True))
                    except: pass
            
            if not has_nav_update and current_project_id:
                project = next((p for p in strat_up.projects_add_or_update if p.id == current_project_id), None) or entity.strategic.projects.get(current_project_id)
                if project and project.status == ProjectStatus.ACTIVE:
                    obj_id = strat_up.current_objective_id_set if strat_up.current_objective_id_set is not None else project.active_objective_id
                    active_obj = next((o for o in project.objectives if o.id == obj_id), None)
                    if active_obj and active_obj.status == ObjectiveStatus.ACTIVE:
                        target_pos = getattr(active_obj, 'target_position', None)
                        if target_pos:
                             has_nav_update = True
                             if entity.navigation.target != target_pos:
                                 ent_upd = replace(ent_upd, navigation=replace(ent_upd.navigation or NavigationUpdate(), target_set=target_pos))
            
            if not has_nav_update:
                town_target = nearest_town_tile(state.town_tiles, entity.navigation.position) or state.town_center
                if len(pending_inventory.items) > 0 and entity.navigation.position != (0.0, 0.0) and town_target:
                    if entity.navigation.target != town_target:
                        has_nav_update = True
                        ent_upd = replace(ent_upd, 
                            navigation=replace(ent_upd.navigation or NavigationUpdate(), target_set=town_target, movement_mode_set=MovementMode.REGROUP),
                            interaction=InteractionUpdate(reset=True)
                        )
            
            # Finalize entity update - only if changed
            if strat_up is not None and strat_up.is_noop():
                strat_up = None
            if final_identity_upd is not None and final_identity_upd.is_noop():
                final_identity_upd = None

            if final_identity_upd is not ent_upd.identity or strat_up is not ent_upd.strategic or ent_upd.navigation is not None or ent_upd.interaction is not None or has_existing_upd:
                # TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE: this is the live
                # pipeline's actual strategic-intelligence merge site (fused_strategic_pass(),
                # wired via src/engine/pipeline.py:333) -- copy-then-set, not a wholesale
                # replace, since ent_upd.property_updates may already carry earlier phases'
                # writes for this entity within this same tick.
                prop_updates = dict(ent_upd.property_updates)
                if strat_up is not None and strat_up.last_routing_family_set is not None:
                    prop_updates["last_routing_family"] = strat_up.last_routing_family_set
                if strat_up is not None and strat_up.last_routing_tick_set is not None:
                    prop_updates["last_routing_tick"] = strat_up.last_routing_tick_set
                final_upd = replace(ent_upd, identity=final_identity_upd, strategic=strat_up, property_updates=prop_updates)
                refined_entity_updates[e_id] = final_upd
        
        if state.tick % 10 == 0:
            logger.debug(f"[Tick {state.tick}] fused fast path: hits={fast_hits}, misses={fast_misses}")

        if refined_entity_updates == update.entity_updates:
            return update
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def resolve_blockers(
        state: AuthoritativeState,
        update: StateUpdate,
        cadence: SystemCadence = None
    ) -> StateUpdate:
        """
        Resolve strategic blockers that are satisfied by the current or pending
        authoritative inventory state.
        """
        from src.engine.cadence import should_run
        cadence = cadence or SystemCadence()
        
        from dataclasses import replace
        from src.core.updates import EntityUpdate, StrategicUpdate
        from src.core.inventory import InventoryService

        refined_entity_updates = dict(update.entity_updates)

        def has_item(inventory, item_id: str, quantity: int = 1) -> bool:
            if item_id == "gold":
                return inventory.gold >= quantity
            return any(
                stack.item_id == item_id and stack.quantity >= quantity
                for stack in inventory.items
            )

        candidate_ids = list(state.entities.keys())
        for e_id in sorted(candidate_ids):
            entity = state.entities[e_id]
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))

            pending_inventory = entity.inventory
            if ent_upd.inventory:
                pending_inventory = InventoryService.apply_update(
                    entity.inventory,
                    ent_upd.inventory,
                )

            strat_up = ent_upd.strategic or StrategicUpdate()
            removals = set(strat_up.blockers_remove)
            resolved_ids = set()
            # 1. Passive resolution from existing state
            # We ONLY check blockers from previous ticks. New blockers added this tick (in strat_up)
            # are trusted to be accurate results of current-tick enforcement (e.g. Blacksmith).
            for b_id, b in entity.strategic.blockers.items():
                if b_id in removals or b.resolved: continue
                
                # 1. Material Resolution
                if b.kind == "material" and has_item(pending_inventory, b.subject, b.target_quantity):
                    resolved_ids.add(b_id)
                
                # 2. Access Resolution (RPG-STRAT-011)
                elif b.kind == "access" and b.subject.startswith("("):
                    try:
                        coords = ast.literal_eval(b.subject)
                        if isinstance(coords, tuple) and len(coords) == 2:
                            dx = entity.navigation.position[0] - coords[0]
                            dy = entity.navigation.position[1] - coords[1]
                            dist = (dx*dx + dy*dy)**0.5
                            if dist < 0.5:
                                resolved_ids.add(b_id)
                    except:
                        pass
                
                # 3. Inventory Resolution
                elif b.kind == "inventory" and b.subject == "capacity":
                    if len(pending_inventory.items) < pending_inventory.max_slots:
                        resolved_ids.add(b_id)
            
            # 2. Check for newly resolved blockers (explicitly marked as resolved)
            for blocker in strat_up.blockers_add_or_update:
                if blocker.resolved:
                    resolved_ids.add(blocker.id)

            # 3. Objective Resolution (RPG-STRAT-009 Fix)
            # If a blocker was resolved, check if the active objective is also resolved
            current_proj_id = strat_up.current_project_id_set if strat_up.current_project_id_set is not None else entity.strategic.current_project_id
            project_upd = None
            if current_proj_id:
                project = entity.strategic.projects.get(current_proj_id)
                if project and project.status == ProjectStatus.ACTIVE:
                    obj_id = strat_up.current_objective_id_set if strat_up.current_objective_id_set is not None else project.active_objective_id
                    active_obj = next((o for o in project.objectives if o.id == obj_id), None)
                    if active_obj and active_obj.status == ObjectiveStatus.ACTIVE:
                        # Check if all blockers for this objective are resolved
                        all_blockers_resolved = True
                        for b_id in active_obj.blocker_ids:
                            if b_id not in entity.strategic.blockers and b_id not in [b.id for b in strat_up.blockers_add_or_update]:
                                 # This blocker was never there or already removed?
                                 continue
                            
                            is_now_resolved = (b_id in resolved_ids)
                            if not is_now_resolved:
                                 b_obj = entity.strategic.blockers.get(b_id)
                                 if b_obj and not b_obj.resolved:
                                      all_blockers_resolved = False
                                      break
                        
                        # Special case: Crafting/Collecting objectives (Material-based)
                        is_material_obj = active_obj.kind in ("craft", "collect")
                        if is_material_obj:
                             if has_item(pending_inventory, active_obj.target, 1):
                                  all_blockers_resolved = True
                        
                        if all_blockers_resolved:
                            # Resolve Objective and Complete Project
                            new_obj = replace(active_obj, status=ObjectiveStatus.RESOLVED)
                            new_project = replace(project, objectives=[new_obj if o.id == new_obj.id else o for o in project.objectives], status=ProjectStatus.COMPLETED)
                            project_upd = new_project
            
            if not resolved_ids and not project_upd:
                continue

            # RPG-STRAT-011: Mark resolved blockers in the update for test observability
            new_additions = list(strat_up.blockers_add_or_update)
            for b_id in resolved_ids:
                # 1. Update if already in additions
                found_in_upd = False
                for i, b in enumerate(new_additions):
                    if b.id == b_id:
                        new_additions[i] = replace(b, resolved=True)
                        found_in_upd = True
                        break
                
                # 2. Add if it was only in state
                if not found_in_upd:
                    b_obj = entity.strategic.blockers.get(b_id)
                    if b_obj:
                        new_additions.append(replace(b_obj, resolved=True))

            new_removals = list(
                set(strat_up.blockers_remove) | resolved_ids
            )

            new_projects = list(strat_up.projects_add_or_update)
            if project_upd:
                new_projects.append(project_upd)

            final_identity_upd = ent_upd.identity
            if project_upd and project_upd.status == ProjectStatus.COMPLETED:
                # Milestone 3 Law: Complete means stop trying [INTEG-FIX]
                final_identity_upd = (final_identity_upd or IdentityUpdate()).merge(IdentityUpdate(craft_target=""))

            refined_entity_updates[e_id] = replace(
                ent_upd,
                identity=final_identity_upd,
                strategic=replace(
                    strat_up,
                    blockers_add_or_update=new_additions,
                    blockers_remove=new_removals,
                    projects_add_or_update=new_projects,
                    current_project_id_set="" if project_upd else strat_up.current_project_id_set,
                    current_objective_id_set="" if project_upd else strat_up.current_objective_id_set
                ),
            )

        metric_counters = dict(update.metric_counters) if getattr(update, "metric_counters", None) is not None else {}
        metric_counters["strategic_candidates"] = len(candidate_ids)
        return replace(update, entity_updates=refined_entity_updates, metric_counters=metric_counters)



    @staticmethod
    def evaluate_all_concerns(
        state: AuthoritativeState,
        update: StateUpdate,
        cadence: SystemCadence | None = None
    ) -> StateUpdate:
        """
        Phase 9: Routine, Biological Needs, and Salience Filtering.
        VERIFIED v2: concern_intake_aggregation
        """
        from src.systems.routine import RoutineService
        from src.systems.intake import ConcernIntakeSystem
        from src.engine.domain_logic import SimulationDomainLogic
        
        refined_entity_updates = dict(update.entity_updates)
        
        from src.engine.cadence import should_run, SystemCadence as DefaultCadence
        
        # Phase 9 Fix: Deterministic entity iteration via StrategicWorkQueue
        policy = getattr(update, "current_policy_set", None) or GovernorPolicy()
        candidate_ids = StrategicWorkQueue.build(
            state, update, get_dirty_set(update), 
            budget=policy.strategic_budget, 
            sweep_interval=policy.background_sweep_interval
        )
        for e_id in candidate_ids:
            entity = state.entities[e_id]
            # Phase 5: Bounded frequency and early exit (Hardening)
            if not entity.lifecycle.active or not entity.combat.alive:
                continue
            
            # Legality Guard: Incapacitated entities skip strategic cycles
            if entity.identity.properties.get("status_frozen") or entity.identity.properties.get("status_stunned"):
                continue

            cad_val = (cadence.concern_evaluation if cadence else DefaultCadence().concern_evaluation)
            if not should_run(state.tick, e_id, cad_val):
                continue

            # 1. Internal/Biological Concerns
            concerns = RoutineService.evaluate_biological_needs(entity, state.world_time)
            anchored_concerns = RoutineService.evaluate_anchored_behavior(entity, state)
            env_concerns = RoutineService.evaluate_environmental_concerns(entity)
            
            # 2. External Salience Concerns (Phase 9 Hardening)
            neighbors = SimulationDomainLogic.get_neighbor_view(state, entity, radius=3.0)
            salient_concerns = ConcernIntakeSystem.evaluate_salience(entity, neighbors, state)
            
            concerns.extend(anchored_concerns)
            concerns.extend(env_concerns)
            concerns.extend(salient_concerns)
            
            if not concerns:
                continue
                
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            strat_up = ent_upd.strategic or StrategicUpdate()

            new_concerns = list(set(strat_up.concerns_add_or_update + concerns))
            
            # Law 194: Enforce Strategic Bandwidth for concerns
            # Logic ID: 194
            bandwidth_upd = DetourSuggestionSystem.enforce_bandwidth(entity, state.tick)
            if bandwidth_upd.concerns_remove:
                to_remove = set(bandwidth_upd.concerns_remove)
                new_concerns = [c for c in new_concerns if c.id not in to_remove]
            
            new_strat_up = replace(
                strat_up,
                concerns_add_or_update=new_concerns,
                concerns_remove=list(set(strat_up.concerns_remove + bandwidth_upd.concerns_remove))
            )
            refined_entity_updates[e_id] = replace(ent_upd, strategic=new_strat_up)
                
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def evaluate_all_strategic_intents(
        state: AuthoritativeState,
        update: StateUpdate,
        cadence: SystemCadence | None = None
    ) -> StateUpdate:
        """
        Phase 4.1: Strategic Intent Evaluation (Projects/Objectives).
        Orchestrates the loop over evaluate_strategic_intent for all active entities.
        """
        refined_entity_updates = dict(update.entity_updates)
        
        from src.engine.cadence import should_run, SystemCadence as DefaultCadence
        
        policy = getattr(update, "current_policy_set", None) or GovernorPolicy()
        candidate_ids = StrategicWorkQueue.build(
            state, update, get_dirty_set(update), 
            budget=policy.strategic_budget, 
            sweep_interval=policy.background_sweep_interval
        )
        for e_id in candidate_ids:
            entity = state.entities[e_id]
            if not entity.lifecycle.active or not entity.combat.alive:
                continue
            
            # Legality Guard: Incapacitated entities skip strategic cycles
            if entity.identity.properties.get("status_frozen") or entity.identity.properties.get("status_stunned"):
                continue

            # Staggered frequency (Phase 5/6 spec)
            cad_val = (cadence.strategic_intelligence if cadence else DefaultCadence().strategic_intelligence)
            if not should_run(state.tick, e_id, cad_val):
                continue

            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            # We must pass the "current best guess" of the entity state to evaluate_strategic_intent.
            # However, evaluate_strategic_intent is designed to work on the static EntityState.
            # For v2 consistency, we call it on the current state.
            strat_up = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
            if strat_up:
                # Merge with existing updates if any
                existing_strat = ent_upd.strategic or StrategicUpdate()
                merged_strat = existing_strat.merge(strat_up)
                # TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE: copy-then-set, not a
                # wholesale replace -- ent_upd.property_updates may already carry earlier phases'
                # writes for this entity within this same tick.
                prop_updates = dict(ent_upd.property_updates)
                if strat_up.last_routing_family_set is not None:
                    prop_updates["last_routing_family"] = strat_up.last_routing_family_set
                if strat_up.last_routing_tick_set is not None:
                    prop_updates["last_routing_tick"] = strat_up.last_routing_tick_set
                refined_entity_updates[e_id] = replace(ent_upd, strategic=merged_strat, property_updates=prop_updates)
                
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def apply_routine_biasing(
        entity: EntityState,
        world_time: int,
        projects: List[ProjectState],
        neighbors: List[EntityState] = []
    ) -> List[ProjectState]:
        from src.systems.routine import RoutineService
        from src.systems.learning import StrategicLearningService
        from src.engine.cognition import AppraisalSystem
        
        # 1. Routine and Role Biasing
        projects = RoutineService.apply_role_based_biasing(entity, projects, world_time)
        
        # 2. Strategic Memory (Learning) Biasing
        memory_biases = StrategicLearningService.get_goal_biases(entity.strategic.turning_points)
        
        # 3. Emotional Appraisal (Short-term) Biasing
        # We need neighbors for full appraisal, but can use defaults if empty
        emotion = AppraisalSystem.evaluate_emotional_state(entity, neighbors)
        
        biased_projects = []
        for p in projects:
            score = p.score
            
            # Apply memory bias
            kind_key = p.kind.lower()
            if kind_key in memory_biases:
                score += memory_biases[kind_key]
                
            # Apply emotional bias
            if kind_key == "combat" or kind_key == "detour":
                score *= emotion.aggression_mod
                if emotion.is_fleeing:
                    score -= 50.0 # Heavy penalty for combat if panicked
            
            biased_projects.append(replace(p, score=score))
            
        return biased_projects

    @staticmethod
    def evaluate_project_switch(
        entity: EntityState,
        candidate_project: ProjectState,
        current_tick: int,
        state: Optional[AuthoritativeState] = None
    ) -> Optional[StrategicUpdate]:
        """
        Phase 9: Strategic interruption resistance and retention.

        Lock-bypass gate (when the current project's lock has not yet expired):
        `"detour"` remains the sole unconditional structural bypass. Any other candidate,
        regardless of `kind`, may bypass the lock only when its score — expressed as a
        percentage of its own system's declared max (`_ADVENTURE_ROUTE_SCORE_MAX` for
        `ProjectKind`-typed candidates, `_GOAL_UTILITY_SCORE_MAX` otherwise) — both exceeds
        the current project's own normalized effective score (`current.score` plus
        `retention_margin`, same percentage basis) AND clears `_INTERRUPTION_URGENCY_FLOOR_PCT`.
        This replaces the old hardcoded `kind == "danger" and score > 80` / `kind == "detour"`
        allowlist. The raw `retention_margin`/`effective_current_score` formula and the
        unlocked-path final comparison below are unchanged.

        Logic ID: STRAT-185 (Strategic project retention is bounded by interruption resistance)
        Logic ID: STRAT-186 (Strategic project switching requires margin or explicit emergency)
        Logic ID: STRAT-187 (Current project has reservation priority)
        VERIFIED v2: project_interruption_resistance
        VERIFIED v2: current_project_retention
        """
        # Logic ID: STRAT-003 (Cognition profiles enforce bandwidth)
        profile = entity.strategic.profile
        current_id = entity.strategic.current_project_id

        if not current_id:
            return StrategicUpdate(
                projects_add_or_update=[candidate_project],
                current_project_id_set=candidate_project.id,
                current_objective_id_set=candidate_project.active_objective_id
            )

        current = entity.strategic.projects.get(current_id)
        if not current or current.status != ProjectStatus.ACTIVE:
            return StrategicUpdate(
                projects_add_or_update=[candidate_project],
                current_project_id_set=candidate_project.id,
                current_objective_id_set=candidate_project.active_objective_id
            )

        # Logic ID: STRAT-005 (Project switching uses interruption resistance)
        retention_margin = profile.interruption_resistance * profile.resistance_multiplier
        # Logic ID: STRAT-006 (Current project gets retention priority)
        effective_current_score = current.score + retention_margin

        if current.lock_until_tick > current_tick:
            # STRAT-236 (generalized): when a real world `state` is supplied and the triggering
            # threat has resolved (HP > 80%, no hostile within radius 10.0), the lock is treated
            # as already expired. `state is None` (the default for the 27 pre-existing direct
            # test call sites that predate this check) short-circuits `and` before
            # `_threat_resolved` is ever called, preserving today's behavior exactly. Computed
            # here, inside the lock-active gate, rather than above it, so the O(radius^2) spatial
            # scan in SpatialQueryService.nearby_entities() only runs when the current project is
            # actually locked — not on every evaluate_project_switch() call for an unlocked,
            # healthy entity (the common case across all 3 real production call sites).
            threat_resolved = state is not None and _threat_resolved(entity, state)

            if not threat_resolved:
                # STRAT-186 (generalized): the lock may be bypassed only for the unconditional "detour"
                # structural override, or when the candidate's score — expressed as a percentage of its own
                # system's declared max — both exceeds the current project's own normalized effective score
                # AND clears the urgency floor. This comparison is intentionally normalized and kept separate
                # from the raw `effective_current_score` comparison below: the raw formula and the unlocked
                # path must stay byte-identical (test_interruption_resistance_margin depends on this).
                if candidate_project.kind == "detour":
                    pass
                else:
                    candidate_max = _score_scale_max(candidate_project.kind)
                    current_max = _score_scale_max(current.kind)
                    candidate_pct = candidate_project.score / candidate_max
                    # TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG: the margin term is
                    # deliberately normalized against the universal baseline scale (_GOAL_UTILITY_SCORE_MAX),
                    # not current_max — current_max can be as small as _ADVENTURE_ROUTE_SCORE_MAX (2.9),
                    # which made retention_margin/current_max structurally dominate the comparison.
                    normalized_effective_current_pct = (current.score / current_max) + (retention_margin / _GOAL_UTILITY_SCORE_MAX)
                    if not (candidate_pct > normalized_effective_current_pct
                            and candidate_pct > _INTERRUPTION_URGENCY_FLOOR_PCT):
                        return None

        if candidate_project.score > effective_current_score:
            return StrategicUpdate(
                projects_add_or_update=[
                    replace(current, status=ProjectStatus.SUSPENDED),
                    candidate_project
                ],
                current_project_id_set=candidate_project.id,
                current_objective_id_set=candidate_project.active_objective_id
            )

        return None

    @staticmethod
    def resume_project(
        entity: EntityState,
        project_id: str
    ) -> Optional[StrategicUpdate]:
        project = entity.strategic.projects.get(project_id)
        if not project or project.status != ProjectStatus.SUSPENDED:
            return None

        resumed = replace(project, status=ProjectStatus.ACTIVE)
        return StrategicUpdate(
            projects_add_or_update=[resumed],
            current_project_id_set=project_id,
            current_objective_id_set=project.active_objective_id
        )

    @staticmethod
    def process_project_outcome(
        entity: EntityState,
        project_id: str,
        outcome: ProjectStatus,
        current_tick: int
    ) -> StrategicUpdate:
        """
        Record the final result of a project and apply learning effects.
        """
        project = entity.strategic.projects.get(project_id)
        if not project:
            return StrategicUpdate()

        from src.core.strategic import TurningPointState
        tps = []
        boredom_delta = {}

        if outcome == ProjectStatus.COMPLETED:
            # Record Victory
            tps.append(TurningPointState(
                id=f"victory_{project.kind}_{current_tick}",
                kind="great_victory" if project.score > 15.0 else "victory",
                tick=current_tick,
                salience=0.6
            ))
            # Decrement boredom for this kind (success makes it more rewarding)
            boredom_delta[project.kind] = -2.0
            
        elif outcome == ProjectStatus.ABANDONED:
            # Record Loss
            tps.append(TurningPointState(
                id=f"abandon_{project.kind}_{current_tick}",
                kind="loss",
                tick=current_tick,
                salience=0.4
            ))
            # Increment boredom for this kind
            boredom_delta[project.kind] = 5.0

        updated_project = replace(project, status=outcome)
        
        return StrategicUpdate(
            projects_add_or_update=[updated_project],
            turning_points_add=tps,
            boredom_delta=boredom_delta,
            current_project_id_set="" if entity.strategic.current_project_id == project_id else None
        )

    @staticmethod
    def process_outcome(
        observer: EntityState,
        subject_id: int,
        success: bool
    ) -> SocialUpdate:
        """
        VERIFIED v2: StrategicIntelligenceSystem.process_outcome
        """
        from src.systems.social_systems.appraisal import SocialAppraisalSystem
        outcome_quality = 1.0 if success else -1.0
        # recalibrate_trust in appraisal.py takes observer.social
        return SocialAppraisalSystem.recalibrate_trust(observer.social, subject_id, outcome_quality)

    @staticmethod
    def _resolve_active_objective(state: AuthoritativeState, entity: EntityState) -> Optional[StrategicUpdate]:
        strat = entity.strategic
        if not strat.current_project_id:
            return None
        
        project = strat.projects.get(strat.current_project_id)
        if not project or project.status != ProjectStatus.ACTIVE:
            return None
            
        obj = next((o for o in project.objectives if o.id == project.active_objective_id), None)
        if not obj or obj.status != ObjectiveStatus.ACTIVE:
            return None
            
        # 1. Reach Location Resolution
        if project.kind == "detour" and obj.kind == "reach_location":
            target_pos = obj.target_position
            if not target_pos and obj.target:
                try:
                    if isinstance(obj.target, str):
                        try:
                            import ast
                            target_pos = ast.literal_eval(obj.target)
                        except (ValueError, SyntaxError):
                            target_pos = None
                    else:
                        target_pos = obj.target
                except:
                    target_pos = None
            
            if target_pos:
                dist = abs(entity.navigation.position[0] - target_pos[0]) + abs(entity.navigation.position[1] - target_pos[1])
                if dist < 1.0:
                    resolved_obj = replace(obj, status=ObjectiveStatus.RESOLVED)
                    # For now, we assume 1 objective per detour project
                    return StrategicUpdate(
                        projects_add_or_update=[replace(project, objectives=[resolved_obj], status=ProjectStatus.COMPLETED)],
                        current_project_id_set="",
                        current_objective_id_set=""
                    )
        return None

    @staticmethod
    def evaluate_strategic_intent(
        state: AuthoritativeState,
        entity: EntityState,
        force: bool = False,
        cadence: SystemCadence | None = None
    ) -> StrategicUpdate:
        """
        Produce a collection of strategic intent updates for the next tick.
        """
        # Phase 5: Bounded frequency and early exit (Hardening)
        if not entity.lifecycle.active or not entity.combat.alive:
            return StrategicUpdate()
        
        # Legality Guard: Incapacitated entities skip strategic cycles
        if entity.identity.properties.get("status_frozen") or entity.identity.properties.get("status_stunned"):
            return StrategicUpdate()

        # Worker Fast-Path: If entity is a worker with an active, unblocked harvesting project and navigation target,
        # and biological needs are low, short-circuit redundant strategic evaluation.
        curr_proj_id = entity.strategic.current_project_id
        if curr_proj_id and entity.navigation.target:
            bio = entity.biological
            if bio.hunger < 50.0 and bio.sleep_debt < 50.0 and not entity.strategic.blockers:
                proj = entity.strategic.projects.get(curr_proj_id)
                if proj and proj.status == ProjectStatus.ACTIVE and proj.kind == "harvesting" and proj.active_objective_id:
                    try:
                        nid = int(proj.active_objective_id.split("_")[-1])
                        node = state.resource_nodes.get(nid)
                        if node and node.remaining_charges > 0 and node.cooldown_remaining <= 0:
                            return StrategicUpdate()
                    except Exception:
                        pass

        # 0. Strategic Memory (PH6: Lead Suppression)
        memory_upd = DetourSuggestionSystem.suppress_exhausted_leads(entity, state.tick)
        
        res_up = StrategicIntelligenceSystem._resolve_active_objective(state, entity)
        if res_up:
            return replace(res_up, 
                leads_add_or_update=memory_upd.leads_add_or_update,
                leads_remove=memory_upd.leads_remove
            )

        current_tick = state.tick
        strat = entity.strategic
        
        boredom_upd = {}
        if strat.current_project_id:
            proj = strat.projects.get(strat.current_project_id)
            if proj and proj.status == ProjectStatus.ACTIVE:
                boredom_upd[proj.kind] = 0.1
        
        # 1. Detour Completion & Project Resumption
        active_or_completed_detour = None
        if strat.current_project_id:
            p = strat.projects.get(strat.current_project_id)
            if p and p.kind == "detour":
                active_or_completed_detour = p
        else:
            # Check for a detour that just completed but isn't current anymore
            active_or_completed_detour = next((p for p in strat.projects.values() if p.kind == "detour" and p.status == ProjectStatus.COMPLETED), None)

        if active_or_completed_detour and active_or_completed_detour.status == ProjectStatus.COMPLETED:
            # Phase 6: Resolve associated blockers
            blockers_to_resolve = []
            for obj in active_or_completed_detour.objectives:
                if obj.status == ObjectiveStatus.RESOLVED:
                     blockers_to_resolve.extend(obj.blocker_ids)
            
            blocker_updates = []
            for b_id in blockers_to_resolve:
                b = strat.blockers.get(b_id)
                if b:
                    blocker_updates.append(replace(b, resolved=True))

            suspended = next((p for p in strat.projects.values() if p.status == ProjectStatus.SUSPENDED), None)
            if suspended:
                resumed_up = StrategicIntelligenceSystem.resume_project(entity, suspended.id)
                if resumed_up:
                    final_resumed = replace(
                        resumed_up,
                        projects_add_or_update=resumed_up.projects_add_or_update + [active_or_completed_detour],
                        blockers_add_or_update=resumed_up.blockers_add_or_update + blocker_updates,
                        boredom_delta=boredom_upd,
                        leads_add_or_update=memory_upd.leads_add_or_update,
                        leads_remove=memory_upd.leads_remove
                    )
                    return final_resumed

        # 2. Project Abandonment (PH6)
        if strat.current_project_id:
            project = strat.projects.get(strat.current_project_id)
            if project and project.status == ProjectStatus.ACTIVE:
                # Rejection backoff (STRAT-234 / TCK-20260627-P1A-REJECTION-BACKOFF):
                # Track consecutive ticks where every intent this entity emitted was
                # rejected.  When the counter reaches _MAX_CONSECUTIVE_REJECTIONS the
                # project is abandoned to stop the ~650-rejection/tick cascade observed
                # in D06 F3.  An empty results list (cadence skip / idle tick) does not
                # change the counter in either direction.
                _intent_results = entity.identity.latest_intent_results
                if _intent_results:
                    _any_accepted = any(r.accepted for r in _intent_results)
                    if not _any_accepted:
                        project = replace(project, failure_count=project.failure_count + 1)
                    elif project.failure_count > 0:
                        project = replace(project, failure_count=0)

                # If project has failed too many consecutive times, abandon it.
                if project.failure_count >= _MAX_CONSECUTIVE_REJECTIONS:
                    abandoned = replace(project, status=ProjectStatus.ABANDONED)
                    # Frustration penalty (Phase 6 spec)
                    boredom_upd[project.kind] = boredom_upd.get(project.kind, 0.0) + 0.5
                    return StrategicUpdate(
                        projects_add_or_update=[abandoned],
                        current_project_id_set="",
                        current_objective_id_set="",
                        boredom_delta=boredom_upd,
                        leads_add_or_update=memory_upd.leads_add_or_update,
                        leads_remove=memory_upd.leads_remove
                    )

                # Persist the updated failure_count when below the abandonment threshold.
                # Only return early when the entity has no unresolved blockers: if blockers
                # exist the entity still has a detour path (strategic progress is possible)
                # and the function must continue to the detour-suggestion section.
                # When blockers exist the increment is deferred to the next evaluation
                # where no blocker is active — acceptable because the cascade scenario
                # involves truly stuck entities that never generate actionable blockers.
                if project is not strat.projects.get(strat.current_project_id) and not strat.blockers:
                    return StrategicUpdate(
                        projects_add_or_update=[project],
                        leads_add_or_update=memory_upd.leads_add_or_update,
                        leads_remove=memory_upd.leads_remove
                    )

                if project.kind == "harvesting" and project.active_objective_id:
                    target_id_str = project.active_objective_id.split("_")[-1]
                    try:
                        target_id = int(target_id_str)
                        node = state.resource_nodes.get(target_id)
                        if not node or node.remaining_charges <= 0:
                            return StrategicUpdate(
                                projects_add_or_update=[replace(project, status=ProjectStatus.COMPLETED)],
                                current_project_id_set="",
                                current_objective_id_set="",
                                boredom_delta=boredom_upd,
                                leads_add_or_update=memory_upd.leads_add_or_update,
                                leads_remove=memory_upd.leads_remove
                            )
                    except ValueError:
                        pass
                
                # Hunger/fatigue: complete project when biological need is satisfied
                if project.kind == "hunger" and entity.biological.hunger < 20.0:
                    return StrategicUpdate(
                        projects_add_or_update=[replace(project, status=ProjectStatus.COMPLETED)],
                        current_project_id_set="",
                        current_objective_id_set="",
                        boredom_delta=boredom_upd,
                        leads_add_or_update=memory_upd.leads_add_or_update,
                        leads_remove=memory_upd.leads_remove
                    )
                if project.kind == "fatigue" and entity.biological.sleep_debt < 20.0:
                    return StrategicUpdate(
                        projects_add_or_update=[replace(project, status=ProjectStatus.COMPLETED)],
                        current_project_id_set="",
                        current_objective_id_set="",
                        boredom_delta=boredom_upd,
                        leads_add_or_update=memory_upd.leads_add_or_update,
                        leads_remove=memory_upd.leads_remove
                    )

                # career_change: complete once the entity's role is no longer CITIZEN -- a
                # discrete, verifiable, one-shot transition (unlike REGION_STABILIZATION, which
                # has no completion check anywhere in this scan and is left open-ended
                # deliberately -- see plan.md Design Decision 6). Without this check the project
                # would permanently occupy the entity's max_active_projects budget after a
                # successful transition.
                if project.kind == ProjectKind.CAREER_CHANGE and entity.identity.role != EntityRole.CITIZEN:
                    return StrategicUpdate(
                        projects_add_or_update=[replace(project, status=ProjectStatus.COMPLETED)],
                        current_project_id_set="",
                        current_objective_id_set="",
                        boredom_delta=boredom_upd,
                        leads_add_or_update=memory_upd.leads_add_or_update,
                        leads_remove=memory_upd.leads_remove
                    )

                # resolve_blocker timeout (TCK-20260817-STANDARD-HUNGER-STARVED-BY-RESOLVE-
                # BLOCKER-FLAT-UTILITY): unlike hunger/fatigue/harvesting/shopping above, this
                # GoalKind has no real completion condition -- some blockers (e.g. an "access"
                # blocker whose subject isn't parseable coordinates) can never actually be
                # reached, so the project would otherwise stay ACTIVE forever, permanently
                # occupying current_project_id and starving every other need. 50 ticks matches
                # this project's own creation-time lock_until_tick ceiling
                # (min(current_tick+10, current_tick+50), intelligence.py's generic project-
                # creation branch) -- if it hasn't resolved in that window, it isn't going to.
                # Abandoning alone isn't enough: ResolveBlockerScorer's utility is flat (80.0,
                # non-decaying), so an unsuppressed blocker would just re-win the very next
                # scoring pass and recreate the same project immediately. Suppressing the
                # specific blocker for 100 ticks (2x the attempt window) gives other needs a
                # real chance to win before this blocker is reconsidered.
                if project.kind == "resolve_blocker" and (current_tick - project.created_tick) >= 50:
                    blocker_updates = []
                    blocker_id = project.objectives[0].target if project.objectives else None
                    if blocker_id is not None:
                        b = strat.blockers.get(blocker_id)
                        if b and not b.resolved:
                            blocker_updates.append(replace(b, suppression_until_tick=current_tick + 100))
                    return StrategicUpdate(
                        projects_add_or_update=[replace(project, status=ProjectStatus.ABANDONED)],
                        current_project_id_set="",
                        current_objective_id_set="",
                        blockers_add_or_update=blocker_updates,
                        boredom_delta=boredom_upd,
                        leads_add_or_update=memory_upd.leads_add_or_update,
                        leads_remove=memory_upd.leads_remove
                    )

                # Milestone 8: Shop scarcity feedback
                if project.kind == "shopping" and project.active_objective_id:
                     target_id_str = project.active_objective_id.split("_")[-1]
                     try:
                         b_id = int(target_id_str)
                         building = state.buildings.get(b_id)
                         if not building or not building.functional:
                              return StrategicUpdate(
                                 projects_add_or_update=[replace(project, status=ProjectStatus.ABANDONED)],
                                 current_project_id_set="",
                                 current_objective_id_set="",
                                 boredom_delta=boredom_upd,
                                 leads_add_or_update=memory_upd.leads_add_or_update,
                                 leads_remove=memory_upd.leads_remove
                             )
                     except ValueError:
                         pass
                
                if strat.blockers and entity.identity.group_id is None:
                    detours = DetourSuggestionSystem.suggest_detours(entity, current_tick)
                    if detours:
                        best = detours[0]
                        obj = ObjectiveState(
                            id=f"detour_{best.blocker_id}_{current_tick}",
                            kind=best.objective_kind,
                            target=best.target,
                            status=ObjectiveStatus.ACTIVE,
                            blocker_ids=[best.blocker_id]
                        )
                        detour_proj = ProjectState(
                            id=f"proj_detour_{current_tick}",
                            kind="detour",
                            status=ProjectStatus.ACTIVE,
                            objectives=[obj],
                            active_objective_id=obj.id,
                            lock_until_tick=min(current_tick + 20, current_tick + 50),  # cap at 50 ticks
                            created_tick=current_tick,
                            score=best.score + 50.0
                        )
                        detour_up = StrategicIntelligenceSystem.evaluate_project_switch(entity, detour_proj, current_tick, state=state)
                        if detour_up:
                            final_detour = replace(detour_up, 
                                boredom_delta=boredom_upd,
                                leads_add_or_update=memory_upd.leads_add_or_update,
                                leads_remove=memory_upd.leads_remove
                            )
                            return final_detour
        
        # 4. Goal Scoring & Routine Biasing
        all_scores = GoalRegistry.get_all_scores(entity, state)

        # TCK-20260812-COMMITTED-INTENTION-SEQUENCE: materialize committed_intentions[0] (when
        # due) as an ordinary tier-5 candidate, injected before routine/role-boost so it is
        # boosted like a live scorer's candidate. "When due" reduces to head.status == "pending"
        # -- the arbiter's own lock/margin logic (evaluate_project_switch(), unmodified) does the
        # rest, exactly as it already does for every other tier-5 candidate.
        if strat.committed_intentions:
            head = strat.committed_intentions[0]
            if head.status == "pending":
                try:
                    head_kind = GoalKind(head.goal_kind)
                except ValueError:
                    head_kind = None
                if head_kind in _COMMITTED_INTENTION_ELIGIBLE_KINDS:
                    all_scores = all_scores + [GoalScore(
                        kind=head_kind,
                        utility=_COMMITTED_INTENTION_BASE_UTILITY,
                        target_id=head.target_hint,
                        target_pos=None,
                        metadata={"committed_intention_id": head.intention_id},
                    )]

        # PH9: Routine & Life-Rhythm Biasing
        all_scores = [
            replace(s, utility=s.utility + 
                    RoutineService.get_routine_utility_boost(entity, s.kind.lower(), state.world_time) +
                    RoutineService.get_role_utility_boost(entity, s.kind.lower()))
            for s in all_scores
        ]
        
        # PH7: Leadership Influence
        all_scores = PartyCoordinationSystem.apply_leadership_influence(entity, state, all_scores)
        
        modified_scores = ScoreModifierSystem.apply_modifiers(entity, state, all_scores)
        modified_scores.sort(key=lambda x: (-x.utility, x.kind))
        
        best_candidate = None
        for g_score in modified_scores:
            if g_score.utility < 20.0 or (g_score.target_id is None and g_score.target_pos is None):
                continue
            best_candidate = g_score
            break
            
        # Observability: Trace chosen goal and rejected alternatives
        if modified_scores:
            chosen_kind = getattr(best_candidate.kind, "value", best_candidate.kind) if best_candidate else "None"
            chosen_utility = best_candidate.utility if best_candidate else 0.0
            rejected = [f"{getattr(s.kind, 'value', s.kind)}:{s.utility:.1f}" for s in modified_scores if s != best_candidate]
            logger.debug(
                f"[Tick {state.tick}] Entity {entity.id} strategic goal selection: "
                f"chosen={chosen_kind} ({chosen_utility:.1f}), rejected={', '.join(rejected)}"
            )

            
        if best_candidate:
            existing = next((p for p in strat.projects.values() if p.kind == best_candidate.kind), None)
            
            if existing and existing.status == ProjectStatus.SUSPENDED:
                resumed_up = StrategicIntelligenceSystem.resume_project(entity, existing.id)
                if resumed_up:
                    return replace(resumed_up,
                         boredom_delta=boredom_upd,
                         leads_add_or_update=memory_upd.leads_add_or_update,
                         leads_remove=memory_upd.leads_remove
                    )
            
            if best_candidate.kind == GoalKind.ADVENTURE_ROUTE:
                # AC3/AC4: materialize via RouteToProjectMapper using the RAW route score
                # (metadata["raw_score"]), never best_candidate.utility. _score_scale_max()
                # (intelligence.py:89-107) classifies a RouteToProjectMapper-mapped
                # ProjectState.kind (a real ProjectKind) onto the 2.9-ceiling scale, not the
                # 100-ceiling scale `utility` was normalized onto (Step 2's normalization is
                # ONLY for tier-5 competition, not for the committed ProjectState.score).
                # Passing `utility` here would reproduce the
                # TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG defect class --
                # see design doc Sec 4's worked-through scale-mismatch arithmetic.
                candidate_proj, obj = RouteToProjectMapper.map_to_states(
                    family=best_candidate.metadata.get("route_family"),
                    entity_id=entity.id,
                    target=best_candidate.target_id,
                    target_pos=best_candidate.target_pos,
                    tick=current_tick,
                    score=best_candidate.metadata.get("raw_score", 0.0),
                )
                if candidate_proj is None or obj is None:
                    # Preserves RouteToProjectMapper's existing (None, None) contract
                    # (mapper.py:81-82, confirmed: DEFER_WITH_REASON -> get_kinds() returns
                    # (None, None) -> map_to_states() returns (None, None)). Should not
                    # normally be reached here since DEFER_WITH_REASON never clears the tier-5
                    # floor (AC5, Step 2's early return), but this is a defensive no-op, not an
                    # assumption that the mapper always returns non-None.
                    if boredom_upd:
                        return StrategicUpdate(boredom_delta=boredom_upd)
                    return StrategicUpdate()
            elif best_candidate.kind == GoalKind.SOCIAL_CONTRACT:
                # AC3/AC4/AC5/AC6 (ticket items 2,3,4,5,6): materialize a contract win into a
                # real ProjectKind-typed project, using proj_kind/obj_kind/obj_id_prefix already
                # resolved by SocialContractGoalScorer via ContractService.get_project_mapping()
                # and carried in metadata -- intelligence.py needs no new import of
                # ContractKind/ContractService/ObjectiveKind to build this branch (all resolved
                # upstream in the scorer).
                contract_id = best_candidate.metadata.get("contract_id")
                proj_kind = best_candidate.metadata.get("proj_kind")
                obj_kind = best_candidate.metadata.get("obj_kind")
                obj_id_prefix = best_candidate.metadata.get("obj_id_prefix", "obj_contract_")
                obj = ObjectiveState(
                    id=f"{obj_id_prefix}{contract_id}_t{current_tick}",
                    kind=obj_kind,
                    target=best_candidate.target_id,
                    target_position=best_candidate.target_pos,
                    status=ObjectiveStatus.ACTIVE,
                )
                candidate_proj = ProjectState(
                    id=f"proj_contract_{contract_id}_t{current_tick}",
                    kind=proj_kind,
                    status=ProjectStatus.ACTIVE,
                    objectives=[obj],
                    active_objective_id=obj.id,
                    # Preserves accept_contract()'s original 50-tick lock (contracts.py pre-edit
                    # line 180, confirmed read directly) -- deliberately NOT the generic branch's
                    # min(current_tick+10, current_tick+50) == current_tick+10 (Design
                    # Decision #10).
                    lock_until_tick=current_tick + 50,
                    created_tick=current_tick,
                    # NEVER best_candidate.utility -- utility is normalized onto the 100-ceiling
                    # scale for tier-5 competition only; ProjectState.score is read back through
                    # _score_scale_max()'s 2.9-ceiling scale once kind is a real ProjectKind.
                    # Passing utility here reproduces the
                    # TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG defect class.
                    score=best_candidate.metadata.get("raw_score", 0.0),
                )
            elif best_candidate.kind == GoalKind.REGION_STABILIZATION:
                # AC2/AC3/AC5/AC6: materialize a regional-danger win into a real
                # ProjectKind-typed project, using proj_kind/obj_kind already resolved by
                # RegionStabilizationGoalScorer via EventInterpreter.compute_danger_urgency()
                # and carried in metadata -- intelligence.py needs no new import of
                # ObjectiveKind/EventInterpreter to build this branch (all resolved upstream in
                # the scorer, see plan.md New Finding #11).
                region_id = best_candidate.metadata.get("region_id")
                proj_kind = best_candidate.metadata.get("proj_kind")
                obj_kind = best_candidate.metadata.get("obj_kind")
                obj = ObjectiveState(
                    id=f"obj_stabilize_{region_id}_t{current_tick}",
                    kind=obj_kind,
                    target=best_candidate.target_id,
                    target_position=best_candidate.target_pos,
                    status=ObjectiveStatus.ACTIVE,
                )
                candidate_proj = ProjectState(
                    id=f"project_stabilize_{region_id}_t{current_tick}",
                    kind=proj_kind,
                    status=ProjectStatus.ACTIVE,
                    objectives=[obj],
                    active_objective_id=obj.id,
                    # New Finding #10: the ORIGINAL bypass set no lock_until_tick at all (it
                    # never went through evaluate_project_switch()) -- no bespoke value to
                    # preserve, so this uses the SAME generic-branch default every other
                    # no-bespoke-lock GoalKind already gets, not a new invented value.
                    lock_until_tick=min(current_tick + 10, current_tick + 50),
                    created_tick=current_tick,
                    # NEVER best_candidate.utility -- see New Finding #7's full scale-mismatch
                    # analysis. utility is normalized onto the 100-ceiling scale for tier-5
                    # competition only; ProjectState.score is read back through
                    # _score_scale_max()'s 2.9-ceiling scale once kind is a real ProjectKind.
                    score=best_candidate.metadata.get("raw_score", 0.0),
                )
            elif best_candidate.kind == GoalKind.OCCUPATION_CHANGE:
                # AC1/AC2: materialize a CITIZEN -> SHOPKEEPER/WORKER/GUARD transition win into a
                # real ProjectKind-typed project, using proj_kind/obj_kind/dest_role already
                # resolved by OccupationChangeGoalScorer and carried in metadata.
                region_id = best_candidate.metadata.get("region_id")
                dest_role = best_candidate.metadata.get("dest_role")
                proj_kind = best_candidate.metadata.get("proj_kind")
                obj_kind = best_candidate.metadata.get("obj_kind")
                obj = ObjectiveState(
                    id=f"obj_career_{region_id}_t{current_tick}",
                    kind=obj_kind,
                    target=f"role_{dest_role}",
                    target_position=best_candidate.target_pos,
                    status=ObjectiveStatus.ACTIVE,
                )
                candidate_proj = ProjectState(
                    id=f"project_career_{region_id}_t{current_tick}",
                    kind=proj_kind,
                    status=ProjectStatus.ACTIVE,
                    objectives=[obj],
                    active_objective_id=obj.id,
                    lock_until_tick=min(current_tick + 10, current_tick + 50),
                    created_tick=current_tick,
                    # NEVER best_candidate.utility -- see region_stabilization_scorer.py's own
                    # New Finding #7 comment and
                    # TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG;
                    # _score_scale_max() (intelligence.py:108-126) classifies
                    # ProjectKind.CAREER_CHANGE onto the 2.9-ceiling scale, not the 100-ceiling
                    # utility scale.
                    score=best_candidate.metadata.get("raw_score", 0.0),
                )
            else:
                cand_kind_str = getattr(best_candidate.kind, "value", best_candidate.kind)
                obj = ObjectiveState(
                    id=f"{cand_kind_str}_{best_candidate.target_id}",
                    kind="reach_location",
                    target=best_candidate.target_id,
                    target_position=best_candidate.target_pos,
                    status=ObjectiveStatus.ACTIVE
                )
                candidate_proj = ProjectState(
                    id=f"proj_{cand_kind_str}_{current_tick}",
                    kind=best_candidate.kind,
                    status=ProjectStatus.ACTIVE,
                    objectives=[obj],
                    active_objective_id=obj.id,
                    lock_until_tick=min(current_tick + 10, current_tick + 50),  # cap at 50 ticks
                    created_tick=current_tick,
                    score=best_candidate.utility
                )

            at_capacity = len(strat.projects) >= strat.profile.max_active_projects
            if at_capacity and not existing:
                if boredom_upd:
                    return StrategicUpdate(boredom_delta=boredom_upd)
                return StrategicUpdate()

            switch_up = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate_proj, current_tick, state=state)
            if switch_up:
                # TCK-20260812-COMMITTED-INTENTION-SEQUENCE: win-transition bookkeeping. Only
                # fires when the winning candidate is THIS tick's synthesized committed-intention
                # candidate (matched by the metadata tag set at injection, above) -- a live
                # scorer's candidate for the same GoalKind must not advance the sequence.
                extra_ci = {}
                if strat.committed_intentions and best_candidate.metadata.get("committed_intention_id") == strat.committed_intentions[0].intention_id:
                    extra_ci["committed_intentions_add_or_update"] = [replace(strat.committed_intentions[0], status="active")]
                # TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE: restore
                # last_routing_family/last_routing_tick emission for a winning, accepted
                # ADVENTURE_ROUTE candidate. .value is required -- RouteFamily(str, Enum) means
                # str(route_family) yields "RouteFamily.X", not the deleted phase's original
                # "x" contract that event_shapers.py/event_extractor.py read.
                extra_routing = {}
                if best_candidate.kind == GoalKind.ADVENTURE_ROUTE:
                    route_family = best_candidate.metadata.get("route_family")
                    if route_family is not None:
                        extra_routing["last_routing_family_set"] = route_family.value
                        extra_routing["last_routing_tick_set"] = current_tick
                return replace(switch_up,
                    boredom_delta=boredom_upd,
                    leads_add_or_update=memory_upd.leads_add_or_update,
                    leads_remove=memory_upd.leads_remove,
                    **extra_ci,
                    **extra_routing
                )
            
            # Law 194-197: Enforce Strategic Bandwidth
            # Logic ID: 195, 196
            bandwidth_upd = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick)
            if bandwidth_upd.leads_remove or bandwidth_upd.concerns_remove:
                # Merge with current state of updates
                return StrategicUpdate(
                    leads_add_or_update=memory_upd.leads_add_or_update,
                    leads_remove=list(set(memory_upd.leads_remove + bandwidth_upd.leads_remove)),
                    concerns_remove=bandwidth_upd.concerns_remove,
                    overload_source_set=bandwidth_upd.overload_source_set,
                    overload_tick_set=bandwidth_upd.overload_tick_set,
                    boredom_delta=boredom_upd
                )

        if memory_upd.leads_add_or_update or memory_upd.leads_remove:
            return memory_upd

        if boredom_upd:
            return StrategicUpdate(boredom_delta=boredom_upd)
            
        return StrategicUpdate()

    @staticmethod
    def derive_cognition_profile(entity: EntityState) -> CognitionProfile:
        """
        VERIFIED v2: StrategicIntelligenceSystem.derive_cognition_profile
        """
        return CapacityService.derive_profile(entity)

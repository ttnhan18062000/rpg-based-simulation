"""MilitaryConflictPhase — WAR pair detection, siege, territory transfer, war exhaustion (E53Ca–Cd).

Phase 8e: runs once per tick after diplomatic_transitions (Phase 8d) inside
AuthoritativeApplyPipeline.refine().

E53Ca: skeleton — WAR pair detection + observability logging.
E53Cb: full siege loop — initiation, degradation, squad commitment, defender reinforcement.
E53Cc: territory transfer when siege_progress >= 1.0.
E53Cd: military_strength drain (0.001/tick per WAR faction), WAR_ENDED_EXHAUSTION event,
       orphaned siege cleanup when factions return to NEUTRAL.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState

from src.core.enums import DiplomaticState, EntityRole
from src.core.updates import FactionUpdate, StateUpdate, WorldUpdate

logger = logging.getLogger(__name__)

# Siege degradation constants (per-tick deltas, attacker side)
_SIEGE_SVC_DELTA = -0.05
_SIEGE_PROGRESS_DELTA = 0.05
# Defender reinforcement offsets (when >= 3 GUARD entities in contested region)
_DEF_SVC_DELTA = +0.02
_DEF_PROGRESS_DELTA = -0.02
_DEF_ENTITY_THRESHOLD = 3
# Max squad entities per faction per region
_MAX_SQUAD_SIZE = 5
# War exhaustion drain per WAR faction per tick (E53Cd)
_EXHAUSTION_DRAIN = 0.001
# Peace threshold: WAR→NEUTRAL fires autonomously (DiplomaticStateMachine) when both < 0.3
_PEACE_THRESHOLD = 0.3


class MilitaryConflictPhase:
    """Stateless sub-phase that orchestrates active military conflicts.

    Runs inside AuthoritativeApplyPipeline.refine() as Phase 8e.
    Reads AuthoritativeState (read-only); returns StateUpdate for authoritative apply-path.
    """

    @staticmethod
    def get_war_pairs(state: AuthoritativeState) -> List[Tuple[str, str]]:
        """Return lexicographically ordered list of faction ID pairs currently at WAR.

        Pairs are deduplicated: (a, b) only, never (b, a).
        """
        faction_ids = sorted(state.factions.keys())
        pairs: List[Tuple[str, str]] = []

        for i, fid_a in enumerate(faction_ids):
            fa = state.factions[fid_a]
            for fid_b in faction_ids[i + 1:]:
                rel = fa.diplomatic_relations.get(fid_b, DiplomaticState.NEUTRAL)
                if rel == DiplomaticState.WAR:
                    pairs.append((fid_a, fid_b))

        return pairs

    @staticmethod
    def _find_contested_region(
        state: AuthoritativeState,
        attacker_id: str,
        defender_id: str,
    ) -> Optional[str]:
        """Select the contested region for a WAR pair.

        Priority:
        1. Region already under active siege for this pair (continuation).
        2. First region in defender's territory (sorted for determinism).
        3. Nearest non-attacker region by bounding-box centroid distance.
        """
        # 1. Resume existing siege
        for rid, reg in sorted(state.regions.items()):
            if reg.siege_state is not None:
                if (reg.siege_state.attacker_faction_id == attacker_id
                        and reg.siege_state.defender_faction_id == defender_id):
                    return rid

        # 2. First region in defender's territory
        defender_fs = state.factions.get(defender_id)
        if defender_fs is not None and defender_fs.territory:
            return min(defender_fs.territory)

        # 3. Nearest non-attacker region by centroid distance
        attacker_fs = state.factions.get(attacker_id)
        attacker_territory: Set[str] = set(attacker_fs.territory) if attacker_fs else set()

        attacker_cx: float = 0.0
        attacker_cy: float = 0.0
        attacker_region_count = 0
        for rid in attacker_territory:
            reg = state.regions.get(rid)
            if reg is not None:
                attacker_cx += (reg.bounds[0] + reg.bounds[2]) / 2.0
                attacker_cy += (reg.bounds[1] + reg.bounds[3]) / 2.0
                attacker_region_count += 1
        if attacker_region_count > 0:
            attacker_cx /= attacker_region_count
            attacker_cy /= attacker_region_count

        best_rid: Optional[str] = None
        best_dist: float = float("inf")
        for rid, reg in sorted(state.regions.items()):
            if rid in attacker_territory:
                continue
            cx = (reg.bounds[0] + reg.bounds[2]) / 2.0
            cy = (reg.bounds[1] + reg.bounds[3]) / 2.0
            dist = abs(cx - attacker_cx) + abs(cy - attacker_cy)
            if dist < best_dist or (dist == best_dist and (best_rid is None or rid < best_rid)):
                best_dist = dist
                best_rid = rid

        return best_rid

    @staticmethod
    def _find_guard_entities_in_region(
        state: AuthoritativeState,
        region_id: str,
    ) -> List[int]:
        """Return sorted list of entity IDs with EntityRole.GUARD in the given region."""
        result: List[int] = []
        for eid, entity in state.entities.items():
            nav = getattr(entity, "navigation", None)
            if nav is None or nav.region_id != region_id:
                continue
            identity = getattr(entity, "identity", None)
            if identity is None:
                continue
            if identity.role == EntityRole.GUARD:
                result.append(eid)
        return sorted(result)

    @staticmethod
    def execute(state: AuthoritativeState) -> StateUpdate:
        """Detect active WAR pairs, run siege loop, drain exhaustion, emit peace events.

        E53Ca: detection + observability logging.
        E53Cb: siege initiation, degradation, squad GroupRecord, defender reinforcement.
        E53Cc: territory transfer when siege_progress >= 1.0.
        E53Cd: military_strength drain (0.001/tick per WAR faction); WAR_ENDED_EXHAUSTION
               WorldEvent when drain would push a faction below _PEACE_THRESHOLD; orphaned
               siege cleanup when factions return to NEUTRAL without completing a siege.

        Note on owner_faction_id: RegionState.owner_faction_id is Optional[int] while
        FactionState.faction_id is str. Authoritative ownership is FactionState.territory
        (updated via FactionUpdate.territory_add/remove). RegionState.owner_faction_id is
        NOT set during transfer (documented in FAC-010).

        Note on SEEK_PEACE directive: FactionDirective is transient and cannot flow through
        StateUpdate. The WAR→NEUTRAL transition is handled autonomously by
        DiplomaticStateMachine.compute_transitions() (Phase 8d) when both ms < 0.3.
        The WAR_ENDED_EXHAUSTION WorldEvent here signals the impending peace to observers.

        Args:
            state: Current authoritative world state (read-only).

        Returns:
            StateUpdate encoding all siege, transfer, and exhaustion effects for this tick.
        """
        if not state.factions:
            return StateUpdate()

        from src.core.state import GroupRecord, SiegeState
        from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory

        world_updates: Dict[str, WorldUpdate] = {}
        faction_updates: List[FactionUpdate] = []
        world_events: List[WorldEvent] = []
        groups_add: list = []

        # E53Cd: Orphaned siege cleanup — clear sieges where factions are no longer at WAR
        for rid, reg in sorted(state.regions.items()):
            if reg.siege_state is None:
                continue
            attacker = reg.siege_state.attacker_faction_id
            defender = reg.siege_state.defender_faction_id
            fa = state.factions.get(attacker)
            if fa is None or fa.diplomatic_relations.get(defender, DiplomaticState.NEUTRAL) != DiplomaticState.WAR:
                logger.info(
                    "SIEGE_ORPHAN_CLEANUP tick=%d region=%s attacker=%s defender=%s",
                    state.tick, rid, attacker, defender,
                )
                wu = world_updates.get(rid, WorldUpdate(region_id=rid))
                wu = wu.merge(WorldUpdate(
                    region_id=rid,
                    siege_state_clear=True,
                    service_availability_delta=+1.0,
                ))
                world_updates[rid] = wu

        war_pairs = MilitaryConflictPhase.get_war_pairs(state)
        if not war_pairs:
            return StateUpdate(world_updates=world_updates)

        # E53Cd: War exhaustion drain — deduplicated per faction (flat 0.001/tick regardless of war count)
        drained_factions: Set[str] = set()
        for fid_a, fid_b in war_pairs:
            for fid in (fid_a, fid_b):
                if fid in drained_factions:
                    continue
                drained_factions.add(fid)
                fs = state.factions[fid]
                new_ms = max(0.0, fs.military_strength - _EXHAUSTION_DRAIN)
                faction_updates.append(FactionUpdate(faction_id=fid, military_strength_set=new_ms))

            # Emit WAR_ENDED_EXHAUSTION when a faction crosses the peace threshold this tick
            ms_a = state.factions[fid_a].military_strength
            ms_b = state.factions[fid_b].military_strength
            new_ms_a = max(0.0, ms_a - _EXHAUSTION_DRAIN)
            new_ms_b = max(0.0, ms_b - _EXHAUSTION_DRAIN)
            if (new_ms_a < _PEACE_THRESHOLD or new_ms_b < _PEACE_THRESHOLD) and (
                    ms_a >= _PEACE_THRESHOLD or ms_b >= _PEACE_THRESHOLD):
                # At least one faction crosses the threshold this tick
                logger.info(
                    "WAR_EXHAUSTION_THRESHOLD tick=%d factions=%s:%s ms=%.3f:%.3f",
                    state.tick, fid_a, fid_b, new_ms_a, new_ms_b,
                )
                world_events.append(WorldEvent(
                    category=WorldEventCategory.WAR_ENDED_EXHAUSTION,
                    tick=state.tick,
                    subject=f"{fid_a}:{fid_b}",
                    payload={"ms_a": new_ms_a, "ms_b": new_ms_b},
                ))

        # Siege loop — one contested region per WAR pair
        for fid_a, fid_b in war_pairs:
            attacker_id, defender_id = fid_a, fid_b
            logger.debug("WAR_DETECTED tick=%d factions=%s:%s", state.tick, attacker_id, defender_id)

            contested_region_id = MilitaryConflictPhase._find_contested_region(
                state, attacker_id, defender_id
            )
            if contested_region_id is None:
                continue

            # Skip regions already queued for siege clearing (orphan cleanup above)
            existing_wu = world_updates.get(contested_region_id)
            if existing_wu is not None and existing_wu.siege_state_clear:
                continue

            reg = state.regions.get(contested_region_id)
            if reg is None:
                continue

            wu = existing_wu if existing_wu is not None else WorldUpdate(region_id=contested_region_id)

            # E53Cc: Territory transfer — siege_progress reached 1.0 on the previous tick
            if reg.siege_state is not None and reg.siege_state.siege_progress >= 1.0:
                logger.info(
                    "TERRITORY_TRANSFER tick=%d region=%s attacker=%s defender=%s",
                    state.tick, contested_region_id, attacker_id, defender_id,
                )
                wu = wu.merge(WorldUpdate(
                    region_id=contested_region_id,
                    siege_state_clear=True,
                    service_availability_delta=+1.0,
                ))
                faction_updates.append(FactionUpdate(
                    faction_id=attacker_id,
                    territory_add=(contested_region_id,),
                ))
                faction_updates.append(FactionUpdate(
                    faction_id=defender_id,
                    territory_remove=(contested_region_id,),
                ))
                world_events.append(WorldEvent(
                    category=WorldEventCategory.TERRITORY_TRANSFERRED,
                    tick=state.tick,
                    subject=f"{attacker_id}:{defender_id}:{contested_region_id}",
                    payload={"siege_progress": 1.0},
                ))

            else:
                # Siege initiation (first tick with no active siege for this pair)
                if reg.siege_state is None:
                    wu = wu.merge(WorldUpdate(
                        region_id=contested_region_id,
                        siege_state_set=SiegeState(
                            attacker_faction_id=attacker_id,
                            defender_faction_id=defender_id,
                            siege_progress=0.0,
                            started_tick=state.tick,
                        ),
                    ))
                    world_events.append(WorldEvent(
                        category=WorldEventCategory.SIEGE_BEGINS,
                        tick=state.tick,
                        subject=contested_region_id,
                    ))

                # Siege degradation: -5% service_availability, +5% siege_progress per tick
                wu = wu.merge(WorldUpdate(
                    region_id=contested_region_id,
                    service_availability_delta=_SIEGE_SVC_DELTA,
                    siege_progress_delta=_SIEGE_PROGRESS_DELTA,
                ))

                # Defender reinforcement: ≥ 3 GUARD entities offset attacker progress
                guard_ids = MilitaryConflictPhase._find_guard_entities_in_region(
                    state, contested_region_id
                )
                if len(guard_ids) >= _DEF_ENTITY_THRESHOLD:
                    wu = wu.merge(WorldUpdate(
                        region_id=contested_region_id,
                        service_availability_delta=_DEF_SVC_DELTA,
                        siege_progress_delta=_DEF_PROGRESS_DELTA,
                    ))

                # Squad commitment: up to 5 GUARD entities → GroupRecord with FACTION_SQUAD role
                squad_ids = guard_ids[:_MAX_SQUAD_SIZE]
                if squad_ids:
                    cx, cy = (
                        ((reg.bounds[0] + reg.bounds[2]) / 2.0,
                         (reg.bounds[1] + reg.bounds[3]) / 2.0)
                        if reg.bounds else (0.0, 0.0)
                    )
                    roles = {eid: "FACTION_SQUAD" for eid in squad_ids}
                    group_id = abs(hash((contested_region_id, attacker_id, state.tick))) % (2 ** 31)
                    groups_add.append(GroupRecord(
                        id=group_id,
                        leader_id=squad_ids[0],
                        member_ids=set(squad_ids),
                        anchor=(cx, cy),
                        roles=roles,
                        last_updated_tick=state.tick,
                    ))

            world_updates[contested_region_id] = wu

        return StateUpdate(
            world_updates=world_updates,
            faction_updates=faction_updates,
            world_events_add=world_events,
            groups_add_or_update=groups_add,
        )

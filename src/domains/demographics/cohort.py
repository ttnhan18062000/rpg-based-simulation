# Compliance IDs: WORLD-DEMO-001
# src/domains/demographics/cohort.py
# Epic 5.2A: PopulationCohort durable model + DemographicCycleService birth/death cycle.
# Epic 5.2B: Migration pressure + cohort movement.
# TCK-20260619-E52A-COHORT-MODEL, TCK-20260619-E52B-MIGRATION
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Dict, List, Tuple

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, RegionState
    from src.core.updates import StateUpdate, WorldUpdate


@dataclass(frozen=True, slots=True)
class PopulationCohort:
    """
    Durable per-region demographic cohort model.

    Represents one age-bracket slice of a region's abstract population.
    Drives birth/death cycle every COHORT_INTERVAL ticks.

    Fields
    ------
    bracket : str
        Age bracket identifier — "young" | "adult" | "elder".
    count : int
        Abstract population count for this bracket in this region.
    birth_rate : float
        Fraction of `count` that produce new young entities per 200-tick cycle.
    mortality_rate : float
        Fraction of `count` that die per 200-tick cycle.
    migration_threshold : float
        Regional scarcity level above which this cohort emigrates (used by E52B).
    """

    bracket: str
    count: int = 0
    birth_rate: float = 0.02          # births per 200-tick cycle as fraction of count
    mortality_rate: float = 0.01      # deaths per 200-tick cycle as fraction of count
    migration_threshold: float = 0.7  # scarcity above this → emigrate (E52B)


# ---------------------------------------------------------------------------
# E52B: Migration helpers — pure functions, no side effects
# ---------------------------------------------------------------------------

def compute_regional_scarcity(region_id: str, state: "AuthoritativeState") -> float:
    """
    Compute scarcity for a region as 1.0 - mean(remaining/max) across all resource
    nodes whose position falls within that region's bounds.

    Returns 1.0 (maximum scarcity) if the region has no resource nodes.

    Spec ref: TCK-20260619-E52B-MIGRATION §Scope — "aggregate remaining_charges /
    max_charges across all resource nodes in the region; zero resources = scarcity 1.0."
    """
    region = state.regions.get(region_id)
    if region is None:
        return 1.0

    xmin, ymin, xmax, ymax = region.bounds
    total_ratio = 0.0
    count = 0

    for node in state.resource_nodes.values():
        px, py = node.position
        if xmin <= px < xmax and ymin <= py < ymax:
            if node.max_charges > 0:
                total_ratio += node.remaining_charges / node.max_charges
            count += 1

    if count == 0:
        return 1.0
    return 1.0 - (total_ratio / count)


def find_adjacent_regions(region_id: str, state: "AuthoritativeState") -> List["RegionState"]:
    """
    Return all regions that share a boundary edge with the named region.

    Adjacency definition (from docs/mechanics/06_worldbuilding_foundation.md):
    Regions are strictly disjoint by bounds. Two regions are adjacent when their
    bounds share exactly one edge: one axis interval aligns exactly (e.g.
    source.xmax == neighbour.xmin) while the other axis intervals overlap
    (non-degenerate — i.e. the intersection has positive length).

    Results are sorted by region id for determinism.
    """
    source = state.regions.get(region_id)
    if source is None:
        return []

    sxmin, symin, sxmax, symax = source.bounds
    adjacent: List["RegionState"] = []

    for rid, region in sorted(state.regions.items()):
        if rid == region_id:
            continue
        rxmin, rymin, rxmax, rymax = region.bounds

        # Share a vertical edge: source left == neighbour right (or vice versa)
        shares_vertical = (sxmin == rxmax or sxmax == rxmin)
        # Share a horizontal edge: source bottom == neighbour top (or vice versa)
        shares_horizontal = (symin == rymax or symax == rymin)

        # Y-intervals overlap (non-degenerate) — used when sharing a vertical edge
        y_overlap = min(symax, rymax) > max(symin, rymin)
        # X-intervals overlap (non-degenerate) — used when sharing a horizontal edge
        x_overlap = min(sxmax, rxmax) > max(sxmin, rxmin)

        if (shares_vertical and y_overlap) or (shares_horizontal and x_overlap):
            adjacent.append(region)

    return adjacent


def _check_migration(
    region_id: str,
    region: "RegionState",
    state: "AuthoritativeState",
    tick: int,
) -> Tuple[Dict[str, "WorldUpdate"], List]:
    """
    E52B: Evaluate migration pressure for one region.

    For each cohort whose scarcity exceeds migration_threshold:
    - Compute 30% emigrant count (min 1)
    - Find adjacent region with lowest scarcity (deterministic: sort by id as tiebreak)
    - Build WorldUpdate pairs: source count reduced, target count increased

    Returns (world_updates dict, world_events list).
    """
    from src.core.updates import WorldUpdate
    from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory

    if not region.population_cohorts:
        return {}, []

    scarcity = compute_regional_scarcity(region_id, state)
    world_updates: Dict[str, WorldUpdate] = {}
    world_events = []

    # Snapshot source cohorts; we accumulate modifications across brackets
    # (each bracket is independent — no cross-cohort interaction)
    source_cohorts: Dict[str, PopulationCohort] = dict(region.population_cohorts)
    source_changed = False

    for bracket in sorted(region.population_cohorts.keys()):
        cohort = region.population_cohorts[bracket]
        if scarcity <= cohort.migration_threshold:
            continue

        adjacent = find_adjacent_regions(region_id, state)
        if not adjacent:
            continue

        # Target = lowest-scarcity adjacent region; sort by id for determinism on ties
        target = min(
            adjacent,
            key=lambda r: (compute_regional_scarcity(r.id, state), r.id),
        )

        emigrant_count = max(1, int(cohort.count * 0.30))

        # --- Source update ---
        new_source_count = max(0, cohort.count - emigrant_count)
        source_cohorts[bracket] = replace(cohort, count=new_source_count)
        source_changed = True

        # --- Target update ---
        target_region = state.regions[target.id]
        # Build target cohorts dict (existing + absorbed emigrants)
        existing_target_wu = world_updates.get(target.id)
        if existing_target_wu is not None and existing_target_wu.population_cohorts_set is not None:
            target_cohorts: Dict[str, PopulationCohort] = dict(existing_target_wu.population_cohorts_set)
        else:
            target_cohorts = dict(target_region.population_cohorts)

        if bracket in target_cohorts:
            existing_tc = target_cohorts[bracket]
            target_cohorts[bracket] = replace(existing_tc, count=existing_tc.count + emigrant_count)
        else:
            # New bracket in target — use same rates as emigrating cohort
            target_cohorts[bracket] = replace(cohort, count=emigrant_count)

        new_target_wu = WorldUpdate(
            region_id=target.id,
            population_cohorts_set=target_cohorts,
        )
        if existing_target_wu is not None:
            world_updates[target.id] = existing_target_wu.merge(new_target_wu)
        else:
            world_updates[target.id] = new_target_wu

        # --- Event ---
        world_events.append(WorldEvent(
            category=WorldEventCategory.POPULATION_MIGRATION,
            tick=tick,
            region_id=region_id,
            subject=f"cohort:{bracket}→{target.id}",
            severity=emigrant_count / max(1, cohort.count),
        ))

    if source_changed:
        existing_src_wu = world_updates.get(region_id)
        new_src_wu = WorldUpdate(
            region_id=region_id,
            population_cohorts_set=source_cohorts,
        )
        if existing_src_wu is not None:
            world_updates[region_id] = existing_src_wu.merge(new_src_wu)
        else:
            world_updates[region_id] = new_src_wu

    return world_updates, world_events


class DemographicCycleService:
    """
    Pure decision logic — reads state, returns StateUpdate.
    Never mutates AuthoritativeState directly.

    Birth/death cycle runs every COHORT_INTERVAL ticks.
    Net positive → update cohort count upward (abstractly represents new young).
    Net negative → update cohort count downward (deaths).
    """

    COHORT_INTERVAL: int = 200  # ticks — matches ResourceEcologyService.ECOLOGY_INTERVAL

    @staticmethod
    def process_demographics(state: "AuthoritativeState", tick: int) -> "StateUpdate":
        """
        Apply birth/death rates to all regions' cohorts.

        Returns a StateUpdate with:
        - world_updates: per-region WorldUpdate with population_cohorts_set containing
          updated cohort counts after net birth/death.
        - world_events_add: one WorldEvent per cohort change for observability.

        Returns an empty StateUpdate on off-cycle ticks.
        """
        from src.core.updates import StateUpdate, WorldUpdate
        from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory

        if tick % DemographicCycleService.COHORT_INTERVAL != 0:
            return StateUpdate()

        world_updates: Dict[str, WorldUpdate] = {}
        world_events = []

        for region_id, region in state.regions.items():
            if not region.population_cohorts:
                continue

            new_cohorts: Dict[str, PopulationCohort] = dict(region.population_cohorts)
            region_changed = False

            for bracket, cohort in region.population_cohorts.items():
                births = cohort.count * cohort.birth_rate
                deaths = cohort.count * cohort.mortality_rate
                net = int(births - deaths)
                if net == 0:
                    continue

                new_count = max(0, cohort.count + net)
                new_cohorts[bracket] = replace(cohort, count=new_count)
                region_changed = True

                event_category = (
                    WorldEventCategory.POPULATION_BIRTH
                    if net > 0
                    else WorldEventCategory.POPULATION_DEATH
                )
                world_events.append(WorldEvent(
                    category=event_category,
                    tick=tick,
                    region_id=region_id,
                    subject=f"cohort:{bracket}",
                    severity=abs(net) / max(1, cohort.count),
                ))

            if region_changed:
                existing = world_updates.get(region_id)
                if existing is not None:
                    world_updates[region_id] = replace(
                        existing, population_cohorts_set=new_cohorts
                    )
                else:
                    world_updates[region_id] = WorldUpdate(
                        region_id=region_id,
                        population_cohorts_set=new_cohorts,
                    )

        # E52B: Migration pass — runs after birth/death, merges into same StateUpdate
        for region_id, region in sorted(state.regions.items()):
            if not region.population_cohorts:
                continue
            mig_updates, mig_events = _check_migration(region_id, region, state, tick)
            for rid, wu in mig_updates.items():
                existing = world_updates.get(rid)
                if existing is not None:
                    world_updates[rid] = existing.merge(wu)
                else:
                    world_updates[rid] = wu
            world_events.extend(mig_events)

        if not world_updates and not world_events:
            return StateUpdate()

        return StateUpdate(
            world_updates=world_updates,
            world_events_add=world_events,
        )

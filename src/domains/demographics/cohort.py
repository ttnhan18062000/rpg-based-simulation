# Compliance IDs: WORLD-DEMO-001
# src/domains/demographics/cohort.py
# Epic 5.2A: PopulationCohort durable model + DemographicCycleService birth/death cycle.
# TCK-20260619-E52A-COHORT-MODEL
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


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

        if not world_updates and not world_events:
            return StateUpdate()

        return StateUpdate(
            world_updates=world_updates,
            world_events_add=world_events,
        )

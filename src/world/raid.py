# Compliance IDs: WORLD-032, WORLD-033, WORLD-034
from __future__ import annotations
import math
from dataclasses import replace
from typing import Any, List, Optional, TYPE_CHECKING
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate
from src.core.enums import Faction, Domain
from src.platform.rng import DeterministicRNG

if TYPE_CHECKING:
    from src.systems.world_systems.generator import EntityGenerator

class RaidService:
    """
    Orchestrates faction raids against the town.
    """
    
    RAID_INTERVAL_DAYS = 5
    TICKS_PER_DAY = 100
    RAID_BASE_SIZE = 3
    SANCTUARY_RADIUS = 15
    
    @staticmethod
    def city_places(state: AuthoritativeState) -> List[Any]:
        """Every `PlaceKind.CITY` place, in a stable id order.

        The shared "what counts as a raidable settlement" definition for both raid callers
        (TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION). The two
        callers select *within* this set differently and deliberately: the camp path takes the
        city nearest its camp, while the global path has no anchor to be near and picks
        deterministically. Sorted by id so the global pick does not depend on dict ordering.
        """
        from src.core.state import PlaceKind

        return sorted(
            (p for p in state.places.values() if p.kind == PlaceKind.CITY),
            key=lambda p: p.place_id,
        )

    @staticmethod
    def global_raid_anchor(state: AuthoritativeState) -> Optional[tuple]:
        """Where the global raid should converge, or None if the world offers nowhere.

        Preference order, and the reason for each:
        1. A `PlaceKind.CITY` -- the thing a raid is actually *for*. Every corpus world has
           exactly one (verified at 958aa103d).
        2. Otherwise a region's centre. This fallback exists so the fix stays a *placement* fix:
           requiring a city would also change how *often* raids fire, suppressing them entirely
           in city-less worlds. That is a frequency change this ticket does not intend, and it
           regressed `tests/integration/world/test_phase9_stability.py::test_1000_tick_stability`
           when tried.
        3. Only a world with neither cities nor regions yields None, and then no raid fires --
           there is nowhere inside the playable world to put one.

        Both selections are deterministic: cities and regions are each sorted by id and indexed
        with the seeded RNG, so no choice depends on dict ordering.
        """
        rng = DeterministicRNG(state.seed)

        cities = RaidService.city_places(state)
        if cities:
            # sub_id=1 keeps this draw independent of spawn_raid's own angle draw, which uses
            # (Domain.CALAMITY, state.tick, 0) with the default sub_id.
            idx = rng.get_int(Domain.CALAMITY, state.tick, 0, 0, len(cities) - 1, sub_id=1)
            return cities[idx].position

        regions = sorted(state.regions.values(), key=lambda r: r.id)
        if regions:
            idx = rng.get_int(Domain.CALAMITY, state.tick, 0, 0, len(regions) - 1, sub_id=2)
            return regions[idx].center

        return None

    @staticmethod
    def check_for_raid(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
        """
        Checks if the global (non-camp) tick-cadence raid should spawn and returns the update.

        TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION: this method used
        to pass `origin=(0, 0), target=(0, 0)` literally, which encoded a single-settlement-at-origin
        world. Measured consequence in multi-region corpus worlds: every raider spawned on the
        radius-25 ring around the world origin, landed outside every region with `region_id=None`,
        and never moved again -- the mechanic consumed entity ids and produced no raid.

        It now raids a real place in the world. `origin` and `target` are both the anchor chosen by
        `global_raid_anchor()`, which makes `spawn_raid` place the raiders on that anchor's outskirts
        (the ring is drawn around `origin`) and send them at it. This is deliberately a *placement*
        fix and not a frequency one: the anchor falls back from a city to a region centre so raids
        keep firing exactly as often as before, in every world that has anywhere to raid at all.

        The camp-triggered path (src/world/camp.py) is unchanged: it still calls spawn_raid()
        directly with its own origin/target and its own cadence gate, since this method's
        tick%raid_interval_ticks check does not apply to that call site.
        """
        raid_interval_ticks = RaidService.RAID_INTERVAL_DAYS * RaidService.TICKS_PER_DAY
        if state.tick % raid_interval_ticks != 0 or state.tick == 0:
            return StateUpdate()

        anchor = RaidService.global_raid_anchor(state)
        if anchor is None:
            return StateUpdate()

        raid_size = RaidService.RAID_BASE_SIZE + state.maturity
        return RaidService.spawn_raid(
            state, generator, origin=anchor, target=anchor, raid_size=raid_size,
        )

    @staticmethod
    def spawn_raid(
        state: AuthoritativeState,
        generator: EntityGenerator,
        origin: tuple,
        target: tuple,
        raid_size: int,
    ) -> StateUpdate:
        """
        Composes `raid_size` raiders anchored around `origin`, all targeting `target`. No cadence
        gate of its own -- callers decide when a raid is eligible to fire.
        """
        # Calculate spawn position at a distance from origin, scattered by angle.
        # Using stateless deterministic RNG.
        rng = DeterministicRNG(state.seed)
        angle = rng.get_float(Domain.CALAMITY, state.tick, 0) * 2 * math.pi
        dist = RaidService.SANCTUARY_RADIUS + 10

        spawn_pos = (
            origin[0] + int(math.cos(angle) * dist),
            origin[1] + int(math.sin(angle) * dist)
        )

        entities_add = []
        for i in range(raid_size):
            # Scatter coordinates in a small grid around the base spawn position to avoid overlap
            ox = spawn_pos[0] + (i % 3) - 1
            oy = spawn_pos[1] + (i // 3) - 1

            # Spawn raid mobs (Tier 3-4 difficulty)
            mob = generator.spawn_monster(
                state=state,
                kind="goblin_raider",
                pos=(ox, oy),
                difficulty_tier=4
            )
            # TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION: a raid mob's
            # target above is a raw navigation assignment with no accompanying strategic project
            # -- nothing marks "this entity is mid-raid" to the goal-scoring system, so any scorer
            # that later assigns this entity a real project (confirmed: GuildNeedScorer, once
            # ENABLE_GUILD_QUEST_GENERATION actually reached a real run for the first time) freely
            # overwrites this navigation.target with its own. Real mob factions elsewhere
            # (frontier_marches' own scout/sentinel/leader) legitimately DO run the generic
            # project/goal system, so gating GuildNeedScorer itself by faction was rejected --
            # it broke that live, intended behavior instead of fixing this one. A raid mob's own
            # entire purpose is the raid; it doesn't need or use the project system at all, so
            # max_active_projects=0 is the correct, narrow signal: every capacity-gated scorer
            # (GuildNeedScorer today, any future one) sees zero spare capacity and no-ops,
            # without touching any scorer's own logic or affecting non-raid monsters.
            mob = replace(
                mob,
                navigation=replace(mob.navigation, target=target),
                strategic=replace(
                    mob.strategic,
                    profile=replace(mob.strategic.profile, max_active_projects=0),
                ),
            )
            entities_add.append(mob)

        return StateUpdate(entities_add=entities_add)

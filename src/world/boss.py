# Compliance IDs: WORLD-035, WORLD-036, WORLD-037
# src/world/boss.py
from __future__ import annotations
import math
from typing import TYPE_CHECKING, List, Optional
from src.core.enums import Domain, EntityRole
from src.core.state import PlaceKind
from src.core.updates import StateUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, RegionState
    from src.systems.world_systems.generator import EntityGenerator

class BossService:
    """
    Manages world boss spawning and resolution.
    """
    
    BOSS_SPAWN_THRESHOLD = 50.0 # Maturity or Threat threshold
    
    @staticmethod
    def check_for_boss_spawn(
        state: AuthoritativeState,
        generator: EntityGenerator,
    ) -> StateUpdate:
        """
        Deterministic, idempotent boss spawning.

        LAW:
            At most one active living world boss may exist per spawn/home region.

        Important:
            Boss idempotency must NOT depend only on current position. A boss can
            move outside its original region after spawning. If we map bosses by
            current position only, the original region may incorrectly spawn a
            second boss.

        Boss ownership source:
            1. identity.properties["boss_region_id"]
            2. strategic.home_region_id
            3. fallback: current position region
        """
        from dataclasses import replace

        from src.core.state import ItemStack
        from src.engine.legality import LegalityServiceV2

        def _is_active_living_boss(entity) -> bool:
            return (
                entity.kind == "world_boss"
                and entity.lifecycle.active
                and entity.combat.alive
            )

        def _boss_region_id(entity) -> str | None:
            # Primary: immutable spawn-region metadata.
            region_id = entity.identity.properties.get("boss_region_id")
            if region_id:
                return region_id

            # Secondary: strategic home region, if your strategic component uses it.
            region_id = getattr(entity.strategic, "home_region_id", None)
            if region_id:
                return region_id

            # Fallback only for old bosses that do not have metadata yet.
            region = LegalityServiceV2.get_region_for_position(
                entity.navigation.position,
                state,
            )

            return region.id if region else None

        region_boss_map = {}

        for entity in state.entities.values():
            if not _is_active_living_boss(entity):
                continue

            region_id = _boss_region_id(entity)

            if region_id is not None:
                region_boss_map[region_id] = entity

        entities_add = []

        for region_id, region in state.regions.items():
            if region_id in region_boss_map:
                continue

            if not (
                state.maturity >= BossService.BOSS_SPAWN_THRESHOLD
                and region.trauma_score >= 20.0
            ):
                continue

            xmin, ymin, xmax, ymax = region.bounds
            cx = (xmin + xmax) / 2.0
            cy = (ymin + ymax) / 2.0

            # Rule: never inside town/sanctuary.
            if abs(cx) < 20 and abs(cy) < 20:
                cx = math.copysign(25, cx)
                cy = math.copysign(25, cy)

            spawn_pos = (
                int(cx),
                int(cy),
            )

            boss = generator.spawn_monster(
                spawn_pos,
                state=state,
                kind="ancient_sentinel",
                difficulty_tier=5,
            )

            boss = replace(
                boss,
                kind="world_boss",
                lifecycle=replace(
                    boss.lifecycle,
                    active=True,
                ),
                identity=replace(
                    boss.identity,
                    properties={
                        **boss.identity.properties,
                        "boss_region_id": region_id,
                        "boss_spawn_tick": state.tick,
                    },
                ),
                strategic=replace(
                    boss.strategic,
                    home_region_id=region_id,
                ),
                inventory=replace(
                    boss.inventory,
                    items=[
                        ItemStack(
                            item_id="ancient_core",
                            quantity=1,
                        )
                    ],
                ),
            )

            entities_add.append(boss)

            # Protect this same call too.
            region_boss_map[region_id] = boss

        return StateUpdate(
            entities_add=entities_add,
        )

    @staticmethod
    def check_for_lair_spawn(
        state: AuthoritativeState,
        generator: EntityGenerator,
    ) -> StateUpdate:
        """
        Deterministic, idempotent Lair spawning.

        LAW:
            At most one active living Lair occupant may exist per LAIR-kind Place.

        Lair occupancy source:
            identity.properties["lair_place_id"]

        Generalizes check_for_boss_spawn's entity-property idempotency pattern from
        per-region_id to per-place_id keying, so multiple LAIR-kind Places in one
        Region each get an independent, idempotent spawn slot. See
        TCK-20260904-LAIR-ENTITY-ANCHOR plan.md Decision #1: PlaceState.occupant_entity_id
        stays write-never here (Option A) -- the lock lives on the occupant entity, not
        the Place.
        """
        from dataclasses import replace

        def _is_active_living_lair_occupant(entity) -> bool:
            return (
                entity.kind == "dragonkin"
                and entity.lifecycle.active
                and entity.combat.alive
            )

        def _lair_place_id(entity) -> str | None:
            # No fallback layer here (unlike _boss_region_id): Lair occupancy is
            # entirely new, so there are no pre-existing occupants without this
            # metadata to support.
            return entity.identity.properties.get("lair_place_id")

        place_occupant_map = {}

        for entity in state.entities.values():
            if not _is_active_living_lair_occupant(entity):
                continue

            place_id = _lair_place_id(entity)

            if place_id is not None:
                place_occupant_map[place_id] = entity

        entities_add = []

        for place_id, place in state.places.items():
            if place.kind != PlaceKind.LAIR:
                continue

            if place_id in place_occupant_map:
                continue

            region = state.regions.get(place.region_id)
            if region is None:
                continue

            if not (
                state.maturity >= BossService.BOSS_SPAWN_THRESHOLD
                and region.trauma_score >= 20.0
            ):
                continue

            occupant = generator.spawn_monster(
                place.position,
                state=state,
                kind="dragonkin",
                difficulty_tier=5,
            )

            occupant = replace(
                occupant,
                lifecycle=replace(
                    occupant.lifecycle,
                    active=True,
                ),
                identity=replace(
                    occupant.identity,
                    properties={
                        **occupant.identity.properties,
                        "lair_place_id": place_id,
                        "lair_spawn_tick": state.tick,
                    },
                ),
            )

            entities_add.append(occupant)

            # Protect this same call too.
            place_occupant_map[place_id] = occupant

        return StateUpdate(
            entities_add=entities_add,
        )

    @staticmethod
    def resolve_boss_death(state: AuthoritativeState, boss_id: int) -> StateUpdate:
        """
        Rule: Boss death provides high-tier loot via transaction law.
        """
        # This is handled by LootSystem/QuestResolution if tied to a quest,
        # but here we ensure regional threat reduction.
        boss = state.entities.get(boss_id)
        if not boss: return StateUpdate()
        
        from src.engine.legality import LegalityServiceV2
        region = LegalityServiceV2.get_region_for_position(boss.navigation.position, state)
        if not region: return StateUpdate()
        
        from src.core.updates import WorldUpdate
        w_upd = WorldUpdate(
            region_id=region.id,
            trauma_score_delta=-20.0 # Significant reduction
        )
        
        return StateUpdate(world_updates={region.id: w_upd})

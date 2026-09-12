from __future__ import annotations

from typing import Dict, Optional, Tuple

from src.core.state import EntityState
from src.entities.archetype_factory import ArchetypeEntityFactory, EntitySpawnContext
from src.entities.contract_builder import resolved_archetype_to_contract
from src.worldassembly.context import CompileContext
from src.worldassembly.models import ResolvedEntityProfile


class WorldEntitySpawner:
    """
    Converts CompileContext entity profiles into EntityState objects.

    Primary path: archetype-native — EntityArchetypeResolver → resolved_archetype_to_contract
    → ArchetypeEntityFactory.build_entity(). Used for profiles that carry an archetype_id.

    Legacy guard: profiles without archetype_id fall back to V2EntityBuilder with explicit
    labelling. This path exists for non-archetype-backed entities (town NPCs, synthetic
    entities) that have no catalog archetype definition.
    """

    def __init__(self) -> None:
        self._factory = ArchetypeEntityFactory()

    def spawn_from_context(
        self,
        ctx: CompileContext,
        catalog_repo: object,
        *,
        base_entity_id: int = 1,
        default_position: Tuple[float, float] = (0.0, 0.0),
        seed: int = 42,
    ) -> Dict[int, EntityState]:
        """
        Spawn EntityState objects for all entity profiles in a CompileContext.

        Returns a dict mapping entity_id (int) to EntityState.
        Entity IDs are assigned sequentially starting from base_entity_id.

        Profiles with archetype_id use the archetype-native path.
        Profiles without archetype_id use the explicit legacy guard path.

        `seed` drives real, per-entity personality generation (both paths) --
        TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY. Given the same CompileContext,
        base_entity_id, and seed, spawn_from_context still produces bit-identical EntityState
        objects (docs/world/assembly_contract.md's own determinism guarantee, now parameterized
        by seed rather than seed-free).
        """
        result: Dict[int, EntityState] = {}
        entity_id = base_entity_id

        for _key, profile in ctx.entities.items():
            # TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE: a profile
            # represents one population GROUP, not one entity -- materialize profile.count
            # individuals (porting WorldCompiler.compile()'s classic pipeline behavior), each
            # tagged with the profile's own registration key as population_id, matching that
            # pipeline's own `properties["population_id"] = pop_key` convention exactly.
            positions = profile.spawn_positions or (profile.spawn_position,) * max(profile.count, 0)
            for i in range(profile.count):
                position = (
                    positions[i]
                    if i < len(positions) and positions[i] is not None
                    else default_position
                )
                spawn = EntitySpawnContext(
                    position=position,
                    spawn_region=None,
                    initial_alive=True,
                    initial_active=True,
                    population_id=_key,
                )

                state = self._spawn_one(entity_id, profile, spawn, catalog_repo, seed)
                if state is not None:
                    result[entity_id] = state
                entity_id += 1

        return result

    def _spawn_one(
        self,
        entity_id: int,
        profile: ResolvedEntityProfile,
        spawn: EntitySpawnContext,
        catalog_repo: object,
        seed: int,
    ) -> Optional[EntityState]:
        if profile.archetype_id:
            return self._spawn_archetype_native(entity_id, profile, spawn, catalog_repo, seed)
        else:
            return self._spawn_legacy_guard(entity_id, profile, spawn, seed)

    def _spawn_archetype_native(
        self,
        entity_id: int,
        profile: ResolvedEntityProfile,
        spawn: EntitySpawnContext,
        catalog_repo: object,
        seed: int,
    ) -> Optional[EntityState]:
        """Archetype-native path: catalog → resolved archetype → contract → EntityState."""
        try:
            from src.content.resolver import EntityArchetypeResolver
            resolver = EntityArchetypeResolver(catalog_repo)  # type: ignore[arg-type]
            resolved_arch = resolver.resolve(profile.archetype_id)
            contract = resolved_archetype_to_contract(resolved_arch)
            return self._factory.build_entity(entity_id, contract, spawn, seed)
        except Exception:
            # Archetype resolution failed — fall through to legacy guard
            return self._spawn_legacy_guard(entity_id, profile, spawn, seed)

    def _spawn_legacy_guard(
        self,
        entity_id: int,
        profile: ResolvedEntityProfile,
        spawn: EntitySpawnContext,
        seed: int,
    ) -> EntityState:
        # LEGACY GUARD: no archetype_id available or archetype resolution failed.
        # Uses V2EntityBuilder directly from profile stats. This path is explicit
        # and intentional — not a silent fallback.
        from src.core.builder import V2EntityBuilder
        from src.content_semantics.personality import build_personality_for_entity, get_action_style_for_bravery
        personality = build_personality_for_entity(entity_id, profile.faction_id, seed)
        return (
            V2EntityBuilder(entity_id)
            .kind(profile.species_id or "human")
            .location(*spawn.position)
            .identity(
                role=profile.legacy_role,
                faction=profile.legacy_faction,
                traits=set(profile.traits),
                properties={
                    "archetype_id": profile.archetype_id,
                    "species_id": profile.species_id,
                    "faction_id": profile.faction_id,
                    "role_id": profile.role_id,
                    "population_id": spawn.population_id,
                },
                personality=personality,
            )
            .combat(
                hp=profile.hp,
                max_hp=profile.max_hp,
                atk=profile.atk,
                def_stat=profile.def_stat,
                attack_range=profile.attack_range,
                readiness=profile.readiness,
                alive=True,
                action_style=get_action_style_for_bravery(personality.bravery),
            )
            .build()
        )

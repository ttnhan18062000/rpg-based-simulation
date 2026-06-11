from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.core.state import (
    EntityState,
    IdentityComponent,
    CombatComponent,
    LifecycleComponent,
    NavigationComponent,
)
from src.core.models.inventory import InventoryComponent, ItemStack
from src.core.builder import V2EntityBuilder
from src.entities.runtime_contract import ResolvedEntityRuntimeContract


@dataclass(frozen=True)
class EntitySpawnContext:
    """Positional and lifecycle context for spawning a runtime entity."""

    position: tuple[float, float] = (0.0, 0.0)
    spawn_region: Optional[str] = None
    initial_alive: bool = True
    initial_active: bool = True
    current_tick: Optional[int] = None
    name_override: Optional[str] = None


class ArchetypeEntityFactory:
    """
    Converts ResolvedEntityRuntimeContract + EntitySpawnContext into EntityState.

    This is the archetype-native construction path. Profile IDs that are not
    yet wired to active runtime behavior are preserved in identity.properties
    rather than silently dropped.
    """

    def build_entity(
        self,
        entity_id: int,
        contract: ResolvedEntityRuntimeContract,
        spawn: EntitySpawnContext,
    ) -> EntityState:
        # Metadata carried into properties for traceability
        properties: dict = {
            "archetype_id": contract.archetype_id,
            "race_id": contract.race_id,
            "faction_id": contract.faction_id,
            "role_id": contract.role_id,
        }
        if contract.profession_id is not None:
            properties["profession_id"] = contract.profession_id
        if contract.cognition_profile_id is not None:
            properties["cognition_profile_id"] = contract.cognition_profile_id
        if contract.drive_profile_id is not None:
            properties["drive_profile_id"] = contract.drive_profile_id
        if contract.need_profile_id is not None:
            properties["need_profile_id"] = contract.need_profile_id
        if contract.sense_profile_id is not None:
            properties["sense_profile_id"] = contract.sense_profile_id
        if contract.skill_profile_id is not None:
            properties["skill_profile_id"] = contract.skill_profile_id
        if spawn.spawn_region is not None:
            properties["spawn_region"] = spawn.spawn_region
        if spawn.name_override is not None:
            properties["name"] = spawn.name_override
        if spawn.current_tick is not None:
            properties["spawn_tick"] = spawn.current_tick

        # Legacy projection — use contract values if provided, else default (0)
        legacy_role_int = int(contract.legacy_role) if contract.legacy_role is not None else 0
        legacy_faction_int = int(contract.legacy_faction) if contract.legacy_faction is not None else 0

        # Build inventory items
        items = [
            ItemStack(item_id=item_id, quantity=qty)
            for item_id, qty in sorted(contract.inventory_items.items())
        ]

        builder = (
            V2EntityBuilder(entity_id)
            .kind(contract.kind)
            .location(*spawn.position)
            .identity(
                role=legacy_role_int,
                faction=legacy_faction_int,
                traits=set(contract.traits),
                properties=properties,
            )
            .combat(
                hp=contract.hp,
                max_hp=contract.max_hp,
                atk=contract.atk,
                def_stat=contract.def_stat,
                attack_range=contract.attack_range,
                readiness=contract.readiness,
                alive=spawn.initial_alive,
            )
        )

        entity = builder.build()

        # Replace inventory with populated items and gold
        if items or contract.starting_gold > 0:
            from dataclasses import replace
            inv = InventoryComponent(
                items=items,
                gold=int(contract.starting_gold),
            )
            entity = _replace_inventory(entity, inv)

        # Apply lifecycle active flag
        if not spawn.initial_active:
            entity = _replace_lifecycle(entity, active=False)

        return entity


def _replace_inventory(entity: EntityState, inv: InventoryComponent) -> EntityState:
    """Return a new EntityState with inventory replaced."""
    return EntityState(
        id=entity.id,
        kind=entity.kind,
        interaction=entity.interaction,
        identity=entity.identity,
        attributes=entity.attributes,
        inventory=inv,
        strategic=entity.strategic,
        social=entity.social,
        biological=entity.biological,
        lifecycle=entity.lifecycle,
        aptitude=entity.aptitude,
        combat=entity.combat,
        equipment=entity.equipment,
        navigation=entity.navigation,
        task=entity.task,
        stamina=entity.stamina,
        self_model=entity.self_model,
        cognition=entity.cognition,
    )


def _replace_lifecycle(entity: EntityState, *, active: bool) -> EntityState:
    """Return a new EntityState with lifecycle.active replaced."""
    from dataclasses import replace as dc_replace
    lc = dc_replace(entity.lifecycle, active=active)
    return EntityState(
        id=entity.id,
        kind=entity.kind,
        interaction=entity.interaction,
        identity=entity.identity,
        attributes=entity.attributes,
        inventory=entity.inventory,
        strategic=entity.strategic,
        social=entity.social,
        biological=entity.biological,
        lifecycle=lc,
        aptitude=entity.aptitude,
        combat=entity.combat,
        equipment=entity.equipment,
        navigation=entity.navigation,
        task=entity.task,
        stamina=entity.stamina,
        self_model=entity.self_model,
        cognition=entity.cognition,
    )

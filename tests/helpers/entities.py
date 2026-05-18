from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.movement_modes import MovementMode
from src.core.state import (
    AuthoritativeState,
    BuildingState,
    EntityState,
    IdentityComponent,
    InventoryComponent,
    ItemStack,
    PersonalityComponent,
    LifeStage,
)
from src.core.strategic import (
    ProjectState,
    ContractState,
    DirectiveState,
    BlockerState,
    LeadState,
    ConcernState,
    HypothesisState,
    SourceTrustEntry,
    TurningPointState,
)


def stack(item_id: str, quantity: int = 1) -> ItemStack:
    return ItemStack(item_id=item_id, quantity=quantity)


def stacks(*item_ids: str) -> list[ItemStack]:
    return [stack(item_id) for item_id in item_ids]


def make_entity(
    entity_id: int = 1,
    *,
    kind: str = "hero",
    pos: tuple[float, float] = (0.0, 0.0),
    role: EntityRole | int | None = None,
    faction: Faction | int | None = None,
    group_id: int | None = None,
    gold: int | None = None,
    items: list[ItemStack] | None = None,
    max_slots: int | None = None,
    max_weight: float | None = None,
    hp: int | None = None,
    max_hp: int | None = None,
    atk: int | None = None,
    def_stat: int | None = None,
    speed: int | None = None,
    attack_range: int | None = None,
    readiness: float | None = None,
    alive: bool | None = None,
    action_style: int | None = None,
    tactical_role: str | None = None,
    strength: int | None = None,
    agility: int | None = None,
    vitality: int | None = None,
    endurance: int | None = None,
    intelligence: int | None = None,
    spirit: int | None = None,
    wisdom: int | None = None,
    perception: int | None = None,
    charisma: int | None = None,
    target: tuple[float, float] | None = None,
    home_position: tuple[float, float] | None = None,
    movement_mode: MovementMode | None = None,
    leash_radius: float | None = None,
    chase_ticks: int | None = None,
    max_chase_ticks: int | None = None,
    returning_home: bool | None = None,
    active: bool | None = None,
    sleep_debt: float | None = None,
    hunger: float | None = None,
    rest_pressure: float | None = None,
    personality: PersonalityComponent | None = None,
    life_stage: LifeStage | None = None,
    known_recipes: set[str] | None = None,
    craft_target: str | None = None,
    class_id: str | None = None,
    learned_skills: set[str] | None = None,
    traits: set[str] | None = None,
    evolution_level: int | None = None,
    evolution_points: int | None = None,
    unspent_ap: int | None = None,
    projects: dict[str, ProjectState] | None = None,
    contracts: dict[str, ContractState] | None = None,
    directives: dict[str, DirectiveState] | None = None,
    blockers: dict[str, BlockerState] | None = None,
    leads: dict[str, LeadState] | None = None,
    concerns: dict[str, ConcernState] | None = None,
    hypotheses: dict[str, HypothesisState] | None = None,
    source_trust: dict[int, SourceTrustEntry] | None = None,
    turning_points: list[TurningPointState] | None = None,
    current_project_id: str | None = None,
    current_objective_id: str | None = None,
    boredom: dict[str, float] | None = None,
    trust_history: dict[int, float] | None = None,
    familiarity_history: dict[int, float] | None = None,
    debt_history: dict[int, float] | None = None,
    fear_history: dict[int, float] | None = None,
    grudge_history: dict[int, float] | None = None,
    salience_history: dict[int, float] | None = None,
    betrayal_count: int | None = None,
    public_reputation: float | None = None,
    heroism_score: float | None = None,
    notoriety_score: float | None = None,
    rejection_count: dict[int, int] | None = None,
    properties: dict[str, Any] | None = None,
) -> EntityState:
    builder = V2EntityBuilder(entity_id).kind(kind).location(*pos)

    if any(
        value is not None
        for value in [
            role,
            faction,
            group_id,
            personality,
            life_stage,
            known_recipes,
            craft_target,
            class_id,
            learned_skills,
            traits,
            evolution_level,
            evolution_points,
            unspent_ap,
            properties,
        ]
    ):
        builder.identity(
            role=role,
            faction=faction,
            group_id=group_id,
            personality=personality,
            life_stage=life_stage,
            known_recipes=known_recipes,
            craft_target=craft_target,
            class_id=class_id,
            learned_skills=learned_skills,
            traits=traits,
            evolution_level=evolution_level,
            evolution_points=evolution_points,
            unspent_ap=unspent_ap,
            properties=properties,
        )

    if any(value is not None for value in [gold, items, max_slots, max_weight]):
        builder.inventory(
            gold=gold,
            items=items,
            max_slots=max_slots,
            max_weight=max_weight,
        )

    if any(
        value is not None
        for value in [
            hp,
            max_hp,
            atk,
            def_stat,
            speed,
            attack_range,
            readiness,
            alive,
            action_style,
            tactical_role,
        ]
    ):
        builder.combat(
            hp=hp,
            max_hp=max_hp,
            atk=atk,
            def_stat=def_stat,
            speed=speed,
            attack_range=attack_range,
            readiness=readiness,
            alive=alive,
            action_style=action_style,
            tactical_role=tactical_role,
        )

    if any(
        value is not None
        for value in [
            strength,
            agility,
            vitality,
            endurance,
            intelligence,
            spirit,
            wisdom,
            perception,
            charisma,
        ]
    ):
        builder.attributes(
            strength=strength,
            agility=agility,
            vitality=vitality,
            endurance=endurance,
            intelligence=intelligence,
            spirit=spirit,
            wisdom=wisdom,
            perception=perception,
            charisma=charisma,
        )

    if any(
        value is not None
        for value in [
            target,
            home_position,
            movement_mode,
            leash_radius,
            chase_ticks,
            max_chase_ticks,
            returning_home,
        ]
    ):
        builder.navigation(
            target=target,
            home_position=home_position,
            movement_mode=movement_mode,
            leash_radius=leash_radius,
            chase_ticks=chase_ticks,
            max_chase_ticks=max_chase_ticks,
            returning_home=returning_home,
        )

    if active is not None:
        builder.lifecycle(active=active)

    if any(value is not None for value in [sleep_debt, hunger, rest_pressure]):
        builder.biological(
            sleep_debt=sleep_debt,
            hunger=hunger,
            rest_pressure=rest_pressure,
        )

    if any(
        value is not None
        for value in [
            projects,
            contracts,
            directives,
            blockers,
            leads,
            concerns,
            hypotheses,
            source_trust,
            turning_points,
            current_project_id,
            current_objective_id,
            boredom,
        ]
    ):
        builder.strategic(
            projects=projects,
            contracts=contracts,
            directives=directives,
            blockers=blockers,
            leads=leads,
            concerns=concerns,
            hypotheses=hypotheses,
            source_trust=source_trust,
            turning_points=turning_points,
            current_project_id=current_project_id,
            current_objective_id=current_objective_id,
            boredom=boredom,
        )

    if any(
        value is not None
        for value in [
            trust_history,
            familiarity_history,
            debt_history,
            fear_history,
            grudge_history,
            salience_history,
            betrayal_count,
            public_reputation,
            heroism_score,
            notoriety_score,
            rejection_count,
        ]
    ):
        builder.social(
            trust_history=trust_history,
            familiarity_history=familiarity_history,
            debt_history=debt_history,
            fear_history=fear_history,
            grudge_history=grudge_history,
            salience_history=salience_history,
            betrayal_count=betrayal_count,
            public_reputation=public_reputation,
            heroism_score=heroism_score,
            notoriety_score=notoriety_score,
            rejection_count=rejection_count,
        )

    return builder.build()


def make_hero(
    entity_id: int = 1,
    *,
    pos: tuple[float, float] = (0.0, 0.0),
    **kwargs,
) -> EntityState:
    return make_entity(
        entity_id,
        kind=kwargs.pop("kind", "hero"),
        pos=pos,
        role=kwargs.pop("role", EntityRole.HERO),
        faction=kwargs.pop("faction", Faction.HERO_GUILD),
        **kwargs,
    )


def make_monster(
    entity_id: int = 2,
    *,
    pos: tuple[float, float] = (1.0, 0.0),
    **kwargs,
) -> EntityState:
    return make_entity(
        entity_id,
        kind=kwargs.pop("kind", "monster"),
        pos=pos,
        role=kwargs.pop("role", EntityRole.MONSTER),
        faction=kwargs.pop("faction", Faction.MONSTER_HORDE),
        **kwargs,
    )


def make_actor_pair(
    *,
    attacker_id: int = 1,
    defender_id: int = 2,
    attacker_pos: tuple[float, float] = (0.0, 0.0),
    defender_pos: tuple[float, float] = (1.0, 0.0),
    attacker_kwargs: dict[str, Any] | None = None,
    defender_kwargs: dict[str, Any] | None = None,
) -> tuple[EntityState, EntityState]:
    attacker = make_hero(
        attacker_id,
        pos=attacker_pos,
        hp=100,
        max_hp=100,
        atk=20,
        def_stat=5,
        attack_range=1,
        readiness=100.0,
        alive=True,
        **(attacker_kwargs or {}),
    )

    defender = make_monster(
        defender_id,
        pos=defender_pos,
        hp=100,
        max_hp=100,
        atk=10,
        def_stat=5,
        attack_range=1,
        readiness=100.0,
        alive=True,
        **(defender_kwargs or {}),
    )

    return attacker, defender


def make_state(
    *,
    entities: Iterable[EntityState] = (),
    tick: int = 1,
    seed: int = 42,
    buildings: Iterable[BuildingState] = (),
    town_tiles: set[tuple[float, float]] | None = None,
    building_tiles: dict[tuple[float, float], str] | None = None,
    **overrides,
) -> AuthoritativeState:
    state = AuthoritativeState(
        tick=tick,
        seed=seed,
        entities={entity.id: entity for entity in entities},
        buildings={building.id: building for building in buildings},
        town_tiles=town_tiles or set(),
        building_tiles=building_tiles or {},
    )

    if overrides:
        state = replace(state, **overrides)

    return state


def make_shop(
    building_id: int = 1,
    *,
    pos: tuple[float, float] = (0.0, 0.0),
    gold: int = 1000,
    items: list[ItemStack] | None = None,
) -> BuildingState:
    return BuildingState(
        id=building_id,
        kind="shop",
        position=pos,
        inventory=InventoryComponent(
            gold=gold,
            items=items or [],
        ),
    )


def make_blacksmith(
    building_id: int = 2,
    *,
    pos: tuple[float, float] = (0.0, 0.0),
    gold: int = 1000,
) -> BuildingState:
    return BuildingState(
        id=building_id,
        kind="blacksmith",
        position=pos,
        inventory=InventoryComponent(gold=gold),
    )


def make_town_state(
    entity: EntityState,
    *,
    building: BuildingState,
    tick: int = 1,
    seed: int = 42,
) -> AuthoritativeState:
    return make_state(
        entities=[entity],
        buildings=[building],
        tick=tick,
        seed=seed,
        town_tiles={building.position},
        building_tiles={building.position: building.kind},
    )


def with_component(entity: EntityState, **components) -> EntityState:
    return replace(entity, **components)


def with_identity(entity: EntityState, **changes) -> EntityState:
    return replace(entity, identity=replace(entity.identity, **changes))


def with_inventory(entity: EntityState, **changes) -> EntityState:
    return replace(entity, inventory=replace(entity.inventory, **changes))


def with_combat(entity: EntityState, **changes) -> EntityState:
    return replace(entity, combat=replace(entity.combat, **changes))


def with_navigation(entity: EntityState, **changes) -> EntityState:
    return replace(entity, navigation=replace(entity.navigation, **changes))


def with_strategic(entity: EntityState, **changes) -> EntityState:
    return replace(entity, strategic=replace(entity.strategic, **changes))


def with_social(entity: EntityState, **changes) -> EntityState:
    return replace(entity, social=replace(entity.social, **changes))


def with_biological(entity: EntityState, **changes) -> EntityState:
    return replace(entity, biological=replace(entity.biological, **changes))


def with_lifecycle(entity: EntityState, **changes) -> EntityState:
    return replace(entity, lifecycle=replace(entity.lifecycle, **changes))
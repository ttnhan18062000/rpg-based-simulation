# Compliance IDs: PERF-010, PERF-011
from __future__ import annotations

from src.core.dirty import DirtySet
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, IdentityUpdate, StateUpdate
from src.domains.information.providers import InformationProviderArchetype, InformationProviderState
from src.engine.apply import ApplyPath
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.semantic_entity_index import (
    HUNGER_NEED_THRESHOLD,
    REST_PRESSURE_NEED_THRESHOLD,
    SLEEP_DEBT_NEED_THRESHOLD,
    SemanticEntityIndexService,
    SemanticEntityQuery,
)
from tests.helpers.entities import make_entity, make_state, with_biological, with_identity, with_navigation


def _mixed_state() -> AuthoritativeState:
    hero1 = with_navigation(
        make_entity(1, role=EntityRole.HERO, faction=Faction.HERO_GUILD, class_id="WARRIOR"),
        region_id="north_woods",
    )
    hero2 = with_navigation(
        make_entity(2, role=EntityRole.HERO, faction=Faction.HERO_GUILD, class_id="MAGE"),
        region_id="north_woods",
    )
    monster = with_navigation(
        make_entity(3, role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, class_id="NOVICE"),
        region_id="south_swamp",
    )
    # No region_id set -- must be excluded from the region dimension entirely.
    wanderer = make_entity(4, role=EntityRole.HERO, faction=Faction.NEUTRAL, class_id="ROGUE")
    starving = with_biological(make_entity(5, role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL), hunger=99.0)
    exhausted = with_biological(make_entity(6, role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL), sleep_debt=99.0)
    forced_rest = with_biological(make_entity(7, role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL), rest_pressure=71.0)
    fine = with_biological(make_entity(8, role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL), hunger=10.0, sleep_debt=10.0, rest_pressure=10.0)

    provider = InformationProviderState(
        entity_id=9,
        archetype=InformationProviderArchetype.MERCHANT,
        knowledge_domains=("material_source", "recipe_definition"),
    )

    return make_state(
        entities=[hero1, hero2, monster, wanderer, starving, exhausted, forced_rest, fine],
        tick=10,
        information_providers={9: provider},
    )


def _naive_by_role_class(state: AuthoritativeState, role: int, class_id: str) -> set[int]:
    return {e.id for e in state.entities.values() if e.identity.role == role and e.identity.class_id == class_id}


def _naive_by_region(state: AuthoritativeState, region_id: str) -> set[int]:
    return {e.id for e in state.entities.values() if e.navigation.region_id == region_id}


def _naive_by_faction(state: AuthoritativeState, faction: int) -> set[int]:
    return {e.id for e in state.entities.values() if e.identity.faction == faction}


def test_by_role_class_matches_naive_scan():
    state = _mixed_state()
    for role, class_id in [(EntityRole.HERO, "WARRIOR"), (EntityRole.HERO, "MAGE"), (EntityRole.MONSTER, "NOVICE"), (EntityRole.HERO, "ROGUE"), (EntityRole.HERO, "NOVICE")]:
        expected = _naive_by_role_class(state, role, class_id)
        actual = set(SemanticEntityQuery.by_role_class(state, None, role, class_id))
        assert actual == expected

    # Zero-match combination
    assert set(SemanticEntityQuery.by_role_class(state, None, EntityRole.GUARD, "WARRIOR")) == set()


def test_by_region_matches_naive_scan():
    state = _mixed_state()
    for region_id in ["north_woods", "south_swamp", "nowhere"]:
        expected = _naive_by_region(state, region_id)
        actual = set(SemanticEntityQuery.by_region(state, None, region_id))
        assert actual == expected

    # Entity with no region_id must never appear under any region key.
    all_regioned = set()
    for region_id in ["north_woods", "south_swamp"]:
        all_regioned |= set(SemanticEntityQuery.by_region(state, None, region_id))
    assert 4 not in all_regioned


def test_by_faction_matches_naive_scan():
    state = _mixed_state()
    for faction in [Faction.HERO_GUILD, Faction.MONSTER_HORDE, Faction.NEUTRAL, Faction.TOWN_COUNCIL]:
        expected = _naive_by_faction(state, faction)
        actual = set(SemanticEntityQuery.by_faction(state, None, faction))
        assert actual == expected


def test_by_entity_needs_matches_naive_scan_against_biological_thresholds():
    state = _mixed_state()

    naive_hunger = {e.id for e in state.entities.values() if e.biological.hunger >= HUNGER_NEED_THRESHOLD}
    naive_sleep_debt = {e.id for e in state.entities.values() if e.biological.sleep_debt >= SLEEP_DEBT_NEED_THRESHOLD}
    naive_rest_pressure = {e.id for e in state.entities.values() if e.biological.rest_pressure > REST_PRESSURE_NEED_THRESHOLD}

    assert set(SemanticEntityQuery.by_need(state, None, "hunger")) == naive_hunger == {5}
    assert set(SemanticEntityQuery.by_need(state, None, "sleep_debt")) == naive_sleep_debt == {6}
    assert set(SemanticEntityQuery.by_need(state, None, "rest_pressure")) == naive_rest_pressure == {7}
    assert set(SemanticEntityQuery.by_need(state, None, "unknown_need")) == set()

    # Regression guard: must not reference the out-of-scope from_entity_need/need_kind concept.
    import inspect
    from src.engine import semantic_entity_index as sei_module
    source = inspect.getsource(sei_module)
    assert "from_entity_need" not in source
    assert "need_kind" not in source


def test_by_knowledge_domain_matches_naive_scan():
    state = _mixed_state()

    naive: dict[str, set[int]] = {}
    for provider_id, provider in state.information_providers.items():
        for domain in provider.knowledge_domains:
            naive.setdefault(domain, set()).add(provider_id)

    for domain, expected in naive.items():
        assert set(SemanticEntityQuery.by_knowledge_domain(state, None, domain)) == expected

    assert set(SemanticEntityQuery.by_knowledge_domain(state, None, "unknown_domain")) == set()


def test_index_reflects_dirty_set_change_without_full_rebuild():
    state = _mixed_state()
    idx1 = SemanticEntityIndexService.get_indexes(state)
    assert set(SemanticEntityIndexService.get_indexes(state).by_faction.get(Faction.HERO_GUILD, ())) == {1, 2}

    # Entity 3 switches faction from MONSTER_HORDE to HERO_GUILD; only identity is dirty.
    entities = dict(state.entities)
    entities[3] = with_identity(entities[3], faction=Faction.HERO_GUILD)
    next_state = AuthoritativeState(
        tick=11, seed=state.seed, entities=entities,
        information_providers=state.information_providers,
        semantic_entity_indexes=idx1,
    )
    dirty = DirtySet(identity_entities={3})

    region_calls = []
    needs_calls = []
    knowledge_calls = []
    orig_region = SemanticEntityIndexService._build_region_index
    orig_needs = SemanticEntityIndexService._build_needs_index
    orig_knowledge = SemanticEntityIndexService._build_knowledge_domain_index
    SemanticEntityIndexService._build_region_index = staticmethod(lambda s: (region_calls.append(1), orig_region(s))[1])
    SemanticEntityIndexService._build_needs_index = staticmethod(lambda s: (needs_calls.append(1), orig_needs(s))[1])
    SemanticEntityIndexService._build_knowledge_domain_index = staticmethod(lambda s: (knowledge_calls.append(1), orig_knowledge(s))[1])
    try:
        idx2 = SemanticEntityIndexService.get_indexes(next_state, dirty)
    finally:
        SemanticEntityIndexService._build_region_index = orig_region
        SemanticEntityIndexService._build_needs_index = orig_needs
        SemanticEntityIndexService._build_knowledge_domain_index = orig_knowledge

    assert 3 in idx2.by_faction.get(Faction.HERO_GUILD, ())
    assert 3 not in idx2.by_faction.get(Faction.MONSTER_HORDE, ())
    # Region/needs were not dirty -- reused, not rebuilt.
    assert idx2.by_region is idx1.by_region
    assert idx2.by_need is idx1.by_need
    assert region_calls == []
    assert needs_calls == []
    # Knowledge always conservatively rebuilds (no DirtySet tag backs it).
    assert knowledge_calls == [1]


def test_incremental_index_bit_identical_to_full_rebuild():
    state = _mixed_state()
    SemanticEntityIndexService.get_indexes(state)

    entities = dict(state.entities)
    entities[3] = with_navigation(with_identity(entities[3], faction=Faction.HERO_GUILD), region_id="north_woods")
    entities[5] = with_biological(entities[5], hunger=0.0)
    final_state = AuthoritativeState(
        tick=11, seed=state.seed, entities=entities,
        information_providers=state.information_providers,
        semantic_entity_indexes=SemanticEntityIndexService.get_indexes(state),
    )
    dirty = DirtySet(identity_entities={3}, region_ids={"north_woods"}, biological_entities={5})
    incremental = SemanticEntityIndexService.get_indexes(final_state, dirty)

    object.__setattr__(final_state, "semantic_entity_indexes", None)
    rebuilt = SemanticEntityIndexService.get_indexes(final_state, None)

    assert incremental.by_role_class == rebuilt.by_role_class
    assert incremental.by_region == rebuilt.by_region
    assert incremental.by_faction == rebuilt.by_faction
    assert incremental.by_need == rebuilt.by_need
    assert incremental.by_knowledge_domain == rebuilt.by_knowledge_domain


def test_delete_and_rebuild_index_matches_incremental_across_all_dimensions():
    state = _mixed_state()
    incremental = SemanticEntityIndexService.get_indexes(state, None)

    object.__setattr__(state, "semantic_entity_indexes", None)
    rebuilt = SemanticEntityIndexService.get_indexes(state, None)

    assert (
        incremental.by_role_class,
        incremental.by_region,
        incremental.by_faction,
        incremental.by_need,
        incremental.by_knowledge_domain,
    ) == (
        rebuilt.by_role_class,
        rebuilt.by_region,
        rebuilt.by_faction,
        rebuilt.by_need,
        rebuilt.by_knowledge_domain,
    )


def test_semantic_index_excluded_from_canonical_state_hash():
    state = _mixed_state()
    hash_before = CanonicalStateHasher.get_hash(state)

    indexes = SemanticEntityIndexService.get_indexes(state)
    object.__setattr__(state, "semantic_entity_indexes", indexes)
    hash_after = CanonicalStateHasher.get_hash(state)

    assert hash_before == hash_after


def test_identity_update_sets_identity_entities_tag():
    entity = make_entity(1, role=EntityRole.HERO, faction=Faction.HERO_GUILD)
    state = make_state(entities=[entity], tick=5)

    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, identity=IdentityUpdate(role_set=EntityRole.WORKER))})
    dirty = DirtySet.from_update(state, update)
    assert 1 in dirty.identity_entities

    other_entity = make_entity(2, role=EntityRole.HERO, faction=Faction.HERO_GUILD)
    state2 = make_state(entities=[other_entity], tick=5)
    update2 = StateUpdate(entity_updates={2: EntityUpdate(entity_id=2, attributes=None)})
    dirty2 = DirtySet.from_update(state2, update2)
    assert 2 not in dirty2.identity_entities


def test_identity_only_update_appears_in_all_dirty_entities():
    entity = make_entity(1, role=EntityRole.HERO, faction=Faction.HERO_GUILD)
    state = make_state(entities=[entity], tick=5)

    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, identity=IdentityUpdate(faction_set=Faction.NEUTRAL))})
    dirty = DirtySet.from_update(state, update)

    assert 1 in dirty.identity_entities
    assert 1 in dirty.all_dirty_entities


def test_identity_only_update_does_not_raise_dirty_set_leak_error():
    entity = make_entity(1, role=EntityRole.HERO, faction=Faction.HERO_GUILD)
    prior_state = make_state(entities=[entity], tick=5)

    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, identity=IdentityUpdate(faction_set=Faction.NEUTRAL))})
    update = update.replace(dirty_set=DirtySet.from_update(prior_state, update))

    new_state = ApplyPath.apply_generation(prior_state, update, next_tick=6, audit_dirty_set=True)
    assert new_state.entities[1].identity.faction == Faction.NEUTRAL


def test_semantic_entity_indexes_carried_forward_across_ticks():
    entity = make_entity(1, role=EntityRole.HERO, faction=Faction.HERO_GUILD, class_id="WARRIOR")
    prior_state = make_state(entities=[entity], tick=5)
    idx1 = SemanticEntityIndexService.get_indexes(prior_state, DirtySet())
    assert prior_state.semantic_entity_indexes is idx1

    update = StateUpdate()
    update = update.replace(dirty_set=DirtySet.from_update(prior_state, update))
    new_state = ApplyPath.apply_generation(prior_state, update, next_tick=6)

    # Cross-tick carry-forward: apply_generation's new state must carry the prior
    # tick's resolved indexes object forward by identity, mirroring world_indexes.
    assert new_state.semantic_entity_indexes is idx1

    idx2 = SemanticEntityIndexService.get_indexes(new_state, DirtySet())
    assert idx2.by_role_class is idx1.by_role_class
    assert idx2.by_region is idx1.by_region
    assert idx2.by_faction is idx1.by_faction
    assert idx2.by_need is idx1.by_need


def test_get_indexes_only_rebuilds_dirty_domains_across_ticks():
    entity1 = make_entity(1, role=EntityRole.HERO, faction=Faction.HERO_GUILD, class_id="WARRIOR")
    state0 = make_state(entities=[entity1], tick=5)
    SemanticEntityIndexService.get_indexes(state0, DirtySet())

    update1 = StateUpdate()
    update1 = update1.replace(dirty_set=DirtySet.from_update(state0, update1))
    state1 = ApplyPath.apply_generation(state0, update1, next_tick=6)

    update2 = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, identity=IdentityUpdate(faction_set=Faction.NEUTRAL))})
    update2 = update2.replace(dirty_set=DirtySet.from_update(state1, update2))
    state2 = ApplyPath.apply_generation(state1, update2, next_tick=7)

    role_class_calls, faction_calls, region_calls, needs_calls, knowledge_calls = [], [], [], [], []
    orig_role = SemanticEntityIndexService._build_role_class_index
    orig_faction = SemanticEntityIndexService._build_faction_index
    orig_region = SemanticEntityIndexService._build_region_index
    orig_needs = SemanticEntityIndexService._build_needs_index
    orig_knowledge = SemanticEntityIndexService._build_knowledge_domain_index
    SemanticEntityIndexService._build_role_class_index = staticmethod(lambda s: (role_class_calls.append(1), orig_role(s))[1])
    SemanticEntityIndexService._build_faction_index = staticmethod(lambda s: (faction_calls.append(1), orig_faction(s))[1])
    SemanticEntityIndexService._build_region_index = staticmethod(lambda s: (region_calls.append(1), orig_region(s))[1])
    SemanticEntityIndexService._build_needs_index = staticmethod(lambda s: (needs_calls.append(1), orig_needs(s))[1])
    SemanticEntityIndexService._build_knowledge_domain_index = staticmethod(lambda s: (knowledge_calls.append(1), orig_knowledge(s))[1])
    try:
        result = SemanticEntityIndexService.get_indexes(state2, update2.dirty_set)
    finally:
        SemanticEntityIndexService._build_role_class_index = orig_role
        SemanticEntityIndexService._build_faction_index = orig_faction
        SemanticEntityIndexService._build_region_index = orig_region
        SemanticEntityIndexService._build_needs_index = orig_needs
        SemanticEntityIndexService._build_knowledge_domain_index = orig_knowledge

    # Only "identity" was dirty this tick (role_class + faction both map to it) --
    # region/needs must be reused from the carried-forward object, not rebuilt.
    assert role_class_calls == [1]
    assert faction_calls == [1]
    assert region_calls == []
    assert needs_calls == []
    # Knowledge always conservatively rebuilds regardless of dirty state.
    assert knowledge_calls == [1]
    assert 1 in result.by_faction.get(Faction.NEUTRAL, ())


def test_single_dimension_query_does_not_rebuild_unrequested_invalidated_dimension():
    entity = with_navigation(
        make_entity(1, role=EntityRole.HERO, faction=Faction.HERO_GUILD, class_id="WARRIOR"),
        region_id="north_woods",
    )
    state0 = make_state(entities=[entity], tick=5)
    idx0 = SemanticEntityIndexService.get_indexes(state0, DirtySet())

    entities = dict(state0.entities)
    next_state = AuthoritativeState(
        tick=6, seed=state0.seed, entities=entities,
        information_providers=state0.information_providers,
        semantic_entity_indexes=idx0,
    )
    dirty = DirtySet(identity_entities={1}, biological_entities={1})

    role_class_calls, faction_calls, needs_calls, knowledge_calls, region_calls = [], [], [], [], []
    orig_role = SemanticEntityIndexService._build_role_class_index
    orig_faction = SemanticEntityIndexService._build_faction_index
    orig_needs = SemanticEntityIndexService._build_needs_index
    orig_knowledge = SemanticEntityIndexService._build_knowledge_domain_index
    orig_region = SemanticEntityIndexService._build_region_index
    SemanticEntityIndexService._build_role_class_index = staticmethod(lambda s: (role_class_calls.append(1), orig_role(s))[1])
    SemanticEntityIndexService._build_faction_index = staticmethod(lambda s: (faction_calls.append(1), orig_faction(s))[1])
    SemanticEntityIndexService._build_needs_index = staticmethod(lambda s: (needs_calls.append(1), orig_needs(s))[1])
    SemanticEntityIndexService._build_knowledge_domain_index = staticmethod(lambda s: (knowledge_calls.append(1), orig_knowledge(s))[1])
    SemanticEntityIndexService._build_region_index = staticmethod(lambda s: (region_calls.append(1), orig_region(s))[1])
    try:
        result = SemanticEntityQuery.by_region(next_state, dirty, "north_woods")
    finally:
        SemanticEntityIndexService._build_role_class_index = orig_role
        SemanticEntityIndexService._build_faction_index = orig_faction
        SemanticEntityIndexService._build_needs_index = orig_needs
        SemanticEntityIndexService._build_knowledge_domain_index = orig_knowledge
        SemanticEntityIndexService._build_region_index = orig_region

    # identity/needs are invalidated but not requested by by_region -- must not rebuild.
    assert role_class_calls == []
    assert faction_calls == []
    assert needs_calls == []
    assert knowledge_calls == []
    # region is requested but not invalidated -- reused, not rebuilt.
    assert region_calls == []
    assert 1 in result


def test_knowledge_domain_still_always_rebuilds_when_requested():
    state0 = _mixed_state()
    idx0 = SemanticEntityIndexService.get_indexes(state0, DirtySet())

    entities = dict(state0.entities)
    next_state = AuthoritativeState(
        tick=11, seed=state0.seed, entities=entities,
        information_providers=state0.information_providers,
        semantic_entity_indexes=idx0,
    )
    dirty = DirtySet()  # nothing invalidated this tick

    knowledge_calls = []
    orig = SemanticEntityIndexService._build_knowledge_domain_index
    SemanticEntityIndexService._build_knowledge_domain_index = staticmethod(lambda s: (knowledge_calls.append(1), orig(s))[1])
    try:
        idx2 = SemanticEntityIndexService.get_indexes(next_state, dirty, dimensions={"knowledge_domain"})
    finally:
        SemanticEntityIndexService._build_knowledge_domain_index = orig

    # Requested + unconditional "knowledge" invalidation -> always a fresh rebuild,
    # even though nothing else this tick was dirty.
    assert knowledge_calls == [1]
    assert idx2.by_knowledge_domain is not idx0.by_knowledge_domain
    assert idx2.by_knowledge_domain == idx0.by_knowledge_domain


def test_apply_generation_semantic_index_carry_forward_bit_identical_to_full_rebuild():
    entity1 = with_navigation(
        make_entity(1, role=EntityRole.HERO, faction=Faction.HERO_GUILD, class_id="WARRIOR"),
        region_id="north_woods",
    )
    entity2 = with_biological(
        make_entity(2, role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL),
        hunger=10.0,
    )
    prior_state = make_state(entities=[entity1, entity2], tick=5)
    SemanticEntityIndexService.get_indexes(prior_state, DirtySet())

    update = StateUpdate(entity_updates={2: EntityUpdate(entity_id=2, identity=IdentityUpdate(faction_set=Faction.NEUTRAL))})
    update = update.replace(dirty_set=DirtySet.from_update(prior_state, update))
    new_state = ApplyPath.apply_generation(prior_state, update, next_tick=6)

    carried = SemanticEntityIndexService.get_indexes(new_state, update.dirty_set)

    object.__setattr__(new_state, "semantic_entity_indexes", None)
    rebuilt = SemanticEntityIndexService.get_indexes(new_state, None)

    assert carried.by_role_class == rebuilt.by_role_class
    assert carried.by_region == rebuilt.by_region
    assert carried.by_faction == rebuilt.by_faction
    assert carried.by_need == rebuilt.by_need
    assert carried.by_knowledge_domain == rebuilt.by_knowledge_domain


def test_semantic_entity_indexes_carry_forward_survives_dirty_set_audit():
    entity = make_entity(1, role=EntityRole.HERO, faction=Faction.HERO_GUILD)
    prior_state = make_state(entities=[entity], tick=5)
    idx1 = SemanticEntityIndexService.get_indexes(prior_state, DirtySet())

    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, identity=IdentityUpdate(faction_set=Faction.NEUTRAL))})
    update = update.replace(dirty_set=DirtySet.from_update(prior_state, update))

    new_state = ApplyPath.apply_generation(prior_state, update, next_tick=6, audit_dirty_set=True)

    assert new_state.semantic_entity_indexes is idx1
    assert new_state.entities[1].identity.faction == Faction.NEUTRAL


def test_partial_dimension_request_does_not_reuse_stale_same_tick_object():
    entity = make_entity(1, role=EntityRole.HERO, faction=Faction.HERO_GUILD, class_id="WARRIOR")
    state0 = make_state(entities=[entity], tick=5)
    idx0 = SemanticEntityIndexService.get_indexes(state0, DirtySet())

    entities = dict(state0.entities)
    next_state = AuthoritativeState(
        tick=6, seed=state0.seed, entities=entities,
        information_providers=state0.information_providers,
        semantic_entity_indexes=idx0,
    )
    # identity invalidated this tick; knowledge always-invalidates regardless.
    dirty = DirtySet(identity_entities={1})

    role_class_calls, faction_calls, knowledge_calls = [], [], []
    orig_role = SemanticEntityIndexService._build_role_class_index
    orig_faction = SemanticEntityIndexService._build_faction_index
    orig_knowledge = SemanticEntityIndexService._build_knowledge_domain_index
    SemanticEntityIndexService._build_role_class_index = staticmethod(lambda s: (role_class_calls.append(1), orig_role(s))[1])
    SemanticEntityIndexService._build_faction_index = staticmethod(lambda s: (faction_calls.append(1), orig_faction(s))[1])
    SemanticEntityIndexService._build_knowledge_domain_index = staticmethod(lambda s: (knowledge_calls.append(1), orig_knowledge(s))[1])
    try:
        SemanticEntityIndexService.get_indexes(next_state, dirty, dimensions={"region"})
        # role_class/faction/knowledge_domain were not requested this call -- must not rebuild.
        assert role_class_calls == []
        assert faction_calls == []
        assert knowledge_calls == []

        SemanticEntityIndexService.get_indexes(next_state, dirty, dimensions={"role_class"})
    finally:
        SemanticEntityIndexService._build_role_class_index = orig_role
        SemanticEntityIndexService._build_faction_index = orig_faction
        SemanticEntityIndexService._build_knowledge_domain_index = orig_knowledge

    # role_class is now requested for the first time this tick, and identity is
    # invalidated -- it must be rebuilt, not silently reused from the first call.
    assert role_class_calls == [1]


def test_repeated_same_tick_request_for_same_invalidated_dimension_builds_once():
    state = _mixed_state()
    dirty = DirtySet(identity_entities={1})

    role_class_calls = []
    orig = SemanticEntityIndexService._build_role_class_index
    SemanticEntityIndexService._build_role_class_index = staticmethod(lambda s: (role_class_calls.append(1), orig(s))[1])
    try:
        idx1 = SemanticEntityIndexService.get_indexes(state, dirty, dimensions={"role_class"})
        idx2 = SemanticEntityIndexService.get_indexes(state, dirty, dimensions={"role_class"})
    finally:
        SemanticEntityIndexService._build_role_class_index = orig

    # Two same-tick calls requesting the same invalidated dimension must trigger
    # at most one rebuild, not one per call.
    assert role_class_calls == [1]
    assert idx2.by_role_class is idx1.by_role_class


def test_full_request_after_partial_same_tick_rebuilds_invalidated_unresolved_dimension():
    entity = with_navigation(
        make_entity(1, role=EntityRole.HERO, faction=Faction.HERO_GUILD, class_id="WARRIOR"),
        region_id="north_woods",
    )
    state0 = make_state(entities=[entity], tick=5)
    idx0 = SemanticEntityIndexService.get_indexes(state0, DirtySet())

    # Entity 1's region changes between the carried-forward state and the state
    # under test, so a stale vs. fresh by_region are distinguishably different.
    entities = {1: with_navigation(entity, region_id="south_swamp")}
    next_state = AuthoritativeState(
        tick=6, seed=state0.seed, entities=entities,
        information_providers=state0.information_providers,
        semantic_entity_indexes=idx0,
    )
    # Only "region" is invalidated this tick.
    dirty = DirtySet(region_ids={"south_swamp"})

    idx_call1 = SemanticEntityIndexService.get_indexes(next_state, dirty, dimensions={"role_class"})
    assert idx_call1.resolved_dimensions == {"role_class"}
    # by_region was never requested by call 1 -- reused verbatim from the carried object.
    assert idx_call1.by_region is idx0.by_region

    region_calls = []
    orig_region = SemanticEntityIndexService._build_region_index
    SemanticEntityIndexService._build_region_index = staticmethod(lambda s: (region_calls.append(1), orig_region(s))[1])
    try:
        idx_call2 = SemanticEntityIndexService.get_indexes(next_state, dirty)
    finally:
        SemanticEntityIndexService._build_region_index = orig_region

    # The full request must still re-check the invalidated-but-unresolved "region"
    # dimension that call 1 left untouched -- not silently return the stale value.
    assert region_calls == [1]
    assert idx_call2.by_region != idx0.by_region
    assert set(idx_call2.by_region.get("south_swamp", ())) == {1}

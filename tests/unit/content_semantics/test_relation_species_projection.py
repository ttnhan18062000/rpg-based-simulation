"""Tests for RelationProjectionService.project_relation()'s species-hostility escalation step.

TCK-20260831-RACE-RELATIONS-MATRIX, Step 6. Covers:
- AC #2: two species pairs with contrasting authored hostility produce different labels.
- Upgrade-only: a species entry never downgrades an existing "enemy"/"threat" label.
- Friendly Fire guard: same-faction pairs never get species-driven escalation.
- Ally/protected-label guard (the ticket's single most important correctness property):
  a species entry can never invert a perspective-declared "ally" (or any other off-ladder
  label) into hostile. This is the concrete regression test for the architecture-review
  finding that a `.get(label, 0)`-style default would have silently broken.
"""
import pytest

from src.content.repository import CatalogRepository
from src.content.schema import SpeciesRelationRecord
from src.content_semantics.relation import RelationContext, RelationProjectionService


@pytest.fixture(scope="module")
def repo() -> CatalogRepository:
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture
def fixture_repo(repo: CatalogRepository) -> CatalogRepository:
    """A repo with two synthetic species_relations fixtures injected on top of the real
    catalog, isolated per-test (dict copy) so tests don't interfere with each other or
    with the module-scoped `repo` fixture."""
    isolated = CatalogRepository.__new__(CatalogRepository)
    isolated.__dict__ = dict(repo.__dict__)
    isolated.species_relations = dict(repo.species_relations)
    isolated.species_relations["fixture_high"] = SpeciesRelationRecord(
        id="fixture_high",
        source_species="fixture_predator",
        target_species="fixture_prey",
        relationship_model="test_fixture",
        axes={"hostility": "high"},
    )
    isolated.species_relations["fixture_medium_contextual"] = SpeciesRelationRecord(
        id="fixture_medium_contextual",
        source_species="fixture_predator",
        target_species="fixture_bystander",
        relationship_model="test_fixture",
        axes={"hostility": "medium_contextual"},
    )
    return isolated


def test_species_relations_hostility_changes_projected_label(fixture_repo):
    """AC #2: two species pairs with different authored hostility produce different labels,
    for a faction pair with no perspective/relationship label of its own."""
    service = RelationProjectionService(fixture_repo)

    high_result = service.project_relation(
        "no_such_perspective", "unaffiliated_source", "unaffiliated_target",
        RelationContext(source_species="fixture_predator", target_species="fixture_prey"),
    )
    medium_result = service.project_relation(
        "no_such_perspective", "unaffiliated_source", "unaffiliated_target",
        RelationContext(source_species="fixture_predator", target_species="fixture_bystander"),
    )

    assert high_result.label == "enemy"
    assert medium_result.label == "threat"
    assert high_result.label != medium_result.label


def test_species_relations_missing_species_context_is_noop(fixture_repo):
    """Graceful no-op: target_species (or source_species) unset means the escalation block never
    fires, and behavior falls through to the pre-existing legacy fallback unchanged."""
    service = RelationProjectionService(fixture_repo)
    result = service.project_relation(
        "no_such_perspective", "unaffiliated_source", "unaffiliated_target", RelationContext(),
    )
    assert result.label == "neutral"


def test_species_relations_same_faction_never_becomes_hostile(fixture_repo):
    """Friendly Fire law guard: source_faction_id == target_faction_id must never be
    escalated to hostile via species hostility alone, even with a matching authored entry."""
    service = RelationProjectionService(fixture_repo)
    result = service.project_relation(
        "no_such_perspective", "same_faction", "same_faction",
        RelationContext(source_species="fixture_predator", target_species="fixture_prey"),
    )
    assert result.label == "neutral"


def test_species_relations_upgrade_only_never_downgrades_enemy(fixture_repo):
    """A weaker species entry (or no species entry at all) must never downgrade an
    already-resolved 'enemy' label produced by the relationship-axis block — the
    escalation logic has no downgrade branch at all, only `label = "enemy"` /
    `label = "threat"` assignments guarded by `current_rank < ...`."""
    isolated = fixture_repo
    isolated.faction_relationships = dict(isolated.faction_relationships)
    from src.content.schema import FactionRelationshipDefinition
    isolated.faction_relationships["fixture_hostile_factions"] = FactionRelationshipDefinition(
        id="fixture_hostile_factions",
        source_faction="fixture_faction_a",
        target_faction="fixture_faction_b",
        relationship_model="test_fixture",
        axes={"hostility": "high"},
    )
    isolated.species_relations["fixture_weaker_species_entry"] = SpeciesRelationRecord(
        id="fixture_weaker_species_entry",
        source_species="fixture_species_x",
        target_species="fixture_species_y",
        relationship_model="test_fixture",
        axes={"hostility": "medium_contextual"},
    )
    service = RelationProjectionService(isolated)

    # A weaker (threat-tier) species entry exists between these species, but the faction pair
    # already resolved to "enemy" (rank 2) via the relationship-axis block -- must stay "enemy".
    result = service.project_relation(
        "no_such_perspective", "fixture_faction_a", "fixture_faction_b",
        RelationContext(source_species="fixture_species_x", target_species="fixture_species_y"),
    )
    assert result.label == "enemy"

    # No species entry at all between these two synthetic species -> species_rel is None, no-op.
    result_no_entry = service.project_relation(
        "no_such_perspective", "fixture_faction_a", "fixture_faction_b",
        RelationContext(source_species="unlisted_species_1", target_species="unlisted_species_2"),
    )
    assert result_no_entry.label == "enemy"


def test_species_relations_never_overrides_ally_label(repo):
    """The concrete regression test for the architecture-review finding: the real
    hero_guild_perspective declares forest_wardens (elf species) as an ally_groups member.
    A synthetic human->elf species_relations entry with hostility 'high' must NOT invert
    that ally label to enemy/threat."""
    isolated = CatalogRepository.__new__(CatalogRepository)
    isolated.__dict__ = dict(repo.__dict__)
    isolated.species_relations = dict(repo.species_relations)
    isolated.species_relations["human_to_elf_test"] = SpeciesRelationRecord(
        id="human_to_elf_test",
        source_species="human",
        target_species="elf",
        relationship_model="test_fixture",
        axes={"hostility": "high"},
    )
    service = RelationProjectionService(isolated)

    result = service.project_relation(
        "hero_guild_perspective", "hero_guild", "forest_wardens",
        RelationContext(source_species="human", target_species="elf"),
    )
    assert result.label == "ally"


def test_species_relations_never_overrides_ally_label_dwarf_variant(repo):
    """Second real ally pairing from the same perspective (dwarven_mine_clan, dwarf species),
    for the same guard as above."""
    isolated = CatalogRepository.__new__(CatalogRepository)
    isolated.__dict__ = dict(repo.__dict__)
    isolated.species_relations = dict(repo.species_relations)
    isolated.species_relations["human_to_dwarf_test"] = SpeciesRelationRecord(
        id="human_to_dwarf_test",
        source_species="human",
        target_species="dwarf",
        relationship_model="test_fixture",
        axes={"hostility": "high"},
    )
    service = RelationProjectionService(isolated)

    result = service.project_relation(
        "hero_guild_perspective", "hero_guild", "dwarven_mine_clan",
        RelationContext(source_species="human", target_species="dwarf"),
    )
    assert result.label == "ally"


def test_pre_existing_relation_projection_unaffected_by_no_species_entry(repo):
    """Regression guard: entities with no authored species_relations entry (or no species
    context at all) must produce identical output to pre-ticket behavior."""
    service = RelationProjectionService(repo)
    result = service.project_relation("hero_guild_perspective", "hero_guild", "goblin_warband")
    assert result.label == "enemy"

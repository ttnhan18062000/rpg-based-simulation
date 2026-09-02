"""Tests for RelationProjectionService.project_relation()'s race-hostility escalation step.

TCK-20260831-RACE-RELATIONS-MATRIX, Step 6. Covers:
- AC #2: two race pairs with contrasting authored hostility produce different labels.
- Upgrade-only: a race entry never downgrades an existing "enemy"/"threat" label.
- Friendly Fire guard: same-faction pairs never get race-driven escalation.
- Ally/protected-label guard (the ticket's single most important correctness property):
  a race entry can never invert a perspective-declared "ally" (or any other off-ladder
  label) into hostile. This is the concrete regression test for the architecture-review
  finding that a `.get(label, 0)`-style default would have silently broken.
"""
import pytest

from src.content.repository import CatalogRepository
from src.content.schema import RaceRelationRecord
from src.content_semantics.relation import RelationContext, RelationProjectionService


@pytest.fixture(scope="module")
def repo() -> CatalogRepository:
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture
def fixture_repo(repo: CatalogRepository) -> CatalogRepository:
    """A repo with two synthetic race_relations fixtures injected on top of the real
    catalog, isolated per-test (dict copy) so tests don't interfere with each other or
    with the module-scoped `repo` fixture."""
    isolated = CatalogRepository.__new__(CatalogRepository)
    isolated.__dict__ = dict(repo.__dict__)
    isolated.race_relations = dict(repo.race_relations)
    isolated.race_relations["fixture_high"] = RaceRelationRecord(
        id="fixture_high",
        source_race="fixture_predator",
        target_race="fixture_prey",
        relationship_model="test_fixture",
        axes={"hostility": "high"},
    )
    isolated.race_relations["fixture_medium_contextual"] = RaceRelationRecord(
        id="fixture_medium_contextual",
        source_race="fixture_predator",
        target_race="fixture_bystander",
        relationship_model="test_fixture",
        axes={"hostility": "medium_contextual"},
    )
    return isolated


def test_race_relations_hostility_changes_projected_label(fixture_repo):
    """AC #2: two race pairs with different authored hostility produce different labels,
    for a faction pair with no perspective/relationship label of its own."""
    service = RelationProjectionService(fixture_repo)

    high_result = service.project_relation(
        "no_such_perspective", "unaffiliated_source", "unaffiliated_target",
        RelationContext(source_race="fixture_predator", target_race="fixture_prey"),
    )
    medium_result = service.project_relation(
        "no_such_perspective", "unaffiliated_source", "unaffiliated_target",
        RelationContext(source_race="fixture_predator", target_race="fixture_bystander"),
    )

    assert high_result.label == "enemy"
    assert medium_result.label == "threat"
    assert high_result.label != medium_result.label


def test_race_relations_missing_race_context_is_noop(fixture_repo):
    """Graceful no-op: target_race (or source_race) unset means the escalation block never
    fires, and behavior falls through to the pre-existing legacy fallback unchanged."""
    service = RelationProjectionService(fixture_repo)
    result = service.project_relation(
        "no_such_perspective", "unaffiliated_source", "unaffiliated_target", RelationContext(),
    )
    assert result.label == "neutral"


def test_race_relations_same_faction_never_becomes_hostile(fixture_repo):
    """Friendly Fire law guard: source_faction_id == target_faction_id must never be
    escalated to hostile via race hostility alone, even with a matching authored entry."""
    service = RelationProjectionService(fixture_repo)
    result = service.project_relation(
        "no_such_perspective", "same_faction", "same_faction",
        RelationContext(source_race="fixture_predator", target_race="fixture_prey"),
    )
    assert result.label == "neutral"


def test_race_relations_upgrade_only_never_downgrades_enemy(fixture_repo):
    """A weaker race entry (or no race entry at all) must never downgrade an
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
    isolated.race_relations["fixture_weaker_race_entry"] = RaceRelationRecord(
        id="fixture_weaker_race_entry",
        source_race="fixture_race_x",
        target_race="fixture_race_y",
        relationship_model="test_fixture",
        axes={"hostility": "medium_contextual"},
    )
    service = RelationProjectionService(isolated)

    # A weaker (threat-tier) race entry exists between these races, but the faction pair
    # already resolved to "enemy" (rank 2) via the relationship-axis block -- must stay "enemy".
    result = service.project_relation(
        "no_such_perspective", "fixture_faction_a", "fixture_faction_b",
        RelationContext(source_race="fixture_race_x", target_race="fixture_race_y"),
    )
    assert result.label == "enemy"

    # No race entry at all between these two synthetic races -> race_rel is None, no-op.
    result_no_entry = service.project_relation(
        "no_such_perspective", "fixture_faction_a", "fixture_faction_b",
        RelationContext(source_race="unlisted_race_1", target_race="unlisted_race_2"),
    )
    assert result_no_entry.label == "enemy"


def test_race_relations_never_overrides_ally_label(repo):
    """The concrete regression test for the architecture-review finding: the real
    hero_guild_perspective declares forest_wardens (elf race) as an ally_groups member.
    A synthetic human->elf race_relations entry with hostility 'high' must NOT invert
    that ally label to enemy/threat."""
    isolated = CatalogRepository.__new__(CatalogRepository)
    isolated.__dict__ = dict(repo.__dict__)
    isolated.race_relations = dict(repo.race_relations)
    isolated.race_relations["human_to_elf_test"] = RaceRelationRecord(
        id="human_to_elf_test",
        source_race="human",
        target_race="elf",
        relationship_model="test_fixture",
        axes={"hostility": "high"},
    )
    service = RelationProjectionService(isolated)

    result = service.project_relation(
        "hero_guild_perspective", "hero_guild", "forest_wardens",
        RelationContext(source_race="human", target_race="elf"),
    )
    assert result.label == "ally"


def test_race_relations_never_overrides_ally_label_dwarf_variant(repo):
    """Second real ally pairing from the same perspective (dwarven_mine_clan, dwarf race),
    for the same guard as above."""
    isolated = CatalogRepository.__new__(CatalogRepository)
    isolated.__dict__ = dict(repo.__dict__)
    isolated.race_relations = dict(repo.race_relations)
    isolated.race_relations["human_to_dwarf_test"] = RaceRelationRecord(
        id="human_to_dwarf_test",
        source_race="human",
        target_race="dwarf",
        relationship_model="test_fixture",
        axes={"hostility": "high"},
    )
    service = RelationProjectionService(isolated)

    result = service.project_relation(
        "hero_guild_perspective", "hero_guild", "dwarven_mine_clan",
        RelationContext(source_race="human", target_race="dwarf"),
    )
    assert result.label == "ally"


def test_pre_existing_relation_projection_unaffected_by_no_race_entry(repo):
    """Regression guard: entities with no authored race_relations entry (or no race
    context at all) must produce identical output to pre-ticket behavior."""
    service = RelationProjectionService(repo)
    result = service.project_relation("hero_guild_perspective", "hero_guild", "goblin_warband")
    assert result.label == "enemy"

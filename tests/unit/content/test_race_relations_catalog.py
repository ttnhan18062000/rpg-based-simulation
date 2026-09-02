"""Schema/catalog-loading tests for data/content/social/race_relations.yaml.

TCK-20260831-RACE-RELATIONS-MATRIX: mirrors test_faction_relationships_coverage.py's own
catalog-load pattern for the new race_relations content family (Steps 1-2 of the plan).
"""
import pytest
from pydantic import ValidationError

from src.content.repository import CatalogRepository
from src.content.schema import RaceRelationRecord


@pytest.fixture(scope="module")
def repo() -> CatalogRepository:
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def test_race_relations_content_family_loads(repo):
    assert repo.race_relations, "race_relations should be populated from data/content/social/race_relations.yaml"
    for record in repo.race_relations.values():
        assert isinstance(record, RaceRelationRecord)


def test_race_relation_record_extra_forbid_rejects_bad_field():
    with pytest.raises(ValidationError):
        RaceRelationRecord(
            id="bad_entry",
            source_race="human",
            target_race="wolf",
            relationship_model="predator_prey",
            axes={"hostility": "medium_contextual"},
            unexpected_field="not allowed",
        )


def test_race_relation_record_required_fields_enforced():
    record = RaceRelationRecord(
        id="human_to_wolf_check",
        source_race="human",
        target_race="wolf",
        relationship_model="predator_prey",
        axes={"hostility": "medium_contextual"},
    )
    assert record.source_race == "human"
    assert record.target_race == "wolf"
    assert record.axes == {"hostility": "medium_contextual"}


def test_get_race_relationship_lookup(repo):
    record = repo.get_race_relationship("wolf_to_human")
    assert record is not None
    assert record.source_race == "wolf"
    assert record.target_race == "human"

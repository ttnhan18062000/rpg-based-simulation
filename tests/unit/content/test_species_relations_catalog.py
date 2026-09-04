"""Schema/catalog-loading tests for data/content/social/species_relations.yaml.

TCK-20260831-RACE-RELATIONS-MATRIX: mirrors test_faction_relationships_coverage.py's own
catalog-load pattern for the species_relations content family (Steps 1-2 of the plan).
"""
import pytest
from pydantic import ValidationError

from src.content.repository import CatalogRepository
from src.content.schema import SpeciesRelationRecord


@pytest.fixture(scope="module")
def repo() -> CatalogRepository:
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def test_species_relations_content_family_loads(repo):
    assert repo.species_relations, "species_relations should be populated from data/content/social/species_relations.yaml"
    for record in repo.species_relations.values():
        assert isinstance(record, SpeciesRelationRecord)


def test_species_relation_record_extra_forbid_rejects_bad_field():
    with pytest.raises(ValidationError):
        SpeciesRelationRecord(
            id="bad_entry",
            source_species="human",
            target_species="wolf",
            relationship_model="predator_prey",
            axes={"hostility": "medium_contextual"},
            unexpected_field="not allowed",
        )


def test_species_relation_record_required_fields_enforced():
    record = SpeciesRelationRecord(
        id="human_to_wolf_check",
        source_species="human",
        target_species="wolf",
        relationship_model="predator_prey",
        axes={"hostility": "medium_contextual"},
    )
    assert record.source_species == "human"
    assert record.target_species == "wolf"
    assert record.axes == {"hostility": "medium_contextual"}


def test_get_species_relationship_lookup(repo):
    record = repo.get_species_relationship("wolf_to_human")
    assert record is not None
    assert record.source_species == "wolf"
    assert record.target_species == "human"

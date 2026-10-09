"""Decisions 44, 46 and 50: a kind declares coarse PROPERTIES, never a predator/prey/grazer/hunter label.

Stage order and relations only: no exact figure is pinned here, only that each kind declares a band and food-class
sets, that the vocabulary rejects anything else, and that no behaviour module reads a trait or role list as a label.
"""
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.content.repository import CatalogRepository
from src.content.schema import BodyModelDefinition, FOOD_CLASSES, PROPERTY_BANDS, SpeciesDefinition
from src.content.validator import kind_property_gap_issues

SRC = Path(__file__).resolve().parents[3] / "src"
# The content layer owns these lists; nothing that decides behaviour may read them.
LABEL_READS = (
    "natural_traits", "compatible_roles", "role_family", "get_role_family",
    ".is_combatant(", ".is_civilian(", ".is_worker(", "ecological_predator",
)
CONTENT_LAYER = ("content/", "content_semantics/role.py")


@pytest.fixture(scope="module")
def repo() -> CatalogRepository:
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def test_every_species_declares_its_properties(repo):
    assert kind_property_gap_issues(repo) == []


def test_declared_values_come_from_the_vocabulary(repo):
    for species in repo.species.values():
        assert species.power in PROPERTY_BANDS and species.wits in PROPERTY_BANDS
    for body in repo.body_models.values():
        assert body.size in PROPERTY_BANDS
        assert set(body.diet) <= set(FOOD_CLASSES) and set(body.edible_as) <= set(FOOD_CLASSES)


def test_a_missing_property_is_a_gap_not_a_default(repo):
    stripped = repo.species["wolf"].model_copy(update={"power": None})
    repo.species["wolf"], original = stripped, repo.species["wolf"]
    try:
        assert [i.target_id for i in kind_property_gap_issues(repo)] == ["wolf"]
    finally:
        repo.species["wolf"] = original


def test_bands_and_food_classes_reject_anything_else():
    with pytest.raises(ValidationError):
        BodyModelDefinition(id="x", display_name="X", size="enormous")
    with pytest.raises(ValidationError):
        BodyModelDefinition(id="x", display_name="X", diet=["predator"])
    with pytest.raises(ValidationError):
        SpeciesDefinition.model_validate({"id": "x", "display_name": "X", "power": "mighty"})


def test_no_behaviour_module_reads_a_label_list():
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        rel = path.relative_to(SRC).as_posix()
        if rel.startswith(CONTENT_LAYER[0]) or rel == CONTENT_LAYER[1]:
            continue
        text = path.read_text(encoding="utf-8")
        offenders += [f"{rel}: {token}" for token in LABEL_READS if token in text]
    assert offenders == []

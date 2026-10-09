"""The icon item families (`TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS`): the user's mapping covers every item of the real catalog, and an unknown category fails instead of falling through."""

from __future__ import annotations

from collections import Counter

import pytest

from visual_assets.review.icon_item_families import UnmappedCategory, family_of, load_mapping
from visual_assets.review.pilot_colour_vision import REPO


@pytest.fixture(scope="module")
def catalog_items():
    from src.content.repository import CatalogRepository

    repo = CatalogRepository(str(REPO / "data" / "content"))
    repo.load_all()
    return repo.items


def test_the_mapping_is_the_users_six_families_one_per_first_category():
    mapping = load_mapping()
    assert mapping == {"weapon": "weapon", "armor": "armor", "trinket": "trinket", "tool": "tool", "consumable": "consumable", "material": "material"}
    assert len(set(mapping.values())) == 6


def test_every_item_of_the_real_catalog_maps_to_exactly_one_family(catalog_items):
    mapping = load_mapping()
    families = {item_id: family_of(item.categories, mapping) for item_id, item in catalog_items.items()}
    assert len(families) == len(catalog_items) > 0
    assert set(families.values()) == set(mapping.values())  # no family is empty, none is invented
    # the first category is the app's item_type (metadata_presenter); measured 2026-10-07: 37 items
    assert Counter(families.values()) == {"material": 19, "weapon": 10, "trinket": 2, "armor": 2, "tool": 2, "consumable": 2}


def test_every_first_category_in_the_catalog_is_mapped_and_every_mapped_category_is_used(catalog_items):
    mapping = load_mapping()
    first = {item.categories[0] for item in catalog_items.values() if item.categories}
    assert first == set(mapping)


def test_no_item_of_the_catalog_lacks_categories(catalog_items):
    assert [i for i, item in catalog_items.items() if not item.categories] == []


def test_a_planted_unknown_category_fails_instead_of_falling_through():
    mapping = load_mapping()
    with pytest.raises(UnmappedCategory, match="gemstone"):
        family_of(["gemstone", "arcane"], mapping)
    with pytest.raises(UnmappedCategory):
        family_of([], mapping)
    # only the FIRST tag decides: a later tag naming a mapped category does not rescue an unknown first one
    with pytest.raises(UnmappedCategory):
        family_of(["gemstone", "weapon"], mapping)
    assert family_of(["weapon", "gemstone"], mapping) == "weapon"


def test_a_new_category_added_to_a_catalog_is_caught_by_the_same_check(catalog_items):
    mapping = load_mapping()

    class Planted:
        categories = ["relic", "artifact"]

    with pytest.raises(UnmappedCategory):
        for item in [*catalog_items.values(), Planted()]:
            family_of(item.categories, mapping)

"""Icon item families: the user-approved total mapping from an item's first category to one icon family (`visual_assets/icons/item_families.yaml`).

`family_of` is deliberately strict: an item with no categories, or a first category that is not mapped, raises instead of falling through to a default, so a new category in the content catalog forces
a decision (the guard in `test_icon_item_families.py` runs it over every item of the real catalog). Pure; reads the yaml only.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from tests.visual_assets.pilot_colour_vision import REPO

FAMILIES_FILE = REPO / "visual_assets" / "icons" / "item_families.yaml"


class UnmappedCategory(KeyError):
    pass


def load_mapping(path: Path = FAMILIES_FILE) -> dict[str, str]:
    data = yaml.safe_load(path.read_text())
    assert data["record_type"] == "icon_item_families" and data["schema_version"] == 1
    mapping = data["families"]
    assert mapping and all(isinstance(k, str) and isinstance(v, str) for k, v in mapping.items())
    return dict(mapping)


def family_of(categories: list[str], mapping: dict[str, str]) -> str:
    """The icon family of an item: the family of its FIRST category (the app's `item_type`). Raises `UnmappedCategory` for none or an unknown one."""
    if not categories:
        raise UnmappedCategory("<no categories>")
    first = categories[0]
    if first not in mapping:
        raise UnmappedCategory(first)
    return mapping[first]

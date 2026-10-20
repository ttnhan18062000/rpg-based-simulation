"""`icon_lookalikes.adopted_icon_sprites()` is the art the store holds NOW (`TCK-20261019-VISUAL-ASSETS-ICON-SPRITES-SOURCE-IS-R0001`).

Read-only: the test reads the committed built artifacts (`visual_assets/catalog/generated/<source>--x1/<hash>.rNNNN.artifact.json`, one per icon source, carrying `source_revision` and `pixel_hash`)
and compares them with the accessor's pixels. It runs no store command, so it takes no lock, writes nothing and builds nothing. `pin_mismatches` is the one comparison both the pin and the negative
test call: a revision the accessor drops (the old r0001 art left in place) shows up as that key.
"""

from __future__ import annotations

import json
from pathlib import Path

from tests.visual_assets import adopted_facts as af
from visual_assets.review import icon_lookalikes as la
from visual_assets.review import icon_owner_fixes_draft_set as fixes
from visual_assets.review import icon_sheet_rule as rule
from visual_assets.store import config, pixels

CATALOG = Path(config.CATALOG_ROOT)
# Store icon sources that are NOT among the 36 icons of the accessor, each with the reason.
EXCLUDED = {
    **{k.replace(".", "_"): "object marker (`object-markers-v1`, adopted 2026-10-14): drawn after the 36-icon sheet" for k in af.OBJECT_KEYS},
    **{k.replace(".", "_"): "entity role marker (`entity-markers-v1`, adopted 2026-10-19): drawn after the 36-icon sheet" for k in af.ENTITY_KEYS},
}
REVISED = {k.replace(".", "_") for k in fixes.PROPOSED}


def source_of(key: str) -> str:
    return key.replace(".", "_")


def store_icon_sources() -> set[str]:
    return {p.name for p in (CATALOG / "sources").iterdir() if p.name.startswith("icon_")}


def store_record(source: str) -> dict:
    found = sorted((CATALOG / "generated" / f"{source}--x1").glob("*.artifact.json"))
    assert len(found) == 1, f"{source}: expected exactly one built artifact, found {len(found)}"
    return json.loads(found[0].read_text())


def pixel_hash_of(sprite: rule.Sprite) -> str:
    return pixels.pixel_hash_of(pixels.DecodedImage(sprite.width, sprite.height, b"".join(bytes(p) for p in sprite.rgba)))


def pin_mismatches(sprites: dict[str, rule.Sprite]) -> list[str]:
    """The keys whose sprite is not the pixels (or the revision) the store holds: wrong pixel hash, or r0002 expected for a revised key and r0001 otherwise."""
    bad = []
    for key in sorted(sprites):
        record = store_record(source_of(key))
        revision = "r0002" if source_of(key) in REVISED else "r0001"
        if record["pixel_hash"] != pixel_hash_of(sprites[key]) or record["source_revision"] != revision:
            bad.append(key)
    return bad


def test_every_store_icon_source_is_an_accessor_key_or_explicitly_excluded():
    accessor = {source_of(k) for k in la.adopted_icon_sprites()}
    store = store_icon_sources()
    assert len(accessor) == 36 and len(EXCLUDED) == 29 and not accessor & set(EXCLUDED)
    assert store - accessor - set(EXCLUDED) == set(), "a new adopted icon key is in neither the 36 icons nor the excluded set: decide which"
    assert accessor - store == set(), "an accessor key has no store source"
    assert set(EXCLUDED) - store == set(), "the excluded set names a source the store does not hold"


def test_the_accessor_is_the_art_the_store_holds_for_every_icon_key():
    assert pin_mismatches(la.adopted_icon_sprites()) == []
    assert REVISED == {source_of(k) for k in fixes.PROPOSED} and len(REVISED) == 7


def test_the_old_art_is_not_what_the_store_holds_for_the_seven_revised_keys():
    assert pin_mismatches(la.r0001_icon_sprites()) == sorted(fixes.PROPOSED)


def test_dropping_one_adopted_revision_from_the_accessor_is_reported_as_that_key(monkeypatch):
    kept = tuple(k for k in fixes.PROPOSED if k != "icon.item.tool")
    monkeypatch.setattr(fixes, "PROPOSED", kept)
    assert pin_mismatches(la.adopted_icon_sprites()) == ["icon.item.tool"]

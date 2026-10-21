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
from visual_assets.store import config, pixels, records

CATALOG = Path(config.CATALOG_ROOT)
# Store icon sources that are NOT among the 36 icons of the accessor, each with the reason.
EXCLUDED = {
    **{k.replace(".", "_"): "object marker (`object-markers-v1`, adopted 2026-10-14): drawn after the 36-icon sheet" for k in af.OBJECT_KEYS},
    **{k.replace(".", "_"): "entity role marker (`entity-markers-v1`, adopted 2026-10-19): drawn after the 36-icon sheet" for k in af.ENTITY_KEYS},
}


def source_of(key: str) -> str:
    return key.replace(".", "_")


def store_icon_sources() -> set[str]:
    return {p.name for p in (CATALOG / "sources").iterdir() if p.name.startswith("icon_")}


def newest_adopted_revision(source: str) -> str:
    """The newest revision of `source` that has a SourceRecord and no revocation, read from `sources/<source>/` (read-only record functions: no lock, no CLI, no write)."""
    eligible = [r for r in records.list_revisions(source) if records.is_eligible(source, r)]
    assert eligible, f"{source}: no eligible revision in the store"
    return max(eligible)


def store_record(source: str) -> dict:
    found = sorted((CATALOG / "generated" / f"{source}--x1").glob("*.artifact.json"))
    assert len(found) == 1, f"{source}: expected exactly one built artifact, found {len(found)}"
    return json.loads(found[0].read_text())


def pixel_hash_of(sprite: rule.Sprite) -> str:
    return pixels.pixel_hash_of(pixels.DecodedImage(sprite.width, sprite.height, b"".join(bytes(p) for p in sprite.rgba)))


def pin_mismatches(sprites: dict[str, rule.Sprite]) -> list[str]:
    """The keys whose sprite is not what the store holds: the built artifact is not the source's NEWEST adopted revision (an adopted but unbuilt revision shows here), or its pixel hash differs."""
    bad = []
    for key in sorted(sprites):
        record = store_record(source_of(key))
        if record["source_revision"] != newest_adopted_revision(source_of(key)) or record["pixel_hash"] != pixel_hash_of(sprites[key]):
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
    newest = {k: newest_adopted_revision(source_of(k)) for k in la.adopted_icon_sprites()}
    assert {k for k, r in newest.items() if r == "r0002"} == set(fixes.PROPOSED) and len(fixes.PROPOSED) == 7  # derived from the store, not assumed
    assert {r for k, r in newest.items() if k not in fixes.PROPOSED} == {"r0001"}


def test_an_adopted_revision_that_is_not_built_yet_is_reported(monkeypatch):
    real = records.list_revisions
    monkeypatch.setattr(records, "list_revisions", lambda source, root=None: [*real(source, root), "r0003"] if source == "icon_item_tool" else real(source, root))
    monkeypatch.setattr(records, "is_eligible", lambda source, revision, *a, **k: True)
    assert pin_mismatches(la.adopted_icon_sprites()) == ["icon.item.tool"]  # the store's newest is r0003, the built artifact and the accessor are r0002


def test_the_old_art_is_not_what_the_store_holds_for_the_seven_revised_keys():
    assert pin_mismatches(la.r0001_icon_sprites()) == sorted(fixes.PROPOSED)


def test_dropping_one_adopted_revision_from_the_accessor_is_reported_as_that_key(monkeypatch):
    kept = tuple(k for k in fixes.PROPOSED if k != "icon.item.tool")
    monkeypatch.setattr(fixes, "PROPOSED", kept)
    assert pin_mismatches(la.adopted_icon_sprites()) == ["icon.item.tool"]

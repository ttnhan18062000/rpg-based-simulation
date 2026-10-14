"""The owner's adoption of `object-markers-v1` (2026-10-14, `TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS`) is in the catalog exactly as recorded: 18 keys, one source each, all built."""

from __future__ import annotations

import json

from tests.visual_assets import adopted_facts as af
from visual_assets.store import config, records
from visual_assets.store.catalog.registry import load_registry


def test_the_set_adoption_record_holds_the_eighteen_keys_and_the_hash_and_time_the_owner_decided():
    record = json.loads((config.CATALOG_ROOT / "provenance" / "set-adoptions" / f"{af.OBJECT_SET_ADOPTION_ID}.json").read_text())
    assert record["set_id"] == af.OBJECT_SET_ID and record["draft_set_hash"] == af.OBJECT_DRAFT_SET_HASH and record["decided_at"] == af.OBJECT_DECIDED_AT
    assert sorted(e["visual_key"] for e in record["entries"]) == af.OBJECT_KEYS and len(record["entries"]) == 18
    # The command template's placeholders were recorded literally; the owner's erratum is in docs/assets/store_contract.md. Pinned so a silent rewrite of the record fails.
    assert (record["approver_name"], record["approver_role"]) == ("<your name>", "<your role>")


def test_every_object_key_is_registered_optional_and_held_by_its_own_source_and_has_a_built_artifact():
    registry = load_registry()
    generated = {p.name for p in (config.CATALOG_ROOT / "generated").iterdir()}
    for key in af.OBJECT_KEYS:
        assert registry.keys[key].optional and registry.keys[key].variant_axes == (), key
        assert records.slot_holders(registry.keys[key], None) == [key.replace(".", "_")], key
        assert key.replace(".", "_") + "--x1" in generated, key

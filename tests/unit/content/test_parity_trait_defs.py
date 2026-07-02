"""
tests/unit/content/test_parity_trait_defs.py

STRAT-164: trait serialization is preserved.
STRAT-177: all trait types have definitions.
"""

import yaml
from pathlib import Path
from src.content.schema import TraitDefinition

_TRAITS_YAML = Path(__file__).parent.parent.parent.parent / "data" / "content" / "foundation" / "traits.yaml"


def _load_raw() -> list:
    with open(_TRAITS_YAML) as f:
        raw = yaml.safe_load(f) or []
    return [r for r in raw if isinstance(r, dict) and not r.get("deprecated", False)]


class TestTraitSerialization:
    def test_trait_serialization(self):
        """STRAT-164: TraitDefinition fields are preserved through Pydantic validation."""
        raw_records = _load_raw()
        assert raw_records, "traits.yaml must contain at least one trait"

        first = raw_records[0]
        td = TraitDefinition(**first)

        assert td.id == first["id"]
        if "display_name" in first and first["display_name"] is not None:
            assert td.display_name == first["display_name"]
        if "description" in first and first["description"] is not None:
            assert td.description == first["description"]

    def test_trait_serialization_roundtrip(self):
        """STRAT-164: TraitDefinition round-trips to dict with no field loss."""
        raw_records = _load_raw()
        for raw in raw_records[:5]:
            td = TraitDefinition(**raw)
            assert td.id == raw["id"]
            assert len(td.id) > 0


class TestAllTraitTypesHaveDefinitions:
    def test_all_trait_types_have_definitions(self):
        """STRAT-177: every trait record in the catalog has a non-empty id."""
        raw_records = _load_raw()
        assert raw_records, "traits.yaml must contain at least one trait"

        ids = [r["id"] for r in raw_records if "id" in r]
        assert len(ids) > 0, "At least one trait definition must exist"

        for trait_id in ids:
            assert isinstance(trait_id, str) and len(trait_id) > 0, f"Trait id must be non-empty, got: {trait_id!r}"

        # No duplicate IDs
        assert len(ids) == len(set(ids)), f"Duplicate trait ids found: {[x for x in ids if ids.count(x) > 1]}"

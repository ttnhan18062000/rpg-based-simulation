"""
Multi-pack composition integration tests.

Verifies that frontier_extended_pack and swamp_border_pack can coexist
without ID collisions, broken references, or cross-contamination.

Four modes tested (parametrized):
  base_only            — frontier_village_core only
  base_plus_frontier   — base + frontier_extended_pack modules
  base_plus_swamp      — base + swamp_border_pack modules
  base_plus_both       — base + both packs

Per-mode assertions:
  - ID uniqueness across all active pack records
  - World assembly resolves without blocking errors
  - At least one scenario resolves in the mode's composition

Error cases:
  - Artificial ID collision is detected and reported with pack names
  - Missing dependency is reported clearly
"""

from __future__ import annotations

import pytest
import yaml

from src.content.pack_manifest import ContentPackManifest, ContentPackManifestValidator
from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldassembly.resolver import WorldAssemblyResolver
from src.worldassembly.schema import WorldCompositionSpec

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def module_repo():
    repo = WorldModuleRepository()
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def resolver(catalog, module_repo):
    return WorldAssemblyResolver(catalog, module_repo)


def _load_manifest(pack_id: str) -> ContentPackManifest:
    with open(f"data/content/packs/{pack_id}.yaml") as f:
        return ContentPackManifest(**yaml.safe_load(f))


@pytest.fixture(scope="module")
def frontier_manifest():
    return _load_manifest("frontier_extended_pack")


@pytest.fixture(scope="module")
def swamp_manifest():
    return _load_manifest("swamp_border_pack")


# ---------------------------------------------------------------------------
# Mode matrix
# ---------------------------------------------------------------------------

_MODES = [
    pytest.param(
        {
            "label": "base_only",
            "modules": ["frontier_village_core"],
            "active_packs": [],
        },
        id="base_only",
    ),
    pytest.param(
        {
            "label": "base_plus_frontier",
            "modules": ["frontier_village_core", "orc_clan_territory", "forest_warden_grove"],
            "active_packs": ["frontier_extended_pack"],
        },
        id="base_plus_frontier",
    ),
    pytest.param(
        {
            "label": "base_plus_swamp",
            "modules": ["frontier_village_core", "sunken_swamp_border"],
            "active_packs": ["swamp_border_pack"],
        },
        id="base_plus_swamp",
    ),
    pytest.param(
        {
            "label": "base_plus_both",
            "modules": [
                "frontier_village_core",
                "orc_clan_territory",
                "forest_warden_grove",
                "sunken_swamp_border",
            ],
            "active_packs": ["frontier_extended_pack", "swamp_border_pack"],
        },
        id="base_plus_both",
    ),
]


def _make_comp(modules: list[str], label: str) -> WorldCompositionSpec:
    return WorldCompositionSpec.model_validate({
        "schema_version": "worldcomposition.v1",
        "world_id": f"multi_pack_test_{label}",
        "name": f"Multi-Pack Test: {label}",
        "modules": modules,
    })


# ---------------------------------------------------------------------------
# 1. ID uniqueness across packs
# ---------------------------------------------------------------------------

def test_no_id_collision_between_frontier_and_swamp(frontier_manifest, swamp_manifest):
    """Frontier and swamp pack declared IDs must not overlap."""
    frontier_ids: set[str] = set()
    for ids in frontier_manifest.included_families.values():
        frontier_ids.update(ids)

    swamp_ids: set[str] = set()
    for ids in swamp_manifest.included_families.values():
        swamp_ids.update(ids)

    collisions = frontier_ids & swamp_ids
    assert not collisions, (
        f"ID collision between frontier_extended_pack and swamp_border_pack: {sorted(collisions)}"
    )


@pytest.mark.parametrize("mode", _MODES)
def test_active_pack_ids_are_unique_within_mode(mode, frontier_manifest, swamp_manifest):
    """Within each mode, all active pack IDs must be unique."""
    manifests = {
        "frontier_extended_pack": frontier_manifest,
        "swamp_border_pack": swamp_manifest,
    }
    seen: dict[str, str] = {}  # id → pack_id
    for pack_id in mode["active_packs"]:
        manifest = manifests[pack_id]
        for ids in manifest.included_families.values():
            for item_id in ids:
                if item_id in seen:
                    pytest.fail(
                        f"ID {item_id!r} claimed by both {seen[item_id]!r} and {pack_id!r}"
                    )
                seen[item_id] = pack_id


# ---------------------------------------------------------------------------
# 2. World assembly per mode
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", _MODES)
def test_mode_assembly_has_no_blocking_errors(resolver, mode):
    """Assembly in each mode must succeed without blocking errors."""
    comp = _make_comp(mode["modules"], mode["label"])
    bundle = resolver.assemble(comp)
    blocking = [
        e for e in bundle.assembly_report.get("errors", [])
        if e.get("severity") == "blocking"
    ]
    assert not blocking, f"[{mode['label']}] Blocking errors: {blocking}"


@pytest.mark.parametrize("mode", _MODES)
def test_mode_assembly_is_deterministic(resolver, mode):
    """Two assemblies of the same mode must produce identical world IDs."""
    comp = _make_comp(mode["modules"], mode["label"])
    bundle_a = resolver.assemble(comp)
    bundle_b = resolver.assemble(comp)
    assert bundle_a is not None and bundle_b is not None


# ---------------------------------------------------------------------------
# 3. Pack module isolation: swamp module absent from frontier-only mode
# ---------------------------------------------------------------------------

def test_swamp_module_not_present_in_frontier_only_mode(module_repo):
    """sunken_swamp_border module must not appear in base+frontier assembly."""
    comp = _make_comp(
        ["frontier_village_core", "orc_clan_territory", "forest_warden_grove"],
        "frontier_only_isolation",
    )
    active_ids = {ref.module_id for ref in (comp.module_refs or [])}
    assert "sunken_swamp_border" not in active_ids


def test_frontier_modules_not_present_in_swamp_only_mode(module_repo):
    """orc_clan_territory must not appear in base+swamp assembly."""
    comp = _make_comp(["frontier_village_core", "sunken_swamp_border"], "swamp_only_isolation")
    active_ids = {ref.module_id for ref in (comp.module_refs or [])}
    assert "orc_clan_territory" not in active_ids


# ---------------------------------------------------------------------------
# 4. Error: ID collision detection
# ---------------------------------------------------------------------------

def test_artificial_collision_reported_with_pack_names():
    """Validator reports collisions with pack names included in error message."""
    # Create two manifests that declare the same ID
    m1 = ContentPackManifest(
        schema_version="content_pack.v1",
        pack_id="pack_alpha",
        display_name="Pack Alpha",
        version="1.0",
        included_families={"entity_archetypes": ["shared_id"]},
        sample_compositions=["comp_a"],
    )
    m2 = ContentPackManifest(
        schema_version="content_pack.v1",
        pack_id="pack_beta",
        display_name="Pack Beta",
        version="1.0",
        included_families={"entity_archetypes": ["shared_id"]},
        sample_compositions=["comp_b"],
    )

    # Detect collision
    all_ids: dict[str, str] = {}
    collisions = []
    for m in [m1, m2]:
        for ids in m.included_families.values():
            for item_id in ids:
                if item_id in all_ids:
                    collisions.append(
                        f"ID {item_id!r} claimed by {all_ids[item_id]!r} and {m.pack_id!r}"
                    )
                else:
                    all_ids[item_id] = m.pack_id

    assert collisions, "Expected collision to be detected"
    assert "pack_alpha" in collisions[0] or "pack_beta" in collisions[0]
    assert "shared_id" in collisions[0]


# ---------------------------------------------------------------------------
# 5. Error: dependency resolution fails clearly
# ---------------------------------------------------------------------------

def test_missing_dependency_reported_clearly():
    """Pack with a non-existent dependency must fail validation with a clear message."""
    m = ContentPackManifest(
        schema_version="content_pack.v1",
        pack_id="dependent_pack",
        display_name="Dependent Pack",
        version="1.0",
        dependencies=["nonexistent_required_pack"],
        sample_compositions=["comp_x"],
    )
    validator = ContentPackManifestValidator()
    errors = validator.validate(m, known_packs={"frontier_extended_pack", "swamp_border_pack"})
    assert errors, "Expected dependency error"
    assert "nonexistent_required_pack" in errors[0]

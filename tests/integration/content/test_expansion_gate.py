"""
Content Expansion Readiness Gate.

Asserts all prerequisite conditions before horizontal content expansion begins
(new races, factions, archetypes, regions, modules, scenarios).

Run standalone with:
    pytest tests/integration/content/test_expansion_gate.py -v

Each gate item maps to one checklist line in the output. Items blocked by
the pre-existing CAT-REL-099 defect (moon_cult_ruins / apprentice_mage) are
marked xfail(strict=False) so they appear as expected-failures rather than hard
failures in the baseline report.

Pass conditions required before expansion:
  01  Content family registry complete (all families load)
  02  Fail-closed scenario schema active (extra="forbid")
  03  Content reference graph builds without error
  04  No new dead active-data violations beyond known baseline
  05  Entity archetypes present in catalog
  06  Populations reference valid archetypes
  07  All world modules normalize without error
  08  All world composition specs load without error
  09  Registry adapters project without AdapterError
  10  Scenario schema validates correctly
  11  World assembly resolves at least one composition  [xfail: CAT-REL-099]
  12  Migration map covers all required legacy families
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Tuple

import pytest
import yaml

from src.content.reference_graph import ContentReferenceGraph, FAMILY_TO_SHORT
from src.content.repository import CatalogRepository, CANONICAL_FAMILIES
from src.worldmodules.repository import WorldModuleRepository

pytestmark = [pytest.mark.content_pack, pytest.mark.integration]

_CAT_REL_099 = pytest.mark.xfail(
    reason="CAT-REL-099: moon_cult_ruins references apprentice_mage population not in catalog; "
    "CatalogValidator sweeps entire catalog so all assembly calls fail.",
    strict=False,
)

# Inline baseline from test_active_data_consumer — must stay in sync with that file.
_ACTIVE_STATES = frozenset({"EXISTING-LOGIC", "LEGACY-EXPORT", "REDESIGNED-CORE"})
_FAMILIES_WITH_IMPLICIT_CONSUMERS = frozenset({"attribute", "element", "perspective", "projection"})
_KNOWN_INACTIVE_CONTENT: frozenset[Tuple[str, str]] = frozenset({
    ("faction", "neutral"),
    ("role", "shopkeeper"),
    ("stat_profile", "monster_base"),
    ("item", "apprentice_staff"),
    ("item", "basic_bow"),
    ("item", "herb"),
    ("item", "leather_armor"),
    ("item", "rusted_sword"),
    ("item", "wooden_staff"),
    ("recipe", "craft_small_potion"),
    ("skill_profile", "warrior_skills"),
})
_STATE_RE = re.compile(r"#\s*STATE:\s*(\S+)")
_ID_RE = re.compile(r"^-?\s*id:\s*[\"']?([^\"':\s#]+)[\"']?\s*(?:#.*)?$")


# ---------------------------------------------------------------------------
# Shared fixtures
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
def ref_graph(catalog, module_repo):
    return ContentReferenceGraph(
        repo=catalog,
        modules=list(module_repo.modules.values()),
    )


# ---------------------------------------------------------------------------
# Gate item 01 — Content family registry complete
# ---------------------------------------------------------------------------

def test_gate_01_content_family_registry_complete(catalog):
    """All CANONICAL_FAMILIES must load without KeyError."""
    for spec in CANONICAL_FAMILIES:
        family_dict = getattr(catalog, spec.repository_index, None)
        assert family_dict is not None, (
            f"CatalogRepository missing attribute {spec.repository_index!r} "
            f"for family {spec.family!r} — family not registered"
        )


# ---------------------------------------------------------------------------
# Gate item 02 — Fail-closed scenario schema active
# ---------------------------------------------------------------------------

def test_gate_02_fail_closed_scenario_schema_active():
    """SimulationScenarioDefinition must reject unknown fields (extra='forbid')."""
    from src.scenarios.schema import SimulationScenarioDefinition
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        SimulationScenarioDefinition(
            id="gate-test",
            world_composition="any",
            perspective="hero",
            unknown_field_xyz=True,  # should be rejected
        )


# ---------------------------------------------------------------------------
# Gate item 03 — Content reference graph builds
# ---------------------------------------------------------------------------

def test_gate_03_reference_graph_builds(ref_graph):
    """ContentReferenceGraph must build without raising."""
    assert ref_graph is not None


# ---------------------------------------------------------------------------
# Gate item 04 — No new dead active-data violations
# ---------------------------------------------------------------------------

def test_gate_04_no_new_dead_active_data(catalog, module_repo):
    """Active content records must have at least one consumer path.

    New violations beyond KNOWN_INACTIVE_CONTENT fail the gate.
    """
    ref_graph = ContentReferenceGraph(
        repo=catalog,
        modules=list(module_repo.modules.values()),
    )
    family_to_short: Dict[str, str] = FAMILY_TO_SHORT
    path_to_family: Dict[Path, str] = {}
    for spec in CANONICAL_FAMILIES:
        path = Path("data/content") / spec.path
        if path.is_file():
            path_to_family[path] = spec.family.split(".")[-1]

    violations = []
    for file_path, short_family in path_to_family.items():
        if short_family in _FAMILIES_WITH_IMPLICIT_CONSUMERS:
            continue
        if short_family not in family_to_short.values():
            continue
        text = file_path.read_text(encoding="utf-8")
        current_state = None
        for line in text.splitlines():
            m = _STATE_RE.search(line)
            if m:
                current_state = m.group(1)
            if current_state not in _ACTIVE_STATES:
                continue
            id_m = _ID_RE.match(line)
            if not id_m:
                continue
            record_id = id_m.group(1)
            key = (short_family, record_id)
            if key in _KNOWN_INACTIVE_CONTENT:
                continue
            node_id = f"{short_family}:{record_id}"
            if not ref_graph.is_record_used(node_id):
                violations.append(f"  {short_family}:{record_id} (no consumer path)")

    assert not violations, (
        f"Gate 04 FAIL — {len(violations)} active record(s) with no consumer path:\n"
        + "\n".join(violations)
        + "\nAdd to KNOWN_INACTIVE_CONTENT or add a consumer path."
    )


# ---------------------------------------------------------------------------
# Gate item 05 — Archetypes present in catalog
# ---------------------------------------------------------------------------

def test_gate_05_entity_archetypes_present(catalog):
    """Catalog must have at least one entity archetype."""
    assert len(catalog.entity_archetypes) > 0, (
        "Gate 05 FAIL — no entity archetypes found in catalog"
    )


# ---------------------------------------------------------------------------
# Gate item 06 — Populations reference valid archetypes
# ---------------------------------------------------------------------------

def test_gate_06_populations_reference_valid_archetypes(catalog):
    """Each population record's archetype_id must resolve in the catalog."""
    violations = []
    for pop_id, pop in catalog.populations.items():
        archetype_id = getattr(pop, "archetype_id", None)
        if archetype_id and archetype_id not in catalog.entity_archetypes:
            violations.append(
                f"  population:{pop_id} references archetype:{archetype_id!r} not in catalog"
            )
    assert not violations, (
        f"Gate 06 FAIL — {len(violations)} population(s) with invalid archetype_id:\n"
        + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# Gate item 07 — World modules normalize
# ---------------------------------------------------------------------------

def test_gate_07_world_modules_normalize(module_repo):
    """All world modules must normalize without error."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    failures = []
    for module_id, spec in module_repo.modules.items():
        try:
            WorldModuleAuthoringNormalizer.normalize(spec)
        except Exception as e:
            failures.append(f"  {module_id}: {e}")
    assert not failures, (
        f"Gate 07 FAIL — {len(failures)} module(s) failed normalization:\n"
        + "\n".join(failures)
    )


# ---------------------------------------------------------------------------
# Gate item 08 — World compositions load
# ---------------------------------------------------------------------------

def test_gate_08_world_compositions_load():
    """All world composition YAML files must parse into WorldCompositionSpec."""
    from src.worldassembly.schema import WorldCompositionSpec
    compositions_dir = Path("data/content/world_compositions")
    failures = []
    for yaml_file in sorted(compositions_dir.glob("*.yaml")):
        try:
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            WorldCompositionSpec.model_validate(data)
        except Exception as e:
            failures.append(f"  {yaml_file.name}: {e}")
    assert not failures, (
        f"Gate 08 FAIL — {len(failures)} composition(s) failed to load:\n"
        + "\n".join(failures)
    )


# ---------------------------------------------------------------------------
# Gate item 09 — Registry adapters project
# ---------------------------------------------------------------------------

def test_gate_09_registry_adapters_project(catalog):
    """CatalogToXxx adapters must run without raising AdapterError."""
    from src.core.modes import RuntimeContentMode
    from src.core.registries import (
        CatalogToItemRegistryAdapter,
        CatalogToRecipeRegistryAdapter,
        CatalogToRegionRegistryAdapter,
        CatalogToResourceRegistryAdapter,
        CatalogToServiceRegistryAdapter,
        AdapterError,
    )
    mode = RuntimeContentMode.CATALOG_WITH_COMPATIBILITY
    try:
        CatalogToItemRegistryAdapter(catalog, mode=mode).adapt()
        CatalogToRecipeRegistryAdapter(catalog).adapt()
        CatalogToServiceRegistryAdapter(catalog, catalog_mode=True, mode=mode).adapt()
        CatalogToRegionRegistryAdapter(catalog).adapt()
        CatalogToResourceRegistryAdapter(catalog, mode=mode).adapt()
    except AdapterError as e:
        pytest.fail(f"Gate 09 FAIL — Adapter raised AdapterError: {e}")


# ---------------------------------------------------------------------------
# Gate item 10 — Scenario schema validates
# ---------------------------------------------------------------------------

def test_gate_10_scenario_schema_validates():
    """SimulationScenarioDefinition must accept a minimal valid scenario."""
    from src.scenarios.schema import SimulationScenarioDefinition
    scenario = SimulationScenarioDefinition(
        id="expansion-gate-baseline",
        world_composition="frontier_only",
        perspective="hero",
    )
    assert scenario.id == "expansion-gate-baseline"


# ---------------------------------------------------------------------------
# Gate item 11 — World assembly resolves  [xfail: CAT-REL-099]
# ---------------------------------------------------------------------------

@_CAT_REL_099
def test_gate_11_world_assembly_resolves(catalog, module_repo):
    """WorldAssemblyResolver must assemble at least one composition without error."""
    from src.worldassembly.resolver import WorldAssemblyResolver
    resolver = WorldAssemblyResolver(catalog, module_repo)
    compositions_dir = Path("data/content/world_compositions")
    from src.worldassembly.schema import WorldCompositionSpec
    import yaml as _yaml
    first = sorted(compositions_dir.glob("*.yaml"))[0]
    with open(first) as f:
        spec = WorldCompositionSpec.model_validate(_yaml.safe_load(f))
    result = resolver.assemble(spec)
    assert result is not None


# ---------------------------------------------------------------------------
# Gate item 12 — Migration map covers required families
# ---------------------------------------------------------------------------

def test_gate_12_migration_map_covers_required_families():
    """migration_map.yaml must exist and cover all required legacy families."""
    map_path = Path("data/content/compatibility/migration_map.yaml")
    assert map_path.is_file(), "Gate 12 FAIL — migration_map.yaml missing"
    with open(map_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data.get("schema_version") == "migration_map.v1", (
        "Gate 12 FAIL — migration_map.yaml has wrong schema_version"
    )
    families_present = {e["legacy_family"] for e in data.get("entries", [])}
    required = {"resource", "recipe", "region", "enemy", "role_enum", "faction_enum", "item", "service"}
    missing = required - families_present
    assert not missing, (
        f"Gate 12 FAIL — migration_map.yaml missing required families: {sorted(missing)}"
    )

"""Positive and negative controls for tools/world_composition_corpus_probe.py.

A detector that reports zero proves nothing unless it is shown to fire on a deliberately introduced
instance, so every check gets one end-to-end or pure-data case where it must fire and one where it
must stay quiet. The end-to-end cases register tiny synthetic modules into the real module repository
and resolve them through the real ``WorldAssemblyResolver``.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import world_composition_corpus_probe as probe  # noqa: E402

from src.worldassembly.resolve_io import load_content_repositories  # noqa: E402
from src.worldassembly.resolver import ResolverError  # noqa: E402
from src.worldassembly.schema import ModuleRefSpec, WorldCompositionSpec  # noqa: E402
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.recipe import PlaceRecipeSpec, RegionRecipeSpec  # noqa: E402
from src.worldbuilding.schema import FactionSpec, WorldSpec  # noqa: E402
from src.worldmodules.schema import WorldModuleSpec  # noqa: E402


@pytest.fixture(scope="module")
def repos():
    return load_content_repositories()


def _register(module_repo, spec: WorldModuleSpec) -> None:
    module_repo.modules[spec.module_id] = spec
    module_repo.raw_data[spec.module_id] = spec.model_dump()


def _module(module_id: str, regions) -> WorldModuleSpec:
    return WorldModuleSpec(
        schema_version="worldmodule.v1",
        module_id=module_id,
        module_type="terrain",
        display_name=module_id,
        regions=list(regions),
    )


def _composition(world_id: str, refs) -> WorldCompositionSpec:
    return WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id=world_id,
        name=world_id,
        module_refs=[ModuleRefSpec(module_id=m, enabled=True, order=i, namespace=ns) for i, (m, ns) in enumerate(refs)],
    )


def _base_spec() -> dict:
    return {
        "schema_version": "worldspec.v1",
        "world_id": "probe_valley",
        "name": "Probe Valley",
        "topology": {"width": 50, "height": 50, "coordinate_system": "grid"},
        "regions": [
            {"id": "town_square", "type": "town", "bounds": [0, 0, 10, 10], "terrain": "GRASS"},
            {"id": "wilds", "type": "wilderness", "bounds": [15, 15, 40, 40], "terrain": "FOREST"},
        ],
        "factions": [{"id": "villagers", "type": "civilian"}],
        "entities": [{"id": "citizens", "count": 2, "role": "citizen", "faction": "villagers", "spawn_region": "town_square"}],
        "resources": [],
        "buildings": [],
    }


# ---- duplicate_place_ids ---------------------------------------------------------------


def test_duplicate_place_ids_fires_and_compile_loses_the_place():
    data = _base_spec()
    data["regions"][0]["places"] = [{"id": "shrine", "kind": "LANDMARK", "position": [2, 2]}]
    data["regions"][1]["places"] = [{"id": "shrine", "kind": "LANDMARK", "position": [20, 20]}]
    spec = WorldSpec.model_validate(data)

    row = probe.duplicate_place_ids(spec)
    assert row["duplicate_ids"] == ["shrine"] and row["count"] == 1 and row["places_declared"] == 2

    # The compiler's bare dict assignment keeps one of the two: the overwrite the probe measures.
    state, _ = WorldCompiler.compile(spec, seed=42)
    assert len(state.places) == 1


def test_duplicate_place_ids_quiet_for_distinct_ids():
    data = _base_spec()
    data["regions"][0]["places"] = [{"id": "shrine", "kind": "LANDMARK", "position": [2, 2]}]
    data["regions"][1]["places"] = [{"id": "ruin", "kind": "LANDMARK", "position": [20, 20]}]
    row = probe.duplicate_place_ids(WorldSpec.model_validate(data))
    assert row["count"] == 0 and row["places_declared"] == 2


def test_duplicate_place_ids_end_to_end_through_the_resolver(repos):
    catalog, module_repo = repos
    place = PlaceRecipeSpec(id="shrine", kind="LANDMARK", position=(2, 2))
    place_b = PlaceRecipeSpec(id="shrine", kind="LANDMARK", position=(22, 22))
    _register(module_repo, _module("probe_dup_a", [RegionRecipeSpec(id="hometown", type="town", grid_bounds=(0, 0, 5, 5), places=[place])]))
    _register(module_repo, _module("probe_dup_b", [RegionRecipeSpec(id="bandit_road", type="wilderness", grid_bounds=(20, 20, 25, 25), places=[place_b])]))
    rows = probe.probe_composition(_composition("probe_dup_world", [("probe_dup_a", None), ("probe_dup_b", None)]), catalog, module_repo)
    row = next(r for r in rows if r["check"] == "duplicate_place_ids")
    assert row["duplicate_ids"] == ["shrine"]
    assert row["places_declared"] == 2 and row["places_lost_at_compile"] == 1


# ---- dropped_placements ----------------------------------------------------------------


def test_dropped_placements_fires_for_each_kind_of_dangling_reference():
    data = _base_spec()
    data["entities"].append({"id": "ghosts", "count": 1, "role": "monster", "faction": "villagers", "spawn_region": "nowhere"})
    data["resources"] = [{"id": "ore", "resource_type": "ore", "count": 1, "region": "nowhere"}]
    data["buildings"] = [{"id": "hut", "type": "inn", "region": "nowhere"}]
    row = probe.dropped_placements(WorldSpec.model_validate(data))
    assert row["count"] == 3
    assert {d.split(":")[0] for d in row["dangling"]} == {"population", "resource", "building"}


def test_dropped_placements_quiet_for_resolving_references():
    assert probe.dropped_placements(WorldSpec.model_validate(_base_spec()))["count"] == 0


# ---- faction_merge ---------------------------------------------------------------------


def test_faction_merge_fires_for_an_id_the_resolver_did_not_pre_seed():
    row = probe.faction_merge(["villagers"], [("mod_a", [FactionSpec(id="orphans", type="neutral")])])
    assert row["not_pre_seeded"] == ["mod_a:orphans"] and row["count"] == 1


def test_faction_merge_fires_when_two_modules_disagree_about_one_id():
    contributions = [
        ("mod_a", [FactionSpec(id="villagers", type="civilian")]),
        ("mod_b", [FactionSpec(id="villagers", type="hostile")]),
    ]
    row = probe.faction_merge(["villagers"], contributions)
    assert row["differing_definitions"] == ["villagers"] and row["count"] == 1


def test_faction_merge_quiet_when_every_contribution_matches_the_seed():
    contributions = [
        ("mod_a", [FactionSpec(id="villagers", type="civilian")]),
        ("mod_b", [FactionSpec(id="villagers", type="civilian")]),
    ]
    row = probe.faction_merge(["villagers"], contributions)
    assert row["count"] == 0 and row["contributions"] == 2


def test_a_module_naming_a_faction_outside_the_catalog_cannot_reach_the_merge(repos):
    """Why the corpus count is structurally zero: the resolver refuses such a module before any merge."""
    catalog, module_repo = repos
    bad = WorldModuleSpec(
        schema_version="worldmodule.v1",
        module_id="probe_bad_faction",
        module_type="terrain",
        display_name="bad",
        regions=[RegionRecipeSpec(id="hometown", type="town", grid_bounds=(0, 0, 5, 5))],
        factions=["no_such_faction_in_the_catalog"],
    )
    _register(module_repo, bad)
    with pytest.raises(ResolverError):
        probe.probe_composition(_composition("probe_bf_world", [("probe_bad_faction", None)]), catalog, module_repo)


# ---- biome_provenance ------------------------------------------------------------------


def _biome_row(repos, namespace: str):
    catalog, module_repo = repos
    assert catalog.get_region("hometown") is not None and catalog.get_region("hometown").biome
    mid = f"probe_biome_{namespace or 'bare'}"
    _register(module_repo, _module(mid, [RegionRecipeSpec(id="hometown", type="town", grid_bounds=(0, 0, 5, 5))]))
    rows = probe.probe_composition(_composition(f"{mid}_world", [(mid, namespace)]), catalog, module_repo)
    return next(r for r in rows if r["check"] == "biome_provenance")


def test_biome_provenance_fires_for_a_namespace_that_contains_an_underscore(repos):
    row = _biome_row(repos, "moon_cult")
    assert row["count"] == 1
    mismatch = row["mismatches"][0]
    assert mismatch["region"] == "moon_cult_hometown" and mismatch["namespaced"] is True
    assert mismatch["expected_biome"] and mismatch["recorded_biome"] is None


def test_biome_provenance_quiet_for_a_single_word_namespace(repos):
    row = _biome_row(repos, "trading")
    assert row["count"] == 0 and row["namespaced_regions"] == 1


def test_biome_provenance_quiet_without_a_namespace(repos):
    row = _biome_row(repos, None)
    assert row["count"] == 0 and row["namespaced_regions"] == 0


# ---- validator_residue / output --------------------------------------------------------


def test_validator_residue_counts_issues_per_rule_without_raising(repos):
    catalog, _ = repos
    data = _base_spec()
    data["resources"] = []  # NoResourcesWarningRule must fire
    row = probe.validator_residue(WorldSpec.model_validate(data), catalog)
    assert row["per_rule"].get("WORLD-WARN-001") == 1 and row["count"] >= 1


def test_main_rejects_a_non_jsonl_output_path(tmp_path):
    with pytest.raises(SystemExit):
        probe.main(["--out", str(tmp_path / "evidence.json")])


def test_summarize_reports_zero_counts_per_check():
    rows = [{"world": "w", "check": c, "count": 0} for c in probe.CHECKS]
    summary = probe.summarize(rows)
    assert all(summary[c] == {"worlds": 1, "worlds_nonzero": 0, "total": 0} for c in probe.CHECKS)

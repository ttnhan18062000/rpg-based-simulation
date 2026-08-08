"""TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY — corpus_registry.yaml coverage/consistency."""
import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from generate_corpus_registry import build_worlds_section, generate  # noqa: E402

ANCHORS_PATH = Path("tests/simulation_quality/fixtures/grade_anchors.json")
WORLDS_ROOT = Path("data/worlds")
REGISTRY_PATH = Path("config/simulation_quality/corpus_registry.yaml")


def _real_anchor_run_keys() -> set[str]:
    anchors = json.loads(ANCHORS_PATH.read_text())
    return {k for k in anchors if not k.startswith("_")}


def test_corpus_registry_covers_every_anchored_run_key():
    entries = generate()
    assert set(entries.keys()) == _real_anchor_run_keys()


def test_corpus_registry_world_names_resolve_to_real_directories():
    entries = generate()
    for run_key, entry in entries.items():
        world_dir = WORLDS_ROOT / entry["world_name"]
        assert world_dir.is_dir(), f"{run_key}: world_name {entry['world_name']!r} has no real directory"


def test_corpus_registry_scale_fields_match_compile_report():
    entries = generate()
    sample_keys = list(entries.keys())[:5]
    for run_key in sample_keys:
        entry = entries[run_key]
        report_path = WORLDS_ROOT / entry["world_name"] / "world_compile_report.json"
        report = json.loads(report_path.read_text())
        assert entry["scale"]["entity_count"] == report.get("entity_count")
        assert entry["scale"]["region_count"] == report.get("region_count")


def test_corpus_registry_committed_file_matches_fresh_generation():
    """Guards against the committed file going stale relative to real anchors/world data —
    the same staleness pattern corpus_tier_taxonomy.md's own gap-list hit twice (2026-08-05)."""
    assert REGISTRY_PATH.exists(), "run `make simq-corpus-registry` to generate the committed file"
    committed = yaml.safe_load(REGISTRY_PATH.read_text())
    fresh = generate()
    committed_run_keys = {k: v for k, v in committed.items() if k != "_worlds"}
    assert committed_run_keys == fresh
    assert committed["_worlds"] == build_worlds_section(fresh)


def test_corpus_registry_worlds_section_dedupes_correctly():
    """TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW — one _worlds entry per unique world_name,
    with scale/tier verified (not assumed) identical across every run_key for that world."""
    entries = generate()
    worlds = build_worlds_section(entries)
    real_world_names = {e["world_name"] for e in entries.values()}
    assert set(worlds.keys()) == real_world_names
    for world_name, summary in worlds.items():
        for run_key in summary["run_keys"]:
            assert entries[run_key]["scale"] == summary["scale"]
            assert entries[run_key]["tier"] == summary["tier"]


def test_corpus_registry_worlds_run_keys_cross_reference_real_entries():
    entries = generate()
    worlds = build_worlds_section(entries)
    for world_name, summary in worlds.items():
        for run_key in summary["run_keys"]:
            assert run_key in entries, f"{world_name}: run_key {run_key!r} not a real registry entry"


_DENSITY_KEYS = {
    "entity_density_per_area", "entity_density_per_region", "resource_density",
    "quest_density", "faction_density", "building_density",
}


def test_worlds_section_has_density_subobject():
    """TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE — every world entry carries the 6 documented
    density metrics."""
    entries = generate()
    worlds = build_worlds_section(entries)
    for world_name, summary in worlds.items():
        assert "density" in summary, f"{world_name}: missing density sub-object"
        assert set(summary["density"].keys()) == _DENSITY_KEYS, f"{world_name}: unexpected density keys"


def test_density_values_are_real_not_placeholder():
    """Spot-check against hand-computed expected values from real scale/topology data — not a
    tautological computed-vs-computed check."""
    entries = generate()
    worlds = build_worlds_section(entries)
    urban = worlds["urban_political"]
    scale = urban["scale"]
    resolved = yaml.safe_load((WORLDS_ROOT / "urban_political" / "resolved" / "world.resolved.yaml").read_text())
    map_area = resolved["topology"]["width"] * resolved["topology"]["height"]
    assert urban["density"]["entity_density_per_area"] == round(scale["entity_count"] / map_area, 6)
    assert urban["density"]["resource_density"] == round(scale["resource_node_count"] / scale["region_count"], 4)
    assert urban["density"]["quest_density"] == round(scale["quest_count"] / scale["entity_count"], 4)


def test_density_values_internally_consistent_with_source_counts():
    """entity_density_per_region * region_count recovers entity_count (within float tolerance),
    and similarly for the other region-based ratios — catches a formula/field-mismatch bug."""
    entries = generate()
    worlds = build_worlds_section(entries)
    for world_name, summary in worlds.items():
        scale = summary["scale"]
        density = summary["density"]
        region_count = scale["region_count"]
        assert density["entity_density_per_region"] * region_count == pytest.approx(scale["entity_count"], abs=0.01)
        assert density["resource_density"] * region_count == pytest.approx(scale["resource_node_count"], abs=0.01)
        assert density["faction_density"] * region_count == pytest.approx(scale["distinct_populated_factions"], abs=0.01)
        assert density["building_density"] * region_count == pytest.approx(scale["building_count"], abs=0.01)
        assert density["quest_density"] * scale["entity_count"] == pytest.approx(scale["quest_count"], abs=0.01)


def test_no_world_breaches_high_entity_density_warning_threshold():
    """Real assertion from investigation.md: every world's entity_density_per_area stays under
    HighEntityDensityWarningRule's own 0.5 threshold (src/worldbuilding/validator.py:WORLD-WARN-002),
    computed fresh from real topology + entity_count, not hardcoded expected values."""
    entries = generate()
    worlds = build_worlds_section(entries)
    for world_name, summary in worlds.items():
        assert summary["density"]["entity_density_per_area"] < 0.5, (
            f"{world_name}: entity_density_per_area {summary['density']['entity_density_per_area']} "
            f"breaches HighEntityDensityWarningRule's 0.5 threshold"
        )


_ARCHETYPE_VALUES = {"civilian_settlement", "monster_only_gauntlet"}


def test_worlds_section_has_archetype_field():
    """TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS — every world entry carries a real,
    computed archetype value, not a placeholder."""
    entries = generate()
    worlds = build_worlds_section(entries)
    for world_name, summary in worlds.items():
        assert "archetype" in summary, f"{world_name}: missing archetype"
        assert summary["archetype"] in _ARCHETYPE_VALUES, f"{world_name}: unexpected archetype value"


def test_monster_only_gauntlet_worlds_correctly_identified():
    """Real, corpus-wide survey (investigation.md): wilderness_survival, dungeon_crawl, and
    quest_dense_frontier are the only 3 worlds with zero civilian-service (worker/guard/merchant/
    blacksmith) population -- every other world has all 4."""
    entries = generate()
    worlds = build_worlds_section(entries)
    monster_only = {
        name for name, summary in worlds.items() if summary["archetype"] == "monster_only_gauntlet"
    }
    assert monster_only == {"wilderness_survival", "dungeon_crawl", "quest_dense_frontier"}
    assert worlds["sandbox_world"]["archetype"] == "civilian_settlement"
    assert worlds["urban_political"]["archetype"] == "civilian_settlement"

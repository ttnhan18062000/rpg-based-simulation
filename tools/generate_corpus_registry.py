#!/usr/bin/env python3
"""Generate config/simulation_quality/corpus_registry.yaml from real, authoritative data.

One entry per grade_anchors.json run_key — never hand-transcribed. Reuses evaluate_simq.py's own
world/profile resolution (`_resolve_world_name`, `_parse_run_key`) rather than re-deriving it, so
this registry can't silently diverge from what SimQ itself actually calibrates.

Per-world tier + one-line archetype description is transcribed once from
docs/simulation_quality/corpus_tier_taxonomy.md's own table (TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY) —
that doc points at this registry for machine-readable facts going forward, not the reverse.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_simq import WORLDS_ROOT, _parse_run_key, _resolve_world_name  # noqa: E402

ANCHORS_PATH = Path("tests/simulation_quality/fixtures/grade_anchors.json")
PROFILES_DIR = Path("config/simulation_quality/profiles")
OUTPUT_PATH = Path("config/simulation_quality/corpus_registry.yaml")

# One-time transcription from corpus_tier_taxonomy.md's per-world table (2026-08-08).
# Keyed by world_name (the resolved data/worlds/ directory), not run_key or profile_name.
_WORLD_TIER = {
    "wilderness_survival": "end_to_end",
    "sandbox_world": "end_to_end",
    "highland_traverse": "end_to_end",
    "urban_political": "regression_baseline",
    "dungeon_crawl": "end_to_end",
    "swamp_border_world": "end_to_end",
    "simq_routing_test": "regression_baseline",
    "frontier_living_world": "end_to_end",
    "generated_frontier_3_42": "end_to_end",
    "frontier_extended": "end_to_end",
    "unit_faction_tension": "unit",
    "unit_information_source": "unit",
    "unit_selfmodel_pilot": "unit",
    "hero_guild_routing": "unit",
    "unit_information_density": "unit",
    "crowded_frontier": "stress",
    "resource_dense_basin": "stress",
    "frontier_marches": "stress",
    "quest_dense_frontier": "stress",
    "simq_scale_stress_seed42": "stress",
}


def _load_feature_flag_overrides(profile_name: str) -> dict:
    path = PROFILES_DIR / f"{profile_name}.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    return data.get("feature_flags", {})


def _load_compile_report(world_name: str) -> dict:
    path = WORLDS_ROOT / world_name / "world_compile_report.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def generate() -> dict:
    anchors = json.loads(ANCHORS_PATH.read_text())
    entries = {}
    for run_key in sorted(anchors.keys()):
        if run_key.startswith("_"):
            continue
        profile_name, seed, ticks = _parse_run_key(run_key)
        world_name = _resolve_world_name(profile_name)
        compile_report = _load_compile_report(world_name)
        flags = _load_feature_flag_overrides(profile_name)
        entries[run_key] = {
            "world_name": world_name,
            "profile_name": profile_name,
            "seed": seed,
            "ticks": ticks,
            "tier": _WORLD_TIER.get(world_name, "unclassified"),
            "scale": {
                "entity_count": compile_report.get("entity_count"),
                "region_count": compile_report.get("region_count"),
                "resource_node_count": compile_report.get("resource_node_count"),
                "building_count": compile_report.get("building_count"),
                "quest_count": compile_report.get("quest_count"),
                "distinct_populated_factions": compile_report.get("distinct_populated_factions"),
            },
            "active_feature_flags": flags,
        }
    return entries


def compute_density(world_name: str, scale: dict) -> dict:
    """6 real, distinct density ratios (TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE) — each
    answers a different question, none invented without one (see this ticket's own
    investigation.md). `entity_density_per_area` reuses the exact same denominator
    (topology.width * topology.height) as HighEntityDensityWarningRule's own WORLD-WARN-002
    threshold check and src/world/spawn.py's runtime monster-density formula, so it's directly
    comparable to both. `resource_density`/`quest_density` reuse the exact metric definitions
    already established by TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE /
    TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE, not reinvented.
    """
    resolved_path = WORLDS_ROOT / world_name / "resolved" / "world.resolved.yaml"
    resolved = yaml.safe_load(resolved_path.read_text())
    topology = resolved["topology"]
    map_area = topology["width"] * topology["height"]

    entity_count = scale["entity_count"]
    region_count = scale["region_count"]

    return {
        "entity_density_per_area": round(entity_count / map_area, 6),
        "entity_density_per_region": round(entity_count / region_count, 4),
        "resource_density": round(scale["resource_node_count"] / region_count, 4),
        "quest_density": round(scale["quest_count"] / entity_count, 4),
        "faction_density": round(scale["distinct_populated_factions"] / region_count, 4),
        "building_density": round(scale["building_count"] / region_count, 4),
    }


_CIVILIAN_SERVICE_KINDS = frozenset({"worker", "guard", "merchant", "blacksmith"})


def compute_archetype(world_name: str) -> str:
    """"civilian_settlement" vs "monster_only_gauntlet" (TCK-20260808-LIFECYCLE-SCORE-WORLD-
    ARCHETYPE-AWARENESS) — a real, corpus-wide survey found population composition is genuinely
    bimodal: every world either has all 4 of worker/guard/merchant/blacksmith, or none of them at
    all (no world sits in between). Reads the same static resolved YAML compute_density() already
    reads — no live Kernel/world-compile needed. Note: entity.identity.role (the EntityRole enum)
    is NOT a reliable signal for this — real data shows monster-kind entities are tagged
    role=CITIZEN corpus-wide, not role=MONSTER; entity.kind (this file's resolved "role" field,
    confusingly named but distinct from EntityRole) is the real, reliable signal.
    """
    resolved_path = WORLDS_ROOT / world_name / "resolved" / "world.resolved.yaml"
    resolved = yaml.safe_load(resolved_path.read_text())
    kinds = {entry.get("role") for entry in resolved.get("entities", [])}
    if kinds & _CIVILIAN_SERVICE_KINDS:
        return "civilian_settlement"
    return "monster_only_gauntlet"


def build_worlds_section(entries: dict) -> dict:
    """Derive a per-world_name summary from the per-run_key entries — one entry per unique world
    (vs. up to 10 duplicate run_key entries for the same world across seeds/tick-lengths), so
    "what's this world's size/tier" has a direct lookup point instead of requiring the reader to
    find and read any one of several scattered, alphabetically-sorted run_key entries.

    Asserts (not assumes) that `scale`/`tier` are identical across every run_key belonging to the
    same world — true by construction (scale/tier are world-compile facts, not per-seed/per-tick
    ones) but verified here rather than silently trusted, since a violation would mean the
    generator itself has a bug worth surfacing loudly, not silently picking one value.
    """
    worlds: dict[str, dict] = {}
    for run_key, entry in sorted(entries.items()):
        world_name = entry["world_name"]
        if world_name not in worlds:
            worlds[world_name] = {
                "tier": entry["tier"],
                "scale": entry["scale"],
                "density": compute_density(world_name, entry["scale"]),
                "archetype": compute_archetype(world_name),
                "run_keys": [],
            }
        else:
            assert worlds[world_name]["scale"] == entry["scale"], (
                f"{world_name}: scale differs between run_keys — "
                f"{worlds[world_name]['run_keys'][0]!r} vs {run_key!r}. This should never happen "
                f"(scale is a world-compile fact, not per-seed/per-tick) — investigate before "
                f"trusting this registry's dedup."
            )
            assert worlds[world_name]["tier"] == entry["tier"], (
                f"{world_name}: tier differs between run_keys — "
                f"{worlds[world_name]['run_keys'][0]!r} vs {run_key!r}."
            )
        worlds[world_name]["run_keys"].append(run_key)
    return worlds


class _NoAliasDumper(yaml.SafeDumper):
    """Disables YAML anchor/alias generation (&id001/*id001) for repeated identical dicts —
    the _worlds section's own scale dicts are byte-identical to their run_key counterparts by
    construction, which PyYAML would otherwise alias, making the file harder to read at exactly
    the point this ticket exists to make it easier to read."""
    def ignore_aliases(self, data):
        return True


def main() -> None:
    entries = generate()
    worlds = build_worlds_section(entries)
    # "_worlds" is a sibling key alongside the run_key entries, not a restructure of the file's
    # top level — backward compatible with existing consumers (tools/simq_ceiling.py's own
    # tick_budget_ceilings() iterates every top-level key and skips any entry with no "ticks"
    # field via entry.get("ticks") is None, so a "_worlds" entry is silently, safely ignored by
    # code written before this key existed). The leading underscore marks it as metadata, the
    # same convention grade_anchors.json already uses for its own "_note"/"_instructions" keys.
    output = dict(entries)
    output["_worlds"] = worlds
    OUTPUT_PATH.write_text(
        "# Generated by tools/generate_corpus_registry.py — do not hand-edit.\n"
        "# Regenerate: make simq-corpus-registry\n"
        "#\n"
        "# '_worlds' — one entry per unique world (look up size/tier here first, not in the\n"
        "# per-run_key entries below, which repeat the same world's data once per seed/tick).\n"
        + yaml.dump(output, Dumper=_NoAliasDumper, sort_keys=True, default_flow_style=False)
    )
    print(f"Wrote {len(worlds)} worlds (_worlds), {len(entries)} run_key entries to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

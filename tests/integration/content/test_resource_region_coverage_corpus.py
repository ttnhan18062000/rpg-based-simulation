"""
Corpus-wide resource-region coverage audit.

TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT: turns this ticket's most
safety-critical finding (zero hero-role entities corpus-wide are affected by any remaining
source_region_tags gap) into a durable regression guard. Live-globs
data/worlds/*/resolved/world.resolved.yaml rather than hardcoding a world list, so newly
authored worlds are automatically included -- the exact "corpus grew silently" drift this
ticket's investigation found relative to the parent ticket's stale 10/11-world table.

Deliberately does NOT assert an exact-equality all-role uncovered set: bandit_road,
goblin_camp, and wolf_den carry zero resource-node content by design (see
docs/guidelines/intentional_divergences.md #2.29) and are excluded from the hero-role
assertion by definition (no hero-role entity spawns there today), not by an explicit
allowlist in this test.
"""

from __future__ import annotations

import glob

import yaml

from src.content.repository import CatalogRepository
from src.core.modes import RuntimeContentMode
from src.core.registries import CatalogToResourceRegistryAdapter


def _load_covered_region_tags() -> set:
    repo = CatalogRepository("data/content")
    repo.load_all()
    resources, _ = CatalogToResourceRegistryAdapter(
        repo, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY
    ).adapt()
    covered: set = set()
    for res_def in resources.values():
        covered.update(res_def.source_region_tags)
    return covered


def _iter_world_entities():
    for path in sorted(glob.glob("data/worlds/*/resolved/world.resolved.yaml")):
        with open(path) as f:
            world = yaml.safe_load(f)
        for entity in world.get("entities", []):
            yield world.get("world_id", path), entity


def test_no_hero_role_entity_spawns_in_an_uncovered_region_corpus_wide():
    """AC: "Each uncovered region has an explicit disposition recorded" — this test asserts the
    live, current-state consequence of that disposition work: no hero-role entity anywhere in
    the corpus spawns in a region that no resource kind's source_region_tags covers. This is
    the calibration-critical case (AdventureDecisionPhase can permanently stick a hero on
    defer_with_reason for exactly this condition); non-hero uncovered regions are a documented,
    lower-severity finding (see docs/parity_ledger/town_resource.yaml TOWN-189 and
    docs/guidelines/intentional_divergences.md #2.28/#2.29), not asserted here."""
    covered = _load_covered_region_tags()

    uncovered_hero_spawns = []
    for world_id, entity in _iter_world_entities():
        if entity.get("role") != "hero":
            continue
        spawn_region = entity.get("spawn_region")
        if spawn_region and spawn_region not in covered:
            uncovered_hero_spawns.append((world_id, entity.get("id"), spawn_region))

    assert uncovered_hero_spawns == [], (
        f"Hero-role entities spawning in a region with zero resource-kind coverage: "
        f"{uncovered_hero_spawns!r}"
    )

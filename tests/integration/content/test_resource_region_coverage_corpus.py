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

TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP: GuildAction.visit() (wired live via
GuildVisitPhase in TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING) is role-agnostic -- unlike
AdventureDecisionPhase, it is not gated to hero-role entities. A fresh corpus-wide re-scan
(prompted by that wiring going live) found the corpus had drifted since 2026-07-06: 3 new
regions appeared (river_ford, deep_forest, survivor_outpost) that this file's original
hero-only check would never have caught for a non-hero entity. river_ford was a genuine tag-gap
(fixed additively, herb_patch's source_region_tags gained "river_ford" -- see
data/content/world/resources.yaml); deep_forest/survivor_outpost are zero-content regions by
design, extending the same #2.29 disposition class. Added
test_no_entity_of_any_role_spawns_in_an_unresolved_region_corpus_wide below to close this
role-scope gap going forward -- any future new region must get an explicit disposition
(catalog fix or accepted-gap allowlist entry) regardless of which role spawns there first.
"""

from __future__ import annotations

import glob

import yaml

from src.content.repository import CatalogRepository
from src.core.modes import RuntimeContentMode
from src.core.registries import CatalogToResourceRegistryAdapter

# Regions with zero resource-node content by design, reviewed and accepted as an intentional
# hazard-zone/no-foraging-content gap (docs/guidelines/intentional_divergences.md #2.29).
# Extending this set requires the same disposition-tracing rigor as the original audit and
# TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP applied -- confirm zero physical resource
# placement (not just an absent source_region_tags entry) before adding a region here.
_ACCEPTED_ZERO_CONTENT_REGIONS = frozenset({
    "bandit_road", "goblin_camp", "wolf_den", "deep_forest", "survivor_outpost",
})


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


def test_no_entity_of_any_role_spawns_in_an_unresolved_region_corpus_wide():
    """TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP: GuildAction.visit()'s scarcity
    computation (feeding QuestGenerator's pressure-weighted template selection) is role-agnostic
    and now live-dispatched -- unlike AdventureDecisionPhase, it isn't limited to hero-role
    entities. Any entity of any role spawning in a region that is neither covered by some
    resource kind's source_region_tags NOR an explicitly reviewed zero-content region
    (_ACCEPTED_ZERO_CONTENT_REGIONS) is an unresolved disposition gap this test must catch --
    silently treating it as "fully abundant" (scarcity=0.0) would be wrong either way (real
    tag-gap needing a catalog fix, or a new zero-content region needing an explicit accepted-gap
    entry), so this test intentionally does not distinguish between the two failure shapes; it
    only asserts SOME explicit disposition exists for every region any entity actually spawns
    in."""
    covered = _load_covered_region_tags()

    unresolved_spawns = []
    for world_id, entity in _iter_world_entities():
        spawn_region = entity.get("spawn_region")
        if spawn_region and spawn_region not in covered and spawn_region not in _ACCEPTED_ZERO_CONTENT_REGIONS:
            unresolved_spawns.append((world_id, entity.get("id"), entity.get("role"), spawn_region))

    assert unresolved_spawns == [], (
        f"Entities (any role) spawning in a region with neither resource-kind coverage nor an "
        f"explicit accepted-zero-content disposition: {unresolved_spawns!r} -- either add a "
        f"catalog source_region_tags fix (if a resource node is physically placed there) or "
        f"add the region to _ACCEPTED_ZERO_CONTENT_REGIONS (if confirmed zero-content by design)"
    )

"""Coverage/guard tests for data/content/social/race_relations.yaml.

TCK-20260831-RACE-RELATIONS-MATRIX: mirrors test_faction_relationships_coverage.py's
POPULATED_FACTIONS-frozenset pattern for races. Guards the disclosed ~18% coverage
threshold (24 directed entries / 66 populated undirected pairs) this ticket established,
so a future edit cannot silently shrink coverage below what was reviewed and shipped.
"""
import itertools

import pytest

from src.content.repository import CatalogRepository

# The 12 races with a real data/content/entities/entity_archetypes.yaml spawn path
# (confirmed via grep -c "race:" per race). `slime` is excluded -- zero archetype entries,
# no live spawn path, mirroring test_faction_relationships_coverage.py's own
# "zero module path to population" exclusion rationale.
POPULATED_RACES = frozenset({
    "human", "wolf", "goblin", "spider", "orc", "elf", "dwarf",
    "undead", "troll", "lizardfolk", "dragonkin", "spirit",
})

POPULATED_PAIR_COUNT = len(list(itertools.combinations(sorted(POPULATED_RACES), 2)))  # C(12,2) = 66


@pytest.fixture(scope="module")
def repo() -> CatalogRepository:
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def _undirected_pairs(repo: CatalogRepository) -> set[frozenset[str]]:
    return {
        frozenset({rr.source_race, rr.target_race})
        for rr in repo.race_relations.values()
    }


def test_race_relations_coverage_meets_disclosed_threshold(repo):
    """AC #4 -- a disclosed defensible subset (~18% of 66 populated pairs), not all 156
    directed pairs uniformly. Guards against silent coverage regression below the 12
    undirected pairs (24 directed entries) authored and reviewed for this ticket."""
    all_pairs = _undirected_pairs(repo)
    populated_pairs = {pair for pair in all_pairs if pair <= POPULATED_RACES}
    assert len(populated_pairs) >= 12, (
        f"Populated-only race-pair coverage regressed: {len(populated_pairs)}/{POPULATED_PAIR_COUNT} "
        f"(need >= 12/66, ~18%)"
    )
    assert len(populated_pairs) < POPULATED_PAIR_COUNT, (
        "Coverage is expected to remain a disclosed partial subset, not full 66-pair coverage."
    )


def test_race_relations_reference_valid_races_and_axes(repo):
    # repo.races -> repo.species: hard coupling with TCK-20260904-SPECIES-CORE-SCHEMA-RENAME's
    # CatalogRepository rename. This file's own race_relations/source_race/target_race naming
    # is untouched here -- that belongs to TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME.
    race_ids = set(repo.species.keys())
    axis_ids = set(repo.relationship_axes.keys())

    for rr in repo.race_relations.values():
        assert rr.source_race in race_ids, f"{rr.id}: unknown source_race {rr.source_race!r}"
        assert rr.target_race in race_ids, f"{rr.id}: unknown target_race {rr.target_race!r}"
        for axis_key in rr.axes:
            assert axis_key in axis_ids, f"{rr.id}: unknown axis key {axis_key!r}"


def test_race_relations_no_same_race_entry(repo):
    for rr in repo.race_relations.values():
        assert rr.source_race != rr.target_race, (
            f"{rr.id}: nonsensical same-race entry ({rr.source_race} -> {rr.target_race})"
        )


def test_race_relations_entries_are_bidirectional(repo):
    """Every authored undirected pair has both directions authored, matching
    faction_relationships.yaml's own bidirectional-entry convention."""
    directed_pairs = {(rr.source_race, rr.target_race) for rr in repo.race_relations.values()}
    for source, target in directed_pairs:
        assert (target, source) in directed_pairs, (
            f"Missing reverse-direction entry for {source} -> {target}"
        )

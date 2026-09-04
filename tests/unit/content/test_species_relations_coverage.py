"""Coverage/guard tests for data/content/social/species_relations.yaml.

TCK-20260831-RACE-RELATIONS-MATRIX: mirrors test_faction_relationships_coverage.py's
POPULATED_FACTIONS-frozenset pattern for species. Guards the disclosed ~18% coverage
threshold (24 directed entries / 66 populated undirected pairs) this ticket established,
so a future edit cannot silently shrink coverage below what was reviewed and shipped.
"""
import itertools

import pytest

from src.content.repository import CatalogRepository

# The 12 species with a real data/content/entities/entity_archetypes.yaml spawn path
# (confirmed via grep -c "species:" per species). `slime` is excluded -- zero archetype entries,
# no live spawn path, mirroring test_faction_relationships_coverage.py's own
# "zero module path to population" exclusion rationale.
POPULATED_SPECIES = frozenset({
    "human", "wolf", "goblin", "spider", "orc", "elf", "dwarf",
    "undead", "troll", "lizardfolk", "dragonkin", "spirit",
})

POPULATED_PAIR_COUNT = len(list(itertools.combinations(sorted(POPULATED_SPECIES), 2)))  # C(12,2) = 66


@pytest.fixture(scope="module")
def repo() -> CatalogRepository:
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def _undirected_pairs(repo: CatalogRepository) -> set[frozenset[str]]:
    return {
        frozenset({rr.source_species, rr.target_species})
        for rr in repo.species_relations.values()
    }


def test_species_relations_coverage_meets_disclosed_threshold(repo):
    """AC #4 -- a disclosed defensible subset (~18% of 66 populated pairs), not all 156
    directed pairs uniformly. Guards against silent coverage regression below the 12
    undirected pairs (24 directed entries) authored and reviewed for this ticket."""
    all_pairs = _undirected_pairs(repo)
    populated_pairs = {pair for pair in all_pairs if pair <= POPULATED_SPECIES}
    assert len(populated_pairs) >= 12, (
        f"Populated-only species-pair coverage regressed: {len(populated_pairs)}/{POPULATED_PAIR_COUNT} "
        f"(need >= 12/66, ~18%)"
    )
    assert len(populated_pairs) < POPULATED_PAIR_COUNT, (
        "Coverage is expected to remain a disclosed partial subset, not full 66-pair coverage."
    )


def test_species_relations_reference_valid_species_and_axes(repo):
    species_ids = set(repo.species.keys())
    axis_ids = set(repo.relationship_axes.keys())

    for rr in repo.species_relations.values():
        assert rr.source_species in species_ids, f"{rr.id}: unknown source_species {rr.source_species!r}"
        assert rr.target_species in species_ids, f"{rr.id}: unknown target_species {rr.target_species!r}"
        for axis_key in rr.axes:
            assert axis_key in axis_ids, f"{rr.id}: unknown axis key {axis_key!r}"


def test_species_relations_no_same_species_entry(repo):
    for rr in repo.species_relations.values():
        assert rr.source_species != rr.target_species, (
            f"{rr.id}: nonsensical same-species entry ({rr.source_species} -> {rr.target_species})"
        )


def test_species_relations_entries_are_bidirectional(repo):
    """Every authored undirected pair has both directions authored, matching
    faction_relationships.yaml's own bidirectional-entry convention."""
    directed_pairs = {(rr.source_species, rr.target_species) for rr in repo.species_relations.values()}
    for source, target in directed_pairs:
        assert (target, source) in directed_pairs, (
            f"Missing reverse-direction entry for {source} -> {target}"
        )

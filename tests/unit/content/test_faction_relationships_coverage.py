"""Coverage/guard tests for data/content/social/faction_relationships.yaml.

TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS / COMB-294: this catalog file is a live input to
FactionSemanticsService.is_hostile_compat() and LegalityServiceV2.verify_attack_legality()
(Friendly Fire law, docs/mechanics/02_combat_laws.md), not inert content. These tests guard the
coverage threshold this ticket established and the specific safety constraint on `neutral`'s entry.
"""
import itertools

import pytest

from src.content.repository import CatalogRepository
from src.core.enums import Faction, EntityRole
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.engine.legality import LegalityServiceV2
from src.content_semantics.faction import reset_faction_semantics_service

# The 12 factions with a live module-population path today (see investigation.md's
# populated-vs-catalog cross-reference). moon_cult, dwarven_mine_clan, dragon_cult, and neutral
# are deliberately excluded from the populated-only denominator (zero module path to population).
POPULATED_FACTIONS = frozenset({
    "town_council", "merchant_league", "wild_beast_pack", "goblin_warband",
    "bandit_company", "forest_wardens", "spirit_court", "orc_clan",
    "undead_remnants", "arcane_circle", "swamp_tribe", "hero_guild",
})

POPULATED_PAIR_COUNT = len(list(itertools.combinations(sorted(POPULATED_FACTIONS), 2)))  # C(12,2) = 66


@pytest.fixture(scope="module")
def repo() -> CatalogRepository:
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture(autouse=True)
def reset_semantics_cache():
    yield
    reset_faction_semantics_service()


def _undirected_pairs(repo: CatalogRepository) -> set[frozenset[str]]:
    return {
        frozenset({rel.source_faction, rel.target_faction})
        for rel in repo.faction_relationships.values()
    }


def test_faction_relationships_coverage_meets_threshold(repo):
    """AC#1, graded against the populated-only 66-pair basis per this ticket's resolved UQ-1."""
    all_pairs = _undirected_pairs(repo)

    populated_pairs = {
        pair for pair in all_pairs
        if pair <= POPULATED_FACTIONS
    }
    assert len(populated_pairs) >= 33, (
        f"Populated-only coverage regressed: {len(populated_pairs)}/{POPULATED_PAIR_COUNT} "
        f"({len(populated_pairs) / POPULATED_PAIR_COUNT:.1%}), need >= 33/66 (50%+)"
    )

    # Raw 120-pair basis reported for visibility only (not gated, per UQ-1 resolution).
    all_factions = {f.id for f in _iter_faction_defs(repo)}
    raw_pair_count = len(list(itertools.combinations(sorted(all_factions), 2)))
    raw_covered = {pair for pair in all_pairs if pair <= all_factions}
    assert len(raw_covered) / raw_pair_count > 0  # sanity: denominator is non-trivial


def _iter_faction_defs(repo: CatalogRepository):
    # CatalogRepository exposes factions as a dict keyed by id; support both attribute names
    # defensively is unnecessary here since the schema is fixed — use the confirmed attribute.
    return repo.factions.values()


def test_neutral_faction_has_explicit_relationship(repo):
    """AC#3 — neutral appears as source_faction or target_faction in at least one entry."""
    involves_neutral = any(
        rel.source_faction == "neutral" or rel.target_faction == "neutral"
        for rel in repo.faction_relationships.values()
    )
    assert involves_neutral


def test_neutral_first_relationship_is_not_high_hostility(repo):
    """Guards the widest-blast-radius mistake: neutral is the universal get_faction_id_str()
    fallback ID, so an elevated hostility value here would affect every entity that fails
    faction resolution, not just one narrow interaction."""
    neutral_entries = [
        rel for rel in repo.faction_relationships.values()
        if rel.source_faction == "neutral" or rel.target_faction == "neutral"
    ]
    assert neutral_entries
    for rel in neutral_entries:
        hostility = rel.axes.get("hostility", "none")
        assert hostility not in ("high", "medium", "medium_contextual", "high_contextual", "low_base_contextual")


def test_new_relationship_entries_reference_valid_axes_and_factions(repo):
    """Fast unit-speed check of what CAT-REL-012 already validates at catalog-load time —
    every entry's factions and axis keys must resolve in their respective catalogs."""
    faction_ids = {f.id for f in _iter_faction_defs(repo)}
    axis_ids = set(repo.relationship_axes.keys())

    for rel in repo.faction_relationships.values():
        assert rel.source_faction in faction_ids, f"{rel.id}: unknown source_faction {rel.source_faction!r}"
        assert rel.target_faction in faction_ids, f"{rel.id}: unknown target_faction {rel.target_faction!r}"
        for axis_key in rel.axes:
            assert axis_key in axis_ids, f"{rel.id}: unknown axis key {axis_key!r}"


def test_new_populated_faction_pairs_prioritized(repo):
    """AC#2 — a majority of all authored pairs involve only the 12-populated set, not the three
    zero-population factions (moon_cult, dwarven_mine_clan, dragon_cult)."""
    all_pairs = _undirected_pairs(repo)
    populated_only = [pair for pair in all_pairs if pair <= POPULATED_FACTIONS]
    assert len(populated_only) > len(all_pairs) / 2


def test_new_pair_changes_legality_friendly_fire_verdict(repo):
    """COMB-294's test_path: a real LegalityServiceV2.verify_attack_legality() outcome, not just
    schema/coverage counts. bandit_company -> orc_clan is a representative non-perspective-source
    pair (data/content/social/faction_relationships.yaml's "bandits_to_orc_clan" entry,
    hostility: high): both factions share legacy_engine_bucket MONSTER_HORDE, so before this
    ticket the only Friendly-Fire signal available (LegalityServiceV2's own raw-enum fallback,
    src/engine/legality.py:260-261) judged them FRIENDLY_FIRE_ILLEGAL (equal legacy buckets).
    The new relationship record flips LegalityServiceV2's gate to True, so it now calls
    is_hostile_compat() instead, which resolves "high" hostility to unconditional "enemy" ->
    the attack is legal. This is only reachable in a non-anchor world today
    (crowded_frontier/frontier_extended/frontier_marches/generated_frontier_3_42), so it is not
    exercised by `make evaluate-full`'s 4 anchor templates — this test is the real coverage."""

    def build_entity(entity_id, faction_id, faction_enum):
        return (
            V2EntityBuilder(entity_id)
            .kind("actor")
            .location(1.0, 1.0)
            .identity(faction=faction_enum, role=EntityRole.MONSTER, properties={"faction_id": faction_id})
            .combat(hp=100, atk=10, def_stat=5, attack_range=1, readiness=100.0)
            .build()
        )

    attacker = build_entity(1, "bandit_company", Faction.MONSTER_HORDE)
    target = build_entity(2, "orc_clan", Faction.MONSTER_HORDE)
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target})

    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)

    assert legal is True

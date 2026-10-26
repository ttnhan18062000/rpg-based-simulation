"""The indexed ``RelationLookup`` returns exactly what the linear scans it replaced returned.

TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP. ``is_hostile_compat`` and
``project_relation`` used to scan the perspective / faction-relationship / species-relation tables
per call. The lookups must be first-match equivalent (including duplicate keys and missing ids), so the
change is behaviour-neutral. The reference functions below are the removed scans, verbatim in logic.
"""
import itertools
from types import SimpleNamespace

import pytest

from src.content.repository import CatalogRepository
from src.content_semantics.faction import FactionSemanticsService
from src.content_semantics.relation import RelationContext, RelationLookup, RelationProjectionService


@pytest.fixture(scope="module")
def repo() -> CatalogRepository:
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def _scan_perspective(repo, perspective_id):
    found = repo.get_perspective(perspective_id)
    if not found:
        for p in repo.perspectives.values():
            if p.chosen_faction == perspective_id:
                found = p
                break
    return found


def _scan_relationship(repo, source, target):
    for rel in repo.faction_relationships.values():
        if rel.source_faction == source and rel.target_faction == target:
            return rel
    return None


def _scan_species(repo, source, target):
    for rr in repo.species_relations.values():
        if rr.source_species == source and rr.target_species == target:
            return rr
    return None


def _scan_has_perspective(repo, source):
    return any(p.chosen_faction == source or p.id == source for p in repo.perspectives.values())


def _scan_perspective_id(repo, source):
    for p in repo.perspectives.values():
        if p.chosen_faction == source:
            return p.id
    return source


def _ids(repo):
    factions = set(repo.factions)
    for p in repo.perspectives.values():
        factions.update((p.id, p.chosen_faction))
    for r in repo.faction_relationships.values():
        factions.update((r.source_faction, r.target_faction))
    return sorted(factions | {"no_such_faction", ""})


def test_lookups_match_scans_over_all_faction_pairs_and_perspectives(repo):
    lookup = RelationLookup(repo)
    ids = _ids(repo)
    assert len(ids) > 5
    for pid in ids:
        assert lookup.perspective_for(pid) is _scan_perspective(repo, pid), pid
        assert lookup.has_perspective(pid) == _scan_has_perspective(repo, pid), pid
        assert lookup.perspective_id_for_faction(pid) == _scan_perspective_id(repo, pid), pid
    for src, tgt in itertools.product(ids, ids):
        assert lookup.relationship(src, tgt) is _scan_relationship(repo, src, tgt), (src, tgt)


def test_species_lookup_matches_scan(repo):
    lookup = RelationLookup(repo)
    species = {r.source_species for r in repo.species_relations.values()}
    species |= {r.target_species for r in repo.species_relations.values()}
    species |= {"no_such_species", ""}
    for a, b in itertools.product(sorted(species), sorted(species)):
        assert lookup.species_relation(a, b) is _scan_species(repo, a, b), (a, b)


def _duplicate_repo(repo):
    """A copy whose tables carry a duplicate key: the FIRST record must win, as in a scan."""
    dup = CatalogRepository.__new__(CatalogRepository)
    dup.__dict__ = dict(repo.__dict__)
    rels = dict(repo.faction_relationships)
    first = next(iter(rels.values()))
    twin = first.model_copy(update={"id": "zz_duplicate_twin", "axes": {"hostility": "none"}})
    rels["zz_duplicate_twin"] = twin
    dup.faction_relationships = rels
    pers = dict(repo.perspectives)
    p0 = next(iter(pers.values()))
    pers["zz_dup_perspective"] = p0.model_copy(update={"id": "zz_dup_perspective"})
    dup.perspectives = pers
    return dup, first, p0


def test_duplicate_keys_resolve_to_the_first_record(repo):
    dup, first, p0 = _duplicate_repo(repo)
    lookup = RelationLookup(dup)
    assert lookup.relationship(first.source_faction, first.target_faction) is first
    assert lookup.perspective_id_for_faction(p0.chosen_faction) == p0.id
    assert lookup.perspective_for(p0.chosen_faction) is _scan_perspective(dup, p0.chosen_faction)


def test_index_follows_a_table_that_grows(repo):
    iso = CatalogRepository.__new__(CatalogRepository)
    iso.__dict__ = dict(repo.__dict__)
    iso.faction_relationships = dict(repo.faction_relationships)
    lookup = RelationLookup(iso)
    assert lookup.relationship("zz_a", "zz_b") is None
    rel = next(iter(repo.faction_relationships.values())).model_copy(
        update={"id": "zz_new", "source_faction": "zz_a", "target_faction": "zz_b"}
    )
    iso.faction_relationships["zz_new"] = rel
    assert lookup.relationship("zz_a", "zz_b") is rel


def test_projection_and_hostility_unchanged_over_all_pairs(repo):
    """Same labels and same hostility as a service rebuilt per call (the old shape), every pair, with
    and without context. A fresh service per call has a fresh lookup, so it stands for the old per-call
    resolution; the shared service must agree with it."""
    shared = FactionSemanticsService(repo)
    ids = _ids(repo)
    contexts = [
        None,
        RelationContext(distance=2.0),
        RelationContext(distance=9.0, intruding=True),
        RelationContext(combat_engaged=True),
        RelationContext(intruding=False, source_species="human", target_species="goblin"),
    ]
    for src, tgt in itertools.product(ids, ids):
        for ctx in contexts:
            fresh = FactionSemanticsService(repo)
            assert shared.is_hostile_compat(src, tgt, ctx) == fresh.is_hostile_compat(src, tgt, ctx), (src, tgt, ctx)
        pid = _scan_perspective_id(repo, src)
        a = shared._projection_service().project_relation(pid, src, tgt, None)
        b = RelationProjectionService(repo).project_relation(pid, src, tgt, None)
        assert a.model_dump() == b.model_dump(), (src, tgt)


def test_service_reuses_one_projection_service(repo):
    svc = FactionSemanticsService(repo)
    assert svc._projection_service() is svc._projection_service()

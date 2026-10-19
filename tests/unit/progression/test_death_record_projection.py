"""The projection that proves recording a death is behaviour-neutral drops exactly the two new fields and nothing else."""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.death_cause import DeathCause, DeathRecord
from src.core.state import AuthoritativeState
from src.engine.checkpoint import CanonicalStateHasher
from tests.helpers.death_field_projection import projected_canonical, projected_digest


def _state(record=None, attacker=None, hp=50):
    ent = V2EntityBuilder(1).location(0.0, 0.0).build()
    ent = replace(ent, combat=replace(ent.combat, last_attacker_id=attacker, hp=hp), lifecycle=replace(ent.lifecycle, death_record=record))
    return AuthoritativeState(tick=5, seed=1, entities={1: ent})


def test_a_recorded_death_and_a_remembered_attacker_change_the_digest_but_not_the_projection():
    plain, marked = _state(), _state(DeathRecord(DeathCause.COMBAT, 5, 7), attacker=7)
    assert CanonicalStateHasher.get_hash(plain) != CanonicalStateHasher.get_hash(marked)
    assert projected_digest(plain) == projected_digest(marked)
    assert projected_canonical(plain) == projected_canonical(marked)


def test_the_projection_still_sees_every_other_difference():
    assert projected_digest(_state(hp=50)) != projected_digest(_state(hp=49))


def test_the_projection_leaves_the_cached_canonical_state_alone():
    marked = _state(DeathRecord(DeathCause.HAZARD, 5, None, "NATURAL_TERRAIN"), attacker=2)
    projected_canonical(marked)
    ent = marked.entities[1]
    assert ent.lifecycle.to_canonical_dict()["death_record"]["cause"] == "HAZARD" and ent.combat.to_canonical_dict()["last_attacker_id"] == 2

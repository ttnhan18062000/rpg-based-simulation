"""TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE (AC #6) — StateFingerprinter must cover
identity.role/identity.faction. Prior to this ticket, StateFingerprinter.get_fingerprint()'s
per-entity string omitted both fields entirely, so a faction/role mutation would be invisible
to replay-parity checks that rely on this (lighter-weight) fingerprint -- the same failure
class PR #128's architecture review caught for a different field. This is distinct from
CanonicalStateHasher (src/engine/checkpoint.py), which already includes faction via
IdentityComponent.to_canonical_dict() and is out of scope here.
"""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.replay.fingerprint import StateFingerprinter


def _entity(eid: int) -> "EntityState":
    return (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(0.0, 0.0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .inventory(gold=0)
        .build()
    )


def test_fingerprint_changes_when_faction_changes():
    ent = _entity(1)
    state = AuthoritativeState(tick=1, seed=1, entities={1: ent})

    new_ident = replace(ent.identity, faction=Faction.NEUTRAL)
    new_ent = replace(ent, identity=new_ident)
    new_state = replace(state, entities={1: new_ent})

    fp_before = StateFingerprinter.get_fingerprint(state)
    fp_after = StateFingerprinter.get_fingerprint(new_state)

    assert fp_before["state_hash"] != fp_after["state_hash"]


def test_fingerprint_changes_when_role_changes():
    ent = _entity(1)
    state = AuthoritativeState(tick=1, seed=1, entities={1: ent})

    new_ident = replace(ent.identity, role=EntityRole.HERO + 1)
    new_ent = replace(ent, identity=new_ident)
    new_state = replace(state, entities={1: new_ent})

    fp_before = StateFingerprinter.get_fingerprint(state)
    fp_after = StateFingerprinter.get_fingerprint(new_state)

    assert fp_before["state_hash"] != fp_after["state_hash"]

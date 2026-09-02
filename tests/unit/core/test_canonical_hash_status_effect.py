"""
TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION

Determinism/canonical-hash coverage guard: confirms CombatComponent.status_effects
and InteractionComponent.kind are both included in EntityState.to_canonical_dict()
output, so a change to either is visible to the world-state hash used for
determinism checks.
"""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import StatusEffectState


def test_status_effects_change_canonical_dict():
    base = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    with_status = replace(base, combat=replace(base.combat,
        status_effects=[StatusEffectState(kind="frozen", source="test_fixture", magnitude=1.0, expires_tick=-1)]))

    assert base.to_canonical_dict() != with_status.to_canonical_dict()
    assert with_status.to_canonical_dict()["combat"]["status_effects"] == [
        {"kind": "frozen", "source": "test_fixture", "magnitude": 1.0, "expires_tick": -1}
    ]
    assert base.to_canonical_dict()["combat"]["status_effects"] == []


def test_interaction_kind_changes_canonical_dict():
    base = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).interaction(target_node_id=101, progress=0).build()
    with_kind = replace(base, interaction=replace(base.interaction, kind="harvest"))

    assert base.to_canonical_dict() != with_kind.to_canonical_dict()
    assert with_kind.to_canonical_dict()["interaction"]["kind"] == "harvest"
    assert base.to_canonical_dict()["interaction"]["kind"] is None

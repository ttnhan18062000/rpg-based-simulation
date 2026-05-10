import pytest
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import ReasonCode, EntityRole, Faction
from src.core.state import AuthoritativeState
from src.core.updates import (
    StateUpdate,
    EntityUpdate,
    TaskUpdate,
    NavigationUpdate,
    ResourceTransferIntent,
)
from src.engine.pipeline import AuthoritativeApplyPipeline


def make_actor(
    entity_id: int,
    *,
    kind: str = "hero",
    faction=Faction.HERO_GUILD,
    role=EntityRole.HERO,
    pos: tuple[float, float] = (0.0, 0.0),
    hp: int = 100,
    max_hp: int = 100,
    atk: int = 10,
    def_stat: int = 5,
    attack_range: int = 1,
    readiness: float = 100.0,
    active: bool = True,
):
    """
    Build a valid actor for rejection-audit tests.

    Important:
        Rejection auditing depends on legality checks, so the actor must be
        fully initialized. Do not rely on partial builder defaults.

    Fraud this catches:
        - hp=0 actor still has combat.alive=True
        - inactive/dead actors accidentally pass GLOBAL_PROPOSAL legality
        - attack rejection fails for the wrong reason because readiness/range
          setup is incomplete
    """
    entity = (
        V2EntityBuilder(entity_id)
        .kind(kind)
        .location(*pos)
        .identity(
            role=role,
            faction=faction,
        )
        .combat(
            hp=hp,
            max_hp=max_hp,
            atk=atk,
            def_stat=def_stat,
            attack_range=attack_range,
            readiness=readiness,
            alive=hp > 0,
        )
        .lifecycle(active=active)
        .build()
    )

    return entity


def test_rejection_audit_aggregation():
    """
    Verify that the authoritative pipeline aggregates rejection events from
    different law layers in a single refined update.

    Scenario:
        1. Entity 1 proposes an ATTACK against a far target.
           Expected rejection: ATTACK / OUT_OF_RANGE.

        2. Entity 3 is dead but proposes movement.
           Expected rejection: GLOBAL_PROPOSAL.

        3. Entity 1 also proposes a HARVEST transfer from a missing NODE.
           Expected rejection: HARVEST / TARGET_INVALID.

    Fraud this catches:
        - global proposal sanitizer rejects invalid actors but does not emit
          RejectionEvent
        - combat legality rejects out-of-range attacks but does not audit them
        - resource transaction resolver rejects invalid sources but does not
          audit them
        - later pipeline stages overwrite earlier rejection_events
    """
    e1 = make_actor(
        1,
        kind="hero",
        faction=Faction.HERO_GUILD,
        role=EntityRole.HERO,
        pos=(0.0, 0.0),
        hp=100,
        attack_range=1,
        readiness=100.0,
    )

    e2 = make_actor(
        2,
        kind="monster",
        faction=Faction.MONSTER_HORDE,
        role=EntityRole.MONSTER,
        pos=(10.0, 10.0),
        hp=100,
        attack_range=1,
        readiness=100.0,
    )

    e3 = make_actor(
        3,
        kind="hero",
        faction=Faction.HERO_GUILD,
        role=EntityRole.HERO,
        pos=(5.0, 5.0),
        hp=0,
        max_hp=100,
        active=True,
    )

    state = AuthoritativeState(
        tick=100,
        seed=42,
        entities={
            1: e1,
            2: e2,
            3: e3,
        },
    )

    # Guard assertions:
    # These prove each rejection path is intentionally reachable.
    assert e1.combat.readiness >= 100.0
    assert e1.combat.range == 1
    assert e1.combat.alive is True
    assert e2.combat.alive is True
    assert e3.combat.alive is False

    e1_attack_update = EntityUpdate(
        entity_id=1,
        task=TaskUpdate(
            work_kind_set="ENTITY_ACT",
            payload_set={
                "action": "ATTACK",
                "target_id": 2,
            },
        ),
    )

    invalid_harvest_intent = ResourceTransferIntent(
        transaction_id="missing-node-harvest",
        source_id=999,
        source_kind="NODE",
        transfer_kind="HARVEST",
    )

    e1_update = replace(
        e1_attack_update,
        resource_transfers=[invalid_harvest_intent],
    )

    e3_update = EntityUpdate(
        entity_id=3,
        navigation=NavigationUpdate(target_set=(6.0, 6.0)),
    )

    raw_update = StateUpdate(
        entity_updates={
            1: e1_update,
            3: e3_update,
        }
    )

    refined_update = AuthoritativeApplyPipeline.refine(state, raw_update)
    events = refined_update.rejection_events

    assert events, "Expected rejection audit events, but none were captured."

    assert any(
        ev.actor_id == 3
        and ev.action_kind == "GLOBAL_PROPOSAL"
        for ev in events
    )

    assert any(
        ev.actor_id == 1
        and ev.action_kind == "ATTACK"
        and ev.reason == ReasonCode.OUT_OF_RANGE
        and ev.target_id == 2
        for ev in events
    )

    assert any(
        ev.actor_id == 1
        and ev.action_kind == "HARVEST"
        and ev.reason == ReasonCode.TARGET_INVALID
        and ev.target_id == "NODE:999"
        for ev in events
    )
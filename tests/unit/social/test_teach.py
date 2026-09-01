# Compliance IDs: SOC-258 (see docs/parity_ledger/social_narrative.yaml)
"""
Unit tests for CoreActions.execute_train() (TCK-20260831-TRUST-GATED-TEACHING).

Mirrors test_team_up.py's style for the closest existing precedent
(CoreActions.execute_team_up()) -- a two-party action that routes a temp
ContractState through SocialAppraisalSystem.appraise_contract() and asserts
on the resulting EntityUpdate bundle. Teaching differs from TEAM_UP in that
the target appraises the teacher's own trustworthiness (not the reverse),
and on acceptance emits IdentityUpdate(recipes_learned=[skill_id]) directly
on the target's EntityUpdate rather than a shared/nested mutation.
"""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, SocialBond
from src.core.strategic import BlockerState
from src.engine.domain.action_router import ActionRouter
from src.engine.domain.core_actions import CoreActions


def _trusting_bond(entity, toward_id, sentiment=0.8):
    return replace(entity, social=replace(entity.social, bonds={toward_id: SocialBond(target_id=toward_id, sentiment=sentiment)}))


def test_teach_action_requires_teacher_and_target():
    teacher = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    student = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    student = _trusting_bond(student, 1, sentiment=0.8)
    state = AuthoritativeState(tick=5, seed=42, entities={1: teacher, 2: student})

    updates = CoreActions.execute_train(
        teacher, {"skill_id": "STRIKE", "target_id": 2}, 5, [], state
    )

    assert 1 in updates
    assert 2 in updates

    # target_id cannot be resolved
    no_target_updates = CoreActions.execute_train(
        teacher, {"skill_id": "STRIKE", "target_id": 999}, 5, [], state
    )
    assert no_target_updates[1].navigation.failure_reason == "TARGET_NOT_FOUND"


def test_teach_refused_below_trust_hard_cancel_threshold():
    teacher = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    student = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    student = _trusting_bond(student, 1, sentiment=-0.9)
    state = AuthoritativeState(tick=5, seed=42, entities={1: teacher, 2: student})

    updates = CoreActions.execute_train(
        teacher, {"skill_id": "STRIKE", "target_id": 2}, 5, [], state
    )

    assert updates[2].identity is None
    assert updates[2].social.rejection_increment == {1: 1}


def test_teach_succeeds_when_trust_clears_emits_direct_identity_update():
    teacher = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    student = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    student = _trusting_bond(student, 1, sentiment=0.8)
    state = AuthoritativeState(tick=5, seed=42, entities={1: teacher, 2: student})

    updates = CoreActions.execute_train(
        teacher, {"skill_id": "STRIKE", "target_id": 2}, 5, [], state
    )

    assert updates[2].identity.recipes_learned == ["STRIKE"]
    assert not updates[2].resource_transfers
    assert not updates[1].resource_transfers


def test_teach_no_gold_leg_regardless_of_gold_balance():
    teacher = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).inventory(gold=0).build()
    student = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).inventory(gold=0).build()
    student = _trusting_bond(student, 1, sentiment=0.8)
    state = AuthoritativeState(tick=5, seed=42, entities={1: teacher, 2: student})

    updates = CoreActions.execute_train(
        teacher, {"skill_id": "STRIKE", "target_id": 2}, 5, [], state
    )

    assert updates[2].identity.recipes_learned == ["STRIKE"]
    assert not updates[1].resource_transfers
    assert not updates[2].resource_transfers


def test_teach_target_appraises_teacher_trust_not_vice_versa():
    teacher = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    student = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()

    # Teacher is hostile toward student, but student trusts teacher -> succeeds
    teacher_hostile = _trusting_bond(teacher, 2, sentiment=-0.9)
    student_trusting = _trusting_bond(student, 1, sentiment=0.8)
    state = AuthoritativeState(tick=5, seed=42, entities={1: teacher_hostile, 2: student_trusting})

    updates = CoreActions.execute_train(
        teacher_hostile, {"skill_id": "STRIKE", "target_id": 2}, 5, [], state
    )
    assert updates[2].identity.recipes_learned == ["STRIKE"]

    # Invert: teacher trusts student, but student distrusts teacher -> fails
    teacher_trusting = _trusting_bond(teacher, 2, sentiment=0.8)
    student_hostile = _trusting_bond(student, 1, sentiment=-0.9)
    state2 = AuthoritativeState(tick=5, seed=42, entities={1: teacher_trusting, 2: student_hostile})

    updates2 = CoreActions.execute_train(
        teacher_trusting, {"skill_id": "STRIKE", "target_id": 2}, 5, [], state2
    )
    assert updates2[2].identity is None


def test_teach_resolves_target_capability_blocker_not_teacher():
    blocker = BlockerState(id="c1", kind="capability", subject="STRIKE")
    teacher = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    student = (
        V2EntityBuilder(2)
        .kind("hero")
        .location(1.0, 0.0)
        .strategic(blockers={"c1": blocker})
        .build()
    )
    student = _trusting_bond(student, 1, sentiment=0.8)
    state = AuthoritativeState(tick=5, seed=42, entities={1: teacher, 2: student})

    updates = CoreActions.execute_train(
        teacher, {"skill_id": "STRIKE", "target_id": 2}, 5, [], state
    )

    assert updates[2].strategic.blockers_remove == ["c1"]


def test_train_action_still_routes_through_action_router():
    teacher = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).combat(readiness=100.0).build()
    student = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    student = _trusting_bond(student, 1, sentiment=0.8)
    state = AuthoritativeState(tick=5, seed=42, entities={1: teacher, 2: student})

    updates = ActionRouter.execute_action(
        teacher,
        payload={"action": "TRAIN", "skill_id": "STRIKE", "target_id": 2},
        current_tick=5,
        neighbor_view=[(2, student)],
        context=state,
    )

    assert updates[2].identity.recipes_learned == ["STRIKE"]

"""
tests/integration/domains/test_combat_risk_belief_end_to_end.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN — Acceptance Criterion #4.

"HelpNeedEvaluator.evaluate()'s combat-support-need logic is verified to actually fire in a real
simulation run at least once, not just in hand-constructed unit tests."

This drives the REAL AuthoritativeApplyPipeline.refine() + ApplyPath.apply_generation() loop over
multiple ticks with both gating flags ON, so:

  tick N   : combat_engagement phase writes the combat_risk BeliefEntry (real producer)
  apply    : merge_dict() lands it at entity.strategic.beliefs["combat_risk"] (real apply path)
  tick N+1 : cooperation phase reads it back (real consumer)

The multi-tick span is load-bearing, not incidental: in src/engine/pipeline.py the `cooperation`
phase runs BEFORE `combat_engagement` within a single refine() pass, so a belief written this tick
is only visible to the consumer on the following tick. A single-tick test would pass vacuously.
"""

import pytest
from dataclasses import replace as dataclass_replace

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import (
    AuthoritativeState, CombatComponent, BiologicalComponent, PersonalityComponent
)
from src.core.strategic import (
    RiskLevel, ProjectState, ProjectKind, ObjectiveState, ObjectiveKind
)
from src.core.updates import StateUpdate
from src.domains.optimization.feature_flags import FeatureMode
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.domains.cooperation.evaluators import HelpNeedEvaluator
from src.systems.strategic_systems.belief import BeliefEntry


def _combatant(ent_id: int, x: float, y: float, hp: int, atk: int, faction: Faction = None):
    b = V2EntityBuilder(ent_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=100, atk=atk, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(
        evolution_level=1,
        personality=PersonalityComponent(
            greed=0.5, bravery=0.5, sociability=0.5, industry=0.5
        ),
        faction=faction,
    )
    b.location(x, y)
    b.lifecycle(active=True)
    entity = b.build()

    # Give the actor a real active combat objective, which HelpNeedEvaluator requires before
    # it will emit any need at all (it early-returns on no current_objective_id).
    obj = ObjectiveState(id=f"obj_{ent_id}", kind=ObjectiveKind.DEFEAT_ENEMY)
    proj = ProjectState(
        id=f"proj_{ent_id}",
        kind=ProjectKind.COMBAT,
        objectives=[obj],
        active_objective_id=f"obj_{ent_id}",
    )
    entity.strategic.projects[f"proj_{ent_id}"] = proj
    object.__setattr__(entity.strategic, "current_project_id", f"proj_{ent_id}")
    object.__setattr__(entity.strategic, "current_objective_id", f"obj_{ent_id}")
    return entity


def _state_with_flags(entities, tick: int = 1) -> AuthoritativeState:
    state = AuthoritativeState(
        entities={e.id: e for e in entities}, tick=tick, seed=42
    )
    return dataclass_replace(state, feature_flags={
        "ENABLE_COMBAT_ENGAGEMENT": FeatureMode.ON,
        "ENABLE_SOCIAL_COOPERATION": FeatureMode.ON,
    })


def test_combat_risk_belief_is_produced_and_consumed_across_real_ticks():
    """
    Full real-pipeline round trip: a badly outmatched actor next to a much stronger hostile must
    end up with a real combat_risk BeliefEntry in durable state, which the real
    HelpNeedEvaluator then turns into a combat_support_needed HelpNeed.
    """
    # Weak actor beside a far stronger hostile -> low power_ratio -> high death_risk.
    weak = _combatant(1, 0.0, 0.0, hp=25, atk=2, faction=Faction.HERO_GUILD)
    strong = _combatant(2, 1.0, 1.0, hp=100, atk=40, faction=Faction.MONSTER_HORDE)
    state = _state_with_flags([weak, strong])

    produced_level = None

    # Drive several real ticks through the actual pipeline + apply path.
    for _ in range(3):
        refined = AuthoritativeApplyPipeline.refine(state, StateUpdate())
        state = ApplyPath.apply_generation(state, refined, next_tick=state.tick + 1)

        belief = state.entities[1].strategic.beliefs.get("combat_risk")
        if belief is not None and produced_level is None:
            produced_level = belief.claim

    # 1. The real producer ran inside the real pipeline.
    stored = state.entities[1].strategic.beliefs.get("combat_risk")
    assert stored is not None, (
        "combat_engagement phase must write a real combat_risk belief during a real tick"
    )
    assert isinstance(stored, BeliefEntry), "must be a real BeliefEntry, not a bespoke dict"
    assert stored.claim in {lvl.value for lvl in RiskLevel}
    assert stored.subject == "combat_risk"
    # Outmatched actor: death_risk should be meaningful, not a floor value.
    assert stored.certainty > 0.0

    # A 25hp/atk-2 actor beside a 100hp/atk-40 hostile is decisively outmatched, so the produced
    # level must be HIGH or EXTREME. Asserted directly rather than guarded behind an `if`, so this
    # test cannot silently pass vacuously if the mapping or risk formula ever drifts.
    assert RiskLevel(stored.claim) in (RiskLevel.HIGH, RiskLevel.EXTREME), (
        f"badly outmatched actor should perceive HIGH/EXTREME risk, got {stored.claim}"
    )

    # 2. The real consumer reads that same durable belief back and acts on it.
    needs = HelpNeedEvaluator.evaluate(state.entities[1], state)
    assert any(n.key == "combat_support_needed" for n in needs), (
        "HelpNeedEvaluator must raise combat_support_needed from the pipeline-produced belief"
    )


def test_isolated_entity_gets_low_risk_combat_belief_in_a_real_run():
    """
    TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN (correction, 2026-09-08): no nearby hostile
    now yields a real, current LOW-risk belief (not an absent one) through the real authoritative
    apply path -- restoring the "current assessment, replaced every tick" invariant this module
    documents, which the hostility filter would otherwise leave permanently stale.
    """
    lone = _combatant(1, 0.0, 0.0, hp=100, atk=10)
    faraway = _combatant(2, 400.0, 400.0, hp=100, atk=10)
    state = _state_with_flags([lone, faraway])

    for _ in range(3):
        refined = AuthoritativeApplyPipeline.refine(state, StateUpdate())
        state = ApplyPath.apply_generation(state, refined, next_tick=state.tick + 1)

    belief = state.entities[1].strategic.beliefs.get("combat_risk")
    assert belief is not None
    assert belief.claim == "LOW"

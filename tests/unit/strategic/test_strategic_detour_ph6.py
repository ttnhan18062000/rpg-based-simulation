import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState
from src.core.strategic import (
    ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus,
    BlockerState, LeadState, LeadCertainty
)
from src.systems.strategic import StrategicIntelligenceSystem
from src.core.updates import StateUpdate

def create_mock_entity(eid: int):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(eid)
        .kind("hero")
        .location(0, 0)
        .identity(class_id="hero")
        .combat(hp=100, max_hp=100, atk=10, def_stat=5, alive=True)
        .inventory(gold=10)
        .build()
    )

def test_strategic_detour_creation_and_resumption():
    # Existing project (harvesting)
    harvest_proj = ProjectState(
        id="proj_harvest",
        kind="harvesting",
        status=ProjectStatus.ACTIVE,
        score=40.0
    )
    
    # Blocker for wood
    blocker = BlockerState(id="blocker_mat_wood", kind="material", subject="wood")
    
    # Lead for wood
    lead = LeadState(
        id="lead_wood",
        kind="location",
        subject="wood",
        detail="(10.0, 10.0)",
        certainty=LeadCertainty.PRECISE
    )
    
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .identity(class_id="hero")
        .strategic(
            projects={"proj_harvest": harvest_proj},
            blockers={"blocker_mat_wood": blocker},
            leads={"lead_wood": lead},
            current_project_id="proj_harvest"
        )
        .build())
    
    state = AuthoritativeState(tick=100, seed=42)
    
    # 2. evaluate_strategic_intent should suggest a detour
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    
    assert update.current_project_id_set is not None
    assert "proj_detour" in update.current_project_id_set
    
    # Verify harvest project is suspended
    harvest_up = next((p for p in update.projects_add_or_update if p.id == "proj_harvest"), None)
    assert harvest_up is not None
    assert harvest_up.status == ProjectStatus.SUSPENDED
    
    # 3. Simulate Detour Completion
    # We'll create a new state where the detour is completed
    detour_proj = next((p for p in update.projects_add_or_update if p.kind == "detour"), None)
    detour_obj = replace(detour_proj.objectives[0], status=ObjectiveStatus.RESOLVED)
    detour_proj = replace(detour_proj, status=ProjectStatus.COMPLETED, objectives=[detour_obj])
    
    entity = replace(entity, strategic=replace(entity.strategic,
        projects={
            "proj_harvest": harvest_up,
            detour_proj.id: detour_proj
        },
        current_project_id=detour_proj.id
    ))
    
    # 4. evaluate_strategic_intent should resume harvest project
    update_resume = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    
    assert update_resume.current_project_id_set == "proj_harvest"
    harvest_resumed = next((p for p in update_resume.projects_add_or_update if p.id == "proj_harvest"), None)
    assert harvest_resumed.status == ProjectStatus.ACTIVE
    
    # Verify blocker is marked as resolved (Phase 6 rule)
    resolved_blocker = next((b for b in update_resume.blockers_add_or_update if b.id == "blocker_mat_wood"), None)
    assert resolved_blocker.resolved == True


def test_resolve_blocker_project_timeout_abandons_and_suppresses_blocker():
    """TCK-20260817-STANDARD-HUNGER-STARVED-BY-RESOLVE-BLOCKER-FLAT-UTILITY: a resolve_blocker
    project has no completion condition (unlike hunger/fatigue/harvesting), so a blocker that can
    never actually be reached (e.g. a non-coordinate 'access' blocker) would keep the project
    ACTIVE forever, permanently starving every other need. Past the 50-tick window (matching this
    project kind's own creation-time lock_until_tick ceiling), it must abandon and suppress the
    specific blocker it failed to resolve, not just any blocker."""
    blocker = BlockerState(id="blocker_access_1", kind="access", subject="(unparseable)")

    resolve_proj = ProjectState(
        id="proj_resolve_blocker_1",
        kind="resolve_blocker",
        status=ProjectStatus.ACTIVE,
        objectives=[ObjectiveState(
            id="reach_location_blocker_access_1",
            kind="reach_location",
            target="blocker_access_1",
            status=ObjectiveStatus.ACTIVE,
        )],
        active_objective_id="reach_location_blocker_access_1",
        created_tick=0,
        score=80.0,
    )

    entity = create_mock_entity(2)
    entity = replace(entity, strategic=replace(
        entity.strategic,
        projects={"proj_resolve_blocker_1": resolve_proj},
        blockers={"blocker_access_1": blocker},
        current_project_id="proj_resolve_blocker_1",
    ))

    state = AuthoritativeState(tick=60, seed=42)  # 60 - 0 >= 50 -> timed out

    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert update.current_project_id_set == ""
    abandoned = next((p for p in update.projects_add_or_update if p.id == "proj_resolve_blocker_1"), None)
    assert abandoned is not None
    assert abandoned.status == ProjectStatus.ABANDONED

    suppressed_blocker = next((b for b in update.blockers_add_or_update if b.id == "blocker_access_1"), None)
    assert suppressed_blocker is not None
    assert suppressed_blocker.resolved is False  # not resolved -- still real, just deprioritized
    assert suppressed_blocker.suppression_until_tick == 160  # current_tick(60) + 100


def test_resolve_blocker_scorer_skips_suppressed_blocker():
    """ResolveBlockerScorer must not keep re-bidding a flat, un-decaying utility for a blocker a
    timed-out resolve_blocker project already failed to resolve, or the abandon-then-immediately-
    re-win cycle would never actually let another need win."""
    from src.ai.goals.scorers import ResolveBlockerScorer
    from src.core.strategic import GoalKind

    blocker = BlockerState(id="blocker_access_1", kind="access", subject="(1.0, 2.0)")
    entity = create_mock_entity(3)
    state = AuthoritativeState(tick=100, seed=42)

    # Not suppressed -- scores normally.
    active_entity = replace(entity, strategic=replace(entity.strategic, blockers={"blocker_access_1": blocker}))
    score = ResolveBlockerScorer().score(active_entity, state)
    assert score.kind == GoalKind.RESOLVE_BLOCKER
    assert score.utility == 80.0

    # Suppressed until a tick beyond the current one -- scores 0.0 (no active blockers to bid on).
    suppressed_blocker = replace(blocker, suppression_until_tick=150)
    suppressed_entity = replace(entity, strategic=replace(entity.strategic, blockers={"blocker_access_1": suppressed_blocker}))
    score = ResolveBlockerScorer().score(suppressed_entity, state)
    assert score.utility == 0.0

    # Suppression window has elapsed -- scores normally again.
    expired_blocker = replace(blocker, suppression_until_tick=100)
    expired_entity = replace(entity, strategic=replace(entity.strategic, blockers={"blocker_access_1": expired_blocker}))
    score = ResolveBlockerScorer().score(expired_entity, state)
    assert score.utility == 80.0

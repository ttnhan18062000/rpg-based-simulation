import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, CombatComponent, InventoryComponent, SocialComponent, IdentityComponent, BiologicalComponent, LifecycleComponent, StrategicComponent, IntentResult
from src.core.strategic import LeadState, LeadCertainty, ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus
from src.systems.strategic import StrategicIntelligenceSystem
from src.systems.strategic_systems.intelligence import _MAX_CONSECUTIVE_REJECTIONS
from src.core.enums import EntityRole, Faction
from src.core.builder import V2EntityBuilder
from src.engine.apply import replace as fast_replace

def create_mock_entity(eid: int):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(eid)
        .kind("hero")
        .location(0, 0)
        .lifecycle(active=True)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, atk=10, def_stat=5)
        .inventory(gold=10)
        .build())

def test_lead_failure_suppression():
    # Lead that just failed
    lead = LeadState(id="l1", kind="location", subject="forest", tested=True, test_outcome="FAILURE")
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .lifecycle(active=True)
        .strategic(leads={lead.id: lead})
        .build())
    
    state = AuthoritativeState(tick=100, seed=42)
    
    # Run evaluation
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    
    # Should contain suppression update
    assert len(update.leads_add_or_update) > 0
    updated_lead = update.leads_add_or_update[0]
    assert updated_lead.failure_count == 1
    assert updated_lead.suppression_until_tick == 100 + 500

def test_lead_exhaustion():
    # Lead that failed 2 times already
    lead = LeadState(id="l1", kind="location", subject="forest", tested=True, test_outcome="FAILURE", failure_count=2)
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .lifecycle(active=True)
        .strategic(leads={lead.id: lead})
        .build())
    
    state = AuthoritativeState(tick=100, seed=42)
    
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    
    # Should be EXHAUSTED after 3rd failure
    assert len(update.leads_add_or_update) > 0
    updated_lead = update.leads_add_or_update[0]
    assert updated_lead.failure_count == 3
    assert updated_lead.certainty == LeadCertainty.EXHAUSTED

def test_project_abandonment():
    """
    Verify that the currently active project is abandoned after repeated failure.

    Logic under test:
        StrategicIntelligenceSystem only evaluates abandonment for
        `entity.strategic.current_project_id`.

        A project merely existing in `strategic.projects` is not enough.
        It must be the active/current project.

        The abandonment threshold is _MAX_CONSECUTIVE_REJECTIONS (currently 20).
        Abandonment is only triggered when latest_intent_results contains at least
        one failure and the cumulative failure_count reaches the threshold.

    Fraud this catches:
        - abandoned-project logic exists but only scans all projects incorrectly
        - failed projects are ignored even when they are current
        - boredom/frustration penalty is not emitted when abandonment happens
        - test accidentally inserts a failed project but forgets to make it current
    """
    # Set failure_count one below threshold so one more rejection triggers abandonment.
    proj = ProjectState(
        id="p1",
        kind="quest",
        status=ProjectStatus.ACTIVE,
        failure_count=_MAX_CONSECUTIVE_REJECTIONS - 1,
    )

    base_entity = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .lifecycle(active=True)
        .strategic(
            projects={proj.id: proj},
            current_project_id=proj.id,
        )
        .build()
    )

    # Inject a rejected intent result so the backoff counter increments.
    rejected = IntentResult(
        transaction_id=None, accepted=False, reason="INTERACTION_RESET",
        source_kind="NODE", source_id=1,
    )
    new_id = fast_replace(base_entity.identity, latest_intent_results=(rejected,))
    entity = fast_replace(base_entity, identity=new_id)

    state = AuthoritativeState(tick=100, seed=42)

    # Guard assertions:
    # These prove the setup reaches the exact branch this test wants to verify.
    assert entity.strategic.current_project_id == "p1"
    assert entity.strategic.projects["p1"].status == ProjectStatus.ACTIVE
    assert entity.strategic.projects["p1"].failure_count >= _MAX_CONSECUTIVE_REJECTIONS - 1
    assert any(not r.accepted for r in entity.identity.latest_intent_results)

    update = StrategicIntelligenceSystem.evaluate_strategic_intent(
        state,
        entity,
        force=True,
    )

    assert len(update.projects_add_or_update) > 0

    abandoned_proj = next(
        p for p in update.projects_add_or_update
        if p.id == "p1"
    )

    assert abandoned_proj.status == ProjectStatus.ABANDONED

    # 0.1 = normal active-project boredom
    # 0.5 = frustration penalty for abandonment
    assert update.boredom_delta["quest"] == 0.6

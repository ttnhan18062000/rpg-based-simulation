import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import EntityState, RegionState, AuthoritativeState
from src.core.strategic import StrategicComponent
from src.core.updates import StateUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.systems.routine import RoutineService

def test_anchored_world_generates_return_home_concern_directly():
    """
    Direct law test for anchored-world behavior.

    Purpose:
        Prove that the low-level anchored-world rule itself works:
        an entity with `strategic.home_region_id` should generate a
        `concern_return_home` concern when it is outside its home region,
        idle, and the home region exists.

    Why this test exists:
        This test prevents a false pipeline pass/fail from hiding the real
        source of the bug. If this test fails, the issue is in one of:

        - V2EntityBuilder.strategic(home_region_id=...)
        - StrategicComponent.home_region_id storage
        - RoutineService.evaluate_anchored_behavior(...)
        - region bounds / position logic

        It does NOT test the authoritative pipeline.
    """
    home = RegionState(id="home", name="Home", bounds=(0, 0, 2, 2))
    away = RegionState(id="away", name="Away", bounds=(10, 10, 12, 12))

    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(11.0, 11.0)
        .strategic(home_region_id="home")
        .build()
    )

    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"home": home, "away": away},
        entities={1: hero},
    )

    # Guard assertions:
    # These prove the test setup is valid before checking anchored behavior.
    # If any of these fail, the test is invalid and should not blame
    # RoutineService.
    assert hero.strategic.home_region_id == "home"
    assert hero.strategic.current_project_id is None
    assert hero.navigation.position == (11.0, 11.0)
    assert "home" in state.regions

    # This call isolates the anchored-world rule from the full pipeline.
    # It is the fraud-detection point: the service must produce the concern
    # directly, not only appear to work through some unrelated pipeline effect.
    concerns = RoutineService.evaluate_anchored_behavior(hero, state)

    assert any(c.id == "concern_return_home" for c in concerns)


def test_anchored_world_persistence_pipeline_integration():
    """
    Pipeline integration test for anchored-world behavior.

    Purpose:
        Prove that anchored-world behavior is wired into the authoritative
        refinement pipeline, not only implemented as unused RoutineService logic.

    Important:
        The current strategic concern intake is cadence-gated:

            (state.tick + entity_id) % 10 == 0

        Therefore this test deliberately uses tick=99 for entity_id=1 so the
        anchored concern path is eligible to run.

    Fraud this test catches:
        - RoutineService.evaluate_anchored_behavior exists but is not called
          by the real pipeline
        - strategic concern intake drops anchored concerns
        - pipeline produces readiness updates but no StrategicUpdate
        - test accidentally runs on a non-concern-evaluation tick
    """
    home = RegionState(
        id="home",
        name="Home",
        bounds=(0, 0, 2, 2),
    )
    away = RegionState(
        id="away",
        name="Away",
        bounds=(10, 10, 12, 12),
    )

    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(11.0, 11.0)
        .combat(
            hp=100,
            max_hp=100,
            alive=True,
            readiness=100.0,
        )
        .lifecycle(active=True)
        .strategic(home_region_id="home")
        .build()
    )

    state = AuthoritativeState(
        tick=99,  # entity_id=1 -> (99 + 1) % 10 == 0
        seed=42,
        regions={
            "home": home,
            "away": away,
        },
        entities={
            1: hero,
        },
    )

    # Guard assertions:
    # These prove the test setup reaches the anchored-concern branch.
    assert (state.tick + hero.id) % 10 == 0
    assert hero.lifecycle.active is True
    assert hero.combat.alive is True
    assert hero.strategic.home_region_id == "home"
    assert hero.strategic.current_project_id is None
    assert hero.navigation.position == (11.0, 11.0)
    assert "home" in state.regions

    update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, update)

    ent_upd = refined.entity_updates[1]

    assert ent_upd.strategic is not None
    assert any(
        c.id == "concern_return_home"
        for c in ent_upd.strategic.concerns_add_or_update
    )
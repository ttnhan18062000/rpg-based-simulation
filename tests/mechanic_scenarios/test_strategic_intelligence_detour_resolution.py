"""Runtime-evidence program, batch 2 (TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION).
Covers the shared `strategic_intelligence` phase, one independent observation per peer review (not
4 -- `goal_hierarchy`, `strategic_intelligence_core`, `strategic_learning_bias`, and `concern_intake`
all live in or under this one phase; confirming it runs doesn't independently confirm each of their
own separate branches, see this file's own scope note below).

`StrategicIntelligenceSystem.fused_strategic_pass()` (`strategic_intelligence_core`'s own binding)
is called unconditionally every tick (`src/engine/pipeline.py:398`, no feature-flag argument) --
reachable in the sense that matters for §5 item 4's backing rule (nothing gates the phase itself
off). Its own PER-ENTITY cadence for re-evaluating strategic intents is a separate, real number:
`src/engine/pipeline.py:53`'s `DefaultCadence(strategic_intelligence=1)` override only applies when
`refine()` receives no cadence at all, and a live `Kernel` run does supply one --
`cadence.strategic_intelligence=20` under `PROD_SMALL` (confirmed by direct instrumentation, not
assumed from the pipeline.py read alone; see `_stage_detour_project`'s own note below). This scenario targets
`StrategicIntelligenceSystem._resolve_active_objective()` -- one of `goal_hierarchy`'s own 5 bound
methods -- via its one real, narrow branch: a `"detour"`-kind project's `reach_location` objective
resolves once the entity is within 1.0 distance of the objective's `target_position`
(`intelligence.py:1199-1238`).

Differential design: same staged detour project on the same entity, same real `Kernel.tick_once()`
dispatch, only `entity.navigation.position` differs --
- "mechanism present" (within resolution distance): the objective resolves, the project completes,
  `current_project_id` clears.
- "mechanism absent" (outside resolution distance): nothing changes.

**Scope note, honest per peer review**: this scenario exercises `_resolve_active_objective()`
specifically (`goal_hierarchy`) and confirms `fused_strategic_pass()` itself really dispatches
(`strategic_intelligence_core`). It does NOT exercise `ConcernIntakeSystem.evaluate_salience()`
(`concern_intake`, gated behind its own `has_hostiles_or_dead or hunger > 60.0` precondition plus a
separate cadence-10 check not overridden to 1) or `StrategicLearningService.get_goal_biases()`
(`strategic_learning_bias`, needs real `turning_points` history) -- those need their own staging and
are not claimed as verified by this scenario.
"""
import os
from dataclasses import replace

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.core.strategic import ProjectState, ObjectiveState, ProjectStatus, ObjectiveStatus, ObjectiveKind

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
GOBLIN_ID = 1
PROJECT_ID = "detour_scenario"
OBJECTIVE_ID = "obj_reach_scenario"
TARGET_POSITION = (5.0, 5.0)
SEED = 42


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _stage_detour_project(state, *, goblin_position):
    """Stages a real ACTIVE 'detour' project with one ACTIVE reach_location objective -- the exact
    shape `_resolve_active_objective()` itself checks for (`intelligence.py:1213`). `kind="detour"`
    is a real, production string this codebase's own DetourSuggestionSystem constructs elsewhere
    (confirmed: ProjectKind's own enum deliberately has no DETOUR member, per
    `evaluate_project_switch`'s own docstring -- "detour" is the one unconditional structural
    bypass kind, checked as a plain string) -- not an invented value.

    `state.tick` is set to 19 (not the compiled default of 0): the real `cadence.strategic_intelligence`
    used by a live `Kernel` run is 20 (`PhaseBudgetGovernor.evaluate()` under `PROD_SMALL`), not the
    `DefaultCadence(strategic_intelligence=1)` override `src/engine/pipeline.py:53` applies only when
    no cadence is otherwise supplied -- confirmed by direct instrumentation, not assumed. Per-entity
    cadence gating is `(tick + entity_id) % 20 == 0`; for `GOBLIN_ID=1` that's tick 19. Starting there
    means the phase's own cadence-gated re-evaluation fires on the very first real tick, before the
    goblin's own real combat/movement logic (which independently repositions it every tick, chasing
    the orc) has a chance to drift it away from the staged target position -- confirmed directly: a
    multi-tick run from tick 0 lets the entity drift 2+ tiles off target before its first
    cadence-aligned evaluation even happens, which would make the "present" condition fail for a
    reason unrelated to the resolution logic itself (drift, not gate correctness)."""
    object.__setattr__(state, "tick", 19)
    goblin = state.entities[GOBLIN_ID]

    objective = ObjectiveState(
        id=OBJECTIVE_ID,
        kind=ObjectiveKind.REACH_LOCATION,
        target_position=TARGET_POSITION,
        status=ObjectiveStatus.ACTIVE,
    )
    project = ProjectState(
        id=PROJECT_ID,
        kind="detour",
        status=ProjectStatus.ACTIVE,
        objectives=[objective],
        active_objective_id=OBJECTIVE_ID,
    )
    goblin = replace(
        goblin,
        navigation=replace(goblin.navigation, position=goblin_position),
        strategic=replace(goblin.strategic, current_project_id=PROJECT_ID, projects={PROJECT_ID: project}),
    )

    new_entities = dict(state.entities)
    new_entities[GOBLIN_ID] = goblin
    object.__setattr__(state, "entities", new_entities)
    return state


def _run_one_tick_and_get_project(state):
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
        final_state = kernel._state
    finally:
        kernel.shutdown()

    goblin = final_state.entities[GOBLIN_ID]
    return goblin.strategic.current_project_id, goblin.strategic.projects.get(PROJECT_ID)


def test_detour_objective_resolves_when_entity_reaches_the_target_position():
    """Mechanism present: the goblin is already at the objective's own target_position (distance
    0.0 < 1.0). `_resolve_active_objective()` must resolve the objective and complete the project
    through a real Kernel dispatch of the real, unconditional strategic_intelligence phase."""
    state = _compile_world()
    state = _stage_detour_project(state, goblin_position=TARGET_POSITION)

    current_project_id, project = _run_one_tick_and_get_project(state)

    assert current_project_id == "", (
        "strategic_intelligence_core/goal_hierarchy mechanic: expected current_project_id to clear "
        f"once the detour objective resolves, but got {current_project_id!r}."
    )
    assert project is not None and project.status == ProjectStatus.COMPLETED, (
        "strategic_intelligence_core/goal_hierarchy mechanic: expected the detour project to reach "
        f"COMPLETED once the entity reached the objective's target position, but got {project!r}."
    )


def test_detour_objective_does_not_resolve_when_entity_is_far_from_the_target_position():
    """Mechanism absent: the goblin is far from the objective's target_position (distance >= 1.0).
    The differential half -- without this passing too, the first test could pass for a reason
    unrelated to the distance check (e.g. every detour project completing regardless of position),
    and the scenario would not actually be testing the resolution logic specifically."""
    state = _compile_world()
    state = _stage_detour_project(state, goblin_position=(0.0, 0.0))

    current_project_id, project = _run_one_tick_and_get_project(state)

    assert current_project_id == PROJECT_ID, (
        "strategic_intelligence_core/goal_hierarchy mechanic: expected current_project_id to stay "
        f"{PROJECT_ID!r} when the entity is far from the target position, but got "
        f"{current_project_id!r}."
    )
    assert project is not None and project.status == ProjectStatus.ACTIVE, (
        "strategic_intelligence_core/goal_hierarchy mechanic: expected the detour project to stay "
        f"ACTIVE when the entity has not reached the target position, but got {project!r}."
    )

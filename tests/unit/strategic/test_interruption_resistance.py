"""
Contract tests for Strategic Cognition: Interruption Resistance & Project Switching.

Covers:
- Part 1 §Strategic: Project switching uses interruption resistance / margin logic
- Part 1 §Strategic: Current project gets reservation/retention priority
- RPG-0040: project_objective_continuity
- RPG-0041: project_interruption_resistance
- RPG-0042: current_project_retention
"""
import pytest
from src.core.state import AuthoritativeState, CombatComponent, EntityState
from src.core.strategic import (
    StrategicComponent, CognitionProfile, ProjectState, ProjectStatus,
    ObjectiveState, ObjectiveStatus
)
from src.systems.strategic import StrategicIntelligenceSystem


def _make_state(entities: list, tick: int = 5) -> AuthoritativeState:
    """Minimal AuthoritativeState fixture, mirroring
    tests/unit/systems/test_spawn_lock_condition.py's own _make_state() shape."""
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=tick,
        seed=42,
        world_time=100,
        entities=ent_map,
        groups={},
        regions={},
        resource_nodes={},
        buildings={},
        chests={},
        ground_items={},
        corpses={},
        camps={},
        local_scars={},
        global_resources={},
        town_tiles=(),
        building_tiles=(),
        terrain=(),
        home_storage={},
        town_center=(0.0, 0.0),
        periodic_due_ticks={},
        work_debt={},
        movement_count=0,
        maturity=0,
        last_calamity_tick=0,
        blocked_tiles=(),
        town_entity_ids=(),
    )


def _make_entity(profile=None, current_project=None):
    """Helper to build a minimal entity for testing."""
    from src.core.builder import V2EntityBuilder
    projects = {current_project.id: current_project} if current_project else {}
    current_id = current_project.id if current_project else None
    
    builder = (V2EntityBuilder(1)
        .kind("hero")
        .location(5.0, 5.0)
        .strategic(projects=projects))
    
    if current_id:
        builder.strategic(current_project_id=current_id)
        
    if profile:
        builder.cognition(
            interruption_resistance=profile.interruption_resistance
        )
        
    return builder.build()


class TestInterruptionResistance:
    """Part 1 §Strategic: Project switching uses margin logic."""

    def test_switch_when_no_current_project(self):
        """Always switch if there's no current project."""
        entity = _make_entity()
        candidate = ProjectState(id="new_proj", kind="crafting", status=ProjectStatus.ACTIVE, score=30)
        result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=10)
        assert result is not None
        assert result.current_project_id_set == "new_proj"

    def test_retention_when_candidate_below_margin(self):
        """Current project retained when candidate doesn't exceed margin."""
        current = ProjectState(id="current", kind="crafting", status=ProjectStatus.ACTIVE, score=50)
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.5),
            current_project=current
        )
        # Candidate score 55 vs current 50 + (0.5 * 30) = 65 → candidate loses
        candidate = ProjectState(id="rival", kind="quest", status=ProjectStatus.ACTIVE, score=55)
        result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=10)
        assert result is None  # No switch

    def test_switch_when_candidate_exceeds_margin(self):
        """Switch when candidate clearly outscores current + retention bonus."""
        current = ProjectState(id="current", kind="crafting", status=ProjectStatus.ACTIVE, score=50)
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.3),
            current_project=current
        )
        # Candidate score 80 vs current 50 + (0.3 * 30) = 59 → candidate wins
        candidate = ProjectState(id="urgent", kind="combat", status=ProjectStatus.ACTIVE, score=80)
        result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=10)
        assert result is not None
        assert result.current_project_id_set == "urgent"
        # Verify current was suspended
        suspended = [p for p in result.projects_add_or_update if p.id == "current"]
        assert len(suspended) == 1
        assert suspended[0].status == ProjectStatus.SUSPENDED

    def test_higher_resistance_prevents_more_switches(self):
        """Higher resistance → harder to switch."""
        current = ProjectState(id="current", kind="crafting", status=ProjectStatus.ACTIVE, score=50)
        candidate = ProjectState(id="rival", kind="quest", status=ProjectStatus.ACTIVE, score=65)

        # Low resistance: switch happens
        entity_low = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.2),
            current_project=current
        )
        result_low = StrategicIntelligenceSystem.evaluate_project_switch(entity_low, candidate, current_tick=10)
        assert result_low is not None

        # High resistance: switch blocked
        entity_high = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.8),
            current_project=current
        )
        result_high = StrategicIntelligenceSystem.evaluate_project_switch(entity_high, candidate, current_tick=10)
        assert result_high is None

    def test_lock_prevents_switch(self):
        """Project lock blocks a switch when the candidate doesn't clear the urgency floor,
        but no longer blocks unconditionally: a candidate whose normalized score clears both
        the current project's normalized effective score and the urgency floor now bypasses
        the lock, regardless of kind (generalized STRAT-186 rule)."""
        current = ProjectState(
            id="locked", kind="crafting", status=ProjectStatus.ACTIVE,
            score=10, lock_until_tick=100
        )
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.0),
            current_project=current
        )
        # score=50 -> candidate_pct=0.5, below the 0.8 urgency floor -> still blocked.
        low_urgency_candidate = ProjectState(id="rival", kind="quest", status=ProjectStatus.ACTIVE, score=50)
        result = StrategicIntelligenceSystem.evaluate_project_switch(entity, low_urgency_candidate, current_tick=50)
        assert result is None  # Locked until tick 100, floor not cleared

        # score=999 -> candidate_pct=9.99, clears both the floor and current's normalized
        # effective score -> the generalized rule now bypasses the lock (intentional loosening).
        high_urgency_candidate = ProjectState(id="rival", kind="quest", status=ProjectStatus.ACTIVE, score=999)
        result_bypass = StrategicIntelligenceSystem.evaluate_project_switch(entity, high_urgency_candidate, current_tick=50)
        assert result_bypass is not None
        assert result_bypass.current_project_id_set == "rival"

    def test_interruption_resistance_resume_suspended(self):
        """Verify a suspended project can be resumed."""
        from src.core.builder import V2EntityBuilder
        suspended = ProjectState(
            id="old_quest", kind="quest", status=ProjectStatus.SUSPENDED,
            score=40, active_objective_id="obj_1"
        )
        entity = (V2EntityBuilder(1)
            .kind("hero")
            .location(5.0, 5.0)
            .strategic(projects={"old_quest": suspended})
            .build())

        result = StrategicIntelligenceSystem.resume_project(entity, "old_quest")
        assert result is not None
        resumed = result.projects_add_or_update[0]
        assert resumed.status == ProjectStatus.ACTIVE
        assert result.current_project_id_set == "old_quest"
        assert result.current_objective_id_set == "obj_1"


class TestGenericInterruptionBypass:
    """STRAT-186 (generalized): the lock-bypass gate replaces the old kind-string allowlist
    (kind=='danger' and score>80, or kind=='detour') with: 'detour' as the sole unconditional
    structural bypass, and any other kind bypassing only when its score -- normalized as a
    percentage of its own system's declared max -- both exceeds the current project's own
    normalized effective score AND clears the 0.8 urgency floor."""

    def test_generic_kind_bypasses_when_score_and_floor_clear(self):
        """A novel kind never seen by the old allowlist bypasses the lock when both the
        floor and the current's normalized effective score are cleared."""
        current = ProjectState(
            id="current", kind="crafting", status=ProjectStatus.ACTIVE,
            score=5, lock_until_tick=100
        )
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.1),
            current_project=current
        )
        # candidate_pct = 90/100 = 0.9 > 0.8 floor; current_pct = 5/100 + 3/100 = 0.08
        candidate = ProjectState(id="novel", kind="scavenge", status=ProjectStatus.ACTIVE, score=90)
        result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=50)
        assert result is not None
        assert result.current_project_id_set == "novel"

    def test_generic_kind_blocked_when_floor_not_cleared(self):
        """A novel kind clears the current's normalized effective score but not the 0.8
        urgency floor -- still blocked."""
        current = ProjectState(
            id="current", kind="crafting", status=ProjectStatus.ACTIVE,
            score=5, lock_until_tick=100
        )
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.1),
            current_project=current
        )
        # candidate_pct = 60/100 = 0.6 < 0.8 floor, even though 0.6 > current_pct (0.08)
        candidate = ProjectState(id="novel", kind="scavenge", status=ProjectStatus.ACTIVE, score=60)
        result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=50)
        assert result is None

    def test_generic_kind_blocked_when_effective_current_not_cleared(self):
        """A novel kind clears the 0.8 urgency floor but the current project's own
        normalized effective score still exceeds it -- still blocked."""
        current = ProjectState(
            id="current", kind="crafting", status=ProjectStatus.ACTIVE,
            score=90, lock_until_tick=100
        )
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.5),
            current_project=current
        )
        # candidate_pct = 85/100 = 0.85 > 0.8 floor
        # current_pct = 90/100 + (0.5*30)/100 = 0.9 + 0.15 = 1.05 > candidate_pct
        candidate = ProjectState(id="novel", kind="scavenge", status=ProjectStatus.ACTIVE, score=85)
        result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=50)
        assert result is None

    def test_detour_bypasses_lock_unconditionally(self):
        """'detour' stays the sole unconditional structural bypass -- it must not be folded
        into the generic score/floor gate, so a detour candidate whose normalized percentage
        is far below the 0.8 urgency floor still bypasses the lock (the generic gate's own
        floor/normalized-effective-pct condition is never evaluated for it).

        Note: current's raw score/resistance are kept low (not "high-score" as originally
        sketched) because the function's final `candidate.score > effective_current_score`
        check (STRAT-005/006) is unchanged and unconditional -- it applies after the lock
        gate on every path, including a detour-bypassed one. A high-score current would fail
        that final raw check regardless of the lock-bypass outcome, making it impossible for
        this test to observe a successful switch; a low-score current isolates the assertion
        to the lock-bypass gate itself, which is what this test targets."""
        current = ProjectState(
            id="current", kind="crafting", status=ProjectStatus.ACTIVE,
            score=0.5, lock_until_tick=100
        )
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.0),
            current_project=current
        )
        # candidate_pct would be 1.0/100 = 0.01, far below the 0.8 floor -- a non-detour
        # candidate at this score would be blocked by the generic gate. detour skips it.
        candidate = ProjectState(id="detour_proj", kind="detour", status=ProjectStatus.ACTIVE, score=1.0)
        result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=50)
        assert result is not None
        assert result.current_project_id_set == "detour_proj"

    def test_danger_bypass_still_works_when_effective_current_clears(self):
        """The old 'kind==danger and score>80' scenario still bypasses post-generalization
        when the current project's own normalized effective score also clears (AC4, identical
        half)."""
        current = ProjectState(
            id="current", kind="crafting", status=ProjectStatus.ACTIVE,
            score=10, lock_until_tick=100
        )
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.3),
            current_project=current
        )
        # candidate_pct = 85/100 = 0.85 > 0.8 floor
        # current_pct = 10/100 + (0.3*30)/100 = 0.1 + 0.09 = 0.19 < candidate_pct
        candidate = ProjectState(id="danger_proj", kind="danger", status=ProjectStatus.ACTIVE, score=85)
        result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=50)
        assert result is not None
        assert result.current_project_id_set == "danger_proj"

    def test_danger_bypass_blocked_when_effective_current_not_cleared(self):
        """AC4's intentional-tightening half: a 'kind==danger, score>80' candidate that would
        have bypassed unconditionally under the old code is now blocked because the current
        project's own normalized effective score is not cleared."""
        current = ProjectState(
            id="current", kind="crafting", status=ProjectStatus.ACTIVE,
            score=90, lock_until_tick=100
        )
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.8),
            current_project=current
        )
        # candidate_pct = 85/100 = 0.85 > 0.8 floor
        # current_pct = 90/100 + (0.8*30)/100 = 0.9 + 0.24 = 1.14 > candidate_pct
        candidate = ProjectState(id="danger_proj", kind="danger", status=ProjectStatus.ACTIVE, score=85)
        result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=50)
        assert result is None


class TestEvaluateProjectSwitchStateParam:
    """AC1/AC2 (TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION): evaluate_project_switch()
    gains an optional `state` parameter used to check whether the triggering threat for a
    locked project has resolved (HP > 80%, no hostile within radius 10.0)."""

    def test_evaluate_project_switch_signature_accepts_state_kwarg(self):
        """The signature accepts a `state=` kwarg, and also still accepts no `state` at all
        (backward-compat smoke test for the 27 pre-existing direct call sites' calling
        convention, which predate this parameter)."""
        current = ProjectState(
            id="current", kind="crafting", status=ProjectStatus.ACTIVE, score=10
        )
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.0),
            current_project=current,
        )
        candidate = ProjectState(id="rival", kind="quest", status=ProjectStatus.ACTIVE, score=50)
        state = _make_state([entity], tick=10)

        # (a) called with a real state=
        result_with_state = StrategicIntelligenceSystem.evaluate_project_switch(
            entity, candidate, current_tick=10, state=state
        )
        assert result_with_state is not None

        # (b) called with no state argument at all
        result_without_state = StrategicIntelligenceSystem.evaluate_project_switch(
            entity, candidate, current_tick=10
        )
        assert result_without_state is not None

    def test_evaluate_project_switch_unlocked_path_identical_with_and_without_state(self):
        """For an unlocked current project (lock_until_tick <= current_tick), the raw
        comparison result must be byte-identical whether `state` is passed or omitted --
        `state` must not leak into the unlocked raw-comparison path."""
        current = ProjectState(
            id="current", kind="crafting", status=ProjectStatus.ACTIVE,
            score=50, lock_until_tick=0,
        )
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.5),
            current_project=current,
        )
        candidate = ProjectState(id="rival", kind="quest", status=ProjectStatus.ACTIVE, score=55)
        state = _make_state([entity], tick=10)

        result_with_state = StrategicIntelligenceSystem.evaluate_project_switch(
            entity, candidate, current_tick=10, state=state
        )
        result_without_state = StrategicIntelligenceSystem.evaluate_project_switch(
            entity, candidate, current_tick=10
        )
        assert result_with_state == result_without_state

    def test_evaluate_project_switch_locked_project_released_when_threat_resolved(self):
        """Locked current project + entity HP>80% + no hostile within radius 10.0 --> the
        locked-branch percentage/urgency-floor gate is skipped entirely and the raw
        comparison alone determines the outcome. The candidate here is scored to FAIL the
        old percentage/urgency-floor gate but PASS the raw comparison, proving the
        short-circuit is real and not accidentally equivalent to the pre-existing gate."""
        from src.core.builder import V2EntityBuilder
        from src.engine.apply import replace as fast_replace

        current = ProjectState(
            id="locked", kind="crafting", status=ProjectStatus.ACTIVE,
            score=10, lock_until_tick=100,
        )
        builder = (
            V2EntityBuilder(1)
            .kind("hero")
            .location(5.0, 5.0)
            .strategic(projects={current.id: current}, current_project_id=current.id)
            .cognition(interruption_resistance=0.0)
        )
        builder.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
        entity = builder.build()

        # candidate_pct = 40/100 = 0.4, below the 0.8 urgency floor -> would be blocked by
        # the old percentage gate. But candidate.score (40) > effective_current_score
        # (10 + 0.0*margin = 10) -> passes the raw comparison this test targets.
        candidate = ProjectState(id="rival", kind="quest", status=ProjectStatus.ACTIVE, score=40)
        state = _make_state([entity], tick=50)

        result = StrategicIntelligenceSystem.evaluate_project_switch(
            entity, candidate, current_tick=50, state=state
        )
        assert result is not None
        assert result.current_project_id_set == "rival"


class TestCognitionProfile:
    """Part 1 §Strategic: Profile derivation is deterministic."""

    def test_profile_derivation_deterministic(self):
        """Same entity state always produces same profile."""
        from src.core.builder import V2EntityBuilder
        entity = (V2EntityBuilder(1)
            .kind("hero")
            .location(5.0, 5.0)
            .attributes(wisdom=15, intelligence=12)
            .build())
        p1 = StrategicIntelligenceSystem.derive_cognition_profile(entity)
        p2 = StrategicIntelligenceSystem.derive_cognition_profile(entity)
        assert p1 == p2

    def test_higher_stats_produce_larger_capacities(self):
        """Higher WIS/INT → bigger strategic bandwidth."""
        from src.core.builder import V2EntityBuilder
        entity_low = (V2EntityBuilder(1)
            .kind("hero")
            .location(5.0, 5.0)
            .attributes(wisdom=5, intelligence=5, perception=5)
            .build())
        entity_high = (V2EntityBuilder(2)
            .kind("hero")
            .location(5.0, 5.0)
            .attributes(wisdom=25, intelligence=25, perception=25)
            .build())
        p_low = StrategicIntelligenceSystem.derive_cognition_profile(entity_low)
        p_high = StrategicIntelligenceSystem.derive_cognition_profile(entity_high)

        assert p_high.max_leads > p_low.max_leads
        assert p_high.max_concerns > p_low.max_concerns
        assert p_high.interruption_resistance > p_low.interruption_resistance

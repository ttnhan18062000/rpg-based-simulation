# Compliance IDs: PERF-001, PERF-017, RES-025, STRAT-PERF-001
import pytest
from src.core.governance import RuntimeMode, PressureSignals
from src.config.profiles import RuntimeProfile, HardwareClass
from src.engine.phase_governor import PhaseBudgetGovernor, ScanPolicy, PhaseBudgets
from src.engine.policy import GovernorPolicy
from src.engine.governor import ResourceGovernor
from src.engine.runtime_status import RuntimeStatus
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.updates import StateUpdate, EntityUpdate, NavigationUpdate
from src.core.movement_modes import MovementMode
from src.engine.candidate_selector import MovementCandidateSelector
from src.systems.strategic_systems.work_queue import StrategicWorkQueue
from src.core.dirty import DirtySet


@pytest.fixture
def base_profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="test_m17",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1024,
        max_cpu_percent=80.0,
        max_worker_count=4,
        max_queue_depth=100,
        max_work_debt=100,
        max_replay_buffer_kb=1000,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=16.0,
        degradation_threshold_ram=0.8,
        recovery_watermark=0.5,
        dwell_time_ticks=5,
        confidence_window_ticks=3
    )


def test_phase_budget_governor_normal_mode(base_profile: RuntimeProfile):
    signals = PressureSignals(tick_compute_ms=10.0)
    budgets = PhaseBudgetGovernor.evaluate(base_profile, signals, RuntimeMode.NORMAL, 100)

    assert budgets.candidate_budget == 1000
    assert budgets.strategic_budget == 50
    assert budgets.movement_budget == 1000
    assert budgets.scan_policy == ScanPolicy.FULL
    assert budgets.background_sweep_interval == 1
    assert budgets.compaction_level == "NORMAL"


def test_phase_budget_governor_constrained_mode(base_profile: RuntimeProfile):
    signals = PressureSignals(tick_compute_ms=10.0)
    budgets = PhaseBudgetGovernor.evaluate(base_profile, signals, RuntimeMode.CONSTRAINED, 101)

    assert budgets.candidate_budget == 500
    assert budgets.strategic_budget == 25
    assert budgets.movement_budget == 500
    assert budgets.scan_policy == ScanPolicy.THROTTLED
    assert budgets.background_sweep_interval == 3
    assert budgets.compaction_level == "NORMAL"


def test_phase_budget_governor_degraded_mode(base_profile: RuntimeProfile):
    signals = PressureSignals(tick_compute_ms=10.0)
    budgets = PhaseBudgetGovernor.evaluate(base_profile, signals, RuntimeMode.DEGRADED, 102)

    assert budgets.candidate_budget == 200
    assert budgets.strategic_budget == 10
    assert budgets.movement_budget == 200
    assert budgets.scan_policy == ScanPolicy.EXACT_DIRTY
    assert budgets.background_sweep_interval == 5
    assert budgets.compaction_level == "AGGRESSIVE"


def test_phase_budget_governor_survival_mode(base_profile: RuntimeProfile):
    signals = PressureSignals(tick_compute_ms=10.0)
    budgets = PhaseBudgetGovernor.evaluate(base_profile, signals, RuntimeMode.SURVIVAL, 103)

    assert budgets.candidate_budget == 50
    assert budgets.strategic_budget == 5
    assert budgets.movement_budget == 50
    assert budgets.scan_policy == ScanPolicy.EXACT_DIRTY
    assert budgets.background_sweep_interval == 10
    assert budgets.compaction_level == "AGGRESSIVE"


def test_resource_governor_propagates_phase_budgets(base_profile: RuntimeProfile):
    gov = ResourceGovernor()
    status = RuntimeStatus()

    # Normal
    signals_normal = PressureSignals(tick_compute_ms=5.0)
    policy = gov.evaluate(base_profile, signals_normal, status, 10)
    assert status.current_mode == RuntimeMode.NORMAL
    assert policy.phase_budgets.candidate_budget == 1000

    # Survival
    signals_survival = PressureSignals(tick_compute_ms=30.0)
    policy_surv = gov.evaluate(base_profile, signals_survival, status, 11)
    assert status.current_mode == RuntimeMode.SURVIVAL
    assert policy_surv.phase_budgets.candidate_budget == 50
    assert policy_surv.candidate_budget == 50
    assert policy_surv.strategic_budget == 5
    assert policy_surv.movement_budget == 50
    assert policy_surv.scan_policy == ScanPolicy.EXACT_DIRTY
    assert policy_surv.background_sweep_interval == 10
    assert policy_surv.compaction_level == "AGGRESSIVE"


def test_movement_candidate_selector_throttles_wander_under_budget():
    entities = {}
    # Create 2 urgent entities (dirty nav update) and 10 non-urgent entities
    for i in range(1, 13):
        entities[i] = (
            V2EntityBuilder(i)
            .kind("ACTOR")
            .location(10.0, 10.0)
            .navigation(target=(20.0, 20.0), movement_mode=MovementMode.PURSUE)
            .combat(alive=True, readiness=20.0, move_cost=5.0)
            .lifecycle(active=True)
            .build()
        )

    state = AuthoritativeState(tick=100, seed=42, world_time=100, entities=entities)
    raw_update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(30.0, 30.0))),
            2: EntityUpdate(entity_id=2, navigation=NavigationUpdate(target_set=(30.0, 30.0)))
        }
    )
    from dataclasses import replace
    ds = DirtySet.from_update(state, raw_update)
    update = replace(raw_update, dirty_set=ds)

    # Under tight movement budget = 4 and throttled scan policy
    selected = MovementCandidateSelector.select(
        state, update, state.entities.keys(), budget=4, scan_policy=ScanPolicy.THROTTLED
    )

    # Must preserve the 2 urgent entities exactly and fill remainder of budget with non-urgent
    assert 1 in selected
    assert 2 in selected
    assert len(selected) == 4


def test_strategic_work_queue_throttles_background_sweep():
    entities = {}
    # Create 20 healthy, idle entities (no active blockers or biological emergencies)
    # They will only be eligible for Tier 7 (background sweep)
    for i in range(1, 21):
        entities[i] = (
            V2EntityBuilder(i)
            .kind("ACTOR")
            .location(10.0, 10.0)
            .combat(alive=True, readiness=20.0)
            .lifecycle(active=True)
            .build()
        )

    state = AuthoritativeState(tick=100, seed=42, world_time=100, entities=entities)
    update = StateUpdate()

    # Under normal sweep_interval = 1, all 20 are included in sweep (capped by budget 10)
    selected_normal = StrategicWorkQueue.build(state, update, DirtySet(), budget=10, sweep_interval=1)
    assert len(selected_normal) == 10

    # Under survival sweep_interval = 10, only entities where (tick+id)%10 == 0 are included
    # For tick=100, (100+id)%10 == 0 => id=10, id=20 (exactly 2 entities)
    selected_throttled = StrategicWorkQueue.build(state, update, DirtySet(), budget=10, sweep_interval=10)
    assert set(selected_throttled) == {10, 20}

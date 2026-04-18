import pytest
from src_v2.core.state import AuthoritativeState, EntityState
from src_v2.engine.scheduler import DeterministicScheduler, PeriodicDefinition
from src_v2.engine.policy import GovernorPolicy
from src_v2.core.governance import RuntimeMode
from src_v2.core.work import WorkClass


def test_survival_shedding():
    """Verify that only authoritative work survives in SURVIVAL mode."""
    # Definitions: one auth, one non-auth
    p_auth = PeriodicDefinition(subsystem_id="A", action_type="ACT", cadence=1, is_authoritative=True)
    p_non_auth = PeriodicDefinition(subsystem_id="N", action_type="ACT", cadence=1, is_authoritative=False)
    
    scheduler = DeterministicScheduler(periodic_defs=[p_auth, p_non_auth])
    
    state = AuthoritativeState(tick=1, seed=42, 
        entities={1: EntityState(id=1, kind="hero", position=(0,0), readiness=100.0)},
        periodic_due_ticks={"A": 1, "N": 1}
    )
    
    # 1. Normal Policy
    policy_normal = GovernorPolicy.from_mode(RuntimeMode.NORMAL)
    work_normal = scheduler.select_work(state, policy_normal)
    # Expect 3 items: Entity 1, Auth P, Non-Auth P
    assert len(work_normal) == 3
    
    # 2. Survival Policy
    policy_survival = GovernorPolicy.from_mode(RuntimeMode.SURVIVAL)
    work_survival = scheduler.select_work(state, policy_survival)
    # Expect 2 items: Entity 1, Auth P. Non-Auth P should be shed.
    assert len(work_survival) == 2
    owner_ids = [w.owner_id for w in work_survival]
    assert 1 in owner_ids
    assert "A" in owner_ids
    assert "N" not in owner_ids


def test_degraded_opportunistic_shedding():
    """Verify that opportunistic work (placeholder) is dropped in DEGRADED."""
    # Opportunistic logic is currently a placeholder in select_work, 
    # but the policy flag is what we test here.
    policy_degraded = GovernorPolicy.from_mode(RuntimeMode.DEGRADED)
    assert policy_degraded.allow_opportunistic is False
    
    policy_normal = GovernorPolicy.from_mode(RuntimeMode.NORMAL)
    assert policy_normal.allow_opportunistic is True

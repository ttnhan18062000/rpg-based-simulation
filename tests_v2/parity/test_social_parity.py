import pytest
from src_v2.core.state import EntityState, SocialComponent, IdentityComponent, InventoryComponent
from src_v2.core.strategic import StrategicComponent
from src_v2.systems.social import SocialAppraisalSystem
from src_v2.engine.apply import ApplyPath
from src_v2.core.updates import EntityUpdate, StateUpdate, SocialUpdate

def test_source_trust_recalibration():
    """
    Parity Test: LEG-RPG-049 / test_source_trust_recalibration
    Verify that a False lead outcome reduces source trust by 0.2 and a Good outcome increases it by 0.1.
    """
    # 1. Setup Initial State
    observer = EntityState(
        id=1,
        kind="hero",
        position=(0, 0),
        social=SocialComponent(trust_history={2: 0.5}) # Base trust 0.5
    )
    
    # 2. Test Success (Lead was true)
    success_upd = SocialAppraisalSystem.recalibrate_trust(observer, 2, 1.0)
    assert success_upd.trust_delta[2] == pytest.approx(0.1)
    
    # Apply update
    state_upd = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, social=success_upd)})
    new_state = ApplyPath._apply_entity_update(observer, state_upd.entity_updates[1])
    assert new_state.social.trust_history[2] == pytest.approx(0.6)
    
    # 3. Test Failure (Lead was false)
    fail_upd = SocialAppraisalSystem.recalibrate_trust(new_state, 2, -1.0)
    assert fail_upd.trust_delta[2] == pytest.approx(-0.2)
    
    # Apply update
    state_upd_fail = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, social=fail_upd)})
    final_state = ApplyPath._apply_entity_update(new_state, state_upd_fail.entity_updates[1])
    assert final_state.social.trust_history[2] == pytest.approx(0.4)

def test_recruitment_offer_evaluation():
    """
    Parity Test: test_recruitment_offer_evaluation_acceptance
    Verify that recruitment is accepted only if Trust + Reward outweighs Risk.
    """
    # High trust, low payout, low risk -> Accept
    candidate = EntityState(
        id=1,
        kind="hero",
        position=(0, 0),
        social=SocialComponent(trust_history={2: 0.9})
    )
    assert SocialAppraisalSystem.evaluate_recruitment_offer(candidate, 2, 50, 0.1) is True
    
    # Low trust (Stranger), low payout, high risk -> Reject
    stranger = EntityState(
        id=1,
        kind="hero",
        position=(0, 0),
        social=SocialComponent(trust_history={2: 0.2})
    )
    assert SocialAppraisalSystem.evaluate_recruitment_offer(stranger, 2, 50, 0.8) is False

def test_betrayal_increment():
    """
    Verify that recording a betrayal authoritatively increments the betrayal count.
    """
    observer = EntityState(id=1, kind="hero", position=(0,0))
    betray_upd = SocialAppraisalSystem.record_betrayal(2)
    
    state_upd = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, social=betray_upd)})
    new_state = ApplyPath._apply_entity_update(observer, state_upd.entity_updates[1])
    
    assert new_state.social.betrayal_count == 1

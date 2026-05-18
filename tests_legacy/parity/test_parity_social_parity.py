import pytest
from src_legacy.core.state import EntityState, SocialComponent, IdentityComponent, CombatComponent
from src_legacy.systems.social import SocialAppraisalSystem
from src_legacy.engine.apply import ApplyPath
from src_legacy.core.updates import EntityUpdate, StateUpdate, SocialUpdate

@pytest.mark.v2_contract
def test_source_trust_recalibration_ratio():
    """
    Parity Test: LEG-RPG-049 / test_source_trust_recalibration
    Verify that harm (damage) reduces trust according to the legacy formula:
    trust_delta = -0.1 - (damage_ratio * 0.5)
    """
    observer = EntityState(
        id=1, kind="hero", position=(0, 0),
        social=SocialComponent(trust_history={2: 0.8}),
        combat=CombatComponent(hp=100, max_hp=100)
    )
    
    # 1. Test Harm (Damage ratio 0.2)
    # Expected: -0.1 - (0.2 * 0.5) = -0.1 - 0.1 = -0.2
    harm_upd = SocialAppraisalSystem.recalibrate_trust(observer, 2, harm_ratio=0.2)
    assert harm_upd.trust_delta[2] == pytest.approx(-0.2)
    
    new_state = ApplyPath._apply_entity_update(observer, EntityUpdate(entity_id=1, social=harm_upd))
    assert new_state.social.trust_history[2] == pytest.approx(0.6)
    
    # 2. Test Help (Help ratio 0.1)
    # Expected: 0.05 + (0.1 * 0.4) = 0.05 + 0.04 = 0.09
    help_upd = SocialAppraisalSystem.recalibrate_trust(new_state, 2, help_ratio=0.1)
    assert help_upd.trust_delta[2] == pytest.approx(0.09)
    
    final_state = ApplyPath._apply_entity_update(new_state, EntityUpdate(entity_id=1, social=help_upd))
    assert final_state.social.trust_history[2] == pytest.approx(0.69)

@pytest.mark.v2_contract
def test_recruitment_offer_evaluation():
    """
    Parity Test: test_recruitment_offer_evaluation_acceptance
    Verify that recruitment is accepted only if Trust + Reward outweighs Risk.
    """
    candidate = EntityState(
        id=1, kind="hero", position=(0, 0),
        social=SocialComponent(trust_history={2: 0.9})
    )
    assert SocialAppraisalSystem.evaluate_recruitment_offer(candidate, 2, 50, 0.1) is True
    
    stranger = EntityState(
        id=1, kind="hero", position=(0, 0),
        social=SocialComponent(trust_history={2: 0.2})
    )
    assert SocialAppraisalSystem.evaluate_recruitment_offer(stranger, 2, 50, 0.8) is False

@pytest.mark.v2_contract
def test_betrayal_increment():
    """
    Verify that recording a betrayal authoritatively increments the betrayal count.
    """
    observer = EntityState(id=1, kind="hero", position=(0,0))
    betray_upd = SocialAppraisalSystem.record_betrayal(2)
    
    new_state = ApplyPath._apply_entity_update(observer, EntityUpdate(entity_id=1, social=betray_upd))
    assert new_state.social.betrayal_count == 1

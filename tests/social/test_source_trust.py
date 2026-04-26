"""
Contract tests for Source Trust Recalibration.

Covers:
- LEG-RPG-123: Refutation drops trust
- Part 1 §Social: Social learning updates trust bonds from interaction evidence
"""
import pytest
from src.core.state import EntityState
from src.core.strategic import StrategicComponent, SourceTrustEntry
from src.systems.social import SocialAppraisalSystem


def _make_entity_with_trust(source_id, trust=0.5, interactions=0):
    source_entry = SourceTrustEntry(
        entity_id=source_id, trust=trust, interactions=interactions
    )
    strategic = StrategicComponent(
        source_trust={source_id: source_entry}
    )
    return EntityState(id=1, kind="hero", position=(5.0, 5.0), strategic=strategic)


class TestRefutationDropsTrust:
    """LEG-RPG-123: Refutation drops trust."""

    def test_failure_drops_source_trust(self):
        entity = _make_entity_with_trust(source_id=42, trust=0.6)
        result = SocialAppraisalSystem.recalibrate_source_trust(
            observer=entity, source_id=42, outcome="FAILURE"
        )
        assert len(result.source_trust_updates) == 1
        updated = result.source_trust_updates[0]
        assert updated.trust < 0.6
        assert updated.trust == pytest.approx(0.45, abs=0.01)
        assert updated.last_outcome == "FAILURE"

    def test_success_boosts_source_trust(self):
        entity = _make_entity_with_trust(source_id=42, trust=0.5)
        result = SocialAppraisalSystem.recalibrate_source_trust(
            observer=entity, source_id=42, outcome="SUCCESS"
        )
        updated = result.source_trust_updates[0]
        assert updated.trust > 0.5
        assert updated.trust == pytest.approx(0.6, abs=0.01)
        assert updated.last_outcome == "SUCCESS"

    def test_repeated_failures_degrade_trust(self):
        """Multiple failures compound trust degradation."""
        entity = _make_entity_with_trust(source_id=42, trust=0.5)

        # First failure
        r1 = SocialAppraisalSystem.recalibrate_source_trust(entity, 42, "FAILURE")
        new_trust = r1.source_trust_updates[0].trust

        # Simulate applying the update
        entity2 = _make_entity_with_trust(source_id=42, trust=new_trust, interactions=1)

        # Second failure
        r2 = SocialAppraisalSystem.recalibrate_source_trust(entity2, 42, "FAILURE")
        final_trust = r2.source_trust_updates[0].trust

        assert final_trust < new_trust
        assert final_trust < 0.5

    def test_trust_never_below_zero(self):
        entity = _make_entity_with_trust(source_id=42, trust=0.05)
        result = SocialAppraisalSystem.recalibrate_source_trust(entity, 42, "FAILURE")
        assert result.source_trust_updates[0].trust >= 0.0

    def test_trust_never_above_one(self):
        entity = _make_entity_with_trust(source_id=42, trust=0.95)
        result = SocialAppraisalSystem.recalibrate_source_trust(entity, 42, "SUCCESS")
        assert result.source_trust_updates[0].trust <= 1.0

    def test_unknown_source_defaults_to_half(self):
        """Source not in source_trust starts at 0.5."""
        entity = EntityState(id=1, kind="hero", position=(5.0, 5.0))
        result = SocialAppraisalSystem.recalibrate_source_trust(entity, 99, "SUCCESS")
        updated = result.source_trust_updates[0]
        assert updated.trust == pytest.approx(0.6, abs=0.01)
        assert updated.interactions == 1


class TestSocialContracts:
    """Part 1 §Social: Social contracts as strategic objects with consequences."""

    def test_honored_contract_boosts_trust(self):
        from src.systems.social import SocialContract
        contract = SocialContract(
            id="contract_001", kind="escort",
            party_ids=[1, 2], status="ACTIVE", created_tick=10
        )
        social_up, turning_points = SocialAppraisalSystem.process_contract_outcome(
            contract, outcome="HONORED", current_tick=50
        )
        assert 2 in social_up.trust_delta
        assert social_up.trust_delta[2] > 0
        assert len(turning_points) == 0

    def test_broken_contract_creates_betrayal_turning_points(self):
        from src.systems.social import SocialContract
        contract = SocialContract(
            id="contract_002", kind="alliance",
            party_ids=[1, 2, 3], status="ACTIVE", created_tick=10
        )
        social_up, turning_points = SocialAppraisalSystem.process_contract_outcome(
            contract, outcome="BROKEN", current_tick=60
        )
        # Trust drops for all parties
        assert any(v < 0 for v in social_up.trust_delta.values())
        # Betrayal turning points created
        assert len(turning_points) == 3  # One per party
        assert all(tp.kind == "betrayal" for tp in turning_points)


class TestFamiliarity:
    """Part 1 §Social: Social learning updates familiarity bonds."""

    def test_positive_interaction_builds_familiarity(self):
        entity = EntityState(id=1, kind="hero", position=(5.0, 5.0))
        update = SocialAppraisalSystem.update_familiarity(
            observer=entity, subject_id=42,
            interaction_quality=1.0, current_tick=100
        )
        assert len(update.bond_updates) == 1
        b_upd = update.bond_updates[0]
        assert b_upd.familiarity_delta > 0
        assert b_upd.sentiment_delta > 0

    def test_cha_modifier_scales_gain(self):
        entity = EntityState(id=1, kind="hero", position=(5.0, 5.0))
        upd_low = SocialAppraisalSystem.update_familiarity(
            entity, 42, 1.0, 100, cha_modifier=0.5
        )
        upd_high = SocialAppraisalSystem.update_familiarity(
            entity, 42, 1.0, 100, cha_modifier=2.0
        )
        assert upd_high.bond_updates[0].familiarity_delta > upd_low.bond_updates[0].familiarity_delta

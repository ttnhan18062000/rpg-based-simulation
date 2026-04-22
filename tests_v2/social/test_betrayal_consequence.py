"""
Contract tests for Betrayal Consequence Pipeline.

Covers:
- LEG-RPG-119: Betrayal (Avenge) — betrayal turning point adds Avenge directive
- Part 1 §Social: Private betrayal history can override public recruiter reputation
"""
import pytest
from src_v2.core.state import EntityState, SocialComponent
from src_v2.core.strategic import (
    StrategicComponent, DirectivePriority
)
from src_v2.systems.social import SocialAppraisalSystem


def _make_entity(entity_id=1, trust_history=None, betrayal_count=0):
    social = SocialComponent(
        trust_history=trust_history or {},
        betrayal_count=betrayal_count
    )
    return EntityState(id=entity_id, kind="hero", position=(5.0, 5.0), social=social)


class TestBetrayalConsequence:
    """LEG-RPG-119: Betrayal (Avenge)."""

    def test_betrayal_adds_avenge_directive(self):
        """High-salience betrayal creates an AVENGE directive."""
        entity = _make_entity(trust_history={99: 0.7})
        social_up, strat_up = SocialAppraisalSystem.process_betrayal(
            victim=entity, betrayer_id=99, salience=0.8, current_tick=50
        )
        # Social: trust drops, betrayal incremented
        assert 99 in social_up.trust_delta
        assert social_up.trust_delta[99] < 0
        assert social_up.betrayal_increment == 1

        # Strategic: avenge directive created
        assert len(strat_up.directives_add_or_update) == 1
        d = strat_up.directives_add_or_update[0]
        assert d.kind == "avenge"
        assert d.target == "99"
        assert d.priority == DirectivePriority.HIGH

    def test_low_salience_betrayal_no_directive(self):
        """Low-salience betrayal doesn't create a directive."""
        entity = _make_entity()
        social_up, strat_up = SocialAppraisalSystem.process_betrayal(
            victim=entity, betrayer_id=99, salience=0.3, current_tick=50
        )
        assert social_up.betrayal_increment == 1
        assert len(strat_up.directives_add_or_update) == 0

    def test_betrayal_drops_trust_heavily(self):
        """Betrayal produces large negative trust delta."""
        entity = _make_entity(trust_history={99: 0.8})
        social_up, _ = SocialAppraisalSystem.process_betrayal(
            victim=entity, betrayer_id=99, salience=0.9, current_tick=50
        )
        assert social_up.trust_delta[99] < -0.5


class TestBetrayalOverridesReputation:
    """Part 1 §Social: Private betrayal overrides public reputation."""

    def test_betrayal_trauma_blocks_recruitment(self):
        """Entity that has been betrayed is harder to recruit."""
        # Clean entity accepts reasonable offer
        # Score = (0.7 * 0.5) + (200/200 * 0.3) - (0.2 * 0.1) - 0 = 0.35 + 0.3 - 0.02 = 0.63
        clean = _make_entity(trust_history={10: 0.7}, betrayal_count=0)
        assert SocialAppraisalSystem.evaluate_recruitment_offer(
            clean, recruiter_id=10, payout=200, risk=0.2
        ) is True

        # Same offer refused by entity with betrayal trauma
        # Score = (0.7 * 0.5) + (200/200 * 0.3) - (0.2 * 0.1) - 0.3 = 0.63 - 0.3 = 0.33
        traumatized = _make_entity(trust_history={10: 0.7}, betrayal_count=3)
        assert SocialAppraisalSystem.evaluate_recruitment_offer(
            traumatized, recruiter_id=10, payout=200, risk=0.2
        ) is False

    def test_low_trust_recruiter_penalized(self):
        """Recruiter with low trust faces extra penalty."""
        entity = _make_entity(trust_history={10: 0.2}, betrayal_count=0)
        result = SocialAppraisalSystem.evaluate_recruitment_offer(
            entity, recruiter_id=10, payout=150, risk=0.3
        )
        assert result is False  # Low trust + penalty makes score too low

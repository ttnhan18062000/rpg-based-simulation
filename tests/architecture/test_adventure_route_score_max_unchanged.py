"""
Architecture guard for TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5.

This ticket deliberately decoupled AdventureGoalScorer.score()'s tier-5-competition
normalization from src.systems.strategic_systems.intelligence._ADVENTURE_ROUTE_SCORE_MAX,
giving it its own dedicated _ADVENTURE_ROUTE_TIER5_COMPETITION_MAX constant in
adventure_scorer.py instead. _ADVENTURE_ROUTE_SCORE_MAX itself must stay exactly 2.9 and
continue to serve only _score_scale_max()'s Generalized Bypass gate purpose in
evaluate_project_switch() (STRAT-186) -- this ticket's fix must never touch it, and any future
change (accidental or otherwise) that alters the Generalized Bypass gate's own denominator
should fail loudly here rather than silently.

See tests/architecture/test_committed_intention_arbiter_byte_identical_guard.py for the sibling
byte-identical-guard precedent this test follows in spirit (a direct source-level pin, not a
behavioral test), and tests/unit/strategic/test_score_normalization.py for the existing
Generalized Bypass gate behavioral coverage this test deliberately does not modify or duplicate.
"""
from src.systems.strategic_systems.intelligence import _ADVENTURE_ROUTE_SCORE_MAX


def test_adventure_route_score_max_stays_2_9_unchanged():
    assert _ADVENTURE_ROUTE_SCORE_MAX == 2.9, (
        "_ADVENTURE_ROUTE_SCORE_MAX must remain exactly 2.9 -- it is the Generalized Bypass "
        "gate's own denominator (evaluate_project_switch()/_score_scale_max(), STRAT-186), "
        "decoupled from AdventureGoalScorer.score()'s tier-5-competition normalization by "
        "TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5's own dedicated "
        "_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX constant. A change here would silently affect "
        "RegionStabilizationGoalScorer/SocialContractGoalScorer, which still reuse this constant."
    )

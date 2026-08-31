"""
Architecture guard for TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION's AC2.

ENABLE_ADVENTURE_ROUTING gates nothing today: AdventureDecisionPhase (the phase that used
to read this flag via run_phase(..., feature_flag="ENABLE_ADVENTURE_ROUTING")) was deleted
in full by TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE. Its replacement,
AdventureGoalScorer.score() (src/ai/goals/adventure_scorer.py), runs unconditionally every
tick as a tier-5 GoalScorer candidate -- not gated behind this or any other flag (see
docs/parity_ledger/strategic_cognition.yaml STRAT-252, docs/engine/known_limitations.md
Section 1.5). This structural inertness is what resolves the "does ENABLE_SELF_MODEL_COGNITION
interact with ENABLE_ADVENTURE_ROUTING" question statically, without an empirical combination
trial: there is no runtime path left for the two flags' values to interact.

This test pins that inertness so a future re-wiring of ENABLE_ADVENTURE_ROUTING to gate
something again fails loudly here, forcing an explicit update to known_limitations.md
Section 1.5's claim and re-examination of this ticket's AC2 resolution, instead of the
doc silently going stale.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

_LIVE_GATING_PATTERNS = (
    'is_enabled("ENABLE_ADVENTURE_ROUTING")',
    "is_enabled('ENABLE_ADVENTURE_ROUTING')",
    'get_flag_mode("ENABLE_ADVENTURE_ROUTING")',
    "get_flag_mode('ENABLE_ADVENTURE_ROUTING')",
    'feature_flag="ENABLE_ADVENTURE_ROUTING"',
    "feature_flag='ENABLE_ADVENTURE_ROUTING'",
)

# The flag's own registration -- default OFF, not a gating call site.
_EXEMPT_PATH = SRC_ROOT / "domains" / "optimization" / "feature_flags.py"


def test_enable_adventure_routing_has_no_live_gating_call_site():
    offenders = []
    for path in SRC_ROOT.rglob("*.py"):
        if path == _EXEMPT_PATH:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in _LIVE_GATING_PATTERNS:
            if pattern in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {pattern!r}")

    assert not offenders, (
        "ENABLE_ADVENTURE_ROUTING has a live gating call site outside "
        "feature_flags.py's own registration -- this reopens the "
        "ENABLE_SELF_MODEL_COGNITION + ENABLE_ADVENTURE_ROUTING combination question "
        "(TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION AC2) and requires updating "
        "docs/engine/known_limitations.md Section 1.5 and "
        "docs/parity_ledger/strategic_cognition.yaml STRAT-252 to match:\n"
        + "\n".join(offenders)
    )

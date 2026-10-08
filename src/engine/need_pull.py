"""
src/engine/need_pull.py
───────────────────────────────────────────────────────────────────────────────
TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07

World Rule SURV-07: a need's pull on a subject's choice grows steeply as its consequence line approaches, so that well
before the line it outranks ordinary goals (work, trade, social errands, clearing a blocker), early enough for a subject
with a way to meet it to reach that way before the line. Only a present threat to life outranks a pressing need.

The curve and its constants are engineering's (the Rule leaves them to engineering). Justification, measured on the corpus
(`crowded_frontier` and `frontier_living_world`, seed 42, 1500 ticks, `audit_mode`): the highest ordinary goal utilities are
region_stabilization 100.0 (flat), resolve_blocker 103.8, harvesting 95, and the need goals themselves are only the raw need
(hunger 0 to 100, fatigue sleep_debt plus 30 at night), so no need ever won. The ramp below takes a need above 104 by about
75% of its line, and above town_return's 134.8 by 85%; the worst walk to an inn is about 190 tiles, so the margin is the need
the subject will have ON ARRIVAL, not the need it has now. Pure functions: no state, no randomness.
"""
from __future__ import annotations

# The pull is the raw need below ESCALATION_ONSET (a fraction of the consequence line), then a smoothstep adds up to
# ESCALATION_AMPLITUDE by ESCALATION_FULL.
ESCALATION_ONSET = 0.6
ESCALATION_FULL = 0.85
ESCALATION_AMPLITUDE = 60.0

# The consequence lines of `src/engine/apply.py` (hunger damage from 95.0, sleep-deprivation damage from 98.0); kept here as
# named values, not re-derived. The per-tick accumulation is NOT here: it is per kind (SURV-05, `need_rates(entity)`), so callers
# pass the subject's own rate.
HUNGER_LINE = 95.0
SLEEP_LINE = 98.0

# A walking subject covers about one tile per tick (measured: 21 tiles in 20 ticks).
TICKS_PER_TILE = 1.0


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """0 at or below `edge0`, 1 at or above `edge1`, and a smooth S between."""
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def arrival_fraction(need: float, rate: float, travel_tiles: float, line: float) -> float:
    """The fraction of its consequence line the need will have reached when the subject gets where it can meet it."""
    return (need + rate * TICKS_PER_TILE * max(0.0, travel_tiles)) / line


def need_pull(raw_utility: float, need: float, rate: float, travel_tiles: float, line: float) -> float:
    """`raw_utility` (the need's utility today) plus the SURV-07 escalation for the need level on arrival."""
    return raw_utility + ESCALATION_AMPLITUDE * smoothstep(
        ESCALATION_ONSET, ESCALATION_FULL, arrival_fraction(need, rate, travel_tiles, line)
    )


def hunger_pull(raw_utility: float, hunger: float, hunger_rate: float, travel_tiles: float) -> float:
    """The hunger goal's utility with the SURV-07 escalation for the hunger the subject will have on arrival."""
    return need_pull(raw_utility, hunger, hunger_rate, travel_tiles, HUNGER_LINE)


def sleep_pull(raw_utility: float, sleep_debt: float, sleep_rate: float, travel_tiles: float) -> float:
    """The fatigue goal's utility with the SURV-07 escalation for the sleep debt the subject will have on arrival."""
    return need_pull(raw_utility, sleep_debt, sleep_rate, travel_tiles, SLEEP_LINE)

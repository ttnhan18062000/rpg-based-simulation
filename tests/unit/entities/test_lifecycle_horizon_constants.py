"""
Unit regression guard for TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING (Card J,
J3 -- `aging_death`/`succession`).

Pins the ticket's Level-2 horizon arithmetic: `LifecycleComponent.max_age_ticks` (default,
src/core/state.py:165) is `70 * TICKS_PER_FANTASY_YEAR`
(`TICKS_PER_FANTASY_YEAR = 288_000`, src/core/calendar.py:10-13) == 20,160,000 ticks -- roughly
4,032x-20,160x longer than the 1,000-5,000-tick corpus runs this repo's own evidence cites. This
is a real-corpus-horizon reachability CONDITION, not a defect: the mechanism itself is proven
correct via staged-scenario technique
(tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py), but no real corpus run has
been observed to produce a natural old-age death through ordinary per-tick accumulation. If the
default lifespan or the fantasy-year calendar constant is ever changed, this test forces that
re-examination rather than letting the arithmetic go silently stale.
"""
from __future__ import annotations

from src.core.calendar import TICKS_PER_FANTASY_YEAR
from src.core.state import LifecycleComponent

_CORPUS_RUN_LENGTH_REFERENCE_TICKS = 5000


def test_default_lifespan_exceeds_corpus_run_horizon():
    max_age_ticks = LifecycleComponent().max_age_ticks

    assert max_age_ticks == 70 * TICKS_PER_FANTASY_YEAR == 20_160_000

    ratio = max_age_ticks / _CORPUS_RUN_LENGTH_REFERENCE_TICKS
    assert ratio >= 1000, (
        f"Default lifespan ({max_age_ticks} ticks) is only {ratio:.1f}x the reference corpus "
        f"run length ({_CORPUS_RUN_LENGTH_REFERENCE_TICKS} ticks) -- J3's Level-2 'not reachable "
        "within any real corpus run' claim (TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-"
        "AGING) needs re-examination."
    )

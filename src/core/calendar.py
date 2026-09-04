"""Single source of truth for the World Evolution Bible's calendar authority
(docs/mechanics/05_world_evolution.md; decided in TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY):
2,400 ticks/day, a 120-day fantasy year (4 seasons of 30 days each). Any code converting
between raw ticks and fantasy-calendar units should import these constants rather than
hardcoding a second copy of the conversion.
"""

import math

TICKS_PER_DAY = 2400
DAYS_PER_SEASON = 30
SEASONS_PER_YEAR = 4
TICKS_PER_FANTASY_YEAR = TICKS_PER_DAY * DAYS_PER_SEASON * SEASONS_PER_YEAR  # 288,000


def fantasy_years_to_ticks(years: float) -> int:
    """Converts a fantasy-year duration into whole ticks, rounding up (a fractional tick
    cannot elapse, and rounding down would let an entity cross a boundary early)."""
    return math.ceil(years * TICKS_PER_FANTASY_YEAR)

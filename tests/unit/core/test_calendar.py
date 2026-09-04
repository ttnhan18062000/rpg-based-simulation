"""
TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION: locks in src/core/calendar.py as the single
source of truth for the World Evolution Bible's calendar authority (decided in
TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY: 2,400 ticks/day, a 120-day fantasy year).
"""
from src.core.calendar import (
    TICKS_PER_DAY, DAYS_PER_SEASON, SEASONS_PER_YEAR, TICKS_PER_FANTASY_YEAR,
    fantasy_years_to_ticks,
)


def test_calendar_constants_match_the_bible():
    assert TICKS_PER_DAY == 2400
    assert DAYS_PER_SEASON == 30
    assert SEASONS_PER_YEAR == 4
    assert TICKS_PER_FANTASY_YEAR == 288000


def test_fantasy_years_to_ticks_matches_manual_multiplication():
    assert fantasy_years_to_ticks(1) == 288000
    assert fantasy_years_to_ticks(12) == 3456000
    assert fantasy_years_to_ticks(60) == 17280000
    assert fantasy_years_to_ticks(70) == 20160000


def test_fantasy_years_to_ticks_rounds_up_fractional_years():
    """A fractional tick cannot elapse, and rounding down would let an entity cross a boundary
    one tick early -- confirms the ceiling, not truncation."""
    assert fantasy_years_to_ticks(0.5) == 144000
    assert fantasy_years_to_ticks(1 / 3) == 96000
    # A value that does NOT divide evenly must round up, not truncate.
    assert fantasy_years_to_ticks(1 / 7) > 288000 / 7

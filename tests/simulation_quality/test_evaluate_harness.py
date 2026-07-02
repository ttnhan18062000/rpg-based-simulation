"""Unit tests for tools/evaluate_simq.py core logic."""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from tools.evaluate_simq import _within_band, _compare, _parse_run_key


class TestWithinBand:
    def test_same_grade(self):
        assert _within_band("B", "B") is True

    def test_adjacent_pass_up(self):
        assert _within_band("A", "B") is True

    def test_adjacent_pass_down(self):
        assert _within_band("C", "B") is True

    def test_two_apart_fail_up(self):
        assert _within_band("S", "B") is False

    def test_two_apart_fail_down(self):
        assert _within_band("D", "B") is False

    def test_boundary_low(self):
        assert _within_band("D", "D") is True

    def test_boundary_high(self):
        assert _within_band("S", "S") is True

    def test_unknown_grade_returns_false(self):
        assert _within_band("Z", "B") is False
        assert _within_band("B", "Z") is False


class TestCompare:
    def test_detects_regression(self):
        rows = _compare("test_key", {"COMBAT": "D"}, {"COMBAT": "B"})
        assert len(rows) == 1
        assert rows[0]["status"] == "REGRESS"
        assert rows[0]["actual"] == "D"
        assert rows[0]["anchor"] == "B"

    def test_passes_within_band(self):
        rows = _compare("test_key", {"COMBAT": "A"}, {"COMBAT": "B"})
        assert len(rows) == 1
        assert rows[0]["status"] == "PASS"

    def test_exact_match_passes(self):
        rows = _compare("test_key", {"COMBAT": "B"}, {"COMBAT": "B"})
        assert rows[0]["status"] == "PASS"

    def test_missing_pillar(self):
        rows = _compare("test_key", {}, {"COMBAT": "B"})
        assert len(rows) == 1
        assert rows[0]["status"] == "MISSING"
        assert rows[0]["actual"] == "—"

    def test_multiple_pillars(self):
        actual = {"COMBAT": "A", "NARRATIVE": "D", "WORLD": "B"}
        anchor = {"COMBAT": "B", "NARRATIVE": "B", "WORLD": "B"}
        rows = _compare("test_key", actual, anchor)
        statuses = {r["pillar"]: r["status"] for r in rows}
        assert statuses["COMBAT"] == "PASS"
        assert statuses["NARRATIVE"] == "REGRESS"
        assert statuses["WORLD"] == "PASS"


class TestParseRunKey:
    def test_standard(self):
        name, seed, ticks = _parse_run_key("dungeon_crawl_seed42_200t")
        assert name == "dungeon_crawl"
        assert seed == 42
        assert ticks == 200

    def test_multiword_name(self):
        name, seed, ticks = _parse_run_key("urban_political_seed123_500t")
        assert name == "urban_political"
        assert seed == 123
        assert ticks == 500

    def test_routing_test_key(self):
        name, seed, ticks = _parse_run_key("simq_routing_test_seed456_500t")
        assert name == "simq_routing_test"
        assert seed == 456
        assert ticks == 500

    def test_long_tick_count(self):
        name, seed, ticks = _parse_run_key("sandbox_world_seed42_2000t")
        assert name == "sandbox_world"
        assert seed == 42
        assert ticks == 2000

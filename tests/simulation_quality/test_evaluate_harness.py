"""Unit tests for tools/evaluate_simq.py core logic."""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest

from tools.evaluate_simq import _within_band, _compare, _parse_run_key, _resolve_world_name, main


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


class TestResolveWorldName:
    """Regression coverage for TCK-20260713-SIMQ-EVAL-PROFILE-BUG.

    `_run_calibration` previously received the profile-name prefix and passed
    it straight through as the engine's `--name` (world) argument, which only
    happened to work when profile and world names were identical.
    """

    def test_profile_name_matches_world_directly(self):
        assert _resolve_world_name("dungeon_crawl") == "dungeon_crawl"

    def test_profile_name_is_a_variant_of_a_shorter_world_name(self):
        assert _resolve_world_name("urban_political_selfmodel_probe") == "urban_political"

    def test_unresolvable_profile_name_raises(self):
        with pytest.raises(ValueError):
            _resolve_world_name("totally_unknown_world_xyz")


class TestAnchorSchemaCompat:
    """Regression coverage for TCK-20260713-SIMQ-RAWSCORE-PERSIST.

    grade_anchors.json's per-pillar schema changed from a bare grade string
    (``"S"``) to an object (``{"grade": "S", "score": 2.87}``). main()'s call
    site must extract just the grade before calling _compare(), which still
    takes dict[str, str] unchanged.
    """

    def test_new_schema_read_path_matches_old_bare_string_inputs(self):
        old_schema_anchor_grades = {"COMBAT": "B", "NARRATIVE": "S"}
        new_schema_anchors = {
            "COMBAT": {"grade": "B", "score": 0.31},
            "NARRATIVE": {"grade": "S", "score": 3.19},
        }

        extracted = {p: v["grade"] for p, v in new_schema_anchors.items()}

        assert extracted == old_schema_anchor_grades
        actual = {"COMBAT": "A", "NARRATIVE": "D"}
        assert _compare("test_key", actual, extracted) == _compare(
            "test_key", actual, old_schema_anchor_grades
        )

    def test_main_dry_run_smoke_against_real_migrated_fixture(self, capsys):
        """Dry-run against the real post-migration fixture and calibration data,
        catching key-ordering/typing issues a synthetic dict might miss.
        """
        old_argv = sys.argv[:]
        try:
            sys.argv = [
                "evaluate_simq",
                "--dry-run",
                "--scenario", "sandbox_world_seed42_200t",
            ]
            with pytest.raises(SystemExit) as exc_info:
                main()
        finally:
            sys.argv = old_argv

        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "0 regressions" in out

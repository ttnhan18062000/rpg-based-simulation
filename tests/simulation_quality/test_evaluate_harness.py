"""Unit tests for tools/evaluate_simq.py core logic."""
from __future__ import annotations

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest

import tools.evaluate_simq as eval_mod
from tools.evaluate_simq import _within_band, _compare, _parse_run_key, _resolve_world_name, main
from src.simulation_quality.run_health import RunHealthRecord
from src.simulation_quality.persistence import QualityPersistence
from tests.simulation_quality.test_calibrate_simq import _force_small_queue, _patch_kernel_with_hook


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


class TestQueueOverflowGuardIntegration:
    """AC #3, TCK-20260702-OBSISO-ISOLATION-PROOF Steps 8-10: a forced queue
    overflow (or SURVIVAL entry) reaches evaluate_simq.py's outputs — hard-fail
    for evaluate-full (non-dry-run, inherits calibrate_simq.py's guard via
    _run_calibration() -> calibrate_simq.main()), warn for --dry-run.
    """

    def test_evaluate_simq_flags_queue_overflow_run(self, monkeypatch, tmp_path):
        def _hook(kernel):
            _force_small_queue(kernel, max_size=2)
            kernel.event_recorder.queue.get_size = lambda: 0

        _patch_kernel_with_hook(monkeypatch, _hook)
        monkeypatch.setattr(eval_mod, "CALIBRATION_ROOT", tmp_path / "calibration")

        run_key = "sandbox_world_seed42_5t"
        anchors_path = tmp_path / "anchors.json"
        anchors_path.write_text(json.dumps({run_key: {"COMBAT": {"grade": "B", "score": 0.0}}}))

        old_argv = sys.argv[:]
        try:
            sys.argv = ["evaluate_simq", "--scenario", run_key, "--anchors", str(anchors_path)]
            with pytest.raises(SystemExit) as exc_info:
                eval_mod.main()
        finally:
            sys.argv = old_argv

        assert exc_info.value.code == 2, (
            "a calibration run that hard-fails its integrity guard must be treated "
            "as a setup error (exit 2), not silently skipped or graded"
        )

        sidecar_path = tmp_path / "calibration" / run_key / "quality_report.run_health.json"
        assert sidecar_path.exists()
        record = RunHealthRecord.from_dict(json.loads(sidecar_path.read_text()))
        assert record.guard_passed is False
        assert record.dropped_count > 0

    def test_evaluate_simq_dry_run_warns_on_failed_guard_sidecar(self, monkeypatch, tmp_path, capsys):
        """--dry-run never re-runs the engine — it can only warn from a
        previously-written RunHealthRecord sidecar sitting next to a (possibly
        stale) quality_report.json, per the ticket's own default (hard-fail for
        calibration, warn for ad-hoc evaluation)."""
        monkeypatch.setattr(eval_mod, "CALIBRATION_ROOT", tmp_path / "calibration")

        run_key = "sandbox_world_seed42_5t"
        run_dir = tmp_path / "calibration" / run_key
        run_dir.mkdir(parents=True)
        (run_dir / "quality_report.json").write_text(json.dumps({
            "run_id": "stale-run",
            "tick_count": 5,
            "overall_score": 0.0,
            "overall_grade": "B",
            "generated_at": "2026-01-01T00:00:00+00:00",
            "pillars": {
                "COMBAT": {
                    "raw_score": 0.0, "normalized_score": 0.0, "grade": "B",
                    "event_count": 0, "negative_count": 0, "loop_detected": False,
                    "loop_flags": [], "worst_events": [],
                },
            },
        }))
        QualityPersistence.write_run_health(
            str(run_dir),
            RunHealthRecord(dropped_count=3, pressure_mode_final="NORMAL", survival_triggered=False, guard_passed=False),
        )

        anchors_path = tmp_path / "anchors.json"
        anchors_path.write_text(json.dumps({run_key: {"COMBAT": {"grade": "B", "score": 0.0}}}))

        old_argv = sys.argv[:]
        try:
            sys.argv = ["evaluate_simq", "--dry-run", "--scenario", run_key, "--anchors", str(anchors_path)]
            with pytest.raises(SystemExit):
                eval_mod.main()
        finally:
            sys.argv = old_argv

        err = capsys.readouterr().err
        assert "guard FAILED" in err
        assert "dropped_count=3" in err

    def test_evaluate_simq_dry_run_silent_when_guard_passed(self, monkeypatch, tmp_path, capsys):
        """Anti-drift: a sidecar showing guard_passed=True must not print a warning."""
        monkeypatch.setattr(eval_mod, "CALIBRATION_ROOT", tmp_path / "calibration")

        run_key = "sandbox_world_seed42_5t"
        run_dir = tmp_path / "calibration" / run_key
        run_dir.mkdir(parents=True)
        (run_dir / "quality_report.json").write_text(json.dumps({
            "run_id": "clean-run",
            "tick_count": 5,
            "overall_score": 0.0,
            "overall_grade": "B",
            "generated_at": "2026-01-01T00:00:00+00:00",
            "pillars": {
                "COMBAT": {
                    "raw_score": 0.0, "normalized_score": 0.0, "grade": "B",
                    "event_count": 0, "negative_count": 0, "loop_detected": False,
                    "loop_flags": [], "worst_events": [],
                },
            },
        }))
        QualityPersistence.write_run_health(
            str(run_dir),
            RunHealthRecord(dropped_count=0, pressure_mode_final="NORMAL", survival_triggered=False, guard_passed=True),
        )

        anchors_path = tmp_path / "anchors.json"
        anchors_path.write_text(json.dumps({run_key: {"COMBAT": {"grade": "B", "score": 0.0}}}))

        old_argv = sys.argv[:]
        try:
            sys.argv = ["evaluate_simq", "--dry-run", "--scenario", run_key, "--anchors", str(anchors_path)]
            with pytest.raises(SystemExit):
                eval_mod.main()
        finally:
            sys.argv = old_argv

        err = capsys.readouterr().err
        assert "guard FAILED" not in err

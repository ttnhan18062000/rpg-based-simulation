"""Tests for the profiling toolkit (TCK-20261003-PERF-PROFILING-TOOLKIT).

Nothing here needs the profiler binary except one end-to-end test that skips cleanly without py-spy.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tools.perf import _profiling_common as common
from tools.perf import flag_attribution, profile_diff, profile_tick

REPO_ROOT = Path(__file__).resolve().parents[2]
PERF = REPO_ROOT / "tools" / "perf"

FOLDED_OLD = (
    "# commit: aaa\n# scenario: combat\n"
    "main (k.py:1);_phase_resolution (kernel.py:683);<lambda> (src/engine/pipeline.py:320);work (m.py:5) 10\n"
    "main (k.py:1);_phase_resolution (kernel.py:690);<lambda> (src/engine/pipeline.py:398);other (n.py:9) 30\n"
    "main (k.py:1);_phase_advancement (kernel.py:846);replace (dc.py:3) 60\n"
)
FOLDED_NEW = (
    "# commit: aaa\n# scenario: combat\n"
    "main (k.py:1);_phase_resolution (kernel.py:683);<lambda> (src/engine/pipeline.py:320);work (m.py:5) 50\n"
    "main (k.py:1);_phase_resolution (kernel.py:690);<lambda> (src/engine/pipeline.py:398);other (n.py:9) 30\n"
    "main (k.py:1);_phase_advancement (kernel.py:846);replace (dc.py:3) 20\n"
)


class TestHeader:
    def test_every_header_names_the_required_fields_and_provisional(self):
        fields = common.header_fields("combat", 60, 42, 3, 10, commit="abc")
        for text in (common.comment_header(fields, "T"), common.markdown_header(fields, "T"),
                     "\n".join(common.header_lines(fields, "T"))):
            for needle in ("PROVISIONAL", "abc", "combat", "60", "42", "python", "host_cores", "warmup_ticks", "measured_ticks"):
                assert needle in text, (needle, text)

    def test_metropolis_header_carries_the_known_defect_warning(self):
        assert "TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION" in "\n".join(
            common.header_lines(common.header_fields("metropolis", 10, 1, 1, 1, commit="x"), "T"))
        assert "METROPOLIS" not in "\n".join(common.header_lines(common.header_fields("combat", 10, 1, 1, 1, commit="x"), "T"))

    def test_comment_header_round_trips_provenance(self):
        text = common.comment_header(common.header_fields("combat", 60, 42, 3, 10, commit="abc"), "T") + "a;b 3\n"
        got = common.parse_comment_header(text)
        assert got["commit"] == "abc" and got["scenario"] == "combat" and got["entities"] == "60"

    def test_stamp_html_adds_comment_and_visible_banner(self, tmp_path):
        page = tmp_path / "f.html"
        page.write_text("<!DOCTYPE html>\n<html><body class='x'><p>hi</p></body></html>", encoding="utf-8")
        common.stamp_html(page, common.header_lines(common.header_fields("combat", 1, 1, 1, 1, commit="c"), "T"))
        text = page.read_text(encoding="utf-8")
        assert text.startswith("<!DOCTYPE html>") and text.count("PROVISIONAL") == 2


class TestStatistics:
    def test_mean_p95_spread(self):
        assert common.mean([1, 2, 3]) == 2 and common.mean([]) == 0.0
        assert common.p95(list(range(1, 21))) == 19  # nearest rank: ceil(0.95 * 20) = 19th value
        assert common.p95([5.0]) == 5.0 and common.p95([]) == 0.0
        assert common.spread([3.0, 1.0, 2.0]) == {"min": 1.0, "max": 3.0, "range": 2.0}

    def test_phase_table_means_p95_and_share_of_tick(self):
        rows = common.phase_table([{"a": 10.0, "b": 2.0}, {"a": 30.0}], [20.0, 40.0])
        by = {r["phase"]: r for r in rows}
        assert by["a"]["mean_ms"] == 20.0 and by["a"]["share_of_tick"] == pytest.approx(20.0 / 30.0)
        assert by["b"]["mean_ms"] == 1.0  # a missing phase counts as 0 for that tick
        assert [r["phase"] for r in rows] == ["a", "b"]  # sorted by mean descending


class TestFoldedStacks:
    def test_parse_skips_comments_blank_and_bad_lines_and_sums_duplicates(self):
        got = common.parse_folded("# c\n\na;b 3\na;b 2\nbad line\nc 1\n")
        assert dict(got) == {"a;b": 5, "c": 1}

    def test_filter_keeps_only_stacks_with_the_marker(self):
        kept, kept_n, total = common.filter_stacks({"x;_measured_ticks;y": 4, "setup;z": 6}, "_measured_ticks")
        assert dict(kept) == {"x;_measured_ticks;y": 4} and (kept_n, total) == (4, 10)

    def test_speedscope_is_a_valid_sampled_profile(self):
        doc = common.folded_to_speedscope({"a;b": 3, "a;c": 1}, "n", ["h1", "PROVISIONAL x"])
        prof = doc["profiles"][0]
        frames = doc["shared"]["frames"]
        assert prof["type"] == "sampled" and len(prof["samples"]) == len(prof["weights"]) == 2
        assert prof["endValue"] == 4 and doc["_header"][1].startswith("PROVISIONAL")
        names = [[frames[i]["name"] for i in sample] for sample in prof["samples"]]
        assert names == [["a", "b"], ["a", "c"]]
        assert all(0 <= i < len(frames) for sample in prof["samples"] for i in sample)

    def test_normalize_frame_drops_the_line_except_for_lambdas(self):
        assert common.normalize_frame("f (a/b.py:12)") == "f (a/b.py)"
        assert common.normalize_frame("<lambda> (src/engine/pipeline.py:320)") == "<lambda> (src/engine/pipeline.py:320)"
        assert common.normalize_frame("odd frame") == "odd frame"

    def test_frame_shares_inclusive_counts_a_recursive_frame_once(self):
        shares = common.frame_shares({"r;r;leaf": 5, "r;other": 5})
        assert shares["r"]["inclusive"] == 1.0 and shares["leaf"]["self"] == 0.5 and shares["leaf"]["inclusive"] == 0.5

    def test_diff_reports_grew_and_shrank_with_both_values(self):
        diff = common.diff_shares(common.parse_folded(FOLDED_OLD), common.parse_folded(FOLDED_NEW))
        grew = {r["frame"]: r for r in diff["phases_inclusive"]["grew"]}
        shrank = {r["frame"]: r for r in diff["phases_inclusive"]["shrank"]}
        lam = grew["<lambda> (src/engine/pipeline.py:320)"]
        assert lam["old_inclusive"] == pytest.approx(0.10) and lam["new_inclusive"] == pytest.approx(0.50)
        assert "_phase_advancement (kernel.py)" in shrank  # line stripped so one function is one frame
        assert shrank["_phase_advancement (kernel.py)"]["delta_inclusive"] == pytest.approx(-0.40)
        assert "replace (dc.py)" in {r["frame"] for r in diff["functions_self"]["shrank"]}


class TestAttribution:
    def _run(self, a_costs, b_costs, wall, events):
        return {"per_tick_costs": [{"a": a_costs[0], "b": b_costs[0]}, {"a": a_costs[1], "b": b_costs[1]}],
                "tick_wall_ms": wall, "events": events}

    def test_delta_share_and_spread_arithmetic(self):
        off = [self._run((10, 10), (1, 1), [12, 12], {"x": 4}), self._run((12, 12), (1, 1), [14, 14], {"x": 6})]
        on = [self._run((30, 30), (1, 1), [33, 33], {"x": 14}), self._run((34, 34), (1, 1), [37, 37], {"x": 16})]
        got = common.attribute_flag(off, on)
        rows = {r["phase"]: r for r in got["phases"]}
        assert got["total_delta_ms"] == pytest.approx(22.0)  # (35 - 13)
        assert rows["a"]["off_mean_ms"] == 11.0 and rows["a"]["on_mean_ms"] == 32.0 and rows["a"]["delta_ms"] == 21.0
        assert rows["a"]["share_of_total_delta"] == pytest.approx(21.0 / 22.0)
        assert rows["a"]["off_spread_ms"]["range"] == 2.0 and rows["a"]["on_spread_ms"]["range"] == 4.0
        assert rows["b"]["delta_ms"] == 0.0 and got["phases"][0]["phase"] == "a"  # largest |delta| first
        assert got["events_off"] == {"x": 5.0} and got["events_on"] == {"x": 15.0}
        assert got["repetitions"] == {"off": 2, "on": 2}

    def test_zero_total_delta_gives_zero_shares_not_a_division_error(self):
        run = self._run((5, 5), (1, 1), [6, 6], {})
        got = common.attribute_flag([run], [run])
        assert all(r["share_of_total_delta"] == 0.0 for r in got["phases"])

    def test_markdown_render_has_header_table_and_events(self):
        run_off = self._run((10, 10), (1, 1), [12, 12], {"x": 4})
        run_on = self._run((30, 30), (1, 1), [33, 33], {"x": 14})
        result = common.attribute_flag([run_off], [run_on])
        result["modes"] = {"off": [["NORMAL"]], "on": [["NORMAL", "CONSTRAINED"]]}
        text = flag_attribution.render_markdown(
            result, common.header_fields("combat", 60, 42, 3, 10, commit="c"), "ENABLE_X",
            {"off": {"manager": "OFF"}, "on": {"manager": "ON"}})
        assert "PROVISIONAL" in text and "Share of total delta" in text and "| x |" in text
        assert "WARNING: a run left RuntimeMode NORMAL" in text

    def test_distinct_sequences_dedupes_across_runs(self):
        runs = [{"runtime_mode_sequence": ["NORMAL"]}, {"runtime_mode_sequence": ["NORMAL"]},
                {"runtime_mode_sequence": ["NORMAL", "CONSTRAINED"]}]
        assert flag_attribution.distinct_sequences(runs) == [["NORMAL"], ["NORMAL", "CONSTRAINED"]]

    def test_summarize_ticks_collapses_the_mode_sequence(self):
        data = {"ticks": [{"wall_ms": 1.0, "costs": {"a": 1.0}, "mode": m, "work": {"phase_runs": 3}, "events": 0}
                          for m in ("NORMAL", "NORMAL", "DEGRADED")], "events": {"e": 2}}
        s = common.summarize_ticks(data)
        assert s["runtime_mode_sequence"] == ["NORMAL", "DEGRADED"] and s["work_mean_per_tick"] == {"phase_runs": 3.0}


class TestBinaryHandling:
    def test_missing_binary_message_names_the_install_command_and_forbids_substitution(self):
        msg = common.missing_binary_message("py-spy")
        assert 'pip install -e ".[perf]"' in msg and "No substitute profiler" in msg
        assert "[dev]" in common.missing_binary_message("memray")

    def test_find_binary_explicit_env_and_absent(self, tmp_path, monkeypatch):
        fake = tmp_path / "py-spy"
        fake.write_text("#!/bin/sh\n")
        assert common.find_binary("py-spy", str(fake)) == str(fake)
        assert common.find_binary("py-spy", str(tmp_path / "nope")) is None
        monkeypatch.setenv("PY_SPY", str(fake))
        assert common.find_binary("py-spy") == str(fake)
        monkeypatch.delenv("PY_SPY")
        monkeypatch.setenv("PATH", str(tmp_path / "empty"))
        assert common.find_binary("py-spy") is None

    def test_profile_tick_exits_2_with_the_message_when_the_binary_is_absent(self, tmp_path):
        done = subprocess.run([sys.executable, str(PERF / "profile_tick.py"), "--scenario", "idle",
                               "--py-spy", str(tmp_path / "absent"), "--out-dir", str(tmp_path / "o")],
                              capture_output=True, text=True, cwd=REPO_ROOT)
        assert done.returncode == 2 and 'pip install -e ".[perf]"' in done.stderr
        assert not (tmp_path / "o").exists()  # nothing is written when the profiler is missing

    def test_metropolis_selection_prints_the_known_defect_warning(self, tmp_path):
        done = subprocess.run([sys.executable, str(PERF / "profile_tick.py"), "--scenario", "metropolis",
                               "--py-spy", str(tmp_path / "absent")], capture_output=True, text=True, cwd=REPO_ROOT)
        assert "TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION" in done.stderr

    def test_flag_attribution_warns_for_metropolis_before_running(self, tmp_path):
        done = subprocess.run([sys.executable, str(PERF / "flag_attribution.py"), "--flag", "ENABLE_NOPE",
                               "--scenario", "metropolis", "--reps", "0"], capture_output=True, text=True, cwd=REPO_ROOT)
        assert "TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION" in done.stderr


class TestProfileDiffCli:
    def _files(self, tmp_path, old=FOLDED_OLD, new=FOLDED_NEW):
        a, b = tmp_path / "old.folded", tmp_path / "new.folded"
        a.write_text(old, encoding="utf-8")
        b.write_text(new, encoding="utf-8")
        return a, b

    def test_markdown_output_lists_growth_with_both_shares_and_the_header(self, tmp_path):
        a, b = self._files(tmp_path)
        done = subprocess.run([sys.executable, str(PERF / "profile_diff.py"), str(a), str(b)],
                              capture_output=True, text=True, cwd=REPO_ROOT)
        assert done.returncode == 0, done.stderr
        assert "PROVISIONAL" in done.stdout and "pipeline.py:320" in done.stdout
        assert "10.00%" in done.stdout and "50.00%" in done.stdout and "+40.00 pts" in done.stdout

    def test_json_output_and_commit_mismatch_warning(self, tmp_path):
        a, b = self._files(tmp_path, new=FOLDED_NEW.replace("commit: aaa", "commit: bbb"))
        done = subprocess.run([sys.executable, str(PERF / "profile_diff.py"), str(a), str(b), "--format", "json"],
                              capture_output=True, text=True, cwd=REPO_ROOT)
        data = json.loads(done.stdout)
        assert any("different commits" in w for w in data["warnings"]) and data["header"][1].startswith("PROVISIONAL")

    def test_unreadable_and_empty_inputs_exit_2(self, tmp_path):
        a, _ = self._files(tmp_path)
        bad = subprocess.run([sys.executable, str(PERF / "profile_diff.py"), str(a), str(tmp_path / "x")],
                             capture_output=True, text=True, cwd=REPO_ROOT)
        empty = tmp_path / "empty.folded"
        empty.write_text("# only a header\n", encoding="utf-8")
        none = subprocess.run([sys.executable, str(PERF / "profile_diff.py"), str(a), str(empty)],
                              capture_output=True, text=True, cwd=REPO_ROOT)
        assert bad.returncode == 2 and none.returncode == 2

    def test_build_diff_warns_when_provenance_is_missing(self):
        diff = profile_diff.build_diff("a 1\n", "a 2\n")
        assert any("no PROVISIONAL header" in w for w in diff["warnings"])


class TestFlagOverride:
    def test_override_builds_a_new_state_and_sets_both_mechanisms(self, monkeypatch):
        import dataclasses

        from src.domains.optimization import feature_flags as ff

        monkeypatch.setattr(ff.FeatureFlagManager, "get_flag_mode", ff.FeatureFlagManager.get_flag_mode)  # restored after

        @dataclasses.dataclass(frozen=True)
        class FrozenState:
            feature_flags: dict

        state = FrozenState({"OTHER": "ON"})
        new_state, seen = common.apply_flag_override(state, "ENABLE_COMBAT_ENGAGEMENT", "OFF")
        assert seen == {"manager": "OFF", "state": "OFF"}
        assert new_state is not state and state.feature_flags == {"OTHER": "ON"}  # original untouched
        assert new_state.feature_flags == {"OTHER": "ON", "ENABLE_COMBAT_ENGAGEMENT": "OFF"}
        assert ff.FeatureFlagManager().get_flag_mode("ENABLE_BELIEF_ASSIMILATION").value == "ON"  # others untouched
        with pytest.raises(ValueError):
            common.apply_flag_override(state, "ENABLE_COMBAT_ENGAGEMENT", "MAYBE")
        with pytest.raises(ValueError):
            common.apply_flag_override(state, "ENABLE_NO_SUCH_FLAG", "ON")

    def test_real_authoritative_state_is_replaced_not_written_through(self, monkeypatch):
        from src.domains.optimization import feature_flags as ff

        monkeypatch.setattr(ff.FeatureFlagManager, "get_flag_mode", ff.FeatureFlagManager.get_flag_mode)
        state = common.build_state("idle", 5)
        before = dict(state.feature_flags)
        new_state, seen = common.apply_flag_override(state, "ENABLE_COMBAT_ENGAGEMENT", "OFF")
        assert new_state is not state and state.feature_flags == before
        assert new_state.feature_flags["ENABLE_COMBAT_ENGAGEMENT"] == "OFF" and seen["state"] == "OFF"
        assert len(new_state.entities) == len(state.entities)


class TestReportRendering:
    def test_phase_report_has_header_context_and_warns_off_normal(self):
        fields = common.header_fields("combat", 60, 42, 3, 10, commit="c")
        summary = {"runtime_mode_sequence": ["DEGRADED"], "work_mean_per_tick": {"phase_runs": 30.0},
                   "events": {"e": 3}, "tick_wall_ms": [10.0, 20.0]}
        rows = common.phase_table([{"a": 5.0}, {"a": 15.0}], [10.0, 20.0])
        text = profile_tick.render_phase_report(fields, summary, rows, "py-spy at 100 Hz")
        assert "PROVISIONAL" in text and "phase_runs=30.0" in text and "WARNING: the RuntimeMode left NORMAL" in text
        assert "| a | 10.000 | 15.000 |" in text


@pytest.mark.skipif(shutil.which("py-spy") is None, reason="py-spy is not installed (optional `perf` group)")
def test_end_to_end_tiny_profile_with_py_spy(tmp_path):
    done = subprocess.run([sys.executable, str(PERF / "profile_tick.py"), "--scenario", "idle", "--entities", "20",
                           "--ticks", "4", "--warmup", "1", "--out-dir", str(tmp_path)],
                          capture_output=True, text=True, cwd=REPO_ROOT, timeout=240)
    assert done.returncode == 0, done.stderr
    for name in ("profile.folded", "profile.speedscope.json", "phases.md", "phases.json"):
        assert "PROVISIONAL" in (tmp_path / name).read_text(encoding="utf-8")

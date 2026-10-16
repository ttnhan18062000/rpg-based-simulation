"""The paired measurement tool's arithmetic and refusals, on staged runs (no simulation): the people set is the base arm's tick-0 roster read on
the same ids in both arms, SE and the drift verdict, the extinction check, the self-check spread and the host-independence refusal."""
from __future__ import annotations

import pytest

from src.observability.reporting.run_determinism import NonAuditRunError
from tools.rpg_measure import paired, stats


def _run(world="w", seed=42, start=(), final=None, counters=None, final_hash="h", start_hash="s"):
    """start rows: (id, kind, keeps_coin); final: id -> (alive, cause, kind)."""
    rows = [[i, k, c, 1] for i, k, c in start]
    fin = {str(i): list(v) for i, v in (final or {}).items()}
    return {"world": world, "seed": seed, "start": rows, "final": fin, "counters": counters, "perception_samples": 5, "final_hash": final_hash, "start_hash": start_hash,
            "audit_mode": True, "signals_zeroed": True, "adds": {}}


START = [(1, "merchant", 1), (2, "guard", 1), (3, "wolf", 0)]


def test_people_are_the_base_tick_zero_keeps_coin_roster_read_on_the_same_ids_in_both_arms():
    base = _run(start=START, final={1: (0, "COMBAT", "merchant"), 2: (1, None, "guard"), 3: (0, "COMBAT", "wolf")})
    # in the new arm the wolf's species now keeps coin and is listed as a person there: the people set must not grow
    new = _run(start=[(1, "merchant", 1), (2, "guard", 1), (3, "wolf", 1)], final={1: (0, "COMBAT", "merchant"), 2: (0, "COMBAT", "guard"), 3: (0, "COMBAT", "wolf")})
    ids = stats.people_ids(base["start"])
    assert ids == {"1", "2"}
    assert stats.people_deaths(base, ids) == 1 and stats.people_deaths(new, ids) == 2
    assert stats.roster_mismatch(base["start"], new["start"])["changed"] == ["3"]


def test_an_entity_missing_from_the_final_state_counts_as_dead_and_a_late_id_is_added_not_a_person():
    run = _run(start=START, final={1: (1, None, "merchant"), 9: (1, None, "merchant")})
    assert stats.is_dead(run, "2") and not stats.is_dead(run, "1")
    assert stats.added(run) == ["9"]
    assert stats.people_deaths(run, stats.people_ids(run["start"])) == 1


def test_standard_error_is_the_sd_of_the_per_seed_difference_over_root_n():
    diffs = [2.0, 4.0, 6.0, 8.0, 10.0]
    sd = (sum((d - 6.0) ** 2 for d in diffs) / 4) ** 0.5
    assert stats.standard_error(diffs) == pytest.approx(sd / 5 ** 0.5)
    assert stats.standard_error([3.0]) == 0.0


def test_more_deaths_past_two_se_and_the_floor_stop_and_fewer_is_report_only():
    assert stats.verdict([5.0, 5.0, 5.0, 6.0, 4.0]) == stats.STOP
    assert stats.verdict([-5.0, -5.0, -5.0, -6.0, -4.0]) == stats.REPORT_ONLY
    assert stats.verdict([5.0, 5.0, 5.0, 6.0, 4.0], floor_per_seed=5.0) == ""
    assert stats.verdict([4.0, -3.0, 5.0, -4.0, 1.0]) == ""


def test_with_zero_spread_the_floor_is_the_only_guard():
    assert stats.verdict([1.0] * 5) == ""
    assert stats.verdict([2.0] * 5) == stats.STOP
    assert stats.verdict([0.0] * 5) == ""


def test_extinction_stop_only_when_extinct_in_every_new_seed_and_not_in_the_base():
    def runs(alive_by_seed):
        return [_run(seed=s, start=[(1, "scout", 1)], final={1: (a, None, "scout")}) for s, a in enumerate(alive_by_seed)]
    assert stats.extinction_verdict(runs([1, 0, 1]), runs([0, 0, 0])) == {"stop": ["scout"], "base_state": [], "recovered": []}
    assert stats.extinction_verdict(runs([0, 0, 0]), runs([0, 0, 0]))["base_state"] == ["scout"]
    assert stats.extinction_verdict(runs([1, 1, 1]), runs([0, 0, 1]))["stop"] == []


def test_self_check_names_every_pair_that_is_not_byte_identical():
    a = _run(seed=42, final={1: (1, None, "x")})
    assert stats.self_check_spread([a], [dict(a)]) == []
    assert stats.self_check_spread([a], [dict(a, final_hash="other")]) == ["w:42"]


def test_a_run_without_signals_zeroed_is_refused_and_named():
    good, bad = _run(), dict(_run(), signals_zeroed=None)
    paired.refuse_non_audit("base", {("w", 42): good})
    with pytest.raises(NonAuditRunError, match="base:w:43"):
        paired.refuse_non_audit("base", {("w", 42): good, ("w", 43): bad})
    with pytest.raises(NonAuditRunError, match="audit_mode"):
        paired.refuse_non_audit("new", {("w", 42): dict(good, audit_mode=False)})


def test_the_world_section_reports_per_seed_people_deaths_the_verdict_and_the_watch_row():
    def pair(seed, new_dead):
        base = _run(seed=seed, start=START, final={1: (1, None, "merchant"), 2: (1, None, "guard"), 3: (1, None, "wolf")})
        new_final = {1: (0 if new_dead >= 1 else 1, "COMBAT", "merchant"), 2: (0 if new_dead >= 2 else 1, "COMBAT", "guard"), 3: (1, None, "wolf")}
        return base, _run(seed=seed, start=START, final=new_final)
    pairs = [pair(s, d) for s, d in zip(range(42, 47), [1, 1, 1, 2, 1])]
    lines, row = paired.world_section("w", [p[0] for p in pairs], [p[1] for p in pairs], 0.0, None)
    text = "\n".join(lines)
    assert row["people_base"] == 0 and row["people_new"] == 6 and row["delta"] == 6 and row["verdict"] == "STOP"
    assert "base [0, 0, 0, 0, 0] -> new [1, 1, 1, 2, 1]" in text
    assert "n/a (an arm tree predates the ledger counters)" in text
    assert "| step | 2.1 | w | 0->6 | +6 (STOP) |" in "\n".join(paired.watch_rows("step", "2.1", [row]))


def test_results_are_cached_by_commit_and_the_repeat_arm_has_its_own_directory(tmp_path):
    a = paired.result_path(tmp_path, "a" * 40, 5000, "w", 42)
    assert a == paired.result_path(tmp_path, "a" * 40, 5000, "w", 42)
    assert a != paired.result_path(tmp_path, "b" * 40, 5000, "w", 42)
    assert a != paired.result_path(tmp_path, "a" * 40, 5000, "w", 42, repeat=True)


def test_an_arm_already_in_the_cache_is_not_run_again_and_a_repeat_always_is(tmp_path, monkeypatch):
    calls = []

    def fake(tree, world, seed, ticks, out):
        calls.append((world, seed))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text('{"world": "%s", "seed": %d}' % (world, seed), encoding="utf-8")

    monkeypatch.setattr(paired, "run_one", fake)
    jobs = [("w", 42), ("w", 43)]
    paired.run_arm(tmp_path, tmp_path, "c" * 40, jobs, 10, 1)
    paired.run_arm(tmp_path, tmp_path, "c" * 40, jobs, 10, 1)
    assert calls == jobs
    paired.run_arm(tmp_path, tmp_path, "c" * 40, jobs, 10, 1, repeat=True)
    paired.run_arm(tmp_path, tmp_path, "c" * 40, jobs, 10, 1, repeat=True)
    assert len(calls) == 6


def test_a_legacy_base_is_accepted_only_when_its_kernel_was_forced_and_it_never_recorded_live_signals():
    forced = {"audit_mode": True, "no_frame_pacing": True}
    old = dict(_run(), signals_zeroed=None, audit_mode=None, forced_flags=forced)
    paired.refuse_non_audit("base", {("w", 42): old}, legacy=True)
    with pytest.raises(NonAuditRunError):
        paired.refuse_non_audit("base", {("w", 42): old})  # strict mode still refuses it
    with pytest.raises(NonAuditRunError, match="base:w:43"):
        paired.refuse_non_audit("base", {("w", 42): old, ("w", 43): dict(old, signals_zeroed=False)}, legacy=True)
    with pytest.raises(NonAuditRunError, match="base:w:44"):
        paired.refuse_non_audit("base", {("w", 44): dict(old, forced_flags={"audit_mode": True, "no_frame_pacing": False})}, legacy=True)
    with pytest.raises(NonAuditRunError, match="base:w:45"):
        paired.refuse_non_audit("base", {("w", 45): dict(old, forced_flags=None)}, legacy=True)


def test_a_report_only_reading_never_says_stop_and_still_names_the_drift():
    def pair(seed, d):
        base = _run(seed=seed, start=START, final={1: (1, None, "merchant"), 2: (1, None, "guard"), 3: (1, None, "wolf")})
        return base, _run(seed=seed, start=START, final={1: (0 if d >= 1 else 1, "COMBAT", "merchant"), 2: (0 if d >= 2 else 1, "COMBAT", "guard"), 3: (1, None, "wolf")})
    pairs = [pair(s, d) for s, d in zip(range(42, 47), [2, 2, 2, 2, 2])]
    stop_lines, stop_row = paired.world_section("w", [p[0] for p in pairs], [p[1] for p in pairs], 1.0, None)
    ro_lines, ro_row = paired.world_section("w", [p[0] for p in pairs], [p[1] for p in pairs], 1.0, None, report_only=True)
    assert stop_row["verdict"] == "STOP" and ro_row["verdict"] == "REPORT-ONLY"
    assert "STOP" not in "\n".join(paired.watch_rows("s", "d", [ro_row], True)).replace("never trips a stop", "")
    assert "REPORT-ONLY reading" in "\n".join(paired.watch_rows("s", "d", [ro_row], True))

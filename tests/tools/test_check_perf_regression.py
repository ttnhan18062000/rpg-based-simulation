"""Tests for tools/perf/check_perf_regression.py and the perf_ci.py exit-2 handling
(TCK-20261004-PERF-REGRESSION-CHECK-NO-SILENT-PASS).

Baseline and report directories are built under tmp_path; no benchmark is ever run and
subprocess.run is patched for perf_ci.
"""
import json
from types import SimpleNamespace

import pytest

from tools.perf import check_perf_regression as cpr
from tools.perf import perf_ci


def _record(profile="PERF_512MB_LOCAL", sample_ticks=20, avg=2.0, rss=100.0, **extra):
    rec = {
        "profile": profile,
        "sample_ticks": sample_ticks,
        "tick_ms": {"avg": avg, "p95": avg},
        "mem_rss_mb": {"max": rss},
        "phase_breakdown": {},
    }
    rec.update(extra)
    return rec


@pytest.fixture
def dirs(tmp_path):
    b, r = tmp_path / "baselines", tmp_path / "reports"
    b.mkdir()
    r.mkdir()
    return b, r


def _put(directory, name, record):
    (directory / f"{name}.json").write_text(json.dumps(record))


def _run(dirs):
    return cpr.check_regression(baseline_dir=dirs[0], report_dir=dirs[1])


def test_all_matching_and_stable_exits_zero(dirs, capsys, caplog):
    _put(dirs[0], "idle", _record())
    _put(dirs[1], "idle", _record(avg=2.1))
    with caplog.at_level("INFO"):
        assert _run(dirs) == 0
    assert "1 compared, 0 not comparable, 0 regressions" in capsys.readouterr().out
    assert "PASSED" in caplog.text


def test_a_regression_exits_one(dirs):
    _put(dirs[0], "idle", _record(avg=10.0))
    _put(dirs[1], "idle", _record(avg=20.0))
    assert _run(dirs) == 1


def test_regression_wins_over_not_comparable(dirs):
    _put(dirs[0], "a", _record(avg=10.0))
    _put(dirs[1], "a", _record(avg=20.0))
    _put(dirs[0], "b", _record())  # no report
    assert _run(dirs) == 1


def test_memory_regression_still_detected(dirs):
    _put(dirs[0], "idle", _record(rss=100.0))
    _put(dirs[1], "idle", _record(rss=130.0))
    assert _run(dirs) == 1


def test_sample_ticks_mismatch_exits_two_and_names_the_field(dirs, capsys):
    _put(dirs[0], "idle", _record(sample_ticks=20))
    _put(dirs[1], "idle", _record(sample_ticks=50))
    assert _run(dirs) == 2
    out = capsys.readouterr().out
    assert "sample_ticks differs" in out and "baseline=20" in out and "report=50" in out


def test_profile_mismatch_exits_two_and_names_the_field(dirs, capsys):
    _put(dirs[0], "idle", _record(profile="PERF_512MB_LOCAL"))
    _put(dirs[1], "idle", _record(profile="PROD_DEFAULT"))
    assert _run(dirs) == 2
    assert "profile differs" in capsys.readouterr().out


def test_a_mismatched_scenario_is_not_compared_even_if_it_would_regress(dirs):
    _put(dirs[0], "idle", _record(sample_ticks=20, avg=1.0))
    _put(dirs[1], "idle", _record(sample_ticks=50, avg=100.0))
    assert _run(dirs) == 2  # not 1: it was never compared


def test_warmup_is_checked_only_when_both_carry_it(dirs):
    _put(dirs[0], "a", _record(warmup_ticks=10))
    _put(dirs[1], "a", _record())
    assert _run(dirs) == 0
    _put(dirs[1], "a", _record(warmup_ticks=50))
    assert _run(dirs) == 2


def test_missing_report_exits_two(dirs, capsys):
    _put(dirs[0], "idle", _record())
    assert _run(dirs) == 2
    assert "no report" in capsys.readouterr().out


def test_one_missing_report_among_good_ones_is_not_a_pass(dirs):
    for name in ("a", "b"):
        _put(dirs[0], name, _record())
    _put(dirs[1], "a", _record())
    assert _run(dirs) == 2


def test_zero_baselines_exits_two(dirs):
    _put(dirs[1], "idle", _record())  # reports exist, baselines do not
    assert _run(dirs) == 2


def test_missing_baseline_directory_exits_two(tmp_path):
    assert cpr.check_regression(baseline_dir=tmp_path / "nope", report_dir=tmp_path) == 2


@pytest.mark.parametrize("which", ["baseline", "report"])
@pytest.mark.parametrize("drop", ["tick_ms", "mem_rss_mb", "avg", "max", "profile", "sample_ticks"])
def test_a_missing_key_exits_two_not_an_exception(dirs, which, drop):
    base, rep = _record(), _record()
    target = base if which == "baseline" else rep
    if drop == "avg":
        target["tick_ms"] = {"p95": 1.0}
    elif drop == "max":
        target["mem_rss_mb"] = {}
    else:
        del target[drop]
    _put(dirs[0], "idle", base)
    _put(dirs[1], "idle", rep)
    assert _run(dirs) == 2


def test_unparseable_or_non_object_files_exit_two(dirs):
    (dirs[0] / "idle.json").write_text(json.dumps(_record()))
    (dirs[1] / "idle.json").write_text("{broken")
    assert _run(dirs) == 2
    (dirs[1] / "idle.json").write_text("[]")
    assert _run(dirs) == 2


def test_never_passes_when_nothing_was_compared(dirs, caplog):
    _put(dirs[0], "idle", _record(profile="A"))
    _put(dirs[1], "idle", _record(profile="B"))
    with caplog.at_level("INFO"):
        assert _run(dirs) != 0
    assert "PASSED" not in caplog.text


def test_thresholds_are_unchanged():
    assert (cpr.RELATIVE_THRESHOLD, cpr.ABSOLUTE_THRESHOLD_MS, cpr.MEMORY_RSS_LIMIT_MB) == (1.15, 3.0, 20.0)


@pytest.mark.parametrize(
    ("returncode", "expected", "message"),
    [(0, True, None), (1, False, "failed"), (2, False, "not comparable")],
)
def test_perf_ci_reports_exit_two_as_not_comparable(monkeypatch, caplog, returncode, expected, message):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0 if "run_benchmarks" in cmd[1] else returncode)

    monkeypatch.setattr(perf_ci.subprocess, "run", fake_run)
    with caplog.at_level("INFO"):
        assert perf_ci.run_ci_gate() is expected
    assert len(calls) == 2
    if message:
        assert message in caplog.text

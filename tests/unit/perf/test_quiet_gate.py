from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import pytest

from tests.unit.perf.test_benchmark_record import make_record
from tools.perf import quiet_gate as qg, rerun_baselines as rr

REAL_RUN = subprocess.run
CAUSE = "TCK-20261014-PERF-UNIT-CAUSE"
HOST = {c: (0, 1000) for c in range(6)}


def jiff(busy: Dict[int, int], total: int = 1000) -> qg.CpuJiffies:
    return {c: (busy.get(c, 0), total) for c in range(6)}


def reading(load: float = 0.3, avail: float = 5000.0, **extra: Any) -> Dict[str, Any]:
    return {"loadavg_1min": load, "available_mb": avail, **extra}


def gate(busy_cpu4: int = 0, swap=(0, 0), affinity=frozenset({4, 5}), base=None, host_after=None) -> Dict[str, Any]:
    calls = iter([jiff({}, 1000), jiff({4: busy_cpu4}, 2000)])
    swaps = iter([(10, 20), (10 + swap[0], 20 + swap[1])])
    return qg.gate_read(lambda: base or reading(), sleep=lambda s: None, stat=lambda: next(calls), vmstat=lambda: next(swaps), affinity=lambda: set(affinity) if affinity else None)


def test_a_pinned_run_is_gated_on_the_busy_fraction_of_its_own_cpus_not_on_the_load_average() -> None:
    ok, text = qg.evaluate(gate(busy_cpu4=500, base=reading(load=0.1)), 1.5, 3000.0)
    assert not ok and "allowed-CPU busy" in text and "loadavg1 >=" not in text
    assert qg.evaluate(gate(busy_cpu4=90, base=reading(load=9.0)), 1.5, 3000.0)[0]  # 9 % busy passes at a host load of 9: the load average is not looked at when pinned


def test_the_busy_fraction_bound_is_strict_below_ten_percent() -> None:
    assert qg.evaluate(gate(busy_cpu4=99), 1.5, 3000.0)[0] and not qg.evaluate(gate(busy_cpu4=100), 1.5, 3000.0)[0]


def test_an_unpinned_process_keeps_the_load_rule() -> None:
    unpinned = frozenset(range(6))
    assert qg.evaluate(gate(affinity=unpinned, base=reading(load=1.49)), 1.5, 3000.0)[0]
    ok, text = qg.evaluate(gate(affinity=unpinned, base=reading(load=1.5)), 1.5, 3000.0)
    assert not ok and "loadavg1 >= 1.5" in text
    assert gate(affinity=unpinned)["busy_pct"] is None and gate(affinity=None)["pinned"] is None


def test_memory_below_three_gb_fails_whatever_the_cpus_do() -> None:
    assert qg.evaluate(gate(base=reading(avail=3000.0)), 1.5, 3000.0)[0]
    ok, text = qg.evaluate(gate(base=reading(avail=2999.0)), 1.5, 3000.0)
    assert not ok and "available memory" in text
    assert qg.evaluate(reading(avail=None, **{"busy_pct": None}), 1.5, 3000.0)[0]  # unreadable memory is not a reason to refuse


@pytest.mark.parametrize("swap", [(1, 0), (0, 7)])
def test_any_swap_activity_over_the_sample_fails(swap) -> None:
    ok, text = qg.evaluate(gate(swap=swap), 1.5, 3000.0)
    assert not ok and "swap activity" in text
    assert qg.evaluate(gate(swap=(0, 0)), 1.5, 3000.0)[0]


def test_the_readers_parse_proc_files(tmp_path: Path) -> None:
    stat = tmp_path / "stat"
    stat.write_text("cpu  1 1 1 1 1 1 1 1 0 0\ncpu4 100 10 30 500 50 5 5 2 0 0\ncpu5 0 0 0 10 0 0 0 0 0 0\nintr 1\n", encoding="utf-8")
    jiffies = qg.read_cpu_jiffies(str(stat))
    assert jiffies[4] == (100 + 10 + 30 + 5 + 5 + 2, 100 + 10 + 30 + 500 + 50 + 5 + 5 + 2) and jiffies[5] == (0, 10) and "cpu" not in jiffies
    vm = tmp_path / "vmstat"
    vm.write_text("nr_free 1\npswpin 12\npswpout 34\n", encoding="utf-8")
    assert qg.read_swap_counters(str(vm)) == (12, 34) and qg.read_swap_counters(str(tmp_path / "none")) is None
    with pytest.raises(qg.GateError):
        qg.read_cpu_jiffies(str(tmp_path / "none"))


def test_the_own_cgroup_time_is_read_from_the_scope_named_in_proc_self_cgroup(tmp_path: Path) -> None:
    scope = tmp_path / "root" / "user.slice" / "run-x.scope"
    scope.mkdir(parents=True)
    (scope / "cpu.stat").write_text("usage_usec 4200000\nuser_usec 1\n", encoding="utf-8")
    proc = tmp_path / "cgroup"
    proc.write_text("0::/user.slice/run-x.scope\n", encoding="utf-8")
    assert qg.read_own_cgroup_usec(str(proc), str(tmp_path / "root")) == 4_200_000
    for bad in (str(tmp_path / "missing"),):
        with pytest.raises(qg.GateError):
            qg.read_own_cgroup_usec(bad, str(tmp_path / "root"))
    proc.write_text("0::/user.slice/other.scope\n", encoding="utf-8")
    with pytest.raises(qg.GateError):
        qg.read_own_cgroup_usec(str(proc), str(tmp_path / "root"))


def watch(busy_seconds_each: float, own_usec: int, wall: float, affinity=frozenset({4, 5})) -> qg.RunWatch:
    stats = iter([jiff({}), jiff({4: int(busy_seconds_each * 100), 5: int(busy_seconds_each * 100)})])
    usecs = iter([1_000_000, 1_000_000 + own_usec])
    clock = iter([100.0, 100.0 + wall])
    return qg.RunWatch(stat=lambda: next(stats), cgroup_usec=lambda: next(usecs), affinity=lambda: set(affinity), clock=lambda: next(clock))


def test_the_foreign_share_is_busy_minus_own_over_allowed_cpu_seconds() -> None:
    w = watch(busy_seconds_each=10.0, own_usec=18_000_000, wall=10.0)  # 20 s busy, 18 s own, 2 CPUs x 10 s
    w.start()
    assert w.finish() == pytest.approx(0.10, abs=1e-4)


def test_the_foreign_share_is_clamped_at_zero() -> None:
    w = watch(busy_seconds_each=5.0, own_usec=12_000_000, wall=10.0)
    w.start()
    assert w.finish() == 0.0


def test_an_unpinned_process_skips_the_in_run_check_and_reads_no_cgroup() -> None:
    w = qg.RunWatch(stat=lambda: HOST, cgroup_usec=lambda: pytest.fail("no cgroup read when unpinned"), affinity=lambda: set(range(6)))
    w.start()
    assert w.finish() is None


def test_a_pinned_process_with_an_unreadable_cgroup_refuses_rather_than_skips() -> None:
    def unreadable() -> int:
        raise qg.GateError("no cpu.stat")

    w = qg.RunWatch(stat=lambda: HOST, cgroup_usec=unreadable, affinity=lambda: {4, 5})
    with pytest.raises(qg.GateError):
        w.start()


class FakeWatch:
    def __init__(self, shares: List[float], fail_start: bool = False) -> None:
        self._shares, self._fail = shares, fail_start

    def start(self) -> None:
        if self._fail:
            raise qg.GateError("no cpu.stat")

    def finish(self):
        return self._shares.pop(0)


def _drive(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, watch_obj: FakeWatch) -> int:
    monkeypatch.setattr(rr, "wait_for_quiet_window", lambda *a, **k: (True, "quiet"))
    monkeypatch.setattr(rr, "new_run_watch", lambda: watch_obj)

    def fake_run(argv, env=None, check=False, **kw):
        if "--out" not in argv:
            return REAL_RUN(argv, env=env, check=check, **kw)
        out = Path(argv[argv.index("--out") + 1])
        out.write_text(json.dumps(make_record(avg=40.0).to_dict()), encoding="utf-8")
        out.with_suffix(".meta.json").write_text(json.dumps({"loadavg_1min": 0.5, "swap_used_mb": 0.0, "wall_s": 1.0, "peak_rss_mb": 90.0}), encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(rr.subprocess, "run", fake_run)
    return rr.cmd_record("resource_100_local", tmp_path, CAUSE)


def test_a_pinned_series_under_the_foreign_share_threshold_completes_and_records_each_share(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    assert _drive(monkeypatch, tmp_path, FakeWatch([0.0, 0.04, 0.099])) == 0
    summary = json.loads((tmp_path / "resource_100_local" / "summary.json").read_text(encoding="utf-8"))
    assert [g["foreign_share"] for g in summary["gates"]] == [0.0, 0.04, 0.099] and summary["cpu_affinity"]


def test_a_foreign_share_of_ten_percent_stops_the_series_and_writes_no_candidate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    assert _drive(monkeypatch, tmp_path, FakeWatch([0.0, 0.10, 0.0])) == 1
    err = capsys.readouterr().err
    assert "run 2" in err and "10.0 %" in err and "no candidate" in err
    assert not (tmp_path / "resource_100_local" / "candidate.json").exists()


def test_a_pinned_series_whose_cgroup_cannot_be_read_is_refused_before_any_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    monkeypatch.setattr(rr.subprocess, "run", lambda *a, **k: pytest.fail("nothing may start"))
    monkeypatch.setattr(rr, "wait_for_quiet_window", lambda *a, **k: (True, "quiet"))
    monkeypatch.setattr(rr, "new_run_watch", lambda: FakeWatch([], fail_start=True))
    assert rr.cmd_record("resource_100_local", tmp_path, CAUSE) == 1
    assert "cannot be taken" in capsys.readouterr().err and not (tmp_path / "resource_100_local" / "candidate.json").exists()


def test_a_gate_failure_names_the_failed_check_and_stops_the_series(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    results = iter([(True, "ok"), (False, "swap in+out pages 3 [FAILED: swap activity (pswpin/pswpout moved)]")])
    monkeypatch.setattr(rr, "wait_for_quiet_window", lambda *a, **k: next(results))
    monkeypatch.setattr(rr, "new_run_watch", lambda: FakeWatch([0.0]))

    def fake_run(argv, env=None, check=False, **kw):
        if "--out" not in argv:
            return REAL_RUN(argv, env=env, check=check, **kw)
        out = Path(argv[argv.index("--out") + 1])
        out.write_text(json.dumps(make_record(avg=40.0).to_dict()), encoding="utf-8")
        out.with_suffix(".meta.json").write_text(json.dumps({"loadavg_1min": 0.5, "swap_used_mb": 0.0, "wall_s": 1.0, "peak_rss_mb": 90.0}), encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(rr.subprocess, "run", fake_run)
    assert rr.cmd_record("resource_100_local", tmp_path, CAUSE) == 1
    assert "swap activity" in capsys.readouterr().err and not (tmp_path / "resource_100_local" / "candidate.json").exists()

"""The harness's after-collect memory readings and the declared-memory ratio (TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE).

The harness is driven with a fake kernel, so no engine tick runs: the collector's state, the order of the clock reads and the collect, and the memory
readings are the things under test.
"""
from __future__ import annotations

import dataclasses
import gc
import mmap
from types import SimpleNamespace
from typing import Any, List

import pytest

from src.perf import bench_harness
from src.perf.bench_harness import BenchHarness
from src.perf.benchmark_record import SCHEMA_VERSION, BenchmarkRecord, OutcomeState, Thresholds, compare
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_idle_state
from tests.unit.perf.test_benchmark_record import make_record
from tools.perf import baseline_lifecycle, tripwire

PROFILE = PERF_PROFILES["PERF_512MB_LOCAL"]
LEGACY_KEYS = {"rss_high_water", "rss_delta", "sample_every_ticks"}
NEW_KEYS = {
    "rss_before_window_mb", "rss_after_collect_mb", "rss_after_trim_mb", "rss_trim_delta_mb", "allocated_blocks_delta", "gc_collected_objects",
    "gc_collect_s", "declared_ram_mb", "rss_over_declared", "rss_over_declared_basis_trim", "peak_rss_over_declared",
}
TRIM_KEYS = {"rss_after_trim_mb", "rss_trim_delta_mb"}


class _Cycle:
    """A reference cycle that owns real pages (an ``mmap`` is unmapped, so RSS falls, when it is freed)."""

    def __init__(self, size: int) -> None:
        self.me = self
        self.pages = mmap.mmap(-1, size)
        self.pages.write(b"x" * size)  # touch every page so it counts in RSS


def _fake_kernel(events: List[str], garbage_cycles: int = 0, cycle_bytes: int = 1 << 21):
    class FakeKernel:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            self.status = SimpleNamespace(current_mode=SimpleNamespace(name="NORMAL"), get_recent_history=lambda _n: [SimpleNamespace(
                phase_costs_ms={"p": 1.0}, tick_compute_ms=1.0, metrics={})])
            self.ticks = 0

        def tick_once(self) -> None:
            self.ticks += 1
            events.append(f"tick:gc_enabled={gc.isenabled()}")
            for _ in range(garbage_cycles):
                _Cycle(cycle_bytes)

        def shutdown(self) -> None:
            events.append("shutdown")

    return FakeKernel


def _run(monkeypatch: pytest.MonkeyPatch, events: List[str], *, garbage_cycles: int = 0, ticks: int = 20, profile=PROFILE):
    monkeypatch.setattr(bench_harness, "Kernel", _fake_kernel(events, garbage_cycles))
    harness = BenchHarness(profile)
    result = harness.run_benchmark("MEM_UNIT", build_idle_state(entity_count=2), warmup_ticks=2, sample_ticks=ticks)
    assert harness.last_record is not None
    return harness, result


def test_garbage_makes_the_old_fields_large_and_the_collected_delta_small(monkeypatch: pytest.MonkeyPatch) -> None:
    harness, result = _run(monkeypatch, [], garbage_cycles=5)  # 5 x 2 MB per tick, 20 ticks: about 200 MB of uncollected garbage
    memory = harness.last_record.result.memory_mb
    assert memory["rss_delta"] > 40.0  # RSS sampled with the collector disabled grows with the garbage
    assert memory["rss_after_collect_mb"] - memory["rss_before_window_mb"] < memory["rss_delta"] / 4  # collected to collected: the garbage is gone
    assert memory["gc_collected_objects"] >= 100  # 5 cycles x 20 ticks, each an object (plus its dict), freed by the end collect or by the first gen-0 pass after gc.enable
    assert memory["allocated_blocks_delta"] < 5000  # live python blocks do not grow with collected garbage
    assert result["mem_rss_mb"]["delta"] == memory["rss_delta"] and result["peak_rss_mb"] == memory["rss_high_water"]


def test_the_result_dict_and_the_old_memory_keys_are_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    harness, result = _run(monkeypatch, [])
    assert set(result["mem_rss_mb"]) == {"avg", "max", "delta"} and "mem_after_collect" not in result
    memory = harness.last_record.result.memory_mb
    assert LEGACY_KEYS <= set(memory) and set(memory) == LEGACY_KEYS | NEW_KEYS
    assert memory["sample_every_ticks"] == 10


def test_the_declared_ratio_is_the_trimmed_rss_over_the_profiles_max_ram(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bench_harness, "_malloc_trim", lambda: True)
    for name in ("PERF_512MB_LOCAL", "PERF_2GB_LOCAL"):
        profile = PERF_PROFILES[name]
        harness, result = _run(monkeypatch, [], profile=profile)
        memory = harness.last_record.result.memory_mb
        assert memory["declared_ram_mb"] == float(profile.max_ram_mb) and memory["rss_over_declared_basis_trim"] == 1.0
        assert memory["rss_over_declared"] == pytest.approx(memory["rss_after_trim_mb"] / profile.max_ram_mb, abs=1e-4)
        assert memory["rss_trim_delta_mb"] == pytest.approx(memory["rss_after_trim_mb"] - memory["rss_before_window_mb"], abs=0.02)
        assert memory["peak_rss_over_declared"] == pytest.approx(result["peak_rss_mb"] / profile.max_ram_mb, abs=1e-4)


@pytest.mark.parametrize("initially_enabled", [True, False])
def test_the_end_collect_comes_after_the_clocks_stop_and_gc_is_left_as_found(monkeypatch: pytest.MonkeyPatch, initially_enabled: bool) -> None:
    events: List[str] = []
    real_collect = gc.collect
    monkeypatch.setattr(bench_harness, "Kernel", _fake_kernel(events))
    harness = BenchHarness(PROFILE)
    real_cpu_times = harness._process.cpu_times

    def logging_collect(*args: Any, **kwargs: Any) -> int:
        events.append(f"collect:gc_enabled={gc.isenabled()}")
        return real_collect(*args, **kwargs)

    def logging_cpu_times() -> Any:
        events.append("cpu_times")
        return real_cpu_times()

    def logging_trim() -> bool:
        events.append("trim")
        return True

    monkeypatch.setattr(bench_harness, "_malloc_trim", logging_trim)

    monkeypatch.setattr(gc, "collect", logging_collect)
    monkeypatch.setattr(harness, "_process", SimpleNamespace(cpu_times=logging_cpu_times, memory_info=harness._process.memory_info))
    (gc.enable if initially_enabled else gc.disable)()
    try:
        harness.run_benchmark("MEM_UNIT", build_idle_state(entity_count=2), warmup_ticks=2, sample_ticks=3)
        assert gc.isenabled() is initially_enabled  # exactly the state it had before
    finally:
        gc.enable()
    collects = [e for e in events if e.startswith("collect")]
    assert len(collects) == 2  # the one before the window and the one after it
    ticks = [i for i, e in enumerate(events) if e.startswith("tick")]
    sampled = ticks[2:]  # after the two warm-up ticks
    last_cpu = max(i for i, e in enumerate(events) if e == "cpu_times")
    end_collect = max(i for i, e in enumerate(events) if e.startswith("collect"))
    assert sampled[-1] < last_cpu < end_collect < events.index("shutdown")  # tick, clock stop, collect, shutdown
    trims = [i for i, e in enumerate(events) if e == "trim"]
    assert len(trims) == 1 and last_cpu < end_collect < trims[0] < events.index("shutdown")  # one trim, after the clocks and after the end collect, never before the window
    assert all(e == "tick:gc_enabled=False" for e in (events[i] for i in sampled))  # the latency window runs with the collector off


def test_the_protocol_is_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    harness, _ = _run(monkeypatch, [])
    protocol = harness.last_record.result.protocol
    assert (protocol.warmup_ticks, protocol.measured_ticks, protocol.gc_disabled) == (2, 20, True)
    assert {n: (s.warmup, s.ticks) for n, s in tripwire.TRIPWIRE_SCENARIOS} == {"idle_100_local": (10, 50), "movement_100_local": (10, 50)}


def test_a_failure_reading_the_new_keys_never_fails_the_run(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(self: BenchHarness, *_a: Any, **_k: Any) -> Any:
        raise RuntimeError("boom")

    monkeypatch.setattr(BenchHarness, "_memory_mb", broken)
    monkeypatch.setattr(bench_harness, "Kernel", _fake_kernel([]))
    harness = BenchHarness(PROFILE)
    result = harness.run_benchmark("MEM_UNIT", build_idle_state(entity_count=2), warmup_ticks=2, sample_ticks=3)
    assert harness.last_record is None and result["sample_ticks"] == 3


def _with_ratio(record: BenchmarkRecord, ratio: float, version: str) -> BenchmarkRecord:
    memory = {**record.result.memory_mb, "rss_after_collect_mb": 900.0, "rss_over_declared": ratio, "declared_ram_mb": 512.0}
    return dataclasses.replace(record, schema_version=version, result=dataclasses.replace(record.result, memory_mb=memory))


def test_the_ratio_is_report_only_for_compare_and_promotion() -> None:
    plain, over = make_record(), _with_ratio(make_record(), 3.0, SCHEMA_VERSION)
    assert compare(plain, plain, tripwire.TRIPWIRE_THRESHOLDS) == compare(plain, over, tripwire.TRIPWIRE_THRESHOLDS)
    root = baseline_lifecycle.REPO_ROOT
    assert baseline_lifecycle.refusals(plain, "TCK-20261015-X", root) == baseline_lifecycle.refusals(over, "TCK-20261015-X", root)


@pytest.mark.parametrize("base_version,head_version", [("1.1", "1.2"), ("1.2", "1.1"), ("1.2", "1.2"), ("1.1", "1.1")])
def test_a_minor_schema_difference_does_not_change_the_compare_outcome(base_version: str, head_version: str) -> None:
    base = dataclasses.replace(make_record(), schema_version=base_version)
    head = dataclasses.replace(make_record(avg=10.5), schema_version=head_version)
    same = compare(dataclasses.replace(make_record(), schema_version="1.1"), dataclasses.replace(make_record(avg=10.5), schema_version="1.1"), tripwire.TRIPWIRE_THRESHOLDS)
    assert compare(base, head, tripwire.TRIPWIRE_THRESHOLDS) == same


def test_a_major_schema_difference_is_still_inconclusive() -> None:
    outcome = compare(make_record(), dataclasses.replace(make_record(), schema_version="2.0"), Thresholds())
    assert outcome.state is OutcomeState.INCONCLUSIVE and "MAJOR" in outcome.reason


def test_a_1_1_record_without_the_new_keys_loads_and_reserialises_unchanged() -> None:
    record = dataclasses.replace(make_record(), schema_version="1.1")
    again = BenchmarkRecord.from_dict(record.to_dict())
    assert again == record and set(again.result.memory_mb) == LEGACY_KEYS


def test_without_a_trim_the_keys_are_absent_and_the_ratio_says_it_used_the_collect_reading(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bench_harness, "_malloc_trim", lambda: False)
    harness, _ = _run(monkeypatch, [])
    memory = harness.last_record.result.memory_mb
    assert not TRIM_KEYS & set(memory) and set(memory) == LEGACY_KEYS | (NEW_KEYS - TRIM_KEYS)
    assert memory["rss_over_declared_basis_trim"] == 0.0
    assert memory["rss_over_declared"] == pytest.approx(memory["rss_after_collect_mb"] / PROFILE.max_ram_mb, abs=1e-4)


def test_malloc_trim_never_raises_when_libc_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    import ctypes

    def refuse(*_a: Any, **_k: Any) -> Any:
        raise OSError("no libc.so.6")

    monkeypatch.setattr(ctypes, "CDLL", refuse)
    assert bench_harness._malloc_trim() is False


def test_the_collected_total_reads_gc_stats_and_a_collect_raises_it() -> None:
    before = bench_harness._gc_collected_total()
    cycle: List[Any] = []
    cycle.append(cycle)
    del cycle
    gc.collect()
    assert bench_harness._gc_collected_total() > before


def test_a_trim_that_released_nothing_still_counts_as_a_trim(monkeypatch: pytest.MonkeyPatch) -> None:
    """glibc's malloc_trim returns 0 when there was nothing to release; that is not "unavailable" and must not drop the trim keys."""
    import ctypes

    class StubLibc:
        calls: List[int] = []

        def malloc_trim(self, pad: int) -> int:
            StubLibc.calls.append(pad)
            return 0

    monkeypatch.setattr(ctypes, "CDLL", lambda *_a, **_k: StubLibc())
    assert bench_harness._malloc_trim() is True and StubLibc.calls == [0]
    harness, _ = _run(monkeypatch, [])
    memory = harness.last_record.result.memory_mb
    assert TRIM_KEYS <= set(memory) and memory["rss_over_declared_basis_trim"] == 1.0
    assert memory["rss_over_declared"] == pytest.approx(memory["rss_after_trim_mb"] / PROFILE.max_ram_mb, abs=1e-4)

"""The untimed, collector-on memory pass and its merge into a record (TCK-20261016-PERF-BENCH-COLLECTOR-ON-MEMORY-PASS).

The pass is driven with a fake kernel, so no engine tick runs. The things under test: the collector is on inside the pass and restored after it, no clock is
read, cyclic garbage does not show in the working set, the merge adds ``memory_mb`` keys and changes nothing else, and the ``rss_over_declared`` precedence.
"""
from __future__ import annotations

import dataclasses
import gc
import json
import subprocess
from pathlib import Path
from typing import Any, List

import pytest

from src.perf import bench_harness
from src.perf.bench_harness import BenchHarness, run_memory_pass
from src.perf.benchmark_record import (
    SCHEMA_VERSION,
    BenchmarkRecord,
    BenchmarkRecordError,
    MemoryPassReading,
    OutcomeState,
    compare,
    with_working_set,
    working_set_mismatch,
)
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_idle_state
from tests.unit.perf.test_bench_harness_memory import PROFILE, _fake_kernel
from tests.unit.perf.test_benchmark_record import make_record
from tools.perf import rerun_baselines as rr

DECLARED = 512.0


def _reading(record: BenchmarkRecord, **changes: Any) -> MemoryPassReading:
    base = dict(
        scenario_id=record.identity.scenario.id,
        seed=record.identity.rng.seed,
        profile_name=record.identity.config.profile_name,
        warmup_ticks=record.result.protocol.warmup_ticks,
        sample_ticks=record.result.protocol.measured_ticks,
        rss_before_mb=100.0,
        rss_after_collect_mb=130.0,
        rss_after_trim_mb=106.0,
        blocks_delta=211_000,
        gc_collected=1_200_000,
    )
    base.update(changes)
    return MemoryPassReading(**base)


def _timed_record() -> BenchmarkRecord:
    record = make_record()
    memory = dict(record.result.memory_mb, rss_after_trim_mb=311.0, rss_over_declared=0.61, rss_over_declared_basis_trim=1.0, declared_ram_mb=DECLARED)
    return dataclasses.replace(record, result=dataclasses.replace(record.result, memory_mb=memory))


def _pass(monkeypatch: pytest.MonkeyPatch, events: List[str], *, garbage_cycles: int = 0, ticks: int = 20) -> MemoryPassReading:
    monkeypatch.setattr(bench_harness, "Kernel", _fake_kernel(events, garbage_cycles))
    return run_memory_pass(PROFILE, build_idle_state(entity_count=2), "MEM_UNIT", 2, ticks)


# ── the pass ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("initially_enabled", [True, False])
def test_the_collector_is_on_inside_the_pass_and_left_as_found(monkeypatch: pytest.MonkeyPatch, initially_enabled: bool) -> None:
    events: List[str] = []
    was = gc.isenabled()
    (gc.enable if initially_enabled else gc.disable)()
    try:
        _pass(monkeypatch, events)
        assert gc.isenabled() is initially_enabled
    finally:
        (gc.enable if was else gc.disable)()
    ticks = [e for e in events if e.startswith("tick:")]
    assert len(ticks) == 2 + 20
    assert all(e == "tick:gc_enabled=True" for e in ticks[2:])  # the sampled ticks of the pass run with the collector enabled
    assert events[-1] == "shutdown"


def test_the_pass_reads_no_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse() -> float:
        raise AssertionError("the memory pass must not read a clock")

    monkeypatch.setattr(bench_harness.time, "perf_counter", refuse)
    reading = _pass(monkeypatch, [])
    assert reading.sample_ticks == 20 and reading.warmup_ticks == 2


def test_the_reading_echoes_the_identity_it_ran_under(monkeypatch: pytest.MonkeyPatch) -> None:
    reading = _pass(monkeypatch, [])
    state = build_idle_state(entity_count=2)
    assert (reading.scenario_id, reading.seed, reading.profile_name) == ("MEM_UNIT", state.seed, PROFILE.name)


def test_cyclic_garbage_is_in_the_timed_rss_delta_and_not_in_the_working_set(monkeypatch: pytest.MonkeyPatch) -> None:
    events: List[str] = []
    monkeypatch.setattr(bench_harness, "Kernel", _fake_kernel(events, 5))
    harness = BenchHarness(PROFILE)
    harness.run_benchmark("MEM_UNIT", build_idle_state(entity_count=2), warmup_ticks=2, sample_ticks=20)
    timed = harness.last_record
    assert timed is not None and timed.result.memory_mb["rss_delta"] > 40.0  # about 200 MB of garbage the disabled collector kept
    reading = _pass(monkeypatch, [], garbage_cycles=5)
    merged = with_working_set(timed, reading, DECLARED)
    assert merged.result.memory_mb["working_set_delta_mb"] < 30.0
    assert merged.result.memory_mb["working_set_delta_mb"] < timed.result.memory_mb["rss_delta"] / 3


# ── the merge ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_the_merge_adds_memory_keys_and_changes_nothing_else() -> None:
    record = _timed_record()
    merged = with_working_set(record, _reading(record), DECLARED)
    before, after = record.to_dict(), merged.to_dict()
    assert before["result"].pop("memory_mb").keys() <= after["result"].pop("memory_mb").keys()
    assert before == after  # identity, schema_version and every other result field byte for byte
    assert merged.schema_version == record.schema_version == SCHEMA_VERSION == "1.5"


def test_with_the_pass_rss_over_declared_is_the_working_set_ratio_and_says_so() -> None:
    record = _timed_record()
    memory = with_working_set(record, _reading(record), DECLARED).result.memory_mb
    assert memory["working_set_mb"] == 106.0 and memory["working_set_delta_mb"] == 6.0 and memory["working_set_basis_trim"] == 1.0
    assert memory["rss_over_declared"] == round(106.0 / DECLARED, 4) and memory["rss_over_declared_basis_working_set"] == 1.0
    assert memory["rss_over_declared_timed_pass"] == 0.61  # the timed pass's ratio is kept
    assert memory["rss_after_trim_mb"] == 311.0  # the timed pass's own readings are untouched
    assert memory["working_set_allocated_blocks_delta"] == 211_000.0 and memory["working_set_measured_ticks"] == 20.0


def test_without_the_pass_the_1_2_meaning_applies_unchanged() -> None:
    record = _timed_record()
    memory = record.result.memory_mb
    assert memory["rss_over_declared"] == 0.61 and memory["rss_over_declared_basis_trim"] == 1.0
    assert not [k for k in memory if k.startswith("working_set") or k.endswith("basis_working_set") or k.endswith("timed_pass")]
    assert BenchmarkRecord.from_dict(record.to_dict()) == record


def test_without_a_trim_the_working_set_falls_back_to_the_collect_reading() -> None:
    record = _timed_record()
    memory = with_working_set(record, _reading(record, rss_after_trim_mb=None), DECLARED).result.memory_mb
    assert memory["working_set_mb"] == 130.0 and memory["working_set_basis_trim"] == 0.0


@pytest.mark.parametrize("field,value", [("scenario_id", "other"), ("seed", 7), ("profile_name", "PERF_1GB_LOCAL"), ("warmup_ticks", 6), ("sample_ticks", 21)])
def test_a_pass_of_another_run_is_refused(field: str, value: Any) -> None:
    record = _timed_record()
    forged = _reading(record, **{field: value})
    assert working_set_mismatch(record, forged) is not None
    with pytest.raises(BenchmarkRecordError):
        with_working_set(record, forged, DECLARED)
    assert working_set_mismatch(record, _reading(record)) is None


def test_the_working_set_keys_are_report_only_for_compare() -> None:
    base, head = make_record(avg=10.0), make_record(avg=10.0)
    assert compare(base, head).state is OutcomeState.PASS
    merged = with_working_set(head, _reading(head, rss_after_trim_mb=5000.0), DECLARED)  # a huge working set: no gate reads it
    assert compare(base, merged).state is OutcomeState.PASS


@pytest.mark.parametrize("version", ["1.0", "1.1", "1.2"])
def test_older_records_still_load(version: str) -> None:
    data = make_record().to_dict()
    data["schema_version"] = version
    assert BenchmarkRecord.from_dict(data).schema_version == version


# ── the CLI ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def _fake_child(monkeypatch: pytest.MonkeyPatch, record: BenchmarkRecord, spawned: List[str], exit_code: int = 0, **changes: Any) -> None:
    def spawn(name: str, out: Path) -> int:
        spawned.append(name)
        if exit_code == 0:
            out.write_text(json.dumps(_reading(record, **changes).to_dict()), encoding="utf-8")
        return exit_code

    monkeypatch.setattr(rr, "spawn_memory_pass", spawn)


def _write(path: Path, record: BenchmarkRecord) -> None:
    path.write_text(json.dumps(record.to_dict()), encoding="utf-8")


def test_apply_merges_the_pass_and_keeps_the_timed_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    record, spawned = _timed_record(), []
    path = tmp_path / "run1.json"
    _write(path, record)
    _fake_child(monkeypatch, record, spawned)
    applied, message = rr.apply_memory_pass("idle_100_local", path)
    assert applied and spawned == ["idle_100_local"] and "working_set_mb 106.0" in message
    kept = BenchmarkRecord.from_dict(json.loads(path.with_suffix(".timed.json").read_text(encoding="utf-8")))
    merged = BenchmarkRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
    assert kept == record  # the unmerged record, byte for byte
    assert dataclasses.replace(merged, result=dataclasses.replace(merged.result, memory_mb=kept.result.memory_mb)) == kept  # only memory_mb differs
    assert merged.result.memory_mb["working_set_mb"] == 106.0


def test_a_failing_child_leaves_the_record_as_it_was(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    record = _timed_record()
    path = tmp_path / "run1.json"
    _write(path, record)
    before = path.read_text(encoding="utf-8")
    _fake_child(monkeypatch, record, [], exit_code=1)
    applied, message = rr.apply_memory_pass("idle_100_local", path)
    assert not applied and "exited 1" in message and path.read_text(encoding="utf-8") == before and not path.with_suffix(".timed.json").exists()


def test_a_forged_identity_is_refused_and_the_record_is_untouched(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    record = _timed_record()
    path = tmp_path / "run1.json"
    _write(path, record)
    before = path.read_text(encoding="utf-8")
    _fake_child(monkeypatch, record, [], seed=999)
    applied, message = rr.apply_memory_pass("idle_100_local", path)
    assert not applied and "seed" in message and "refused" in message and path.read_text(encoding="utf-8") == before


def test_record_runs_the_pass_once_not_once_per_timed_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(rr, "wait_for_quiet_window", lambda *a, **k: (True, "quiet"))
    record, spawned, timed_children = _timed_record(), [], []

    def fake_run(argv, env=None, check=False, **kw):
        out = Path(argv[argv.index("--out") + 1])
        timed_children.append(out.name)
        _write(out, record)
        out.with_suffix(".meta.json").write_text(json.dumps({"loadavg_1min": 1.0, "swap_used_mb": 0.0, "wall_s": 1.0, "peak_rss_mb": 90.0}), encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(rr.subprocess, "run", fake_run)
    _fake_child(monkeypatch, record, spawned)
    assert rr.cmd_record("resource_100_local", tmp_path, "TCK-20261018-PERF-UNIT-CAUSE", memory_pass=True) == 0
    assert len(timed_children) == 3 and spawned == ["resource_100_local"]  # 3 timed runs, exactly one pass child
    candidate = json.loads((tmp_path / "resource_100_local" / "candidate.json").read_text(encoding="utf-8"))
    assert candidate["result"]["memory_mb"]["working_set_mb"] == 106.0
    assert "working_set_mb" not in json.dumps(json.loads((tmp_path / "resource_100_local" / "run1.json").read_text(encoding="utf-8")))  # the timed runs are not merged


def test_the_pass_is_off_by_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rr, "wait_for_quiet_window", lambda *a, **k: (True, "quiet"))
    record = _timed_record()

    def fake_run(argv, env=None, check=False, **kw):
        out = Path(argv[argv.index("--out") + 1])
        _write(out, record)
        out.with_suffix(".meta.json").write_text(json.dumps({"loadavg_1min": 1.0, "swap_used_mb": 0.0, "wall_s": 1.0, "peak_rss_mb": 90.0}), encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(rr.subprocess, "run", fake_run)
    monkeypatch.setattr(rr, "spawn_memory_pass", lambda *a, **k: pytest.fail("no pass unless --memory-pass is given"))
    assert rr.cmd_record("resource_100_local", tmp_path, "TCK-20261018-PERF-UNIT-CAUSE") == 0
    assert not rr._parser().parse_args(["record", "resource_100_local", "--cause", "TCK-20261018-X"]).memory_pass
    assert rr._parser().parse_args(["measure", "--name", "idle_100_local", "--out", "x", "--memory-pass"]).memory_pass

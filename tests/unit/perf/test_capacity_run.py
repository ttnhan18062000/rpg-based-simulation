"""The capacity-run projection (TCK-20261010-PERF-M2-T04-CAPACITY-RUN). Tiny scenarios only; never part of default CI."""
from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
from typing import List

import pytest

from src.perf.benchmark_record import BenchmarkRecord, Engine, GateTier, ModeRun, OutcomeState, PercentileMethod, Runner, latency_stats
from tests.unit.perf.test_benchmark_record import make_record
from tools.perf import capacity_run as cap

TINY = cap.RunSpec(scenario="movement", entities=15, profile="PERF_1GB_LOCAL", warmup=2, ticks=10)


def rec(avg: float, *, dirty: bool = False, modes=(ModeRun("NORMAL", 20),)) -> BenchmarkRecord:
    record = make_record(avg=avg, modes=modes)
    identity = dataclasses.replace(record.identity, engine=Engine(commit="a" * 40, dirty_src=dirty), runner=Runner(False, "host"))
    return dataclasses.replace(record, identity=identity)


# ── the declared protocol ─────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_the_default_protocol_is_100_warmup_and_1000_sampled_ticks() -> None:
    args = cap._build_parser().parse_args([])
    assert (args.warmup, args.ticks, args.repetitions, args.cv_limit) == (100, 1000, 5, 0.10)
    assert cap.DEFAULT_WARMUP == 100 and cap.DEFAULT_TICKS == 1000


def test_exact_nearest_rank_values_for_a_fixed_sample_list() -> None:
    stats = latency_stats([float(i) for i in range(1, 21)])
    assert (stats["p50"], stats["p95"], stats["p99"], stats["max"], stats["min"], stats["avg"]) == (10.0, 19.0, 20.0, 20.0, 1.0, 10.5)


# ── assess(): variance, dirty tree, excursions ──────────────────────────────────────────────────────────────────────────────────


def test_variance_above_the_limit_is_inconclusive_and_names_variance() -> None:
    outcome = cap.assess([rec(10.0), rec(14.0), rec(20.0)], cv_limit=0.10)
    assert outcome.state is OutcomeState.INCONCLUSIVE and outcome.reason.startswith("variance:") and "0.10" in outcome.reason


def test_variance_within_the_limit_is_not_a_pass_and_makes_no_claim() -> None:
    outcome = cap.assess([rec(10.0), rec(10.1), rec(9.9)], cv_limit=0.10)
    assert outcome.state is OutcomeState.NOT_APPLICABLE and "no capacity claim" in outcome.reason
    assert OutcomeState.PASS not in {cap.assess([rec(10.0)] * 3).state, cap.assess([rec(10.0), rec(30.0)]).state}


def test_a_dirty_tree_is_inconclusive_never_pass() -> None:
    outcome = cap.assess([rec(10.0), rec(10.0, dirty=True)])
    assert outcome.state is OutcomeState.INCONCLUSIVE and "dirty_src" in outcome.reason


def test_an_excursion_or_a_single_repetition_or_nothing_is_inconclusive() -> None:
    assert "left NORMAL" in cap.assess([rec(10.0), rec(10.0, modes=(ModeRun("DEGRADED", 20),))]).reason
    assert "one repetition" in cap.assess([rec(10.0)]).reason
    assert cap.assess([]).state is OutcomeState.INCONCLUSIVE


def test_median_record_is_the_middle_repetition() -> None:
    assert cap.median_record([rec(30.0), rec(10.0), rec(20.0)]).result.latency_ms["avg"] == 20.0
    assert cap.median_record([rec(10.0), rec(20.0)]).result.latency_ms["avg"] == 10.0


# ── real runs in fresh processes ──────────────────────────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def two_repetitions(tmp_path_factory):
    samples = tmp_path_factory.mktemp("capsamples")
    spec = dataclasses.replace(TINY, samples_dir=str(samples))
    outcome, records = cap.run_unpaired(spec, cap.REPO_ROOT, repetitions=2, cv_limit=100.0)
    return outcome, records, samples


def test_n_repetitions_emit_n_capacity_run_records(two_repetitions) -> None:
    outcome, records, _ = two_repetitions
    assert len(records) == 2 and outcome.state in (OutcomeState.NOT_APPLICABLE, OutcomeState.INCONCLUSIVE)
    for record in records:
        assert record.identity.gate.tier is GateTier.CAPACITY_RUN and record.identity.gate.projection == "capacity_run"
        assert record.identity.runner.controlled is False and record.identity.runner.name != "unknown"
        assert record.result.protocol.warmup_ticks == 2 and record.result.protocol.measured_ticks == 10
        assert record.result.protocol.percentile_method is PercentileMethod.NEAREST_RANK
        assert record.result.outcome == outcome
        assert "rss_high_water" in record.result.memory_mb


def test_the_samples_are_a_pointer_with_a_matching_sha_and_distinct_files(two_repetitions) -> None:
    _, records, samples_dir = two_repetitions
    uris = [r.result.samples.uri for r in records]
    assert len(set(uris)) == 2 and all(Path(u).parent == samples_dir for u in uris)
    for record in records:
        pointer = record.result.samples
        assert pointer.tick_wall_ms is None
        assert hashlib.sha256(Path(pointer.uri).read_bytes()).hexdigest() == pointer.sha256


def test_the_cli_writes_records_and_a_summary_with_no_claim(tmp_path, capsys) -> None:
    code = cap.main(
        ["--scenario", "movement", "--entities", "15", "--warmup", "2", "--ticks", "10", "--repetitions", "2", "--cv-limit", "100", "--out-dir", str(tmp_path / "out"), "--samples-dir", str(tmp_path / "s")]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "OUTCOME:" in out and "CLAIM: none" in out
    assert "sustains" not in out and "capacity of" not in out  # the output states no claim
    summary = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    assert summary["claim"] == cap.NO_CLAIM and summary["repetitions"] == 2
    assert sorted(summary["records"]) == ["head_rep01.json", "head_rep02.json"]
    assert OutcomeState.PASS.value != summary["outcome"]["state"]
    for name in summary["records"]:
        BenchmarkRecord.from_dict(json.loads((tmp_path / "out" / name).read_text(encoding="utf-8")))


def test_a_bad_profile_or_scenario_cannot_run(tmp_path, capsys) -> None:
    assert cap.main(["--profile", "NOPE", "--out-dir", str(tmp_path)]) == 1
    assert "cannot run" in capsys.readouterr().err


# ── paired mode ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_paired_mode_runs_each_side_in_a_fresh_process_under_its_own_root(monkeypatch, tmp_path) -> None:
    seen: List[Path] = []

    def fake_spawn(spec, root):
        seen.append(root)
        return rec(10.0 if root.name == "base" else 40.0)

    monkeypatch.setattr(cap, "spawn", fake_spawn)
    outcome, sides = cap.run_paired(TINY, tmp_path / "base", tmp_path / "head", 3, 100.0, cap.Thresholds())
    assert seen == [tmp_path / "base"] * 3 + [tmp_path / "head"] * 3
    assert set(sides) == {"base", "head"} and outcome.state is OutcomeState.REGRESSION  # compare(10 ms, 40 ms) over the default threshold


def test_paired_mode_is_inconclusive_when_a_side_cannot_emit_records(monkeypatch, tmp_path) -> None:
    def fake_spawn(spec, root):
        if root.name == "base":
            raise cap.CapacityRunError("repetition under base produced no record (exit 1): no module named benchmark_record")
        return rec(10.0)

    monkeypatch.setattr(cap, "spawn", fake_spawn)
    outcome, _ = cap.run_paired(TINY, tmp_path / "base", tmp_path / "head", 2, 100.0, cap.Thresholds())
    assert outcome.state is OutcomeState.INCONCLUSIVE and outcome.reason.startswith("base side:")


def test_spawn_runs_a_real_worker_process_pointed_at_a_root(monkeypatch) -> None:
    calls = []
    real = cap.subprocess.run

    def spy(argv, **kwargs):
        calls.append((argv, kwargs["cwd"], kwargs["env"][cap.ROOT_ENV]))
        return real(argv, **kwargs)

    monkeypatch.setattr(cap.subprocess, "run", spy)
    record = cap.spawn(TINY, cap.REPO_ROOT)
    assert record.identity.gate.tier is GateTier.CAPACITY_RUN
    argv, cwd, root_env = calls[0]
    assert argv[2] == "worker" and cwd == cap.REPO_ROOT and root_env == str(cap.REPO_ROOT)


# ── honesty ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_no_pyperf_in_the_tool_or_harnesses_and_the_claim_constant_is_none() -> None:
    for path in (Path(cap.__file__), Path("src/perf/bench_harness.py"), Path("src/perf/long_run_harness.py")):
        text = path.read_text(encoding="utf-8")
        assert "import pyperf" not in text and "from pyperf" not in text, path
    assert cap.NO_CLAIM.startswith("none")

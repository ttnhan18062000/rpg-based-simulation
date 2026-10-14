"""The T08 re-record tool (TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS): names, protocol, the median and the NOISY rule. No heavy run."""
from __future__ import annotations

import dataclasses
import json
import subprocess
from pathlib import Path

import pytest

from src.perf.profiles import PERF_CANONICAL_PROFILES
from src.perf.scenarios import SCENARIO_BUILDERS
from tests.unit.perf.test_benchmark_record import make_record
from tools.perf import baseline_lifecycle, rerun_baselines as rr, tripwire


REAL_RUN = subprocess.run


def run(avg: float, load: float = 1.0) -> rr.Run:
    return rr.Run("p.json", avg, load, 0.0, 100.0, 3.0)


def test_every_synthetic_baseline_is_a_legacy_file_or_a_promoted_version() -> None:
    baselines = Path(baseline_lifecycle.DEFAULT_BASELINES_DIR)
    legacy = {f[:-5] for f in baseline_lifecycle.LEGACY_TRIPWIRE_REFERENCES}
    promoted = {m.group("name") for f in baselines.glob("*.json") if (m := baseline_lifecycle._VERSIONED_RE.match(f.name))}
    assert {n for n in rr.known_names() if not n.startswith("simq_corpus_")} <= legacy | promoted


def test_the_mixed_records_are_known_now_that_the_spawn_collision_fix_is_on_main() -> None:
    assert rr.SYNTHETIC["mixed_200_local"][2] == "PERF_1GB_LOCAL" and rr.SYNTHETIC["mixed_200_concurrent"][2] == "PERF_2GB_CONC"
    state = rr.build_state("mixed", 200, 42)
    positions = [tuple(e.navigation.position) for e in state.entities.values()]
    assert len(positions) == len(set(positions))  # no two entities on one tile (LAW-SPAWN-OCCUPANCY)


def test_the_profiles_and_scenarios_exist_and_have_a_canonical_variant() -> None:
    for name, (scenario, entities, profile) in rr.SYNTHETIC.items():
        assert scenario in SCENARIO_BUILDERS and entities > 0 and profile in PERF_CANONICAL_PROFILES, name
    assert rr.CORPUS_PROFILE in PERF_CANONICAL_PROFILES


def test_the_two_declared_tripwire_scenarios_reuse_the_tripwire_spec_unchanged() -> None:
    for name, spec in tripwire.TRIPWIRE_SCENARIOS:
        assert rr.spec_for(name) == spec
        assert rr.SYNTHETIC[name][2] == spec.profile  # the table agrees with the declared spec


def test_the_other_synthetic_records_keep_the_committed_protocol_under_the_canonical_contract() -> None:
    spec = rr.spec_for("combat_10_local")
    assert (spec.warmup, spec.ticks, spec.contract, spec.profile) == (10, 20, "canonical", "PERF_2GB_LOCAL")
    assert (spec.gate_tier, spec.gate_projection) == ("tripwire", "tripwire_paired")


def test_a_corpus_record_keeps_100_plus_1000_on_the_512mb_profile() -> None:
    spec = rr.spec_for("simq_corpus_frontier_extended")
    assert (spec.warmup, spec.ticks, spec.profile, spec.scenario) == (100, 1000, "PERF_512MB_LOCAL", "corpus:frontier_extended")


def test_an_unknown_name_is_a_usage_error() -> None:
    with pytest.raises(rr.RerunError):
        rr.spec_for("idle_999_local")


def test_combat_and_resource_use_the_call_shape_of_run_benchmarks() -> None:
    combat = rr.build_state("combat", 10, 42)
    assert len(combat.entities) == 20  # team_a_count = team_b_count = 10
    resource = rr.build_state("resource", 100, 42)
    assert len(resource.resource_nodes) == 50  # node_count = entity_count // 2


def test_the_median_run_is_promoted_and_the_spread_is_max_over_min() -> None:
    summary = rr.summarize([run(10.0), run(12.0), run(11.0)])
    assert summary.median_index == 2 and summary.spread == 0.2 and summary.noisy


def test_a_spread_at_or_under_15_percent_is_not_noisy() -> None:
    assert not rr.summarize([run(100.0), run(110.0), run(115.0)]).noisy
    assert rr.summarize([run(100.0), run(110.0), run(116.0)]).noisy


def test_no_runs_is_an_error() -> None:
    with pytest.raises(rr.RerunError):
        rr.summarize([])


def test_the_promotion_note_carries_every_runs_load_and_the_spread() -> None:
    note = rr.promotion_note("idle_100_local", rr.summarize([run(10.0, 2.5), run(11.0, 3.5), run(10.5, 4.5)]), "host / cpu / 6 vCPU")
    for text in ("loadavg1 2.5", "loadavg1 3.5", "loadavg1 4.5", "spread 10.0 %", "promoted run 3", "host / cpu / 6 vCPU", "claims none"):
        assert text in note


def test_the_tool_never_writes_under_the_baselines_directory() -> None:
    source = Path(rr.__file__).read_text(encoding="utf-8")
    assert "tests/perf/baselines" not in source.replace("``tests/perf/baselines/``", "")


def test_record_runs_three_fresh_processes_and_writes_the_median_candidate_without_promoting(tmp_path, monkeypatch, capsys) -> None:
    averages = iter([30.0, 34.0, 32.0])

    def fake_run(argv, env=None, check=False, **kw):
        if "--out" not in argv:
            return REAL_RUN(argv, env=env, check=check, **kw)
        assert argv[2] == "measure"  # one fresh process per run
        out = Path(argv[argv.index("--out") + 1])
        out.write_text(json.dumps(make_record(avg=next(averages)).to_dict()), encoding="utf-8")
        out.with_suffix(".meta.json").write_text(json.dumps({"loadavg_1min": 2.0, "swap_used_mb": 5.0, "wall_s": 1.0, "peak_rss_mb": 90.0}), encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(rr.subprocess, "run", fake_run)
    assert rr.main(["record", "idle_100_local", "--out-root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    summary = json.loads((tmp_path / "idle_100_local" / "summary.json").read_text(encoding="utf-8"))
    assert summary["median_run"] == 3 and summary["noisy"] is False and len(summary["runs"]) == 3
    candidate = json.loads((tmp_path / "idle_100_local" / "candidate.json").read_text(encoding="utf-8"))
    assert candidate["result"]["latency_ms"]["avg"] == 32.0
    assert "PROMOTE: python3 tools/perf/baseline_lifecycle.py promote" in out and "NOISY" not in out


def test_a_noisy_record_is_reported_and_no_promote_command_is_printed(tmp_path, monkeypatch, capsys) -> None:
    averages = iter([30.0, 50.0, 40.0])

    def fake_run(argv, env=None, check=False, **kw):
        if "--out" not in argv:
            return REAL_RUN(argv, env=env, check=check, **kw)
        out = Path(argv[argv.index("--out") + 1])
        out.write_text(json.dumps(make_record(avg=next(averages)).to_dict()), encoding="utf-8")
        out.with_suffix(".meta.json").write_text(json.dumps({"loadavg_1min": 9.0, "swap_used_mb": 5000.0, "wall_s": 1.0, "peak_rss_mb": 90.0}), encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(rr.subprocess, "run", fake_run)
    assert rr.main(["record", "movement_100_local", "--out-root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "NOISY" in out and "PROMOTE:" not in out
    assert json.loads((tmp_path / "movement_100_local" / "summary.json").read_text(encoding="utf-8"))["noisy"] is True


def test_a_failing_run_stops_the_record_with_exit_one(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(rr.subprocess, "run", lambda argv, env=None, check=False, **kw: subprocess.CompletedProcess(argv, 3))
    assert rr.main(["record", "idle_100_local", "--out-root", str(tmp_path)]) == 1


def test_a_record_that_left_normal_is_reported_and_no_promote_command_is_printed(tmp_path, monkeypatch, capsys) -> None:
    from src.perf.benchmark_record import ModeRun

    def fake_run(argv, env=None, check=False, **kw):
        if "--out" not in argv:
            return REAL_RUN(argv, env=env, check=check, **kw)
        out = Path(argv[argv.index("--out") + 1])
        record = make_record(avg=30.0)
        record = dataclasses.replace(record, result=dataclasses.replace(record.result, runtime_mode_sequence=(ModeRun("NORMAL", 5), ModeRun("CONSTRAINED", 15))))
        out.write_text(json.dumps(record.to_dict()), encoding="utf-8")
        out.with_suffix(".meta.json").write_text(json.dumps({"loadavg_1min": 1.0, "swap_used_mb": 0.0, "wall_s": 1.0, "peak_rss_mb": 90.0}), encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(rr.subprocess, "run", fake_run)
    assert rr.main(["record", "strategic_100_local", "--out-root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "NOT A BASELINE" in out and "CONSTRAINED" in out and "PROMOTE:" not in out
    assert json.loads((tmp_path / "strategic_100_local" / "summary.json").read_text(encoding="utf-8"))["off_normal"] == ["CONSTRAINED"]

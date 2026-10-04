# Compliance IDs: PERF-001, PERF-004, PERF-011
"""Claims tests for tools/release/generate_optimization_proof.py
(TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS).

The engine never runs: BenchHarness and the scenario builders are replaced by stubs, and the
report paths point at tmp_path. Not marked slow.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.release import generate_optimization_proof as gop

_NAMES = list(gop.SCENARIO_CONFIGS)


def _result(name, profile, sample_ticks, tps=150.0, p95=5.0, rss=120.0):
    return {
        "scenario_id": name,
        "profile": profile,
        "sample_ticks": sample_ticks,
        "compute_tps": tps,
        "tick_ms": {"avg": 1.0, "p95": p95},
        "mem_rss_mb": {"max": rss},
        "metrics": {"counter": 3.0},
        "phase_breakdown": {},
    }


def _baseline_entry(name, **override):
    cfg = gop.SCENARIO_CONFIGS[name]
    entry = _result(name, cfg["profile"].name, cfg["sample_ticks"], tps=100.0, p95=10.0, rss=100.0)
    entry.update(override)
    return entry


@pytest.fixture
def proof(tmp_path, monkeypatch):
    """Redirect report paths, stub the engine, and expose the harness construction count."""
    monkeypatch.setattr(gop, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(gop, "BASELINE_PATH", tmp_path / "baseline.json")
    monkeypatch.setattr(gop, "PROOF_JSON_PATH", tmp_path / "optimization_proof.json")
    monkeypatch.setattr(gop, "PROOF_MD_PATH", tmp_path / "optimization_proof.md")
    monkeypatch.setattr(
        gop, "SCENARIO_BUILDERS", {cfg["builder"]: (lambda **kw: object()) for cfg in gop.SCENARIO_CONFIGS.values()}
    )
    state = {"constructed": 0, "overrides": {}}

    class StubHarness:
        def __init__(self, profile):
            state["constructed"] += 1
            self.profile = profile

        def run_benchmark(self, scenario_id, initial_state, warmup_ticks, sample_ticks, flags=None, **_):
            r = _result(scenario_id, self.profile.name, sample_ticks)
            r.update(state["overrides"].get(scenario_id, {}))
            return r

    monkeypatch.setattr(gop, "BenchHarness", StubHarness)

    def write_baseline(data):
        (tmp_path / "baseline.json").write_text(json.dumps(data))

    state["write_baseline"] = write_baseline
    state["tmp"] = tmp_path
    return state


def _all_matching_baseline():
    return {n: _baseline_entry(n) for n in _NAMES}


def test_matching_scenarios_are_compared_with_ratios_from_the_data(proof):
    proof["write_baseline"](_all_matching_baseline())
    results = gop.run_proof()
    for name in _NAMES:
        c = results["comparisons"][name]
        assert c["status"] == "compared"
        assert c["speedup_x"] == 1.5  # 150 / 100
        assert c["latency_reduction_x"] == 2.0  # 10 / 5
        assert "reason" not in c


def test_profile_mismatch_is_not_comparable_with_a_reason(proof):
    data = _all_matching_baseline()
    data["COMBAT_100"]["profile"] = "PERF_2GB_LOCAL"
    proof["write_baseline"](data)
    c = gop.run_proof()["comparisons"]["COMBAT_100"]
    assert c["status"] == "not_comparable"
    assert "profile differs" in c["reason"]
    assert "PERF_2GB_LOCAL" in c["reason"] and "PROD_DEFAULT" in c["reason"]
    assert "speedup_x" not in c and "latency_reduction_x" not in c


def test_sample_ticks_mismatch_is_not_comparable(proof):
    data = _all_matching_baseline()
    data["MOVEMENT_1000"]["sample_ticks"] = 20
    proof["write_baseline"](data)
    c = gop.run_proof()["comparisons"]["MOVEMENT_1000"]
    assert c["status"] == "not_comparable"
    assert "sample_ticks differs" in c["reason"] and "20" in c["reason"]


def test_missing_baseline_scenario_is_not_comparable_not_one(proof):
    data = _all_matching_baseline()
    del data["RESOURCE_1000"]
    proof["write_baseline"](data)
    c = gop.run_proof()["comparisons"]["RESOURCE_1000"]
    assert c["status"] == "not_comparable"
    assert "absent from the baseline" in c["reason"]
    assert c["baseline"]["tps"] is None and c["baseline"]["p95_ms"] is None
    assert "speedup_x" not in c


def test_missing_p95_in_baseline_is_not_comparable(proof):
    data = _all_matching_baseline()
    data["STRATEGIC_500"]["tick_ms"] = {"avg": 1.0}
    proof["write_baseline"](data)
    c = gop.run_proof()["comparisons"]["STRATEGIC_500"]
    assert c["status"] == "not_comparable"
    assert "baseline is missing p95" in c["reason"]


def test_missing_measured_value_in_the_current_run_is_not_comparable(proof):
    proof["write_baseline"](_all_matching_baseline())
    proof["overrides"]["MIXED_1000"] = {"compute_tps": None}
    c = gop.run_proof()["comparisons"]["MIXED_1000"]
    assert c["status"] == "not_comparable"
    assert "current run is missing TPS" in c["reason"]


def test_zero_divisors_are_not_comparable_instead_of_defaulting(proof):
    data = _all_matching_baseline()
    data["MOVEMENT_1000"]["compute_tps"] = 0.0
    proof["write_baseline"](data)
    proof["overrides"]["COMBAT_100"] = {"tick_ms": {"p95": 0.0}}
    comparisons = gop.run_proof()["comparisons"]
    assert comparisons["MOVEMENT_1000"]["status"] == "not_comparable"
    assert "baseline TPS is not positive" in comparisons["MOVEMENT_1000"]["reason"]
    assert comparisons["COMBAT_100"]["status"] == "not_comparable"
    assert "current p95 is not positive" in comparisons["COMBAT_100"]["reason"]


def test_warmup_is_compared_only_when_both_sides_record_it():
    base = _baseline_entry("COMBAT_100")
    res = _result("COMBAT_100", base["profile"], base["sample_ticks"])
    assert gop.compare_scenario("COMBAT_100", base, res, 20)["status"] == "compared"
    base["warmup_ticks"], res["warmup_ticks"] = 10, 20
    c = gop.compare_scenario("COMBAT_100", base, res, 20)
    assert c["status"] == "not_comparable" and "warmup_ticks differs" in c["reason"]


@pytest.mark.parametrize("bad", ["[]", "{}", '{"timestamp": "2026-10-04T00:00:00Z"}', "not json"])
def test_bad_baseline_exits_before_running_anything(proof, bad):
    (proof["tmp"] / "baseline.json").write_text(bad)
    with pytest.raises(SystemExit) as exc:
        gop.run_proof()
    assert exc.value.code == 1
    assert proof["constructed"] == 0


def test_missing_baseline_file_exits_before_running_anything(proof):
    with pytest.raises(SystemExit) as exc:
        gop.run_proof()
    assert exc.value.code == 1
    assert proof["constructed"] == 0


def test_markdown_has_no_fixed_claims_and_its_counts_match_the_json(proof):
    data = _all_matching_baseline()
    data["COMBAT_100"]["profile"] = "PERF_2GB_LOCAL"
    data["MIXED_1000"]["sample_ticks"] = 20
    proof["write_baseline"](data)
    results = gop.run_proof()
    md = (proof["tmp"] / "optimization_proof.md").read_text()
    saved = json.loads((proof["tmp"] / "optimization_proof.json").read_text())

    for removed in ("Key Takeaway", "strict isolation", "preventing measurement jitter", "consistent speedups", "validating our"):
        assert removed not in md
    assert "Provisional" in md.split("## Summary")[0]
    assert "capacity claim" in md.split("## Summary")[0]

    summary = saved["summary"]
    assert (summary["compared"], summary["not_comparable"], summary["total"]) == (3, 2, 5)
    assert f"{summary['compared']} of {summary['total']} scenarios were compared" in md
    assert f"{summary['not_comparable']} were not comparable" in md
    assert "3 were faster" in md and "0 slower" in md
    assert results["summary"] == summary
    assert saved["metadata"]["provisional"] is True
    for name, c in saved["comparisons"].items():
        assert c["status"] in ("compared", "not_comparable")
        assert ("speedup_x" in c) == (c["status"] == "compared")


def test_markdown_audit_statement_reports_only_what_the_code_set(proof):
    proof["write_baseline"](_all_matching_baseline())
    gop.run_proof(quick_test=True)
    md = (proof["tmp"] / "optimization_proof.md").read_text()
    assert "quick_test: True" in md
    assert '"no_frame_pacing": true' in md and '"no_replay": true' in md
    assert "warmup_ticks=5" in md and "sample_ticks=10" in md


def test_all_not_comparable_writes_reports_and_exits_non_zero(proof):
    proof["write_baseline"](_all_matching_baseline())
    # quick mode runs 10 sample ticks, so none of the 50-tick baselines is comparable
    assert gop.main(["--quick"]) == 1
    assert (proof["tmp"] / "optimization_proof.json").exists()
    assert (proof["tmp"] / "optimization_proof.md").exists()


def test_partial_result_exits_zero(proof):
    data = _all_matching_baseline()
    data["COMBAT_100"]["profile"] = "PERF_2GB_LOCAL"
    proof["write_baseline"](data)
    assert gop.main([]) == 0


def test_source_has_no_numeric_fallback_for_measured_values():
    source = Path(gop.__file__).read_text(encoding="utf-8")
    assert ", 1.0)" not in source
    assert "else 1.0" not in source


def test_report_states_the_limits_of_its_own_check(proof):
    proof["write_baseline"](_all_matching_baseline())
    results = gop.run_proof()
    saved = json.loads((proof["tmp"] / "optimization_proof.json").read_text())
    md = (proof["tmp"] / "optimization_proof.md").read_text()

    listed = saved["metadata"]["unchecked_identity"]
    assert listed == list(gop.UNCHECKED_IDENTITY)
    assert any("workload" in item for item in listed)
    assert "warmup_ticks" in listed and "run flags" in listed

    summary_section = md.split("## Summary")[1].split("## Comparison Matrix")[0]
    assert "Comparability was checked on profile and sample_ticks only;" in summary_section
    for item in listed:
        assert item in summary_section
    assert "are not recorded in the baseline and were not checked." in summary_section

    for name, c in results["comparisons"].items():
        assert c["optimized"]["workload"] == gop.SCENARIO_CONFIGS[name]["kwargs"]
        assert saved["comparisons"][name]["optimized"]["workload"] == gop.SCENARIO_CONFIGS[name]["kwargs"]


def test_limits_sentence_is_shown_even_when_nothing_is_compared(proof):
    proof["write_baseline"](_all_matching_baseline())
    gop.main(["--quick"])
    md = (proof["tmp"] / "optimization_proof.md").read_text()
    assert "were not checked." in md

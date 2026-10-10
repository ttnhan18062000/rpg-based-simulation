"""The paired tripwire (TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED). Fake spawns only; the one real-process test is marked slow."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Dict, List

import pytest

from src.perf.benchmark_record import OutcomeState, PercentileMethod, Thresholds
from src.config.profiles import SignalContract
from tests.unit.perf.test_benchmark_record import make_record, replace_identity
from tools.agent_working_paths import TICKETS
from tools.perf import baseline_lifecycle, capacity_run
from tools.perf import tripwire as tw

SPEC = tw.TRIPWIRE_SCENARIOS[0][1]
BASE, HEAD = Path("/base"), Path("/head")


def fake_spawn(avgs: Dict[str, List[float]], calls: List[Path]):
    """A spawn returning records whose avg latency comes from ``avgs[root.name]`` in call order."""

    def spawn(spec, root):
        calls.append(root)
        return make_record(avg=avgs[root.name].pop(0))

    return spawn


# ── declared protocol ─────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_the_declared_scenarios_are_small_tripwire_specs_on_the_canonical_contract() -> None:
    assert [n for n, _ in tw.TRIPWIRE_SCENARIOS] == ["idle_100_local", "movement_100_local"]
    for _, spec in tw.TRIPWIRE_SCENARIOS:
        assert (spec.warmup, spec.ticks, spec.contract) == (10, 50, "canonical")
        assert (spec.gate_tier, spec.gate_projection) == ("tripwire", "tripwire_paired")


def test_the_threshold_clears_the_measured_noise_and_keeps_its_floor() -> None:
    """The relative threshold must sit above the largest A/A deviation seen with identical code (tripwire.NOISE_BUDGET, from `calibrate`)."""
    assert tw.NOISE_BUDGET == 0.31
    assert tw.TRIPWIRE_THRESHOLDS.relative > tw.NOISE_BUDGET
    assert tw.TRIPWIRE_THRESHOLDS.absolute_ms == 5.0 and tw.TRIPWIRE_THRESHOLDS.metric == "avg"


def test_a_noise_sized_delta_is_a_pass_under_the_declared_thresholds() -> None:
    """A +30% delta, the size of the observed A/A noise, must not be a regression at the declared thresholds."""
    result = tw.run_scenario("s", SPEC, BASE, HEAD, spawn=fake_spawn({"base": [100.0], "head": [130.0]}, []))
    assert result.outcome.state is OutcomeState.PASS


# ── paired comparison ─────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_a_head_slower_than_both_the_relative_threshold_and_the_floor_is_a_regression() -> None:
    calls: List[Path] = []
    result = tw.run_scenario("s", SPEC, BASE, HEAD, Thresholds(0.25, 5.0), fake_spawn({"base": [100.0, 100.0], "head": [200.0, 200.0]}, calls))
    assert result.first.outcome.state is OutcomeState.REGRESSION and result.outcome.state is OutcomeState.REGRESSION
    assert "reproduced on the diagnostic retry" in result.outcome.reason


def test_a_delta_inside_the_noise_budget_is_a_pass_without_a_retry() -> None:
    calls: List[Path] = []
    result = tw.run_scenario("s", SPEC, BASE, HEAD, Thresholds(0.25, 5.0), fake_spawn({"base": [100.0], "head": [110.0]}, calls))
    assert result.outcome.state is OutcomeState.PASS and result.retry is None
    assert calls == [BASE, HEAD]  # one fresh process per side


def test_a_delta_over_the_relative_threshold_but_under_the_absolute_floor_is_a_pass() -> None:
    result = tw.run_scenario("s", SPEC, BASE, HEAD, Thresholds(0.25, 5.0), fake_spawn({"base": [2.0], "head": [4.5]}, []))
    assert result.outcome.state is OutcomeState.PASS


def test_each_side_runs_under_its_own_root_in_its_own_process() -> None:
    calls: List[Path] = []
    tw.run_scenario("s", SPEC, BASE, HEAD, spawn=fake_spawn({"base": [10.0], "head": [10.0]}, calls))
    assert calls == [BASE, HEAD]


# ── the diagnostic retry ──────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_at_most_one_retry_runs_and_the_report_has_both_outcomes() -> None:
    calls: List[Path] = []
    spawn = fake_spawn({"base": [100.0] * 5, "head": [300.0] * 5}, calls)
    result = tw.run_scenario("s", SPEC, BASE, HEAD, Thresholds(0.25, 5.0), spawn)
    assert len(calls) == 4  # first pair + exactly one retry pair, never more
    assert result.first is not None and result.retry is not None and tw.MAX_RETRIES == 1
    body = tw.report([result])["scenarios"][0]
    assert body["first"]["state"] == "REGRESSION" and body["retry"]["state"] == "REGRESSION"


def test_a_retry_that_disagrees_is_inconclusive_never_a_pass() -> None:
    result = tw.run_scenario("s", SPEC, BASE, HEAD, Thresholds(0.25, 5.0), fake_spawn({"base": [100.0, 100.0], "head": [300.0, 101.0]}, []))
    assert result.first.outcome.state is OutcomeState.REGRESSION and result.retry.outcome.state is OutcomeState.PASS
    assert result.outcome.state is OutcomeState.INCONCLUSIVE and "not reproducible" in result.outcome.reason


def test_a_side_that_cannot_produce_a_record_is_inconclusive_naming_the_side() -> None:
    def spawn(spec, root):
        if root.name == "base":
            raise capacity_run.CapacityRunError("no module named benchmark_record")
        return make_record(avg=10.0)

    result = tw.run_scenario("s", SPEC, BASE, HEAD, spawn=spawn)
    assert result.outcome.state is OutcomeState.INCONCLUSIVE and "base side" in result.outcome.reason


# ── non-blocking ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_a_regression_does_not_fail_the_run_and_is_annotated_as_a_warning(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(tw.capacity_run, "spawn", fake_spawn({"base": [100.0] * 8, "head": [400.0] * 8}, []))
    monkeypatch.setattr(tw, "run_all", lambda base, head, chosen, *a, **k: [tw.run_scenario(n, s, base, head, spawn=tw.capacity_run.spawn) for n, s in chosen])
    code = tw.main(["run", "--base", "/base", "--head", "/head", "--out-dir", str(tmp_path), "--github-annotations"])
    out = capsys.readouterr().out
    assert code == 0 and "::warning title=perf tripwire idle_100_local::REGRESSION" in out
    body = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert body["blocking"] is False and body["claim"].startswith("none") and len(body["scenarios"]) == 2


def test_an_unknown_scenario_cannot_run(capsys) -> None:
    assert tw.main(["run", "--base", "/b", "--scenario", "nope"]) == 1
    assert "cannot run" in capsys.readouterr().err


# ── the nightly lane: a missing or incompatible baseline is INCONCLUSIVE ─────────────────────────────────────────────────────


def test_a_missing_baseline_is_inconclusive_with_a_named_reason(tmp_path) -> None:
    record, reason = tw.load_baseline("idle_100_local", tmp_path)
    outcome = tw.compare_with_baseline(record, reason, make_record())
    assert record is None and outcome.state is OutcomeState.INCONCLUSIVE and "no baseline named idle_100_local" in outcome.reason


def test_a_legacy_reference_has_no_identity_so_it_is_inconclusive_not_a_skip() -> None:
    record, reason = tw.load_baseline("idle_100_local")  # the committed legacy file
    outcome = tw.compare_with_baseline(record, reason, make_record())
    assert record is None and outcome.state is OutcomeState.INCONCLUSIVE and "legacy tripwire reference" in outcome.reason


@pytest.mark.parametrize(
    "change, field",
    [
        ({"percentile_method": PercentileMethod.LINEAR}, "result.protocol.percentile_method"),
        ({"signal": SignalContract.CANONICAL}, "identity.contract.signal_contract"),
    ],
)
def test_an_incompatible_baseline_identity_is_inconclusive_naming_the_field(change, field) -> None:
    base = make_record()
    if "percentile_method" in change:
        head = dataclasses.replace(base, result=dataclasses.replace(base.result, protocol=dataclasses.replace(base.result.protocol, percentile_method=change["percentile_method"])))
    else:
        head = replace_identity(base, "contract", signal_contract=change["signal"])
    outcome = tw.compare_with_baseline(base, "", head)
    assert outcome.state is OutcomeState.INCONCLUSIVE and field in outcome.reason


def test_a_promoted_baseline_is_loaded_and_compared(tmp_path) -> None:
    repo = tmp_path / "repo"
    (repo / TICKETS / "done").mkdir(parents=True)
    (repo / TICKETS / "done" / "TCK-20261010-X.md").write_text("x", encoding="utf-8")
    directory = tmp_path / "baselines"
    directory.mkdir()
    candidate = make_record().to_dict()
    candidate["identity"]["engine"] = {"commit": "a" * 40, "dirty_src": False}
    baseline_lifecycle.promote(candidate, "idle_100_local", "TCK-20261010-X", directory, "t", repo)
    record, reason = tw.load_baseline("idle_100_local", directory)
    assert record is not None and reason == ""
    assert tw.compare_with_baseline(record, reason, make_record(avg=11.0)).state is OutcomeState.PASS


# ── retired tools ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_the_two_old_regression_tools_are_gone() -> None:
    root = Path(__file__).resolve().parents[3]
    for name in ("check_perf_regression.py", "perf_ci.py"):
        assert not (root / "tools" / "perf" / name).exists()


@pytest.mark.slow
def test_a_real_paired_run_writes_a_report_and_exits_zero(tmp_path, capsys) -> None:
    """Real fresh processes, one scenario, this checkout as both sides (A/A): whatever the outcome, the run reports and does not fail."""
    code = tw.main(["run", "--base", str(tw.REPO_ROOT), "--head", str(tw.REPO_ROOT), "--scenario", "idle_100_local", "--out-dir", str(tmp_path), "--github-annotations"])
    assert code == 0
    body = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert body["blocking"] is False and [s["name"] for s in body["scenarios"]] == ["idle_100_local"]
    scenario = body["scenarios"][0]
    assert scenario["outcome"]["state"] in {"PASS", "REGRESSION", "INCONCLUSIVE"}
    assert scenario["first"]["base_avg_ms"] > 0 and scenario["first"]["head_avg_ms"] > 0
    assert "::" in capsys.readouterr().out  # an annotation line

"""Summary maths of tools/loadtest: CSV parsing, spread across repeats, the saturation rule (fixed fixtures)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.loadtest import summary
from tools.loadtest.keys import api_key_hashes, hash_key

STATS_HEADER = ('"Type","Name","Request Count","Failure Count","Median Response Time","Average Response Time",'
                '"Min Response Time","Max Response Time","Average Content Size","Requests/s","Failures/s",'
                '"50%","66%","75%","80%","90%","95%","98%","99%","99.9%","99.99%","100%"')


def _stats_csv(path: Path, *, requests: int, failures: int, rps: float, p50: int, p95: int, p99: int) -> Path:
    row = (f'"","Aggregated",{requests},{failures},{p50},{p50},1,500,100,{rps},0,{p50},{p50},{p50},{p50},'
           f'{p95},{p95},{p95},{p99},{p99},{p99},{p99}')
    path.write_text(STATS_HEADER + '\n"GET","/health",5,0,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1\n' + row + "\n")
    return path


def test_parse_stats_csv_reads_the_aggregated_row(tmp_path: Path) -> None:
    path = _stats_csv(tmp_path / "s.csv", requests=900, failures=9, rps=30.5, p50=12, p95=40, p99=90)
    assert summary.parse_stats_csv(path) == summary.StepStats(900, 9, 30.5, 12.0, 40.0, 90.0)


def test_parse_stats_csv_without_aggregated_row_raises(tmp_path: Path) -> None:
    path = tmp_path / "s.csv"
    path.write_text(STATS_HEADER + "\n")
    with pytest.raises(ValueError):
        summary.parse_stats_csv(path)


def test_failures_are_split_into_their_own_categories(tmp_path: Path) -> None:
    path = tmp_path / "f.csv"
    path.write_text('"Method","Name","Error","Occurrences"\n'
                    '"GET","/a","admission_429",7\n"GET","/a","server_5xx_503",2\n"GET","/b","server_5xx_500",1\n'
                    '"GET","/b","http_404",4\n"GET","/c","ConnectionError(...)",3\n')
    assert summary.parse_failures_csv(path) == {"admission_429": 7, "server_5xx": 3, "http_other": 4, "transport": 3}


def test_missing_failures_csv_means_no_failures(tmp_path: Path) -> None:
    assert summary.parse_failures_csv(tmp_path / "none.csv") == {"admission_429": 0, "server_5xx": 0, "http_other": 0, "transport": 0}


def test_spread_across_repeats_is_median_and_min_max() -> None:
    assert summary.spread([100.0, 90.0, 120.0]) == {"median": 100.0, "min": 90.0, "max": 120.0}
    assert summary.spread([5.0, 7.0]) == {"median": 6.0, "min": 5.0, "max": 7.0}
    with pytest.raises(ValueError):
        summary.spread([])


def test_aggregate_repeats_covers_throughput_and_percentiles() -> None:
    repeats = [summary.StepStats(100, 0, r, p, p * 2, p * 3) for r, p in ((50.0, 10.0), (60.0, 20.0), (55.0, 30.0))]
    agg = summary.aggregate_repeats(repeats)
    assert agg["rps"] == {"median": 55.0, "min": 50.0, "max": 60.0}
    assert agg["p95"]["median"] == 40.0 and agg["p99"]["max"] == 90.0


def test_error_rates_handle_zero_requests() -> None:
    assert summary.error_rates(0, {"admission_429": 0}) == {"admission_429": 0.0}
    assert summary.error_rates(200, {"admission_429": 10}) == {"admission_429": 0.05}


QUIET = {"backend_cpu_pct": 40.0, "host_cpu_pct": 50.0, "run_queue": 2, "backend_mem_mb": 300.0, "swap_kb_s": 0}


def test_no_resource_saturated_when_everything_is_below_threshold() -> None:
    assert summary.saturated_resources(QUIET, nproc=6, mem_limit_mb=1024, rates={}) == []


def test_each_resource_threshold() -> None:
    def hit(**change: float) -> list[str]:
        use = {**QUIET, **change}
        return [name for name, _ in summary.saturated_resources(use, nproc=6, mem_limit_mb=1024, rates={})]

    assert hit(backend_cpu_pct=90.0) == ["backend_cpu"]
    assert hit(backend_cpu_pct=89.9) == []
    assert hit(host_cpu_pct=95.0) == ["host_cpu"]
    assert hit(run_queue=6) == []          # equal to nproc is not saturated
    assert hit(run_queue=7) == ["run_queue"]
    assert hit(backend_mem_mb=921.6) == ["memory"]
    assert hit(swap_kb_s=1) == ["swap"]


def test_error_rate_thresholds() -> None:
    assert [n for n, _ in summary.saturated_resources(QUIET, nproc=6, mem_limit_mb=1024, rates={"admission_429": 0.01})] == ["admission_429"]
    assert summary.saturated_resources(QUIET, nproc=6, mem_limit_mb=1024, rates={"server_5xx": 0.0099}) == []


def test_first_saturation_is_the_lowest_step_and_ties_follow_resource_order() -> None:
    hot = {**QUIET, "backend_cpu_pct": 99.0, "host_cpu_pct": 97.0}
    steps = [(100, hot, {}), (10, QUIET, {}), (50, hot, {}), (25, QUIET, {})]
    assert summary.first_saturation(steps, nproc=6, mem_limit_mb=1024) == (50, "backend_cpu", 99.0)


def test_first_saturation_none_when_never_saturated() -> None:
    assert summary.first_saturation([(10, QUIET, {}), (25, QUIET, {})], nproc=6, mem_limit_mb=1024) is None


def test_classify_failure_separates_admission_from_server_errors() -> None:
    assert summary.classify_failure(200) is None
    assert summary.classify_failure(429) == "admission_429"
    assert summary.classify_failure(503) == "server_5xx_503"
    assert summary.classify_failure(401) == "http_401"


def test_api_key_hashes_match_the_server_format() -> None:
    value = api_key_hashes(["k0", "k1"])
    assert value == f"loadtest-0:{hash_key('k0')},loadtest-1:{hash_key('k1')}"
    assert len(hash_key("k0")) == 64

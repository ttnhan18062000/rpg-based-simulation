"""Summary maths of tools/loadtest: CSV parsing, spread across repeats, the saturation rule (fixed fixtures)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.loadtest import summary
from tools.loadtest.keys import STATUS_CLIENT_ID, api_key_hashes, hash_key

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
                    '"GET","/a","CatchResponseError(\'admission_429\')",7\n"GET","/a","CatchResponseError(\'server_5xx_503\')",2\n'
                    '"GET","/b","CatchResponseError(\'server_5xx_500\')",1\n"GET","/b","CatchResponseError(\'http_404\')",4\n'
                    '"GET","/c","ConnectionError(...)",3\n')
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


def _view(users: int, rps: float, p95: float, backend: float = 100.0, host: float = 40.0, runq: float = 2) -> summary.StepView:
    return summary.StepView(users, rps, p95, backend, host, runq)


def test_no_knee_while_throughput_keeps_growing() -> None:
    steps = [_view(10, 100, 50), _view(25, 180, 70), _view(50, 300, 120)]
    assert summary.find_saturation(steps, nproc=6) is None


def test_no_knee_when_throughput_flat_but_p95_does_not_rise() -> None:
    assert summary.find_saturation([_view(10, 100, 50), _view(25, 105, 60)], nproc=6) is None


def test_no_knee_when_p95_rises_but_throughput_still_grows() -> None:
    assert summary.find_saturation([_view(10, 100, 50), _view(25, 130, 90)], nproc=6) is None


def test_knee_thresholds_are_gain_under_10_percent_and_p95_rise_at_least_50_percent() -> None:
    # gain exactly 10 % is not under the limit; p95 rise exactly 50 % is enough
    assert summary.find_saturation([_view(10, 100, 100), _view(25, 110, 200)], nproc=6) is None
    assert summary.find_saturation([_view(10, 100, 100), _view(25, 109.9, 150)], nproc=6) is not None


def test_knee_attributed_to_host_cpu_by_cpu_percent() -> None:
    steps = [_view(10, 100, 50), _view(25, 105, 90, backend=120, host=93)]
    got = summary.find_saturation(steps, nproc=6)
    assert got is not None and (got.users, got.resource) == (25, "host_cpu") and "93" in got.branch


def test_knee_attributed_to_host_cpu_by_run_queue() -> None:
    steps = [_view(10, 100, 50), _view(25, 105, 90, backend=120, host=60, runq=7)]
    got = summary.find_saturation(steps, nproc=6)
    assert got is not None and got.resource == "host_cpu" and "run queue" in got.branch
    steps_equal = [_view(10, 100, 50), _view(25, 105, 90, backend=120, host=60, runq=6)]
    assert summary.find_saturation(steps_equal, nproc=6).resource == "backend_process"


def test_knee_attributed_to_backend_process_when_backend_cpu_is_near_its_maximum() -> None:
    steps = [_view(10, 100, 50, backend=60), _view(25, 105, 90, backend=130), _view(50, 106, 200, backend=125)]
    got = summary.find_saturation(steps, nproc=6)
    assert got is not None and (got.users, got.resource) == (25, "backend_process")


def test_knee_unattributed_when_nothing_matches() -> None:
    steps = [_view(10, 100, 50, backend=130), _view(25, 105, 90, backend=70, host=40, runq=2)]
    got = summary.find_saturation(steps, nproc=6)
    assert got is not None and got.resource == "unattributed"


def test_first_knee_wins_and_steps_are_ordered_by_users() -> None:
    steps = [_view(50, 106, 400, backend=130), _view(10, 100, 50), _view(25, 104, 100, backend=130)]
    assert summary.find_saturation(steps, nproc=6).users == 25


def test_pool_ceiling_and_the_half_ceiling_warning() -> None:
    assert summary.pool_ceiling_rps(1000) == 3000.0
    assert not summary.ceiling_warning(1500.0, 1000)    # exactly 50 % is not over
    assert summary.ceiling_warning(1500.1, 1000)
    assert summary.ceiling_warning(400.0, 250)


def test_host_swap_and_disk_are_judged_against_the_idle_baseline() -> None:
    assert summary.above_baseline(5000.0, 4200.0) == (800.0, False)
    delta, flagged = summary.above_baseline(5300.0, 4000.0)
    assert delta == 1300.0 and flagged
    assert summary.above_baseline(100.0, 4000.0)[1] is False   # below baseline


def test_step_flags() -> None:
    flags = summary.step_flags(backend_mem_mb=930.0, mem_limit_mb=1024.0, rates={"admission_429": 0.02, "server_5xx": 0.0},
                               swap_delta_kb_s=2000.0, disk_delta_kb_s=10.0)
    assert flags == ["memory_near_limit", "admission_429", "host_swap"]
    assert summary.step_flags(backend_mem_mb=100.0, mem_limit_mb=1024.0, rates={}, swap_delta_kb_s=0.0, disk_delta_kb_s=0.0) == []


def test_classify_failure_separates_admission_from_server_errors() -> None:
    assert summary.classify_failure(200) is None
    assert summary.classify_failure(429) == "admission_429"
    assert summary.classify_failure(503) == "server_5xx_503"
    assert summary.classify_failure(401) == "http_401"


def test_api_key_hashes_match_the_server_format() -> None:
    value = api_key_hashes(["k0", "k1"])
    assert value == f"loadtest-0:{hash_key('k0')},loadtest-1:{hash_key('k1')}"
    assert len(hash_key("k0")) == 64


def test_status_key_is_hashed_after_the_pool_under_its_own_client_id() -> None:
    value = api_key_hashes(["k0"], status_key="status")
    assert value == f"loadtest-0:{hash_key('k0')},{STATUS_CLIENT_ID}:{hash_key('status')}"
    assert "status" not in value.replace(STATUS_CLIENT_ID, "")   # only the hash, never the key


# --- engine state per step -------------------------------------------------------------------------------------------------

def _status(tick: int, elapsed: float | None = None, governor: str = "DEGRADED") -> dict:
    return {"status": "RUNNING", "current_tick": tick, "elapsed_seconds": elapsed, "governor_mode": governor,
            "health_state": "DEGRADED", "observability_mode": "LIGHT", "run_id": "ignored"}


def test_engine_reading_keeps_only_the_status_fields_and_the_time() -> None:
    reading = summary.engine_reading(_status(10, 2.0), 100.0)
    assert reading is not None and reading["current_tick"] == 10 and reading["taken_at"] == 100.0
    assert "run_id" not in reading


def test_engine_reading_of_a_missing_payload_is_none() -> None:
    assert summary.engine_reading(None, 1.0) is None


def test_ticks_per_second_uses_the_engines_own_elapsed_seconds() -> None:
    start, end = summary.engine_reading(_status(100, 10.0), 0.0), summary.engine_reading(_status(300, 20.0), 99.0)
    assert summary.ticks_per_second(start, end) == pytest.approx(20.0)


def test_ticks_per_second_falls_back_to_wall_time() -> None:
    start, end = summary.engine_reading(_status(100), 0.0), summary.engine_reading(_status(160), 30.0)
    assert summary.ticks_per_second(start, end) == pytest.approx(2.0)


@pytest.mark.parametrize("start,end", [(None, {"current_tick": 5, "taken_at": 1.0}), ({"current_tick": 9, "taken_at": 0.0}, {"current_tick": 5, "taken_at": 1.0}),
                                       ({"current_tick": 5, "taken_at": 1.0}, {"current_tick": 9, "taken_at": 1.0}),
                                       ({"current_tick": None, "taken_at": 0.0}, {"current_tick": 9, "taken_at": 1.0})])
def test_ticks_per_second_is_none_when_it_cannot_be_trusted(start, end) -> None:
    assert summary.ticks_per_second(start, end) is None


def test_aggregate_engine_gives_median_rate_and_modes_seen() -> None:
    windows = [(summary.engine_reading(_status(0, 0.0), 0.0), summary.engine_reading(_status(100, 10.0), 10.0)),
               (summary.engine_reading(_status(100, 10.0), 10.0), summary.engine_reading(_status(120, 20.0, "NORMAL"), 20.0)),
               (None, None)]
    agg = summary.aggregate_engine(windows)
    assert agg["ticks_per_s"] == [10.0, 2.0, None]
    assert agg["ticks_per_s_median"] == pytest.approx(6.0)
    assert agg["governor_modes"] == ["DEGRADED", "NORMAL"]
    assert agg["start"]["current_tick"] == 0 and agg["end"] is None


def test_aggregate_engine_with_no_readings_is_all_unread() -> None:
    agg = summary.aggregate_engine([(None, None)])
    assert agg["ticks_per_s_median"] is None and agg["governor_modes"] == [] and agg["start"] is None


def test_engine_row_shows_ticks_and_modes_and_na_when_unread() -> None:
    row = summary.format_engine_row(25, {"ticks_per_s_median": 12.34, "governor_modes": ["DEGRADED"], "health_states": ["DEGRADED", "OK"],
                                         "observability_modes": ["LIGHT"]})
    assert row.split() [:3] == ["25", "12.3", "ticks/s"] and row.endswith("DEGRADED / DEGRADED, OK / LIGHT")
    assert summary.format_engine_row(10, {"ticks_per_s_median": None, "governor_modes": [], "health_states": [], "observability_modes": []}).endswith("n/a / n/a / n/a")

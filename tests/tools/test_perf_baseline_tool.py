"""Tests for tools/perf/perf_baseline.py (TCK-20261004-PERF-LATEST-JSON-SINGLE-WRITER).

No benchmark is ever run: paths are redirected to tmp_path and subprocess.run is patched.
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.perf import perf_baseline

_REPO_ROOT = Path(__file__).parent.parent.parent


def _entry(key):
    return {
        "scenario_id": key,
        "profile": "PERF_512MB_LOCAL",
        "sample_ticks": 50,
        "compute_tps": 10.0,
        "tick_ms": {"avg": 1.0, "p95": 2.0},
        "mem_rss_mb": {"max": 100.0},
    }


@pytest.fixture
def paths(tmp_path, monkeypatch):
    latest = tmp_path / "latest.json"
    baseline = tmp_path / "out" / "baseline.json"
    monkeypatch.setattr(perf_baseline, "LATEST_PATH", str(latest))
    monkeypatch.setattr(perf_baseline, "BASELINE_PATH", str(baseline))
    return latest, baseline


def test_update_copies_a_valid_scenario_keyed_file(paths):
    latest, baseline = paths
    latest.write_text(json.dumps({"IDLE_100": _entry("IDLE_100"), "MIXED_1000": _entry("MIXED_1000")}))
    assert perf_baseline.main(["--update"]) == 0
    written = json.loads(baseline.read_text())
    assert set(written) == {"IDLE_100", "MIXED_1000", "timestamp"}
    assert written["timestamp"].endswith("Z")


def test_update_accepts_the_legacy_avg_tps_alias(paths):
    latest, baseline = paths
    entry = _entry("IDLE_100")
    entry["avg_tps"] = entry.pop("compute_tps")
    latest.write_text(json.dumps({"IDLE_100": entry}))
    assert perf_baseline.main(["--update"]) == 0


def test_update_refuses_the_flat_worker_throughput_shape(paths, capsys):
    latest, baseline = paths
    baseline.parent.mkdir(parents=True)
    baseline.write_text('{"keep": 1}')
    latest.write_text(json.dumps({
        "scenario": "worker_throughput_5000", "entity_count": 5000, "duration_ms": 12.0,
        "throughput_ips": 100.0, "worker_utilization": 0.5, "max_capacity": 8,
    }))
    assert perf_baseline.main(["--update"]) == 1
    assert json.loads(baseline.read_text()) == {"keep": 1}
    assert "scenario" in capsys.readouterr().out


def test_update_refuses_an_empty_dict(paths):
    latest, baseline = paths
    latest.write_text("{}")
    assert perf_baseline.main(["--update"]) == 1
    assert not baseline.exists()


def test_update_refuses_a_scenario_id_that_differs_from_its_key(paths, capsys):
    latest, baseline = paths
    latest.write_text(json.dumps({"IDLE_100": _entry("IDLE_500")}))
    assert perf_baseline.main(["--update"]) == 1
    assert "IDLE_100" in capsys.readouterr().out
    assert not baseline.exists()


def test_update_refuses_an_entry_missing_required_keys(paths, capsys):
    latest, baseline = paths
    entry = _entry("IDLE_100")
    del entry["tick_ms"]
    latest.write_text(json.dumps({"IDLE_100": entry}))
    assert perf_baseline.main(["--update"]) == 1
    assert "tick_ms" in capsys.readouterr().out
    assert not baseline.exists()


def test_update_with_a_missing_latest_exits_non_zero(paths):
    assert perf_baseline.main(["--update"]) == 1


def test_update_with_unparseable_json_exits_non_zero(paths):
    latest, baseline = paths
    latest.write_text("{not json")
    assert perf_baseline.main(["--update"]) == 1
    assert not baseline.exists()


def test_run_step_invokes_run_perf_baseline_without_executing_it(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(perf_baseline.subprocess, "run", fake_run)
    assert perf_baseline.main([]) == 0
    assert len(calls) == 1
    assert calls[0][1].endswith("run_perf_baseline.py")
    assert not any("bench_worker_throughput" in part for part in calls[0])


def test_worker_throughput_script_writes_its_own_file_not_latest_json():
    source = (_REPO_ROOT / "tests" / "perf" / "bench_worker_throughput.py").read_text(encoding="utf-8")
    assert 'REPORT_FILENAME = "worker_throughput.json"' in source
    assert "latest.json" not in source.replace("`latest.json`", "")


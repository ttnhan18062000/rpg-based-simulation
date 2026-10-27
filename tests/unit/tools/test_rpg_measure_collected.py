"""``paired --collected``: compare results produced elsewhere, executing nothing (TCK-20261026-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS).

Staged result files only (no simulation, no git): missing results, runner identity, repeat files, rejected flags, the verdict JSON, cost.json, and
that the collected table is the local table plus the one ``- runners:`` line.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.rpg_measure import paired

BASE, NEW = "a" * 40, "b" * 40
TICKS = 10
SEEDS = (42, 43)
START = [(1, "merchant", 1), (2, "guard", 1), (3, "wolf", 0)]
RUNNER = {"name": "gh-1", "image": "ubuntu-24.04", "cpu_model": "x", "nproc": 4, "mem_total_mb": 16000, "python": "3.12.3", "os": "Linux 6.8"}


def _run(world, seed, new_dead=0, final_hash="h", start_hash="s"):
    rows = [[i, k, c, 1] for i, k, c in START]
    fin = {"1": [0 if new_dead >= 1 else 1, "COMBAT" if new_dead >= 1 else None, "merchant"], "2": [0 if new_dead >= 2 else 1, "COMBAT" if new_dead >= 2 else None, "guard"], "3": [1, None, "wolf"]}
    return {"world": world, "seed": seed, "start": rows, "final": fin, "counters": None, "perception_samples": 5, "final_hash": final_hash,
            "start_hash": start_hash, "audit_mode": True, "signals_zeroed": True, "adds": {}}


def _put(cache: Path, sha: str, w: str, s: int, run: dict, ticks=TICKS, repeat=False, runner=None, wall=1.5):
    path = paired.result_path(cache, sha, ticks, w, s, repeat)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run), encoding="utf-8")
    if runner is not None:
        paired.cost_path(path).write_text(json.dumps({"wall_seconds": wall, "peak_rss_mb": None, "runner": runner}), encoding="utf-8")
    return path


def stage(cache: Path, new_dead=0, repeat=True, runner=RUNNER, neutral=False):
    for w in paired.WORLDS:
        for s in ((42,) if neutral else SEEDS):
            t = paired.NEUTRAL_TICKS if neutral else TICKS
            _put(cache, BASE, w, s, _run(w, s), ticks=t, runner=runner)
            _put(cache, NEW, w, s, _run(w, s, new_dead), ticks=t, runner=runner)
            if repeat and s == 42 and not neutral:
                _put(cache, BASE, w, s, _run(w, s), repeat=True, runner=runner)


def collected(cache, *extra, capsys=None):
    argv = ["--collected", str(cache), "--base", BASE, "--new", NEW, "--seeds", *map(str, SEEDS), "--ticks", str(TICKS), *extra]
    return paired.main(argv)


def test_a_complete_collected_cache_gives_the_report_and_exit_0(tmp_path, capsys):
    stage(tmp_path)
    assert collected(tmp_path) == 0
    out = capsys.readouterr().out
    assert "## Paired measurement" in out and "- runners (collected off host): gh-1/ubuntu-24.04 python 3.12.3 Linux 6.8" in out


def test_a_missing_result_is_refused_with_its_keys_and_nothing_runs(tmp_path, capsys, monkeypatch):
    stage(tmp_path)
    paired.result_path(tmp_path, NEW, TICKS, "urban_political", 43).unlink()
    paired.result_path(tmp_path, BASE, TICKS, "crowded_frontier", 42, True).unlink()
    monkeypatch.setattr(paired, "run_one", lambda *a, **k: pytest.fail("a collected run must not execute anything"))
    monkeypatch.setattr(paired, "_git", lambda *a, **k: pytest.fail("a collected run must not call git"))
    assert collected(tmp_path) == 2
    err = capsys.readouterr().err
    assert "new:urban_political:43" in err and "base-repeat:crowded_frontier:42" in err and err.startswith("REFUSED")


@pytest.mark.parametrize("field,value", [("python", "3.11.9"), ("os", "Linux 5.15"), ("image", "ubuntu-22.04")])
def test_a_runner_whose_python_os_or_image_differs_is_refused(tmp_path, capsys, field, value):
    stage(tmp_path)
    _put(tmp_path, NEW, "urban_political", 43, _run("urban_political", 43), runner={**RUNNER, field: value})
    assert collected(tmp_path) == 2
    err = capsys.readouterr().err
    assert "urban_political:43" in err and field in err


def test_a_repeat_runner_that_differs_from_its_base_is_refused(tmp_path, capsys):
    stage(tmp_path)
    _put(tmp_path, BASE, "frontier_living_world", 42, _run("frontier_living_world", 42), repeat=True, runner={**RUNNER, "python": "3.13.0"})
    assert collected(tmp_path) == 2
    assert "frontier_living_world:42 python" in capsys.readouterr().err


def test_a_different_runner_name_or_cpu_is_not_a_refusal(tmp_path, capsys):
    stage(tmp_path)
    _put(tmp_path, NEW, "urban_political", 43, _run("urban_political", 43), runner={**RUNNER, "name": "gh-2", "cpu_model": "y", "nproc": 2})
    assert collected(tmp_path) == 0


def test_a_repeat_file_is_read_and_never_unlinked(tmp_path):
    stage(tmp_path)
    repeats = sorted(p for p in tmp_path.rglob("*.json") if "-repeat" in str(p.parent) and ".cost." not in p.name)
    assert repeats
    assert collected(tmp_path) == 0
    assert all(p.exists() and paired.cost_path(p).exists() for p in repeats)


def test_a_repeat_that_is_not_byte_identical_is_refused(tmp_path, capsys):
    stage(tmp_path)
    _put(tmp_path, BASE, "frontier_living_world", 42, _run("frontier_living_world", 42, final_hash="DIFFERENT"), repeat=True, runner=RUNNER)
    assert collected(tmp_path) == 2
    assert "not byte-identical" in capsys.readouterr().err


@pytest.mark.parametrize("extra", [["--jobs", "2"], ["--clean-cache"]])
def test_jobs_and_clean_cache_are_rejected_with_collected(tmp_path, capsys, extra):
    stage(tmp_path)
    with pytest.raises(SystemExit) as e:
        collected(tmp_path, *extra)
    assert e.value.code == 2 and "not allowed" in capsys.readouterr().err


@pytest.mark.parametrize("flag", ["--base", "--new"])
def test_a_short_or_non_hex_sha_is_rejected(tmp_path, capsys, flag):
    argv = ["--collected", str(tmp_path), "--base", BASE, "--new", NEW]
    argv[argv.index(flag) + 1] = "abc123"
    with pytest.raises(SystemExit) as e:
        paired.main(argv)
    assert e.value.code == 2 and "40-hex" in capsys.readouterr().err


def _verdict(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_verdict_json_pass_stop_refused_and_report_only(tmp_path):
    v = tmp_path / "v.json"
    stage(tmp_path / "pass", new_dead=0)
    assert collected(tmp_path / "pass", "--verdict-json", str(v)) == 0
    assert _verdict(v) == {"outcome": "PASS", "mode": "step", "detail": None}
    stage(tmp_path / "stop", new_dead=2)
    assert collected(tmp_path / "stop", "--verdict-json", str(v), "--floor-per-seed", "0") == 0  # a STOP is in the table; the exit code stays 0
    got = _verdict(v)
    assert got["outcome"] == "STOP" and got["mode"] == "step" and "frontier_living_world" in got["detail"]
    assert collected(tmp_path / "stop", "--verdict-json", str(v), "--floor-per-seed", "0", "--report-only") == 0
    assert _verdict(v) == {"outcome": "PASS", "mode": "report_only", "detail": None}
    paired.result_path(tmp_path / "pass", NEW, TICKS, "urban_political", 43).unlink()
    assert collected(tmp_path / "pass", "--verdict-json", str(v)) == 2
    got = _verdict(v)
    assert got["outcome"] == "REFUSED" and got["mode"] == "step" and "urban_political:43" in got["detail"]


def test_neutral_collected_pass_and_stop_with_exit_1(tmp_path, capsys):
    v = tmp_path / "v.json"
    stage(tmp_path, neutral=True)
    argv = ["--collected", str(tmp_path), "--base", BASE, "--new", NEW, "--neutral", "--verdict-json", str(v)]
    assert paired.main(argv) == 0
    assert _verdict(v) == {"outcome": "PASS", "mode": "neutral", "detail": None}
    assert "NEUTRAL PASS" in capsys.readouterr().out
    _put(tmp_path, NEW, "urban_political", 42, _run("urban_political", 42, final_hash="X"), ticks=paired.NEUTRAL_TICKS, runner=RUNNER)
    assert paired.main(argv) == 1
    got = _verdict(v)
    assert got["outcome"] == "STOP" and got["mode"] == "neutral" and "urban_political" in got["detail"]


def test_a_verdict_write_failure_warns_and_keeps_the_exit_code(tmp_path, capsys):
    stage(tmp_path)
    assert collected(tmp_path, "--verdict-json", str(tmp_path / "no" / "such" / "dir" / "v.json")) == 0
    assert "WARNING: could not write --verdict-json" in capsys.readouterr().err


def test_a_missing_cost_json_gives_null_wall_and_rss_and_is_not_a_refusal(tmp_path, capsys):
    stage(tmp_path, runner=None)
    path = paired.result_path(tmp_path, BASE, TICKS, "urban_political", 42)
    assert paired.load_cost(path) is None
    assert collected(tmp_path) == 0
    assert "none recorded" in capsys.readouterr().out
    _put(tmp_path, BASE, "urban_political", 42, _run("urban_political", 42), runner=RUNNER)
    cost = paired.load_cost(path)
    assert cost["wall_seconds"] == 1.5 and cost["peak_rss_mb"] is None


def test_the_collected_table_is_the_local_table_plus_one_runners_line(tmp_path, capsys, monkeypatch):
    stage(tmp_path)
    assert collected(tmp_path) == 0
    collected_out = capsys.readouterr().out
    # the local path on the same cache: git and tree extraction stubbed, the repeat re-run stubbed to rewrite the base result
    monkeypatch.setattr(paired, "_git", lambda *a, **k: str(tmp_path))
    monkeypatch.setattr(paired, "prepare_tree", lambda repo, rev, cache: (rev, tmp_path))
    monkeypatch.setattr(paired, "run_one", lambda tree, world, seed, ticks, out: out.write_text(json.dumps(_run(world, seed)), encoding="utf-8"))
    assert paired.main(["--base", BASE, "--new", NEW, "--cache", str(tmp_path), "--seeds", "42", "43", "--ticks", str(TICKS), "--jobs", "1"]) == 0
    local_out = capsys.readouterr().out
    extra = [ln for ln in collected_out.splitlines() if ln not in local_out.splitlines()]
    assert len(extra) == 1 and extra[0].startswith("- runners (collected off host):")
    assert [ln for ln in collected_out.splitlines() if not ln.startswith("- runners (collected")] == local_out.splitlines()

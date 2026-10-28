"""TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST: the matrix plan, one arm's run and cost record, and the assemble refusals (AC2). Fake artifacts only."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.rpg_measure import paired
from tools.test_architecture import paired_arms as pa

BASE, NEW = "a" * 40, "b" * 40
W = "frontier_living_world"
RUNNER = {"name": "GitHub Actions 7", "image": "ubuntu24-20260101.1.0", "cpu_model": "AMD EPYC 7763", "nproc": 4, "mem_total_mb": 16000, "python": "3.13.1", "os": "Ubuntu 24.04.1 LTS"}


def _write(job: Path, sha: str, world: str, seed: int, *, repeat=False, runner=None, doc="{}", ticks=5000, child="c0ffee00"):
    directory = job / "results" / f"{sha[:12]}-{child}-{ticks}{'-repeat' if repeat else ''}"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{world}_{seed}.json").write_text(doc)
    (directory / f"{world}_{seed}.cost.json").write_text(json.dumps({"wall_seconds": 1.5, "peak_rss_mb": 200.0, "runner": runner or RUNNER}))


def _pair_job(root: Path, world=W, seed=42, **kw) -> Path:
    job = root / f"paired-arms-s-{world}-s{seed}"
    _write(job, BASE, world, seed, **kw)
    _write(job, NEW, world, seed, **kw)
    return job


# ---- plan

def test_the_plan_takes_its_world_set_from_paired_pys_constants_and_keeps_no_copy():
    assert not hasattr(pa, "WORLDS") and not hasattr(pa, "TERRAIN_WORLD") and pa.SELF_CHECK_SEED == 42


def _plan(worlds=",".join(paired.WORLDS), seeds="42,43", self_check="seed42"):
    return pa.plan_matrix(worlds, seeds, self_check)


def test_the_plan_has_a_pair_job_per_world_and_seed_and_seed_42_self_jobs_per_world():
    plan = _plan()
    pairs = [(e["world"], e["seed"]) for e in plan["include"] if e["kind"] == "pair"]
    selfs = [(e["world"], e["seed"]) for e in plan["include"] if e["kind"] == "self"]
    assert sorted(pairs) == sorted((w, s) for w in paired.WORLDS for s in (42, 43)) and sorted(selfs) == sorted((w, 42) for w in paired.WORLDS)
    assert plan["terrain"] is False


def test_the_self_check_modes_full_and_off_and_seed_42_even_when_the_seeds_omit_it():
    assert len([e for e in _plan(self_check="full")["include"] if e["kind"] == "self"]) == 6
    assert [e for e in _plan(self_check="off")["include"] if e["kind"] == "self"] == []
    assert len([e for e in _plan(seeds="43,44")["include"] if e["kind"] == "self"]) == 3  # paired.py expects seed 42 per world whatever --seeds holds


def test_the_terrain_world_is_allowed_only_in_full_and_sets_terrain():
    plan = _plan(worlds=",".join([*paired.WORLDS, paired.TERRAIN_WORLD]))
    assert plan["terrain"] is True and any(e["world"] == paired.TERRAIN_WORLD for e in plan["include"])


@pytest.mark.parametrize("worlds, seeds, self_check", [
    (W, "42", "seed42"), (",".join(paired.WORLDS[:2]), "42", "seed42"), (",".join([*paired.WORLDS, paired.WORLDS[0]]), "42", "seed42"),
    (",".join([*paired.WORLDS, "x y"]), "42", "seed42"), (",".join(paired.WORLDS), "42,a", "seed42"), (",".join(paired.WORLDS), "", "seed42"), (",".join(paired.WORLDS), "42", "sometimes"),
])
def test_a_plan_that_paired_would_not_expect_is_refused(worlds, seeds, self_check):
    with pytest.raises(pa.ArmsRefused):
        pa.plan_matrix(worlds, seeds, self_check)


def test_the_step_slug_is_artifact_safe():
    assert pa.step_slug("D75 route/2: new") == "D75-route-2-new" and pa.step_slug("///") == "step"


def test_the_plan_cli_prints_the_github_output_lines(capsys):
    assert pa.main(["plan", "--worlds", ",".join(paired.WORLDS), "--seeds", "42", "--self-check", "off", "--step", "D75 route"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("matrix={") and lines[1:] == ["terrain=false", "slug=D75-route"]
    assert json.loads(lines[0][len("matrix="):])["include"][0] == {"world": paired.WORLDS[0], "seed": 42, "kind": "pair"}
    assert pa.main(["plan", "--worlds", "x", "--seeds", "42"]) == 2


# ---- run one arm (paired's own functions, faked)

def test_run_arm_uses_paireds_cache_key_and_writes_the_cost_beside_the_result(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(paired, "prepare_tree", lambda repo, rev, cache: (BASE, tmp_path / "tree"))

    def fake_run_one(tree, world, seed, ticks, out):
        calls.append((tree, world, seed, ticks, out))
        out.write_text("{}")

    monkeypatch.setattr(paired, "run_one", fake_run_one)
    cost = pa.run_arm(tmp_path, "main", "base", W, 42, 100, tmp_path / "cache")
    out = paired.result_path(tmp_path / "cache", BASE, 100, W, 42)
    assert calls == [(tmp_path / "tree", W, 42, 100, out)] and out.is_file()
    written = json.loads(out.with_name(f"{W}_42.cost.json").read_text())
    assert set(written) == {"wall_seconds", "peak_rss_mb", "runner"} and set(written["runner"]) == set(pa.IDENTITY_FIELDS) and written == cost
    again = pa.run_arm(tmp_path, "main", "base", W, 42, 100, tmp_path / "cache")  # cached: not run again
    assert len(calls) == 1 and again["wall_seconds"] == 0.0 and again["peak_rss_mb"] is None
    pa.run_arm(tmp_path, "main", "self", W, 42, 100, tmp_path / "cache", repeat=True)  # the repeat is its own result and always runs
    assert len(calls) == 2 and calls[1][4].parent.name.endswith("-repeat")
    with pytest.raises(pa.ArmsRefused):
        pa.run_arm(tmp_path, "main", "other", W, 42, 100, tmp_path / "cache")


# ---- assemble

def _assemble(root: Path, **kw):
    return pa.assemble(root, root.parent / "collected", base=kw.pop("base", BASE), new=kw.pop("new", NEW))


def test_assemble_merges_the_jobs_into_one_paired_cache_root(tmp_path):
    root = tmp_path / "arms"
    _pair_job(root, seed=42)
    _pair_job(root, seed=43)
    self_job = root / f"paired-arms-s-{W}-s42-self"
    _write(self_job, BASE, W, 42, doc="{}")  # the same bytes the pair job wrote
    _write(self_job, BASE, W, 42, repeat=True)
    summary = _assemble(root)
    collected = tmp_path / "collected"
    assert sorted(p.name for p in (collected / "results").iterdir()) == sorted([f"{BASE[:12]}-c0ffee00-5000", f"{NEW[:12]}-c0ffee00-5000", f"{BASE[:12]}-c0ffee00-5000-repeat"])
    assert (collected / "results" / f"{BASE[:12]}-c0ffee00-5000" / f"{W}_43.json").is_file()
    assert len(summary["jobs"]) == 3 and len(summary["arms"]) == 6 and json.loads((collected / "identities.json").read_text()) == summary


@pytest.mark.parametrize("field, other", [("python", "3.13.2"), ("os", "Ubuntu 22.04.5 LTS")])
def test_assemble_refuses_jobs_that_differ_in_python_version_or_os(tmp_path, field, other):
    root = tmp_path / "arms"
    _pair_job(root, seed=42)
    _pair_job(root, seed=43, runner={**RUNNER, field: other})
    with pytest.raises(pa.ArmsRefused, match=f"different {field} values"):
        _assemble(root)
    assert not (tmp_path / "collected").exists()  # nothing merged


def test_assemble_allows_a_different_cpu_model_runner_name_and_image_across_jobs(tmp_path):
    root = tmp_path / "arms"
    _pair_job(root, seed=42)
    _pair_job(root, seed=43, runner={**RUNNER, "cpu_model": "Intel Xeon", "name": "GitHub Actions 9", "image": "ubuntu24-20260201.1.0"})
    assert len(_assemble(root)["jobs"]) == 2  # the CPU model varies between runners: it is a description, not a pin


def test_assemble_refuses_the_arms_of_one_key_that_ran_on_different_images(tmp_path):
    root = tmp_path / "arms"
    job = _pair_job(root, seed=42)
    _write(job, NEW, W, 42, runner={**RUNNER, "image": "ubuntu24-20260201.1.0"})
    with pytest.raises(pa.ArmsRefused, match=f"{W}_42: its arms ran on different image"):
        _assemble(root)


def test_assemble_refuses_a_pair_job_missing_either_arm(tmp_path):
    root = tmp_path / "arms"
    job = root / f"paired-arms-s-{W}-s42"
    _write(job, BASE, W, 42)
    with pytest.raises(pa.ArmsRefused, match="needs both the base"):
        _assemble(root)
    _write(job, NEW, W, 43)  # the new arm of ANOTHER key does not count: both arms must be the same key from the same job
    with pytest.raises(pa.ArmsRefused, match="needs both the base"):
        _assemble(root)


def test_assemble_refuses_a_result_without_a_runner_record(tmp_path):
    root = tmp_path / "arms"
    job = _pair_job(root)
    cost = next(job.glob("results/*/*.cost.json"))
    cost.write_text(json.dumps({"wall_seconds": 1.0, "peak_rss_mb": None}))
    with pytest.raises(pa.ArmsRefused, match="no runner record"):
        _assemble(root)
    cost.write_text(json.dumps({"wall_seconds": 1.0, "peak_rss_mb": None, "runner": {"python": "3.13"}}))
    with pytest.raises(pa.ArmsRefused, match="no runner record with"):
        _assemble(root)
    cost.write_text("not json")
    with pytest.raises(pa.ArmsRefused, match="unreadable"):
        _assemble(root)


def test_assemble_refuses_two_jobs_writing_different_bytes_to_one_result(tmp_path):
    root = tmp_path / "arms"
    _pair_job(root, seed=42, doc='{"a": 1}')
    self_job = root / f"paired-arms-s-{W}-s42-self"
    _write(self_job, BASE, W, 42, doc='{"a": 2}')
    with pytest.raises(pa.ArmsRefused, match="different bytes"):
        _assemble(root)


def test_assemble_refuses_nothing_to_assemble_and_a_bad_sha(tmp_path):
    (tmp_path / "arms").mkdir()
    with pytest.raises(pa.ArmsRefused, match="no job artifacts"):
        _assemble(tmp_path / "arms")
    with pytest.raises(pa.ArmsRefused, match="40-character"):
        _assemble(tmp_path / "arms", base="main")


def test_the_assemble_cli_exits_2_with_the_refusal_and_0_on_a_good_set(tmp_path, capsys):
    root = tmp_path / "arms"
    _pair_job(root, seed=42)
    args = ["assemble", "--in", str(root), "--out", str(tmp_path / "collected"), "--base", BASE, "--new", NEW]
    assert pa.main(args) == 0 and "assembled 1 job(s), 2 arm run(s)" in capsys.readouterr().out
    _pair_job(root, seed=43, runner={**RUNNER, "python": "3.12.0"})
    assert pa.main(args) == 2 and "REFUSED: the jobs ran on different python values" in capsys.readouterr().err


# ---- round trip through rpg's real --collected

def _doc(world: str, seed: int) -> dict:
    """A minimal result document in the shape paired.py reads (no simulation): two people alive, audit flags True."""
    return {"world": world, "seed": seed, "start": [[1, "merchant", 1, 1], [2, "guard", 1, 1]], "final": {"1": [1, None, "merchant"], "2": [1, None, "guard"]},
            "counters": None, "perception_samples": 5, "final_hash": "h", "start_hash": "s", "audit_mode": True, "signals_zeroed": True, "adds": {}}


def test_jobs_run_by_run_arm_and_assembled_are_accepted_by_paireds_real_collected_compare(tmp_path, monkeypatch, capsys):
    """The matrix plan's jobs, each with its own cache like a CI job, written by run_arm (only the child is faked), assembled, then compared by the real
    ``paired.main(["--collected", ...])``: exit 0, the one runners line, and nothing executed. Guards the layout and cost.json contract against rpg's merged reader."""
    ticks = 10
    monkeypatch.setattr(paired, "prepare_tree", lambda repo, rev, cache: ({"base": BASE, "new": NEW}[rev], tmp_path / "tree"))
    monkeypatch.setattr(paired, "run_one", lambda tree, world, seed, t, out: out.write_text(json.dumps(_doc(world, seed))))
    monkeypatch.setattr(pa, "runner_identity", lambda env=None: dict(RUNNER))
    root = tmp_path / "arms"
    for job in pa.plan_matrix(",".join(paired.WORLDS), "42,43", "seed42")["include"]:
        w, s = job["world"], job["seed"]
        cache = root / f"paired-arms-s-{w}-s{s}{'-self' if job['kind'] == 'self' else ''}"
        if job["kind"] == "pair":
            pa.run_arm(tmp_path, "base", "base", w, s, ticks, cache)
            pa.run_arm(tmp_path, "new", "new", w, s, ticks, cache)
        else:
            pa.run_arm(tmp_path, "base", "base", w, s, ticks, cache)
            pa.run_arm(tmp_path, "base", "self", w, s, ticks, cache, repeat=True)
    pa.assemble(root, tmp_path / "collected", base=BASE, new=NEW)
    monkeypatch.setattr(paired, "run_one", lambda *a: pytest.fail("--collected must execute nothing"))
    capsys.readouterr()
    assert paired.main(["--collected", str(tmp_path / "collected"), "--base", BASE, "--new", NEW, "--seeds", "42", "43", "--ticks", str(ticks)]) == 0
    out = capsys.readouterr().out
    assert "## Paired measurement" in out and "self-check (seed42, 3 runs): spread 0" in out
    assert [line for line in out.splitlines() if line.startswith("- runners")] == [f"- runners (collected off host): {RUNNER['name']}/{RUNNER['image']} python {RUNNER['python']} {RUNNER['os']} ({RUNNER['cpu_model']}, nproc {RUNNER['nproc']})"]

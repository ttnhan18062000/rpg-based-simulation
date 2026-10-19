"""TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS: determinism, process isolation, crash handling, pooling and the harness hash."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.test_architecture import rpg_gate_harness as h
from tools.test_architecture.rpg_gate_baseline import load_config

STUB = "tests.helpers.rpg_gate_stub_metrics"
WORLD = "sandbox_world"
SHA = "0123456789abcdef"
ROOT = h.repo_root()


def _cfg(tmp_path: Path, seeds=(1, 2), ticks=15, worlds=(WORLD,)) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(f"worlds: {list(worlds)}\nseeds: {list(seeds)}\nticks: {ticks}\nstale_after_days: 30\n")
    return path


def _run(tmp_path: Path, out: str, **kw):
    cfg = _cfg(tmp_path, **kw)
    return h.run_matrix(load_config(cfg), cfg, tmp_path / out, metrics_module=STUB, sha=SHA, workers=2, timeout_s=300)


def _doc(tmp_path: Path, out: str, name: str) -> dict:
    return json.loads((tmp_path / out / name).read_text())


def test_same_sha_world_seed_gives_byte_identical_documents(tmp_path):
    _run(tmp_path, "a")
    _run(tmp_path, "b")
    for name in (h.doc_name(WORLD, 1), h.doc_name(WORLD, 2), h.doc_name(WORLD, None)):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()
    doc = _doc(tmp_path, "a", h.doc_name(WORLD, 1))
    assert doc["schema"] == h.SCHEMA and doc["status"] == "ok" and doc["sha"] == SHA and doc["ticks"] == 15
    assert doc["harness_hash"] == h.harness_hash(tmp_path / "config.yaml", metrics_module=STUB)


def test_a_module_global_mutated_in_one_run_does_not_reach_the_next(tmp_path):
    _run(tmp_path, "a")
    leaks = [next(m["value"] for m in _doc(tmp_path, "a", h.doc_name(WORLD, s))["metrics"] if m["id"] == "S2.leak") for s in (1, 2)]
    assert leaks == [1, 1]  # a fresh process each; in one process the second call would see 2


def test_the_stand_in_really_leaks_inside_one_process():
    """Negative control for the test above: without process isolation the global does carry over."""
    from tests.helpers import rpg_gate_stub_metrics as stub

    art = SimpleNamespace(seed=1, ticks=1, state=SimpleNamespace(entities={}), events_path=Path("none"))
    before = stub.LEAK
    first = stub.compute(art)[1]["value"]
    second = stub.compute(art)[1]["value"]
    assert (first, second) == (before + 1, before + 2)


def test_a_crashing_run_is_no_data_with_its_error_and_the_others_complete(tmp_path, monkeypatch):
    monkeypatch.setenv("RPG_GATE_STUB_CRASH_SEED", "2")
    matrix = _run(tmp_path, "a", seeds=(1, 2, 3))
    status = {r["seed"]: r["status"] for r in matrix["runs"]}
    assert status == {1: "ok", 2: "no-data", 3: "ok"}
    bad = _doc(tmp_path, "a", h.doc_name(WORLD, 2))
    assert bad["metrics"] == [] and "stub crash for seed 2" in bad["error"]
    assert bad["reason"] == "metric_error" and bad["exception_type"] == "RuntimeError"  # an exception in compute


def test_a_world_with_a_no_data_seed_gets_no_data_pooled_metrics_never_a_partial_pool(tmp_path, monkeypatch):
    monkeypatch.setenv("RPG_GATE_STUB_CRASH_SEED", "2")
    matrix = _run(tmp_path, "a")
    pooled = _doc(tmp_path, "a", h.doc_name(WORLD, None))
    assert matrix["pooled"][WORLD]["status"] == "no-data" and pooled["metrics"] == [] and "without data" in pooled["error"] and pooled["reason"] == "seed_no_data"


def test_a_complete_world_is_pooled_in_a_fresh_process(tmp_path):
    matrix = _run(tmp_path, "a")
    pooled = _doc(tmp_path, "a", h.doc_name(WORLD, None))
    assert matrix["pooled"][WORLD]["status"] == "ok"
    assert pooled["metrics"][0]["scope"] == "pooled" and "seed" not in pooled


def test_a_missing_world_is_no_data_not_a_harness_failure(tmp_path):
    matrix = _run(tmp_path, "a", worlds=("no_such_world",))
    assert {r["status"] for r in matrix["runs"]} == {"no-data"}
    doc = _doc(tmp_path, "a", h.doc_name("no_such_world", 1))
    assert doc["reason"] == "run_error" and doc["exception_type"]  # the world could not be compiled: an exception in the simulation


def test_a_timeout_is_no_data(tmp_path):
    cfg = _cfg(tmp_path)
    matrix = h.run_matrix(load_config(cfg), cfg, tmp_path / "a", metrics_module=STUB, sha=SHA, workers=2, timeout_s=0.01)
    assert {r["status"] for r in matrix["runs"]} == {"no-data"} and "timed out" in matrix["runs"][0]["error"]
    assert _doc(tmp_path, "a", h.doc_name(WORLD, 1))["reason"] == "harness_error"


def test_run_directories_are_removed_by_id_and_cost_is_recorded(tmp_path):
    matrix = _run(tmp_path, "a")
    for seed in (1, 2):
        assert not list((ROOT / h.RUNS_DIR).glob(f"{h.run_id_for(WORLD, seed, SHA)}*"))
    assert all(r["wall_seconds"] > 0 and r["peak_rss_mb"] > 0 for r in matrix["runs"])
    assert "wall_seconds" in matrix and "peak_rss_mb" not in _doc(tmp_path, "a", h.doc_name(WORLD, 1))  # cost stays out of the document


def test_the_harness_hash_changes_with_the_config_the_pins_and_the_code(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    base = h.harness_hash(cfg)
    assert h.harness_hash(cfg) == base
    cfg.write_text(cfg.read_text() + "# changed\n")
    assert h.harness_hash(cfg) != base
    cfg.write_text(cfg.read_text().replace("# changed\n", ""))
    assert h.harness_hash(cfg) == base
    monkeypatch.setitem(h.PIN_SETTINGS, "governor", "Other")
    assert h.harness_hash(cfg) != base
    monkeypatch.undo()
    fake_root = tmp_path / "root"
    for rel in h._HARNESS_SOURCES:
        (fake_root / rel).parent.mkdir(parents=True, exist_ok=True)
        (fake_root / rel).write_text("x")
    code_a = h.harness_hash(cfg, fake_root)
    (fake_root / h._HARNESS_SOURCES[1]).write_text("y")
    assert h.harness_hash(cfg, fake_root) != code_a


def test_the_pins_are_the_ones_the_ticket_names():
    run_source = (ROOT / "tools/test_architecture/rpg_gate_run.py").read_text()
    for needle in ("PinnedNormalGovernor()", "LocalSequentialExecutor()", '"audit_mode": True', "run_id=run_id"):
        assert needle in run_source


def test_the_metric_module_is_named_in_one_place_and_the_run_hands_it_the_event_stream(tmp_path):
    assert h.DEFAULT_METRICS_MODULE == "src.observability.rpg_gate_metrics"
    _run(tmp_path, "a")
    counts = next(m for m in _doc(tmp_path, "a", h.doc_name(WORLD, 1))["metrics"] if m["id"] == "V9")["counts"]
    assert counts["events_file_exists"] is True


def test_the_harness_hash_covers_the_metrics_module_source_and_name(tmp_path):
    cfg = _cfg(tmp_path)
    root = tmp_path / "root"
    for rel in h._HARNESS_SOURCES:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text("x")
    module = root / "pkg" / "metrics.py"
    module.parent.mkdir(parents=True)
    module.write_text("V = 1")
    base = h.harness_hash(cfg, root, "pkg.metrics")
    module.write_text("V = 2")  # a changed metric definition
    assert h.harness_hash(cfg, root, "pkg.metrics") != base
    assert h.harness_hash(cfg, root, "pkg.metrics:compute") != h.harness_hash(cfg, root, "pkg.metrics")  # a different name is a different input
    assert h.harness_hash(cfg, root, "pkg.absent") != base  # a module not there yet hashes as a marker, so its arrival changes the hash
    absent = h.harness_hash(cfg, root, "pkg.later")
    (root / "pkg" / "later.py").write_text("V = 1")
    assert h.harness_hash(cfg, root, "pkg.later") != absent


def test_the_real_stub_source_is_hashed_by_the_run_that_records_it(tmp_path):
    cfg = _cfg(tmp_path)
    with_stub = h.harness_hash(cfg, metrics_module=STUB)
    assert with_stub != h.harness_hash(cfg, metrics_module="tests.helpers.not_there")


def test_two_invocations_on_one_sha_use_different_run_ids():
    assert h.run_id_for(WORLD, 1, SHA, "7-1") != h.run_id_for(WORLD, 1, SHA, "8-1")


def test_every_document_records_the_seed_set_its_floor_was_computed_from(tmp_path):
    _run(tmp_path, "a", seeds=(1, 2, 3))
    for name in (h.doc_name(WORLD, 1), h.doc_name(WORLD, 2), h.doc_name(WORLD, 3), h.doc_name(WORLD, None)):
        assert _doc(tmp_path, "a", name)["floor_seeds"] == [1, 2, 3], name


def test_a_rerun_child_gets_the_full_seed_set_never_just_the_seed_it_reruns(tmp_path):
    """The report's same-SHA rerun calls run_one for one (world, seed) with the whole config: the floor's seed set must still be all seeds, else the rerun's floor differs."""
    cfg = _cfg(tmp_path, seeds=(1, 2, 3))
    out = tmp_path / "rerun"
    out.mkdir()
    h.run_one(WORLD, 2, load_config(cfg), out, metrics_module=STUB, sha=SHA, hhash="hh", keep_runs=False, timeout_s=300, token="rerun-test")
    assert json.loads((out / h.doc_name(WORLD, 2)).read_text())["floor_seeds"] == [1, 2, 3]

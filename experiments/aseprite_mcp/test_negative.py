"""Negative / failure-mode suite against real Aseprite (M1-W06). Need real Aseprite + bwrap.

Every test asserts the exact observable outcome (error text or on-disk state).

Run: .venv/bin/python -m pytest experiments/aseprite_mcp -q
"""

from __future__ import annotations

import errno
import hashlib
import logging
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adapter  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (Path(adapter.ASEPRITE).exists() and shutil.which("bwrap")),
    reason="requires aseprite and bwrap",
)

CLEAR = "#00000000"
PX = [{"op": "pixels", "pixels": [{"x": 1, "y": 1, "color": "#ff0000"}]}]


@pytest.fixture(autouse=True)
def workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "WORKSPACE", tmp_path / "ws")
    return tmp_path / "ws"


def sprite_dir(ws, name="s"):
    return ws / "sprites" / name


def revisions(ws, name="s"):
    """Sorted revision names; asserts the chain is gap-free and every revision has a sidecar."""
    files = sorted(p.name for p in sprite_dir(ws, name).glob("r????.aseprite"))
    assert files == [f"r{i:04d}.aseprite" for i in range(1, len(files) + 1)], files
    for f in files:
        assert (sprite_dir(ws, name) / f).with_suffix(".sha256").is_file(), f"{f} lacks a sidecar"
    return [f[:5] for f in files]


def sidecars(ws, name="s"):
    return sorted(p.name for p in sprite_dir(ws, name).glob("*.sha256"))


def jobs_empty(ws):
    jobs = ws / ".jobs"
    assert not jobs.exists() or list(jobs.iterdir()) == [], list(jobs.iterdir())


def aseprite_pids():
    out = subprocess.run(
        ["pgrep", "-f", "aseprite -b --script /lua/ops.lua"], capture_output=True, text=True
    )
    return out.stdout.split()


def mk(name="s"):
    return adapter.new_sprite(name, 4, 4, CLEAR)


# ------------------------------------------------------------------ N1 timeout


def test_timeout_publishes_nothing_and_leaves_no_process(workspace, monkeypatch):
    mk()
    monkeypatch.setattr(adapter, "JOB_TIMEOUT_S", 0.01)
    with pytest.raises(adapter.AdapterError, match=r"aseprite timed out after 0\.01s"):
        adapter.apply_ops("s", "r0001", PX)
    assert revisions(workspace) == ["r0001"]
    jobs_empty(workspace)
    deadline = time.monotonic() + 10  # bounded poll for the sandbox to be reaped, not a sync sleep
    while aseprite_pids() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert aseprite_pids() == [], "an aseprite process outlived the timeout"
    monkeypatch.undo()
    monkeypatch.setattr(adapter, "WORKSPACE", workspace)
    assert adapter.apply_ops("s", "r0001", PX)["revision"] == "r0002"  # still usable


# ------------------------------------------------------------------ N2 corrupt input


def test_corrupt_input_with_matching_hash_is_rejected_by_aseprite(workspace):
    mk()
    r1 = sprite_dir(workspace) / "r0001.aseprite"
    garbage = b"this is definitely not an aseprite file" * 4
    r1.write_bytes(garbage)
    r1.with_suffix(".sha256").write_text(hashlib.sha256(garbage).hexdigest() + "\n")
    # the hash gate passes (hash matches), so only Aseprite itself can refuse it
    adapter._resolve_revision("s", None)
    with pytest.raises(adapter.AdapterError, match=r"aseprite produced no result|operation failed"):
        adapter.apply_ops("s", "r0001", PX)
    assert revisions(workspace) == ["r0001"]
    jobs_empty(workspace)
    with pytest.raises(adapter.AdapterError, match=r"aseprite produced no result|operation failed"):
        adapter.inspect_sprite("s")
    jobs_empty(workspace)


def test_tampered_input_without_matching_hash_fails_the_hash_gate(workspace):
    mk()
    (sprite_dir(workspace) / "r0001.aseprite").write_bytes(b"tampered")
    with pytest.raises(adapter.AdapterError, match="failed its content-hash check"):
        adapter.apply_ops("s", "r0001", PX)
    assert revisions(workspace) == ["r0001"]
    jobs_empty(workspace)


# ------------------------------------------------------------------ N3 publish failure


def test_link_failure_publishes_no_revision_or_orphan_sidecar(workspace, monkeypatch):
    mk()

    def boom(src, dst, **kw):
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(adapter.os, "link", boom)
    with pytest.raises(adapter.AdapterError, match="could not publish revision"):
        adapter.apply_ops("s", "r0001", PX)
    monkeypatch.undo()
    monkeypatch.setattr(adapter, "WORKSPACE", workspace)
    assert revisions(workspace) == ["r0001"]
    assert sidecars(workspace) == ["r0001.sha256"]  # no orphan r0002.sha256
    jobs_empty(workspace)
    assert adapter.apply_ops("s", "r0001", PX)["revision"] == "r0002"  # later edit works
    assert revisions(workspace) == ["r0001", "r0002"]


@pytest.mark.parametrize("fail_at", ["create", "write"])
def test_sidecar_failure_publishes_no_revision(workspace, monkeypatch, fail_at):
    mk()
    import builtins

    class WriteFails:
        def __init__(self, fh):
            self._fh = fh

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self._fh.close()

        def write(self, data):
            self._fh.write(data[:4])  # a partial sidecar is left behind unless cleaned up
            raise OSError(errno.EIO, "Input/output error")

    def fake_open(file, mode="r", *a, **kw):
        if str(file).endswith(".sha256") and "x" in mode:
            if fail_at == "create":
                raise OSError(errno.EIO, "Input/output error")
            return WriteFails(builtins.open(file, mode, *a, **kw))
        return builtins.open(file, mode, *a, **kw)

    monkeypatch.setattr(adapter, "open", fake_open, raising=False)
    with pytest.raises(adapter.AdapterError, match="could not publish revision"):
        adapter.apply_ops("s", "r0001", PX)
    monkeypatch.undo()
    monkeypatch.setattr(adapter, "WORKSPACE", workspace)
    # a revision file without a sidecar would brick the sprite; none may be visible, no partial sidecar left
    assert revisions(workspace) == ["r0001"]
    assert sidecars(workspace) == ["r0001.sha256"]
    assert adapter.inspect_sprite("s")["revision"] == "r0001"
    assert adapter.apply_ops("s", "r0001", PX)["revision"] == "r0002"


# ------------------------------------------------------------------ N4/N5 races


def _race(fn, n):
    barrier = threading.Barrier(n)

    def run(_):
        barrier.wait()
        try:
            return ("ok", fn())
        except adapter.AdapterError as exc:
            return ("err", str(exc))

    with ThreadPoolExecutor(max_workers=n) as pool:
        return list(pool.map(run, range(n)))


def test_same_base_race_exactly_one_winner(workspace):
    mk()
    n = 6
    results = _race(lambda: adapter.apply_ops("s", "r0001", PX), n)
    wins = [r for r in results if r[0] == "ok"]
    errs = [r[1] for r in results if r[0] == "err"]
    assert len(wins) == 1 and wins[0][1]["revision"] == "r0002"
    assert len(errs) == n - 1
    assert all(e.startswith("stale base_revision r0001; latest is r0002") for e in errs), errs
    assert revisions(workspace) == ["r0001", "r0002"]
    jobs_empty(workspace)


def test_first_creation_race_exactly_one_r0001(workspace):
    n = 6
    results = _race(lambda: mk(), n)
    wins = [r for r in results if r[0] == "ok"]
    errs = [r[1] for r in results if r[0] == "err"]
    assert len(wins) == 1 and wins[0][1]["revision"] == "r0001"
    assert all(e.startswith("sprite already exists: s") for e in errs) and len(errs) == n - 1
    assert revisions(workspace) == ["r0001"]
    jobs_empty(workspace)


# ------------------------------------------------------------------ N6 .jobs cleanup


def _fail_bad_layer(ws):
    with pytest.raises(adapter.AdapterError, match="no such layer: nope"):
        adapter.apply_ops("s", "r0001", [{"op": "clear", "layer": "nope"}])


def _fail_timeout(ws, monkeypatch):
    monkeypatch.setattr(adapter, "JOB_TIMEOUT_S", 0.01)
    with pytest.raises(adapter.AdapterError, match="timed out"):
        adapter.inspect_sprite("s")


def _fail_oversize(ws, monkeypatch):
    monkeypatch.setattr(adapter, "MAX_FILE_BYTES", 10)
    with pytest.raises(adapter.AdapterError, match="did not produce a valid output file"):
        adapter.apply_ops("s", "r0001", PX)


def _fail_export(ws, monkeypatch):
    with pytest.raises(adapter.AdapterError, match="no such frame: 9"):
        adapter.render_preview("s", frame=9)


def _fail_branch(ws, monkeypatch):
    mk("t")
    with pytest.raises(adapter.AdapterError, match="sprite already exists: t"):
        adapter.branch_sprite("s", "t")


@pytest.mark.parametrize("path", ["success", "bad_layer", "timeout", "oversize", "export", "branch"])
def test_jobs_dir_is_empty_after_every_path(workspace, monkeypatch, path):
    mk()
    jobs_empty(workspace)
    if path == "success":
        adapter.apply_ops("s", "r0001", PX)
        adapter.inspect_sprite("s")
        adapter.render_preview("s")
        adapter.render_filmstrip("s")
    elif path == "bad_layer":
        _fail_bad_layer(workspace)
    elif path == "timeout":
        _fail_timeout(workspace, monkeypatch)
    elif path == "oversize":
        _fail_oversize(workspace, monkeypatch)
    elif path == "export":
        _fail_export(workspace, monkeypatch)
    else:
        _fail_branch(workspace, monkeypatch)
    jobs_empty(workspace)


def test_cleanup_failure_is_logged_not_silent(workspace, monkeypatch, caplog):
    mk()

    def bad_rmtree(path, *a, **kw):
        raise OSError(errno.EBUSY, "Device or resource busy")

    monkeypatch.setattr(adapter.shutil, "rmtree", bad_rmtree)
    with caplog.at_level(logging.WARNING, logger="aseprite_mcp"):
        res = adapter.apply_ops("s", "r0001", PX)  # the published edit still succeeds
    assert res["revision"] == "r0002"
    assert any("could not remove job dir" in r.getMessage() for r in caplog.records)


# ------------------------------------------------------------------ N7 oversize output


def test_oversize_output_is_rejected_and_nothing_published(workspace, monkeypatch):
    mk()
    monkeypatch.setattr(adapter, "MAX_FILE_BYTES", 10)
    with pytest.raises(adapter.AdapterError, match="aseprite did not produce a valid output file"):
        adapter.apply_ops("s", "r0001", PX)
    with pytest.raises(adapter.AdapterError, match="aseprite did not produce a valid output file"):
        mk("fresh")
    assert revisions(workspace) == ["r0001"]
    assert not list(sprite_dir(workspace, "fresh").glob("r*"))
    jobs_empty(workspace)


def test_oversize_export_is_rejected(workspace, monkeypatch):
    mk()
    monkeypatch.setattr(adapter, "MAX_FILE_BYTES", 10)
    with pytest.raises(adapter.AdapterError, match="export failed"):
        adapter.render_preview("s")
    jobs_empty(workspace)


# ------------------------------------------------------------------ N8 names and paths

BAD_NAMES = [
    "..", ".", "../x", "x/../y", "/etc/passwd", "a/b", "a\\b", "a\x00b", "", " s", "s ", "s\n",
    "S", "A-b", "-s", "_s", "a" * 33, "ѕ",  # cyrillic dze, looks like latin s
    "ｓ",  # fullwidth latin s
    "s​",  # zero-width space
    "é", "s.aseprite", "s;rm", "$(id)",
]


@pytest.mark.parametrize("bad", BAD_NAMES)
def test_bad_sprite_names_are_rejected_everywhere(workspace, bad):
    mk()
    msg = "name must match"
    with pytest.raises(adapter.AdapterError, match=msg):
        adapter.new_sprite(bad, 4, 4)
    with pytest.raises(adapter.AdapterError, match=msg):
        adapter.apply_ops(bad, "r0001", PX)
    with pytest.raises(adapter.AdapterError, match=msg):
        adapter.inspect_sprite(bad)
    with pytest.raises(adapter.AdapterError, match=msg):
        adapter.branch_sprite(bad, "t")
    with pytest.raises(adapter.AdapterError, match=msg):
        adapter.branch_sprite("s", bad)
    with pytest.raises(adapter.AdapterError, match=msg):
        adapter.render_preview(bad)
    with pytest.raises(adapter.AdapterError, match=msg):
        adapter.render_filmstrip(bad)
    with pytest.raises(adapter.AdapterError, match=msg):
        adapter.apply_ops("s", "r0001", [{"op": "stamp", "source": bad, "x": 0, "y": 0}])
    # nothing escaped the sprites dir or leaked a job
    assert sorted(p.name for p in (workspace / "sprites").iterdir()) == ["s"]
    jobs_empty(workspace)


@pytest.mark.parametrize("bad", ["../x", "/abs", "a\x00b", "", "ѕ", "x" * 33, "a/b", "-x"])
def test_bad_layer_names_are_rejected_before_aseprite(workspace, bad, monkeypatch):
    mk()
    monkeypatch.setattr(adapter, "_run_lua", lambda *a, **k: pytest.fail("aseprite was invoked"))
    for op in (
        {"op": "clear", "layer": bad},
        {"op": "add_layer", "name": bad},
        {"op": "add_tag", "name": bad, "from_frame": 1, "to_frame": 1},
    ):
        with pytest.raises(adapter.AdapterError, match="must match"):
            adapter.apply_ops("s", "r0001", [op])
    with pytest.raises(adapter.AdapterError, match="must match"):
        adapter.render_preview("s", layer=bad)


@pytest.mark.parametrize("bad", ["r1", "r00001", "../r0001", "r0001/../r0001", "R0001", "r000a", 1, ""])
def test_bad_revision_strings_are_rejected(workspace, bad):
    mk()
    with pytest.raises(adapter.AdapterError, match="revision must look like r0001"):
        adapter.inspect_sprite("s", bad)


def test_symlinked_sprite_dir_is_refused_and_nothing_written_outside(workspace, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (workspace / "sprites").mkdir(parents=True)
    (workspace / "sprites" / "evil").symlink_to(outside, target_is_directory=True)
    with pytest.raises(adapter.AdapterError, match="symlink"):
        adapter.new_sprite("evil", 4, 4)
    assert list(outside.iterdir()) == []
    assert adapter.list_sprites() == []
    jobs_empty(workspace)


def test_symlinked_sprite_dir_pointing_at_real_sprite_is_not_reachable(workspace, tmp_path):
    mk()
    (workspace / "sprites" / "alias").symlink_to(sprite_dir(workspace), target_is_directory=True)
    with pytest.raises(adapter.AdapterError, match="symlink"):
        adapter.inspect_sprite("alias")
    with pytest.raises(adapter.AdapterError, match="symlink"):
        adapter.branch_sprite("s", "alias")
    assert [s["name"] for s in adapter.list_sprites()] == ["s"]


def test_symlinked_revision_file_is_not_trusted(workspace, tmp_path):
    mk()
    real = tmp_path / "elsewhere.aseprite"
    shutil.copyfile(sprite_dir(workspace) / "r0001.aseprite", real)
    r2 = sprite_dir(workspace) / "r0002.aseprite"
    r2.symlink_to(real)
    r2.with_suffix(".sha256").write_text(hashlib.sha256(real.read_bytes()).hexdigest() + "\n")
    # a symlinked r0002 (with a matching sidecar) must be ignored: latest is still r0001
    assert adapter.inspect_sprite("s")["revision"] == "r0001"
    assert adapter.list_sprites() == [{"name": "s", "latest": "r0001", "revisions": 1}]


def test_preview_of_missing_frame_or_layer_is_an_error_not_a_misleading_image(workspace):
    mk()
    with pytest.raises(adapter.AdapterError, match="no such frame: 2"):
        adapter.render_preview("s", frame=2)
    with pytest.raises(adapter.AdapterError, match="no such layer: nope"):
        adapter.render_preview("s", layer="nope")
    adapter.apply_ops("s", "r0001", [{"op": "add_frame"}])
    assert adapter.render_preview("s", frame=2, layer="base")[:4] == b"\x89PNG"
    jobs_empty(workspace)


# ------------------------------------------------------------------ publish collision window


def _inject_competitor(ws, name="s"):
    """Drop a complete, valid r0002 (+ its sidecar) into the sprite dir, as an un-locked writer would."""
    d = sprite_dir(ws, name)
    src = d / "r0001.aseprite"
    (d / "r0002.aseprite").write_bytes(src.read_bytes())
    (d / "r0002.sha256").write_text(hashlib.sha256(src.read_bytes()).hexdigest() + "\n")


def test_collision_before_the_exists_check_leaves_the_winner_intact(workspace, monkeypatch):
    mk()
    real = adapter._sha256

    def racing(path):
        if Path(path).name == "out.aseprite":  # competitor appears while we hash our output
            _inject_competitor(workspace)
        return real(path)

    monkeypatch.setattr(adapter, "_sha256", racing)
    with pytest.raises(adapter.AdapterError, match="revision collision; retry"):
        adapter.apply_ops("s", "r0001", PX)
    monkeypatch.undo()
    monkeypatch.setattr(adapter, "WORKSPACE", workspace)
    assert adapter.inspect_sprite("s", "r0002")["revision"] == "r0002"  # winner still verifies
    assert revisions(workspace) == ["r0001", "r0002"]
    jobs_empty(workspace)


def test_collision_between_check_and_sidecar_write_does_not_overwrite_winners_hash(workspace, monkeypatch):
    mk()
    real = Path.is_symlink
    fired = []

    def racing(self):
        if self.name == "r0002.aseprite" and not fired:  # the last call of the exists-check
            fired.append(1)
            _inject_competitor(workspace)
            return False  # our check saw nothing; the competitor lands right after it
        return real(self)

    monkeypatch.setattr(Path, "is_symlink", racing)
    with pytest.raises(adapter.AdapterError, match="revision collision; retry"):
        adapter.apply_ops("s", "r0001", PX)
    monkeypatch.undo()
    monkeypatch.setattr(adapter, "WORKSPACE", workspace)
    assert fired
    sidecar = (sprite_dir(workspace) / "r0002.sha256").read_text().strip()
    assert sidecar == hashlib.sha256((sprite_dir(workspace) / "r0002.aseprite").read_bytes()).hexdigest()
    assert adapter.inspect_sprite("s", "r0002")["revision"] == "r0002"
    jobs_empty(workspace)


def test_orphan_sidecar_from_an_interrupted_publish_is_replaced(workspace):
    mk()
    (sprite_dir(workspace) / "r0002.sha256").write_text("0" * 64 + "\n")  # orphan: no r0002.aseprite
    out = adapter.apply_ops("s", "r0001", PX)
    assert out["revision"] == "r0002"
    assert adapter.inspect_sprite("s", "r0002")["sha256"] == out["sha256"]  # verifies against the new hash
    assert revisions(workspace) == ["r0001", "r0002"]

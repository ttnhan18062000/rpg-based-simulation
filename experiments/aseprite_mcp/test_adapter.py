"""Spike tests. Need real Aseprite + bwrap, so they skip cleanly where either is missing.

Run: .venv/bin/python -m pytest experiments/aseprite_mcp -q
"""

from __future__ import annotations

import hashlib
import shutil
import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adapter  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (Path(adapter.ASEPRITE).exists() and shutil.which("bwrap")),
    reason="requires aseprite and bwrap",
)


@pytest.fixture(autouse=True)
def workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "WORKSPACE", tmp_path / "ws")
    return tmp_path / "ws"


def test_create_draw_creates_immutable_revisions(workspace):
    r1 = adapter.new_sprite("hero", 8, 8, "#00000000")
    assert r1["revision"] == "r0001" and r1["nonempty_pixels"] == 0
    r1_file = workspace / "sprites" / "hero" / "r0001.aseprite"
    before = hashlib.sha256(r1_file.read_bytes()).hexdigest()

    r2 = adapter.draw_pixels("hero", "r0001", [{"x": 1, "y": 2, "color": "#ff0000"}])
    assert r2["revision"] == "r0002" and r2["nonempty_pixels"] == 1
    assert hashlib.sha256(r1_file.read_bytes()).hexdigest() == before  # r0001 untouched

    old = adapter.inspect_sprite("hero", "r0001")
    new = adapter.inspect_sprite("hero", "r0002")
    assert old["nonempty_pixels"] == 0 and new["nonempty_pixels"] == 1


def test_readback_matches_what_was_drawn():
    adapter.new_sprite("grid", 8, 8)
    adapter.fill_rect("grid", "r0001", 0, 0, 4, 4, "#0000ff")
    adapter.draw_line("grid", "r0002", 0, 7, 7, 0, "#00ff00")
    got = adapter.inspect_sprite("grid", region={"x": 0, "y": 0, "w": 8, "h": 8})
    assert got["revision"] == "r0003"
    assert got["region"][0][0] == "#0000ffff"
    assert got["region"][7][0] == "#00ff00ff" and got["region"][0][7] == "#00ff00ff"
    assert got["region"][7][7] == "#00000000"


def test_stale_base_revision_rejected():
    adapter.new_sprite("s", 4, 4)
    adapter.draw_pixels("s", "r0001", [{"x": 0, "y": 0, "color": "#ffffff"}])
    with pytest.raises(adapter.AdapterError, match="stale"):
        adapter.draw_pixels("s", "r0001", [{"x": 1, "y": 1, "color": "#ffffff"}])
    assert [s["latest"] for s in adapter.list_sprites()] == ["r0002"]


def test_tampered_revision_refused(workspace):
    adapter.new_sprite("s", 4, 4)
    (workspace / "sprites" / "s" / "r0001.aseprite").write_bytes(b"corrupt")
    with pytest.raises(adapter.AdapterError, match="hash"):
        adapter.inspect_sprite("s")


@pytest.mark.parametrize(
    "call",
    [
        lambda: adapter.new_sprite("../evil", 4, 4),
        lambda: adapter.new_sprite("a/b", 4, 4),
        lambda: adapter.new_sprite("Upper", 4, 4),
        lambda: adapter.new_sprite("ok", 0, 4),
        lambda: adapter.new_sprite("ok", 4, adapter.MAX_DIM + 1),
        lambda: adapter.new_sprite("ok", 4, 4, "red"),
        lambda: adapter.new_sprite("ok", True, 4),
        lambda: adapter.draw_pixels("ok", "r0001", []),
        lambda: adapter.inspect_sprite("nope"),
        lambda: adapter.render_preview("nope", scale=2),
    ],
)
def test_bad_input_rejected(call):
    with pytest.raises(adapter.AdapterError):
        call()


def test_out_of_bounds_pixel_rejected_without_new_revision():
    adapter.new_sprite("s", 4, 4)
    with pytest.raises(adapter.AdapterError, match="out of bounds"):
        adapter.draw_pixels("s", "r0001", [{"x": 5, "y": 0, "color": "#ffffff"}])
    assert adapter.list_sprites()[0]["latest"] == "r0001"


def test_duplicate_create_rejected():
    adapter.new_sprite("s", 4, 4)
    with pytest.raises(adapter.AdapterError, match="already exists"):
        adapter.new_sprite("s", 4, 4)


def test_preview_is_png_at_requested_scale():
    adapter.new_sprite("p", 6, 4, "#ff00ffff")
    png = adapter.render_preview("p", scale=4)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    w, h = struct.unpack(">II", png[16:24])
    assert (w, h) == (24, 16)


def test_same_ops_give_same_pixels():
    for name in ("a", "b"):
        adapter.new_sprite(name, 8, 8, "#102030")
        adapter.fill_rect(name, "r0001", 1, 1, 3, 3, "#aabbcc", filled=False)
    region = {"x": 0, "y": 0, "w": 8, "h": 8}
    a = adapter.inspect_sprite("a", region=region)["region"]
    b = adapter.inspect_sprite("b", region=region)["region"]
    assert a == b


def test_sandbox_hides_host_files(tmp_path):
    secret = Path.home() / ".config" / "aseprite" / "aseprite.ini"
    probe = tmp_path / "probe.lua"
    probe.write_text(
        "local out = {}\n"
        "for _, p in ipairs({'%s', '/etc/passwd', '/etc/shadow', '/proc/1/environ'}) do\n"
        "  local f = io.open(p, 'rb'); out[#out+1] = p .. '=' .. tostring(f ~= nil)\n"
        "  if f then f:close() end\n"
        "end\n"
        "local w = io.open('/job/probe.txt', 'wb'); w:write(table.concat(out, '\\n')); w:close()\n"
        % secret
    )
    job = tmp_path / "job"
    job.mkdir()
    shutil.copy(probe, job / "probe.lua")
    adapter._bwrap(job, ["--script", "/job/probe.lua"])
    seen = dict(line.split("=") for line in (job / "probe.txt").read_text().splitlines())
    assert seen[str(secret)] == "false"  # real home is not mounted
    assert seen["/etc/passwd"] == "false" and seen["/etc/shadow"] == "false"


def test_template_hash_is_enforced(monkeypatch):
    monkeypatch.setattr(adapter, "LUA_SHA256", "0" * 64)
    with pytest.raises(adapter.AdapterError, match="pinned hash"):
        adapter.new_sprite("s", 4, 4)

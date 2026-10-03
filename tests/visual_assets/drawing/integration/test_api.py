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

from visual_assets.drawing import api, config
from visual_assets.drawing.backend import sandbox
from visual_assets.drawing.errors import AdapterError

pytestmark = pytest.mark.needs_aseprite






def test_create_draw_creates_immutable_revisions(workspace):
    r1 = api.new_sprite("hero", 8, 8, "#00000000")
    assert r1["revision"] == "r0001" and r1["nonempty_pixels"] == 0
    r1_file = workspace / "sprites" / "hero" / "r0001.aseprite"
    before = hashlib.sha256(r1_file.read_bytes()).hexdigest()

    r2 = api.draw_pixels("hero", "r0001", [{"x": 1, "y": 2, "color": "#ff0000"}])
    assert r2["revision"] == "r0002" and r2["nonempty_pixels"] == 1
    assert hashlib.sha256(r1_file.read_bytes()).hexdigest() == before  # r0001 untouched

    old = api.inspect_sprite("hero", "r0001")
    new = api.inspect_sprite("hero", "r0002")
    assert old["nonempty_pixels"] == 0 and new["nonempty_pixels"] == 1


def test_readback_matches_what_was_drawn():
    api.new_sprite("grid", 8, 8)
    api.fill_rect("grid", "r0001", 0, 0, 4, 4, "#0000ff")
    api.draw_line("grid", "r0002", 0, 7, 7, 0, "#00ff00")
    got = api.inspect_sprite("grid", region={"x": 0, "y": 0, "w": 8, "h": 8})
    assert got["revision"] == "r0003"
    assert got["region"][0][0] == "#0000ffff"
    assert got["region"][7][0] == "#00ff00ff" and got["region"][0][7] == "#00ff00ff"
    assert got["region"][7][7] == "#00000000"


def test_stale_base_revision_rejected():
    api.new_sprite("s", 4, 4)
    api.draw_pixels("s", "r0001", [{"x": 0, "y": 0, "color": "#ffffff"}])
    with pytest.raises(AdapterError, match="stale"):
        api.draw_pixels("s", "r0001", [{"x": 1, "y": 1, "color": "#ffffff"}])
    assert [s["latest"] for s in api.list_sprites()] == ["r0002"]


def test_tampered_revision_refused(workspace):
    api.new_sprite("s", 4, 4)
    (workspace / "sprites" / "s" / "r0001.aseprite").write_bytes(b"corrupt")
    with pytest.raises(AdapterError, match="hash"):
        api.inspect_sprite("s")


@pytest.mark.parametrize(
    "call",
    [
        lambda: api.new_sprite("../evil", 4, 4),
        lambda: api.new_sprite("a/b", 4, 4),
        lambda: api.new_sprite("Upper", 4, 4),
        lambda: api.new_sprite("ok", 0, 4),
        lambda: api.new_sprite("ok", 4, config.MAX_DIM + 1),
        lambda: api.new_sprite("ok", 4, 4, "red"),
        lambda: api.new_sprite("ok", True, 4),
        lambda: api.draw_pixels("ok", "r0001", []),
        lambda: api.inspect_sprite("nope"),
        lambda: api.render_preview("nope", scale=2),
    ],
)
def test_bad_input_rejected(call):
    with pytest.raises(AdapterError):
        call()


def test_out_of_bounds_pixel_rejected_without_new_revision():
    api.new_sprite("s", 4, 4)
    with pytest.raises(AdapterError, match="out of bounds"):
        api.draw_pixels("s", "r0001", [{"x": 5, "y": 0, "color": "#ffffff"}])
    assert api.list_sprites()[0]["latest"] == "r0001"


def test_duplicate_create_rejected():
    api.new_sprite("s", 4, 4)
    with pytest.raises(AdapterError, match="already exists"):
        api.new_sprite("s", 4, 4)


def test_preview_is_png_at_requested_scale():
    api.new_sprite("p", 6, 4, "#ff00ffff")
    png = api.render_preview("p", scale=4)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    w, h = struct.unpack(">II", png[16:24])
    assert (w, h) == (24, 16)


def test_same_ops_give_same_pixels():
    for name in ("a", "b"):
        api.new_sprite(name, 8, 8, "#102030")
        api.fill_rect(name, "r0001", 1, 1, 3, 3, "#aabbcc", filled=False)
    region = {"x": 0, "y": 0, "w": 8, "h": 8}
    a = api.inspect_sprite("a", region=region)["region"]
    b = api.inspect_sprite("b", region=region)["region"]
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
    sandbox.bwrap(job, ["--script", "/job/probe.lua"])
    seen = dict(line.split("=") for line in (job / "probe.txt").read_text().splitlines())
    assert seen[str(secret)] == "false"  # real home is not mounted
    assert seen["/etc/passwd"] == "false" and seen["/etc/shadow"] == "false"


def test_template_hash_is_enforced(monkeypatch):
    monkeypatch.setattr(config, "LUA_SHA256", "0" * 64)
    with pytest.raises(AdapterError, match="pinned hash"):
        api.new_sprite("s", 4, 4)

"""MCP protocol test: spawns server.py over real stdio and talks to it with the MCP client.

Deliberately does not import `adapter` to fake the server (only the constants of the files it reads).
Run: .venv/bin/python -m pytest experiments/aseprite_mcp -q
"""

from __future__ import annotations

import asyncio
import base64
import json
import shutil
import struct
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
ASEPRITE = "/usr/bin/aseprite"

pytestmark = pytest.mark.skipif(
    not (Path(ASEPRITE).exists() and shutil.which("bwrap")),
    reason="requires aseprite and bwrap",
)

EXPECTED_TOOLS = {
    "new_sprite", "apply_ops", "branch_sprite", "inspect", "preview", "filmstrip", "list_sprites",
    # high-level layer (highlevel_tools.register)
    "make_ramp", "shade", "dither", "stroke", "auto_outline", "remap_palette", "lint_sprite",
    "ascii_view",
}


@asynccontextmanager
async def session(workspace: Path):
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(HERE / "server.py")],
        env={"ASEPRITE_MCP_WORKSPACE": str(workspace)},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await asyncio.wait_for(s.initialize(), 30)
            yield s


def run(coro):
    return asyncio.run(asyncio.wait_for(coro, 120))


def text(result) -> str:
    return "".join(c.text for c in result.content if c.type == "text")


def data(result) -> dict:
    return json.loads(text(result))


def png_size(item):
    assert item.type == "image" and item.mimeType == "image/png"
    raw = base64.b64decode(item.data)
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", raw[16:24])


def test_exact_tool_list(tmp_path):
    async def go():
        async with session(tmp_path / "ws") as s:
            return {t.name: t for t in (await s.list_tools()).tools}

    tools = run(go())
    assert set(tools) == EXPECTED_TOOLS
    desc = tools["apply_ops"].description
    for op in ("delete_layer", "delete_frame", "resize_canvas"):
        assert op in desc


def test_bad_call_is_a_tool_error_carrying_the_adapter_message(tmp_path):
    async def go():
        async with session(tmp_path / "ws") as s:
            bad_name = await s.call_tool("new_sprite", {"name": "../evil", "width": 4, "height": 4})
            bad_dim = await s.call_tool("new_sprite", {"name": "ok", "width": 999, "height": 4})
            missing = await s.call_tool("inspect", {"name": "ghost"})
            return bad_name, bad_dim, missing

    bad_name, bad_dim, missing = run(go())
    assert bad_name.isError and "name must match [a-z0-9][a-z0-9_-]{0,31}" in text(bad_name)
    assert bad_dim.isError and "width must be an integer in [1, 128]" in text(bad_dim)
    assert missing.isError and "no such sprite: ghost" in text(missing)
    assert not (tmp_path / "ws" / "sprites" / "evil").exists()


def test_stale_base_revision_is_a_tool_error(tmp_path):
    async def go():
        async with session(tmp_path / "ws") as s:
            created = await s.call_tool("new_sprite", {"name": "s", "width": 4, "height": 4})
            op = [{"op": "pixels", "pixels": [{"x": 0, "y": 0, "color": "#ff0000"}]}]
            first = await s.call_tool("apply_ops", {"name": "s", "base_revision": "r0001", "ops": op})
            stale = await s.call_tool("apply_ops", {"name": "s", "base_revision": "r0001", "ops": op})
            listed = await s.call_tool("list_sprites", {})
            return created, first, stale, listed

    created, first, stale, listed = run(go())
    assert not created.isError and data(created)["revision"] == "r0001"
    assert not first.isError and data(first)["revision"] == "r0002"
    assert stale.isError
    assert "stale base_revision r0001; latest is r0002" in text(stale)
    assert not listed.isError and "r0002" in text(listed)


def test_preview_and_filmstrip_return_png_images_of_the_expected_size(tmp_path):
    async def go():
        async with session(tmp_path / "ws") as s:
            await s.call_tool("new_sprite", {"name": "s", "width": 16, "height": 8})
            await s.call_tool("apply_ops", {"name": "s", "base_revision": "r0001", "ops": [
                {"op": "add_frame"}, {"op": "add_frame"}]})
            prev = await s.call_tool("preview", {"name": "s", "scale": 4})
            film = await s.call_tool("filmstrip", {"name": "s", "scale": 2})
            bad = await s.call_tool("preview", {"name": "s", "frame": 9})
            return prev, film, bad

    prev, film, bad = run(go())
    assert not prev.isError and len(prev.content) == 1 and png_size(prev.content[0]) == (64, 32)
    assert not film.isError and len(film.content) == 1 and png_size(film.content[0]) == (3 * 16 * 2, 16)
    assert bad.isError and "no such frame: 9" in text(bad)


def test_new_structural_ops_work_over_the_protocol(tmp_path):
    async def go():
        async with session(tmp_path / "ws") as s:
            await s.call_tool("new_sprite", {"name": "s", "width": 4, "height": 4})
            ok = await s.call_tool("apply_ops", {"name": "s", "base_revision": "r0001", "ops": [
                {"op": "resize_canvas", "width": 8, "height": 6}]})
            last = await s.call_tool("apply_ops", {"name": "s", "base_revision": "r0002", "ops": [
                {"op": "delete_layer", "layer": "base"}]})
            return ok, last

    ok, last = run(go())
    assert not ok.isError and (data(ok)["width"], data(ok)["height"]) == (8, 6)
    assert last.isError and "cannot delete the last layer" in text(last)


def test_high_level_tools_work_over_the_protocol(tmp_path):
    async def go():
        async with session(tmp_path / "ws") as s:
            ramp = await s.call_tool("make_ramp", {"base": "#808080", "steps": 5})
            bad = await s.call_tool("make_ramp", {"base": "nope"})
            await s.call_tool("new_sprite", {"name": "s", "width": 8, "height": 8})
            await s.call_tool("apply_ops", {"name": "s", "base_revision": "r0001", "ops": [
                {"op": "rect", "x": 2, "y": 2, "width": 4, "height": 4, "color": "#c04040"}]})
            lint = await s.call_tool("lint_sprite", {"name": "s"})
            return ramp, bad, lint

    ramp, bad, lint = run(go())
    assert not ramp.isError
    body = text(ramp)
    assert "#808080" in body  # the base colour is kept in the ramp
    assert bad.isError and text(bad)
    assert not lint.isError and text(lint)

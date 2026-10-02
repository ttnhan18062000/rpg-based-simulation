"""MCP protocol test: spawns the real server over stdio and talks to it with the MCP client.

Does not import the API to fake the server. These tests do not need Aseprite (they run in CI);
the ones that draw live in integration/test_server_stdio.py.
"""

from __future__ import annotations

from tests.visual_assets.drawing.stdio_support import EXPECTED_TOOLS, run, session, text


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

"""MCP protocol tests that draw through the real server over stdio. Need real Aseprite + bwrap."""

from __future__ import annotations

import pytest

from tests.visual_assets.drawing.stdio_support import data, png_size, run, session, text

pytestmark = pytest.mark.needs_aseprite


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


def test_export_handoff_over_stdio_writes_a_candidate_directory_and_nothing_else(tmp_path):
    async def go():
        async with session(tmp_path / "ws") as s:
            await s.call_tool("new_sprite", {"name": "s", "width": 8, "height": 8})
            edited = await s.call_tool("apply_ops", {"name": "s", "base_revision": "r0001", "ops": [
                {"op": "pixels", "pixels": [{"x": 1, "y": 1, "color": "#ff0000"}]}]})
            ok = await s.call_tool("export_handoff", {"name": "s", "revision": data(edited)["revision"],
                                                       "licence_state": "CLEARED", "licence_evidence_ref": "note"})
            again = await s.call_tool("export_handoff", {"name": "s", "revision": data(edited)["revision"],
                                                          "licence_state": "CLEARED", "licence_evidence_ref": "note"})
            return ok, again

    ok, again = run(go())
    assert not ok.isError and data(ok) == data(again)
    result = data(ok)
    directory = tmp_path / "ws" / "handoffs" / result["candidate_id"]
    assert sorted(p.name for p in directory.iterdir()) == ["package.json", "preview.png", "source.aseprite"]
    assert result["directory"] == str(directory) and "does not adopt" in result["next"]
    assert sorted(p.name for p in (tmp_path / "ws").iterdir() if p.name != ".jobs") == ["handoffs", "sprites"]

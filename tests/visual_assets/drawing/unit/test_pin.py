"""`python -m visual_assets.drawing.pin` re-pins LUA_SHA256 after a reviewed template change (no Aseprite)."""

from __future__ import annotations

import hashlib

import pytest

from visual_assets.drawing import config, pin


def test_pin_rewrites_exactly_the_pin_line(tmp_path):
    lua = tmp_path / "ops.lua"
    lua.write_text("-- changed template\n")
    cfg = tmp_path / "config.py"
    cfg.write_text('A = 1\nLUA_SHA256 = "' + "0" * 64 + '"\nB = 2\n')
    digest = pin.pin(cfg, lua)
    assert digest == hashlib.sha256(lua.read_bytes()).hexdigest()
    assert cfg.read_text() == f'A = 1\nLUA_SHA256 = "{digest}"\nB = 2\n'


def test_pin_refuses_a_config_without_exactly_one_pin_line(tmp_path):
    lua = tmp_path / "ops.lua"
    lua.write_text("x")
    cfg = tmp_path / "config.py"
    cfg.write_text("A = 1\n")
    with pytest.raises(SystemExit):
        pin.pin(cfg, lua)
    assert cfg.read_text() == "A = 1\n"


def test_the_committed_pin_matches_the_committed_template():
    assert config.LUA_SHA256 == hashlib.sha256(config.LUA_PATH.read_bytes()).hexdigest()

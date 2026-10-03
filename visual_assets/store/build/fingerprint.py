"""The build fingerprint recorded in every artifact: what produced these pixels."""

from __future__ import annotations

from visual_assets.store.contracts.artifact import BuildFingerprint


def build_fingerprint(*, tool_version: str, export_config_hash: str, lua_pin_hash: str) -> BuildFingerprint:
    """`lua_pin_hash` is the pin of the Lua template mounted in the sandbox. Plain PNG export does not run Lua; this records which pinned
    template the tool suite had available, not a claim that Lua ran."""
    return BuildFingerprint(
        tool_name="Aseprite", tool_version=tool_version, export_config_hash=export_config_hash, lua_pin_hash=lua_pin_hash
    )

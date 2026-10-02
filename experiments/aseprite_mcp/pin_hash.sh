#!/usr/bin/env bash
# Re-pin LUA_SHA256 in adapter.py after a deliberate, reviewed change to lua/ops.lua.
cd "$(dirname "$0")"
H=$(sha256sum lua/ops.lua | cut -d' ' -f1)
sed -i "s/^LUA_SHA256 = .*/LUA_SHA256 = \"$H\"/" adapter.py
grep -n '^LUA_SHA256' adapter.py

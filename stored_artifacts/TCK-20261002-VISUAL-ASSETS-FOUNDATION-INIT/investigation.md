---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT
artifact_type: investigation
tags: [mcp, architecture, testing, documentation]
---

# Investigation — TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT

## Context scan
`search_docs` + `graphify query` for MCP tooling layout and asset management, then direct reads of
`docs/plans/visual-asset-management-runtime-integration/` (README, M1, M4), the asset proposal §6-§9.6, the Aseprite
plan package, `pyproject.toml`, `.github/workflows/test.yml`, `tests/tools/test_mcp_json_registration.py`.

## Facts that shape the move (verified 2026-10-02 at 7dfd1349 + PR #286)
- `src/` is the installable engine (`[tool.setuptools.packages.find] include = ["src*"]`); mypy runs on `src/` only.
- `tools/` holds 94 entries / 307 files; root-level subsystems already exist (`agent-orchestration/`, `frontend/`).
- CI lists test directories explicitly: 23 `Run: tests/...` steps. `tests/tools` runs in job `api-tools`; a new
  test root runs nowhere until a step is added. That job installs `requirements.txt`, which pins `mcp==1.28.1`,
  so the server module imports in CI. CI has no Aseprite and no guarantee of `bwrap`.
- `pyproject.toml` has `pythonpath = ["."]`; `norecursedirs` does not exclude a new root package.
- `.mcp.json` servers are launched through `tools/start_*.sh` scripts that probe candidate interpreters;
  `tests/tools/test_mcp_json_registration.py` asserts existing entries byte-identical and permits additions.
- The shared worktree has no `.venv`; the main checkout's is `/home/vboxuser/Work/rpg-based-simulation/.venv`.
- Current code: `adapter.py` 660 lines (constants, validators, op schema, storage, sandbox, operations in one
  module), `highlevel.py` 444 (pure maths), `highlevel_tools.py` 417 (sprite-facing + `register`), `server.py` 105,
  five test files, `lua/ops.lua` 418. 209 tests.

## Risks specific to this refactor
1. **Monkeypatched module globals.** Tests patch `adapter.WORKSPACE`, `adapter.LUA_SHA256`, `adapter.JOB_TIMEOUT_S`,
   `adapter.MAX_FILE_BYTES`, `adapter._bwrap`, `adapter._sha256`, `os.link`. After the split these live in different
   modules; any `from config import WORKSPACE` style import freezes the value at import time and silently defeats
   the patch (a test would then run against the real `~/.cache` workspace). Rule: read config as `config.NAME` at
   call time, and patch the module that owns the name.
2. **`LUA_PATH` and the sandbox bind** are derived from the module's own location; moving the Lua file changes it.
3. **`server.py` uses `sys.path.insert` + bare `import adapter`**; as a package it must use package imports and be
   runnable with `python -m` from the repo root. The stdio test spawns it as a subprocess: its `cwd` and command change.
4. **Name collision**: the drawing tools' experiment-workspace package is `workspace/`, not `store/`, because
   `visual_assets/store/` is the asset store.
5. **CI visibility**: integration tests skip in CI, so a broken sandbox path would not be seen there. The
   acceptance criteria require the local run with Aseprite and the simulated no-Aseprite run, both reported.

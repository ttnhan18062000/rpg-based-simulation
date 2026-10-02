---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT
artifact_type: plan
tags: [mcp, architecture, testing, documentation]
---

# Plan — TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT

Behaviour-preserving refactor. Keep the suite green at every step; never batch the move and a behaviour change.

## Step 0 — baseline
Run the suite in `experiments/aseprite_mcp` (expect 209 passed). Record `sha256sum lua/ops.lua` and the 15 tool names.

## Step 1 — move, then split
1. `git mv experiments/aseprite_mcp visual_assets/drawing` style moves so history follows whole files
   (`lua/ops.lua` -> `visual_assets/drawing/backend/lua/ops.lua`, byte-identical).
2. Split `adapter.py` by responsibility, top-down in dependency order so each new module imports only lower ones:
   `errors` -> `config` -> `colors` -> `schema/primitives` -> `schema/ops` -> `backend/sandbox` ->
   `backend/lua_runner` -> `workspace/{jobs,locks,revisions}` -> `api`.
   `highlevel.py` -> `technique/{ramps,dither,stroke,shading,masks,lint,ascii}` (+ colour helpers into `colors`).
   `highlevel_tools.py` -> `compose.py` (functions) and `server/highlevel_tools.py` (registration).
   `server.py` -> `server/app.py`, `server/lowlevel_tools.py`, `server/__main__.py`.
   `pin_hash.sh` -> `pin.py` (`python -m visual_assets.drawing.pin`), same effect.
3. Config access rule (investigation risk 1): modules do `from visual_assets.drawing import config` and read
   `config.WORKSPACE` etc. at call time. No `from ...config import NAME` for anything a test patches.
4. `visual_assets/drawing/__init__.py` re-exports the public API (`new_sprite`, `apply_ops`, `branch_sprite`,
   `inspect_sprite`, `render_preview`, `render_filmstrip`, `list_sprites`, `AdapterError`, `__version__`).

## Step 2 — tests
Move to `tests/visual_assets/drawing/`. `conftest.py`: `workspace` fixture patching `config.WORKSPACE`, and
`needs_aseprite = pytest.mark.skipif(...)`. Sort each test into `unit/` (pure technique, lint, ascii, schema
validation that asserts Aseprite never runs) or `integration/` (anything that launches Aseprite). Update patches to
the owning module. Then prove risk 1 is handled: temporarily make the `workspace` fixture a no-op and confirm tests
fail or would touch the real workspace; restore.

## Step 3 — boundary test
`tests/visual_assets/test_boundaries.py`: parse imports with `ast` for every module under `visual_assets/` and
assert the allowed-direction table from the structure doc; assert no `src` import under `visual_assets/` and no
`visual_assets` import under `src/`; assert no module under `drawing/` mentions the catalog directory. Apply the
three planted violations from the ticket, see each fail, revert.

## Step 4 — skeletons
`visual_assets/README.md`, `visual_assets/store/{__init__.py,README.md}`, `visual_assets/catalog/{README.md,
STORE_FORMAT}` + `.gitkeep` in `definitions sources provenance build-config generated manifests/candidates fixtures`;
`.gitignore` entry for `visual_assets/catalog/.quarantine/`. READMEs state: not implemented, gates, who may write.

## Step 5 — launcher, registration, CI
`visual_assets/start_mcp.sh`: same shape as `tools/start_search_mcp.sh` (quiet `find_spec('mcp')` probe, candidates
`$REPO_ROOT/.venv`, `/home/vboxuser/Work/rpg-based-simulation/.venv`, `python3`; `cd "$REPO_ROOT"`; `exec "$py" -m
visual_assets.drawing.server`; one clear final error). `.mcp.json`: add `aseprite-pixel-art` with
`{"command": "bash", "args": ["visual_assets/start_mcp.sh"], "env": {}, "description": ...}`; touch nothing else.
Extend the two `tests/tools` files in their existing style. CI: add the step in `api-tools` after `tests/tools`,
with its own junit file, and add it to the merge list and the base-collect list in that job.

## Step 6 — docs
As listed in the ticket Scope 7. The plan-package status notes are dated additions, not rewrites: Aseprite README
gains "decided by evidence 2026-10-02: U-01 host Linux dev machine, U-03 project-owned stdio adapter, U-04 `mcp`
already pinned in requirements.txt, U-06 bwrap confinement proven on the dev machine; still open: U-02, U-05,
U-07..U-14". Asset-management README gains a pointer to the foundation package and the AM items it will implement.
Run `make knowledge-index-update`, `graphify update .`, and Finalize's registry regeneration.

## Scope guards (reviewer will check)
No behaviour change; no store logic; no `src/`, `frontend/`, dependency change; `.mcp.json` existing entries
byte-identical; do not touch the user-scope registration; one commit for this ticket is the planner's job (do not
commit or push); new commits only, never amend the pushed branch.

## Acceptance-criteria map
AC1-2 -> Steps 0-1; AC3-4 -> Step 2; AC5 -> Step 3; AC6-7 -> Step 5; AC8 -> Step 5 + PR run; AC9 -> Step 6; AC10 -> final diff.

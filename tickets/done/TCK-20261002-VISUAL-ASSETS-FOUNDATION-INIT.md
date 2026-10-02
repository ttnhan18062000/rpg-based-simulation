---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT
phase: done
date: 2026-10-02
tags: [mcp, architecture, testing, documentation]
---

# TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT

## Title
Initialise `visual_assets/`: move and restructure the drawing tools, add store/catalog skeletons, CI, registration, docs

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
First child of `TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION`. Move the drawing tools out of
`experiments/aseprite_mcp/` into the approved in-project home `visual_assets/drawing/`, split into the layered
modules of `docs/plans/visual-asset-foundation/README.md`, with **no behaviour change**; create the `store/` and
`catalog/` skeletons (no logic); make CI run the tests it can; register the MCP server in `.mcp.json`; move the
docs; record the decisions. Planner/reviewer: `asset-planner`. Implementer: `asset-implementer`.

## Scope
1. `visual_assets/drawing/` package per the structure doc: `config`, `errors`, `colors`, `schema/`, `backend/`
   (incl. `lua/ops.lua`, byte-identical), `workspace/`, `api`, `technique/`, `compose`, `server/`, `pin`.
   `git mv` where a file moves whole so history follows. `experiments/aseprite_mcp/` is removed entirely.
2. Tests to `tests/visual_assets/drawing/{unit,integration}/` + `conftest.py` (shared workspace fixture and
   `needs_aseprite` marker) + `test_server_stdio.py`. `unit/` must not need Aseprite or bwrap.
3. `tests/visual_assets/test_boundaries.py`: layering rules from the structure doc, no `src` import in either
   direction, `drawing` has no write path into `visual_assets/catalog/`.
4. Skeletons only: `visual_assets/store/` (`__init__.py`, `README.md` stating "not implemented, see SEQUENCE.md")
   and `visual_assets/catalog/` (`README.md`, `STORE_FORMAT`, the seven subdirectories with `.gitkeep`,
   `.quarantine/` gitignored). No store logic, no records, no fixtures content.
5. CI: one `Run: tests/visual_assets` step in the `api-tools` job of `.github/workflows/test.yml`, mirroring the
   existing per-directory steps exactly (junit path, merge list, base-collect list).
6. Registration: `visual_assets/start_mcp.sh` launcher + `aseprite-pixel-art` entry in `.mcp.json`; extend
   `tests/tools/test_mcp_json_registration.py` and `tests/tools/test_mcp_launcher_hardening.py`.
7. Docs: `docs/assets/drawing_tools.md` and `docs/assets/pixel_art_technique.md` (moved from the experiment's
   README and TECHNIQUE_GUIDE), `docs/assets/store_contract.md` (designed vs built, clearly marked),
   `docs/architecture/visual_asset_foundation_adr.md` (D1, D5, D6, D7 decided; D2-D4 proposed, not decided),
   status notes in both plan-package READMEs; `make knowledge-index-update`; `graphify update .`.

## Out of Scope
- Any store logic (contracts, intake, adoption, build, release, verify, revoke, gc): children 2-6.
- `handoff.py` and any store-facing MCP tool.
- Behaviour changes to the drawing tools, new ops, new limits, renamed tools or changed error messages.
- `src/`, `frontend/`, `requirements*.txt`, `pyproject.toml` dependencies (pytest config may be touched only if
  collection of `tests/visual_assets` requires it; say so if it does).
- Removing or repointing the user-scope MCP registration (planner does that after review).

## Acceptance Criteria
- [x] `experiments/aseprite_mcp/` no longer exists; `visual_assets/drawing/` matches the structure doc's module list
      (any deviation listed and justified in Implementation Notes).
- [x] No behaviour change: the same 15 MCP tool names; `lua/ops.lua` byte-identical (same `LUA_SHA256`); every
      test from the old suite still exists under the new tree and passes (209 before; state the new count and
      account for any difference test by test).
- [x] With Aseprite available: whole `tests/visual_assets` green, 0 skipped. With `ASEPRITE_MCP_BINARY` pointing at
      a nonexistent path: 0 failed, and the exact passed/skipped counts are reported (this is what CI will see).
- [x] `unit/` contains no test that needs Aseprite; `integration/` contains every test that does.
- [x] Boundary test fails for each of these planted violations, then passes when reverted: a `technique` module
      importing `api`; a `drawing` module importing `src`; a `drawing` module referencing the catalog path for writing.
- [x] `python -m visual_assets.drawing.server` starts and answers `list_tools` over stdio from the repo root;
      `bash visual_assets/start_mcp.sh` does the same and fails with one clear message when no interpreter has `mcp`.
- [x] `.mcp.json` has the new entry; the two extended `tests/tools` test files pass; existing entries byte-identical.
- [ ] CI step added and green on the PR, and its junit shard appears in the merged report. (Step added and parsed; the green PR run and merged-report shard can only be observed after asset-planner pushes; see Completion Summary.)
- [x] Docs created with valid frontmatter; `docs/assets/store_contract.md` and the ADR state plainly what is
      built vs proposed; both plan READMEs carry a dated status note; knowledge index updated.
- [x] `git diff --stat origin/main` shows no change under `src/`, `frontend/`, `requirements*.txt`.

## Related Tickets
- TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION (parent)
- TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING, TCK-20261002-ASEPRITE-MCP-HIGHLEVEL-PIXEL-ART-TOOLS (code being moved)

## Related Docs
- docs/plans/visual-asset-foundation/README.md (structure, layering rules, decisions)
- docs/plans/aseprite-mcp-pixel-art/README.md, docs/plans/visual-asset-management-runtime-integration/README.md
- docs/guidelines/agent_working_environment.md (MCP setup section)

## Related Stored Artifacts
- staging_artifacts/TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT/

## Related Code Areas
- experiments/aseprite_mcp/ -> visual_assets/drawing/, tests/visual_assets/, .mcp.json, .github/workflows/test.yml, tests/tools/

## Assumptions / Open Questions
- `pyproject.toml` already sets `pythonpath = ["."]`, so `import visual_assets...` works under pytest from the repo root.
- Open: whether `graphify update .` picks up a new top-level package (it indexes code; confirm and report).

## Implementation Notes
Work done in the shared worktree (`rpg-aseprite-mcp`, branch `aseprite-mcp-pixel-art`), behaviour-preserving, in plan order. The split was
generated mechanically from AST nodes of the old modules (names rewritten, bodies untouched), then verified by the identical-names check below.

Module map (old -> new): `adapter.py` -> `config`, `errors`, `schema/{primitives,ops}`, `backend/{sandbox,lua_runner}`,
`workspace/{revisions,jobs,locks}`, `api`; `highlevel.py` -> `colors` + `technique/{ramps,dither,stroke,shading,masks,ascii,lint}`;
`highlevel_tools.py` -> `compose` + `server/highlevel_tools`; `server.py` -> `server/{app,lowlevel_tools,__init__,__main__}`;
`pin_hash.sh` -> `pin.py`; `lua/ops.lua` -> `backend/lua/ops.lua` (git rename, 0 changed lines, same sha256).

**Deviations from the structure doc (each with its reason):**
1. `technique` may import the leaf modules `errors` and `colors` (table said "nothing"): it raises `AdapterError` and parses colours; duplicating
   both would be worse. It still imports no I/O layer. Encoded in `DRAWING_ALLOWED`, recorded in the ADR.
2. `colors.py` holds one hex parser; the adapter's `_color` is now `list(hex_to_rgba(value))` (same regex, same message, same values).
   `_hue_toward`, `_N4`, `_BAYER` lost their underscore because they are now used across modules (`hue_toward`, `shading.N4`, `dither.BAYER`).
3. `backend/lua_runner.check_lua_template` hashes the template with `hashlib` directly instead of calling the workspace's `sha256_file`
   (backend must not import workspace). The workspace's `sha256_file` stays the single patch point for revision hashing.
4. `server/`: `__init__` assembles the app (low-level tools register by import, high-level via `register(mcp)`), so `python -m visual_assets.drawing.server`
   and `from visual_assets.drawing.server import mcp` both give the full 15 tools in the old order. The high-level tools call `compose.X` instead of the
   old `globals()["X"]` indirection (same behaviour).
5. Tests: validation-before-Aseprite tests (e.g. `test_validation_rejects_before_running_aseprite`) stay in `integration/` because they create a sprite
   first; their bodies are unchanged. A `needs_aseprite` marker (registered and applied by `tests/visual_assets/drawing/conftest.py`) replaces the
   per-module `skipif`. The stdio tests are split: tool list and error reporting need no Aseprite (`drawing/test_server_stdio.py`, run in CI);
   the four that draw are in `integration/test_server_stdio.py`. They now pass `ASEPRITE_MCP_BINARY` to the server, so they skip under
   `ASEPRITE_MCP_BINARY=/nonexistent` (before, they used a hardcoded `/usr/bin/aseprite` check).
6. CI base-collect list: `$([ -d tests/visual_assets ] && echo tests/visual_assets)` instead of an unconditional entry, because on this PR the base
   checkout has no such directory and pytest would abort the whole base collection for the existing directories.
7. `.mcp.json`: the new entry is a pure text insertion; every existing entry's content is byte-identical, but the headroom entry's closing `}` gains
   a trailing comma (unavoidable JSON syntax).
8. `pyproject.toml` untouched: the `needs_aseprite` marker is registered by a `pytest_configure` hook in the new conftest, not in `[tool.pytest]`.
9. `backend/lua/ops.lua` still has a comment that says "validated by adapter.py"; left as is because the file must stay byte-identical.

Extra tests added beyond the 209 (49 total): `test_boundaries.py` (41: one per module, `src` direction, layer known, and 7 planted-violation self-tests
that feed the checker source with a broken rule), `unit/test_workspace_isolation.py` (5: each patched config name is observed from the module that
consumes it), `unit/test_pin.py` (3).

### Post-push CI defect and fix (2026-10-02, asset-planner)
The first push of this ticket (0286705d) failed CI job "Architecture / docs / static": the base-branch collection
list used `$([ -d tests/visual_assets ] && echo tests/visual_assets)` (deviation 6), which
`tests/static/test_ci_step_summary_reporting.py` tokenises as an extra path (`tests/visual_assets)`), breaking the
required head/base path parity. The planner accepted that deviation in review without running `tests/static`.
Fix: list the path plainly, like the others, and create the directory in the base checkout on its own line first
(`mkdir -p /tmp/base-checkout/tests/visual_assets`), so a base branch without it does not abort collection. A first
attempt at the fix failed two guards (a comment containing a `tests/...` token, and a broken
`cd /tmp/base-checkout && pytest` prefix) and was corrected. Verified: the job's test set passes locally (277 passed),
and the base collection was simulated on an `origin/main` checkout that lacks the directory (exit 0, 3479 collected).

## Test Summary
All commands from the worktree root with the main checkout's venv.
- **R1 regression:** the 209 pre-move test ids (function + parameters) are identical by name under `tests/visual_assets`
  (`comm` of the sorted collect-only lists is empty both ways before the 49 additions); new total **258**, difference exactly the 49 added tests above.
- **Full, with Aseprite:** `pytest tests/visual_assets` -> **258 passed, 0 skipped**. Also run with `HOME` pointed at an empty temp dir: 258 passed and the
  dir was still empty afterwards (R4, dynamic).
- **As CI sees it** (`ASEPRITE_MCP_BINARY=/nonexistent`): **96 passed, 162 skipped, 0 failed**. Baseline in the old tree under the same condition was
  51 passed / 158 skipped; 51 + 49 new - 4 stdio tests that now honour the env var = 96 passed; 158 + 4 = 162 skipped.
- **R2:** `backend/lua/ops.lua` sha256 `efa8638607c4686717bb7a41ff0c4e1e7d7f1c543b6d032b3528143534b50a94` before and after; `config.LUA_SHA256` equal;
  git shows the file as a pure rename (0 lines). Tool names unchanged (15, same order): new_sprite apply_ops branch_sprite inspect preview filmstrip
  list_sprites make_ramp shade dither stroke auto_outline remap_palette lint_sprite ascii_view.
- **S1:** `python -m visual_assets.drawing.server` from the repo root and `bash visual_assets/start_mcp.sh` run from `/tmp` both answered `list_tools` over real
  stdio with the same 15 tools. Launcher failure branch (probe pointed at a missing package): one line "ERROR: no usable python3 with the 'mcp' package found
  for visual_assets drawing server", exit 1.
- **tests/tools** (the CI step it joins): `registration + launcher + generate_registry + write_path_guard + ci_workflow_test_coverage` 179 passed.
  The whole directory showed 3 failures + 1 error on the first full run: the two `test_generate_registry` ones were this ticket's own docs lacking frontmatter
  (fixed, now pass); `test_write_path_guard` passes on rerun (flaky under load); `test_entity_lifecycle_score::...800t...` fails the same way on the untouched main
  checkout (pre-existing, unrelated).
Mutation / planted-violation results (each applied for real, seen, reverted; `.mutbak` leftovers checked absent):
- B1 `technique/ramps.py` importing `api` -> CAUGHT (`test_visual_assets_module_respects_the_boundaries[...ramps.py]`)
- B2 `drawing/api.py` importing `src` -> CAUGHT; `src/core/items.py` importing `visual_assets` -> CAUGHT (`test_src_never_imports_visual_assets`)
- B3 `drawing/workspace/jobs.py` referencing `visual_assets/catalog/...` -> CAUGHT
- R4 a module doing `from ...config import WORKSPACE` -> CAUGHT by the boundary test; an import-time frozen copy of `config.WORKSPACE` in `jobs`, `revisions`,
  `locks`, `api.list_sprites`, of `JOB_TIMEOUT_S`/`ASEPRITE` in `sandbox`, of `LUA_SHA256` in `lua_runner`, of `MAX_FILE_BYTES` in `revisions` -> each CAUGHT by
  `unit/test_workspace_isolation.py` (two first attempts were invalid mutations I made myself and re-did: a no-op variable, and an assignment placed before `import config`;
  `list_sprites` first survived until the test planted a revision in the temp workspace)
- L1 launcher: probe removed, bare-exists shortcut added, `cd "$REPO_ROOT"` removed -> each CAUGHT (3 mutants)
- L2 `.mcp.json`: args altered, entry renamed -> CAUGHT (2 mutants)
- pin: wrong digest written, no refusal on a config without exactly one pin line -> CAUGHT (2 mutants)

## Files Changed
`visual_assets/` (new: `__init__`, README, `start_mcp.sh`, `drawing/**`, `store/{__init__.py,README.md}`, `catalog/{README.md,STORE_FORMAT,7 x .gitkeep}`);
`tests/visual_assets/**` (new); `tests/tools/test_mcp_json_registration.py`, `tests/tools/test_mcp_launcher_hardening.py` (extended); `.mcp.json` (+1 entry);
`.github/workflows/test.yml` (+1 step, merge list, base-collect list); `.gitignore` (+`visual_assets/catalog/.quarantine/`); `docs/assets/{drawing_tools,pixel_art_technique,store_contract}.md`;
`docs/architecture/visual_asset_foundation_adr.md`; `docs/plans/aseprite-mcp-pixel-art/README.md` and `docs/plans/visual-asset-management-runtime-integration/README.md`
(dated status notes); removed `experiments/aseprite_mcp/`; bookkeeping: this ticket, stored artifacts, `docs/REGISTRY.yaml`, branch monitoring shards.
No change under `src/`, `frontend/`, `requirements*.txt` or `pyproject.toml` (`git diff --stat origin/main` over those paths is empty).

## Completion Summary
Closed 2026-10-02 by hand-orchestration. The drawing tools now live in `visual_assets/drawing/` with the layered module layout, no behaviour change (209 old tests
present by name and green, `ops.lua` byte-identical, same 15 tools), tests in `tests/visual_assets/`, a boundary guard with planted-violation self-tests, empty
`store/` and `catalog/` skeletons, launcher + `.mcp.json` entry, one CI step, docs and ADR. Suite: 258 passed with Aseprite, 96 passed / 162 skipped without.
`make knowledge-index-update` ran (the worktree had no index, so it was a full build, about 10 minutes, exit 0) and `graphify update .` ran (the worktree had no graph,
so it was a full rebuild; it does index the new top-level package: `visual_assets/drawing/*.py` nodes appear in queries).
Open, not verifiable here: the PR CI run of the new step and its junit shard in the merged report (the one unchecked criterion); the user-scope MCP registration still points
at the old path until asset-planner repoints it. Known gaps: D2-D4 stay proposed; ops.lua's stale "adapter.py" comment cannot change; nothing committed or pushed.

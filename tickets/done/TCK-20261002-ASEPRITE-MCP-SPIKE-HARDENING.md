---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING
phase: done
date: 2026-10-02
tags: [mcp, testing, security]
---

# TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING

## Title
Harden the Aseprite MCP spike: real-editor negative suite, missing structural ops, MCP-level test

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`experiments/aseprite_mcp/` is a working, registered (user-scope) project-owned stdio MCP server that
draws RGB pixel-art through the real Aseprite binary (54 tests green; a 16x16 knight with 3 layers,
2-frame idle and 3 variants was drawn end to end). It is a spike: it lacks the failure-mode evidence the
M1 plan requires (`M1-W06` negative suite), three structural operations the art experiments will hit, and
any test that drives the real MCP protocol. This ticket closes those three gaps *inside `experiments/`*.
It does not promote the spike to `src/`, does not touch CI, and does not create game art.

Planner/reviewer: `asset-planner`. Implementer: `asset-implementer`.

## Scope
1. **Negative suite against real Aseprite** (new `experiments/aseprite_mcp/test_negative.py`), each case
   asserting the exact observable outcome (error text or state), never just "did not crash":
   - job timeout (set `JOB_TIMEOUT_S` tiny via monkeypatch; expect `timed out`, no new revision, job dir removed)
   - corrupt `.aseprite` input whose sidecar hash was *also* rewritten to match (so the hash gate passes and
     Aseprite itself must reject it): expect `AdapterError`, no new revision
   - publish failure (monkeypatch `os.link` to raise `OSError`): no partial revision file, no orphan `.sha256`,
     job dir removed, a later edit still succeeds
   - concurrent mutation race: N threads call `apply_ops` with the same `base_revision`; exactly one succeeds,
     the rest get `stale base_revision`, and the revision chain is gap-free
   - `.jobs/` is empty after every success and every failure path
   - oversize output (monkeypatch `MAX_FILE_BYTES` small): rejected, nothing published
   - names/paths: `..`, absolute paths, NUL, unicode look-alikes, symlinked sprite dir -> rejected or confined
2. **Three structural ops**, added to `lua/ops.lua` + `adapter.py` (`OPS`, validators, `_LAYER_OPS`/`_FRAME_OPS`),
   then `./pin_hash.sh`: `delete_layer {layer}`, `delete_frame {frame}`, `resize_canvas {width, height}`
   (top-left anchored, crop or transparent pad, every layer/frame, same 1..128 bounds). Each gets a positive
   test, a bounds/validation test, and a test that the last layer / last frame cannot be deleted.
3. **MCP protocol test** (new `experiments/aseprite_mcp/test_server_stdio.py`): spawn `server.py` over real
   stdio with a temp `ASEPRITE_MCP_WORKSPACE` and assert: exact tool list, `isError` on a bad call with the
   adapter's message, an `image/png` result from `preview` and `filmstrip` with the expected pixel size,
   and that a stale `base_revision` is reported as a tool error.
4. Update `experiments/aseprite_mcp/README.md` (ops table, "Not done" list) and `OPS_HELP` in `server.py`.

## Out of Scope
- Moving anything into `src/`, `.mcp.json`, `requirements*.txt`, `pyproject.toml`, or CI (plan `U-04`, `U-14`).
- M0 licence/provenance review (`U-02`), host/confinement sign-off (`U-01`, `U-06`), numeric budgets (`U-05`).
- Indexed/grayscale colour modes, layer groups, reorder layer, onion skin, linked cels.
- Creating, judging, or committing any game art; B0-B3 adaptive memory; display harness (`CAP-A09`, M2).
- Editing `docs/plans/aseprite-mcp-pixel-art/` (a doc note on spike results is a separate ticket).

## Acceptance Criteria
- [x] `test_negative.py` covers every bullet in Scope 1; each test fails if its guarded behaviour is removed
      (implementer states, per test, the mutation used to prove this: e.g. delete the `finally`/cleanup, drop
      the stale check, drop the `_check_lua_template` call).
- [x] The race test is deterministic (barrier-started threads, no `sleep`-based timing) and passes 20 times in a row.
- [x] `delete_layer`, `delete_frame`, `resize_canvas` work through `apply_ops`, are listed in `OPS_HELP` and the
      README, and reject invalid input *before* Aseprite runs (like the existing parametrized validation test).
- [x] `test_server_stdio.py` passes with real stdio transport; it does not import `adapter` to fake the server.
- [x] Whole `experiments/aseprite_mcp/` suite green (`.venv/bin/python -m pytest experiments/aseprite_mcp -q`), 0 skipped
      on this machine; tests still skip cleanly where Aseprite/bwrap are missing.
- [x] `LUA_SHA256` re-pinned; `git diff` shows no change outside `experiments/aseprite_mcp/` except ticket bookkeeping.
- [x] No new third-party dependency; `.venv`/`.venv-knowledge` untouched.
- [x] Any defect found in the existing adapter by these tests is fixed in the adapter (not by weakening a test) and
      listed in the Completion Summary; anything not fixed is listed as a known gap.

## Related Tickets
- None open. Spike authored in this session (2026-10-02); no prior ticket (Scope/Investigate artifacts below).

## Related Docs
- docs/plans/aseprite-mcp-pixel-art/README.md and `01_supervised_headless_drawing_plan.md` (`M1-W02`, `M1-W06`, `CAP-A08`)
- docs/brainstorm/render-and-art/aseprite_mcp_pixel_art_workflow_proposal.md (sections 13, 14: tool contract, containment)
- docs/plans/render-and-art/07_manual_art_experiment_execution_plan.md (`ART-W01`..`W07`)

## Related Stored Artifacts
- staging_artifacts/TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING/ (plan, investigation, test_plan)

## Related Code Areas
- experiments/aseprite_mcp/{adapter.py, server.py, lua/ops.lua, test_adapter.py, test_ops.py, pin_hash.sh, README.md}

## Assumptions / Open Questions
- Aseprite 1.3.18.6 at `/usr/bin/aseprite` and `bwrap` (user namespaces allowed) are present on the dev machine.
- Planner probe (plan.md Step 2): Aseprite silently allows deleting the last frame/layer (leaving 0), `crop` resizes
  the canvas but not cel images, and `deleteFrame` shrinks spanning tags. The ticket's guards and cel normalisation
  follow from that; the implementer re-verifies, not assumes.
- Open: whether concurrency beyond the per-sprite `flock` (multiple server processes) is in scope later; here only
  single-process threads and two-process `flock` correctness are required.

## Implementation Notes
Order followed: negative suite first, adapter fixes driven by it, then ops, stdio test, docs. Work done in the shared
worktree `rpg-aseprite-mcp` (branch `aseprite-mcp-pixel-art`). All changes inside `experiments/aseprite_mcp/`.

Defects the new tests exposed in the existing adapter, all fixed in `adapter.py` (no test weakened):
1. **Symlinked sprite directory was followed** (`new_sprite("evil")` wrote revisions outside the workspace). `_sprite_dir`
   now refuses a symlink; `_rev_files` ignores symlinked/non-regular revision files; `list_sprites` skips symlinks.
2. **Publish was not failure-safe.** `os.link` / sidecar-write `OSError`s escaped raw (leaking paths), and a link followed by a
   failed sidecar write left a visible revision with no hash sidecar, which bricks the sprite. `_publish` now writes the sidecar
   first, links second, removes the sidecar on any failure and raises `AdapterError("could not publish revision ...")`.
   **Review fix (asset-planner, reproduced):** the first version of that order overwrote another writer's `rNNNN.sha256` when a
   collision landed between the `target.exists()` check and the sidecar write (loser bricked the winner). The sidecar is now
   created exclusively (`open(..., "x")`), so an existing one is never overwritten; an existing sidecar with no revision file is an
   orphan from an interrupted publish and is removed once and retried; if the revision file exists too, `revision collision; retry`
   is raised and only a sidecar WE created is ever removed. Invariant kept: a visible revision file implies its sidecar. Residual,
   not closable without cross-process coordination: an un-locked writer caught between its own sidecar create and its link could
   lose that sidecar to our orphan cleanup; all flock-holding writers are serialised and cannot hit it.
3. **Job-dir cleanup failure was silent** (`rmtree(ignore_errors=True)`). Now logged via logger `aseprite_mcp`; the op outcome is unchanged.
4. **`render_preview` of a missing frame or layer returned a PNG** of a blank/wrong frame. It now raises `no such frame: N` /
   `no such layer: name` (one extra inspect job per preview).

Behaviour changes callers can see: items 1, 2 and 4 above (new error messages). Risks 1 (first-creation race) and 3 (orphan
aseprite after timeout) from investigation.md were checked and are NOT defects: both tests passed unmodified and their mutations are killed.

New ops (`lua/ops.lua` + `adapter.py`, `LUA_SHA256` re-pinned): `delete_layer` (layer required, refuses last layer),
`delete_frame` (frame required, refuses last frame; tag shrink/removal is Aseprite-native and asserted in a test),
`resize_canvas` (`spr:crop`, then every existing cel normalised to a full-canvas image). Planner probes re-verified: Aseprite
deletes the last layer/frame without the guard (mutants O1/O2 are killed only because the guard exists), and `crop` leaves
cel images unresized (mutant O3 is killed: per-layer pixel counts would include off-canvas pixels). Deviation from plan: the
planner's `delete_layer {layer}` could have defaulted to the bottom layer; the adapter requires an explicit layer/frame for both
deletes so an omitted field cannot delete frame 1 or the base layer.

Test-plan corrections found while mutating: N2's listed mutation ("skip the no-result check") SURVIVES because Aseprite
still writes `res.json` with `ok=false` for a corrupt file, so the real guard is the `res.get("ok")` check (mutant N2b killed);
N3's mutation is "link before sidecar" (N3, killed by the sidecar-failure test) because the design is now sidecar-first.
Mutation O3c (drop cel normalisation only for the pad case) is behaviourally equivalent: a smaller cel renders correctly and
`cel_img` normalises on first draw, so crop is the case that needs it.

## Test Summary
`.venv/bin/python -m pytest experiments/aseprite_mcp -q -p no:cacheprovider`: **201 passed, 0 skipped** in the shared worktree (baseline 54; this includes the 49 `test_highlevel.py` tests and the high-level stdio test added by the sibling ticket, hardening's own total after the review fix is 151: 201 - 49 - 1).
Race tests looped 20x in shell: 0 failures. Barrier-started threads, no sleep for synchronisation (timeout test polls with a
10s deadline for process reaping only).
One line per test group: mutation applied -> result (every mutant applied for real, seen to fail, reverted).
- N1 timeout: delete `timeout=JOB_TIMEOUT_S` -> KILLED (`test_timeout_publishes_nothing_and_leaves_no_process`)
- N2 corrupt input + matching hash: skip no-result check -> SURVIVED (equivalent, see notes); drop `res.get("ok")` check -> KILLED
- N3 link failure: drop sidecar cleanup -> KILLED; link-before-sidecar order -> KILLED (`test_sidecar_failure_publishes_no_revision[create|write]`, which also asserts no partial sidecar remains)
- N3c collision window (review fix): `open(sidecar,"x")` -> `"w"` -> KILLED (`test_collision_between_check_and_sidecar_write_...`); unlink the competitor's sidecar on collision -> KILLED (same test); drop orphan-sidecar handling -> KILLED (`test_orphan_sidecar_..._is_replaced`); drop sidecar cleanup on write failure -> KILLED (`[write]`); remove the early `target.exists()` re-check -> SURVIVED (equivalent: the exclusive create catches the same case; kept as defence in depth)
- N4 same-base race: `flock` -> `pass` -> KILLED
- N5 first-creation race: remove exists-check in `new_sprite` -> KILLED
- N6 `.jobs` empty (success/timeout paths): remove `rmtree` -> KILLED; cleanup-failure logging removed -> KILLED
- N7 oversize: remove size check in `_publish` -> KILLED; remove size check in `_export_png` -> KILLED
- N8 names/paths: loosen `_NAME_RE` / `_LAYER_RE` / `_REV_RE` -> KILLED each; symlink-dir guard off -> KILLED; symlink-revision guard off -> KILLED; drop `_check_lua_template` call -> KILLED (existing `test_template_hash_is_enforced`)
- P preview missing frame/layer: disable check -> KILLED
- O1 `delete_layer` guard removed -> KILLED; O2 `delete_frame` guard removed -> KILLED
- O3 `resize_canvas`: drop cel normalisation -> KILLED; wrong anchor `Rectangle(1,1,..)` -> KILLED; pad-only normalisation drop -> SURVIVED (equivalent)
- O4 validation: width/height upper and lower bounds loosened -> KILLED (3 mutants; first attempt hit the `rect` validator, re-run at the right site); drop "needs a frame"/"needs a layer"/registration -> KILLED
- S1 tool list: remove a tool decorator / rename an op in help -> KILLED; S2 swallow errors in `_call` -> KILLED; S3 swap preview scale/frame args -> KILLED
`.venv`/`.venv-knowledge` untouched; no dependency added.

## Files Changed
All under `experiments/aseprite_mcp/`: `adapter.py` (fixes + 3 ops + pin; `_publish` reworked after review), `lua/ops.lua` (3 handlers), `server.py` (`OPS_HELP`),
`README.md`, new `test_negative.py`, new `test_server_stdio.py`, `test_ops.py` (extended). Bookkeeping: this ticket, its stored
artifacts, `docs/REGISTRY.yaml`, and the branch's `agent-monitoring/data/2026-W40/aseprite-mcp-pixel-art.*` shards (the working-log
row lives in `...working_log.jsonl`; `tickets/working_log.csv` is unchanged).

## Completion Summary
Closed 2026-10-02 by hand-orchestration. All four scope items delivered inside `experiments/aseprite_mcp/`: negative suite
(`test_negative.py`), three structural ops with guards and re-pinned `LUA_SHA256`, real-stdio MCP test, README/`OPS_HELP`.
Suite 196 passed / 0 skipped; race tests 20/20; every new test's mutation applied and seen to fail (two equivalent mutants
documented, one test-plan mutation corrected). Defects found and fixed: symlinked sprite dir followed, non-failure-safe publish
(orphan/missing sidecar, raw OSError), silent cleanup failure, preview of missing frame/layer returning an image.
Known gaps (unfixed, deliberate): kill/power-loss mid-publish not injected (an orphan sidecar is harmless); multi-process
concurrency only reasoned from `flock`, not tested; one extra Aseprite job per `preview`; M0 items U-01/U-02/U-05/U-06 and CI (U-14)
remain out of scope. No `src/`, `.mcp.json`, dependency or CI change; nothing committed or pushed.

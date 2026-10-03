---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING
artifact_type: plan
tags: [mcp, testing, security]
---

# Plan — TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING

All work stays in `experiments/aseprite_mcp/`. Order matters: tests that expose defects come first so fixes are
driven by evidence.

## Step 1 — Negative suite first (test-driven)
Create `test_negative.py` (same `pytestmark` skip and `workspace` fixture style as `test_ops.py`). Write all cases
from the ticket's Scope 1 before changing adapter code. Run; for each failure decide: real adapter defect (fix in
`adapter.py`) or wrong test expectation (fix the test and say why in Implementation Notes).
Helpers to add in the test file only: `jobs_empty()` (asserts `WORKSPACE/".jobs"` has no entries),
`no_aseprite_processes()` (`pgrep -f "aseprite -b"` after a timeout), `revisions(name)` (sorted `r*.aseprite`
names, asserts gap-free and each has a `.sha256`).
Race test: `threading.Barrier(N)` + `ThreadPoolExecutor`; collect results; assert exactly one success.

Expected defect candidates (see investigation §Risks 1-3): first-creation race, silent cleanup failure, orphan
Aseprite after timeout. Fix minimally: e.g. create the sprite dir under a workspace-level lock; surface cleanup
errors via a logged warning rather than `ignore_errors`; ensure the child is reaped (`start_new_session` +
kill the group, or rely on `--die-with-parent` and prove it).

## Step 2 — Three ops (API behaviour already probed by the planner, 2026-10-02, Aseprite 1.3.18.6)
Probed facts the implementation must respect:
- `spr:crop(Rectangle(0,0,w,h))` both shrinks AND grows the canvas (top-left anchored; new area transparent).
  It does NOT resize existing cel images: after a grow, a cel stays 4x4 on a 6x6 canvas; after a shrink it stays
  larger than the canvas. So after `resize_canvas`, normalise every layer x frame cel to a full-canvas image at
  the origin (clip anything outside) — reuse the `cel_img` normalisation already in `lua/ops.lua` by calling it for
  every existing cel. Without this, `summary()`'s per-layer pixel counts include off-canvas pixels.
- `spr:deleteFrame(n)` shrinks a tag spanning it (tag 1..2 became 1..1); a tag fully inside the deleted frame is
  removed. Assert and document this native behaviour; do not hand-roll tag math.
- **`spr:deleteFrame` on the only frame and `spr:deleteLayer` on the only layer both SUCCEED silently, leaving a
  sprite with 0 frames / 0 layers.** The guard ("refuse if last") is therefore mandatory in Lua, not optional;
  a test must prove the sprite is untouched and no revision is published when refused.
- `spr:deleteLayer(layerObject_or_name)` works on a named layer.

`lua/ops.lua`: `handlers.delete_layer` (guard: `#spr.layers > 1`), `handlers.delete_frame` (guard:
`#spr.frames > 1`, `check_frame`), `handlers.resize_canvas` (`spr:crop`, then normalise all cels).
`adapter.py`: validators + register in `OPS`, `_LAYER_OPS` (`delete_layer`), `_FRAME_OPS` (`delete_frame`);
`resize_canvas` takes `width`/`height` in 1..`MAX_DIM`, document-level (no layer/frame).
Run `./pin_hash.sh`. Update `OPS_HELP` in `server.py` and the README ops table.

## Step 3 — MCP stdio test
`test_server_stdio.py`: use `mcp.client.stdio.stdio_client` + `ClientSession` (already installed, `mcp==1.28.1`),
`pytest.mark.asyncio` only if `pytest-asyncio` is installed (it is, 1.4.0) else `asyncio.run` inside the test.
Server env: `ASEPRITE_MCP_WORKSPACE=<tmp_path>`. Assert exact tool names set, structure of errors, PNG sizes.
Do not import `adapter` here except to read constants.

## Step 4 — Docs + hash pin + final run
README ops table and "Not done" list updated; `./pin_hash.sh`; run the suite 20x for the race test
(`-k race --count` is unavailable, so loop in shell); ensure 0 skipped.

## Scope guards (reviewer will check)
- No edits outside `experiments/aseprite_mcp/` and ticket/staging/working-log bookkeeping.
- No new dependency, no `.mcp.json`, no CI, no `src/`.
- No test weakened to make it pass; no sleeps for synchronisation.
- Do not run `claude mcp add/remove`; registration is already done and is the planner's call.

## Acceptance-criteria map
| AC | Step |
|---|---|
| negative suite + mutation proof | 1 |
| deterministic race x20 | 1 |
| three ops + pre-validation | 2 |
| stdio test | 3 |
| suite green, 0 skipped, hash pinned, no stray diffs, no deps | 4 |
| defects fixed in adapter | 1-2 |

## Closure (per CLAUDE.md, hand-orchestrated)
Tests run; ticket moved to `tickets/done/`; staging artifacts moved to `stored_artifacts/`;
`record_hand_orchestrated_closure.py` (writes the working-log row itself); `done_checker_static.py`;
`mechanism_registry_changed_code_check.py` (advisory); clean `data/runs/*` and `reports/release_proof/*`;
stage `agent-monitoring/` and `docs/REGISTRY.yaml`; `graphify update .` is NOT needed (no `src/` or `tests/` change).
Do not commit, push, or open a PR without the user's say-so.

---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-ASEPRITE-MCP-HIGHLEVEL-PIXEL-ART-TOOLS
phase: done
date: 2026-10-02
tags: [mcp, testing, rendering]
---

# TCK-20261002-ASEPRITE-MCP-HIGHLEVEL-PIXEL-ART-TOOLS

## Title
High-level pixel-art tools for the Aseprite MCP spike (ramps, shading, dithering, strokes, outline, lint)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The spike's low-level ops (pixels, shapes, layers, frames) leave every art decision to the caller. The user
asked for researched pixel-art technique (palette, shading, technique from public guides) to be turned into
tools, both low-level control and high-level operations. This ticket adds a high-level layer that composes
the existing low-level ops, plus a technique guide with sources.

Authored by `asset-planner` at the user's explicit direction (normally planner plans/reviews only).
Remaining wiring and an independent review go to `asset-implementer`.

## Scope
- `experiments/aseprite_mcp/highlevel.py`: pure, deterministic maths: `make_ramp` (hue-shifted ramps),
  `dither_cells` (Bayer 2/4/8), `stroke_pixels` (pixel-perfect polyline), `shade_offsets` (hard-banded
  light-direction shading with orphan cleanup), `ascii_grid`, `lint_grid`.
- `experiments/aseprite_mcp/highlevel_tools.py`: sprite-facing tools built on `adapter.apply_ops` and tiled
  region readback: `ramp`, `shade`, `dither`, `stroke`, `auto_outline` (full / selout), `remap_palette`,
  `lint`, `ascii_view`, and `register(mcp)` exposing 8 MCP tools.
- `experiments/aseprite_mcp/test_highlevel.py`: 49 tests (pure + real Aseprite).
- `experiments/aseprite_mcp/TECHNIQUE_GUIDE.md`: rules, numbers, tool mapping, source disagreements, sources.
- **Remaining (implementer):** wire `highlevel_tools.register(mcp)` into `server.py`; extend the stdio test's
  expected tool set; add the tools to the README.

## Out of Scope
- Any change to `lua/ops.lua` or `adapter.py` (owned by TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING).
- Per-layer readback, cel offset/translate, polygon fill, blend modes, rotation (need Lua; follow-up).
- Anti-aliasing tools (guidance says avoid at 16-32px), indexed colour mode.
- `src/`, `.mcp.json`, CI, dependencies, game art, art-direction decisions.

## Acceptance Criteria
- [x] Ramps: base colour kept in place, luma strictly increasing, shadow hue toward blue and highlight toward
      yellow without overshooting, neutral bases handled, inputs validated.
- [x] Dither: exact coverage on a full tile for each matrix, monotone gradient, deterministic.
- [x] Stroke: L-corners removed from freehand trace; end points and vertices next to a longer segment kept (a closed box keeps its corners). Met after the review fix (see Review findings).
- [x] Shade: bevel rect lights top/left and shades bottom/right; round ellipse has 3 bands oriented to the
      light; 5 bands reachable; no orphan bands; deterministic.
- [x] Sprite tools create exactly one new revision, reject a stale base before drawing, and publish nothing on error.
- [x] `auto_outline selout` adds no new colour when a darker one already exists.
- [x] `lint` reports palette budget, orphans, value separation, edge clipping, outline mix.
- [x] High-level tests pass (49 originally in a scratch copy; now 57 in the shared worktree, 209 suite total).
- [x] MCP wiring in `server.py` + stdio tool-set test + README (implementer, 2026-10-02).
- [x] Independent review by `asset-implementer` (author cannot self-review); mutation check on at least the
      shading, dither-coverage and selout-reuse tests. DONE, but it found a defect in the Stroke criterion (below).
- [x] Whole `experiments/aseprite_mcp/` suite green in the shared worktree: 197 passed, 0 skipped.

## Related Tickets
- TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING (same worktree/branch; owns adapter.py, lua/ops.lua, server.py edits)

## Related Docs
- docs/plans/aseprite-mcp-pixel-art/README.md
- docs/plans/render-and-art/07_manual_art_experiment_execution_plan.md (ART-W01..W07)
- experiments/aseprite_mcp/TECHNIQUE_GUIDE.md (sources)

## Related Stored Artifacts
- staging_artifacts/TCK-20261002-ASEPRITE-MCP-HIGHLEVEL-PIXEL-ART-TOOLS/

## Related Code Areas
- experiments/aseprite_mcp/{highlevel.py, highlevel_tools.py, test_highlevel.py, TECHNIQUE_GUIDE.md, server.py}

## Assumptions / Open Questions
- Readers see the flattened frame (the adapter has no per-layer readback); documented as a limit.
- Numeric defaults (14 degrees/step, luma gap 12, budgets 8/12/16/24) are derived from the cited guides and one
  drawn knight; they are advice, not calibrated thresholds, and `lint` findings are never gates.
- Open: whether per-layer readback and cel offset should be added in Lua (needed for layer-accurate shading
  and for idle-bob animation without redrawing).

## Implementation Notes
Defects found by the tests/visual check and fixed in this ticket: (1) neutral bases rotated hue from 0 degrees
through magenta, giving reddish "blue" shadows; now the target hue is taken outright when saturation < 0.10.
(2) `stroke` reported a closed stroke's repeated start point; now counts distinct pixels. (3) `auto_outline
selout` invented one colour per neighbour colour (19 colours on a 16px knight); now reuses an existing darker
colour (12, the rest from shading three materials). Test-side mistakes fixed: a zero-hue-shift assertion
without rounding tolerance, a vacuous `or >= 0` assertion, an uppercase sprite name, a wrong remap count.

## Test Summary
`test_highlevel.py`: 49 passed, run in a private scratch copy made of the main checkout's coherent
`adapter.py` + `lua/ops.lua` and this ticket's three files. Not yet run green in the shared worktree: at the
time of writing its `lua/ops.lua` did not match `LUA_SHA256` (hardening ticket mid-edit), so every
Aseprite-backed test there fails closed on the pin. Visual check: a 16x16 knight (flat vs shaded+outlined),
three ramps and a dither gradient were rendered and inspected. No mutation check done yet (open AC).

## Files Changed
New (asset-planner): experiments/aseprite_mcp/highlevel.py, highlevel_tools.py, test_highlevel.py, TECHNIQUE_GUIDE.md.
Implementer: server.py (import + register hook), test_server_stdio.py (8 tool names + 2 protocol calls), README.md (High-level tools table), and the stroke fix in highlevel.py / highlevel_tools.py docstring / test_highlevel.py / TECHNIQUE_GUIDE.md. Bookkeeping: this ticket, stored artifacts, docs/REGISTRY.yaml, branch agent-monitoring shards.

## Completion Summary
Closed 2026-10-02. Wiring, stdio coverage, README and an independent review done; the review found that `stroke`'s
pixel-perfect cleanup was a no-op and it was fixed under asset-planner's explicit instruction (see Review findings). Suite in the
shared worktree: 209 passed, 0 skipped. Mutation results are recorded below. Known gaps: lint thresholds and numeric defaults are
advice from the cited guides, not calibrated; per-layer readback and cel offset still need Lua (follow-ups, not this ticket); nothing
committed or pushed.


## Review findings (asset-implementer, independent review, 2026-10-02)
Wiring done as specified: `server.py` imports `highlevel_tools` and calls `register(mcp)` before `__main__` (nothing else changed);
stdio test expects the 8 extra tool names and drives `make_ramp` (good and bad colour) and `lint_sprite` over the protocol;
README gained a High-level tools table linking TECHNIQUE_GUIDE.md. Suite in the worktree: **197 passed, 0 skipped**.

Mutations applied (file in `experiments/aseprite_mcp/`), each run against the matching tests and reverted:
- Shading direction: flip light sign in `shade_offsets` (both axes, and y only) -> KILLED (`test_bevel_rect_lights_top_left_...`)
- Dither: threshold `+0.5` -> `+0` -> KILLED (`test_dither_extremes_and_gradient_monotone`); `+0.5` -> `+1.5`, `n2` -> `n2+1`, `>` -> `<` -> all KILLED (`test_dither_coverage_over_full_tile_is_exact`). Note the exact-count test alone would not catch `+0.5` -> `+0`; the extremes/gradient test does.
- Selout reuse: always return the darkened colour -> KILLED (`test_selout_reuses_existing_dark_colours_...`); drop the luma limit -> KILLED
- Ramp: perturb the base colour -> KILLED; neutral base takes shifted hue instead of target hue -> KILLED
- Tool registration removed from `server.py` -> KILLED (`test_exact_tool_list`)
- Stroke: keep-set protection removed -> KILLED (`test_stroke_vertices_are_always_kept_...`)
- **Stroke: pixel-perfect cleanup disabled entirely, and "never remove a corner" -> both SURVIVED.**

**Defect (reported, not fixed, per the plan's scope guard):** `stroke_pixels(pixel_perfect=True)` never changes its output.
Fuzzed 40,000 cases (random 2-6 vertex polylines, open and closed): output identical with and without the flag every time.
Cause: every point the caller passes is a vertex and therefore in `keep`, and Bresenham segments between vertices contain no L
corner of their own, so the only candidate corners are protected. Even an explicit stair-step `[(0,0),(1,0),(1,1),(2,1),(2,2)]` is
returned unchanged. The `stroke` tool's docstring and README promise "pixel-perfect corner cleanup (no L-shaped doubles)", which it
does not deliver. The test `test_stroke_keeps_endpoints_vertices_and_removes_nonvertex_L_corners` is vacuous: it re-implements the
cleanup loop inside the test and never calls `stroke_pixels` on corner-bearing input, so it cannot fail when the real function
changes. Planner decision needed: either make the cleanup real (e.g. treat only the first/last point plus corners the caller marks as
vertices, or apply cleanup to a dense trace input) and test through `stroke_pixels`, or drop the claim from the docstring/README/guide.


### Stroke defect and fix (found by asset-implementer's review, fixed on asset-planner's instruction)
Finding: see above (40,000-case fuzz, vacuous test). Fix in `highlevel.stroke_pixels` (behaviour change, requested by the planner):
a point is a protected corner only if it is an end of an open stroke, or a vertex with at least one adjacent segment longer than one
pixel step (Chebyshev > 1); a vertex between two single-step segments is trace and is cleaned. Closed strokes judge the first/last vertex
with wrap-around neighbours, are cleaned cyclically (never below 3 pixels), and still repeat the start pixel at the end. Consecutive
duplicate points are dropped; cleanup repeats to a fixpoint. The invalid test was replaced by tests that call `stroke_pixels` itself
(staircase -> `[(0,0),(1,1),(2,2)]`, False -> unchanged; long-segment corner kept; closed box keeps its corners and perimeter; closed
unit loop rounded all the way round; tiny loop floor; wrap-around judgement; duplicates; two seeded property tests: dense unit-step
walks keep endpoints, give a subsequence of the raw path and leave no removable L corner; vertex lists with only long segments are
unchanged). Docstrings, the `stroke` tool description, README and TECHNIQUE_GUIDE rule 9 and Lessons bullet now state the real rule.
Surprise for the planner's example: for `[(0,0),(4,0),(4,1),(5,1),(5,2)]` the rule removes `(4,1)`, not `(5,1)` (both are unit-step trace
and the staircase loses exactly one corner, the first found); `(4,0)` is kept as expected. The test pins this.
Stroke mutants: disable cleanup, never-remove-a-corner, protect-all-vertices (the original bug), protect-none, no fixpoint loop, no
wrap-around neighbours, no 3-pixel floor -> all KILLED. SURVIVED, equivalent: marking open-stroke ends unprotected (the open loop
already skips the ends) and dropping the duplicate-point step (protection is by pixel position, so a zero-length neighbour changes nothing).

Test Summary update: whole `experiments/aseprite_mcp/` suite in the shared worktree **209 passed, 0 skipped** (high-level: 57 tests in
`test_highlevel.py`; hardening 151; stdio file 6 of which 1 is the high-level protocol test).

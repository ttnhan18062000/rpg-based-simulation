---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-REAL-ART-DRAFTS
phase: done
date: 2026-10-11
tags: [architecture, testing, mcp]
---

# TCK-20261011-VISUAL-ASSETS-REAL-ART-DRAFTS

## Title
Real-art proof: draw the three sources with the drawing tool, hand off, intake PASS, owner adopts

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 2 of `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF`. Real art, made through the same agent path every future sprite will use.

## Scope
- Draw the three sources with the `aseprite-pixel-art` MCP tools, following `docs/assets/pixel_art_technique.md` (palette discipline, outline, readable at 1x). Frames via the tools' frame support; tags; slices via the `set_slice` op (#499). Real art, not noise or fills: the point is a realistic size.
- `lint_sprite` clean (or each remaining finding justified), `export_handoff` (declares frame and slice counts), `submit_candidate`, store intake **PASS** for all three. Keep the review exports.
- Record per source: `.aseprite` bytes, dimensions, frames, tags, slices/keys, record sizes (`SourceRecord` JSON bytes, `IntakeResult` bytes), preview bytes and dimensions. Each against its bound (`MAX_SOURCE_BYTES`, `MAX_DIM`, `MAX_ANIMATION_FRAMES`, `MAX_ANIMATION_TAGS`, `MAX_SOURCE_SLICES`, `MAX_SLICE_KEYS`, `MAX_RECORD_BYTES`, `MAX_PREVIEW_BYTES`, `MAX_PREVIEW_DIM`).
- **Any bound exceeded -> STOP** (no shrinking the art to fit): report to asset-planner, who raises it as its own owner question.
- **Owner-only step:** ask the owner (blocking question, with the review exports) to `adopt` the three candidates. Record the answer and the adoption ids. The agent never runs `adopt`.

## Out of Scope
- No store (`visual_assets/store/**`) or drawing-tool (`visual_assets/drawing/**`) code change is planned. If the pipeline cannot carry real art, STOP and report to `asset-planner`: a code change becomes its own ticket on the owner's answer.
- **No bound changes** (lead-planner condition 1, 2026-10-11): if real art exceeds any bound, STOP and raise it as its own owner question; do not shrink the art to fit, and do not edit a bound or a test to pass.
- No `src/`, no app wiring (activation parked until the RPG core lands, PR #450), no client use of animation/slices/atlases, no gate result moved, no `.github/` change, no `frontend/` file.
- No new registry schema field (`MAX_REGISTRY_BYTES` budget review is the first step of the NEXT batch, not this one); keys only.
- Git LFS, raising any bound, a self-hosted runner: this batch only produces the evidence for them.

## Acceptance Criteria
- [ ] Three intake PASS results; the measurement table filled.
- [ ] The owner's adopt answer recorded (adopted, or what the owner asked to redraw).
- [ ] Planted: a handoff whose declared slice count disagrees fails intake (the existing check, run on this real art once).

## Related Tickets
- Parent: `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF`
- Needs: `TCK-20261011-VISUAL-ASSETS-REAL-ART-KEYS`

## Related Docs
- `docs/assets/store_contract.md` (animation, slices, atlas sections; "Not built" parked list), `docs/assets/budgets.md`, `docs/assets/drawing_tools.md`, `docs/assets/pixel_art_technique.md`, `docs/architecture/visual_asset_foundation_adr.md` (D2 no Git LFS, D10 local proof record, D24, D25)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS/`, `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS/` (what this batch proves on real art)

## Related Code Areas
- `visual_assets/drawing/**` (used), `visual_assets/store/intake/**` (used), `visual_assets/drafts/`, `visual_assets/catalog/**`

## Assumptions / Open Questions
- A redraw the owner asks for is in scope (same keys); a different set of keys is not.

## Implementation Notes
- DEVIATION (accepted by asset-planner 2026-10-11): the three sources were NOT drawn through the aseprite MCP server. The server in this session was started at 17:35, before PR #499 merged, and its in-memory Lua pin no longer matches the checked-out `ops.lua` (`new_sprite` refuses: "lua/ops.lua does not match its pinned hash; refusing to run"). The guard refusing is correct behaviour, not a bug. I called the exact functions the tools wrap (`visual_assets.drawing.api`, `compose`, `handoff.build_handoff`) from this worktree, whose pin matches (`5a9b265f...`, `python -m visual_assets.drawing.pin` unchanged), with a private `ASEPRITE_MCP_WORKSPACE`. Intake and review ran with `python -m visual_assets.store` in this worktree (`submit_candidate` would have staged into the main checkout). No code changed.
- The pixels come from small deterministic scripts tuned by eye after looking at every preview, not stroke-by-stroke drawing. The owner was told this and approved. The scripts are kept in `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-REAL-ART-DRAFTS/scripts/ (as `.py.txt`)` (moved to stored artifacts at close) so the art can be reproduced; the dry-run measurement is next to them.
- Art: `ui.panel_frame` 24x24, bevelled frame, four corner studs, constant centre rows/columns, slice `panel` 24x24 with 9-slice centre 8,8,8,8, 8 colours. `fx.selection_ring` 32x32, 8 frames at 100 ms, tag `pulse`, iso ring with a lit upper-left arc and a travelling highlight, slice `anchor` pivot (16,16), 4 colours. `fx.campfire` 64x64, 16 frames at 80 ms, tag `burn`, crossed logs, stones, dithered ground glow, three flames in four bands, embers, sparks rising 4 px per frame (a seamless loop), slice `base` pivot (32,63), 15 colours.
- Lint: `touches_edge` and `orphan_pixels` (info) are deliberate. The campfire has 5 `value_separation` warnings, all dark ground, log and ember tones of a decorative effect, judged acceptable and stated in the handoff limitation; one palette nudge reduced but did not clear them.
- Measurements (bounds from `visual_assets/store/config.py`), `ui.panel_frame` / `fx.selection_ring` / `fx.campfire`: source 421 / 1,919 / 10,154 B (campfire 9.9 % of `MAX_SOURCE_BYTES` 102,400); dimensions 24 / 32 / 64 (`MAX_DIM` 128); frames 1 / 8 / 16 (`MAX_ANIMATION_FRAMES` 16); tags 0 / 1 / 1 (16); slices 1 / 1 / 1 (16); slice keys per slice 1 (16); `IntakeResult` 672 B each (`MAX_RECORD_BYTES` 131,072); preview 828 B 192x192 / 881 B 256x256 / 3,397 B 512x512 (`MAX_PREVIEW_BYTES` 524,288, `MAX_PREVIEW_DIM` 1024); handoff `package.json` 1,159 / 1,188 / 1,223 B. No bound exceeded.
- `SourceRecord` JSON: dry run 520 / 666 / 680 B; REAL adopted 520 / 669 / 677 B (the ids are not the placeholders, a few bytes either way; far under `MAX_RECORD_BYTES`).
- Intake: PASSED, no findings: `in-a60055155aaf773c` (panel), `in-4023376bcfb08add` (ring), `in-01dc468da4fc8235` (campfire). `review`: "Store render: MATCH" for all three. Planted: the campfire handoff with `slice_count` 2 -> QUARANTINED, `SLICE_COUNT_MISMATCH: claimed slice count 2, source has 1` (`in-aaf0a020897f0f23`, a local gitignored quarantine record only).
- Owner answers (2026-10-11): first "Approve all three"; then, after being told the four facts asset-planner required (scripted art, the build exports frame 1 only, the 5 warnings, adoption is toward rc-0009 = 70 + 3 and the rc is a separate question), "Approve all three" again. The owner ran `adopt` (the agent never does): `ad-89f6a62b866bba54` (`ui.panel_frame`, source `ui_panel_frame` r0001), `ad-6b7562f0799be9ea` (`fx.selection_ring`, `fx_selection_ring`), `ad-27d874d5da867cc0` (`fx.campfire`, `fx_campfire`); approver nhan, owner; `store verify`: ok.
- Known fact (not a bug, recorded for activation): the build exports frame 1 only (`build/exportconfig.py:53`), so a release carries the ring and the campfire as their first frame; the animation stays in the source and in `export-runtime --animation`.

## Test Summary
At this commit (`d94f58b69`): `tests/visual_assets` 2427 passed; the same 12 `registry_mismatch` tests red until rc-0009, nothing else. Catalog fixtures moved to exact new values in `adopted_facts.py` (73 sources, 80 adoptions, 160 intake files, 80 revisions; `PROOF_SOURCES`, `PROOF_ANIMATED`); the two guards now assert exactly which committed sources carry animation and slices (the proof sources only). At the batch head: 2441 passed, 0 red.

## Files Changed
- `visual_assets/catalog/sources/{ui_panel_frame,fx_selection_ring,fx_campfire}/r0001.{aseprite,source.json}`, `visual_assets/catalog/provenance/adoptions/ad-{89f6a62b866bba54,6b7562f0799be9ea,27d874d5da867cc0}.json`, `visual_assets/catalog/provenance/intake/in-{a60055155aaf773c,4023376bcfb08add,01dc468da4fc8235}{,.review}.json`
- `tests/visual_assets/adopted_facts.py`, `tests/visual_assets/test_icon_owner_fixes_adoption.py`, `tests/visual_assets/store/unit/test_detail_axis.py`, `tests/visual_assets/store/unit/test_animation_metadata.py`, `tests/visual_assets/store/unit/test_slice_metadata.py`
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-REAL-ART-DRAFTS/` (drawing scripts, dry-run measurement)

## Completion Summary
Three real sources drawn (scripts tuned by eye, driven through the drawing api because the session's MCP server was stale), intake PASS, largest 10,154 B of 102,400, no bound exceeded; the owner adopted them (`ad-89f6a62b866bba54`, `ad-6b7562f0799be9ea`, `ad-27d874d5da867cc0`) after being told the four facts asset-planner required. Commit `d94f58b69`.

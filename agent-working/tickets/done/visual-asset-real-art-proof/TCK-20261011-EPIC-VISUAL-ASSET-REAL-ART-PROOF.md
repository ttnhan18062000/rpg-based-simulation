---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF
phase: done
date: 2026-10-11
tags: [architecture, planning]
---

# TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF

## Title
Visual asset real-art proof: real animated and 9-slice sources through the whole store pipeline, measured against every bound

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
lead-planner, owner-authorized (owner, 2026-10-11: "you also can ask and decide what other runnings session to do"), chose candidate B of asset-planner's proposal: a real-art proof for animation and slices. PRs #487 and #499 shipped animation metadata, slices/9-slice/pivots, atlases and `export-runtime --slices` proven only on synthetic fixtures; no committed source has more than one frame or any slice. The parked Git LFS (ADR D2) and raise-a-bound questions reopen only "when real art exceeds it" (`store_contract.md`, `budgets.md` R4), and no real art has been measured. Lead conditions: (1) any bound exceeded -> stop, own owner question, no bound change here; (2) adopt and rc approval stay with the owner, listed as explicit asks in the PR body; (3) record measured sizes against EVERY bound in budgets.md, fits included, and name the Git LFS and raise-bounds questions with a verdict each in the closing summary; (4) the stale session_handoff refresh goes in this (first) PR.

## Scope
- Child 1 `TCK-20261011-VISUAL-ASSETS-REAL-ART-KEYS`: register the three keys below; refresh BOTH `docs/assets/session_handoff/*` snapshots (the merged ones say "awaiting push/PR").
- Child 2 `TCK-20261011-VISUAL-ASSETS-REAL-ART-DRAFTS`: draw the three sources with the drawing tool (MCP), hand off, submit, intake PASS; owner adopts (blocking question).
- Child 3 `TCK-20261011-VISUAL-ASSETS-REAL-ART-RELEASE-PROOF`: build, release rc-0009 = rc-0008's 70 + 3 (only after the owner's answer), `export-runtime --atlas --slices` proof; rc-0008's 70 entries byte-identical.
- Child 4 `TCK-20261011-VISUAL-ASSETS-REAL-ART-BUDGETS-AND-CLOSE`: measured sizes against every bound in budgets.md, the two verdicts (Git LFS, raise bounds), docs, closure.

Three new `optional: true` keys (planner decision; the owner may overrule):
  - `ui.panel_frame`: 24x24, 1 frame, one slice `panel` with a 9-slice centre (8x8 at 8,8): a HUD panel border; `safety_class: decorative`, `fallback: {kind: "none"}`.
  - `fx.selection_ring`: 32x32, 8 frames, tag `pulse`, one slice `anchor` with a pivot at the centre: the selected-unit ring; `decorative`, `fallback: {kind: "none"}`.
  - `fx.campfire`: 64x64, 16 frames (= `MAX_ANIMATION_FRAMES`), tag `burn`, one slice `base` with a pivot on the bottom row: the heaviest realistic animated source we would draw; `decorative`, `fallback: {kind: "none"}`.

## Out of Scope
- No store (`visual_assets/store/**`) or drawing-tool (`visual_assets/drawing/**`) code change is planned. If the pipeline cannot carry real art, STOP and report to `asset-planner`: a code change becomes its own ticket on the owner's answer.
- **No bound changes** (lead-planner condition 1, 2026-10-11): if real art exceeds any bound, STOP and raise it as its own owner question; do not shrink the art to fit, and do not edit a bound or a test to pass.
- No `src/`, no app wiring (activation parked until the RPG core lands, PR #450), no client use of animation/slices/atlases, no gate result moved, no `.github/` change, no `frontend/` file.
- No new registry schema field (`MAX_REGISTRY_BYTES` budget review is the first step of the NEXT batch, not this one); keys only.
- Git LFS, raising any bound, a self-hosted runner: this batch only produces the evidence for them.

## Acceptance Criteria
- [ ] Children 1-4 DONE, each commit reviewed and approved by `asset-planner`.
- [ ] Owner adopted the three sources and approved rc-0009 (or a bound was exceeded and the batch stopped on its own owner question).
- [ ] budgets.md records the real measurements against every bound; the Completion Summary names the Git LFS question and the raise-bounds question with a verdict each.
- [ ] One PR whose body lists each owner-only step (adopt, rc approval, push/merge) as an explicit ask with its status; pushed and merged only on the user's own answer (`--admin` merge run by the user).

## Related Tickets
- Children: `TCK-20261011-VISUAL-ASSETS-REAL-ART-KEYS`, `TCK-20261011-VISUAL-ASSETS-REAL-ART-DRAFTS`, `TCK-20261011-VISUAL-ASSETS-REAL-ART-RELEASE-PROOF`, `TCK-20261011-VISUAL-ASSETS-REAL-ART-BUDGETS-AND-CLOSE`
- Previous batches: `TCK-20261010-EPIC-VISUAL-ASSET-SLICES` (PR #499), `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING` (PR #487), icon rc-0008 (PR #480)
- Next (not filed): entity map markers (candidate A), which starts with the `MAX_REGISTRY_BYTES` budget review

## Related Docs
- `docs/assets/store_contract.md` (animation, slices, atlas sections; "Not built" parked list), `docs/assets/budgets.md`, `docs/assets/drawing_tools.md`, `docs/assets/pixel_art_technique.md`, `docs/architecture/visual_asset_foundation_adr.md` (D2 no Git LFS, D10 local proof record, D24, D25)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS/`, `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS/` (what this batch proves on real art)

## Related Code Areas
- `visual_assets/catalog/definitions/visual_keys.yaml`, `visual_assets/catalog/**`, `visual_assets/drawing/**` (used, not edited), `visual_assets/store/{cli,runtime_export,atlas,slices,animation}.py` (used, not edited)

## Assumptions / Open Questions
- Planner decisions and lead conditions recorded in `SEQUENCE.md`.
- Known fact to record, not fix: the build exports frame 1 only (`visual_assets/store/build/exportconfig.py:53`, "only the first frame is exported"). An animated source is released as its first frame plus its animation metadata; frames 2..N stay in the source. Client animation needs a build change first: say so in the closing summary as an input for activation, do not change it here.

## Implementation Notes


## Test Summary
`tests/visual_assets` at the batch head: 2441 passed, 0 red (it was 12 red between the keys commit and the rc-0009 commit, by planner ruling). Targeted `tests/tools`, `tests/docs`, `tests/architecture` subsets and `done_checker_static.py` per ticket are listed in the PR body.

## Files Changed


## Completion Summary
All four children are DONE on `visual-asset-real-art-proof` (off origin/main `9a9058808`), each approved by `asset-planner`: KEYS `0abcc3153`, DRAFTS `d94f58b69`, RELEASE-PROOF `a28282206` + proof record `96ca645f9`, BUDGETS-AND-CLOSE `4692f2149` + the closing commit. `tests/visual_assets`: 2441 passed, 0 red at the head; the 12 export tests that were red from KEYS until rc-0009 are green. No store or drawing code changed, no bound exceeded or changed, nothing under `src/`, `frontend/` or `.github/`.

**Owner steps, as done (2026-10-11):** the owner adopted the three sources (`ad-89f6a62b866bba54` `ui.panel_frame`, `ad-6b7562f0799be9ea` `fx.selection_ring`, `ad-27d874d5da867cc0` `fx.campfire`) after being told the pixels come from scripts, the build exports frame 1 only, the campfire's 5 `value_separation` warnings, and that adoption goes toward rc-0009; and answered "Assemble rc-0009" (73 = rc-0008's 70 byte-identical + 3).

**Verdict 1, Git LFS (ADR D2): keep closed.** Largest real source 10,154 B = 9.9 % of `MAX_SOURCE_BYTES` (102,400); tracked catalog 380,335 B / 558 files -> 418,669 B / 580 files (+10 %). Scratch noisy 64x64x16 (not committed art): 2-colour dither 16,835 B, 16-colour noise 53,832 B, full-colour noise 225,803 B (2.2x over, not pixel art). The R4 trigger has not fired.

**Verdict 2, raise a bound: none.** Every bound touched is measured in `docs/assets/budgets.md` ("Real-art measurements (2026-10)"); the closest are `MAX_ANIMATION_FRAMES` at 100 % (the campfire, by design) and `MAX_ATLAS_DIM` at 70.8 % (icon sheet). Reported only.

**Findings:** (1) the build exports frame 1 only (`build/exportconfig.py:53`), recorded as a fact; backlog `TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY` (not part of this batch). (2) any registry edit makes older candidates unexportable (`registry_mismatch`); not a rollback break; written into `store_contract.md` Known gaps.

**Deviation:** the aseprite MCP server of the session was started before PR #499 merged and its Lua pin no longer matched `ops.lua`; the pin guard correctly refused. The art was driven through the drawing api (`visual_assets.drawing.api`, pin `5a9b265f...` matched) from the worktree with small deterministic scripts tuned by eye (kept in the stored artifacts), and intake ran with the store CLI in the worktree. The owner restarted an aseprite MCP server on 2026-10-11 (asset-planner's note), so the cause is resolved for sessions started after that. NOT confirmed from the implementer session: its own `new_sprite` after the restart still refused with the pin message, because that session's server was started before the re-pin; a session started after the restart must run one `new_sprite` to confirm.

**Next asset batch:** `TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP` (filed; branch `visual-asset-sample-map`; dispatched after this merges).

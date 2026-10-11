---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-REAL-ART-BUDGETS-AND-CLOSE
phase: open
date: 2026-10-11
tags: [architecture, documentation]
---

# TCK-20261011-VISUAL-ASSETS-REAL-ART-BUDGETS-AND-CLOSE

## Title
Real-art proof: budgets.md measurements against every bound, Git LFS and raise-bounds verdicts, docs, close

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Child 4 of `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF`. Lead condition 3: the evidence must let the owner close or reopen the parked questions on facts.

## Scope
- `docs/assets/budgets.md`: a dated "Real-art measurements (2026-10)" section, one row per bound touched by children 1-3 (registry, source, record, preview, PNG, decoded, manifest, atlas, animation, slices): measured value, bound, percent used, which source. Fits are recorded too. Existing rows untouched apart from a pointer.
- Two verdicts, written in budgets.md and in the epic's Completion Summary:
  1. **Git LFS (ADR D2)**: keep closed / reopen, with the largest real source vs `MAX_SOURCE_BYTES` and the catalog's total size before and after.
  2. **Raise any bound**: none / which, with the measurement that triggers it. A trigger is only reported, never acted on here.
- `docs/assets/store_contract.md`: the frame-1 fact next to the animation section, if not already said; parked list unchanged unless the owner decided otherwise.
- Refresh both session_handoff snapshots again at close.
- Re-run `make PYTHON3=<project venv> visual-assets-aseprite-local` once if the CI staleness test says the proof record is stale (no store/drawing code edit is planned, so it may be fresh).
- PR body (`tools/delivery/pr_render.py`): an "Owner asks" list, each with its status: adopt (child 2), rc-0009 approval (child 3), any bound question, push/PR, `--admin` merge.
- Close: `record_hand_orchestrated_closure.py --path-reason batch_hand_close` per ticket, `done_checker_static.py --ticket-id` PASS, folder moved to `tickets/done/visual-asset-real-art-proof/`, `make knowledge-index-update`, REGISTRY regenerated AFTER the final stored-artifact move and before push (PR #499 CI failed once on a stale `artifact_files`).

## Out of Scope
- No store (`visual_assets/store/**`) or drawing-tool (`visual_assets/drawing/**`) code change is planned. If the pipeline cannot carry real art, STOP and report to `asset-planner`: a code change becomes its own ticket on the owner's answer.
- **No bound changes** (lead-planner condition 1, 2026-10-11): if real art exceeds any bound, STOP and raise it as its own owner question; do not shrink the art to fit, and do not edit a bound or a test to pass.
- No `src/`, no app wiring (activation parked until the RPG core lands, PR #450), no client use of animation/slices/atlases, no gate result moved, no `.github/` change, no `frontend/` file.
- No new registry schema field (`MAX_REGISTRY_BYTES` budget review is the first step of the NEXT batch, not this one); keys only.
- Git LFS, raising any bound, a self-hosted runner: this batch only produces the evidence for them.

## Acceptance Criteria
- [ ] Every bound touched by real art has a measured row in budgets.md.
- [ ] The epic's Completion Summary names both questions with a verdict each.
- [ ] All 5 tickets closed, done_checker PASS; proof record fresh at the PR head.

## Related Tickets
- Parent: `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF`
- Needs: `TCK-20261011-VISUAL-ASSETS-REAL-ART-KEYS`, `TCK-20261011-VISUAL-ASSETS-REAL-ART-DRAFTS`, `TCK-20261011-VISUAL-ASSETS-REAL-ART-RELEASE-PROOF`

## Related Docs
- `docs/assets/store_contract.md` (animation, slices, atlas sections; "Not built" parked list), `docs/assets/budgets.md`, `docs/assets/drawing_tools.md`, `docs/assets/pixel_art_technique.md`, `docs/architecture/visual_asset_foundation_adr.md` (D2 no Git LFS, D10 local proof record, D24, D25)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS/`, `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS/` (what this batch proves on real art)

## Related Code Areas
- `docs/assets/{budgets,store_contract}.md`, `docs/assets/session_handoff/*`, `docs/assets/aseprite_local_proof.json`

## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary


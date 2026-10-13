---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY
phase: open
date: 2026-10-11
tags: [architecture]
---

# TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY

## Title
The store build exports frame 1 only: animated sources need a frame-export path before any client animation activation

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Backlog, filed by asset-planner at lead-planner's request (2026-10-11), outside batch `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF`. That batch only records this limit, so it is not lost in budgets.md. `build-config` accepts only `frame: 1` (`visual_assets/store/build/exportconfig.py:53`, "only the first frame is exported"), and the exporter renders `--frame-range 0,0` (`visual_assets/store/build/exporter.py:64`). Animation metadata (durations, tags; PR #487) and slice keys per frame (PR #499) reach the runtime export, but the pixels of frames 2..N never leave the source. **Trigger: before any client animation activation** (activation is parked until the RPG core lands).

## Scope
- Design (ADR D-record, owner approves the text): how a released animated artifact carries all frames (per-frame PNGs, or a strip/sheet per source), how this interacts with atlases (`MAX_ATLAS_DIM`) and `slices.json` frame keys, and how the artifact identity and fingerprint change (the D10 proof record and LUA pin).
- Budget rows for the new output (decoded and PNG bounds per frame or per sheet), measured on the real animated sources from the real-art proof batch.
- Single-frame sources stay byte-identical; rc-0008/rc-0009 entries rebuild identically.

## Out of Scope
- Client animation playback (activation), any `src/` or `frontend/` change, raising existing bounds without an owner decision.

## Acceptance Criteria
- [ ] Owner-approved D-record; an animated source's frames all reach the release, checked by pixel hash per frame.
- [ ] Single-frame artifacts and existing rcs byte-identical; proof record re-run once.

## Related Tickets
- `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF` (records the fact; its real animated sources are this ticket's test input)
- `TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS`, `TCK-20261010-EPIC-VISUAL-ASSET-SLICES`

## Related Docs
- `docs/assets/store_contract.md` (animation, atlas, slice sections), `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS/`

## Related Code Areas
- `visual_assets/store/build/{exportconfig,exporter}.py`, `visual_assets/store/{runtime_export,atlas,animation,slices}.py`, `visual_assets/catalog/build-config`

## Assumptions / Open Questions
- Not scheduled. It reopens when activation of client animation is planned, or earlier on the owner's word.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary


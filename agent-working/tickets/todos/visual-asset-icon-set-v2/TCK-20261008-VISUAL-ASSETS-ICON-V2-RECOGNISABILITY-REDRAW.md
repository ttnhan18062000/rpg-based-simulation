---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW
phase: open
date: 2026-10-08
tags: [architecture, hud, testing]
---

# TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW

## Title
Run the recognisability checks on icons-v2 and redraw every flagged icon to its spec, the weapon sword included, before the owner gate

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Child 4c of `TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2`. With child 4b's specs and checks committed, fix what they flag. The weapon sword is flagged by the owner already. At the owner gate of `icons-v2` the user found the weapon sword "kinda weird" (a short 4 px blade, a lumpy grip
wider than the guard, no pommel: reads as a cleaver, and it nearly duplicates the rogue dagger) and asked for the root
cause. Planner analysis (2026-10-08): every gate measures **distinguishability** (I1 shape, I2 value, I3 contrast, lint),
none measures **recognisability**. Four misreads in 36 icons all passed every gate: the debuff frame (a smile), the shrine
(a bell), the ruins (a boot), the sword (a cleaver). Causes: one-word glyph specs with no proportions; drawing from
memory with no reference study; a design loop that optimised the rule numbers; no cross-family comparison; agent eyeballing
of tiny pixel art is unreliable (the implementer and the planner both passed the sword). The user chose (blocking
question, 2026-10-08) **"Fix the process now"**: build the checks in this batch, run them on the 22 v2 icons, redraw what
they flag, then the owner gate.

## Scope
- Redraw the sword to its spec and every icon the recognition check or the look-alike report flags (report-only
  findings: the planner decides which are redrawn). `draft keep --replace` per slot; intakes via the worktree CLI.
- Re-run the sheet rule (thresholds unchanged), the recognition check and the look-alike report on the full set; record
  before/after per redrawn icon in `docs/assets/icon_set_v2_review.md`; refresh the fixture and the draft set hash in
  the adopt-set template.
- If a family convention changes (e.g. weapons upright), list every icon it touches and redraw those too.

## Out of Scope
- Adopted key-set pixels (a finding there is reported to the owner only). Wiring.

## Acceptance Criteria
- [ ] Every flagged icon redrawn or explicitly kept by the planner with a reason; the sword redrawn.
- [ ] Sheet rule PASS, recognition re-run recorded, look-alike report re-run recorded.

## Related Tickets
- TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2 (epic), TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS

## Related Docs


## Related Stored Artifacts


## Related Code Areas
- visual_assets/drafts/icons-v2/, frontend/src/visualAssets/__fixtures__/icondraft_v2/

## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary


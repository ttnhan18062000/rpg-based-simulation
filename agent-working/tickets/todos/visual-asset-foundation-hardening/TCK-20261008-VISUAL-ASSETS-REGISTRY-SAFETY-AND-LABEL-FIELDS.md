---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REGISTRY-SAFETY-AND-LABEL-FIELDS
phase: open
date: 2026-10-08
tags: [architecture, testing, hud]
---

# TCK-20261008-VISUAL-ASSETS-REGISTRY-SAFETY-AND-LABEL-FIELDS

## Title
Structured fallback-safety class and translatable label per visual key, verify rejects variant axes, activation-time fallback check (M1 gaps W02.7, W03.1, W06.3)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 3 of `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING`. The 36 icon keys state their class and fallback only as prose (35 identifying, 1
decorative). Register GAP rows W02.7 (no class field), W03.1 (nothing rejects non-empty `variant_axes`, D17), W06.3 (no
check that each key has its alternative). External research (W3C WAI images tutorial) adds a functional label per icon
(what it does, translatable) and a decorative flag so the client can emit alt/aria text.

## Scope
- Registry schema: `safety_class` (decorative | identifying | critical) and `fallback` (structured: text and/or glyph
  reference) and `label_key` + default English label for icon keys; migrate every key from its prose (terrain, border,
  icon). The planner proposes the label text; the OWNER approves the label list by blocking question before commit
  (critical alternatives need the surface owner per fallback_safety rule 2).
- `verify`: reject non-empty `variant_axes` (W03.1); reject a key without class/fallback (W02.7); a check usable at
  build/release/activation that each key's alternative exists (W06.3).
- Update `m1_contract_register.md` rows W02.7, W03.1, W06.3 to MET with evidence; the M1 RESULT stays BLOCKED (M0) —
  say so. ADR row if the schema change needs one. Registry hash moves: with child 1 done no fixture guard breaks; no new
  release candidate is assembled unless the owner asks.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art.

## Acceptance Criteria
- [ ] Fields in the schema, all keys migrated, owner-approved labels; verify rules tested with mutants; register rows re-derived; M1 result unchanged and stated.

## Related Tickets


## Related Docs
- docs/assets/fallback_safety.md (rules 1-3), m1_contract_register.md (W02.7, W03.1, W06.3), ADR D17

## Related Stored Artifacts


## Related Code Areas
- visual_assets/store/contracts/definitions, visual_assets/catalog/definitions/visual_keys.yaml, visual_assets/store/verify.py

## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary


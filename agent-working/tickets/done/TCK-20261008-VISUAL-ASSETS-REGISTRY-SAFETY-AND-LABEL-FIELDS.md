---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REGISTRY-SAFETY-AND-LABEL-FIELDS
phase: done
date: 2026-10-08
tags: [architecture, testing, hud]
---

# TCK-20261008-VISUAL-ASSETS-REGISTRY-SAFETY-AND-LABEL-FIELDS

## Title
Structured fallback-safety class and translatable label per visual key, verify rejects variant axes, activation-time fallback check (M1 gaps W02.7, W03.1, W06.3)

## Status
DONE

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
- [x] Fields in the schema, all keys migrated, owner-approved labels; verify rules tested with mutants; register rows re-derived; M1 result unchanged and stated.

## Related Tickets


## Related Docs
- docs/assets/fallback_safety.md (rules 1-3), m1_contract_register.md (W02.7, W03.1, W06.3), ADR D17

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-REGISTRY-SAFETY-AND-LABEL-FIELDS/ (plan with the owner's approval, investigation, test_plan, mutant_proof)

## Related Code Areas
- visual_assets/store/contracts/definitions, visual_assets/catalog/definitions/visual_keys.yaml, visual_assets/store/verify.py

## Assumptions / Open Questions
- Owner approved the 35 labels by blocking question on 2026-10-09: "Approve the list as written".
- `icon.marker.enemy_camp`'s registry prose was truncated at 256 characters; its structured fallback follows the other markers (assumption, in plan.md).
- No release candidate was assembled (none asked for); rc-0007 keeps its older registry hash and the store's refusal for a stale candidate is unchanged.

## Implementation Notes
- Model fields `safety_class`, `fallback`, `label_key`, `label` (optional in the record); `registry.safety_problems` (W02.7, W03.1) in the loader; `registry.fallback_problems` (W06.3) in `assemble_release` and `export_runtime` (`fallback_missing`). All 62 keys migrated from their prose. ADR D23. Register rows re-derived: 58 MET / 4 GAP / 6 N/A, the M1 result stays BLOCKED (M0 INCONCLUSIVE).

## Test Summary
- 2023 passed (scoped), 2 skipped, 1 xfailed; mutants J-T (two survived at first and the tests were strengthened); store verify ok; icon fixtures identical; vitest 270 passed.

## Files Changed
- visual_assets/store/{contracts/definitions,catalog/registry,release,runtime_export}.py, visual_assets/catalog/definitions/visual_keys.yaml, visual_assets/catalog/fixtures/contracts/visual_keys.fixture.yaml, tests (registry, release, runtime export, record bounds), docs (register, fallback_safety, ADR D23, budgets, plan README), ticket and artifacts.

## Completion Summary
Every registry key declares a safety class and a structured fallback, icons carry owner-approved accessible labels, the loader refuses axes and malformed fallbacks, and release and export refuse a key left without an alternative; registering them moved the registry hash and broke no fixture guard. Register rows W02.7, W03.1, W06.3 are MET; the M1 result stays BLOCKED.

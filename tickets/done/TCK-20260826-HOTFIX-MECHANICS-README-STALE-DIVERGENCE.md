---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260826-HOTFIX-MECHANICS-README-STALE-DIVERGENCE
phase: open
date: 2026-08-26
tags: [documentation]
---

# TCK-20260826-HOTFIX-MECHANICS-README-STALE-DIVERGENCE

## Title
`docs/mechanics/README.md`'s wound-threshold "Parity note" describes an already-fixed divergence
as still open

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Found and confirmed during `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`'s "Known open
items" review: `docs/mechanics/README.md`'s Sub-Contract Index carried a "Parity note" stating
`damage_formula_contract.md` documents wound-infliction threshold as 25% while Chapter 02 states
40%, citing `docs/parity_ledger/combat_movement.yaml` entry COMB-290 as `status: divergent`.
Confirmed directly, not assumed: COMB-290 is `status: verified` (not divergent), and
`docs/mechanics/02_combat_laws.md` already correctly states "strictly greater than 25%". The
divergence this note describes no longer exists.

## Scope
- Remove the stale "Parity note" blockquote from `docs/mechanics/README.md`'s Sub-Contract Index
  section -- the divergence it describes is already resolved, both cited source documents agree.

## Out of Scope
- Any change to `docs/mechanics/02_combat_laws.md` or `damage_formula_contract.md` themselves --
  both already correct, confirmed directly.
- Any change to COMB-290's own parity ledger entry -- already `status: verified`, accurate as-is.

## Acceptance Criteria
- [x] The stale "Parity note" blockquote is removed
- [x] Confirmed directly (not assumed) that COMB-290 is `status: verified` and Chapter 02 already
      states 25%, before removing the note

## Related Tickets
None -- flagged directly in `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`'s "Known open
items" section as a small doc-only hotfix, independent of any of the 65 roadmap design ideas.

## Related Docs
- docs/mechanics/README.md (the file changed)
- docs/mechanics/02_combat_laws.md (confirmed already correct, cross-referenced)
- docs/parity_ledger/combat_movement.yaml (COMB-290, confirmed already `status: verified`)

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
None -- documentation only.

## Assumptions / Open Questions
None.

## Implementation Notes
No test references this note's text (`grep`-confirmed before removal), so no test updates needed.

## Test Summary
Documentation-only change. `tools/validate_frontmatter.py docs/mechanics/README.md` passes.

## Files Changed
- docs/mechanics/README.md

## Completion Summary
The Mechanics Bible's own Sub-Contract Index no longer flags a resolved parity divergence as
open, closing a small but real documentation-currency gap.

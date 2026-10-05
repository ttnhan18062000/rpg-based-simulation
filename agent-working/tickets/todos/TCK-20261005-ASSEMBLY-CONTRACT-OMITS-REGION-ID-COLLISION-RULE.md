---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261005-ASSEMBLY-CONTRACT-OMITS-REGION-ID-COLLISION-RULE
phase: open
date: 2026-10-05
tags: [world, documentation]
---

# TCK-20261005-ASSEMBLY-CONTRACT-OMITS-REGION-ID-COLLISION-RULE

## Title
`assembly_contract.md` documents quest-id collisions but not region-id collisions or #335's
namespace-prefix rule — the newest assembly-abort condition is undocumented

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Raised by `rpg-implementer-2` while closing
`TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` as stale-premise, and filed here
because placing doc text is the planner's call.

`docs/world/assembly_contract.md` §"Quest Definitions Merge Contract (WORLD-ASM-012)" documents one
assembly-abort condition in full: two modules contributing the same quest `id` raises
`AssemblyCollisionError(ValueError)`, not recoverable, assembly aborts.

**There is now a second such condition and the contract does not mention it.** PR #335 added
per-module-ref region namespacing (`_assign_region_namespaces`), and a duplicate region id that
survives it raises from `src/worldbuilding/resolver.py:359` and `src/worldbuilding/schema.py:319`.
Neither the namespace rule nor the abort appears anywhere in the contract, so a module author reading
it has no way to learn that region ids are prefixed, or that a collision is fatal, or that namespace
choice is the disambiguation mechanism.

This is the pattern the Authoritative Mechanics Rule exists to prevent: the behaviour landed, the
contract did not move with it.

## Scope
1. Add a region-id collision section to `docs/world/assembly_contract.md`, stating the namespace
   prefixing, the abort, and the author's disambiguation lever. **Verbatim text below** — use it
   rather than paraphrasing, then verify each claim against `src/` at the commit being edited.
2. Check whether the section needs a `WORLD-ASM-0xx` compliance id to match its siblings, and if so
   add the row to the "Compliance ID Index" table at `:226`. Every other contract section in the file
   carries one; a section without one may be invisible to whatever consumes that index. **Check what
   consumes it before inventing an id** — if ids are assigned by a registry or a test, follow that
   mechanism rather than picking the next free number.
3. Re-derive the two line numbers (`resolver.py:359`, `schema.py:319`) at the commit being edited.
   They are from `fb0c1c318`.

## Out of Scope
- Region *geometry* overlap. That is `TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER`, a
  separate and larger defect — distinct ids whose bounds still overlap. Do not conflate them; this
  ticket is about ids only.
- Changing the namespacing behaviour or the abort. Documenting what #335 shipped.
- The quest-id section. Correct as it stands.

## Proposed Verbatim Text

Insert as a new section immediately **before** the line `## WorldAssemblyValidator Parametric
Contract (WORLD-ASM-013)` (unique anchor):

```markdown
## Region Id Collision Contract

`WorldModuleSpec` region contributions are merged into `WorldSpec.regions` during module traversal.
Unlike quest definitions, region ids are **namespaced before** the duplicate check rather than
colliding on the authored id.

**Merge rules:**

1. Each region id is prefixed with `"<namespace>_"` per module ref, where the namespace comes from
   the composition's own module ref. A module authored with region `hometown`, composed under
   namespace `trading`, contributes `trading_hometown`.
2. A module ref with no namespace contributes its region ids unprefixed.
3. A duplicate region id that survives prefixing aborts assembly with
   `ValueError("Duplicate region ID collision ...")`. Not recoverable.

**Author guidance:** two modules may both author a region called `hometown`; they are composable
only if at least one is given a distinct namespace in the composition. The namespace, not the
authored id, is the disambiguation lever. A composition that gives two modules the same namespace
and the same authored region id is invalid and will abort.

**Not covered by this rule:** region *bounds*. Namespacing makes ids distinct; it does not make the
regions spatially disjoint, and two differently-named regions may occupy overlapping tiles. The
overlap policy is a separate contract — see `docs/mechanics/06_worldbuilding_foundation.md`.
```

## Acceptance Criteria
- [ ] The section exists in `docs/world/assembly_contract.md`, placed as described.
- [ ] Every claim in it is verified against `src/` at the editing commit, and the two line numbers are
      re-derived rather than copied from this ticket.
- [ ] The compliance-id question from Scope 2 is answered either way, with the reason recorded —
      "no id needed because X consumes the index and does not require one" is a valid answer.
- [ ] The closing "Not covered by this rule" paragraph survives. It is the part that stops the next
      reader from assuming namespacing solved the geometry problem too, which is exactly the
      conflation this ticket's sibling exists to fix.
- [ ] `make knowledge-index-update` run, since `docs/` changed.

## Related Tickets
- `TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` — closed stale-premise; this is the
  doc half of its closure.
- `TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER` — the geometry sibling. Explicitly a
  different defect.
- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` (#335) — shipped the behaviour being
  documented.

## Related Docs
- `docs/world/assembly_contract.md` — the file to edit
- `docs/mechanics/06_worldbuilding_foundation.md` — the overlap policy the new text points at

## Related Stored Artifacts
_(none)_

## Related Code Areas
- `src/worldbuilding/resolver.py:359` — the duplicate-region-id raise (at `fb0c1c318`)
- `src/worldbuilding/schema.py:319` — the second raise site (at `fb0c1c318`)
- `src/worldbuilding/resolver.py::_assign_region_namespaces` — #335's prefixing

## Assumptions / Open Questions
- The proposed text's claim that an unnamespaced module ref contributes ids unprefixed is inferred
  from how `frontier_living_world` resolves (`hometown` bare, `trading_hometown` prefixed). **Verify
  it against `_assign_region_namespaces` before committing the text** — if the real rule is different
  (e.g. a default namespace derived from the module id), fix the text rather than the code.
- Whether `ValueError` should be an `AssemblyCollisionError` for symmetry with the quest case is a
  code question, not this ticket's. Note it if it looks right; do not change it here.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_

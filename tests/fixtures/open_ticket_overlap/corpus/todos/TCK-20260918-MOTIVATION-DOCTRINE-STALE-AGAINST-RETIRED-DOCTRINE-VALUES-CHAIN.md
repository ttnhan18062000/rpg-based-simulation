---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN
phase: open
date: 2026-09-18
tags: [architecture, schema]
---

# TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN

## Title
`motivation_doctrine`'s registry entry outlived the code chain it names — `doctrine`/`values` were
formally retired, but the mechanism and its `depends_on` edges remain

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
Found incidentally while auditing `depends_on` edges
(`TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT`): `MotivationModel`
(`src/core/cognition.py:419-438`), the state class most plausibly behind `motivation_doctrine`, is a
pure dataclass — only `role_fit`/`ambition`/`moral`/`named_intention` fields plus
`to_canonical_dict()`, no computation. Its own docstring states:

> `doctrine`/`values` fields (formerly `IdentityDoctrine`/`ValuePreferenceProfile`) removed --
> confirmed dead, never read outside the now-deleted `MotivationBiasService`'s own bias-multiplier
> method. See `docs/guidelines/intentional_divergences.md` §2.53.

(`TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT`.) The registry's `motivation_doctrine`
mechanism entry (`registries/mechanisms.yaml`) still declares `depends_on: [goal_hierarchy,
affection_relationship_bonds]` and `state: gap` — a mechanism named after a concept
(`doctrine`) whose own code chain was already formally retired ten days before this finding.

## Scope
1. Re-check whether `motivation_doctrine` as currently named/scoped still describes anything real in
   the codebase, given the doctrine/values retirement — or whether it should itself be retired,
   renamed, or its scope narrowed to what `MotivationModel` actually still contains
   (`role_fit`/`ambition`/`moral`/`named_intention`).
2. If retired: follow the Retire path in the seven-kind change taxonomy
   (`docs/plans/mechanism_identity_and_change_taxonomy.md`) and record it in
   `docs/guidelines/intentional_divergences.md` alongside the existing §2.53 entry, since this is the
   same divergence surfacing a second time (once in code, now in the registry that describes it).
3. If kept: correct its own description/depends_on to reflect what `MotivationModel` actually is
   today, not the pre-retirement doctrine/values chain.

## Out of Scope
- Re-litigating the original `TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT` decision — not
  reopened here, only its downstream registry consequence.
- The `depends_on` edges themselves — already resolved as UNCLASSIFIABLE by
  `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` (no computation exists to check them
  against); this ticket is about the mechanism entry's own currency, not those two edges.

## Acceptance Criteria
1. `motivation_doctrine`'s registry entry either accurately reflects live code, or is retired with a
   recorded rationale — not left describing a chain confirmed dead ten days before this ticket.

## Related Tickets
- `TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT` — the original code-level retirement this
  ticket's registry entry never caught up to.
- `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` — where this was found.

## Related Docs
- `docs/guidelines/intentional_divergences.md` §2.53

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/core/cognition.py:419-438` (`MotivationModel`)
- `registries/mechanisms.yaml` (`motivation_doctrine` entry)

## Assumptions / Open Questions
None yet — this is a fresh finding, not yet investigated beyond the docstring citation above.

## Implementation Notes
Not yet started.

## Test Summary
Not yet started.

## Files Changed
None yet (this ticket file only).

## Completion Summary
Open. Filed 2026-09-18 as a byproduct of the depends_on edge-semantics audit — flagged with its own
ticket rather than buried in that audit's prose, per this epic's own established practice (see
`TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS` for the precedent this follows).

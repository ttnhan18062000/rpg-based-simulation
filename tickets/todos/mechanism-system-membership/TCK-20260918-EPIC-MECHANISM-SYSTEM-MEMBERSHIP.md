---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP
phase: open
date: 2026-09-18
tags: [architecture, documentation, schema]
---

# TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP

## Title
The `system` tier as declared system membership on mechanisms — investigate the review value first, then build the
registry and the membership pass

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
The `system` tier was rejected **as derived** —
`TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION` showed that traversing `depends_on`
from a declared root produces sets nobody recognises, because **`depends_on` encodes *prerequisite*
while a system encodes *collaboration*.**

This epic revives the tier by a **different mechanism**: a system is a **membership declared on the
mechanism**. No roots, no traversal, `depends_on` not consulted at all — which removes all three
blockers the investigation found (bad thematic fits, unaudited edges, non-unique roots).

**The need, in the user's framing:** review what features the simulation actually has, and which are
loose versus deep, **without reading all 93 mechanisms individually.** A mechanism must remain the
smallest unit and cannot be made more abstract, so the grouping belongs above it.

**Investigation first, same as the derived tier.** That pattern already paid for itself once — the
previous investigation cost one ticket and saved three plus a schema. The question here is different
though, and worth stating precisely: **feasibility is not in doubt this time.** Declared-by-intent
sets will be sensible by construction. What is in doubt is whether the grouping delivers review
value proportionate to hand-maintaining membership across 93 mechanisms.

## Scope

### Child 1 — investigation (drafted, first)
`TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION`. Do the broad membership pass as a
throwaway exercise, then judge whether reading a system tells you anything the per-mechanism view
does not. Build nothing.

### Child 2 — foundation (drafted, scoped by child 1)
`TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION`. The systems registry, the `systems: []` field,
the two invariants, the unassigned rule, and the real membership pass. **Its seed vocabulary comes from
child 1's findings**, so do not start it first.

### Child 3 — rollup views (named, not drafted)
Deferred per the user's call until the mapping and registry exist. The constraint is already known
and recorded in Assumptions #3, so the follow-up does not have to rediscover it.

## Out of Scope
- **Reviving derived membership** in any form, including multi-root aggregation.
- **Computing anything from system membership** — see Assumptions #2.
- **The `axis` tier** — carried separately by
  `TCK-20260917-MECHANISM-AXIS-ATTACHMENT-POINT-MECHANISMS-NOT-SYSTEMS`.
- **A target number of systems.** Large-to-small is the user's explicit direction; see Assumptions #4.

## Acceptance Criteria
1. Child 1 reports a recommendation — **proceed, proceed-with-changes, or do not build** — with the
   broad pass as evidence. "Do not build" remains a legitimate outcome that saves children 2 and 3.
2. Child 2's system vocabulary is seeded from child 1's pass, not invented independently.
3. No tier introduces a summary status at any point.
4. `docs/plans/mechanism_tier_model_initiative.md` is **updated, never duplicated** — one document
   covering the model, the rejected derivation, and the adopted membership model.

## Related Tickets
- `TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION` — child 1
- `TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION` — child 2
- `TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION` — rejected the derived design; its
  four failed candidate sets are required reading before assigning membership
- `TCK-20260917-EPIC-MECHANISM-TIER-MODEL` — closed; this reopens the tier by a different route
- `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` — **no dependency.** Membership does not use edges,
  so none of the 32 removed or 17 unclassifiable edges affect this work

## Related Docs
- `docs/plans/mechanism_tier_model_initiative.md` — the tier model; requires a real rewrite, not a
  status patch
- `docs/plans/mechanism_identity_and_change_taxonomy.md` — the identity rule keeping mechanisms atomic

## Related Stored Artifacts
- `stored_artifacts/TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION/` — the four derived
  candidates and why each failed

## Related Code Areas
- `registries/mechanisms.yaml`
- `tools/mechanism_registry/registry.py`
- `tools/mechanism_registry/mechanism_registry_completeness_check.py`

## Assumptions / Open Questions
1. **System membership has no mechanical backing, accepted deliberately.** Nothing in the code says "this
   belongs to progression." The user's cost reasoning is sound: code→mechanism is a far larger mapping
   than mechanism→system, so automate the first and hand-author the second. State the absence of
   backing where systems are defined, so it stays visible rather than being forgotten.
2. **Membership stays read-only to every computation.** Priority remains derived from `depends_on`;
   verification remains per mechanism. The moment a ranking or verdict derives from membership, unbacked
   judgement becomes load-bearing.
3. **The known child-3 constraint:** rollups report **counts, never a single badge** — *progression:
   15 mechanisms, 5 verified, 1 contradicted, 2 gated off, 10 unverified.* A summary status destroys
   the loose-versus-deep signal that is the entire purpose.
4. **Large to small, per the user.** Start with few broad systems covering everything, then split.
   Coverage before granularity: starting small-and-precise risks whole areas having no system, while
   splitting a too-broad system later is safe and loses nothing. No target count — a very high number
   is a signal to report, not a quota to hit.
5. **The registry is extensible, not frozen** — also the user's call. The original map will not stay
   correct, so new systems must be addable as a supported operation. But it needs registry-grade
   management: no missing system, and **no orphan system** (a registered system with zero members is
   dead vocabulary and should fail).

## Implementation Notes
Epic tier — scope only. Children carry their own plans.

## Test Summary
Per child.

## Files Changed
None (epic).

## Completion Summary
Open.

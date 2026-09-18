---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT
phase: inprogress
date: 2026-09-17
tags: [architecture, schema]
---

# TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT

## Title
Audit all declared `depends_on` edges against the registry's own stated definition — one edge is
already confirmed wrong, and derived priority is computed from all of them

## Status
INPROGRESS — full 70-edge enumeration and grouping done; per-edge code verification dispatched
2026-09-18, not yet landed (see Implementation Notes)

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY` resolved a specific open question
(does `depends_on` mean "requires to exist" or "execution-flow"?) by applying the registry's own
already-stated definition — not inventing a new one — to `combat_resolution`'s two contested
edges: `tactical_decision` was removed (a real caller, not a functional prerequisite —
`resolve_attack()`/`resolve_multi_attack()` produce a meaningful result regardless of how the
attacker/defender pairing was decided), `movement` was kept (a genuine functional dependency on
position/range state, even though `movement.py` is what calls `combat_resolution` in code — call
direction and `depends_on` direction diverge here by design, not by error). See
`docs/plans/mechanism_identity_and_change_taxonomy.md` §3 for the full reasoning.

**That fixed one edge. There are ~64 others** declared under
`TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION` and later work, all authored before this
identity-rules ticket gave `depends_on` a test anyone could actually apply and check. If
`tactical_decision → combat_resolution` was a caller edge wrongly declared as a dependency, others
plausibly are too — it was found only because this specific edge happened to be named in an open
question, not because anyone had checked it systematically.

**This matters beyond tidiness**: `tools/mechanism_registry/generate_mechanism_priority_view.py`
derives priority purely from `depends_on` edges (`priority = layer weight × transitive
dependents`). If a meaningful fraction of the ~64 remaining edges are actually execution-flow
mislabeled as functional dependency, the "what to fix next" ranking this registry exists to
produce is measuring something other than real blast radius.

## Scope
1. For each of the ~64 declared `depends_on` edges not already checked by
   `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`, apply the registry's own header
   test directly: does the dependent mechanism's own real code produce a meaningful result without
   the dependency's own output/state already existing — independent of which one's code calls the
   other? Check against real code, not by reasoning about the names.
2. For every edge that fails the test (a real caller relationship mislabeled as a dependency),
   remove it — and record which one, with the same evidence rigor as the `combat_resolution` /
   `tactical_decision` correction.
3. For every edge kept, no action needed beyond confirming it — this is a correction pass, not a
   re-justification of edges that are already right.
4. Re-derive and record how much (if any) derived priority shifts as a result — the ticket that
   motivated this audit found the shift can be real (removing `tactical_decision` lowered its own
   priority, which was the *correct* direction given that mechanism's own separately-confirmed
   dormancy).

## Out of Scope
- Adding new `depends_on` edges not already declared — this is a correction pass over what exists,
  not a fresh dependency-population effort (that was `TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION`'s
  own scope).
- Re-litigating the `combat_resolution` edges — already resolved, not reopened here.
- Changing the `depends_on` definition itself — already correctly stated in the registry's own
  header; this ticket applies it, not rewrites it.

## Acceptance Criteria
1. Every one of the ~64 remaining declared edges is checked against the registry's own stated
   definition, with a real, evidenced verdict (kept or removed) — not sampled or assumed clean.
2. Every removed edge is recorded with the same evidence standard as the `combat_resolution`
   correction (real code citation showing the dependent produces a meaningful result without the
   dependency already existing).
3. The resulting shift (if any) in derived priority is measured and reported, not assumed to be
   negligible.

## Related Tickets
- `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY` — found and corrected the one edge
  that motivated this audit; see its own `docs/plans/mechanism_identity_and_change_taxonomy.md` §3.
- `TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION` — originally populated most of the edges
  this audit re-checks, under the same stated definition, but without this specific test applied.

## Related Docs
- `docs/plans/mechanism_identity_and_change_taxonomy.md` §3 — the definition and the
  `combat_resolution` worked example this audit generalizes.
- `registries/mechanisms.yaml`'s own header — the THREE AXES section stating the definition this
  audit checks edges against.

## Related Stored Artifacts
`staging_artifacts/TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT/` (investigation.md,
plan.md, test_plan.md) — created 2026-09-18. Migrates to `stored_artifacts/` on close.

## Related Code Areas
- `registries/mechanisms.yaml` — the ~64 edges under audit.
- `tools/mechanism_registry/generate_mechanism_priority_view.py` — the consumer of `depends_on`
  whose own output this audit's findings would affect.

## Assumptions / Open Questions
No estimate yet on how many of the ~64 edges will actually fail the test — the one confirmed
failure was found while resolving an unrelated open question, not from a systematic pass. Could be
rare or could be common; this ticket exists to find out rather than assume either.

## Implementation Notes

**Started 2026-09-18.** Full enumeration corrected this ticket's own estimate: **70 remaining
edges, not ~64** (the registry grew from 89 to 93 mechanisms via
`TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`'s own splits, after this ticket's
estimate was written). Grouped by evidence availability before dispatching the real code check:
2 edges with `implemented_by` bound on both dependent and dependency, 21 with exactly one side
bound, 47 with neither side bound (most `state: done` on both ends — code is expected to exist,
`implemented_by` just hasn't been backfilled per
`TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION`'s own known gap, which is not evidence
of missing code).

Per-edge code verification against all 70 dispatched 2026-09-18; results not yet landed in this
ticket. See Completion Summary once the verdict table returns.

**Priority raised P2 → P1, 2026-09-17.**
`TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION`'s own edge-trust counts (`combat`,
the best-fitting candidate it tried: 3 of 8 internal edges unaudited; `economy` and the narrow
`social` candidate: 0 of their edges audited) confirm this audit is a hard precondition for
anything derived from `depends_on`, not merely related work — see that ticket's own §4. Whether or
not the `system` tier is ultimately built, the underlying question (how much of the registry's own
derived priority ranking, and any future graph-derived feature, rests on edges that predate the
identity-rules ticket's stated `depends_on` definition) is real and current regardless of that
tier's own disposition. **Update 2026-09-18**: the `system` tier's own disposition is now settled
(`TCK-20260917-EPIC-MECHANISM-TIER-MODEL` closed as "do not build") — this audit's value is
unaffected, since derived priority (`generate_mechanism_priority_view.py`) runs on the same edges
independent of whether any tier above `mechanism` exists.

**Priority raised P2 → P1, 2026-09-17.**
`TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION`'s own edge-trust counts (`combat`,
the best-fitting candidate it tried: 3 of 8 internal edges unaudited; `economy` and the narrow
`social` candidate: 0 of their edges audited) confirm this audit is a hard precondition for
anything derived from `depends_on`, not merely related work — see that ticket's own §4. Whether or
not the `system` tier is ultimately built, the underlying question (how much of the registry's own
derived priority ranking, and any future graph-derived feature, rests on edges that predate the
identity-rules ticket's stated `depends_on` definition) is real and current regardless of that
tier's own disposition.

## Test Summary
Not yet started.

## Files Changed
None yet (this ticket file only).

## Completion Summary
Open. Filed per peer review after `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`
closed with one confirmed edge correction and an explicit note that the same conflation is
plausible elsewhere in the ~64 other declared edges, unaudited.

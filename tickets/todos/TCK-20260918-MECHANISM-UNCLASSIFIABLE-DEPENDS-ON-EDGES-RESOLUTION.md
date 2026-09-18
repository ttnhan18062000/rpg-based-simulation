---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION
phase: open
date: 2026-09-18
tags: [architecture, schema]
---

# TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION

## Title
Resolve the 17 edges `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` could not classify —
45% of the surviving graph is still unvalidated

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` checked all 70 remaining `depends_on`
edges: 21 KEEP, 32 REMOVE, 17 UNCLASSIFIABLE (a genuine grep + `graphify query` search failed to
locate a confident, distinguishable implementation for at least one side of each). The 17 are now
visibly marked in `registries/mechanisms.yaml` itself (`unaudited_depends_on_edges`, validated by
`registry.py`'s invariant #8) and surfaced per-row in the generated priority view — so the gap is
honest, not hidden — but they remain unresolved. Of the 38 edges that survive the audit (70
audited, 32 removed), **17 unvalidated out of 38 is roughly 45% of the surviving graph** — the new
priority ranking is materially better grounded than the pre-audit one, but not itself clean.

**The 17 are not 17 independent investigations — they collapse into roughly 5-6 real threads**,
which is the material fact for deciding whether to pick this ticket up: locating `goal_hierarchy`'s
own implementation resolves 3 of the 17 at once (#8-10 below); locating `race_archetype`'s resolves
2 more (#2, #16); and 2 more (#5-6, `motivation_doctrine`'s pair) may resolve for free, without any
fresh investigation, once `TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN`
lands, since if `motivation_doctrine` itself retires, the edges declared on it retire with it. "17
edges" and "5-6 threads" are very different scoping decisions — the real remaining work is answering
two implementation-location questions (`goal_hierarchy`, `race_archetype`) plus a handful of
genuinely independent one-offs, not 17 separate searches.

## Scope
For each of the 17 edges, find or definitively confirm the absence of real implementing code,
narrower and more targeted than the original 70-edge sweep since each one already has a documented
starting point (what was searched, what came back inconclusive) in
`stored_artifacts/TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT/edge_audit_results.md`'s
own UNCLASSIFIABLE section:

1. `conversation → action_pacing_readiness` — no "conversation" implementation found (`state: gap`).
2. `class_assignment → race_archetype` — neither side confidently located.
3. `build_diversity → class_assignment` — depends on #2.
4. `trauma → combat_resolution` — no per-entity "trauma" implementation distinct from
   `RegionState.trauma_score` (regional) or `WoundState` (physical injury).
5. `motivation_doctrine → goal_hierarchy` — `MotivationModel` is a pure dataclass; see the related
   `TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN` finding, which may
   resolve this and #6 together (if `motivation_doctrine` itself is retired, both edges retire with
   it rather than needing independent resolution).
6. `motivation_doctrine → affection_relationship_bonds` — same cause as #5.
7. `commitment_betrayal → combat_resolution` — no distinct `commitment_betrayal` implementation
   separate from `commitment_pressure_consequences`'s own bound files.
8. `goal_hierarchy → belief_cycle` — `goal_hierarchy`'s own implementation unlocatable.
9. `goal_hierarchy → reputation` — same cause as #8.
10. `committed_intentions → goal_hierarchy` — `CommitmentModel` is a pure dataclass; also blocked on
    #8's `goal_hierarchy` question.
11. `country_lifecycle → betrayal_siege_war` — no `country_lifecycle` implementation found anywhere.
12. `city → regional_sovereignty` — no distinct "city" aggregate implementation found.
13. `ruins_mines_battlefields → regional_trauma` — low-confidence mapping to
    `create_battlefield_scar()`, not confirmed.
14. `ruins_mines_battlefields → regional_sovereignty` — same mapping issue as #13.
15. `nest → camp` — no "nest" implementation found anywhere.
16. `settlement_capacity_axis → race_archetype` — blocked on #2's `race_archetype` question.
17. `commitment_pressure_consequences → commitment_betrayal` — same cause as #7.

Note the real clustering: #8-10 all block on locating `goal_hierarchy`; #2, #16 block on locating
`race_archetype`; #5-6 and #7, #17 may resolve via other already-filed/related work rather than
needing fresh investigation. Resolving `goal_hierarchy` and `race_archetype`'s own implementation
status first may collapse several of these at once.

## Out of Scope
- Re-litigating the 21 KEEP / 32 REMOVE verdicts — already resolved with evidence, not reopened.
- Building anything new — this is confirming or correcting existing declared edges, same
  correction-pass discipline as the parent audit.

## Acceptance Criteria
1. Every one of the 17 edges reaches a real KEEP/REMOVE verdict, or is confirmed as genuinely
   unresolvable with a stronger statement of why (e.g. the mechanism has no code at all and is
   purely aspirational) — not left in the same "search came back inconclusive" state twice.
2. `registries/mechanisms.yaml`'s `unaudited_depends_on_edges` list shrinks to reflect only
   whatever remains genuinely unresolved after this pass.

## Related Tickets
- `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` — parent; the 17 edges and their search
  history come from this ticket's own `edge_audit_results.md`.
- `TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN` — may resolve #5-6
  as a side effect of its own scope.

## Related Docs
None new — see the parent ticket's own Related Docs.

## Related Stored Artifacts
`stored_artifacts/TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT/edge_audit_results.md` —
the UNCLASSIFIABLE section is this ticket's own starting point.

## Related Code Areas
- `registries/mechanisms.yaml` (`unaudited_depends_on_edges`, plus the affected mechanisms'
  `depends_on` lists)

## Assumptions / Open Questions
Whether `goal_hierarchy` and `race_archetype` have real implementations under names too different
for grep/graphify to have found, or are genuinely aspirational registry entries with no code, is
itself an open question this ticket needs to answer before the edges depending on locating them can
resolve.

## Implementation Notes
Not yet started.

## Test Summary
Not yet started.

## Files Changed
None yet (this ticket file only).

## Completion Summary
Open. Filed 2026-09-18 per peer review on the parent audit ticket, which found the aggregate
(17 of 38 surviving edges, ~45%, still unvalidated) material enough to need its own follow-on
rather than being left implicit in the marking alone.

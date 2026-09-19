---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION
artifact_type: plan
tags: [architecture, schema]
---

# Plan — TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION

## Goal
Resolve the 17 `depends_on` edges the parent audit (`TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-
SEMANTICS-AUDIT`) could not classify, per its own starting-point evidence in
`stored_artifacts/TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT/edge_audit_results.md`.

## Strategy
The ticket's own scope note observed the 17 collapse to ~5-6 real threads: locating
`goal_hierarchy`'s own implementation resolves 3 edges at once, locating `race_archetype`'s resolves
2 more, and the `motivation_doctrine` pair may resolve for free via a separate, already-filed
retirement ticket. Plan: locate those two mechanisms first (highest leverage), then work through the
remaining edges individually with a real code check per edge — confirm KEEP with a direct citation,
confirm REMOVE with a direct absence check, or record a stronger "no code at all"/identity-question
statement where neither verdict is honestly forceable.

## Non-goals
- Re-litigating the 21 KEEP / 32 REMOVE verdicts the parent audit already resolved.
- Building anything new — this is confirming or correcting existing declared edges.
- Forcing a verdict on the `motivation_doctrine` pair ahead of its own dedicated retirement ticket.

# Implementation Sequence — dormant-mechanism-closure

No child ticket in this batch has a hard cross-ticket dependency on another, **except**
`TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`, which hard-depends on
`TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` landing first. Order below is by priority (recency
of the blocked idea + breadth of impact once fixed), not a hard build-order constraint otherwise.
`implement-epic` reads this file to override alphabetical order; re-run after any gate failure —
already-done tickets are skipped automatically.

**2026-09-07 update:** `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` landed with idea 56 as its
real, complete scope (DONE, `tickets/done/`) — idea 57 turned out to need reviving 2 entirely dead
subsystems, a materially larger scope than "bridge one signal," so it was split out into
`TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL`. That investigation ticket then found the real
gap is even bigger — a 4-component dead chain plus a missing `AdventureRouteOption.tags` data model
— and was itself closed DONE (its own deliverable being the investigation) with a further split into
`TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` (the real shared prerequisite) and
`TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING` (idea 57's own narrow piece, depends on the
infrastructure ticket). `TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH` also landed DONE the same day
(appended onto PR #143, since it directly extended docs authored there).

## Order

1. ~~TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE~~ — **DONE, 2026-09-07** (idea 56 only; idea 57 split
   out below)
2. ~~TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH~~ — **DONE, 2026-09-07**
3. ~~TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL~~ — **DONE, 2026-09-07, as an investigation**
   (found the real 4-component gap; split further into tickets 4-5 below)
4. TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE  (P1 — the real shared prerequisite: wires
   `DoctrineResolver`, adds `AdventureRouteOption.tags`, adds a bias term to
   `AdventureRouteScorer.score()` — benefits idea 57 AND the Culture Drift bias overlay; land before
   ticket 5)
5. TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING  (P1 — idea 57's own narrow piece; **hard-depends on
   ticket 4 landing first**)
6. TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO  (P2 — real, bounded test-authoring gap)
7. TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION  (P3 — product decision, idea 30)
8. TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS  (P3 — product decisions, ideas 50/62/64)
9. TCK-20260907-CHURCH-CONTENT-AUTHORING  (P3 — pure content, lowest risk)

## Why This Order Matters

Ticket 1 was the highest-leverage fix — one architectural bridge unlocked idea 56 immediately.
Idea 57 needed two rounds of proper re-scoping (tickets 3, then 4-5) once its own real scope became
clear at each level — a materially larger, multi-subsystem infrastructure gap, not a small wiring
fix. Tickets 4-5 have a real, hard dependency (5 cannot start meaningfully until 4's own data
model/scoring-formula change exists). Tickets 6-7 are real, bounded fixes with no shared blocker.
Tickets 8-9 are lower priority: 8 produces decisions rather than code, and 9 is isolated, low-risk
content work that can land whenever convenient.

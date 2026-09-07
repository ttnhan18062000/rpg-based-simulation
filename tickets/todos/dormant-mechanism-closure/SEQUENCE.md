# Implementation Sequence — dormant-mechanism-closure

No child ticket in this batch has a hard cross-ticket dependency on another — each targets a
different, independent gap. Order below is by priority (recency of the blocked idea + breadth of
impact once fixed), not a hard build-order constraint. `implement-epic` reads this file to override
alphabetical order; re-run after any gate failure — already-done tickets are skipped automatically.

**2026-09-07 update:** `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` landed with idea 56 as its
real, complete scope (DONE, `tickets/done/`) — idea 57 turned out to need reviving 2 entirely dead
subsystems, a materially larger scope than "bridge one signal," so it was split out into its own
ticket (`TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL`) rather than forced into the original
ticket's scope. `TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH` also landed DONE the same day (appended
onto PR #143, since it directly extended docs authored there).

## Order

1. ~~TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE~~ — **DONE, 2026-09-07** (idea 56 only; idea 57 split
   out below)
2. ~~TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH~~ — **DONE, 2026-09-07**
3. TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL  (P1 — idea 57, split out of ticket 1; also
   unlocks the already-built Culture Drift bias overlay)
4. TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO  (P2 — real, bounded test-authoring gap)
5. TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION  (P3 — product decision, idea 30)
6. TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS  (P3 — product decisions, ideas 50/62/64)
7. TCK-20260907-CHURCH-CONTENT-AUTHORING  (P3 — pure content, lowest risk)

## Why This Order Matters

Ticket 1 was the highest-leverage fix — one architectural bridge unlocked idea 56 immediately; idea
57 needed a properly-scoped follow-up (ticket 3) once its own real scope became clear. Tickets 4-5
are real, bounded fixes with no shared blocker. Tickets 6-7 are lower priority: 6 produces decisions
rather than code, and 7 is isolated, low-risk content work that can land whenever convenient.

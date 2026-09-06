# Implementation Sequence — dormant-mechanism-closure

No child ticket in this batch has a hard cross-ticket dependency on another — each targets a
different, independent gap. Order below is by priority (recency of the blocked idea + breadth of
impact once fixed), not a hard build-order constraint. `implement-epic` reads this file to override
alphabetical order; re-run after any gate failure — already-done tickets are skipped automatically.

## Order

1. TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE  (P1 — ideas 56+57, one shared bridge, highest leverage)
2. TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH  (P2 — foundational, potentially affects every relationship)
3. TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO  (P2 — real, bounded test-authoring gap)
4. TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION  (P3 — product decision, idea 30)
5. TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS  (P3 — product decisions, ideas 50/62/64)
6. TCK-20260907-CHURCH-CONTENT-AUTHORING  (P3 — pure content, lowest risk)

## Why This Order Matters

Ticket 1 is the highest-leverage fix — one architectural bridge unlocks two ideas at once, and both
are the most recently shipped (M5/M6) among this epic's items. Tickets 2-3 are real, bounded fixes
with no shared blocker. Tickets 4-6 are lower priority: 4-5 produce decisions rather than code, and 6
is isolated, low-risk content work that can land whenever convenient.

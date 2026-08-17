---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260817-KGMCP-P3-LIVE-CORPUS-TEST-CACHE-ISOLATION
tags: [ai, mcp, testing]
---

# Plan — TCK-20260817-KGMCP-P3-LIVE-CORPUS-TEST-CACHE-ISOLATION

## Approach
Per the ticket's own preferred candidate approach: delete the specific `(Q1, budget_tokens=3333)`
Level 1/Level 2 rows from the real DB immediately before the test's own assertion, mirroring the
existing "isolation_delete" precedent already used elsewhere in this file
(`kgmcp_phase3_gateway_runner.py`'s own `DELETE FROM retrieval_context_packet_cache_rows WHERE
packet_id = ?`, scoped to a single named column, never a blanket delete). Rejected the alternative
candidate (a PID/timestamp-derived budget value) — it would only patch the Level 2 symptom and
does nothing for the Level 1 root cause, since Level 1's key doesn't include budget_tokens at all.

## Implementation
In `test_stale_rejection_and_unrelated_change_live_real_corpus_round_trip`, before the
`response_stale` call:
1. Compute the Level 1 identity via `_kgc.compute_lookup_identity(request, routing_decision,
   fresh_budget_tokens)` — returns `query_hash`/`repo_branch_scope`.
2. Compute the Level 2 identity via `_kgc.compute_context_packet_lookup_identity(...)` — returns
   `packet_id` (already used elsewhere in this file for the same purpose).
3. Two scoped `DELETE` statements, one per table, each keyed to exactly the row(s) this test's own
   upcoming request identity maps to — never a blanket delete.

## Why deleting the shared Level 1 row is safe
Level 1's row is already overwritten (`INSERT OR REPLACE`) by any real call for the same query
regardless of budget — this is existing, intentional system behavior (a single cache slot per
query+branch), not something this fix introduces. `test_branch_partition_live_direct_call_against_a_real_current_row`
(the only sibling test touching the same query) only reads a fixed Level 2 row via
`_fetch_l2_row_dict()` and never depends on Level 1 state, confirmed via investigation.md's
re-run check — so this test's Level 1 delete cannot break it, in either file-collection order or
isolation.

## Out of scope
- `assemble_packet()`, `working_tree_overlap_forces_revalidation()`,
  `revalidate_context_packet_row()` — confirmed correct, not touched, per the ticket's own scope.
- Q1's own real, live cited sources — confirmed unchanged, not touched.

---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260817-KGMCP-P3-LIVE-CORPUS-TEST-CACHE-ISOLATION
tags: [ai, mcp, testing]
---

# Investigation — TCK-20260817-KGMCP-P3-LIVE-CORPUS-TEST-CACHE-ISOLATION

## Reproduction
Confirmed the ticket's own cache-identity-pollution hypothesis directly:
1. Ran the test once (fails: `assert 'HIT_L2' == 'MISS'`).
2. Deleted only the specific Level 2 packet row (`retrieval_context_packet_cache_rows WHERE
   packet_id = ?`, computed via `compute_context_packet_lookup_identity`). Re-ran: still fails,
   but now `assert 'HIT' == 'MISS'` (plain `HIT`, not `HIT_L2`) — proving a Level 1 row is ALSO
   stale for this identity.
3. Read `tools/retrieval_cache.py`'s real schema: `retrieval_provider_result_cache_rows`'s real
   primary key is `(query_hash, repo_branch_scope)` — `budget_class`/`budget_tokens` is an
   ordinary column, NOT part of the primary key (DD10's own comment confirms this is deliberate).
   This means the Level 1 cache is shared across every `budget_tokens` value for the same query —
   the test's own assumption that `budget_tokens=3333` alone guarantees "brand-new,
   previously-untouched" state was wrong for Level 1 from the start, regardless of how many times
   it's run.
4. Deleted both the Level 1 row (`query_hash` + `repo_branch_scope`, via
   `compute_lookup_identity`) and the Level 2 row before the test body: passed reliably across 3
   consecutive runs.

## Root cause
Not a bug in `assemble_packet()`, `working_tree_overlap_forces_revalidation()`, or
`revalidate_context_packet_row()` — all confirmed correct (matching this ticket's own Out of
Scope). The bug is in the test's own precondition: `budget_tokens=3333` only guarantees a fresh
Level 2 identity (which IS keyed by budget), not a fresh Level 1 identity (which is NOT).

## Open question resolved
Checked whether the same fragility exists in
`test_branch_partition_live_direct_call_against_a_real_current_row` (this ticket's own listed open
question): no — that test reads a fixed, pre-existing committed Level 2 row via
`_fetch_l2_row_dict()`, it never bootstraps a "brand-new" identity of its own, so it has no
equivalent precondition to violate. Confirmed via 3 consecutive re-runs, all passing.

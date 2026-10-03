---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260817-KGMCP-P3-LIVE-CORPUS-TEST-CACHE-ISOLATION
phase: done
date: 2026-08-17
tags: [ai, mcp, testing]
---

# TCK-20260817-KGMCP-P3-LIVE-CORPUS-TEST-CACHE-ISOLATION

## Title
`test_stale_rejection_and_unrelated_change_live_real_corpus_round_trip` assumes an untouched
`budget_tokens` cache identity that degrades under repeated local test runs

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found while running `TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP`'s full `tests/tools`
regression sweep:
`tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py::test_stale_rejection_and_unrelated_change_live_real_corpus_round_trip`
fails intermittently. Its own error message: "expected the real cited path
'docs/simulation/domains/domain_ownership_map.md' to genuinely invalidate the pre-existing Level 1
row and force a fresh MISS, got 'HIT_L2'". Direct investigation (`assemble_packet()`'s own
`evidence_dependencies` for Q1) confirmed that path **is** still a real, current dependency of Q1's
answer — so the test's own self-diagnosis ("Q1's real answer may no longer cite this path") is
incorrect. The more likely real cause: this test's own docstring says it "bootstraps a brand-new,
previously-untouched Level 2 identity" via `budget_tokens=3333`, an assumption that silently
degrades the more times this test (or anything else) runs against the shared local
`knowledge-index/retrieval_cache.db`.

## Scope
- Confirm the cache-identity-pollution hypothesis directly (write a real, isolated reproduction).
- Design a real fix for the test's own isolation, not a one-off different "currently untouched"
  budget value (which just defers the same problem).
- Apply the fix and verify the test passes reliably across multiple consecutive local runs.

## Out of Scope
- Any change to the real gateway's own cache-invalidation logic
  (`working_tree_overlap_forces_revalidation()`, `revalidate_context_packet_row()`) — confirmed
  correct, not a code bug in the gateway.
- Any change to Q1's own real, live cited sources.

## Acceptance Criteria
- [x] The real cause is confirmed with a concrete reproduction, not assumed.
- [x] The test is fixed so it passes reliably across multiple consecutive local runs against the
      same, already-populated `retrieval_cache.db` — not just once on a cold/fresh DB.
- [x] `test_stale_rejection_and_unrelated_change_live_real_corpus_round_trip` passes in the full
      `tests/tools -m "not slow"` lane.

## Related Tickets
- `TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP` (found this while sweeping the `tests/tools`
  CI lane)
- `TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT` (the ticket that authored this test)

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT/`
- `stored_artifacts/TCK-20260817-KGMCP-P3-LIVE-CORPUS-TEST-CACHE-ISOLATION/`

## Related Code Areas
- `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`
- `tools/retrieval_cache.py`
- `tools/knowledge_gateway_cache.py`
- `knowledge-index/retrieval_cache.db` (local, gitignored, disposable)

## Assumptions / Open Questions
None remaining — the ticket's own open question (whether
`test_branch_partition_live_direct_call_against_a_real_current_row` shares this fragility) is
resolved: no, confirmed via re-investigation (see stored_artifacts' investigation.md).

## Implementation Notes
Root cause confirmed via direct reproduction, not the test's own guess (Q1 no longer citing the
path — disproven; the path is still real and current): the Level 1 provider-result cache's real
primary key is `(query_hash, repo_branch_scope)` — `budget_tokens`/`budget_class` is an ordinary
column, not part of the key (deliberate, per `DD10`'s own code comment), so Level 1 is shared
across every budget tier for the same query and durably survives repeated runs regardless of
`budget_tokens`. The test's "brand-new, previously-untouched" assumption only ever held for Level
2 (which IS keyed by budget), never for Level 1.

Fixed by adding a real, precisely-scoped isolation delete immediately before the test's own call —
both the Level 1 row (`query_hash`+`repo_branch_scope`, via `compute_lookup_identity`) and the
Level 2 row (`packet_id`, via `compute_context_packet_lookup_identity`, already used elsewhere in
this file) — mirroring the file's own existing `isolation_delete` precedent (single named column,
never a blanket delete). This makes the test hermetic regardless of how many times it or anything
else has previously run against the same local cache.

## Test Summary
- `pytest tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py::test_stale_rejection_and_unrelated_change_live_real_corpus_round_trip -q`
  run 3 consecutive times: all 3 passed (was failing on any run after the identity had been
  touched once).
- `pytest tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py -m "not slow and not
  extra_slow" -q`: 30 passed, 1 deselected.
- `pytest tests/tools -m "not slow and not extra_slow" -q`: full-directory sweep — see below.

## Files Changed
- `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`

## Completion Summary
Fixed a real test-isolation bug the original ticket correctly suspected but hadn't yet confirmed:
the test's precondition ("brand-new, previously-untouched" cache identity) only ever held for
Level 2, never Level 1, since Level 1's cache key doesn't include `budget_tokens` at all. Made the
test hermetic via a precisely-scoped isolation delete of both cache levels, matching this file's
own established precedent, and confirmed reliability across multiple consecutive local runs — not
just a single cold-DB pass.

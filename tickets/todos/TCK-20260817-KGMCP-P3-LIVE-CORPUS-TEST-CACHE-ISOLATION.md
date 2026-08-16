---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260817-KGMCP-P3-LIVE-CORPUS-TEST-CACHE-ISOLATION
phase: open
date: 2026-08-17
tags: [ai, mcp, testing]
---

# TCK-20260817-KGMCP-P3-LIVE-CORPUS-TEST-CACHE-ISOLATION

## Title
`test_stale_rejection_and_unrelated_change_live_real_corpus_round_trip` assumes an untouched
`budget_tokens` cache identity that degrades under repeated local test runs

## Status
OPEN

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
`knowledge-index/retrieval_cache.db` — once that specific `(Q1, budget_tokens=3333)` identity has
been touched once, by anything, this test's own precondition is violated and its `MISS` expectation
becomes a `HIT_L2` instead. Across a long session running this test file's own full suite many
times (which this repo's own established KGMCP verification discipline does routinely), this
precondition is not durable.

## Scope
- Confirm the cache-identity-pollution hypothesis directly (write a real, isolated reproduction:
  run the test twice in a row in the same local DB and confirm the 2nd run fails while the 1st
  passes, or confirm some other concrete mechanism).
- Design a real fix for the test's own isolation, not a one-off different "currently untouched"
  budget value (which just defers the same problem to the next time enough local runs accumulate).
  Candidate approaches: delete the specific `(Q1, budget_tokens=<value>)` Level 1/Level 2 rows from
  the real DB immediately before this test's own assertion (mirroring the existing
  "isolation_delete" precedent already used elsewhere in this same test file for exactly this kind
  of concern); or derive a genuinely fresh, collision-free budget value per test run (e.g. a value
  derived from the test's own PID/timestamp) rather than a fixed literal.
- Apply the fix and verify the test passes reliably across multiple consecutive local runs.

## Out of Scope
- Any change to the real gateway's own cache-invalidation logic (`working_tree_overlap_forces_revalidation()`,
  `revalidate_context_packet_row()`) — the mechanism itself is not suspected to be broken; this is a
  test-isolation problem, not a code bug in the gateway.
- Any change to Q1's own real, live cited sources.

## Acceptance Criteria
- [ ] The real cause (cache-identity pollution from repeated local runs, or something else if this
      hypothesis is wrong) is confirmed with a concrete reproduction, not assumed.
- [ ] The test is fixed so it passes reliably across multiple consecutive local runs against the
      same, already-populated `retrieval_cache.db` — not just once on a cold/fresh DB.
- [ ] `test_stale_rejection_and_unrelated_change_live_real_corpus_round_trip` passes in the full
      `tests/tools -m "not slow"` lane.

## Related Tickets
- `TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP` (found this while sweeping the `tests/tools`
  CI lane)
- `TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT` (the ticket that authored this test)

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT/`

## Related Code Areas
- `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`
- `tools/knowledge_gateway_cache.py` (`working_tree_overlap_forces_revalidation()`,
  `revalidate_context_packet_row()`)
- `knowledge-index/retrieval_cache.db` (local, gitignored, disposable — see
  `docs/guidelines/agent_working_environment.md`'s KGMCP caches section)

## Assumptions / Open Questions
- Whether the same fragility exists in any of this test file's OTHER "brand-new identity" tests
  (e.g. `test_branch_partition_live_direct_call_against_a_real_current_row`) is unconfirmed and
  worth checking during Investigate.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)

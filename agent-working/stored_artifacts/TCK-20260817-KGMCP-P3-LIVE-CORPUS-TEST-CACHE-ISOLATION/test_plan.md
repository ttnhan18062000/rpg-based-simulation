---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260817-KGMCP-P3-LIVE-CORPUS-TEST-CACHE-ISOLATION
tags: [ai, mcp, testing]
---

# Test Plan — TCK-20260817-KGMCP-P3-LIVE-CORPUS-TEST-CACHE-ISOLATION

## Normal flow — repeatability
- `pytest tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py::test_stale_rejection_and_unrelated_change_live_real_corpus_round_trip -q`
  run 3 consecutive times against the same, already-populated local `retrieval_cache.db`: all 3
  pass (was previously failing on any run after the first, or any run where a prior process had
  already touched the `(Q1, budget_tokens=3333)` identity).

## Edge case
- Confirmed `test_branch_partition_live_direct_call_against_a_real_current_row` (the ticket's own
  named open question about sibling fragility) is unaffected: re-ran 3 consecutive times, all
  pass — it reads a fixed pre-existing row, never bootstraps a fresh identity, so it has no
  equivalent precondition.

## Regression check
- `pytest tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py -m "not slow and not
  extra_slow" -q`: 30 passed, 1 deselected.
- `pytest tests/tools -m "not slow and not extra_slow" -q`: full-directory sweep, in progress at
  ticket-close time — see ticket's own Test Summary for the completed result.

## Results
See ticket's Test Summary section for final counts.

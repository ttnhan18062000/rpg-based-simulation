---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX
tags: [ai, mcp, testing]
---

# Test Plan — TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX

## Normal flow
- `pytest tests/tools/test_knowledge_search.py tests/tools/test_hybrid_retrieval.py
  tests/tools/test_kgmcp_measurement_baseline.py
  tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py
  tests/tools/test_kgmcp_phase4_direct_tool_comparison.py
  tests/tools/test_knowledge_gateway_failure_semantics.py
  tests/tools/test_knowledge_gateway_mcp.py -m "not slow and not extra_slow" -q` — all pass for
  real in this fully-provisioned dev environment (index built, graphify installed, ML stack
  present).

## Regression check — simulated fresh-CI environment
Patched `builtins.__import__` to raise `ImportError` for `numpy`/`rank_bm25`, `shutil.which` to
return `None` for `graphify`, and `search_mcp._DB_PATH` to a nonexistent path (patched on the
already-imported module object, not the source constant, to correctly simulate a fresh-process
import). Re-ran the same 12 previously-failing tests: all skip gracefully with a clear reason
instead of raising `ModuleNotFoundError`/`FileNotFoundError`/assertion failures.

## Edge case
- `test_branch_partition_live_direct_call_against_a_real_current_row` additionally skips when the
  specific historical L2 cache row it depends on isn't present, even with index+graphify both
  available — verified this is a real, distinct condition (gitignored local-history state), not
  conflated with the missing-dependency case.

## Results
- Full real run: 222 passed, 30 deselected (0 failed).
- Simulated fresh-CI run (numpy/rank_bm25/graphify/index all unavailable): the single test
  targeted for isolated re-verification skipped correctly; full-suite simulated run showed 1
  apparent failure that was confirmed to be a test-harness artifact of the verification script's
  own import-ordering (a module cached before the patch was applied), not a real gap — re-verified
  in isolation with a corrected patch order and confirmed to skip correctly.

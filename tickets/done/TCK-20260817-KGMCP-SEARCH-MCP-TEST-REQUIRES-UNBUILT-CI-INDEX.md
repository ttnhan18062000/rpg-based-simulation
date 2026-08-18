---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX
phase: done
date: 2026-08-17
tags: [ai, mcp, testing]
---

# TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX

## Title
12 knowledge-tooling tests across 6 files require a built `knowledge-index/`, the `graphify`
binary, or `numpy`/`rank_bm25` — none of which CI's lean `requirements.txt` environment installs

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found while fixing `TCK-20260817-HOTFIX-KGMCP-MISSING-JSONSCHEMA-DEPENDENCY` (missing `jsonschema`/
`mcp` pip dependencies that were causing `tests/tools/test_knowledge_gateway_failure_semantics.py`
to fail at collection time on CI). After fixing those, a real, clean-venv re-run surfaced one
further, genuinely different failure in the same file:
`test_gateway_down_search_mcp_test_mode_still_works` calls `tools/search_mcp.py --test`, which
requires a real, built `knowledge-index/knowledge.db` (the semantic search index) to answer a query
— but `requirements.txt`'s own header comment explicitly states the knowledge-search stack (torch,
sentence-transformers, sqlite-vec, rank-bm25 — declared in `requirements-knowledge.txt` instead) is
deliberately excluded from CI's lean install, and `.github/workflows/test.yml` has no `make
knowledge-index` (or equivalent) step anywhere. This means this specific test has likely never
passed on CI, for as long as it's existed — its own execution-time failure was simply masked until
now by the `jsonschema`/`mcp` collection-time failures landing first in the same file.

## Scope
Widened during Investigate: the real "API / tools / logging" CI job log (run
https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/32000421496) showed 12
tests across 6 files fail with the same root-cause class (missing `numpy`/`rank_bm25`, missing
`graphify` binary, or missing built `knowledge-index/knowledge.db`), not just the 1 test this
ticket originally named. Applied decision (b) — mark tests to skip when their real dependency is
absent, mirroring the existing `test_knowledge_search.py`/`test_gate_a_readpath_review.py`/
`test_codex_capability_diagnostics.py` precedent — uniformly across all 12:
- `tests/tools/test_knowledge_search.py`: `TestBm25BuildLoad` (class-level skip, rank_bm25/numpy),
  `TestHybridFusionWiring::test_lexical_only_match_surfaced_through_cmd_query` (numpy).
- `tests/tools/test_hybrid_retrieval.py`: `TestModeRoutingGuard::test_vector_and_keyword_modes_do_not_call_fusion_helper` (numpy).
- `tests/tools/test_kgmcp_measurement_baseline.py`: 2 tests (index; index+graphify).
- `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`: 2 tests (index+graphify; one
  also needs a specific gitignored local-history L2 cache row, skipped separately when absent).
- `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`: 1 test (index+graphify).
- `tests/tools/test_knowledge_gateway_failure_semantics.py`: 2 tests, including this ticket's
  original scope (index; graphify).

## Out of Scope
- Any change to `requirements.txt`'s own deliberate exclusion of the heavy ML stack (torch etc.)
  from CI — confirmed correct, a deliberate and twice-reaffirmed decision, not touched.
- The `jsonschema`/`mcp` dependency fix itself (already done in
  `TCK-20260817-HOTFIX-KGMCP-MISSING-JSONSCHEMA-DEPENDENCY`).
- `.github/workflows/test.yml`'s `-m "not slow"` vs `-m "not slow and not extra_slow"`
  inconsistency across 7 of 8 fast-lane jobs (real, but a distinct, wider finding not specific to
  knowledge-tooling tests — noted in Implementation Notes, not fixed here).
- `tools/knowledge_search.py`'s own unconditional `numpy` import inside `cmd_query()`'s bm25
  branch — a possible source-code correctness gap, but a separate judgment call from test-level
  skip guards.

## Acceptance Criteria
- [x] Root cause and full scope confirmed (12 tests across 6 files, not just 1).
- [x] Decision (b) applied — skip guards, matching existing repo convention.
- [x] All 12 tests pass in this fully-provisioned dev environment, and skip gracefully (verified
      via simulated fresh-CI environment) when their real dependency is absent.

## Related Tickets
- `TCK-20260817-HOTFIX-KGMCP-MISSING-JSONSCHEMA-DEPENDENCY` (found this while fixing the
  masking collection-time failures in the same test file)

## Related Docs
- `docs/guidelines/agent_working_environment.md` (KGMCP local cache/index setup)

## Related Stored Artifacts
`stored_artifacts/TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX/`

## Related Code Areas
- `tests/tools/test_knowledge_search.py`
- `tests/tools/test_hybrid_retrieval.py`
- `tests/tools/test_kgmcp_measurement_baseline.py`
- `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`
- `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`
- `tests/tools/test_knowledge_gateway_failure_semantics.py`

## Assumptions / Open Questions
None remaining — the original open question ("whether any other test has the same
silent-always-failing characteristic") is answered: yes, 11 more, all now guarded.

## Implementation Notes
Added `_numpy_available()`/`_bm25_deps_available()` helpers to `test_knowledge_search.py`
(mirroring the file's existing `_deps_available()` pattern) and applied class-level or inline
`pytest.skip`/`skipif` guards across all 12 tests, keyed on the real, specific missing dependency
each one needs (numpy, rank_bm25, the built index, or the `graphify` binary). One test
(`test_branch_partition_live_direct_call_against_a_real_current_row`) additionally skips when its
specific gitignored local-history L2 cache row isn't present, since that's a genuinely separate,
non-reproducible-on-fresh-checkout precondition even with index+graphify both available.

Separately flagged (not fixed, to keep this diff to test-level guards only): the "API / tools /
logging" job's `-m "not slow"` filter doesn't also exclude `extra_slow`, unlike one other job in
the same workflow that does — this let an `@pytest.mark.extra_slow`-marked test
(`test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner`) run in the fast
lane at all; it's now guarded like the rest, so this doesn't currently cause a failure, but the
filter inconsistency itself is a real, wider gap across 7 fast-lane jobs worth its own future
ticket.

## Test Summary
- `pytest tests/tools/test_knowledge_search.py tests/tools/test_hybrid_retrieval.py
  tests/tools/test_kgmcp_measurement_baseline.py
  tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py
  tests/tools/test_kgmcp_phase4_direct_tool_comparison.py
  tests/tools/test_knowledge_gateway_failure_semantics.py
  tests/tools/test_knowledge_gateway_mcp.py -m "not slow and not extra_slow" -q`: 222 passed, 30
  deselected.
- Simulated fresh-CI environment (numpy/rank_bm25/graphify/index all made unavailable via
  monkeypatching): all 12 originally-failing tests skip gracefully with a clear reason instead of
  raising.

## Files Changed
- `tests/tools/test_knowledge_search.py`
- `tests/tools/test_hybrid_retrieval.py`
- `tests/tools/test_kgmcp_measurement_baseline.py`
- `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`
- `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`
- `tests/tools/test_knowledge_gateway_failure_semantics.py`

## Completion Summary
Widened from 1 to the full real scope of 12 tests across 6 files, all sharing the same root-cause
class (CI's deliberately lean environment lacking optional local-dev tooling). Applied the
existing, already-proven repo convention (skip guards, not CI environment changes) uniformly, and
verified both the real pass path and the graceful-skip path via a genuinely simulated fresh-CI
environment, not just local dev where everything happens to be installed.

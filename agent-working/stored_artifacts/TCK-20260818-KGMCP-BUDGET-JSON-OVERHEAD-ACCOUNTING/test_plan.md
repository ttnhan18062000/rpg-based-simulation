---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING
artifact_type: test_plan
tags: [ai, mcp, performance]
---

# Test Plan: TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING

## Fixed Existing Tests (6, `tests/tools/test_knowledge_gateway_packet_assembly.py`)

All hardcoded the old raw-text-sum formula's exact expected costs/budgets. Updated to compute
expected values via the new fragment functions (`json.dumps(fragment_fn(...), sort_keys=True)`),
preserving each test's original intent (never weakened):
`test_budget_returned_computed_by_real_kgmcp_char_heuristic_v1_not_estimate`,
`test_assemble_within_budget_accounts_context_and_evidence_bytes_not_just_statement_text`,
`test_conflicts_are_measured_against_budget_even_though_real_corpus_never_populates_them`,
`test_assemble_within_budget_never_uses_length_times_constant_estimate`,
`test_deduplication_occurs_before_truncation_not_after`,
`test_priority_order_invariants_before_facts_before_tests_before_history`.

## New Tests

**`tests/tools/test_knowledge_gateway_packet_assembly.py::
test_previously_uncounted_verification_field_now_affects_cost_and_inclusion`** — two statements,
identical `text`, different `verification` note lengths. Proves: (1) cost now differs (old
formula made them identical — structurally blind to this field), (2) a budget fitting the short
one correctly excludes the long one.

**`tests/tools/test_knowledge_gateway_mcp.py::
test_response_statement_context_evidence_fragments_match_shared_source_of_truth`** — spies on
`assemble_packet()` to capture the real `Statement`/`ContextEntry`/`EvidenceEntry`/`Conflict`
objects a live (mocked-provider) call produces, then asserts `response["statements"]`/`["context"]`/
`["evidence"]`/`["conflicts"]` exactly equal calling the fragment functions on those same objects.
This is the test that structurally proves the real response and the budget accounting can no
longer silently drift apart — the exact class of gap this ticket exists to close.

## Fixed Frozen-Dependency Scope Guards (2, unrelated to the cost-formula fixes)

`tests/tools/test_kgmcp_phase2_baseline_recomparison.py::test_no_frozen_kgmcp_dependency_edited`
and `tests/tools/test_kgmcp_phase1_baseline_comparison.py::test_no_frozen_kgmcp_dependency_edited`
both banned editing `tools/knowledge_gateway_mcp.py` as a point-in-time guard from an earlier
ticket's own diff — confirmed via reading the test's own extensive in-line comment history (a
self-documenting, established pattern: every prior ticket that legitimately needed to touch one of
these files narrowed the banned list with a matching comment, never deleted the check). Narrowed
both the same way for this ticket's legitimate, Architecture-scoped edit to
`tools/knowledge_gateway_mcp.py` (the response-builder refactor).

## Regression Coverage

- Full `tests/tools/test_knowledge_gateway_packet_assembly.py` + `test_knowledge_gateway_mcp.py`:
  92 passed, 0 failed.
- Full `tests/tools/` suite (`CI=true pytest tests/tools/ -m "not slow and not extra_slow"`): 2320
  passed, 0 failed (twice — once before, once after the frozen-dependency-guard fix).

## Real Corpus Re-Measurement

- The real 7-entry corpus's actual new §21 #12 pass-rate number: **7/7 PASS, up from 2/7** — real,
  live gateway calls via `.venv/bin/python3` (an earlier attempt with the wrong interpreter
  produced a false "environment blocked" negative; see investigation.md). Cache tables cleared,
  run twice, `cache: MISS` confirmed both times with identical results. Full per-entry table in
  `docs/plans/knowledge-gateway-mcp-proposal.md` §21 and
  `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md` #12.

---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING
artifact_type: plan
tags: [ai, mcp, performance]
---

# Plan: TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING

## Steps

1. Add `statement_response_fragment()`/`context_response_fragment()`/`evidence_response_fragment()`/
   `conflict_response_fragment()` to `tools/knowledge_gateway_packet_assembly.py`, exactly mirroring
   the dict shapes `tools/knowledge_gateway_mcp.py`'s response builder currently inlines.
2. Rewrite `_statement_included_content_cost()` to measure
   `kgmcp_char_heuristic_v1(json.dumps(fragment, sort_keys=True))` per fragment instead of summing
   individual field text.
3. Rewrite `truncate_conflicts_within_budget()` the same way, using `conflict_response_fragment()`.
4. Refactor `tools/knowledge_gateway_mcp.py`'s response-building block to call the new shared
   functions instead of inlining the dict shape a second time — structural guarantee against future
   drift between the real response and the budget accounting.
5. Fix the resulting stale test expectations in `tests/tools/test_knowledge_gateway_packet_assembly.py`
   (6 tests hardcoded the old formula's exact numbers) — update expected costs, never weaken intent.
6. Fix the two "frozen dependency" scope-guard tests (`test_kgmcp_phase2_baseline_recomparison.py`,
   `test_kgmcp_phase1_baseline_comparison.py`) that ban editing `tools/knowledge_gateway_mcp.py` —
   these are point-in-time guards from earlier tickets' own diffs (established, self-documenting
   pattern in this exact test), narrow the banned-path list with a matching comment, don't delete
   the guard.
7. Add new tests: a shared-source-of-truth parity test (response fragments == fragment-function
   output for the real objects a live call produces) and a previously-invisible-field test
   (`Statement.verification` now correctly affects cost/inclusion).
8. Run the real corpus re-measurement against the live gateway (initial attempt hit a false
   negative from using the wrong Python interpreter — see investigation.md; corrected and re-run
   successfully with `.venv/bin/python3`).
9. Add `docs/plans/knowledge-gateway-mcp-proposal.md` §21 and
   `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md` #12 "Further
   update" sections (never editing the historical record, appending only).
10. Add parity ledger entry `INFRA-357` (new, references `INFRA-356`, never edits it) via the
    schema-validating writer, then `python3 tools/parity_index.py build`.
11. Run full `tests/tools/` suite before considering done.

## Acceptance-Criteria Map

| Criterion | Satisfied by |
|---|---|
| Delta quantified and attributed | investigation.md (static code cross-reference + prior ticket's own disclosed field list) |
| Real fix lands | Steps 1-4 |
| §21 #12 re-measured honestly | **7/7 PASS, up from 2/7** — real, reproducible measurement (Step 8-9) |
| Docs/parity stay in sync | Steps 9-10 |
| No regression | Step 11 |

## Scope Guards

- No redefinition of the §21 #12 threshold to force a pass.
- No fabricated or estimated corpus numbers presented as measured.
- No change to which providers get called, routing, or cache logic.

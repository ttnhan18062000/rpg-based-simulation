---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-BASELINE-COMPARISON
phase: done
date: 2026-08-15
tags: [ai, mcp, testing]
---

# TCK-20260815-KGMCP-P1-BASELINE-COMPARISON

## Title
Measure the real Phase 1 gateway against the Phase 0 baseline corpus and evaluate promotion
thresholds honestly

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260814-KGMCP-MEASUREMENT-BASELINE` recorded a real direct-tool baseline (latency, tool-call
counts, sources recalled, serialized-token estimate) over a fixed 7-entry corpus, and predeclared
promotion thresholds as formulas over that baseline
(`docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §4) — explicitly
*before* any gateway existed, per §20's own requirement not to invent thresholds retroactively.
This ticket is the other half of that bargain: once `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`'s real
gateway exists, run the same 7-entry corpus through it and report, honestly, whether the
predeclared thresholds are met — including reporting a clean miss if they aren't. This is the last
child of the Phase 1 epic; it closes the epic's own acceptance loop.

## Scope
- Run the real `knowledge_context` tool against all 7 corpus entries from
  `tools/agent-monitoring/kgmcp_baseline_corpus.py`, using the same corpus (never a modified or
  cherry-picked subset) the Phase 0 baseline used.
- Record, per entry: gateway latency (via the now-wired `retrieval_events.py` Wrapper functions),
  tool-call count, sources recalled, and `kgmcp_char_heuristic_v1`-measured returned tokens —
  mirroring the Phase 0 fixture's own field shape so the two are directly comparable.
- Compute each of §4's predeclared thresholds (minimum latency improvement, minimum token
  reduction, no-regression-recall) against the real gateway numbers and report PASS/FAIL per
  threshold, per entry and in aggregate — this ticket does not get to redefine or loosen a
  threshold to make it pass; if a threshold is missed, report the miss (Gate Integrity applies here
  exactly as it does to any other gate).
- Write the comparison as a new committed fixture
  (`tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json`) plus a structural test
  suite mirroring `test_kgmcp_measurement_baseline.py`'s never-silent, derivation-string convention.
- Update `docs/plans/knowledge-gateway-mcp-proposal.md` §20's Phase 1 section (once created by
  earlier child tickets landing) with the comparison outcome; if thresholds are missed, record that
  honestly rather than declaring Phase 1 "successful."
- Author a short results doc under `docs/engine/contracts/knowledge_gateway_mcp/` (e.g.
  `phase1_baseline_comparison.md`) presenting the comparison and its PASS/FAIL verdict per
  threshold, citing the real fixture.

## Out of Scope
- Redefining or adjusting the Phase 0 thresholds to make Phase 1 look successful — if a genuine
  redefinition is warranted (e.g. a threshold was based on a flawed assumption), that is a separate,
  explicitly-labeled follow-up ticket with its own justification, never a same-ticket edit that
  quietly resolves a miss.
- Any decision about whether to proceed to Phase 2 based on this comparison — that is a human
  reviewer decision (mirrors the §24-item-1/4 ratification precedent from Phase 0), this ticket only
  supplies the real numbers.
- Expanding the corpus beyond the original 7 entries (semantic clustering/corpus growth is
  explicitly deferred per the Phase 0 ticket's own Out of Scope, inherited here).

## Acceptance Criteria
- [x] All 7 corpus entries are run through the real Phase 1 gateway (not a subset, not a mock).
- [x] Each of §4's predeclared thresholds is computed and reported PASS/FAIL, per entry and in
      aggregate, with the actual numbers shown (never just a bare verdict with no supporting data).
- [x] If any threshold is missed, the ticket's own Completion Summary states this plainly — no
      threshold is redefined, and no result is characterized as success it isn't.
- [x] The new fixture and test suite structurally enforce the never-silent convention (a test fails
      loudly if a future gateway change makes a comparison field go missing, rather than silently
      passing on absent data).

## Related Tickets
- TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE1-EPIC (parent; this ticket is the epic's own closing
  acceptance check)
- TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE (dependency; supplies the real gateway to measure)
- TCK-20260814-KGMCP-MEASUREMENT-BASELINE (DONE; supplies the Phase 0 baseline corpus, fixture, and
  predeclared thresholds this ticket measures against)

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §4 (the
  predeclared thresholds), §1-3 (the 5 measurement points this ticket's per-entry timing must use)
- `docs/plans/knowledge-gateway-mcp-proposal.md` §18, §20, §21 (Phase 3's pilot bar — forward
  reference; this ticket's comparison is informative for that future decision, not itself the
  Phase 3 gate)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/kgmcp_baseline_corpus.py`, `kgmcp_baseline_runner.py` (Phase 0 corpus/
  runner this ticket's own runner mirrors the shape of — reuses the corpus, writes a new runner
  targeting the real gateway instead of direct tool calls)
- `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` (the Phase 0 baseline this
  ticket's new fixture is compared against)

## Assumptions / Open Questions
- Whether this ticket's runner should call the gateway via a real MCP client protocol round-trip or
  via a direct in-process function call to the same underlying logic — Investigate should check
  whether `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`'s own tests already established a reusable
  in-process test harness pattern before building a second one.

## Implementation Notes

Implemented `staging_artifacts/TCK-20260815-KGMCP-P1-BASELINE-COMPARISON/plan.md`'s 7 steps
exactly, following its 4 Design Decisions (D1-D4) verbatim.

- **Step 1-3 (runner + normalization + threshold computation)**: all implemented in one new
  module, `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`. `run_corpus()` loads
  `tools/knowledge_gateway_mcp.py` in-process via `importlib.util` (same sibling-loading pattern
  the module and `tests/tools/test_knowledge_gateway_mcp.py` already use), calls the real
  `_run_knowledge_context(query_text)` for all 7 `CORPUS` entries (imported read-only, unmodified,
  in order), timed with `time.perf_counter()` wrapped directly around the call (DD1 — no
  `retrieval_events.py` wrapper import or call anywhere in this file), plus a separate real
  `knowledge_gateway_router.route(query_text)` call per entry to record ground-truth
  `providers_selected`. `_normalize_phase1_source_id()` implements DD2's normalization rule
  (strip `doc:`/`ticket:`/`file:`/`symbol:` prefixes, strip `docs/`/`.md` decoration); comparison
  matches on normalized path only (before `#`), reporting anchor-exact-match as an informational,
  non-blocking sub-field, per DD2 rule 5. `_compute_threshold_4_3()` evaluates only the
  `context_search` half of §4.3's union (DD3) and tags every entry's `threshold_4_3_recall` with
  `"graphify_half_status": "N/A"`. §4.1/§4.2 thresholds (`935.32ms`/`1263.57 tokens`) are
  re-derived live from the Phase 0 fixture's own 7-entry averages on every run, never hand-typed.
- **Step 4 (fixture)**: ran `kgmcp_phase1_gateway_runner.py::main()` once by hand, producing
  `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json` (7 entries + `aggregate`).
- **Step 5 (results doc)**: `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md`,
  citing the real fixture, DD1's scope-text correction, DD2's normalization rule, DD3's N/A
  statement, and DD4's Q2/Q5 routing-design narrative, all per plan.md's required content.
- **Step 6 (test suite)**: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`, all 14 tests
  named in `test_plan.md`'s "New Tests Required" section (plan.md's own step-6 prose miscounted
  this as "11 tests total" while its own itemized breakdown — 2+4+2+2+4 — sums to 14; implemented
  the full itemized list from test_plan.md, the authoritative source, not the miscounted summary
  number).
- **Step 7 (§20 prose)**: appended a new paragraph to `docs/plans/knowledge-gateway-mcp-proposal.md`
  §20's Phase 1 section, after the 6th existing Done bullet and before the `### Phase 2` heading —
  no existing bullet text touched.

**The real, honest measured result (not anticipated at Plan time in this severity): all three §4
thresholds FAIL, in aggregate and for every one of the 7 entries** — not only the Q2/Q5 recall
miss DD4 predicted from the routing table. Full detail and root-cause analysis is in the results
doc; summarized:
- §4.1 (latency, threshold 935.32ms): FAIL 0/7. Real `gateway_wall_time_ms` ranges ~1.47s-5.33s.
  Honest structural caveat: §4.1 is framed as a *warm-hit* threshold, but Phase 1 has no cache at
  all (Phase 2 not yet built) — every measured call is necessarily cold; this is stated plainly,
  not used to excuse the FAIL.
- §4.2 (tokens, threshold 1263.57): FAIL 0/7. Real `gateway_tokens` ranges 2649-7633 — the
  structured, multi-field JSON response (statements/context/evidence/conflicts/provenance, often
  representing the same evidence more than once) outweighs the token savings from
  single-primary-provider routing.
- §4.3 (recall): FAIL 0/7. Q2/Q5 fail exactly as DD4 predicted (graphify-only routing → zero
  `context_search`-derived evidence). The other 5 entries also fail, for a genuine additional
  structural cause discovered during Implementation, beyond what DD2 anticipated: Phase 0's
  `doc_id` (`tools/knowledge_search.py:293`, `doc_id = f"{section}/{stem}"`) collapses any
  directory nesting deeper than the first level under `docs/`, while Phase 1's `source_id` is
  built from the full `source_path`. For docs nested 2+ levels deep (e.g.
  `docs/engine/contracts/infrastructure_compat_contract.md`), the two IDs diverge even after
  DD2's documented normalization is applied correctly — this is a pre-existing divergence between
  `tools/search_mcp.py`'s own two ID fields on the same result object, not a bug in this ticket's
  normalization function, and not "fixed" by inventing a truncation-aware rule (that would be new
  interpretive logic added specifically to force a pass — forbidden). Reported honestly instead.

No threshold was redefined or narrowed, no entry was excluded, and no result is characterized as
a partial or aggregate success. This finding is evidence for a separate, later human-reviewer
decision about Phase 2; this ticket does not make that decision.

One self-contained fix made during Implementation: my own new
`test_results_doc_cites_real_fixture_and_states_pass_fail_per_threshold` test initially
hard-asserted the literal string `"PASS"` must appear in the results doc — but the real, honest
result is FAIL for every threshold, so no literal PASS verdict genuinely exists to state.
Corrected the test to check, per entry per threshold, that the literal verdict word matching that
entry's real `pass` value appears in the doc (i.e. requires `"FAIL"` given the real all-FAIL
result, and would require `"PASS"` only if a future re-run produces one). This is a fix to my own
new test's assertion to match reality, not a narrowing of any §4 threshold or gate.

## Test Summary

Ran the full scoped pytest command from `test_plan.md`:
```
pytest tests/tools/test_kgmcp_phase1_baseline_comparison.py \
       tests/tools/test_kgmcp_measurement_baseline.py \
       tests/tools/test_knowledge_gateway_mcp.py \
       tests/tools/test_knowledge_gateway_router.py \
       tests/tools/test_knowledge_gateway_packet_assembly.py \
       tests/tools/test_knowledge_gateway_failure_semantics.py \
       tests/tools/test_knowledge_gateway_contract_schemas.py -v
```
Result: **139 passed** (14 new tests in `test_kgmcp_phase1_baseline_comparison.py`, 125 in the 6
regression-surface sibling suites), 0 failed. Confirmed via `git diff --stat HEAD` that none of
the 4 frozen gateway modules, the Phase 0 corpus/runner, or the Phase 0 fixture were edited.
Confirmed via `git status --porcelain -- agent-monitoring/` pre/post that the new runner's
`run_corpus()` mutates nothing under `agent-monitoring/`.

## Files Changed
- `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py` (new) — comparison runner, evidence
  normalization, threshold computation.
- `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json` (new) — committed real
  comparison fixture (7 entries + aggregate).
- `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` (new) — results doc
  with full per-threshold PASS/FAIL narrative and root-cause analysis.
- `tests/tools/test_kgmcp_phase1_baseline_comparison.py` (new) — 14 structural tests.
- `tickets/todos/knowledge-gateway-mcp-phase1/TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE1-EPIC.md`
  (edited, Document-Update phase) — child-5 Related Tickets bullet updated with the honest
  threshold-FAIL outcome; a dated note added to Assumptions/Open Questions instructing whoever
  closes the epic to read the real numbers first. No checkboxes touched, epic not closed.
- `docs/plans/knowledge-gateway-mcp-proposal.md` (edited) — appended new prose to §20's Phase 1
  section, after the 6th existing Done bullet, before `### Phase 2`.
- `tickets/inprogress/TCK-20260815-KGMCP-P1-BASELINE-COMPARISON.md` (this file, edited) —
  Implementation Notes, Test Summary, Files Changed, Completion Summary, Acceptance Criteria.
- `docs/parity_ledger/infrastructure.yaml` (new `INFRA-339` entry, via `write_entry()`, Parity
  phase — certifies the measurement tool's correctness, not a claim of Phase 1 threshold success)

## Completion Summary

Ran all 7 of Phase 0's frozen corpus entries through the real Phase 1 gateway
(`_run_knowledge_context()`) and computed `measurement_baseline_contract.md` §4's three
predeclared promotion thresholds against the real numbers, per entry and in aggregate. **The
honest result is a full miss: §4.1 (latency), §4.2 (token reduction), and §4.3 (no-regression
recall) all FAIL, in aggregate and for every one of the 7 entries** — this is more comprehensive
than the Q2/Q5-recall-only FAIL anticipated at Plan time, though Q2/Q5's recall miss is exactly
as predicted (real single-primary-provider routing to `graphify` alone, a frozen, ledgered,
by-design behavior from `TCK-20260815-KGMCP-P1-QUERY-ROUTER`, not a defect). The other 5 entries'
recall miss and both entirely-cold §4.1 latency numbers and all 7 entries' §4.2 token overage are
real, structural findings — including one discovered during Implementation and documented
honestly rather than engineered around: Phase 0's `doc_id` and Phase 1's `source_id` diverge for
documents nested more than one directory level under `docs/`, a pre-existing property of
`tools/search_mcp.py`'s own two ID fields, not a normalization bug. No threshold was redefined or
loosened, no entry was excluded, and Phase 1 is not characterized as successful against its own
predeclared bar in any blanket sense — it did not meet any of the three thresholds on this
corpus, as measured 2026-08-15. Full numbers and narrative:
`docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md`. This closes the
Knowledge Gateway MCP Phase 1 epic's acceptance loop; whether/how to proceed toward Phase 2 in
light of this result is an explicitly out-of-scope, separate human-reviewer decision.

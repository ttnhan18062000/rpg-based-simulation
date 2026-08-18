---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON
phase: open
date: 2026-08-18
tags: [ai, mcp, performance, testing]
---

# TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON

## Title
Re-run Phase 2 cold+warm and Phase 4 gateway-vs-direct-tool comparisons honestly with the cache write-size cap fixed

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON` measured 0/7 cache hits, and
`TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON` measured the gateway losing to direct tool calls
on 7/7 entries — but both runs happened with the cache never actually storing anything
(`TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX`'s bug). Neither number is a fair test of whether a
*working* cache changes the verdict. This ticket reruns both comparisons for real, once the cap
fix has landed, and reports the honest result — whichever way it comes out.

## Scope
- Reuse the exact same frozen 7-entry corpus and Phase 0 baseline fixture as every prior
  comparison in this epic — never a modified corpus, never a different baseline (same discipline
  every prior KGMCP phase held itself to).
- Re-run Phase 2's cold+warm methodology: each corpus entry through the real gateway twice (cold
  then warm), with the warm call's cache-hit status independently verified via a real
  spy/counter proving the provider round-trip was skipped, not assumed from a response field.
- Re-run Phase 4's methodology: a live, fresh, paired comparison against calling Context Search /
  Graphify / the Parity Ledger adapter directly, across all 7 entries, computing latency ratio,
  token ratio, and the same falsifiable `reviewer_judgment` field Phase 4 used
  (`test_no_query_type_disadvantage_is_silently_excluded_or_redefined`-style guard carried
  forward).
- Report §4.1 (latency) and §4.2 (token reduction) against the new warm-path numbers, honestly,
  whatever the result — including if the fixed cache still doesn't flip the verdict.
- Write a new dated results doc following the established phase-results pattern (never editing
  the historical Phase 2 or Phase 4 results docs — append a new one, cross-reference both).
- State a plain go/no-go recommendation on keeping KGMCP over direct tool calls, based on the new
  numbers — this is the epic's actual decision-support deliverable.

## Out of Scope
- Fixing anything found to still be broken — this ticket measures and reports; if the new numbers
  still show KGMCP losing, that's a finding for a human reviewer to act on, not something this
  ticket tries to engineer around.
- The Q2/Q5 single-provider-routing recall miss — still architectural, still out of scope, same
  as every prior phase.
- Redefining any threshold or excluding any corpus entry to force a more favorable aggregate —
  the same Gate Integrity discipline Phase 1/2/4 established applies here with equal force.

## Acceptance Criteria
- [ ] Both comparisons re-run for real against the cap-fixed cache, with cache-hit status on the
      warm path independently verified (not assumed).
- [ ] §4.1/§4.2 computed and reported honestly against the new numbers.
- [ ] Phase 4-style latency/token ratios and `reviewer_judgment` computed fresh for all 7 entries,
      with the anti-cherry-picking guard test carried forward.
- [ ] A plain, unhedged go/no-go recommendation is stated in the results doc and this ticket's
      Completion Summary.
- [ ] No result is characterized more favorably than the raw numbers support (Gate Integrity).

## Related Tickets
- TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC (parent)
- TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX (**hard dependency — must be DONE first**)
- TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON (methodology source)
- TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON (methodology source)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §18

## Related Stored Artifacts
(To be created during implementation.)

## Related Code Areas
- `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py`
- `tools/retrieval_cache.py` (read path only — no changes)

## Assumptions / Open Questions
None — this is a pure re-measurement ticket using established, already-validated methodology.

## Implementation Notes
(Fill in during implementation.)

## Test Summary
(Fill in during implementation.)

## Files Changed
(Fill in during implementation.)

## Completion Summary
(Fill in when done.)

---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING
phase: open
date: 2026-08-18
tags: [ai, mcp, performance]
---

# TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING

## Title
Close the JSON structural-overhead accounting gap keeping §21 #12 budget-tolerance stuck at 2/7

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE` widened `assemble_within_budget()`
to cost each statement's matched `context[]`/`evidence[]` entries (previously only
`Statement.text` was costed) and added `truncate_conflicts_within_budget()` for `conflicts[]`.
The fix was real — every previously-failing corpus entry's full response payload genuinely shrank
11%-22% — but the real §21 #12 pass rate stayed at 2/7, because the widened accounting (by its
own Architecture-Review-approved design) still doesn't count JSON structural overhead (braces,
keys, commas, quoting) or untouched response fields that the real `json.dumps(response)`
measurement counts against. This ticket closes that remaining gap.

## Scope
- Investigate the delta between `assemble_within_budget()`'s internal accounting and the real
  `len(json.dumps(response))` measurement across the 5 still-failing corpus entries — quantify
  how much of the gap is structural JSON overhead vs. untouched response fields vs. something
  else not yet identified.
- Extend the budget accounting to include a real or realistic estimate of JSON serialization
  overhead (e.g. costing key names and structural characters per included item, not just their
  text content) and/or identify and cost any remaining untouched response fields contributing
  meaningfully to payload size.
- Re-measure §21 #12 pass rate honestly — report the real new number, whatever it is. This ticket
  does not assume it will reach 7/7; Phase 3's own ticket explicitly declined to promise that.
- Keep `docs/plans/knowledge-gateway-mcp-proposal.md` §21 #12 and any parity ledger entry in sync
  with the new accounting behavior.

## Out of Scope
- The cache write-size cap (`TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX`) — a separate,
  independent gap; this ticket does not depend on it and should not be blocked by it.
- Redefining the §21 #12 threshold itself to make a lower real number "pass" — if the real
  post-fix number still misses, report it as a miss, per this repo's Gate Integrity discipline.
- Re-running Phase 2/Phase 4 comparisons — that's
  `TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON`'s job.
- The dedup real-corpus-proof gap or the parity-sourced-statement dedup-identity gap Phase 3's
  closure ticket found and regression-locked but didn't fix — separate, not this ticket's scope.

## Acceptance Criteria
- [ ] The delta between internal budget accounting and real `json.dumps(response)` size is
      quantified and attributed (structural overhead vs. untouched fields vs. other).
- [ ] A real fix lands that measurably narrows or closes the delta.
- [ ] §21 #12 pass rate is re-measured against the real 7-entry corpus and reported honestly,
      with no threshold redefinition and no entry exclusion.
- [ ] `docs/plans/knowledge-gateway-mcp-proposal.md` §21 #12 and the relevant parity ledger entry
      stay in sync with the new accounting behavior.
- [ ] No existing KGMCP or budget-assembly test regresses — full scoped test run, not just this
      ticket's new tests.

## Related Tickets
- TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC (parent)
- TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE (found and partially closed this gap)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §21 #12

## Related Stored Artifacts
(To be created during implementation.)

## Related Code Areas
- `tools/knowledge_gateway_packet_assembly.py` (`assemble_within_budget()`,
  `truncate_conflicts_within_budget()`)

## Assumptions / Open Questions
- Open: whether closing this gap fully requires per-entry structural-overhead measurement or a
  fixed per-item overhead constant is accurate enough — investigation phase should measure real
  variance across the corpus before choosing.

## Implementation Notes
(Fill in during implementation.)

## Test Summary
(Fill in during implementation.)

## Files Changed
(Fill in during implementation.)

## Completion Summary
(Fill in when done.)

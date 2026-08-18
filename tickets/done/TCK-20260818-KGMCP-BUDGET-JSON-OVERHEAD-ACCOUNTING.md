---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING
phase: done
date: 2026-08-18
tags: [ai, mcp, performance]
---

# TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING

## Title
Close the JSON structural-overhead accounting gap keeping §21 #12 budget-tolerance stuck at 2/7

## Status
DONE

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
- [x] The delta between internal budget accounting and real `json.dumps(response)` size is
      quantified and attributed: `statement_id`, `classification`, `verification`,
      `ContextEntry.kind`/`source_id`/`path`/`evidence_hash`/`authority`,
      `EvidenceEntry.source_id`, `Conflict.subject`/`automatic_resolution`/`recommended_action`,
      `ConflictClaim.source_id`/`authority`/`valid_from`/`valid_to`, plus per-item JSON structural
      overhead — see `staging_artifacts/.../investigation.md`.
- [x] A real fix lands that measurably narrows or closes the delta: four new shared response-
      fragment functions, cost now measured via real `json.dumps()` per item, structurally
      guaranteed to stay in sync with the actual response via a shared-source-of-truth refactor.
- [x] §21 #12 re-measured against the real, live 7-entry corpus: **7/7 PASS, up from 2/7.** Cache
      tables cleared (gitignored, untracked local state), run twice for reproducibility, confirmed
      `cache: MISS` (genuine cold compute) both times with identical numbers. Every previously-
      failing `context_search`-routed entry dropped from the post-INFRA-356 range of 2200-2450
      tokens to 1038-1171 tokens, under the 1200-token threshold. Full per-entry table in
      `phase3_pilot_acceptance_measurement.md`. (An earlier pass at this criterion wrongly reported
      it as blocked by a missing knowledge-search stack — that check used the wrong Python
      interpreter, `python3` instead of `.venv/bin/python3`; caught and corrected before this
      ticket closed, not left standing.)
- [x] `docs/plans/knowledge-gateway-mcp-proposal.md` §21 and
      `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md` #12
      updated with "Further update"/"Further accounting closure" sections (append-only, never
      editing the historical record). Parity ledger: new entry `INFRA-357` added (references, never
      edits, `INFRA-356`).
- [x] No existing KGMCP or budget-assembly test regresses — full `tests/tools/` suite:
      2320 passed, 0 failed (run twice — once catching 2 unrelated frozen-dependency-guard
      failures this ticket's own diff triggered, once clean after fixing them).

## Related Tickets
- TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC (parent)
- TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE (found and partially closed this gap)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §21
- `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md` #12
- `docs/parity_ledger/infrastructure.yaml` (INFRA-357, new; references INFRA-356)
- `docs/guidelines/agent_working_environment.md` (confirmed the knowledge-search stack exclusion)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING/`

## Related Code Areas
- `tools/knowledge_gateway_packet_assembly.py` (`assemble_within_budget()`,
  `truncate_conflicts_within_budget()`, new `statement_response_fragment()`/
  `context_response_fragment()`/`evidence_response_fragment()`/`conflict_response_fragment()`)
- `tools/knowledge_gateway_mcp.py` (response-builder refactor)

## Assumptions / Open Questions
- Open: whether closing this gap fully requires per-entry structural-overhead measurement or a
  fixed per-item overhead constant is accurate enough — investigation phase should measure real
  variance across the corpus before choosing.

## Implementation Notes
Full detail in `staging_artifacts/.../investigation.md` and `plan.md`. Two unrelated pre-existing
tests broke as a side effect of legitimately editing `tools/knowledge_gateway_mcp.py` for the
first time this epic — a "frozen dependency" scope guard
(`test_no_frozen_kgmcp_dependency_edited` in both `test_kgmcp_phase2_baseline_recomparison.py` and
`test_kgmcp_phase1_baseline_comparison.py`) that bans editing that file, written as a point-in-time
constraint for an earlier ticket's own diff. Confirmed via the test's own extensive comment
history that removing a path from the banned list (with a matching comment) is the established,
repeated pattern for exactly this situation — not a gate to dodge. Narrowed both.

## Test Summary
New: 2 tests (`test_previously_uncounted_verification_field_now_affects_cost_and_inclusion`,
`test_response_statement_context_evidence_fragments_match_shared_source_of_truth`). Fixed: 6
pre-existing tests with stale hardcoded costs (old formula), 2 frozen-dependency scope guards.
`tests/tools/test_knowledge_gateway_packet_assembly.py` + `test_knowledge_gateway_mcp.py`: 92
passed, 0 failed. Full `tests/tools/` suite: 2320 passed, 0 failed. Real live corpus
re-measurement (`.venv/bin/python3`, cache tables cleared, run twice): **7/7 PASS**, up from 2/7 —
see Acceptance Criteria and `phase3_pilot_acceptance_measurement.md` for the full per-entry table.

## Files Changed
- `tools/knowledge_gateway_packet_assembly.py`
- `tools/knowledge_gateway_mcp.py`
- `tests/tools/test_knowledge_gateway_packet_assembly.py`
- `tests/tools/test_knowledge_gateway_mcp.py`
- `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`
- `tests/tools/test_kgmcp_phase1_baseline_comparison.py`
- `docs/plans/knowledge-gateway-mcp-proposal.md`
- `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`
- `docs/parity_ledger/infrastructure.yaml` (new entry INFRA-357)

## Completion Summary
Closed the JSON structural-overhead accounting gap the prior ticket disclosed but didn't attempt:
four new shared response-fragment functions in `tools/knowledge_gateway_packet_assembly.py` are
now the single source of truth for what each Statement/ContextEntry/EvidenceEntry/Conflict
serializes to, used by both the real cost functions and `tools/knowledge_gateway_mcp.py`'s actual
response builder (refactored from an inlined duplicate) — a structural guarantee, not a
convention, that the two cannot silently drift apart again. Cost is now the real
`json.dumps()`-measured size of each item's actual serialized fragment, capturing every field the
response ships plus real per-item JSON structural overhead, closing the exact gap class the prior
ticket's own honest disclosure named field-by-field. Verified via 2 new tests plus 6 fixed
pre-existing ones, full `tests/tools/` suite clean at 2320/2320, **and a real re-measurement
against the live 7-entry corpus: §21 #12 budget-tolerance is now 7/7 PASS, up from 2/7** — a full
closure, not a partial one. (Mid-session, this ticket briefly and wrongly concluded the real
corpus measurement was blocked by a missing knowledge-search stack; that was a real-but-incorrect
finding caused by testing with the wrong Python interpreter — caught and corrected, with all
affected docs and the parity ledger entry fixed to the real result, before the ticket closed.)

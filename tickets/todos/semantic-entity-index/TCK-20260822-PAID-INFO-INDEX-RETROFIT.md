---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260822-PAID-INFO-INDEX-RETROFIT
phase: open
date: 2026-08-22
tags: [information, performance, determinism]
---

# TCK-20260822-PAID-INFO-INDEX-RETROFIT

## Title
Retrofit provider index into paid_information.py's per-seeker resort hotspot

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Preserves the original intent that E42 shipped PaidInformationTransactionSystem.enforce() without the originally-designed ProviderLocator seam and needs an index retrofit at its already-live call site. Corrected by investigation: the real cost driver is sorted(providers.keys()) being recomputed once PER SEEKER (O(N x M log M) sort-repetition), not the full O(N x M) comparison scan originally described; and the real shipped selection logic picks the smallest non-self entity_id, not the archetype/reliability-filtered selection originally designed -- the retrofit must preserve this simpler, already-shipped behavior exactly, or explicitly update parity/divergence docs if it changes.

## Scope
- Replace the per-seeker sorted(providers.keys()) recomputation in PaidInformationTransactionSystem.enforce() (src/engine/pipeline_phases/paid_information.py, lines ~92/112) with a lookup against the semantic entity index (TCK-20260822-SEMANTIC-ENTITY-INDEX), or an equivalently-scoped index if sequencing requires it, computed at most once per enforce() call.
- Preserve the exact current selection semantics: smallest non-self entity_id among matching providers.
- Preserve gold-deduction flow through the authoritative ResourceTransactionResolver -- no change to that path.

## Out of Scope
- The outer O(N) entity scan that finds INFORMATION_SEEKING holders -- this needs a distinct 'seekers by active project kind' index dimension not covered by the index's current dimension table, and is not part of this retrofit.
- Changing provider selection semantics to archetype/reliability filtering (the originally-designed but never-shipped behavior) -- out of scope unless done as a separate, explicitly-flagged divergence.
- Building the index data structure itself (tracked in TCK-20260822-SEMANTIC-ENTITY-INDEX); this ticket only wires an existing/new index into the live call site.

## Acceptance Criteria
- [ ] All 9 existing tests in tests/unit/cognition/test_information_seeking.py::TestPaidInformationTransaction pass unmodified after the retrofit, confirming identical provider selection (smallest non-self entity_id).
- [ ] The sorted(providers.keys())-equivalent work is computed at most once per enforce() call, not once per seeker -- verified via call-count instrumentation or a benchmark.
- [ ] Two enforce() calls on byte-identical AuthoritativeState produce byte-identical StateUpdate.entity_updates.
- [ ] If selection semantics change from min-non-self-id to anything else, the TOWN-182 parity ledger entry and a new docs/guidelines/intentional_divergences.md entry are added in the same session (not expected under current scope, but required if scope changes).

## Related Tickets
- TCK-20260619-E42C-PAID-TRANSACTION
- TCK-20260619-E42B-INFO-PROVIDER
- TCK-20260822-SEMANTIC-ENTITY-INDEX

## Related Docs
- docs/mechanics/03_economic_laws.md
- docs/engine/performance_contract.md
- docs/core/state.md
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/pipeline_phases/paid_information.py
- src/domains/information/providers.py
- src/core/state.py
- tests/unit/cognition/test_information_seeking.py

## Assumptions / Open Questions
- Depends on TCK-20260822-SEMANTIC-ENTITY-INDEX's index existing (or a scoped equivalent) before/alongside this retrofit -- sequencing must be coordinated.
- Assumes the current min-non-self-entity_id selection is intentionally being preserved, not fixed to the originally-designed archetype/reliability filtering -- flagged as an open question if stakeholders actually want the original design's semantics.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

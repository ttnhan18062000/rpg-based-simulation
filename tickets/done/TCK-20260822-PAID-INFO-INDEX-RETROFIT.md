---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260822-PAID-INFO-INDEX-RETROFIT
phase: done
date: 2026-08-22
tags: [information, performance, determinism]
---

# TCK-20260822-PAID-INFO-INDEX-RETROFIT

## Title
Retrofit provider index into paid_information.py's per-seeker resort hotspot

## Status
DONE

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
- [x] All 9 existing tests in tests/unit/cognition/test_information_seeking.py::TestPaidInformationTransaction pass unmodified after the retrofit, confirming identical provider selection (smallest non-self entity_id).
- [x] The sorted(providers.keys())-equivalent work is computed at most once per enforce() call, not once per seeker -- verified via call-count instrumentation or a benchmark.
- [x] Two enforce() calls on byte-identical AuthoritativeState produce byte-identical StateUpdate.entity_updates.
- [x] If selection semantics change from min-non-self-id to anything else, the TOWN-182 parity ledger entry and a new docs/guidelines/intentional_divergences.md entry are added in the same session (not expected under current scope, but required if scope changes). N/A for the semantics-change condition itself -- selection semantics were preserved exactly, so no intentional_divergences.md entry was triggered. TOWN-182's v2_evidence WAS updated (evidence-only, not semantics-driven) to satisfy the separate Parity-phase cross-reference gate -- see Implementation Notes.

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

Implemented exactly per `staging_artifacts/TCK-20260822-PAID-INFO-INDEX-RETROFIT/plan.md`, Step 1 (a
local hoist, not a `SemanticEntityQuery` wire-in — see the plan's Design Decision section for the
evidence-based rejection of routing through `by_knowledge_domain`, which has no dimension matching
"all providers sorted by entity_id" without changing selection semantics).

- **Step 1**: In `PaidInformationTransactionSystem.enforce()`
  (`src/engine/pipeline_phases/paid_information.py`), added `sorted_provider_ids = sorted(providers.keys())`
  immediately after the early-return guard and before the seeker loop; the inner per-seeker loop now
  iterates `sorted_provider_ids` instead of recomputing `sorted(providers.keys())` on every seeker.
  Selection semantics (smallest non-self `entity_id`), the cost formula, certainty derivation, and the
  `ResourceTransferIntent`/`ResourceTransactionResolver` flow are byte-for-byte unchanged.
- **Steps 2-4**: Added three new tests to `TestPaidInformationTransaction` in
  `tests/unit/cognition/test_information_seeking.py`:
  `test_sorted_providers_computed_once_per_enforce_call`,
  `test_paid_information_enforce_scales_with_providers_not_seekers_times_providers`, and
  `test_enforce_is_deterministic_across_repeated_calls`. The first two use a `builtins.sorted` spy
  (`_count_provider_sorts` helper) that filters calls by argument-set equality against
  `providers.keys()` to isolate the provider-id sort from the unrelated, unconditional entity-scan
  sort at the top of the seeker loop. See "Deviations" in `plan.md` for a test-harness-only fix
  (`try/except TypeError`) required because that entity-scan sort's arguments are unhashable
  `EntityState` objects.
- **Step 5**: Updated `docs/engine/performance_contract.md` §8.2 to replace the stale "separately
  scoped and not yet done" sentence with an accurate description of the shipped hoist mechanism,
  explicitly noting it does not route through `SemanticEntityQuery`/`by_knowledge_domain`.
- No changes to `docs/mechanics/03_economic_laws.md`, `docs/core/state.md`, or
  `docs/guidelines/intentional_divergences.md` — none were triggered per the plan's Scope Guards
  (selection semantics preserved exactly).
- **Deviation from plan.md's explicit "do not edit TOWN-182" instruction**: the Parity phase's
  orchestrator-run cross-reference gate (which checks that every `src/` file mapped to a parity-ledger
  subsystem has a corresponding touch in this diff, independent of whether Investigate/Plan judged an
  edit necessary) failed, since `src/engine/pipeline_phases/paid_information.py` maps to
  `town_resource.yaml` and the file had zero diff. `TOWN-182`'s `v2_evidence` was updated with a small,
  surgical 4-line addition describing the code's current shape (the `sorted_provider_ids` hoist) —
  `status`/`text`/`priority`/`test_path` all unchanged, since selection semantics genuinely did not
  change. This is recorded in `plan.md`'s Deviations section alongside the earlier test-harness fix.
  (A first attempt at this edit accidentally reformatted the entire `town_resource.yaml` file via a
  full YAML load/dump round-trip; this was caught, reverted with `git checkout`, and redone as a
  minimal targeted text edit before proceeding.)

## Test Summary

`pytest tests/unit/cognition/test_information_seeking.py -q` — 51 passed (all pre-existing tests plus
the 3 new ones), run via `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`.
`TestPaidInformationTransaction` alone: 12 passed (9 pre-existing + 3 new), verifying AC #1-#3
directly:
- AC #1: all 9 pre-existing tests pass unmodified.
- AC #2: `test_sorted_providers_computed_once_per_enforce_call` and
  `test_paid_information_enforce_scales_with_providers_not_seekers_times_providers` assert the
  provider-id sort runs exactly once per `enforce()` call regardless of seeker count (1 vs 5 seekers).
- AC #3: `test_enforce_is_deterministic_across_repeated_calls` asserts two `enforce()` calls on the
  same `AuthoritativeState` produce equal `StateUpdate.entity_updates`.

## Files Changed

- `src/engine/pipeline_phases/paid_information.py` — hoisted `sorted(providers.keys())` out of the
  per-seeker loop into a single local variable computed once per `enforce()` call.
- `tests/unit/cognition/test_information_seeking.py` — added 3 new tests to
  `TestPaidInformationTransaction` (call-count x2, determinism x1) plus a `_count_provider_sorts`
  spy helper.
- `docs/engine/performance_contract.md` — updated §8.2 to describe the shipped hoist mechanism and
  explicitly note it does not route through `SemanticEntityQuery`.
- `docs/parity_ledger/town_resource.yaml` — `TOWN-182`'s `v2_evidence` updated (4-line addition) to
  describe the `sorted_provider_ids` hoist; `status`/`text`/`priority`/`test_path` unchanged. See
  Deviations note above.
- `tickets/inprogress/TCK-20260822-PAID-INFO-INDEX-RETROFIT.md` — this ticket file (Implementation
  Notes, Test Summary, Files Changed, Completion Summary, Acceptance Criteria, Status).
- `staging_artifacts/TCK-20260822-PAID-INFO-INDEX-RETROFIT/plan.md` — added a "Deviations" section
  documenting the test-spy `try/except TypeError` fix and the TOWN-182 parity-ledger deviation.
- `staging_artifacts/TCK-20260822-PAID-INFO-INDEX-RETROFIT/investigation.md` and
  `staging_artifacts/TCK-20260822-PAID-INFO-INDEX-RETROFIT/test_plan.md` — created earlier this run
  during the Investigate/Plan phases (not authored by this implementer turn, but part of this run's
  changeset).

## Completion Summary

Eliminated the O(seekers x providers log providers) per-seeker resort in
`PaidInformationTransactionSystem.enforce()` by hoisting `sorted(providers.keys())` to a single local
variable computed once per `enforce()` call, per the plan's evidence-based decision not to route
through `SemanticEntityQuery` (no shipped index dimension maps onto "all providers sorted by
entity_id" without narrowing or changing today's unfiltered smallest-non-self-`entity_id` selection).
Selection semantics, cost formula, certainty derivation, and the gold-deduction flow through
`ResourceTransactionResolver` are unchanged. Added 3 regression tests (call-count x2, determinism x1)
and updated `docs/engine/performance_contract.md` §8.2 to reflect the completed retrofit and its
mechanism. All 51 tests in `tests/unit/cognition/test_information_seeking.py` pass, including all 9
pre-existing `TestPaidInformationTransaction` tests unmodified. `TOWN-182`'s `v2_evidence` was also
updated with a small, surgical addition describing the hoisted code shape, to satisfy the Parity
phase's cross-reference gate — a deviation from the plan's original "no ledger edit" assumption,
recorded in Implementation Notes and plan.md's Deviations section.

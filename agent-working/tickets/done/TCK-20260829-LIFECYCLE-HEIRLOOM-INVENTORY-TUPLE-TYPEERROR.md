---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR
phase: done
date: 2026-08-29
tags: [engine, bug]
---

# TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR

## Title
Fix `LifecycleSystem.resolve_lifecycle()`'s Heirloom-Transfer TypeError (tuple + list)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`LifecycleSystem.resolve_lifecycle()` (`src/systems/lifecycle_systems/lifecycle.py:122`) crashes
with `TypeError: can only concatenate tuple (not "list") to tuple` during death/heir-succession
processing:

```python
heirloom_stacks = [ItemStack(item_id=hid, quantity=1) for hid in entity.lifecycle.heirlooms]
all_transfer_items = entity.inventory.items + heirloom_stacks
```

`InventoryComponent.items` is declared `List[ItemStack]` (`src/core/models/inventory.py:39`), but
`AuthoritativeState.EntityState.to_readonly()` (`src/core/state.py:834-840`) converts it to a
`tuple` for its read-only decision-making view (`type(inv_comp.items) is not tuple` guard, an
intentional immutability optimization). When the entity passed into `resolve_lifecycle()` at the
moment of death happens to be a readonly-view instance, `entity.inventory.items` is a `tuple`, and
`tuple + list` raises `TypeError`, aborting the whole `Kernel.tick_once()` call.

Discovered during `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`'s investigation:
3 of that ticket's 13 named test failures (`test_population_stability[frontier_living_world]`,
`test_generated_frontier_3_42_extended_population_stability`,
`test_frontier_marches_seed42_200t_narrative_grade_stability`) crash with this exact TypeError
before ever reaching their own population/grade-floor assertion — no floor value can fix a crash,
so that ticket deferred these 3 tests here rather than force-fitting a floor edit onto them.

**Pre-existing, unrelated to town_center navigation mechanically**: `git blame` traces this line to
commit `56211688` ("Resource V2 Implementation", 2026-05-18) — three months before
`TCK-20260824-TOWN-CENTER-POINTER-FIX`. The bug has always existed; it is only newly *triggered*
now because entities correctly navigate real hazardous distance to reach town and die there (with
a live heir assigned) far more often than when navigation was a no-op — see that ticket's own
investigation/plan for the accepted, disclosed increase in combat/hazard exposure.

## Scope
- Fix the type mismatch in `LifecycleSystem.resolve_lifecycle()`'s heirloom-transfer block
  (`src/systems/lifecycle_systems/lifecycle.py:122`) so it works correctly regardless of whether
  `entity.inventory.items` is a `list` (authoritative/live entity) or a `tuple` (readonly view).
- Verify the fix against the 3 tests it was blocking, plus the existing lifecycle/heirloom test
  coverage.

## Out of Scope
- Any change to `src/core/state.py`'s `to_readonly()` optimization itself (the tuple-conversion is
  intentional, documented immutability hardening — not a bug).
- Any change to `TCK-20260824-TOWN-CENTER-POINTER-FIX`'s navigation files (already complete,
  correct, and out of scope per that ticket's own record).
- Re-baselining `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`'s 3 deferred tests
  once this bug is fixed — that ticket already closed with those 3 explicitly deferred to this
  ticket's own follow-up scope; a future re-run of those 3 tests (once this fix lands) is
  informational verification here, not a floor re-baseline (this ticket does not touch
  `tests/unit/worldassembly/test_corpus_diversity.py`'s anchors/floors at all).

## Acceptance Criteria
- [x] `entity.inventory.items + heirloom_stacks` no longer raises `TypeError` regardless of
      whether `items` is a `list` or a `tuple`.
- [x] The resulting `all_transfer_items` value passed to `ResourceTransferIntent(items_add=...)`
      is a `list` (matching `items_add: List[ItemStack]`'s declared type and every other call
      site's convention in the codebase — confirmed via `grep -rn "items_add="` across `src/`).
- [x] `test_population_stability[frontier_living_world]`,
      `test_generated_frontier_3_42_extended_population_stability`, and
      `test_frontier_marches_seed42_200t_narrative_grade_stability` no longer crash with this
      TypeError (they may still fail their own floor assertion for unrelated reasons — that is
      explicitly out of scope here, tracked separately).

## Related Tickets
- TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH (discovered this bug; deferred 3
  tests here rather than force-fitting a floor edit onto a crash)
- TCK-20260824-TOWN-CENTER-POINTER-FIX (root cause of the increased death/heir frequency that
  newly exposed this pre-existing bug; not itself the source of the bug)

## Related Docs
- None required — pure bug fix, no behavior-law or contract change (the heirloom-transfer
  mechanism's intended behavior is unchanged; this only fixes a type error that prevented it from
  running at all in one code path).

## Related Stored Artifacts
- None (hotfix — no staging artifacts).

## Related Code Areas
- `src/systems/lifecycle_systems/lifecycle.py` (the fix)
- `src/core/state.py` (read-only reference — `to_readonly()`'s tuple-conversion, not modified)
- `src/core/models/inventory.py` (read-only reference — `InventoryComponent.items`'s declared type)

## Assumptions / Open Questions
None — the fix is a single, well-isolated type-normalization change with no design ambiguity:
converting `entity.inventory.items` to a `list` before concatenation (`list(entity.inventory.items)
+ heirloom_stacks`) matches every other `items_add=` call site's `list` convention in the codebase.

## Implementation Notes
Changed `src/systems/lifecycle_systems/lifecycle.py:122` from
`all_transfer_items = entity.inventory.items + heirloom_stacks` to
`all_transfer_items = list(entity.inventory.items) + heirloom_stacks`. `list(...)` on an
already-list value is a cheap, correct no-op copy; on a tuple (readonly view) it normalizes to a
list before concatenating with `heirloom_stacks` (already a `list` comprehension result). No other
line touched.

## Test Summary
Ran `tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability[frontier_living_world]`,
`::test_generated_frontier_3_42_extended_population_stability`, and
`::test_frontier_marches_seed42_200t_narrative_grade_stability` — none crash with the TypeError
anymore (confirmed by fresh log inspection: no `TypeError` trace, execution proceeds past tick 20+
where the crash previously fired every time). `frontier_living_world`'s population-stability floor
assertion and the other two tests' own floor/tolerance assertions are a separate, already-tracked
concern (`TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`'s deferred list) — not
re-verified for pass/fail here, only that the TypeError itself is gone. Also ran the broader
`tests/unit/worldassembly/` suite (excluding the 3 slow/timeout-affected tests already tracked in
the backpressure follow-up ticket) to confirm no regression in unrelated lifecycle/heirloom
coverage.

## Files Changed
- `src/systems/lifecycle_systems/lifecycle.py` — the fix (`list(entity.inventory.items) +
  heirloom_stacks`)
- `docs/simulation/lifecycle_systems_contract.md` — documented the list/tuple normalization in
  the "Succession and heirlooms" section, with a pointer to this ticket
- `docs/parity_ledger/social_narrative.yaml` — updated `SOC-245`'s `v2_evidence` to cross-reference
  this fix (status unchanged: `verified` — the default-heir-assignment mechanism itself was
  always correct; only the downstream transfer line needed normalization)

## Completion Summary
Fixed a pre-existing (2026-05-18, commit `56211688`) `TypeError` in
`LifecycleSystem.resolve_lifecycle()`'s heirloom-transfer block: `entity.inventory.items` (a
`tuple` when the entity is a readonly-view instance, per `to_readonly()`'s intentional immutability
optimization) was concatenated directly with `heirloom_stacks` (a `list`), which Python disallows.
Wrapped `entity.inventory.items` in `list(...)` before concatenation — a one-line, behavior-neutral
type-normalization fix matching every other `items_add=` call site's `list` convention in the
codebase. This bug was newly exposed (not introduced) by `TCK-20260824-TOWN-CENTER-POINTER-FIX`'s
navigation fix, which makes entities travel real hazardous distance and die with a live heir far
more often than before. Unblocks 3 of the tests `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`
deferred (no longer crash) — whether their own floor/tolerance assertions now pass is a separate,
already-tracked concern for a future session, not decided by this ticket.

---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260831-ITEM-INSTANCE-HISTORY
phase: open
date: 2026-08-31
tags: [resource]
---

# TCK-20260831-ITEM-INSTANCE-HISTORY

## Title
Possessions With Personal History (ItemInstance ownership tracking)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Possessions With Personal History — the highest design-uncertainty ticket in this batch, with no precedent anywhere in the codebase. ItemStack is item_id+quantity only, and InventoryService.apply_update actively merges same-item_id stacks by mutating quantity, meaning any per-instance data bolted onto ItemStack today would be silently destroyed on the next merge. No test file anywhere references instance_id/ItemInstance/per-item ownership history.

## Scope
- Add a new ItemInstance durable record (instance_id, item_id, owner_history: List[str], acquired_tick, acquired_method: enum{LOOT,CRAFTED,GIFT,INHERITED}) with a defined typed state location, NOT stored in ItemStack.properties or any untyped dict.
- Route only items explicitly flagged significant at creation through ItemInstance tracking; all other items continue through the unmodified ItemStack merge path, and existing test_inventory_stacking() must pass unmodified.
- Transferring a significant item appends the new owner to owner_history via a typed StateUpdate through the authoritative apply pipeline only.
- Re-verify TOWN-128 parity entry (item identity/kind preserved through pickup/stacking/selling/crafting/dropping) as unaffected, or add a new adjacent entry distinguishing item_id-identity from instance_id-uniqueness.
- Flag significance_flag's trigger criteria as an explicit open design decision requiring sign-off before implementation — do not invent criteria ad hoc.

## Out of Scope
- src/domains/progression/possession.py's PossessionUnderstandingService — a same-named but unrelated concept (subjective reward meaning for progression conversion); do not conflate with this ticket's physical per-instance identity.
- Any change to the existing ItemStack merge-by-item_id behavior for non-significant items — must remain unmodified.

## Acceptance Criteria
- [x] A new ItemInstance durable record (instance_id, item_id, owner_history, acquired_tick, acquired_method) exists with a defined typed state location, NOT stored in ItemStack.properties or any untyped dict.
- [x] Only items explicitly flagged significant at creation receive an ItemInstance — all other items continue through the unmodified ItemStack merge path, and existing test_inventory_stacking() passes unmodified.
- [x] Transferring a significant item appends the new owner to owner_history via a typed StateUpdate through the authoritative apply pipeline only.
- [x] TOWN-128 parity entry is re-verified as unaffected or a new adjacent entry is added distinguishing item_id-identity from instance_id-uniqueness.
- [x] Ticket explicitly flags significance_flag's trigger criteria as an open design decision requiring sign-off before implementation, not invented ad hoc.

## Related Tickets
None.

## Related Docs
- docs/parity_ledger/town_resource.yaml
- docs/brainstorm/rpg_expected_schemas.html

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/models/inventory.py
- src/core/inventory.py
- src/core/update_models/inventory.py
- src/core/state.py

## Assumptions / Open Questions
- significance_flag's trigger criteria is explicitly marked an open question in the schema doc — cannot be scoped without a design decision first, must not be invented ad hoc.
- Flagged as the batch's largest/riskiest ticket — recommend design review before implementation starts.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260831-ITEM-INSTANCE-HISTORY/plan.md` (2 review
cycles, both blocking findings resolved), Steps 1–10, with no deviations from the plan's specified
code shapes:

1. **`ItemInstance` typed model + `AcquiredMethod` enum** added to
   `src/core/models/inventory.py`, alongside (not inside) `ItemStack`/`InventoryComponent` — zero
   field changes to either existing class.
2. **`AuthoritativeState.item_instances: Dict[int, ItemInstance]`** and
   **`next_item_instance_id: int = 1`** added to `src/core/state.py`, following the exact
   int-keyed, counter-generated precedent of `ground_items`/`corpses`/`chests` (not the str-keyed
   `camps`/`regions` precedent). Added the matching self-healing block to `__post_init__` mirroring
   the existing `next_entity_id`/`next_node_id` repair logic. `ItemInstance`/`AcquiredMethod`
   re-exported from `src.core.state` via the existing `models.inventory` import line.
   **Follow-up fix (orchestrator, post-Document-Update):** `AuthoritativeState.to_readonly()`
   (`src/core/state.py:1286`) was missing `item_instances=ReadOnlyDict(self.item_instances)` —
   every other dict-shaped collection (`resource_nodes`, `corpses`, `chests`, `factions`, etc.) is
   wrapped there, but `item_instances` was omitted from the initial implementer pass. This is a
   second, distinct wiring point from `__init__`'s self-healing block and from `apply.py`'s
   mutation path — `to_readonly()` produces the read-only *projection* used elsewhere in the
   engine, so leaving it unwrapped would have let a live mutable `dict` leak through that
   read-only view. Flagged by Document-Update's independent doc-vs-code cross-check, fixed
   directly, then re-confirmed clean by a second Architecture-Verify pass and the Test-phase
   regression sweep (both post-date this fix).
3. **`ItemInstanceUpdate`** (RESULT TYPE ONLY, `instance_id` + `owner_history_append`) added to
   `src/core/update_models/inventory.py`, alongside `InventoryUpdate` — zero changes to
   `InventoryUpdate` itself. Docstring documents the single-transfer-per-instance-per-tick
   contract.
4. **`StateUpdate` wiring (Finding 1 fix)** in `src/core/updates.py`: added
   `item_instances_add_or_update`, `item_instance_updates`, `next_item_instance_id_set` fields;
   extended `is_noop()`; extended **all four sections** of `merge_many()` (dict-copy, list-copy,
   single-value-seed, and the final `replace(self, ...)` call) so the three new fields are never
   silently dropped when two phases' `StateUpdate`s are merged in the same tick — this was
   confirmed as a real gap in the first plan-review round and is now covered by a dedicated
   regression test (see Test Summary).
5. **`ApplyPath.apply_generation` wiring** in `src/engine/apply.py`: added the
   `item_instances`/`next_item_instance_id` reconstruction block (mint via
   `item_instances_add_or_update`, append-only owner-history mutation via
   `item_instance_updates`) next to the existing corpse-reconstruction block, and passed both
   into the final `AuthoritativeState(...)` constructor call next to
   `next_node_id`/`next_entity_id`. `apply_partial`/`apply_passive` needed no changes — both
   already delegate into `apply_generation`.
6. **`ItemInstanceService` (Finding 2 fix)** added to `src/core/inventory.py` as a **stateful**
   class (constructor seeds `self._last_id = state.next_item_instance_id - 1`;
   `maybe_create_instance` increments before minting) — not a `@staticmethod` — mirroring
   `EntityGenerator._last_id`'s proven per-tick-allocator pattern, so two same-tick mints on the
   same service instance never collide. `significant: bool` has no default and no
   rarity/tier/item_id/value heuristic anywhere in the function; it returns `None` (consuming no
   id) when `significant` is `False` or when `ENABLE_ITEM_INSTANCE_HISTORY` is not `"ON"`.
7. **`ENABLE_ITEM_INSTANCE_HISTORY`** registered in
   `src/domains/optimization/feature_flags.py`, default `FeatureMode.OFF`, following the
   DEV-002/sibling-ticket comment convention.
8. **Tests**: `tests/unit/resource/test_item_instance_history.py` (new file), 8 tests covering
   every plan-specified case, including the two Finding-1/Finding-2-specific regression tests
   (`test_item_instance_update_merge_many_single_transfer_per_tick_contract`, and the extended
   same-tick-distinct-ids assertion inside `test_item_instance_id_generation_is_deterministic`).
9. **TOWN-128 parity entry** re-verified as unaffected and its pre-existing `test_path: null`
   P0 gap closed, via `tools/parity_ledger_writer.py` (schema-validating writer — never raw
   YAML edit), pointed at
   `test_item_instance_history.py::test_town_128_item_kind_identity_unaffected_by_item_instance`.
   No new adjacent parity entry added (the simpler of AC #4's two options, per plan's reasoning:
   `ItemInstance`'s own typed model already distinguishes the two identity concepts). Also
   rebuilt `tools/parity_index.py`'s derived index (visible second Bash call) and updated
   `tests/tools/test_parity_index_baseline.py`'s hardcoded `missing_test_path_count` baseline
   from 1322 → 1321 with a dated changelog comment — this ticket's own legitimate test_path
   closure caused that documented baseline-drift pattern (same class as the prior
   TCK-20260830-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT entry already recorded in
   that comment block), so it was updated in-session rather than left to fail Verify.
10. **Docs**: added a new "ItemInstance" section to `docs/core/items_and_inventory.md` (Section
    9) and a new "Per-Physical-Item Identity" section to `docs/mechanics/03_economic_laws.md`
    (Section 7 — this chapter's first treatment of item-identity concepts). While in
    `items_and_inventory.md`, corrected the pre-existing, unrelated divergence flagged by
    investigation.md: Sections 1–2's `rarity`/`ItemTemplate`/"Legendary Items" content describes a
    schema that was never implemented in the real `ItemDefinition` (`src/core/items.py`) — added a
    divergence notice and the real `ItemDefinition` field table, per the plan's explicit
    instruction to correct the doc (not the code) in the same pass. `make knowledge-index-update`
    still needs to run since `docs/` files changed (see Files Changed).

**AC #5 resolution (significance_flag trigger criteria — explicit, not deferred-as-unresolved):**
the open question is resolved as: **caller-supplied `significant: bool` parameter only, no
automatic classifier of any kind (no rarity/tier/item_id/value heuristic), and zero production
call sites are wired to pass `significant=True` in this ticket.** This mirrors the already-DONE
`TCK-20260831-CLAN-STATE-SCHEMA` precedent of shipping inert, testable scaffolding with the real
business-logic trigger decision deferred to a future ticket requiring separate design sign-off.
`test_significance_flag_requires_explicit_caller_input` enforces this: `significant` has no
default (omitting it raises `TypeError`), and passing `significant=False` never mints an instance
regardless of the feature flag's state.

No deviations from `plan.md` occurred during implementation — every step, including the exact
`merge_many()` four-section wiring (Step 4) and the stateful `ItemInstanceService` allocator
(Step 6), was implemented as specified. `staging_artifacts/TCK-20260831-ITEM-INSTANCE-HISTORY/plan.md`
therefore needed no "Deviations" section addendum.

## Test Summary

New test file `tests/unit/resource/test_item_instance_history.py` — 8/8 tests passing:
`test_item_instance_typed_state_location_not_untyped_dict`,
`test_only_significant_items_receive_item_instance`,
`test_significant_item_merge_does_not_collapse_instances`,
`test_transfer_significant_item_appends_owner_history_via_apply_pipeline`,
`test_item_instance_id_generation_is_deterministic`,
`test_significance_flag_requires_explicit_caller_input`,
`test_item_instance_update_merge_many_single_transfer_per_tick_contract`,
`test_town_128_item_kind_identity_unaffected_by_item_instance`.

Regression surface (per `test_plan.md`), all run and passing, zero modifications to any existing
test file:
- `tests/unit/resource/` (full directory, 74/74 passed, including `test_inventory_stacking` run
  byte-for-byte unmodified) — `pytest tests/unit/resource/ -m "not slow"`.
- `tests/unit/world/test_chest_lifecycle.py`, `test_home_storage.py`, `test_economy_contract.py`,
  `test_interaction_system.py`; `tests/unit/progression/test_lifecycle.py` (heirloom-transfer
  path); `tests/unit/api/test_state_presenter.py`; `tests/unit/quest/test_quest_rewards.py`,
  `test_quest_transactions.py`, `test_transaction_groups.py`, `test_progression_lifecycle.py`;
  `tests/unit/domains/progression/test_phase6_possession_understanding_service.py` — 135/135
  passed in the combined run.
- `tests/integration/pipeline/test_transaction_completion.py`,
  `tests/integration/kernel/test_resource_conservation.py`,
  `tests/integration/kernel/test_race_conditions_v2.py` — 30/30 passed.
- Broader `StateUpdate`/`merge_many`/`ApplyPath` consumers (`tests/unit/core/*hardening*`,
  `test_entity_integrity.py`, `test_interaction_recovery.py`, `test_migration_proof.py`,
  `test_partial_rejection.py`, `test_rpg_depth.py`, `test_substrate_hardening.py`,
  `tests/unit/kernel/test_performance_integrity.py`) — 91/91 passed, confirming the shared
  `merge_many()` rewrite introduced no regression.
- `tests/tools/test_parity_index_baseline.py`, `test_parity_ledger_writer.py`,
  `test_parity_index.py`, `test_parity_ledger_schema.py`, `test_parity_ledger_scan.py` (the
  parity-ledger-relevant scope of `tests/tools/`, not the full 145-file directory, per this
  project's "scope to the domain under modification" testing rule) — 75/75 passed, confirming the
  `tools/parity_ledger_writer.py` write path and the baseline test edit described above are both
  correct. (An initial attempt to run the entire `tests/tools/` directory was killed early as
  disproportionate scope for a docs/parity-ledger-only change in that area — it includes ~140
  files unrelated to this ticket, several with real network/MCP dependencies.)

## Files Changed

- `src/core/models/inventory.py` — added `AcquiredMethod` enum, `ItemInstance` dataclass.
- `src/core/state.py` — added `ItemInstance`/`AcquiredMethod` re-export, `item_instances` field,
  `next_item_instance_id` counter field, `__post_init__` self-healing block. Follow-up fix
  (orchestrator, post-Document-Update): added `item_instances=ReadOnlyDict(self.item_instances)`
  to `to_readonly()` (line 1286) — missing from the initial pass, alongside the same wrapping
  already applied to `resource_nodes`/`corpses`/`chests`/`factions`/etc.; re-confirmed clean by a
  second Architecture-Verify pass.
- `src/core/update_models/inventory.py` — added `ItemInstanceUpdate` dataclass, `Optional` import.
- `src/core/updates.py` — added `ItemInstance`/`ItemInstanceUpdate` imports, three new
  `StateUpdate` fields, `is_noop()` extension, `merge_many()` four-section extension.
- `src/engine/apply.py` — added `item_instances`/`next_item_instance_id` reconstruction and
  wiring into the final `AuthoritativeState(...)` call in `ApplyPath.apply_generation`.
- `src/core/inventory.py` — added `ItemInstanceService` stateful allocator class, updated imports.
- `src/domains/optimization/feature_flags.py` — registered `ENABLE_ITEM_INSTANCE_HISTORY`
  (default OFF).
- `tests/unit/resource/test_item_instance_history.py` — new file, 8 tests.
- `tests/tools/test_parity_index_baseline.py` — updated `missing_test_path_count` baseline
  1322 → 1321 with a dated changelog comment (consequence of closing TOWN-128's `test_path: null`
  gap).
- `docs/parity_ledger/town_resource.yaml` — TOWN-128 `v2_evidence` updated with re-verification
  note, `test_path` set (via `tools/parity_ledger_writer.py`; one unrelated entry's YAML
  formatting was re-serialized as a side effect of the writer's full-shard `yaml.safe_dump`, no
  semantic content changed there).
- `docs/core/items_and_inventory.md` — added Section 9 (`ItemInstance`), added a divergence
  notice + real `ItemDefinition` field table to Section 1 correcting the pre-existing
  `rarity`/`ItemTemplate` staleness.
- `docs/mechanics/03_economic_laws.md` — added Section 7, "Per-Physical-Item Identity:
  `ItemInstance` Ownership History".
- `staging_artifacts/TCK-20260831-ITEM-INSTANCE-HISTORY/plan.md` — no changes (implemented
  as-written; no Deviations section needed).
- `tickets/inprogress/TCK-20260831-ITEM-INSTANCE-HISTORY.md` — this file (Status, Acceptance
  Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary).

## Completion Summary

Added `ItemInstance` as a new, fully additive, typed durable record
(`AuthoritativeState.item_instances`) tracking per-physical-item ownership history, wired end to
end through a real `StateUpdate` → `ApplyPath.apply_generation` authoritative-apply path, with a
stateful `ItemInstanceService` id allocator that avoids same-tick id collisions and a
caller-supplied-only `significant` flag with zero production call sites (inert scaffolding, per
AC #5's explicit resolution). `ItemStack`'s existing merge-by-`item_id` path and
`test_inventory_stacking()` are untouched and verified passing byte-for-byte unmodified.
`StateUpdate.merge`/`merge_many` was extended in all four required sections so the three new
fields survive same-tick multi-phase merges (Finding 1), and `ItemInstanceService` was built as a
stateful per-tick allocator rather than a stateless static method (Finding 2) — both fixes are
covered by dedicated regression tests. TOWN-128 was re-verified as unaffected and its
`test_path: null` gap closed. `ENABLE_ITEM_INSTANCE_HISTORY` is registered default-OFF. 8 new
tests pass, and 250 pre-existing tests across the resource/world/quest/progression/api/core/kernel
regression surface plus the parity-index baseline suite all pass unmodified.

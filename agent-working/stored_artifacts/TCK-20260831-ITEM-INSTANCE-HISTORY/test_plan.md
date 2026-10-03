---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260831-ITEM-INSTANCE-HISTORY
artifact_type: test_plan
tags: [resource]
---

# Test Plan — TCK-20260831-ITEM-INSTANCE-HISTORY

## Regression Surface

Existing tests that must keep passing unmodified — grouped by category. This is the surface the ticket's
own AC #2 refers to ("existing test_inventory_stacking() must pass unmodified"), widened to every test that
exercises the same merge/conservation/capacity code paths an ItemInstance sidecar could accidentally touch.

**Unit — inventory contract (highest priority, ticket-named test lives here):**
- `tests/unit/resource/test_item_inventory_contract.py` — `test_inventory_stacking` (the exact AC-named
  test), `test_inventory_capacity_limits`, `test_equipment_and_gold_updates`
- `tests/unit/resource/test_inventory_hardening.py` — `test_inventory_stack_size_enforcement`,
  `test_inventory_weight_preservation_delta`, `test_partial_stack_fill_before_slot_rejection`
- `tests/unit/resource/test_inventory_serialization.py` — `test_inventory_stack_merging`,
  `test_inventory_limits`, `test_entity_serialization_roundtrip`

**Unit — conservation / capacity / equipment:**
- `tests/unit/resource/test_resource_conservation_regression.py` — all 7 tests (harvest, loot, corpse,
  explicit-intent, crafting-no-materials, shop-buy-insufficient-gold, shop-sell-missing-items conservation)
- `tests/unit/resource/test_equipment_chests_storage.py` — `test_auto_equip_ranking`,
  `test_home_storage_atomicity`, `test_chest_loot_and_apply`
- `tests/unit/resource/test_domain_8_economy.py`, `tests/unit/resource/test_economy_hardening.py`,
  `tests/unit/resource/test_resource_contract.py`, `tests/unit/resource/test_resource_v2_boundary.py`,
  `tests/unit/resource/test_resource_conflicts.py`, `tests/unit/resource/test_transaction_grouping.py`,
  `tests/unit/resource/test_durability_repair.py`, `tests/unit/resource/test_harvest_channeling.py`,
  `tests/unit/resource/test_loot_channeling.py`

**Unit — world objects touching inventory-shaped state:**
- `tests/unit/world/test_chest_lifecycle.py`, `tests/unit/world/test_home_storage.py`,
  `tests/unit/world/test_economy_contract.py`, `tests/unit/world/test_interaction_system.py`

**Unit — lifecycle (the one existing "notable item" transfer path, heirlooms):**
- `tests/unit/progression/test_lifecycle.py` (and any test exercising
  `LifecycleSystem.resolve_lifecycle()`'s heirloom-transfer block, per
  `TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR`) — must keep passing to confirm ItemInstance
  work does not regress the (dormant but present) heirloom transfer code path.

**Unit — API presenter (item schema shape):**
- `tests/unit/api/test_state_presenter.py` — covers `src/api/presenters/state_presenter.py:63`'s
  `{"id", "quantity", "metadata"}` item shaping; must keep passing unmodified unless the design explicitly
  adds instance fields to the read model (out of this ticket's stated AC).

**Integration:**
- `tests/integration/pipeline/test_transaction_completion.py`
- `tests/integration/kernel/test_resource_conservation.py`
- `tests/integration/kernel/test_race_conditions_v2.py` (constructs `GroundItemState` directly; confirms no
  ground-item id-space collision introduced)

**Quest (inventory-adjacent, uses ItemStack/InventoryUpdate):**
- `tests/unit/quest/test_quest_rewards.py`, `tests/unit/quest/test_quest_transactions.py`,
  `tests/unit/quest/test_transaction_groups.py`, `tests/unit/quest/test_progression_lifecycle.py`

**Progression (possession false-friend boundary):**
- `tests/unit/domains/progression/test_phase6_possession_understanding_service.py` — must keep passing
  unmodified; confirms `PossessionUnderstandingService` (Out of Scope) is untouched.

## New Tests Required

Per acceptance criteria — the design itself (ItemInstance's exact fields/state-location/id scheme) is a
Plan-phase decision not yet made, so these are described by *shape and intent*, not by presupposing the
final class/module layout. Update file paths once Plan fixes the module location.

- **Test name:** `test_item_instance_typed_state_location_not_untyped_dict`
  **Category:** architecture guard
  **Verifies:** the new `ItemInstance` record is a real typed dataclass/model living in a defined state
  location (e.g. asserting its module/class exists with typed fields `instance_id, item_id, owner_history,
  acquired_tick, acquired_method`), and — the actual guard — that `ItemStack.properties` and no other
  untyped dict anywhere on `EntityState`/`AuthoritativeState` carries any of these field names. This is the
  literal check for AC #1 ("NOT stored in ItemStack.properties or any untyped dict").
  **Where:** new file under `tests/unit/resource/` (or `tests/unit/core/`, matching wherever the
  implementation lands), grouped with the existing inventory-contract tests.

- **Test name:** `test_only_significant_items_receive_item_instance`
  **Category:** unit
  **Verifies:** creating a non-flagged item produces only the ordinary `ItemStack` (no `ItemInstance`
  record anywhere in state); creating an explicitly-flagged-significant item produces both the `ItemStack`
  (for capacity/conservation) *and* a linked `ItemInstance` record. Directly covers AC #2's first half.
  **Where:** same new file as above.

- **Test name:** `test_inventory_stacking_unmodified_by_item_instance_feature` (or: confirm the existing
  `test_inventory_stacking` itself is run as part of this ticket's own scoped verification, not duplicated)
  **Category:** regression / unit
  **Verifies:** AC #2's second half literally — `test_inventory_stacking()` passes with zero modification
  after the feature lands. This is a regression-surface item, not a new test to author from scratch;
  listed here to make explicit that CI/Verify must show this specific test file diffed as unchanged.
  **Where:** `tests/unit/resource/test_item_inventory_contract.py` (existing file, unmodified).

- **Test name:** `test_significant_item_merge_does_not_collapse_instances`
  **Category:** unit (regression-preventing / anti-drift)
  **Verifies:** if two significant items of the same `item_id` ever end up in the same inventory (e.g. two
  looted named swords), `InventoryService.apply_update`'s stack-merge must not silently collapse their two
  distinct `ItemInstance` records into one, or lose either instance's `owner_history`. This directly
  guards the dual-representation risk flagged in investigation.md (Risks and Open Questions) — the failure
  mode is real (equipment items are `stack_size=1` today, but nothing currently blocks two same-`item_id`
  significant items coexisting) and easy to miss if the merge path is only tested with non-significant
  items.
  **Where:** `tests/unit/resource/test_item_inventory_contract.py` or the new ItemInstance test file —
  whichever ends up owning merge-interaction coverage.

- **Test name:** `test_transfer_significant_item_appends_owner_history_via_apply_pipeline`
  **Category:** integration
  **Verifies:** AC #3 — transferring a significant item (e.g. sale, gift, loot pickup by a new owner)
  appends the new owner's entity id to `owner_history` via a typed `StateUpdate`, and that this only ever
  happens through `ApplyPath`/`AuthoritativeApplyPipeline` (i.e. no direct mutation of a live `ItemInstance`
  object anywhere — mirrors the existing pattern proven by `tests/unit/resource/
  test_item_inventory_contract.py`'s use of `ApplyPath.apply_generation()`). Should assert `owner_history`
  is append-only (old entries preserved, not overwritten) across at least two sequential transfers.
  **Where:** `tests/integration/pipeline/` (new file) or `tests/unit/resource/` if the transfer path stays
  unit-testable without a full pipeline run — follow whatever precedent Plan picks for how the transfer
  update is proposed/refined/applied.

- **Test name:** `test_item_instance_id_generation_is_deterministic`
  **Category:** unit (determinism guard)
  **Verifies:** given the same seed/tick/inputs, two independent runs that create the same significant item
  produce the identical `instance_id` (replay-safety). Should mirror the style of
  `tests/unit/kernel/test_replay_determinism.py` if that file already has a reusable double-run comparison
  harness. This is the direct test-shape consequence of investigation.md's determinism findings (world-
  compile counters vs. `corpse_id = 1000000 + e_id`-style mid-sim offset derivation) — whichever scheme
  Plan picks, this test proves it doesn't leak entropy (no raw `random`/`uuid.uuid4()` in the id path).
  **Where:** `tests/unit/kernel/` (paired with existing determinism tests) or co-located with the new
  ItemInstance unit tests — follow whichever convention `test_replay_determinism.py` already establishes.

- **Test name:** `test_town_128_item_kind_identity_unaffected_by_item_instance`
  **Category:** unit (parity-ledger guard)
  **Verifies:** the literal TOWN-128 claim — item_id/kind is preserved through pickup, stacking, selling,
  crafting, and dropping — still holds for a significant item carrying an `ItemInstance` sidecar. This is
  the concrete test that should become TOWN-128's (or a new adjacent entry's) `test_path` per this ticket's
  AC #4 and the pre-existing `test_path: null` gap noted in investigation.md.
  **Where:** `tests/unit/resource/test_item_inventory_contract.py` (extends the existing TOWN-126/127/128
  coverage) or a new adjacent test file, matching wherever Plan resolves the conditional parity-ledger
  bullet.

- **Test name:** `test_significance_flag_requires_explicit_caller_input` (guard against ad-hoc criteria)
  **Category:** unit (anti-drift / architecture guard)
  **Verifies:** whatever scaffolding lands for `significance_flag` in this ticket does not silently invent
  trigger criteria (e.g. hardcoding "rarity == RARE" or an item_id allowlist) without an explicit,
  documented, caller-supplied flag. If Plan defers the actual triggering logic, this test should assert the
  flag is caller-supplied-only (e.g. raises/no-ops without an explicit `significant=True` argument) rather
  than silently deriving significance from any item property. Directly enforces the ticket's own AC #5.
  **Where:** co-located with the new ItemInstance unit tests.

## Scoped Pytest Commands

```bash
# Primary regression surface: inventory/resource unit tests
pytest tests/unit/resource/ -m "not slow"

# Lifecycle (heirloom transfer path — adjacent "notable item" system)
pytest tests/unit/progression/test_lifecycle.py -m "not slow"

# World-object tests touching inventory-shaped state (chests/home storage)
pytest tests/unit/world/test_chest_lifecycle.py tests/unit/world/test_home_storage.py tests/unit/world/test_economy_contract.py tests/unit/world/test_interaction_system.py -m "not slow"

# Quest tests exercising ItemStack/InventoryUpdate
pytest tests/unit/quest/ -m "not slow"

# Possession false-friend boundary (must stay untouched)
pytest tests/unit/domains/progression/test_phase6_possession_understanding_service.py

# API presenter shape (item schema)
pytest tests/unit/api/test_state_presenter.py

# Integration: conservation + transaction completion + race conditions
pytest tests/integration/pipeline/test_transaction_completion.py tests/integration/kernel/test_resource_conservation.py tests/integration/kernel/test_race_conditions_v2.py -m "not slow"

# Determinism (if instance-id generation touches replay path)
pytest tests/unit/kernel/test_replay_determinism.py -m "not slow"

# New ItemInstance-specific tests (path TBD by Plan — update once module location is fixed)
pytest tests/unit/resource/ -k "instance" -m "not slow"
```

Never run bare `pytest tests/` — scope stays within `tests/unit/resource/`, `tests/unit/progression/`,
`tests/unit/world/`, `tests/unit/quest/`, `tests/unit/domains/progression/`, `tests/unit/api/`,
`tests/integration/pipeline/`, `tests/integration/kernel/`, and `tests/unit/kernel/` as listed above.

## Anti-Drift Test Guards

- **Merge-path guard**: `test_inventory_stacking` (existing, unmodified) plus
  `test_significant_item_merge_does_not_collapse_instances` (new) together prove the ordinary merge path is
  untouched for non-significant items *and* that significant items don't silently lose instance data to the
  same merge code — the two failure directions of the same risk.
- **Untyped-dict guard**: `test_item_instance_typed_state_location_not_untyped_dict` directly prevents the
  single most likely scope-creep/architecture violation named in the ticket itself — a lazy implementation
  bolting `instance_id`/`owner_history` onto `ItemStack.properties` because it's the path of least
  resistance given `properties` already exists on the class — data placed there would be silently
  destroyed by the very merge path `test_inventory_stacking` exercises.
- **Possession false-friend guard**: `test_phase6_possession_understanding_service.py` passing unmodified
  proves no implementer conflated `PossessionUnderstandingService` (Out of Scope) with `ItemInstance` —
  e.g. accidentally routing significance evaluation through possession's subjective priority scoring
  instead of a real typed flag.
- **Apply-pipeline-only guard**: `test_transfer_significant_item_appends_owner_history_via_apply_pipeline`
  guards against a direct/local mutation of `owner_history` anywhere outside `ApplyPath` — the exact
  violation this repo's Hard Rules ("Do not mutate durable state outside authoritative flows") and this
  ticket's own AC #3 forbid.
- **Determinism guard**: `test_item_instance_id_generation_is_deterministic` guards against an
  implementer reaching for `uuid.uuid4()`/`random.Random()` for id generation out of convenience — this
  repo's `DeterministicRNG`/monotonic-counter precedent (investigation.md, "Deterministic ID generation")
  exists specifically so replay/determinism isn't broken by exactly this shortcut.
- **Significance-criteria guard**: `test_significance_flag_requires_explicit_caller_input` guards against
  quietly inventing trigger criteria mid-implementation (e.g. "any item with `value > 100`") when the
  ticket, the source schema doc, and this investigation all agree that criteria is an explicit open
  question requiring sign-off, not something to backfill silently to make a test pass.
- **TOWN-128 guard**: `test_town_128_item_kind_identity_unaffected_by_item_instance` guards the specific
  parity claim this ticket's AC #4 requires re-verifying — a regression here would mean the ItemInstance
  sidecar somehow altered `item_id`/`ItemKind` on the underlying `ItemStack`, which nothing in the ticket's
  scope should ever require.

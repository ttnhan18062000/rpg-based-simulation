---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260831-ITEM-INSTANCE-HISTORY
artifact_type: investigation
tags: [resource]
---

# Investigation — TCK-20260831-ITEM-INSTANCE-HISTORY

## Current Behavior

### Item/inventory shape (item_id-as-type + stack count only)
- `src/core/models/inventory.py:24-34` — `ItemStack` is `@dataclass(frozen=True, slots=True)` with exactly
  `item_id: str`, `quantity: int = 1`, `properties: Dict[str, Any] = field(default_factory=dict)`. There is
  no per-instance identifier field anywhere on this class. `properties` is an untyped dict — the ticket's
  scope correctly identifies this as the trap to avoid (see "Anti-Drift Hazards").
- `src/core/models/inventory.py:36-57` — `InventoryComponent` wraps `items: List[ItemStack]` + `gold` +
  `max_slots`/`max_weight`. `src/core/state.py:16` re-exports `ItemKind, EquipSlot, ItemStack,
  InventoryComponent` from `models/inventory.py` — there is only one definition of `ItemStack` in the
  codebase (`src/core/inventory.py` and `src/core/update_models/inventory.py` both import the same class,
  the latter only under `TYPE_CHECKING`).
- `src/core/inventory.py:134-215` — `InventoryService.apply_update()` is the authoritative merge path. On
  addition (line 176-193) it explicitly searches `new_items` for an existing `ItemStack` with the same
  `item_id` and quantity below `defn.stack_size`, and does `new_items[i] = replace(existing,
  quantity=existing.quantity + amount_to_add)` — a destructive quantity-only merge. Nothing in this
  function reads or preserves any field other than `item_id`/`quantity`; any per-instance data placed in
  `ItemStack.properties` would be silently dropped/overwritten by this merge for any two stacks sharing the
  same `item_id` (equipment items today have `stack_size=1` in `ItemRegistry`, e.g. `iron_sword`,
  `steel_sword` at `src/core/items.py:41-48`, so a merge collision requires two copies of the *same*
  equipment id in one inventory — possible via loot + purchase, not blocked anywhere).
- `tests/unit/resource/test_item_inventory_contract.py:9-35` (`test_inventory_stacking`, the exact test
  named in this ticket's acceptance criteria) proves this merge behavior today: two 5-unit `iron_ore`
  additions collapse into one 10-unit stack via `ApplyPath.apply_generation()`.

### False-friend check — no existing `instance_id`
- `grep -rn "instance_id" src/ docs/ tests/` returns exactly one hit, and it is not code: `docs/brainstorm/
  rpg_expected_schemas.html:778` — the *source design doc for this very ticket* (idea 30), proposing
  `instance_id: str` as a **new**, not-yet-built field. `grep -rn "ItemInstance"` likewise returns zero
  source-code hits — only the same schema doc (`:774-782`), `docs/plans/rpg_design_roadmap/
  rpg_m9_corpus_test_coverage_epic.md:174` (a future test-coverage idea referencing the concept as
  not-yet-existing), and the epic plan doc already cited in this ticket's briefing.
- Confirmed: there is **no existing false-friend `instance_id`** anywhere in `src/`. The one concept that
  could be mistaken for a false friend by name similarity — `src/domains/progression/possession.py`'s
  `PossessionUnderstandingService` — is explicitly called out as Out of Scope in the ticket and confirmed
  by reading the file: it evaluates `keep_priority`/`sell_priority`/`equip_priority`/`craft_priority` per
  `item_id` string (`src/domains/progression/possession.py:41-112`), keyed by item **type**, not per
  physical instance, and produces a non-durable `PossessionUnderstandingComponent` recomputed each
  evaluation (`last_evaluated_tick=state.tick`), not a durable ownership-history record. No conflation risk
  found in the actual code.

### TOWN-128 parity ledger entry
- `docs/parity_ledger/town_resource.yaml:1325-1335`:
  ```yaml
  - id: TOWN-128
    text: Item identity/kind is preserved through pickup, stacking, selling, crafting, and dropping.
    status: verified
    priority: P0
    legacy_evidence: null
    v2_evidence: Implementation proven via exhaustive checklist audit Phase 1-11
    proof_type: null
    test_path: null
    divergence_note: null
    support_boundary: null
  ```
  It sits in a triad with **TOWN-126** ("Item *quantity* is preserved through pickup, stacking, selling,
  crafting, and dropping.") and **TOWN-127** ("Item *weight* is preserved...") — same wording pattern,
  same phase-1-11 checklist-audit evidence, all three `test_path: null`. Read together, TOWN-128's
  "identity/kind" plainly means **item_id/ItemKind type identity** (a stack of `iron_ore` stays
  `iron_ore`/`MATERIAL` through every operation) — it is about *type* preservation, the same axis as
  quantity and weight, not per-physical-instance uniqueness. It does **not** already describe
  instance-identity behavior and is **unaffected** by this ticket as currently scoped, provided the
  ItemInstance sidecar never changes `item_id`/`kind` on the underlying `ItemStack` (see Anti-Drift
  Hazards).
- Pre-existing gap, not caused by this ticket: TOWN-128 (and its sibling TOWN-126/127) are **P0** entries
  with `test_path: null`. Per this repo's Authoritative Mechanics Rule, P0 entries require a passing
  `test_path`. `tests/unit/resource/test_item_inventory_contract.py::test_inventory_stacking` and
  `test_inventory_capacity_limits` are strong existing candidates but are not currently wired as the
  entry's `test_path`. Flagging as a gap; not this ticket's scope to fix TOWN-126/127's own `test_path`
  gap, only to decide whether TOWN-128 needs a new adjacent entry (see Docs Requiring Update) which, if
  added, should have a real `test_path` from day one per the P0 rule.

### `significance_flag` — what anchors exist (none, confirmed)
- `docs/brainstorm/rpg_expected_schemas.html:774-783` is the origin of this ticket's scope and already
  marks `significance_flag` with a `badge gap` ("New, open question on trigger criteria") — this is not an
  omission by the ticket author, it is inherited directly from the source design doc.
- `src/core/items.py` (`ItemRegistry`, 218 lines total) has **no rarity/tier/relic/unique/quest-item field
  anywhere** on `ItemDefinition` (fields are only `id, name, kind, weight, stack_size, value, properties`).
  Confirmed by reading the full class definition and every registered item (iron_ore, wood, herb, bread,
  healing_potion, iron_sword, steel_sword, iron_plate, leather_armor, wooden_staff, iron_dagger,
  wooden_club, gold_coin, gold, ore, stone, plus dynamically-classified items further down the file).
- `docs/core/items_and_inventory.md:27-150` (the human-facing "Items & Inventory" technical doc,
  `last_verified: 2026-06-06`) **does** describe a `rarity: Rarity` field (`COMMON/UNCOMMON/RARE`) on an
  `ItemTemplate` class, plus a "Legendary Items" section and an 8-row sell-price-by-rarity table. **This
  does not match the real V2 code** — the actual `ItemDefinition` in `src/core/items.py` has no `rarity`
  field, no `ItemTemplate` class exists (the doc's own "Primary files" line even cites `src/core/models.py`,
  which does not exist — the real files are `src/core/models/inventory.py` and `src/core/items.py`). This
  doc describes the legacy/V1 (or aspirational) item system, not the current implementation. **This is a
  pre-existing doc/code divergence unrelated to this ticket** — flagging it because Plan may otherwise
  mistake this doc's `rarity` field for a real, usable anchor for `significance_flag` trigger criteria. It
  is not: `rarity` does not exist in the running V2 item system today.
- The closest *adjacent* concept found, and the only two real signals in the whole codebase that resemble
  "this item matters more than a generic stack":
  1. `src/domains/progression/possession.py:90-92` — a single hardcoded string check,
     `if item_id == "ancient_fragment": keep_priority = 0.9; reason = "Unknown rare item clue. Keep for
     inquiry."`. This is a subjective, per-item_id, non-durable heuristic inside
     `PossessionUnderstandingService.evaluate()` — not a flag, not durable state, and keyed by type not
     instance. It is evidence that the game world has *some* notion of narratively-special items, but it
     provides no reusable trigger-criteria pattern.
  2. `src/core/state.py:151-152` — `LifecycleComponent.heirlooms: list[str]` (item_id strings) plus
     `heir_entity_id: Optional[int]`. `src/systems/lifecycle_systems/lifecycle.py:126` transfers
     `heirloom_stacks = [ItemStack(item_id=hid, quantity=1) for hid in entity.lifecycle.heirlooms]` to the
     heir on death (`ResourceTransferIntent`, fixed via `TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-
     TYPEERROR`, done ticket). **However**: `grep -rn "heirlooms_add=" src/ tests/` returns **zero** call
     sites — nothing in production code or tests ever populates `LifecycleUpdate.heirlooms_add`
     (`src/core/updates.py:441`), so `heirlooms` is always an empty list in practice today. It is a
     designed-but-dormant list of "specific items worth preserving across death," structurally the closest
     analog to "significant" in the whole codebase, but (a) it is item_id-typed not instance-typed, (b) it
     is completely unwired/orphaned (same "written by nothing" shape the atlas doc already documents for
     `heir_entity_id` itself), and (c) it carries no criteria for *what* makes an item heirloom-worthy —
     the list is just populated externally, whenever something eventually calls `heirlooms_add=[...]`.
- **Conclusion for Plan**: no real trigger-criteria anchor exists anywhere in the codebase. `significance_
  flag`'s trigger criteria remains a genuinely open design decision, exactly as the ticket already states —
  confirmed, not merely assumed.

### Consumers of `ItemStack`/`InventoryComponent` (surfaces a new field could touch or break)
Construct `ItemStack(...)` directly: `src/certification/scenarios.py`, `src/core/inventory.py`,
`src/domains/progression/resolver.py`, `src/engine/blacksmith.py`, `src/engine/intent/action_intent.py`,
`src/engine/interaction.py`, `src/engine/quests.py`, `src/entities/archetype_factory.py`,
`src/perf/scenarios.py`, `src/systems/economy_systems/crafting.py`, `src/systems/economy_systems/loot.py`,
`src/systems/lifecycle_systems/lifecycle.py`, `src/systems/world_systems/harvesting.py`,
`src/town/blacksmith.py`, `src/town/home_storage.py`, `src/town/shop.py`, `src/world/boss.py`.

Reference `InventoryComponent` directly: `src/certification/scenarios.py`, `src/core/builder.py`,
`src/core/conservation.py`, `src/core/inventory.py`, `src/core/models/inventory.py`, `src/core/state.py`,
`src/engine/apply_plan.py`, `src/engine/apply.py`, `src/entities/archetype_factory.py`,
`src/systems/world_systems/generator.py`, `src/town/home_storage.py`, `src/worldbuilding/compiler.py`.

API-facing surface: `src/api/presenters/state_presenter.py:63` shapes each inventory item as `{"id":
i.item_id, "quantity": i.quantity, "metadata": i.metadata}` for the REST read model — this presenter would
need to decide whether/how to surface `instance_id`/`owner_history` for significant items if they should be
API-visible (not required by this ticket's acceptance criteria, but a real touch point if the eventual
design wants instance data client-visible).

`src/core/conservation.py` computes atomic-conservation checks purely via `sum(s.quantity for s in
...items if s.item_id == X.item_id)` (lines 142, 167, 204, 307, 318) — entirely blind to any field beyond
`item_id`/`quantity`. This means: whatever ItemInstance ends up looking like, the underlying `ItemStack`
entry for a significant item must keep flowing through `InventoryComponent.items` unchanged (same
`item_id`, `quantity`) for these conservation checks, harvest/crafting materials-matching, and
`InventoryService.can_add_items`/`apply_update` to keep working — ItemInstance must be a strictly additive
sidecar record, never a replacement of the ItemStack representation in inventory.

### Deterministic ID generation — real precedent in this codebase
No production code today constructs `GroundItemState`/`CorpseState` with a *randomly*-assigned id.
- **World-compile time** (`src/worldbuilding/compiler.py:297,326,355`): simple monotonic integer counters
  seeded per-object-kind — `next_resource_id = 10000`, `next_building_id = 20000`, `next_entity_id = 1` —
  incremented deterministically per spawn, with an explicit deterministic-reroll collision strategy
  (`_ENTITY_SPAWN_COLLISION_SUB_ID_BASE`, lines 132-153) rather than any random/UUID scheme.
- **Mid-simulation** (`src/engine/apply_plan.py:320`): `corpse_id = 1000000 + e_id` — a pure, deterministic
  offset derived from the already-known `entity_id`, computed inline in
  `_compute_world_collection_changes()` at authoritative-apply time, no RNG call at all. This is the
  closest real precedent for a mid-sim durable-record id (e.g. a loot-drop-created ItemInstance): an
  offset-base + known-id derivation, not a random/UUID scheme.
- **Randomized decisions** (`src/platform/rng.py:22-45`, `DeterministicRNG`): where true
  seed-reproducible randomness *is* needed, the pattern is `DeterministicRNG(base_seed).get_int(Domain.X,
  a, b)`/`get_float(...)`, domain-separated so different gameplay domains never share a random stream even
  with the same seed. If instance-id generation ever needs a random component (as opposed to a pure
  offset derivation), this is the sanctioned mechanism — `random.Random()`/`new_random_source()` is
  explicitly documented as non-deterministic and reserved for non-gameplay uses only.
- No production code today ever constructs `GroundItemState` at all (only `src/engine/apply_plan.py:227`
  consumes pre-built ones from `update.ground_items_add_or_update`) — every `GroundItemState(id=...)`
  construction found in the repo is in test fixtures (`tests/unit/cognition/test_information_seeking.py`,
  `tests/unit/resource/test_loot_channeling.py`, `tests/unit/resource/test_resource_conservation_
  regression.py`, `tests/unit/quest/test_transaction_groups.py`, `tests/unit/core/test_migration_proof.py`,
  `tests/integration/pipeline/test_transaction_completion.py`, `tests/integration/kernel/
  test_race_conditions_v2.py`, `tests/integration/kernel/test_resource_conservation.py`,
  `tests/perf/test_perf_metropolis.py`) — i.e. this repo currently has no live worker that mints a brand
  new ground-item id mid-simulation; only the death→corpse path (`apply_plan.py:320`) demonstrates a real
  mid-sim id-minting pattern.

### Existing durable-collection shape precedent (relevant to "a defined typed state location")
`AuthoritativeState` (`src/core/state.py:1140-1177`) holds a flat set of top-level `Dict[<key>, <State>]`
collections for every other world-object kind that needs independent identity and lifecycle: `entities:
Dict[int, EntityState]`, `resource_nodes: Dict[int, ResourceNodeState]`, `ground_items: Dict[int,
GroundItemState]`, `corpses: Dict[int, CorpseState]`, `chests: Dict[int, ChestState]`, `buildings: Dict[int,
BuildingState]`, `camps: Dict[str, CampState]`, `regions: Dict[str, RegionState]`, `groups: Dict[int,
GroupRecord]`. `StateUpdate` (`src/core/updates.py:893-944`) mirrors this with a consistent `<name>_add_or_
update: List[<State>]` + `<name>_remove: List[<key>]` (or `_updates: Dict[<key>, <Update>]`) pair per
collection. This is the existing, load-bearing pattern for "a durable record with its own identity that
isn't owned by a single entity's component tree" — the closest structural precedent for whatever "defined
typed state location" the ItemInstance record ends up using. (Reporting the pattern as evidence only — the
choice between this shape, an entity-scoped component, or something else is a Plan-phase decision, not
decided here.)

### Existing tests covering the affected files
`tests/unit/resource/test_item_inventory_contract.py` — `test_inventory_stacking` (the exact test named in
this ticket's AC), `test_inventory_capacity_limits`, `test_equipment_and_gold_updates`. All three exercise
`InventoryService.apply_update` via `ApplyPath.apply_generation`, marked `@pytest.mark.v2_contract`.

`tests/unit/resource/test_inventory_hardening.py` — `test_inventory_stack_size_enforcement`,
`test_inventory_weight_preservation_delta`, `test_partial_stack_fill_before_slot_rejection`.

`tests/unit/resource/test_inventory_serialization.py` — `test_inventory_stack_merging`,
`test_inventory_limits`, `test_entity_serialization_roundtrip`.

`tests/unit/resource/test_equipment_chests_storage.py` — `test_auto_equip_ranking`,
`test_home_storage_atomicity`, `test_chest_loot_and_apply`.

`tests/unit/resource/test_resource_conservation_regression.py` — 7 tests (`test_harvest_conservation_
full_inventory`, `test_loot_conservation_full_inventory`, `test_corpse_conservation_full_inventory`,
`test_explicit_intent_resolution`, `test_crafting_conservation_no_materials`, `test_shop_buy_conservation_
insufficient_gold`, `test_shop_sell_conservation_missing_items`) — these exercise conservation across the
exact operations TOWN-126/127/128 cover (pickup, stacking, selling, crafting, dropping).

No test file anywhere currently references `instance_id`/`ItemInstance` — confirmed by the same grep used
for the false-friend check above; this matches the ticket's own Request Summary claim exactly.

## Mechanics / Engine Constraints
- `docs/engine/authoritative_mutation_pipeline_contract.md` §1 ("The Pipeline Law: Proposal -> Refine ->
  Apply") — Semantic workers propose deltas from isolated snapshots; `AuthoritativeApplyPipeline` refines
  and tie-breaks; `ApplyPath` alone commits. This directly constrains the ticket's own AC #3
  ("Transferring a significant item appends the new owner to owner_history via a typed StateUpdate through
  the authoritative apply pipeline only") — matches this repo's existing, load-bearing law exactly; no new
  exception needed, no divergence to record.
- `docs/mechanics/03_economic_laws.md` has **no existing section on item identity or per-instance
  ownership** (`grep -n "identity\|instance\|stack"` returns zero matches) — this chapter currently only
  covers atomic conservation, harvesting, trade, and crafting formulas at the item_id/quantity level. It
  does not currently constrain (or bless) instance-level identity in any way; a new subsection would be the
  first mechanics-bible treatment of this concept.
- Project Hard Rules ("Do not mutate durable state outside authoritative flows", "Durable changes must be
  represented through typed records/updates") directly motivate the ticket's own scope constraint (typed
  `ItemInstance` record, not `ItemStack.properties`) — already correctly anticipated in the ticket text, no
  new constraint discovered beyond what's already stated.

## Docs Requiring Update
- `docs/core/items_and_inventory.md`: the "Items & Inventory" technical reference doc has no section
  describing per-instance identity/ownership history; a new class this significant to the item system needs
  a described home in the primary technical doc for this subsystem — new subsection required once
  ItemInstance's design settles. (Independent, pre-existing note: this doc's *existing* content already
  diverges from the real V2 `ItemRegistry`/`ItemStack` shape — see Current Behavior — but that reconciliation
  is out of this ticket's scope; only the new ItemInstance section is required here.)
- `docs/mechanics/03_economic_laws.md`: this ticket introduces a new durable record and a new transfer law
  (owner_history append via typed StateUpdate through the apply pipeline only) with no current Mechanics
  Bible treatment; as a new simulation law governing item behavior, it needs a subsection once the design is
  final.
- `docs/parity_ledger/town_resource.yaml`: the ticket's own AC #4 explicitly frames this as an
  implementation-time choice — re-verify TOWN-128 as unaffected (no edit needed) **or** add a new adjacent
  entry distinguishing item_id-identity from instance_id-uniqueness (edit needed). This bullet is
  conditional on that choice, which has not been made yet (Plan/Implement decision). If the implementer
  confirms TOWN-128 is unaffected and no new entry is warranted, resolve this bullet per the
  `TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED` marker convention ("Resolved during
  implementation, condition not met") rather than deleting it.

The `docs/brainstorm/rpg_expected_schemas.html` doc (path: `docs/brainstorm/rpg_expected_schemas.html`,
under `docs/`) is not required to change for this ticket: it is the brainstorm/design-source doc that
*originated* this ticket's scope (idea 30, lines 774-783) and already accurately describes the intended
shape (`ItemInstance`, `instance_id`, `owner_history`, `acquired_tick`/`acquired_method`,
`significance_flag` marked as an open gap) — this ticket implements what that doc already states, it does
not change the doc's own content.

## Parity Ledger Overlap
- **TOWN-128** (`docs/parity_ledger/town_resource.yaml:1325`, P0, `verified`, `test_path: null`) — "Item
  identity/kind is preserved through pickup, stacking, selling, crafting, and dropping." Describes
  item_id/kind-type identity, not instance identity — unaffected as scoped (see Docs Requiring Update for
  the conditional new-entry decision).
- **TOWN-126** (`:1303`, P0, `verified`, `test_path: null`) — item *quantity* preservation. Same triad,
  same `test_path: null` gap, unaffected by this ticket, flagged only as pre-existing context.
- **TOWN-127** (`:1314`, P0, `verified`, `test_path: null`) — item *weight* preservation. Same triad, same
  gap, unaffected, flagged only as pre-existing context.
- No other `docs/parity_ledger/*.yaml` entry references item identity, instance tracking, or ownership
  history (confirmed by the TOWN-128 grep context read above, which is the entirety of the adjacent block).

## Prior Work
- `TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR` (done, hotfix) — fixed an unrelated
  `list`/`tuple` `TypeError` in the heirloom-transfer-on-death code path
  (`src/systems/lifecycle_systems/lifecycle.py:122`). Directly relevant as **prior art for the closest
  existing "notable item" concept** (`LifecycleComponent.heirlooms`) — see Current Behavior above for why it
  is not a usable anchor for `significance_flag` criteria (item_id-typed, orphaned/unwired,
  no-criteria-of-its-own), but it is the one adjacent system whose behavior (item transfer to a specific
  entity via `ResourceTransferIntent`, `source_kind="CHEST"`) resembles what an ItemInstance
  ownership-transfer path might eventually reuse or need to coexist with.
- `TCK-20260623-FIX-INVENTORY-DEFAULTS` (done) — prior inventory-defaults hardening ticket; touched
  `src/entities/`, `src/domains/resource/`, inventory/resource test dirs. No overlap with per-instance
  identity; confirms this area has had recent, unrelated hardening work but nothing instance-related.
  Registry search (`docs/REGISTRY.yaml`, filtered by `related_code_areas` overlap with `src/core/
  inventory.py`/`src/core/models/inventory.py`/`src/core/state.py` and by tag `resource`/`inventory`)
  returned ~45 historical tickets spanning the whole Resource/Phase 3-9 lineage
  (`TCK-20260418-RESOURCE-KERNEL-M1` through `TCK-20260427-RESOURCE-CONSERVATION-HARDENING` and
  onward) — none of them (beyond the heirloom ticket above) reference per-instance identity, `instance_id`,
  or ownership tracking. This confirms the epic plan's own framing: idea 30 genuinely has no prior
  implementation attempt anywhere in this codebase's history.
- No `stored_artifacts/` entry exists for a prior ItemInstance-shaped ticket (registry search above is
  exhaustive for this scope; no manual directory scan was needed or performed).

## Risks and Open Questions
- **Open, explicitly flagged by the ticket itself and confirmed here with no anchor found**:
  `significance_flag`'s trigger criteria. Do not invent criteria — Plan must either propose criteria for
  sign-off or explicitly defer implementation of the *flagging* mechanism while building the
  `ItemInstance` record/pipeline scaffolding around a caller-supplied flag.
- **Dual-representation risk**: because `src/core/conservation.py`'s atomic-conservation checks and
  `InventoryService`'s slot/weight logic are entirely `ItemStack.item_id`/`.quantity`-driven and blind to
  any richer per-instance data, a significant item must keep a normal `ItemStack` entry in
  `InventoryComponent.items` *in addition to* its `ItemInstance` sidecar record. Any design that tries to
  represent a significant item *only* via `ItemInstance` (removing its `ItemStack` presence) would silently
  break weight/slot capacity checks, conservation checks, and every existing pickup/sell/craft/drop code
  path that iterates `inventory.items`. This is a real, concrete failure mode to design against, not a
  hypothetical.
- **Instance-id key type is undecided**: the schema doc (`rpg_expected_schemas.html:778`) specifies
  `instance_id: str`, but every existing analogous top-level-collection key in `AuthoritativeState`
  (`ground_items`, `corpses`, `chests`, `buildings`, `groups`) is `int`-keyed, while `camps`/`regions` are
  `str`-keyed. Either is precedented in this codebase; Plan needs to pick one and needs a concrete
  deterministic generation scheme either way (see Current Behavior's "Deterministic ID generation"
  section for the two real precedents: world-compile monotonic counters, and the `corpse_id = 1000000 +
  e_id` mid-sim offset-derivation pattern).
- **No production mid-sim id-minting precedent for a brand-new world-object collection** exists to copy
  wholesale — the one real mid-sim id-minting example (`corpse_id = 1000000 + e_id`) is a 1:1 derivation
  from an already-existing entity, which doesn't directly generalize to a loot-drop-created ItemInstance
  that isn't tied to exactly one entity id. This is a genuine design gap Plan must resolve, not merely
  reuse.
- **TOWN-126/127/128's pre-existing `test_path: null` gap** is out of this ticket's scope to fix wholesale,
  but if a new adjacent parity entry is added per AC #4, it should not repeat the same gap — a P0 entry
  needs a real `test_path` from creation, per the Authoritative Mechanics Rule.
- **`item_ownership_transferred` event**: `docs/brainstorm/rpg_expected_schemas.html:978` describes a
  planned `item_ownership_transferred` WorldEvent (`item_instance_id, from_entity_id, to_entity_id,
  acquired_method`) reusing the existing `inventory` `EventCategory` — noted as "scored by zero pillars
  today." This ticket's AC does not explicitly require emitting this event (only that the owner_history
  append happens via a typed StateUpdate through the apply pipeline), so this is flagged as an open
  question for Plan to accept or explicitly defer, not assumed as in-scope.

## Anti-Drift Hazards
- Do **not** add any per-instance field to `ItemStack.properties` (untyped dict) or to any other untyped
  dict anywhere — this is the exact anti-pattern the ticket scope and this repo's Durable State Rule both
  forbid, and it is also the literal mechanism (`InventoryService.apply_update`'s stack-merge, `src/core/
  inventory.py:176-193`) that would silently destroy such data on the very next same-`item_id` stack merge.
- Do **not** modify `InventoryService.apply_update`'s existing merge-by-`item_id` behavior for
  non-significant items — `test_inventory_stacking` (the exact test the AC names) must keep passing
  unmodified, and every other conservation/capacity check in `src/core/conservation.py`/`src/core/
  inventory.py` depends on that merge behavior being unchanged for ordinary stackable items.
- Do **not** conflate this ticket's `ItemInstance` (physical per-item ownership identity) with `src/
  domains/progression/possession.py`'s `PossessionUnderstandingService` (subjective keep/sell/equip
  reasoning) — confirmed unrelated by reading both; explicitly Out of Scope in the ticket.
- Do **not** treat `docs/core/items_and_inventory.md`'s `rarity`/`ItemTemplate`/`Rarity` content as a real,
  implemented anchor for `significance_flag` — confirmed above that this doc describes a system that does
  not exist in the current `src/core/items.py`/`ItemDefinition`. Using it as design grounding would be
  building against documentation, not code.
- Do **not** wire `significance_flag`'s trigger criteria ad hoc during implementation — the ticket, the
  source schema doc, and this investigation all independently confirm this is a genuine open design
  question requiring sign-off, not an oversight to quietly fill in.
- Do **not** let a new `ItemInstance` collection/id scheme silently duplicate or diverge from the existing
  `ground_items`/`corpses`/`chests` id-space (e.g. reusing `int` ids without a collision-avoidance strategy
  analogous to `apply_plan.py:320`'s offset scheme, if an `int`-keyed design is chosen) — this codebase has
  no central sequential-id registry across those three collections today (each has its own base-offset
  convention: 10000/20000/1000000), so a fourth collection needs its own explicit, non-colliding scheme if
  it goes this route.

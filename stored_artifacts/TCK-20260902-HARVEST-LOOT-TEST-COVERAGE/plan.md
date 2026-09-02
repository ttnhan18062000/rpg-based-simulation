---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260902-HARVEST-LOOT-TEST-COVERAGE
artifact_type: plan
tags: [testing, economy]
---

# Implementation Plan — TCK-20260902-HARVEST-LOOT-TEST-COVERAGE

## Summary

Extend the two existing dedicated unit test files —
`tests/unit/resource/test_harvest_channeling.py` and `tests/unit/resource/test_loot_channeling.py`
— with the specific untested branches identified in `investigation.md`, following the ten test
functions already fully specified in `test_plan.md`. No source file (`harvesting.py`, `loot.py`)
is touched. The plan resolves the two open questions the investigation deliberately left for
planning: the harvesting.py node-cooldown "merge" branch (lines 69-74) is confirmed genuinely
unreachable through the public `HarvestSystem.update()` API within a single call and will be
documented, not force-tested; and the TOWN-009/TOWN-010 parity-ledger bonus repair is explicitly
declined this ticket, on fresh evidence read directly from `src/engine/interaction.py` and the
ledger file, because the mismatch between what the ledger cites and what this ticket tests is
real and non-trivial, not a clean path-repointing. The corpse-completion fixture needs no new
helper — it follows the same inline-dataclass-construction style already used by both files, with
`CorpseState` fields confirmed from source.

## Steps

### Step 1 — Harvesting.py entity-loop skip branches
**Files:** `tests/unit/resource/test_harvest_channeling.py`
**Change:** Add two new test functions, both marked `@pytest.mark.v2_contract`, both importing
`HarvestSystem` via the existing shim (`src.systems.harvest_system`, as line 7 of the file already
does) and constructing state via `V2EntityBuilder` / `AuthoritativeState` inline, matching the
existing style (lines 11-23):
- `test_harvest_no_interaction_or_no_target_is_skipped` — construct an entity with no
  `interaction` set (builder default) or with an `InteractionComponent(target_node_id=None)`, call
  `HarvestSystem.update(state)`, assert `entity.id not in sys_upd.entity_updates`. Verified source:
  `src/systems/world_systems/harvesting.py:16-17` (`if not entity.interaction or
  entity.interaction.target_node_id is None: continue`).
- `test_harvest_skips_non_harvest_interaction_kind` — construct an entity with
  `interaction.kind="ground_item"` (or `"corpse"`) and a valid `target_node_id` pointing at a real
  `ResourceNodeState` (so the skip is provably due to `kind`, not a failed node lookup), call
  `HarvestSystem.update(state)`, assert no `entity_updates` entry. Verified source:
  `src/systems/world_systems/harvesting.py:19-20` (`if entity.interaction.kind != "harvest":
  continue`). `InteractionComponent.kind` accepts `"ground_item"`/`"corpse"` as documented values —
  confirmed at `src/core/state.py:407`.
**Do NOT touch:** `src/systems/world_systems/harvesting.py`; `test_harvest_channeling_and_yield`
and `test_harvest_node_cooldown` (existing functions, unmodified).
**Verify:** `pytest tests/unit/resource/test_harvest_channeling.py -v` — both new functions pass.

### Step 2 — Harvesting.py reset branches (missing/depleted node, distance)
**Files:** `tests/unit/resource/test_harvest_channeling.py`
**Change:** Add:
- `test_harvest_resets_on_missing_or_depleted_node` — two sub-cases (either two `@pytest.mark.
  parametrize` cases or two functions): (a) entity's `interaction.target_node_id` has no matching
  key in `state.resource_nodes`; (b) target node exists but `remaining_charges<=0`. Both call
  `HarvestSystem.update(state)` and assert `entity_updates[entity.id].interaction.reset is True`.
  Verified source: `src/systems/world_systems/harvesting.py:26-31` (`if not node or
  node.remaining_charges <= 0: entity_updates[entity.id] = EntityUpdate(...,
  interaction=InteractionUpdate(reset=True))`).
- `test_harvest_resets_on_distance` — entity with a live `harvest` interaction targeting a valid,
  non-depleted node whose Manhattan distance from `entity.navigation.position` exceeds `1.5`
  (e.g. entity at `(0,0)`, node at `(0,2)` → dist `2.0`). Assert `reset is True`. Verified source:
  `src/systems/world_systems/harvesting.py:33-39` (`dist = abs(...) + abs(...); if dist > 1.5:
  reset`). Mirror the existing `test_loot_interruption_by_distance` structure (sibling file, lines
  48-74) for state-construction style, adapted to a `harvest`/`ResourceNodeState` target instead of
  a `ground_item`.
**Do NOT touch:** `src/systems/world_systems/harvesting.py`; the completion/progress branches
(lines 41-62), already covered by `test_harvest_channeling_and_yield` — do not re-test those here.
**Verify:** `pytest tests/unit/resource/test_harvest_channeling.py -v` — new functions pass;
existing `test_harvest_channeling_and_yield` still passes unmodified.

### Step 3 — Harvesting.py node-cooldown branch: reachability resolved as dead code, documented not tested
**Files:** `tests/unit/resource/test_harvest_channeling.py`
**Change:** Confirmed by direct read of `src/systems/world_systems/harvesting.py:11-12` (`entity_updates
= {}`, `node_updates = {}` — both re-initialized empty on every call) and lines 64-79 (the only
code in the entire function that ever writes to `node_updates`, one entry per `node` from
`state.resource_nodes.values()`, keyed by `node.id`): `node_updates` is a plain dict local to the
call, `state.resource_nodes` is itself keyed by `id` (confirmed `src/core/state.py:1156`,
`Dict[int, CorpseState]`-shaped sibling field and the analogous `resource_nodes: Dict[int, ...]`
pattern used identically elsewhere in this file), so `state.resource_nodes.values()` yields each
distinct node id at most once per call. Therefore `current_upd = node_updates.get(node.id)` at
line 68 is evaluated exactly once per node id, always against a dict that has not yet had that key
written (nothing upstream of this loop — the entity loop at lines 15-62 — ever writes to
`node_updates`, only to `entity_updates`). **Verdict: lines 69-74 are genuinely unreachable dead
code within a single `HarvestSystem.update()` call** — there is no input state, however
constructed, that makes `current_upd` truthy on first encounter. This is not testable through the
public API without either (a) calling `update()` twice and manually re-injecting the first
return's `node_updates` as a second call's starting dict — which `update()`'s signature does not
accept as input (it only takes `state: AuthoritativeState`, confirmed line 10) — or (b)
constructing two `ResourceNodeState` entries sharing one `id` in `state.resource_nodes`, which is
itself an invalid/degenerate dict state (a `Dict[int, ResourceNodeState]` cannot hold two entries
under one key by construction) and not a genuine test of the branch's intended purpose.

Per the ticket's own Out of Scope clause ("If a new test reveals a real bug... stop and report it
rather than silently patching... file a separate ticket for any fix") and this session's
established pattern of flagging rather than fixing tangential dead-code discoveries: do **not**
force an artificial test. Instead:
1. Add one short `@pytest.mark.v2_contract` **and** `@pytest.mark.skip(reason=...)` test,
   `test_harvest_node_cooldown_merge_branch_is_unreachable`, whose skip reason cites
   `harvesting.py:68-74` and states the reachability finding in one sentence, so the gap is visible
   in `pytest -v` collection output rather than silently absent. Do not attempt to make the skip
   pass by any means (no monkeypatching internals, no colliding node ids).
2. Add one line to the ticket's `## Implementation Notes` (in
   `tickets/inprogress/TCK-20260902-HARVEST-LOOT-TEST-COVERAGE.md`) recording this as a
   **separate, tangential dead-code finding** (lines 69-74 of `harvesting.py` are unreachable
   as written) worth its own future ticket to evaluate — not something this ticket fixes, since
   fixing it would be a behavior change to `harvesting.py`, explicitly out of scope here.
**Do NOT touch:** `src/systems/world_systems/harvesting.py` — do not simplify, remove, or
"fix" the dead branch; that is a behavior change requiring its own ticket.
**Verify:** `pytest tests/unit/resource/test_harvest_channeling.py -v` shows the new test as
`SKIPPED` (not failed, not silently absent) with the reachability reason visible in `-v` output.

### Step 4 — Loot.py entity-loop skip branches
**Files:** `tests/unit/resource/test_loot_channeling.py`
**Change:** Add two new test functions, `@pytest.mark.v2_contract`, importing `LootSystem` via the
existing shim (`src.systems.loot_system`, line 7):
- `test_loot_no_interaction_or_no_target_is_skipped` — entity with no interaction / with
  `target_node_id is None`; assert no `entity_updates` entry. Verified source:
  `src/systems/economy_systems/loot.py:17-18`.
- `test_loot_skips_non_lootable_interaction_kind` — entity with `interaction.kind="harvest"` and a
  valid `target_node_id`; assert no `entity_updates` entry. Verified source:
  `src/systems/economy_systems/loot.py:20-22` (`if interaction_kind not in ["ground_item",
  "corpse"]: continue`).
**Do NOT touch:** `src/systems/economy_systems/loot.py`; existing `test_loot_channeling_completion`
and `test_loot_interruption_by_distance`.
**Verify:** `pytest tests/unit/resource/test_loot_channeling.py -v` — both new functions pass.

### Step 5 — Loot.py corpse completion path (headline gap)
**Files:** `tests/unit/resource/test_loot_channeling.py`
**Change:** Add `test_loot_corpse_completion_transfers_all_item_stacks`, `@pytest.mark.v2_contract`.
Fixture construction (no new helper needed — inline construction matches the file's existing
style, confirmed by both current tests using inline `GroundItemState(...)` at line 13/50):
- Construct `CorpseState(id=301, original_entity_id=999, position=(0, 1),
  items=[ItemStack(item_id="iron_ore", quantity=3), ItemStack(item_id="wood", quantity=2)],
  decay_tick=1000)`. All fields verified required/present at `src/core/state.py:1027-1036`
  (`id`, `original_entity_id`, `position`, `items: List[ItemStack]`, `decay_tick`,
  `generation: int = 1` — the only field with a default). Use **two distinct `ItemStack` entries**
  specifically so the test distinguishes `target.items` (the full list) from `[target.items[0]]`
  (a bug that would silently drop stacks) — per investigation.md's explicit callout that a
  single-item corpse would not catch this.
- Build entity via `V2EntityBuilder`, start the interaction via
  `LootAction.start_loot(entity, 301, "corpse", state)` (confirmed `src/actions/loot.py:9-42`
  already handles `target_kind == "corpse"` symmetrically with `"ground_item"`, resolving against
  `state.corpses`, lines 22-23).
- Drive progress for 9 ticks via `LootSystem.update(state)` + `ApplyPath.apply_generation`
  (mirroring `test_loot_channeling_completion`'s loop, lines 27-31), then a 10th tick.
- Assert directly on the raw `sys_upd` from the 10th call: `source_kind == "CORPSE"` and
  `items_add == [ItemStack("iron_ore", 3), ItemStack("wood", 2)]` (or equivalent set-based
  comparison) on `sys_upd.entity_updates[entity.id].resource_transfers[0]`. Verified source:
  `src/systems/economy_systems/loot.py:66-68` (`items_to_add = target.items; source_kind =
  "CORPSE"`).
- Then also run `AuthoritativeApplyPipeline.refine(state, sys_upd)` +
  `ApplyPath.apply_generation(...)` (mirroring lines 36-40 of the existing ground-item test) and
  assert `301 in refined.corpses_remove` and that both item stacks landed in
  `new_ent.inventory.items`.
- **Other writers to `corpses_remove` this step must account for**: `src/engine/economy.py`
  (builds `result.corpse_remove`/reservations from `intent.source_kind == "CORPSE"`, confirmed
  lines 346/350) and `src/engine/world_dynamics.py:235-244` (a *second*, independent writer that
  appends to `corpses_remove` based on corpse decay/`decay_tick` expiry, unrelated to looting).
  This test calls only `LootSystem.update()` → `AuthoritativeApplyPipeline.refine()` →
  `ApplyPath.apply_generation()` directly — it never invokes the `world_dynamics` phase — so the
  decay-based writer cannot fire in this test regardless of `decay_tick` value; `decay_tick=1000`
  is chosen only for realism/readability, not because it is load-bearing for avoiding a race. No
  ordering conflict exists between the two writers in this test's call path since only one
  (`economy.py`, via `refine()`) is ever exercised.
- Must **not** duplicate `tests/integration/kernel/test_resource_conservation.py::
  test_loot_corpse_full_inventory_does_not_remove_corpse` — that test asserts the
  inventory-full-rejection path; this new test asserts the happy-path completion shape and must
  use an entity with ordinary (non-full) inventory capacity, matching the existing
  `test_loot_channeling_completion` precedent exactly.
**Do NOT touch:** `src/systems/economy_systems/loot.py`;
`tests/integration/kernel/test_resource_conservation.py` (read-only reference only).
**Verify:** `pytest tests/unit/resource/test_loot_channeling.py -v` — new test passes; then
`pytest tests/integration/kernel/test_resource_conservation.py -v` — unchanged, still passes (no
regression from this addition since no shared file is modified).

### Step 6 — Loot.py reset-on-target-gone (ground_item and corpse)
**Files:** `tests/unit/resource/test_loot_channeling.py`
**Change:** Add `test_loot_resets_on_target_gone` (parametrized or two functions) covering: (a)
`interaction.kind="ground_item"` with `target_node_id` absent from `state.ground_items`; (b)
`interaction.kind="corpse"` with `target_node_id` absent from `state.corpses`. Both should assert
`entity_updates[entity.id].interaction.reset is True`. Verified source:
`src/systems/economy_systems/loot.py:27-41` (`target_pos = None` unless the target lookup
succeeds; `if not target_pos: reset`).
**Do NOT touch:** `src/systems/economy_systems/loot.py`.
**Verify:** `pytest tests/unit/resource/test_loot_channeling.py -v` — new test(s) pass.

### Step 7 — Loot.py distance-interruption for the corpse variant
**Files:** `tests/unit/resource/test_loot_channeling.py`
**Change:** Add `test_loot_corpse_interruption_by_distance`, mirroring the existing
`test_loot_interruption_by_distance` (lines 48-74) exactly in structure, but with a `CorpseState`
target and `kind="corpse"` instead of `GroundItemState`/`"ground_item"`: start the interaction
close, move the entity away (`new_position=(10, 10)`), call `LootSystem.update(state)`, assert
`reset is True`, apply the update, and assert the corpse remains in `state.corpses` afterward
(mirrors the sibling assertion `101 in final_state.ground_items` at line 74). Verified source:
`src/systems/economy_systems/loot.py:43-50` (distance check applies identically regardless of
`interaction_kind`, since `target_pos` was already resolved generically at lines 27-33).
**Do NOT touch:** `src/systems/economy_systems/loot.py`.
**Verify:** `pytest tests/unit/resource/test_loot_channeling.py -v` — new test passes.

## Bonus Scope Item — TOWN-009 / TOWN-010 Parity Ledger `test_path` Repair: DECLINED

Read directly for this decision: `docs/parity_ledger/town_resource.yaml:94-116` (TOWN-009,
TOWN-010 entries) and `src/engine/interaction.py:1-196` (`InteractionSystem.enforce`).

Findings:
- `src/engine/interaction.py:1` carries the file-level compliance header `# Compliance IDs:
  TOWN-005, TOWN-010, TOWN-020` — `InteractionSystem` is explicitly source-tagged as (one of) the
  implementor(s) of TOWN-010.
- `src/systems/world_systems/harvesting.py:1` carries `# Compliance IDs: TOWN-073` — **not**
  TOWN-010. No line in `harvesting.py` carries a `TOWN-010` logic-ID comment anywhere in the file
  (confirmed by full-file read in this planning pass). `harvesting.py`'s own completion check uses
  `entity.identity.properties.get("harvest_duration", 10.0)` (line 43) as the required-ticks value,
  whereas `InteractionSystem.enforce`'s TOWN-010-tagged mechanism (line 112,
  `required_ticks = node.required_ticks if node else 10`) uses a *different* value source
  (`node.required_ticks`, not the entity's `harvest_duration` property). These are not the same
  mechanism, and TOWN-010's `v2_evidence` text ("`InteractionSystem.enforce` checks `new_progress
  >= node.required_ticks`") describes the `interaction.py` mechanism specifically, not
  `harvesting.py`'s. Repointing TOWN-010's `test_path` at this ticket's new `HarvestSystem` tests
  would misattribute evidence to a module the ledger does not cite and whose completion condition
  materially differs from what `v2_evidence` describes.
- `src/systems/economy_systems/loot.py:1` **does** carry `# Compliance IDs: TOWN-009`, and the file
  carries two in-body `Logic ID: TOWN-009` comments (lines 53, 59) directly on the progress-advance
  and completion-intent code this ticket's new tests exercise. So `LootSystem.update()` is a
  legitimate, source-tagged *partial* implementor of TOWN-009. However, TOWN-009's ledger text
  ("channeled state with progress, **interruption**, and completion semantics") also depends on
  interruption/capacity logic that lives only in `InteractionSystem.enforce`
  (`interaction.py:58-89` movement/damage-triggered reset, `interaction.py:114-129` the capacity
  check gating completion) — none of which this ticket's `LootSystem`-only unit tests touch or
  prove. Repointing TOWN-009's `test_path` solely to `test_loot_channeling.py` would therefore
  still be a knowingly incomplete evidence repoint, not a full restoration of the claim as written.

**Decision: do not perform the TOWN-009/TOWN-010 bonus repair in this ticket.** Both entries'
mismatch with this ticket's tested modules is real and non-trivial (a genuinely different
mechanism for TOWN-010, and only partial coverage for TOWN-009), not a mechanical "point at the
right file" fix. Per the ticket's own Scope framing ("not required... do it only if it doesn't
expand scope meaningfully") and Risks section ("if this turns out non-trivial, the correct call is
to skip the bonus, not expand it"), this crosses that threshold. **Do not edit
`docs/parity_ledger/town_resource.yaml` in this ticket.** Record this finding in the ticket's
`## Implementation Notes` and recommend a separate future ticket scoped to properly resolving
TOWN-009/TOWN-010 (likely requiring either new `InteractionSystem.enforce`-targeted tests or a
ledger text/evidence revision to accurately describe both layers) — flag, do not fix, matching
this session's established pattern for tangential findings.

## Scope Guards

- Do not modify `src/systems/world_systems/harvesting.py` or `src/systems/economy_systems/loot.py`
  in any way — both must remain byte-for-byte unmodified (`git diff --stat` on both must show no
  output before closing the ticket).
- Do not create any new test file or module — all ten new test functions go into the two existing
  files only.
- Do not modify `tests/integration/kernel/test_resource_conservation.py` or
  `test_resource_conservation_v2.py`. No genuine duplicate was found during this planning pass (the
  new corpse-completion test in Step 5 is complementary to, not a restatement of, the existing
  full-inventory-rejection integration test) — **no trimming is needed**, contrary to the
  possibility the ticket left open.
- Do not migrate any import from the shim paths (`src.systems.harvest_system`,
  `src.systems.loot_system`) to the canonical module paths — every new test imports via the same
  shims the existing tests already use.
- Do not attempt to make the Step 3 skip-test "pass" by any means (monkeypatching, colliding node
  ids, or altering `update()`'s signature) — it is meant to stay `SKIPPED`, documenting a finding,
  not to become a green test.
- Do not edit `docs/parity_ledger/town_resource.yaml` — the bonus item is explicitly declined (see
  above).
- Every new test function must carry `@pytest.mark.v2_contract` (Step 3's skip-test carries both
  `@pytest.mark.v2_contract` and `@pytest.mark.skip`).

## Dependency Map

All seven steps are independent of one another (each adds isolated test function(s) to one of two
files; none depends on another step's test output). Suggested execution order matches the step
numbering only for readability/reviewability, not because of any technical dependency. Step 3 has
no dependency on Steps 1-2 beyond living in the same file. Steps 4-7 have no dependency on Steps
1-3 (different file). The final full-file verification (`pytest tests/unit/resource/
test_harvest_channeling.py tests/unit/resource/test_loot_channeling.py -v`) should run only after
all seven steps are complete, per the Acceptance Criteria's combined-run requirement.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| harvest (a) no-interaction/no-target skip | Step 1 | `test_harvest_no_interaction_or_no_target_is_skipped` |
| harvest (b) non-"harvest" kind skip | Step 1 | `test_harvest_skips_non_harvest_interaction_kind` |
| harvest (c) reset-on-missing-or-depleted node | Step 2 | `test_harvest_resets_on_missing_or_depleted_node` |
| harvest (d) reset-on-distance | Step 2 | `test_harvest_resets_on_distance` |
| harvest (e) node-cooldown merge branch | Step 3 (resolved: documented as unreachable, not tested as passing behavior) | `test_harvest_node_cooldown_merge_branch_is_unreachable` (SKIPPED, with cited reason) |
| loot (a) no-interaction/no-target skip | Step 4 | `test_loot_no_interaction_or_no_target_is_skipped` |
| loot (b) non-"ground_item"/"corpse" kind skip | Step 4 | `test_loot_skips_non_lootable_interaction_kind` |
| loot (c) full corpse-looting completion path | Step 5 | `test_loot_corpse_completion_transfers_all_item_stacks` |
| loot (d) reset-on-target-gone | Step 6 | `test_loot_resets_on_target_gone` |
| loot (e) distance-interruption for corpse | Step 7 | `test_loot_corpse_interruption_by_distance` |
| All new + existing tests in both files pass | Steps 1-7 | `pytest tests/unit/resource/test_harvest_channeling.py tests/unit/resource/test_loot_channeling.py -v` |
| No integration regression | Steps 1-7 (no shared file touched) | `pytest tests/integration/kernel/test_resource_conservation.py tests/integration/kernel/test_resource_conservation_v2.py -v` |
| `harvesting.py`/`loot.py` byte-for-byte unmodified | Scope Guards (all steps) | `git diff --stat src/systems/world_systems/harvesting.py src/systems/economy_systems/loot.py` shows no output |
| Bonus: TOWN-009/TOWN-010 `test_path` repair | Declined — see "Bonus Scope Item" section | N/A (not attempted; finding recorded in ticket's Implementation Notes) |

## Anti-Drift Notes

- **Node-cooldown branch (harvesting.py:69-74) is confirmed dead code within a single
  `HarvestSystem.update()` call** — do not write a test that claims to exercise it via any indirect
  or artificial means; the Step 3 skip-test is the correct and complete treatment.
- **TOWN-009/TOWN-010 bonus is declined with cited evidence**, not silently dropped — the finding
  (real mechanism mismatch for TOWN-010, partial-only coverage for TOWN-009) belongs in the
  ticket's Implementation Notes as a recommendation for a future, separately-scoped ticket.
- **Corpse fixture needs no new test helper** — construct `CorpseState` inline exactly as
  `GroundItemState`/`ResourceNodeState` are already constructed inline in both files; introducing a
  shared builder/helper function would itself be new-file/new-abstraction scope creep not requested
  by the ticket.
- **Two distinct `ItemStack` entries are required** in the corpse completion test's `items` list —
  a single-stack corpse would not distinguish `target.items` (correct, full transfer) from
  `[target.items[0]]` (a latent bug that would silently drop stacks), per investigation.md's
  explicit callout.
- **If any new test throws an unexpected exception or produces an unexpected value** (e.g. the
  corpse-completion path behaves differently than the ground-item path in some untested way): stop,
  do not patch `loot.py`/`harvesting.py` to make the test pass, and report it — this triggers the
  ticket's Out of Scope "real bug found" clause requiring a separate ticket.
- **Keep the corpse-completion test's entity inventory unconstrained (non-full)** — the
  full-inventory-rejection case for corpses is already owned by
  `test_loot_corpse_full_inventory_does_not_remove_corpse` in the integration suite; duplicating
  that assertion here would violate the no-duplication test policy.

## Deviations

- **Step 2 (`test_harvest_resets_on_missing_or_depleted_node`) and Step 6
  (`test_loot_resets_on_target_gone`)**: implemented as two separate, distinctly-named test
  functions each, rather than one function per the plan's suggested single name (Step 2:
  `test_harvest_resets_on_missing_node` / `test_harvest_resets_on_depleted_node`; Step 6:
  `test_loot_resets_on_ground_item_gone` / `test_loot_resets_on_corpse_gone`). This matches the
  plan's own explicitly stated allowance ("either two `@pytest.mark.parametrize` cases or two
  functions") — noted here only because the exact function names in the plan's text were not
  literally reused. No coverage, assertion, or scope difference from the plan's intent.
- No other deviations. All ten test functions/cases described in Steps 1-7 were implemented as
  specified; Step 3's skip-test and the Bonus decline were both followed exactly as planned. No
  trimming of `tests/integration/kernel/test_resource_conservation*.py` was needed, confirming the
  plan's own "no trimming is needed" call under Scope Guards.

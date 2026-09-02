---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260902-HARVEST-LOOT-TEST-COVERAGE
artifact_type: investigation
tags: [testing, economy]
---

# Investigation — TCK-20260902-HARVEST-LOOT-TEST-COVERAGE

## Current Behavior

### `HarvestSystem.update()` — `src/systems/world_systems/harvesting.py`

`HarvestSystem.update(state)` (staticmethod, lines 9-84) has two loops: an entity loop
(lines 15-62) and a node-cooldown loop (lines 65-79).

Entity loop branches:
- **Lines 16-17** — `if not entity.interaction or entity.interaction.target_node_id is None: continue`.
  No-interaction / no-target skip. **Untested** — no existing test constructs an entity with
  `interaction=None` or `target_node_id=None` and asserts it produces no `entity_updates` entry.
- **Lines 19-20** — `if entity.interaction.kind != "harvest": continue`. Wrong-kind skip (e.g. an
  entity mid-loot, `kind="ground_item"` or `"corpse"`, should not be touched by `HarvestSystem`).
  **Untested.**
- **Lines 26-31** — `if not node or node.remaining_charges <= 0:` → `EntityUpdate` with
  `InteractionUpdate(reset=True)`, then `continue`. Reset-on-missing-or-depleted-target.
  **Untested** — `test_harvest_node_cooldown` (lines 55-79 of
  `tests/unit/resource/test_harvest_channeling.py`) constructs a depleted node
  (`remaining_charges=0`) but never gives any entity an `interaction` targeting it, so this branch
  is never entered by that test. No test currently drives an entity with a live `harvest`
  interaction whose target node is missing from `state.resource_nodes` or has
  `remaining_charges <= 0`.
- **Lines 33-39** — Manhattan-distance proximity check (`dist > 1.5` → reset). **Untested for
  HarvestSystem specifically.** The equivalent distance-interruption branch *is* tested for
  `LootSystem` (`test_loot_interruption_by_distance`), but no analogous test exists for
  `HarvestSystem`.
- **Lines 41-57** — Completion branch (`new_progress >= required` → `ResourceTransferIntent` with
  `source_kind="NODE"`, `transfer_kind="HARVEST"`). Covered by
  `test_harvest_channeling_and_yield` (drives 10 ticks to completion).
- **Lines 58-62** — Non-completion progress-increment branch (`else`). Covered by the same test's
  9-tick loop (lines 30-34) — `sys_upd.node_updates` asserted empty, so `entity_updates` progress
  path is implicitly exercised (though not directly asserted; acceptable, matches `EntityUpdate`
  shape indirectly).

Node-cooldown loop branches (lines 65-79):
- **Line 66** — `if node.cooldown_remaining > 0:` guard. Covered (`test_harvest_node_cooldown`
  sets `cooldown_remaining=1`).
- **Lines 69-74 — the `if current_upd:` merge branch.** This only fires when two different nodes'
  cooldown updates collide in `node_updates` under the same key, which structurally requires two
  resource nodes sharing the same `id` — or, more precisely per the loop shape, requires
  `node_updates.get(node.id)` to already be populated before this node is processed. Since
  `node_updates` is keyed by `node.id` and each `node` in `state.resource_nodes.values()` has a
  distinct id, this branch is **only reachable if `node_updates[node.id]` was already set by
  something upstream of this loop within the same `update()` call** — inspection shows nothing
  upstream populates `node_updates` before this loop (the entity loop only writes
  `entity_updates`), so as currently written **lines 69-74 are dead code within a single
  `HarvestSystem.update()` call** — no combination of input state can reach `current_upd` being
  truthy on first encounter of a given `node.id`, because `node_updates` starts empty and is only
  ever added to within this same loop, one node at a time keyed by unique `node.id`. Flagging as a
  **gap** in the ticket's premise, not a blocker: see Risks and Open Questions — the planner should
  decide whether to test this via a synthetic call pattern (e.g. directly constructing a
  `node_updates` dict — not possible without modifying `update()`'s signature) or accept it as
  effectively unreachable and document that finding instead of writing a test that can't actually
  hit the branch through `HarvestSystem.update()`'s public API. (No behavior change is in scope, so
  this is a test-design question, not a code fix.)
- **Lines 75-79** — the no-existing-update `else` branch. Covered (`test_harvest_node_cooldown`).

### `LootSystem.update()` — `src/systems/economy_systems/loot.py`

Single entity loop (lines 16-86).

- **Lines 17-18** — `if not entity.interaction or entity.interaction.target_node_id is None:
  continue`. No-interaction / no-target skip. **Untested.**
- **Lines 20-22** — `if interaction_kind not in ["ground_item", "corpse"]: continue`. Wrong-kind
  skip (e.g. `kind="harvest"` entity should not be touched by `LootSystem`). **Untested.**
- **Lines 27-33** — target lookup branching on `interaction_kind` (`state.ground_items.get` vs.
  `state.corpses.get`). The `ground_item` branch is exercised by
  `test_loot_channeling_completion`/`test_loot_interruption_by_distance`; the `corpse` branch
  (line 32-33) is **never exercised by any unit test** in `test_loot_channeling.py`. It is
  indirectly touched by `tests/integration/kernel/test_resource_conservation.py::
  test_loot_corpse_full_inventory_does_not_remove_corpse`, but that test drives the
  inventory-full/refine-rejection path (`AuthoritativeApplyPipeline.refine`'s conservation check),
  not `LootSystem.update()`'s own completion logic in isolation, and uses only a single-item
  corpse.
- **Lines 35-41** — `if not target_pos: reset`. Target-gone branch (ground item or corpse missing
  from state, e.g. already looted by another entity same-tick or despawned).  **Untested** — no
  test constructs an entity interacting with a `target_node_id` that has no corresponding entry in
  `state.ground_items` / `state.corpses`.
- **Lines 44-50** — distance-interruption. Covered for `ground_item`
  (`test_loot_interruption_by_distance`); **untested for the `corpse` variant.**
- **Lines 58-80** — completion branch. `items_to_add`/`source_kind` branches on
  `interaction_kind`:
  - `ground_item` branch (lines 63-65): covered by `test_loot_channeling_completion`.
  - `corpse` branch (lines 66-68): `items_to_add = target.items` (multi-stack list directly from
    `CorpseState.items: List[ItemStack]`), `source_kind = "CORPSE"`. **Entirely untested at the
    unit level** — this is the Scope's headline finding. `CorpseState` (src/core/state.py:1028-
    1038) natively supports multiple `ItemStack` entries in `items`, so a proper test should use
    ≥2 stacks to prove the full list transfers, not just a single item (which would not
    distinguish `target.items` from `[target.items[0]]`).
- **Lines 81-86** — non-completion progress-increment `else` branch. Covered indirectly by the
  9-tick loops in both existing tests (not directly asserted on `EntityUpdate` shape, same pattern
  as `HarvestSystem`'s equivalent branch — acceptable).

### Return values
`HarvestSystem.update()` returns `StateUpdate(entity_updates=..., node_updates=...)`.
`LootSystem.update()` returns `StateUpdate(entity_updates=..., ground_items_remove=[],
corpses_remove=[])` — note `ground_items_remove`/`corpses_remove` are **always empty lists** as
built by `LootSystem.update()` itself; actual removal happens downstream in
`AuthoritativeApplyPipeline.refine()` (confirmed via `test_loot_channeling_completion`, which
asserts `101 in refined.ground_items_remove` only after calling `AuthoritativeApplyPipeline.refine`,
not on the raw `LootSystem.update()` output). Any new corpse-completion test should follow the same
pattern: assert on the raw `sys_upd.entity_updates[...].resource_transfers` shape directly (cheaper,
tests `LootSystem.update()` in isolation) and/or through `refine()` if asserting `corpses_remove`
membership, mirroring the ground-item precedent.

## Mechanics / Engine Constraints

- **`docs/mechanics/03_economic_laws.md` §3 "Resource Harvesting"**: node charges decrement per
  harvest tick; depletion removes the node from active harvesting until regeneration. This governs
  the `remaining_charges <= 0` reset branch (harvesting.py:26) and the node-cooldown decrement loop
  (harvesting.py:65-79) — the new tests must respect this law's shape (single-charge-loss-per-tick,
  not per-test-invented values) but do not need to re-prove it; that's already covered by
  `test_harvest_channeling_and_yield`.
- **`docs/mechanics/03_economic_laws.md` §1 "Atomic Conservation Law"**: source/sink balance for
  transfers. This law is enforced by `AuthoritativeApplyPipeline.refine()`, not by
  `HarvestSystem.update()`/`LootSystem.update()` themselves (which only emit *proposed*
  `ResourceTransferIntent`s — see the "Proposed intent for refinement" comments at
  harvesting.py:46 and loot.py:60). New unit tests targeting `HarvestSystem.update()`/
  `LootSystem.update()` directly do not need to invoke `refine()` to prove correctness of the
  branch itself (as `test_loot_interruption_by_distance` already demonstrates by asserting
  directly on `sys_upd.entity_updates[1].interaction.reset`), except where a test wants to confirm
  end-to-end item transfer (corpse completion case), where following the existing
  `test_loot_channeling_completion` pattern (call `refine()` then `apply_generation()`) is
  appropriate.
- No divergence from the Mechanics Bible is implicated by this ticket — this is test-authoring
  only, confirming existing branches match already-documented law, not changing any formula.

## Docs Requiring Update

None.

This is a pure test-authoring ticket with no behavior change (`harvesting.py`/`loot.py` remain
byte-for-byte unmodified per the ticket's own Acceptance Criteria and Out of Scope). No Mechanics
Bible chapter, engine contract, or guideline doc describes behavior that is changing.

The two parity-ledger entries `TOWN-009` and `TOWN-010` (path: `docs/parity_ledger/town_resource.yaml`)
are flagged below under Parity Ledger Overlap and are the subject of the ticket's own explicitly
optional "Bonus" scope item — repointing a stale `test_path` citation is a metadata correction, not
a documentation-of-behavior update, and the ticket itself frames it as optional/non-mandatory
("not required for this ticket's core acceptance criteria... do it only if it doesn't expand scope
meaningfully"). Per the ticket's own framing this is left to the planner/implementer's discretion
and is not written as a Format 1 mandatory bullet here — see Parity Ledger Overlap below for the
detail the planner needs to make that call.

The `docs/mechanics/03_economic_laws.md` chapter (path: `docs/mechanics/03_economic_laws.md`,
under `docs/mechanics/`) is not required to change for this ticket: its harvesting/conservation
laws already accurately describe the branches being newly tested (node depletion, channeled
progress); the new tests prove existing documented behavior, they do not establish new behavior
that the chapter would need to describe.

## Parity Ledger Overlap

- **`TOWN-009`** (`docs/parity_ledger/town_resource.yaml:94-104`) — "Looting is a channeled state
  with progress, interruption, and completion semantics." `status: verified`, `priority: P0`.
  `v2_evidence` cites `src/engine/interaction.py` (`InteractionSystem.enforce` handling
  `node.kind == "LOOT"`) — **not** `src/systems/economy_systems/loot.py`/`LootSystem`, a different
  module than the one this ticket adds tests for (confirmed `src/engine/interaction.py` exists).
  `test_path` cites `` `tests_v2/parity/test_resource_interaction_parity.py` ``, which does not
  exist anywhere in this repo (confirmed: `find . -type d -name tests_v2` returns nothing). This is
  a **P0 entry with a broken `test_path`**, a genuine Mechanics-Bible-rule violation ("P0 entries
  require a passing `test_path`") independent of this ticket.
- **`TOWN-010`** (`docs/parity_ledger/town_resource.yaml:105-116`) — "Harvesting is a channeled
  state tied to nearby resource-node legality and harvest duration." Same shape: `status: verified`,
  `priority: P0`, `v2_evidence` cites `src/engine/interaction.py`
  (`InteractionSystem.enforce` checking `new_progress >= node.required_ticks`), same broken
  `test_path`.
- **Open question for the planner (see Risks below)**: both entries' `v2_evidence` names
  `src/engine/interaction.py`'s `InteractionSystem.enforce`, not `HarvestSystem`/`LootSystem`. If
  `InteractionSystem` is a distinct, still-live legality-enforcement layer (separate from the
  `HarvestSystem`/`LootSystem` progress/completion layer this ticket tests), then repointing
  `test_path` to this ticket's new `HarvestSystem`/`LootSystem` unit tests would narrow the
  entry's evidence scope rather than fully restore it — the planner should verify what
  `InteractionSystem.enforce` actually does before deciding whether the bonus fix is a clean
  `test_path` repoint or needs broader evidence-text review. This ticket's Scope explicitly caps
  the bonus fix to `test_path` repair only ("not required... do it only if low-effort"), so if this
  turns out non-trivial, the correct call is to skip the bonus, not expand it.
- **`TOWN-073`** (`docs/parity_ledger/town_resource.yaml:764-773`) — "hidden discovery from
  perception," `test_path: null`, P0. **`TOWN-074`** (lines 774-783) — "loot recovery consistency,"
  `test_path: null`, P0. Both explicitly out of scope per the ticket's own Out of Scope section —
  noted here only for completeness/traceability, no action.

## Prior Work

- **`TCK-20260425-PH6-M3-HARVEST`** (`stored_artifacts/TCK-20260425-PH6-M3-HARVEST/`) — original
  Harvest V2 implementation ticket; likely origin of `harvesting.py` and
  `test_harvest_channeling.py`.
- **`TCK-20260425-PH6-M2-LOOT`** (`stored_artifacts/TCK-20260425-PH6-M2-LOOT/`) — original Loot V2
  implementation ticket; likely origin of `loot.py` and `test_loot_channeling.py`.
- **`TCK-20260427-PHASE3-RESOURCE-CONSERVATION`** (`stored_artifacts/TCK-20260427-PHASE3-RESOURCE-CONSERVATION/`)
  — likely origin of `tests/integration/kernel/test_resource_conservation*.py`, which already
  contains a `corpse` + full-inventory test (`test_loot_corpse_full_inventory_does_not_remove_corpse`)
  but at the `refine()`-rejection layer, not the `LootSystem.update()` completion layer this ticket
  targets — complementary, not duplicative.
- **`TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION`** and **`TCK-20260831-TRUST-GATED-TEACHING`**
  (both done) — independently flagged the coverage gap during their own Test phases, both under the
  mistaken premise that no dedicated unit test file existed at all; this ticket's Scope corrected
  that premise (the files exist, only specific branches are missing).

## Risks and Open Questions

- **Node-cooldown merge branch (harvesting.py:69-74) may be unreachable through the public
  `HarvestSystem.update()` API.** As analyzed above, `node_updates` starts empty each call and is
  only populated by this same loop, one distinct `node.id` at a time — so `current_upd` can never
  be truthy on first encounter of a given node's id within a single `update()` invocation. This
  contradicts the ticket's Scope, which frames this as a directly-testable "merge branch." The
  planner must decide: (a) accept this as effectively dead code and document the finding instead of
  forcing a test that cannot reach the branch through the real API (would require either a second
  call to `update()` with `node_updates` from a prior return fed back in — but `update()` doesn't
  accept `node_updates` as input — or two nodes constructed with colliding `id` values, which is
  itself an invalid/degenerate state unlikely to be worth constructing), or (b) flag this as a real
  bug/dead-code finding per the ticket's Out of Scope clause ("If a new test reveals a real bug...
  stop and report it rather than silently patching") and report it rather than attempting to write
  an unreachable-branch test. This should be resolved during planning, not silently assumed either
  way.
- **TOWN-009/TOWN-010 evidence-module mismatch** (see Parity Ledger Overlap) — the bonus fix's
  actual effort/correctness depends on what `src/engine/interaction.py`'s `InteractionSystem`
  actually is and whether it's a superseded/parallel implementation. Not fully resolved by this
  investigation pass (out of the ticket's core scope to chase); flagging for the planner to make
  a quick low-cost judgment call rather than assuming the repoint is trivially correct.
- **No RNG/determinism concern found.** Neither `HarvestSystem.update()` nor `LootSystem.update()`
  consumes `state.seed` or any randomness — item yields are deterministic (`node.yields_item`,
  fixed quantities via `ItemStack`), and completion timing is deterministic (`progress >=
  required`). New tests do not need seeded-RNG handling; this is a non-issue.

## Anti-Drift Hazards

- **Do not touch `harvesting.py` or `loot.py`.** Acceptance criteria requires byte-for-byte
  unmodified files. If the node-cooldown merge branch turns out to be genuinely unreachable dead
  code, do not "fix" it to make it reachable — that is a behavior change requiring its own ticket.
- **Do not migrate the `src.systems.harvest_system` / `src.systems.loot_system` shim imports** to
  the canonical `src.systems.world_systems.harvesting` / `src.systems.economy_systems.loot` paths —
  explicitly out of scope; new tests should import via the same shims the existing tests use.
- **Do not duplicate the existing `test_resource_conservation*.py` corpse/full-inventory case.**
  The new corpse-completion unit test must exercise the happy-path completion (`LootSystem.update()`
  producing the correct `ResourceTransferIntent` with `source_kind="CORPSE"` and multi-stack
  `items_add`), which is a distinct concern from the existing integration test's inventory-pressure
  rejection path — these are complementary, not the same assertion, so this is not a
  no-duplication-policy violation, but a new test must not simply re-assert "corpse cannot be
  looted when inventory is full" (already owned by
  `tests/integration/kernel/test_resource_conservation.py::test_loot_corpse_full_inventory_does_not_remove_corpse`).
- **Keep new tests marked `@pytest.mark.v2_contract`**, matching both existing files' convention
  (`docs/testing/test_taxonomy.md`), not `differential`/`regression`/other markers that don't apply
  here.
- **Do not silently patch a real bug found via a new test** (e.g. if the corpse-completion path
  throws or produces wrong `items_add` when actually executed for the first time) — Out of Scope
  requires stopping and filing a separate ticket.

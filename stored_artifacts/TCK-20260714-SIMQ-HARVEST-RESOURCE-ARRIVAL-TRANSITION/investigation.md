---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION
artifact_type: investigation
tags: [simulation-quality, cognition, adventure]
---

# Investigation — TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION

## Current Behavior

### The bug, confirmed exactly as filed

`ObjectiveIntentResolver.resolve()` (`src/domains/adventure/resolver.py:23-90`) is a pure
`ObjectiveKind -> ActionIntent.kind` string lookup with **no positional/distance parameter at
all** — its signature is `resolve(entity_id: int, objective: ObjectiveState, payload:
Optional[Dict] = None)`. The `REACH_RESOURCE` branch (lines 67-69):

```python
elif objective.kind == ObjectiveKind.REACH_RESOURCE:
    # First reach, then harvest
    kind = "MOVE_TO"
```

always returns `kind = "MOVE_TO"`, regardless of whether the entity has arrived. The resulting
`ActionIntent(kind="MOVE_TO", payload={"position": target_pos, ...})` is consumed by
`ActionIntentAdapter.execute()` (`src/engine/intent/action_intent.py:111-124`), whose `MOVE_TO`
branch unconditionally returns `EntityUpdate(navigation=NavigationUpdate(target_set=intent.payload.get("position")))`
— re-issuing navigation to the same position forever. There is no harvest/interact fallback.

### The call site already computes everything needed to detect arrival — it just discards it

`TacticalDecisionSystem.evaluate_entity_intent`'s Pillar 5.1 branch has two parts in
`src/engine/tactical.py`:

1. **`REACH_LOCATION` branch (lines 213-259, unmodified, working reference pattern).**
   `target_pos, node_id, building_id = TacticalDecisionSystem._resolve_target_position(state, obj)`
   (line 215) resolves all three. `dist = |Δx| + |Δy|` (line 218) is computed via Manhattan
   distance against `entity.navigation.position`. When `dist <= 1.0` (line 219) and `node_id is
   not None` (line 220), it emits `EntityUpdate(task=TaskUpdate(work_kind_set="ENTITY_ACT",
   payload_set={"action": "INTERACT", "target_id": node_id}),
   interaction=InteractionUpdate(target_node_id=node_id, progress_delta=1))` directly — it never
   touches `ObjectiveIntentResolver` at all. When `dist > 1.0` (line 253-259), it returns a plain
   `NavigationUpdate`.

2. **The `elif` branch for every other `ObjectiveKind` (lines 260-287, added by the parent
   ticket).** This is the branch `REACH_RESOURCE` actually falls into. It **also** calls
   `_resolve_target_position(state, obj)` (line 268) — but discards `node_id`:
   `target_pos, _, _ = TacticalDecisionSystem._resolve_target_position(state, obj)`. It computes
   the same Manhattan `dist` (line 271) and, **only when `dist > 1.0`** (line 272), returns a
   direct `NavigationUpdate` — bypassing `ObjectiveIntentResolver` entirely, exactly like the
   `REACH_LOCATION` branch's en-route case. **Only when `dist <= 1.0` (arrived) or `target_pos`
   could not be resolved at all** does control fall through to lines 278-287, which call
   `ObjectiveIntentResolver.resolve()` unconditionally and hand the result to
   `ActionIntentAdapter.execute()`.

   This means **`resolve()`'s `REACH_RESOURCE -> MOVE_TO` mapping is only ever reached in
   practice when the entity has already arrived** (or when the target failed to resolve at all) —
   the "still en route" case never reaches it, because the call site's own `dist > 1.0` guard
   short-circuits first. The bug is therefore squarely in what happens on arrival, exactly as
   filed.

`_resolve_target_position` (`tactical.py:675-709`) is a generic, `ObjectiveKind`-agnostic helper —
it int-casts `obj.target`, looks it up in `state.resource_nodes` first (returning `node_id`), then
`state.buildings` (returning `building_id`). It already returns `node_id` for any objective whose
`target` resolves to a resource node, not just `REACH_LOCATION` objectives. The `elif` branch at
line 268 simply doesn't capture the value it already computes.

### `ActionIntentAdapter`'s `HARVEST_RESOURCE` dispatch is real, wired, and converges on the same completion path `REACH_LOCATION` uses

`ActionIntentAdapter.execute()` (`action_intent.py:78-84`, `:130-131`) has a `HARVEST_RESOURCE`
dispatch: it does a (currently no-op, see Risks) requirement pre-check, sets
`router_payload["action"] = "INTERACT"`, `router_payload["target_id"] = intent.target_id`, then
falls through to the shared tail (`action_intent.py:257-260`):
`ActionRouter.execute_action(entity, router_payload, ...)`. `ActionRouter.execute_action`
(`src/engine/domain/action_router.py:58-59`) routes `action == "INTERACT"` to
`CoreActions.execute_interact` (`src/engine/domain/core_actions.py:248-257`), which returns
`EntityUpdate(readiness_delta=-100.0, interaction=InteractionUpdate(target_node_id=target_id,
progress_delta=1))` — **structurally identical** to what `REACH_LOCATION`'s arrival branch builds
by hand. Both converge on the same authoritative completion path,
`InteractionSystem.enforce` (`src/engine/interaction.py:36-195`, wired into the pipeline at
`pipeline.py:272` as the `"interaction_enforcement"` phase), which accumulates
`entity.interaction.progress` tick-over-tick and, once `progress >= node.required_ticks`, auto-
builds `ResourceTransferIntent(source_id=node_id, source_kind="NODE", items_add=[ItemStack(node.yields_item,
1)], transfer_kind="AUTO")` (`interaction.py:168-173`). `ResourceTransactionSystem.resolve_all`
then resolves this into an accepted `intent_results` entry, and `event_extractor.py:326-333`
derives `resource_harvested` from any accepted result with `source_kind == "NODE"`.

**Important:** there is a second, unrelated, orphaned system — `HarvestSystem`
(`src/systems/world_systems/harvesting.py`) and its sibling `HarvestAction.start_harvest`
(`src/actions/harvest.py`) — that implements a *different* channeled-harvest mechanism gated on
`entity.identity.properties.get("interaction_kind") == "harvest"`. **Neither is wired into
`pipeline.py`** (grep confirms zero references to `HarvestSystem` or `HarvestAction` anywhere in
`src/engine/pipeline.py`, and `start_harvest` has zero callers anywhere in `src/`). This is dead
code from an earlier/alternate design. `docs/parity_ledger/town_resource.yaml`'s `TOWN-104`
("`InteractionSystem` harvest path and any standalone `HarvestSystem` path cannot diverge on
capacity rules") names this exact duplication. **Do not route the fix through `HarvestSystem` /
`HarvestAction` / `interaction_kind` property-setting — that is the wrong, unreachable path.** The
real, authoritative completion mechanism is `InteractionSystem.enforce`, and it requires nothing
beyond a plain `InteractionUpdate(target_node_id=..., progress_delta=...)` each tick — which is
exactly what both `REACH_LOCATION`'s arrival branch and the `HARVEST_RESOURCE` `ActionIntent`
dispatch already produce.

### `resolve()` has no arrival/distance awareness by construction — the call site does

Answering the ticket's explicit open question:

- `ObjectiveIntentResolver.resolve()`'s signature (`entity_id, objective, payload=None`) receives
  **no entity position**. `ObjectiveState` (`src/core/strategic.py:231-239`) does carry a
  `target_position: Optional[tuple[float, float]]` field, but it is only ever consumed passively
  (copied into `intent_payload["position"]` at `resolver.py:46-47`) — never compared against
  anything. `resolve()` also never resolves `objective.target` into a concrete node id; that
  resolution (`_resolve_target_position`) lives entirely in `tactical.py`.
- The call site (`tactical.py`'s `elif` branch, lines 260-287) **already has** `target_pos` (from
  `_resolve_target_position`), the entity's current position (`entity.navigation.position`), and
  the computed `dist` — all before it ever calls `resolve()`. It discards `node_id` (line 268)
  even though `_resolve_target_position` already returns it.
- Giving `resolve()` arrival-awareness (option a) would require adding a new parameter (or
  overloading `payload` with ad hoc keys like `"arrived"`/`"node_id"`) — but the caller would
  still have to compute `dist`/`node_id` itself and shape them into the call, so option (a) does
  not eliminate any of the caller-side work; it only relocates the `kind`-selection `if` into
  `resolve()` and couples the resolver's signature to positional/proximity concerns it does not
  otherwise have.
- Option (b) — gating at the call site, mirroring `REACH_LOCATION`'s existing `dist <= 1.0` +
  `node_id is not None` check, and building the harvest action directly (either a raw
  `TaskUpdate`/`InteractionUpdate` pair identical to `REACH_LOCATION`'s, or an
  `ActionIntent(kind="HARVEST_RESOURCE", target_id=node_id)` routed through
  `ActionIntentAdapter.execute()`) — requires only capturing `node_id` (already computed, just
  discarded) and adding one `if obj.kind == ObjectiveKind.REACH_RESOURCE and node_id is not None`
  branch before the existing fallthrough to `resolve()`. It requires **no signature change** to
  `ObjectiveIntentResolver.resolve()` and keeps the resolver a pure, position-agnostic lookup,
  consistent with its current docstring/contract and with how `REACH_LOCATION` already handles
  this exact case one branch up.

**Recommendation: option (b).** The data-flow facts make it structurally cheaper and more
consistent with the one working precedent in the codebase (`REACH_LOCATION`). The ticket's AC #3
wants the integration test to exercise `ActionIntentAdapter.execute()` through to
`event_extractor.py` — this is satisfiable either by having the call site build an
`ActionIntent(kind="HARVEST_RESOURCE", ...)` and call `ActionIntentAdapter.execute()` directly
(reusing the already-wired `HARVEST_RESOURCE` dispatch), or by testing that path in isolation the
same way `tests/integration/domains/adventure/test_harvest_to_event.py` already does for
`item_crafted` (constructs the `ActionIntent` directly in the test, independent of whether
production code happens to route through `ActionIntentAdapter` or a raw `TaskUpdate` for this
specific arrival case). Either sub-shape of (b) is viable; Plan should pick based on how much it
wants the arrival case to literally flow through `ActionIntentAdapter` in production vs. mirror
`REACH_LOCATION`'s bypass. `ObjectiveIntentResolver.resolve()`'s `REACH_RESOURCE -> MOVE_TO`
mapping can remain unchanged under option (b) — it becomes a harmless fallback for the (rare/
malformed) case where `target_pos` resolves but `node_id` does not.

## Mechanics / Engine Constraints

- `docs/mechanics/04_strategic_cognition.md` §4 "The Project Lifecycle" (lines 64-70): defines
  Directive → Project → Objective → Action. `REACH_RESOURCE` is the Objective; the fix must
  resolve it to the Action step ("Interact with [resource]") on arrival — this ticket closes
  exactly the missing Objective → Action transition the chapter's canonical example describes.
- `docs/mechanics/03_economic_laws.md` §3 "Resource Harvesting" (lines 34-72): node charges,
  depletion, `RESOURCE_DEPLETED`/`RESOURCE_RECOVERED` events, and the depletion-aware adventure
  scoring note. This governs what happens *after* a harvest action is issued
  (`InteractionSystem.enforce` / `ResourceEcologyService`) — confirmed unmodified by this
  investigation; the fix only needs to *issue* the action correctly.
- No explicit mechanics-bible section documents the `1.0`-Manhattan-distance interaction-range
  threshold itself; it is a code-level constant (`tactical.py:219`, `tactical.py:34` in
  `HarvestSystem` uses `1.5` for its own, unrelated/unwired system — do not use `1.5`, it belongs
  to the orphaned path). `1.0` is the correct value to mirror, matching the ticket's own
  assumption.

## Parity Ledger Overlap

| ID | File | Status | Priority | Relevance |
|---|---|---|---|---|
| `STRAT-246` | `strategic_cognition.yaml` (~line 2862) | verified | **P0** | Text: "Every ObjectiveKind System A or System B ... reaches real execution via ActionIntentAdapter.execute(), not just REACH_LOCATION." Its own `support_boundary` text explicitly names this exact gap as unresolved: *"ObjectiveIntentResolver's REACH_RESOURCE -> MOVE_TO mapping never transitioning to a harvest/interact action on arrival"* (line ~2062). **This is the entry the ticket asks to update.** It is P0 with an existing `test_path` (`tests/integrity/test_logic_guards.py::test_objective_intent_resolver_is_reachable_from_production_pipeline`; `tests/unit/tactical/test_objective_pursuit_coverage.py`; `tests/unit/domains/adventure/test_craft_upgrade_execution.py`; `tests/integration/domains/adventure/test_harvest_to_event.py`) — per the Authoritative Mechanics Rule, updating `v2_evidence`/`support_boundary` requires the new/updated tests to be added to this `test_path` list (or a new entry created) so the P0 backing stays a passing, real test path. |
| `STRAT-189` | `strategic_cognition.yaml` | verified | P0 | Text: "Objective derivation can create executable objectives." `test_path: null`. Flagged by the parent ticket's investigation as contradicted for `REACH_RESOURCE` (derived but not, until now, executable-on-arrival). Worth a `v2_evidence` touch-up once this ticket lands, though not explicitly required by this ticket's AC — flag for Plan. |
| `TOWN-010`, `TOWN-104`, `TOWN-114`, `TOWN-129` | `town_resource.yaml` | verified | P0/P1 | Harvest-completion mechanics (`InteractionSystem.enforce`) — confirmed by this investigation to be the correct, already-wired completion path the fix must route into. Not modified by this ticket. `TOWN-104` specifically documents the `InteractionSystem`-vs-`HarvestSystem` duplication this investigation also independently found — corroborating evidence, not new information, but worth citing in the parity update as the reason `HarvestSystem`/`HarvestAction` were correctly avoided. |

No other parity ledger file has overlapping text for this specific arrival-transition gap.

## Prior Work

- `stored_artifacts/TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP/` (parent ticket, done and
  migrated) — built the routing bridge this ticket extends. Its `investigation.md` documents the
  two-parallel-systems problem (System A/`src/domains/adventure/` vs. System B/
  `fused_strategic_pass`) and explicitly deferred this exact gap (see its Related Tickets note:
  "That ticket's Scope Guards explicitly excluded modifying `ObjectiveIntentResolver`'s internal
  mapping table"). Its `test_plan.md` established the regression-surface groups (tactical/combat,
  adventure domain, strategic cognition, architecture guard) this ticket's test plan reuses
  verbatim, since the same shared file (`tactical.py`) is touched again.
- `tests/integration/domains/adventure/test_harvest_to_event.py` — already contains a docstring
  explicitly noting *why* it tests `item_crafted` instead of `resource_harvested`: "the new
  tactical.py Pillar 5.1 branch (Step 5) resolves REACH_RESOURCE objectives to
  ObjectiveIntentResolver's unmodified MOVE_TO mapping even on arrival — closing the harvest-on-
  arrival transition is out of this ticket's scope." This file's docstring is stale once this
  ticket lands and should be updated (or left as historical context with a forward pointer) —
  flag for Plan/Implement, not a blocking issue.
- `tests/unit/tactical/test_objective_pursuit_coverage.py::test_objective_kind_reach_resource_produces_executable_action`
  (lines 96-138) — already exists and already exercises the "still en route" (`dist > 1.0`) case
  for `REACH_RESOURCE`, asserting `update.navigation.target_set == node.position`. This test
  should continue to pass unmodified after the fix (per AC #1) — it is the direct regression guard
  for "unchanged when far away."

## Risks and Open Questions

1. **Not blocking, but must be verified at Implement:** `ActionIntentAdapter`'s `HARVEST_RESOURCE`
   requirement pre-check (`action_intent.py:78-84`) does `ResourceRegistry.contains(res_id)` where
   `res_id = intent.target_id`. `ResourceRegistry` (`src/core/registries.py:85-104`) is keyed by
   resource **kind** strings (e.g. `"iron_ore"`), not resource-node integer ids. If the fix sets
   `target_id` to the node's int id (matching `REACH_LOCATION`'s `INTERACT` payload convention and
   `node_id` from `_resolve_target_position`), `ResourceRegistry.contains(node_id)` will be
   `False` and the `required_tool`/`inventory_space` requirement checks will silently no-op
   (`reqs` stays empty) rather than hard-fail. This does not block AC #3 (the completion path is
   `InteractionSystem.enforce`, which does its own independent capacity check via
   `InventoryService.can_add_items`, `interaction.py:127`), but it means the `HARVEST_RESOURCE`
   `ActionIntent` requirement-gate is currently a no-op for node-id-shaped `target_id`s regardless
   of what this ticket does — pre-existing behavior, not introduced by this fix, but worth a one-
   line note in Plan so it isn't mistaken for a new bug.
2. **Not blocking:** the ticket's Related Code Area language frames `resolver.py:67-69` as "the
   exact fix site," but this investigation's data-flow trace shows the cleanest fix (option b)
   does not require changing `resolver.py` at all — it only requires a new branch in
   `tactical.py`'s `elif` block before the existing fallthrough to `resolve()`. If Plan agrees
   with the option-(b) recommendation, `resolver.py` may end up untouched; this is not a scope
   violation of the ticket (Scope explicitly says "the exact mechanism is an implementation
   decision," Related Code Areas is descriptive of where the bug's *symptom* lives, not a mandate
   to edit that exact file) but should be called out explicitly in Plan so it isn't flagged as an
   unexplained AC gap at Verify.
3. **Not blocking, informational:** `test_harvest_to_event.py`'s docstring explicitly documents
   the current gap and should be updated once fixed (see Prior Work) — small doc-hygiene item, not
   an open question that changes scope.

No open question in this investigation blocks the implementation from proceeding to Plan.

## Anti-Drift Hazards

- **Do not route the fix through `HarvestSystem` (`src/systems/world_systems/harvesting.py`) or
  `HarvestAction.start_harvest` (`src/actions/harvest.py`).** Both are dead code — zero production
  callers, not wired into `pipeline.py`. A search for "harvest" in `src/` will surface these first
  (they have the most on-the-nose names) and it is easy to mistakenly wire the fix through them
  instead of the real path (`InteractionSystem.enforce`). `docs/parity_ledger/town_resource.yaml`'s
  `TOWN-104` entry exists specifically to flag this duplication risk.
- **Do not use the `1.5` distance threshold from `HarvestSystem.update`** (`harvesting.py:34`) —
  that belongs to the unwired system. The correct threshold is `1.0`, matching
  `REACH_LOCATION`'s `tactical.py:219`.
- **Do not modify `REACH_LOCATION`'s existing branch (`tactical.py:213-259`)** — it is the working
  reference pattern, not a component being changed. Any new branch must be added to the `elif`
  block (lines 260-287) or as a new, clearly-scoped conditional within it.
- **Do not remove or alter the `resolve()` call for other `ObjectiveKind`s.**
  `tests/integrity/test_logic_guards.py::test_objective_intent_resolver_is_reachable_from_production_pipeline`
  does a literal source-string assertion — `"ObjectiveIntentResolver.resolve" in
  inspect.getsource(TacticalDecisionSystem.evaluate_entity_intent)`. As long as the string
  literally appears somewhere in the method (true for every other non-`REACH_LOCATION`,
  non-`DEFEAT_ENEMY` `ObjectiveKind`), this guard passes regardless of whether `REACH_RESOURCE`
  specifically bypasses it — but a fix that deletes the call entirely (rather than adding a
  narrower pre-check) would break this guard.
- **Do not conflate `ActionIntent.kind == "HARVEST_RESOURCE"` (a string in
  `src/engine/intent/action_intent.py`) with `ObjectiveKind.HARVEST_RESOURCE` (an enum member in
  `src/core/strategic.py`).** They are different vocabularies. No producer anywhere emits
  `ObjectiveState(kind=ObjectiveKind.HARVEST_RESOURCE)` in production (confirmed by the parent
  ticket's investigation and re-confirmed here) — the fix does not need one; it only needs to
  construct an `ActionIntent(kind="HARVEST_RESOURCE", ...)` (or an equivalent raw
  `TaskUpdate`/`InteractionUpdate` pair) once a `REACH_RESOURCE` **Objective** has arrived.
- **Do not touch `InteractionSystem.enforce`, `ResourceEcologyService`, or the
  `RESOURCE_DEPLETED`/`RESOURCE_RECOVERED` emission logic** — explicit ticket Out of Scope,
  confirmed independently correct and already wired.
- **Full regression sweep must include `tests/unit/tactical/`, `tests/unit/combat/`,
  `tests/unit/movement/`, `tests/unit/domains/adventure/`, `tests/integration/domains/adventure/`,
  and `tests/unit/strategic/`** — `tactical.py` is shared infrastructure for combat target
  selection; a change confined to the `elif` block can still be missed by a narrowly-scoped test
  run if combat/movement suites are skipped.

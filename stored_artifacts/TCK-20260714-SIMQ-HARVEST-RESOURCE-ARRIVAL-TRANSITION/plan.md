---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION
artifact_type: plan
tags: [simulation-quality, cognition, adventure]
---

# Implementation Plan — TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION

## Summary

This plan implements **option (b) — call-site gating in `tactical.py`**, exactly as recommended
by `investigation.md`. `TacticalDecisionSystem.evaluate_entity_intent`'s Pillar 5.1 `elif` branch
(`src/engine/tactical.py:260-287`) already calls `_resolve_target_position(state, obj)` and
computes Manhattan `dist`, but discards the `node_id` that helper returns. The fix captures that
`node_id` and adds one new conditional: when `obj.kind == ObjectiveKind.REACH_RESOURCE`, `dist <=
1.0`, and `node_id is not None`, the branch builds an `ActionIntent(kind="HARVEST_RESOURCE",
target_id=node_id, ...)` and routes it through the already-wired `ActionIntentAdapter.execute()`
`HARVEST_RESOURCE` dispatch (`action_intent.py:78-84`, `:130-131`) — the same dispatch
`ActionIntentAdapter` already provides for `ObjectiveKind.HARVEST_RESOURCE` objectives, reused
here rather than duplicated. This converges on `CoreActions.execute_interact` →
`InteractionSystem.enforce` → `ResourceTransactionSystem.resolve_all` →
`event_extractor.py`'s `resource_harvested` derivation — the real, wired, authoritative
completion path (not the dead `HarvestSystem`/`HarvestAction` code).

**`ObjectiveIntentResolver.resolve()` (`src/domains/adventure/resolver.py`) is explicitly left
unmodified.** Its `REACH_RESOURCE -> MOVE_TO` mapping (lines 67-69) remains the fallback for the
rare/malformed case where `target_pos` resolves but `node_id` does not (e.g. `obj.target` doesn't
resolve to a live `resource_nodes` entry) — it is still reached in that case via the existing
fallthrough at lines 278-287, unchanged. No signature change to `resolve()`. This means the
ticket's "Related Code Areas" framing of `resolver.py:67-69` as "the exact fix site" does **not**
translate into a code change there — this is intentional (see Anti-Drift Notes), not a gap.

Three implementation-detail questions flagged by investigation are resolved directly in this
plan (none require a human decision — see Anti-Drift Notes):
1. `ActionIntentAdapter`'s `HARVEST_RESOURCE` requirement pre-check no-ops for node-id-shaped
   `target_id` (pre-existing behavior, unrelated to this fix) — left as-is, noted so it isn't
   mistaken for a new bug at Verify.
2. `resolver.py` is confirmed untouched under option (b) — stated explicitly above so it isn't
   flagged as an unexplained AC gap.
3. `test_harvest_to_event.py`'s stale docstring is updated in Step 3.

## Steps

### Step 1 — Capture `node_id` and add the `REACH_RESOURCE` arrival branch in `tactical.py`
**Files:** `src/engine/tactical.py` (Pillar 5.1 `elif` branch, lines 260-287)

**Change:** Replace the current block:

```python
elif obj and obj.kind not in (ObjectiveKind.REACH_LOCATION, ObjectiveKind.DEFEAT_ENEMY):
    target_pos = None
    if obj.target:
        target_pos, _, _ = TacticalDecisionSystem._resolve_target_position(state, obj)

    if target_pos:
        dist = abs(target_pos[0] - entity.navigation.position[0]) + abs(target_pos[1] - entity.navigation.position[1])
        if dist > 1.0:
            return EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(target_set=target_pos, movement_mode_set=MovementMode.WANDER),
            )

    from src.domains.adventure.resolver import ObjectiveIntentResolver
    from src.engine.intent.action_intent import ActionIntentAdapter

    intent = ObjectiveIntentResolver.resolve(
        entity.id, obj, payload={"position": target_pos} if target_pos else {}
    )
    updates = ActionIntentAdapter.execute(
        entity, intent, current_tick=state.tick, neighbor_view=neighbors, context=state
    )
    return updates.get(entity.id, EntityUpdate(entity_id=entity.id))
```

with:

```python
elif obj and obj.kind not in (ObjectiveKind.REACH_LOCATION, ObjectiveKind.DEFEAT_ENEMY):
    target_pos = None
    node_id = None
    if obj.target:
        target_pos, node_id, _ = TacticalDecisionSystem._resolve_target_position(state, obj)

    if target_pos:
        dist = abs(target_pos[0] - entity.navigation.position[0]) + abs(target_pos[1] - entity.navigation.position[1])
        if dist > 1.0:
            return EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(target_set=target_pos, movement_mode_set=MovementMode.WANDER),
            )
        if obj.kind == ObjectiveKind.REACH_RESOURCE and node_id is not None:
            # Arrived at the resource node: transition to a harvest/interact action
            # instead of falling through to ObjectiveIntentResolver's REACH_RESOURCE
            # -> MOVE_TO mapping (which would re-issue navigation forever).
            from src.engine.intent.action_intent import ActionIntent, ActionIntentAdapter

            harvest_intent = ActionIntent(
                kind="HARVEST_RESOURCE",
                actor_id=entity.id,
                target_id=node_id,
                source_opportunity_id=obj.id,
                reason=f"Arrived at resource node {node_id} for objective {obj.id}",
            )
            updates = ActionIntentAdapter.execute(
                entity, harvest_intent, current_tick=state.tick, neighbor_view=neighbors, context=state
            )
            return updates.get(entity.id, EntityUpdate(entity_id=entity.id))

    from src.domains.adventure.resolver import ObjectiveIntentResolver
    from src.engine.intent.action_intent import ActionIntentAdapter

    intent = ObjectiveIntentResolver.resolve(
        entity.id, obj, payload={"position": target_pos} if target_pos else {}
    )
    updates = ActionIntentAdapter.execute(
        entity, intent, current_tick=state.tick, neighbor_view=neighbors, context=state
    )
    return updates.get(entity.id, EntityUpdate(entity_id=entity.id))
```

Only two things change: (1) `_resolve_target_position`'s second return value is captured as
`node_id` instead of discarded (`_`); (2) one new `if` branch is inserted between the existing
`dist > 1.0` early-return and the existing `ObjectiveIntentResolver.resolve()` fallthrough. The
`ObjectiveIntentResolver.resolve()` call and everything below it is otherwise byte-identical to
today — it remains the path for every other `ObjectiveKind` in this `elif`, and the fallback path
for `REACH_RESOURCE` when `node_id` is `None`.

**Do NOT touch:**
- The `REACH_LOCATION` branch (`tactical.py:213-259`) — working reference pattern, not modified.
- `_resolve_target_position` itself (`tactical.py:675-709`) — already generic and correct; only
  its call-site's unpacking changes.
- `src/domains/adventure/resolver.py` — no change in this step (or this ticket).
- `ActionIntentAdapter.execute()`'s `HARVEST_RESOURCE` dispatch logic (`action_intent.py:78-84`,
  `:130-131`) — reused as-is, not modified.
- The hostile-engagement / `DEFEAT_ENEMY` branch or anything below line 287.

**Verify:**
- `tests/unit/tactical/test_objective_pursuit_coverage.py::test_objective_kind_reach_resource_produces_executable_action`
  (existing far-away case — must still pass unmodified until Step 2 extends it).
- `tests/integrity/test_logic_guards.py::test_objective_intent_resolver_is_reachable_from_production_pipeline`
  (source-string guard — still passes because the `ObjectiveIntentResolver.resolve()` call
  remains textually present in the method for the fallback path).

### Step 2 — Unit tests: explicit far-away regression guard + new arrival test
**Files:** `tests/unit/tactical/test_objective_pursuit_coverage.py`

**Change:**
1. Extend the existing `test_objective_kind_reach_resource_produces_executable_action` (lines
   96-138) with two additional assertions after the existing `update.navigation` assertion, to
   make the "no harvest fires while still far away" claim explicit (AC #1) rather than incidental:
   ```python
   assert update.task is None, (
       "REACH_RESOURCE objective fired a harvest/interact task while still > 1.0 away from the node"
   )
   assert update.interaction is None, (
       "REACH_RESOURCE objective fired an interaction update while still > 1.0 away from the node"
   )
   ```
   Do not rename the test or change its existing fixtures/positions (`_hero(1, (0.0, 0.0))`,
   node at `(50.0, 50.0)` — already far enough that `dist > 1.0`).
2. Add a new test, `test_objective_kind_reach_resource_arrival_produces_harvest_action`, in the
   same file, reusing the same node/objective/project construction pattern as the existing test
   but placing the hero at the node's position (or within 1.0 Manhattan distance of it) instead of
   `(0.0, 0.0)`. Assert:
   - `update.entity_id == 1`
   - `update.navigation is None` (or, if `ActionIntentAdapter`'s `HARVEST_RESOURCE` dispatch sets
     no navigation field, simply omit this assertion rather than assert a specific falsy value —
     check the actual `EntityUpdate` shape returned by `ActionIntentAdapter.execute()` for
     `HARVEST_RESOURCE` intents before writing the assertion)
   - `update.interaction is not None and update.interaction.target_node_id == node.id` — this is
     the direct proof that arrival produces an interact/harvest action, not another `MOVE_TO`.

**Do NOT touch:**
- `test_objective_kind_acquire_item_produces_executable_action` — unrelated `ObjectiveKind`, must
  not regress or be renamed.
- Any other test file in `tests/unit/tactical/`, `tests/unit/combat/`, or `tests/unit/movement/`.

**Verify:** `pytest tests/unit/tactical/test_objective_pursuit_coverage.py -v`

### Step 3 — Integration test proving a real `resource_harvested` event, and docstring cleanup
**Files:** `tests/integration/domains/adventure/test_harvest_to_event.py`

**Change:**
1. Add a new test function,
   `test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline`, mirroring
   the existing `test_crafting_project_produces_item_crafted_event_through_full_pipeline`'s
   structure but exercising the `InteractionSystem.enforce` phase (which the crafting test does
   not need, since `REQUEST_CRAFT` bypasses it). Concrete steps for the test body:
   - Build a hero (`V2EntityBuilder`) with enough free inventory space to receive one item
     (`InventoryService.can_add_items` is checked by `InteractionSystem.enforce`).
   - Build a `ResourceNodeState(id=..., kind=..., position=..., yields_item=..., remaining_charges=1,
     max_charges=1, required_ticks=1)` — `required_ticks=1` so a single `progress_delta=1` tick
     completes the harvest within the test, matching how the existing `item_crafted` test stays
     single-step (per `test_plan.md`'s guidance).
   - `state = AuthoritativeState(tick=10, seed=1, entities={hero.id: hero}, resource_nodes={node.id: node})`
   - `ActionIntentAdapter.clear_traces()`; build
     `intent = ActionIntent(kind="HARVEST_RESOURCE", actor_id=hero.id, target_id=node.id, reason="integration test harvest")`.
   - `adapter_updates = ActionIntentAdapter.execute(hero, intent, current_tick=state.tick, context=state)`
     — this is the same call `CoreActions.execute_interact` produces via the `ActionRouter`,
     yielding an `EntityUpdate(interaction=InteractionUpdate(target_node_id=node.id, progress_delta=1), ...)`.
   - `update = StateUpdate(entity_updates=adapter_updates)`
   - `refined_update = InteractionSystem.enforce(state, update)` — the phase the crafting test
     does not exercise; this is what turns the raw `InteractionUpdate` into a
     `ResourceTransferIntent(source_kind="NODE", ...)` once `progress >= required_ticks`.
   - `resolved_update = ResourceTransactionSystem.resolve_all(state, refined_update)`
   - `EventExtractor.reset_run_state(); events = EventExtractor.extract(state, state, resolved_update, mode=ObservabilityMode.LIGHT)`
   - `assert "resource_harvested" in {e.event_type for e in events}`
   - New imports needed at module top: `from src.core.state import ResourceNodeState` (alongside
     the existing `AuthoritativeState, ItemStack` import) and `from src.engine.interaction import
     InteractionSystem`.
2. Update the module docstring (lines 1-24): remove the paragraph explaining that
   `item_crafted` is used "because ... closing the harvest-on-arrival transition is out of this
   ticket's scope" — replace with a short note that `resource_harvested` is now covered by the
   new test added by `TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION`, and that
   `item_crafted` remains as the original, still-valid proof for the `REQUEST_CRAFT` path.

**Do NOT touch:**
- `test_crafting_project_produces_item_crafted_event_through_full_pipeline` itself — leave its
  body unmodified; only the module docstring above it changes.

**Verify:** `pytest tests/integration/domains/adventure/test_harvest_to_event.py -v`

### Step 4 — Full regression sweep (verification only, no further code changes)
**Files:** none (test-only step; only add a new test if the sweep reveals a real gap per the
conditional note below)

**Change:** Run every command listed in `test_plan.md`'s "Scoped Pytest Commands" section:
```bash
pytest tests/unit/tactical/ tests/unit/combat/ tests/unit/movement/ -v
pytest tests/unit/domains/adventure/ tests/integration/domains/adventure/ -v
pytest tests/unit/strategic/test_strategic_cognition_regression.py tests/unit/strategic/test_cognition_authoritative_path.py tests/integration/pipeline/test_strategic_cadence.py -v
pytest tests/perf/test_phase3_adventure_decision_budget.py -v
pytest tests/integrity/test_logic_guards.py -v
```
All must pass unmodified (this is AC #4 and AC #5). **Conditional addendum:** if this sweep shows
no existing test asserts that `REACH_LOCATION`'s arrival `EntityUpdate` shape
(`tactical.py:213-259`) is unchanged before/after Step 1 — i.e., no test would fail if that branch
were accidentally touched — add `test_reach_location_arrival_behavior_unchanged` to
`tests/unit/tactical/test_objective_pursuit_coverage.py` (per `test_plan.md` item 5), asserting a
byte-identical `EntityUpdate` for both the node-target (`INTERACT`) and building-target
(`EAT`/`REST`) cases. Skip adding it if coverage already exists — do not add a redundant test.

**Do NOT touch:** Do not run `pytest tests/` repo-wide. Do not narrow scope to only
`tests/unit/tactical/`.

**Verify:** All commands above exit 0.

### Step 5 — Update parity ledger `STRAT-246`
**Files:** `docs/parity_ledger/strategic_cognition.yaml` (entry at ~line 2862)

**Change:**
- `test_path`: append the two new tests from Steps 2-3 to the existing pipe-delimited list,
  keeping all four existing entries:
  ```
  tests/integrity/test_logic_guards.py::test_objective_intent_resolver_is_reachable_from_production_pipeline;
  tests/unit/tactical/test_objective_pursuit_coverage.py;
  tests/unit/domains/adventure/test_craft_upgrade_execution.py;
  tests/integration/domains/adventure/test_harvest_to_event.py
  ```
  (the last two entries already implicitly cover the new tests added in Steps 2-3 since they are
  file-level references, not test-function-level — confirm this is still accurate; if the ledger's
  convention elsewhere uses function-level references, add the two new test function names
  explicitly instead).
- `support_boundary`: the current text lists three out-of-scope contributing factors and says
  factor (3) — "`ObjectiveIntentResolver.resolve()` maps `REACH_RESOURCE` to `MOVE_TO`
  unconditionally, including on arrival ... Factor (3) ... is filed as a direct follow-up:
  `TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION (open)`" — update this to state factor
  (3) is now **closed** by this ticket (reference it as done, not open), describe the actual fix
  (call-site gating in `tactical.py`'s Pillar 5.1 branch, per Step 1), and note that factors (1)
  and (2) remain open/out-of-scope exactly as before (do not touch that language).
- `v2_evidence`: append a short paragraph describing the Step 1 fix (capturing `node_id`, the new
  `dist <= 1.0` + `node_id is not None` branch, routing through `ActionIntentAdapter`'s existing
  `HARVEST_RESOURCE` dispatch) so the entry's evidence trail matches its `support_boundary` update.

**Do NOT touch:**
- `STRAT-189` — investigation flagged it as an optional touch-up, not required by this ticket's
  AC. Leave unmodified in this plan (see Scope Guards).
- `TOWN-010`, `TOWN-104`, `TOWN-114`, `TOWN-129` (`town_resource.yaml`) — unmodified, harvest-
  completion mechanics untouched.
- Any other `STRAT-*` entry.

**Verify:** Re-run the full `STRAT-246` `test_path` list (all four existing tests plus the two new
ones from Steps 2-3) and confirm all pass. No automated parity-schema validator is required beyond
this, but confirm the YAML still parses (`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/strategic_cognition.yaml'))"`).

## Scope Guards

- Do not modify `ObjectiveIntentResolver.resolve()` (`src/domains/adventure/resolver.py`) — its
  `REACH_RESOURCE -> MOVE_TO` mapping stays exactly as-is, serving as the fallback for
  unresolvable `node_id` cases.
- Do not route the fix through `HarvestSystem` (`src/systems/world_systems/harvesting.py`) or
  `HarvestAction.start_harvest` (`src/actions/harvest.py`) — both are dead code, zero production
  callers, not wired into `pipeline.py`. Do not add `entity.identity.properties["interaction_kind"]`
  anywhere.
- Do not use the `1.5` distance threshold from `HarvestSystem.update` (`harvesting.py:34`) — use
  `1.0`, matching `REACH_LOCATION`'s existing `tactical.py:219` threshold, which Step 1 already
  reuses via the shared `dist` computation.
- Do not modify `REACH_LOCATION`'s branch (`tactical.py:213-259`) in any way.
- Do not modify `ActionIntentAdapter`'s `HARVEST_RESOURCE` dispatch logic, requirement pre-check,
  or any other dispatch branch (`REQUEST_CRAFT`, `BUY_ITEM`, `MOVE_TO`, etc.) in
  `action_intent.py` — reused as-is.
- Do not touch `InteractionSystem.enforce`, `ResourceEcologyService`, or
  `RESOURCE_DEPLETED`/`RESOURCE_RECOVERED` emission logic — explicit ticket Out of Scope.
- Do not change `ENABLE_ADVENTURE_ROUTING`'s default or any calibration profile YAML
  (`config/simulation_quality/profiles/*.yaml`) — separate, independently-scoped question per the
  ticket's Out of Scope.
- Do not touch `AdventureRouteScorer`'s selection weighting — separate calibration/scoring
  question, explicitly out of scope.
- Do not add a new `ObjectiveKind.HARVEST_RESOURCE`-kind `ObjectiveState` producer anywhere — no
  producer emits this enum member today and this ticket does not need one; the fix operates
  entirely on `REACH_RESOURCE` objectives at arrival.
- Do not modify `STRAT-189` or any parity ledger entry other than `STRAT-246`.
- Do not re-score or re-anchor any SimQ pillar based on the newly-observable `resource_harvested`
  events — explicit ticket Out of Scope, follow-on work only.

## Dependency Map

- Step 1 (tactical.py fix) has no dependencies — it is the root change.
- Step 2 (unit tests) depends on Step 1 (tests assert the new branch's behavior; cannot pass
  before Step 1 lands).
- Step 3 (integration test) is independent of Steps 1-2's code — it exercises
  `ActionIntentAdapter.execute()` + `InteractionSystem.enforce()` directly, not through
  `TacticalDecisionSystem.evaluate_entity_intent`. It can be written in parallel with Step 2, but
  should be run after Step 1 lands so the full suite is consistent.
- Step 4 (regression sweep) depends on Steps 1-3 being complete — it is the verification gate for
  all of them plus the wider regression surface.
- Step 5 (parity ledger) depends on Steps 1-4 — it documents the outcome and must cite tests that
  are confirmed passing (per Step 4) before the ledger update is written.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Entity > 1.0 away from node → unchanged `MOVE_TO`/navigation behavior | Step 1 (unchanged early-return), Step 2 (explicit assertions) | `test_objective_kind_reach_resource_produces_executable_action` (extended) |
| Entity within `dist <= 1.0` of node → harvest/interact action fires, not `MOVE_TO` | Step 1 (new branch) | `test_objective_kind_reach_resource_arrival_produces_harvest_action` (new) |
| Integration test with real pipeline proves `resource_harvested` event | Step 3 | `test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline` (new) |
| No regression to `REACH_LOCATION`, `HARVEST_RESOURCE` resolver mapping, or other `ObjectiveKind`s | Step 1 (scoped diff), Step 4 (full sweep) | All suites listed in Step 4's commands |
| `test_objective_intent_resolver_is_reachable_from_production_pipeline` still passes | Step 1 (call preserved in fallback path) | `tests/integrity/test_logic_guards.py` |
| `docs/parity_ledger/strategic_cognition.yaml`'s `STRAT-246` updated | Step 5 | Re-run of `STRAT-246`'s full `test_path` list |

## Anti-Drift Notes

- **`resolver.py` stays untouched — this is a deliberate design decision, not an oversight.**
  The ticket's "Related Code Areas" section names `resolver.py:67-69` as "the exact fix site,"
  but the investigation's data-flow trace (confirmed by re-reading both files during planning)
  shows the call site in `tactical.py` already computes `node_id` and discards it — capturing it
  is strictly cheaper than adding a new parameter to `resolve()` and duplicating the same
  distance/position logic inside the resolver. Do not "fix" `resolver.py` as a defensive measure
  — it would be dead code (the `elif` branch's new check short-circuits before `resolve()` is ever
  reached for the arrived case) and would violate the Scope Guard above.
- **Two unrelated harvest-completion systems exist in this codebase; only one is real.**
  `HarvestSystem`/`HarvestAction` (`src/systems/world_systems/harvesting.py`,
  `src/actions/harvest.py`) are unwired dead code gated on a property
  (`interaction_kind == "harvest"`) that nothing sets. A keyword search for "harvest" will surface
  these first due to naming. The real, pipeline-wired completion path is
  `InteractionSystem.enforce` (pipeline phase `"interaction_enforcement"`, `pipeline.py:272`).
  Step 1's fix produces a plain `InteractionUpdate` via `ActionIntentAdapter`/`CoreActions.
  execute_interact` — exactly what that real path expects.
- **`ActionIntent.kind == "HARVEST_RESOURCE"` (string) vs. `ObjectiveKind.HARVEST_RESOURCE`
  (enum member) are different vocabularies.** Step 1 constructs an `ActionIntent(kind=
  "HARVEST_RESOURCE", ...)` directly from within the `REACH_RESOURCE` `ObjectiveKind` arrival
  case — it does not require, and must not require, any producer to emit
  `ObjectiveState(kind=ObjectiveKind.HARVEST_RESOURCE)`. No such producer exists in production and
  none is added by this ticket.
- **`ResourceRegistry.contains(node_id)` no-ops for the `HARVEST_RESOURCE` requirement pre-check**
  (`action_intent.py:80`) because `ResourceRegistry` is keyed by resource-kind strings (e.g.
  `"iron_ore"`), not integer node ids, and Step 1's `target_id` is the node's int id (matching
  `REACH_LOCATION`'s existing `INTERACT` payload convention). This means `reqs` stays empty and
  the pre-check effectively does nothing for this path — pre-existing behavior of
  `ActionIntentAdapter`, not introduced by this fix, and not a regression: the real capacity check
  (`InventoryService.can_add_items`) still runs inside `InteractionSystem.enforce`
  (`interaction.py:127`). Do not attempt to "fix" this pre-check as part of this ticket — it is
  out of scope and orthogonal to the arrival-transition bug.
- **The `1.0` Manhattan-distance threshold is a bare code constant, not documented in the
  Mechanics Bible.** Step 1 reuses the existing `dist` computation already present in the `elif`
  block (shared with the `dist > 1.0` early return) — no new threshold is introduced.
- **`tests/integrity/test_logic_guards.py`'s reachability guard is a blunt source-string check**
  (`"ObjectiveIntentResolver.resolve" in inspect.getsource(...)`). Step 1 preserves the literal
  call in the fallback path, so this guard remains satisfied — but it does not by itself prove
  `REACH_RESOURCE`'s arrival case correctly bypasses `resolve()`; that is what the Step 2 unit test
  proves directly.
- **`STRAT-189`'s `v2_evidence` touch-up is explicitly out of scope for this plan** — investigation
  flagged it as optional, and the ticket's AC only names `STRAT-246`. If a future session wants to
  update `STRAT-189` too, it should be a separate, small follow-up, not folded into this ticket's
  commit.

## Deviations

- **Step 4 conditional addendum fired.** Grepped `tests/unit/`, `tests/unit/strategic/`, and
  `tests/unit/tactical/` for any existing test that pins `REACH_LOCATION`'s arrival `EntityUpdate`
  shape (`tactical.py:214-259`) via `TacticalDecisionSystem.evaluate_entity_intent` — none exists
  (the only two tests calling `evaluate_entity_intent` with a `REACH_LOCATION` objective either
  never set `obj.target`, so `_resolve_target_position` is never reached, or don't assert on
  `task`/`interaction` shape). Per the plan's explicit conditional instruction, added
  `test_reach_location_arrival_behavior_unchanged` to
  `tests/unit/tactical/test_objective_pursuit_coverage.py`, covering both the node-target
  (`INTERACT`) case and both building-target cases (`EAT` for a `"hunger"`-kind project, `REST`
  for `"fatigue"`) — not just the two named in the addendum's parenthetical, since both branches of
  the building-target `if/elif` sit in the same untouched code path Step 1's diff runs directly
  above.
- **Step 5 `test_path` resolution.** The plan flagged an open question — whether the two
  file-level `test_path` entries (`test_objective_pursuit_coverage.py`,
  `test_harvest_to_event.py`) already implicitly cover the new tests added in Steps 2-3, or
  whether the ledger's function-level convention elsewhere means explicit function names should be
  added instead. Found both conventions in use in `strategic_cognition.yaml` (e.g. `STRAT-078` is
  function-level). Chose to add explicit function-level entries for the two new arrival tests
  (`test_objective_kind_reach_resource_arrival_produces_harvest_action`,
  `test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline`)
  *alongside* the existing four entries (not replacing them), for direct traceability from the
  ledger entry to the exact tests that close the arrival gap.

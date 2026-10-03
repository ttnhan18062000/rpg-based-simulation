---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260824-TOWN-CENTER-POINTER-FIX
artifact_type: plan
tags: [world, determinism]
---

# Implementation Plan — TCK-20260824-TOWN-CENTER-POINTER-FIX

## Summary

`AuthoritativeState.town_center` is never set by `WorldCompiler.compile()` and silently stays at
its dataclass default `(0.0, 0.0)` for every real compiled world. This plan fixes the root cause
(Step 1), then fixes the three consumers that are *not* transitively repaired by the root-cause fix:
`FlowFieldService`'s hardcoded `ANCHORS["TOWN"]` short-circuit (Step 2), `WorkerPacket.town_center`'s
confirmed-dead duplicate field (Step 3, removed), and `StrategicRedirectionSystem.enforce()` /
`StrategicIntelligenceSystem`'s routine-blocker pass, which both discard a correct `town_center` in
favor of an arbitrary whole-world tile pick (Step 4, replaced with a shared deterministic
nearest-tile-to-entity helper). Step 5 updates the three required docs. Step 6 adds the
integration-level regression coverage and spot-checks the two behavioral baselines that exercise
`urban_political.yaml`'s real two-town-region composition. `AuthoritativeState.town_center` itself
is kept as a single-value field (see Design Decision below) — it is not deprecated or replaced with
a new lookup structure in this ticket.

## Design Decision

**`AuthoritativeState.town_center` is kept as the sole single-value pointer (Option b from the
ticket's framing), computed by `WorldCompiler.compile()` as the centroid of the first
`type == "town"` region encountered in `spec.regions` iteration order.** It is NOT deprecated,
removed, or replaced by a new nearest-town lookup method/registry in this ticket.

Rationale, citing the investigation's own evidence:

1. **The ticket's own AC #1 text requires `town_center` to remain a real, settable field**: "sets
   `AuthoritativeState.town_center` to a real value derived from the compiled town-type region(s)".
   This is satisfied by Option (b) directly. A full removal of the field would contradict this AC's
   literal wording, not just its intent.
2. **Full deprecation is far more invasive than the ticket's explicit Scope/AC list authorizes.**
   Investigation Item 2 (`staging_artifacts/TCK-20260824-TOWN-CENTER-POINTER-FIX/investigation.md`
   lines 42-73) enumerates 9 direct-read call sites beyond the 4 the ticket names in Scope/AC
   (`scorers.py`, `adventure_scorer.py`, `town_navigation.py`, `home_storage.py`, `scheduler.py`,
   plus `checkpoint.py`/`apply.py` plumbing). Migrating all of those to a new lookup API is a
   separate, larger ticket — CLAUDE.md's planner rule is explicit: "Never plan more work than the
   ticket scope. If the investigation reveals adjacent problems, note them as future tickets."
3. **The multi-town under-service problem is already functionally addressed by this ticket's own
   Step 4**, for the two systems where "which town" precision actually matters operationally
   (return-to-town navigation under load). `StrategicRedirectionSystem.enforce()` and
   `StrategicIntelligenceSystem`'s routine-blocker pass are being fixed in Step 4 to compute the
   nearest tile to the *requesting entity* directly from `state.town_tiles` — which investigation
   Item 6 confirms is already a proper multi-town-aware flat set (unioned from every `type=="town"`
   region, `src/worldbuilding/compiler.py:235-236`), not from `town_center` at all. So the AC #4 fix
   already delivers per-entity nearest-town correctness for the highest-traffic consumers, without
   needing `town_center` itself to become multi-town-aware.
4. **Remaining `town_center` consumers do not need per-entity precision today.** `TownScorer` /
   `CombatRetreatScorer` / `RecoverScorer` / `ResolveBlockerScorer` (goal scoring),
   `DeterministicScheduler.select_work()`'s LOD `focus_points`, and `FlowFieldService`'s long-range
   waypoint all currently treat "the town" as a single approximate anchor — none of them today
   compute or need a "nearest of several towns" answer; they only needed a *real* value instead of
   `(0,0)`. Centroid-of-first-town-region gives them that.
5. **Evidence considered against this choice**: investigation Item 6's `urban_political.yaml`
   evidence (two real town regions, ~35 dependent files including the regression baseline) is real
   and does mean a single-value `town_center` under-serves the second town for these remaining
   consumers specifically. This is a genuine, known limitation of Option (b), not an oversight — it
   is called out explicitly here rather than left implicit. **Follow-up (explicitly NOT part of this
   ticket, noted for a future ticket only, per CLAUDE.md's "note as future tickets" rule)**: if
   `TownScorer`/`scheduler`/`home_storage` need per-entity nearest-town precision later, add a
   `WorldCompiler`-produced per-region town-center registry or a
   `get_nearest_town_tile(state, position)` helper reusing Step 4's new shared function, and migrate
   those 9 call sites onto it.

**Derivation rule for `WorldCompiler.compile()` (Step 1)**: iterate `spec.regions` in its existing
list order (the same order already used to build `terrain`/`town_tiles`/`regions` at
`src/worldbuilding/compiler.py:211`); take the first `r_spec` where `r_spec.type == "town"`; compute
`town_center = ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)` from that region's own
`r_spec.bounds` (not a centroid of the *union* of all town tiles across regions — investigation's
Risks/Open Questions section flags that a cross-region centroid could land in the empty space
between two distant towns; a single region's own bounds centroid cannot). If no `type=="town"`
region exists in `spec.regions`, leave `town_center` unset in the constructor call so it keeps the
dataclass default `(0.0, 0.0)` — identical to today's no-town-region behavior, so this is not a
behavior change for that edge case (`town_tiles` is also empty in that case, and every downstream
`if state.town_tiles:` / `if town_tiles:` guard already no-ops correctly).

**`WorkerPacket.town_center` disposition: REMOVE the field.** Investigation Item 4's full call-graph
trace (`execute_brain` → `CognitionDomain.execute_brain` → `TacticalDecisionSystem.evaluate_entity_intent`
→ full read of `_resolve_target_position`, plus the `ENTITY_MOVE` branch not calling
`MovementSystem`/`NavigationSystem` at all) found zero real consumers. Per CLAUDE.md's Durable State
Rule ("Do not create hidden or implicit durable behavior") and the Hard Rules against unread durable
state, removing dead duplicate state that is written every tick for every dispatched work item and
never read is the correct fix — not inventing an artificial consumer just to justify keeping the
field. Verified during planning (`grep -n "town_center" tests/unit/kernel/test_worker_integrity.py
tests/unit/core/test_no_worker_direct_mutation.py tests/unit/kernel/test_worker_adaptation.py
tests/unit/kernel/test_worker_bounds.py tests/unit/kernel/test_worker_fallback.py
tests/unit/core/test_fallback_hardening.py tests/integration/kernel/test_milestone_b_closure.py
tests/integration/kernel/test_authoritative_outcome_truth.py
tests/integration/kernel/test_worker_determinism.py tests/unit/core/test_signal_hardening.py` — the
9 test files that construct `WorkerPacket(...)` besides `src/engine/executor.py` itself — found zero
matches): no test file passes `town_center=` explicitly to `WorkerPacket(...)`, so removing the
field's declaration only requires dropping the one keyword argument at
`src/engine/executor.py:321` (`town_center=state.town_center`); no test fixture needs updating. This
is a narrower blast radius than `test_plan.md`'s "Worker protocol / engine" regression-surface
section speculated (it named 3 files as needing confirmation; verified here that none actually pass
the field).

## Steps

### Step 1 — WorldCompiler.compile() derives a real town_center

**Files:** `src/worldbuilding/compiler.py`

**Change:** In `WorldCompiler.compile()`'s region-compilation loop (`compiler.py:211-252`, already
read in full during planning), after the loop completes, add a small block that scans `spec.regions`
in its existing list order for the first `r_spec` with `r_spec.type == "town"` and computes
`town_center = ((r_spec.bounds[0] + r_spec.bounds[2]) / 2.0, (r_spec.bounds[1] + r_spec.bounds[3]) / 2.0)`
(confirmed `r_spec.bounds` unpacks as `min_x, min_y, max_x, max_y` at `compiler.py:212`). If no
`type=="town"` region exists, leave the local variable unset/`None`. Then, in the final
`AuthoritativeState(...)` constructor call (`compiler.py:594-610`, confirmed by direct read — no
`town_center=` keyword present among the 15 fields currently passed), add
`town_center=town_center if town_center is not None else (0.0, 0.0)` (or omit the kwarg entirely
when `None`, relying on the dataclass default at `src/core/state.py:1129` — either is equivalent;
prefer the explicit default for readability at the call site).

**Other writers to `AuthoritativeState.town_center` (durable-state field, shared resource) and how
this step interacts with each**: `src/engine/checkpoint.py:75` and `src/engine/apply.py:385` are the
only other places that touch this field, and both are pure plumbing — `checkpoint.py` folds the
current value into the canonical-fingerprint dict (read-only), and `apply.py` carries the existing
value forward unchanged tick-to-tick via `dataclasses.replace()` (never assigns a new value itself).
Neither writes an independent value, so there is no ordering conflict, race, or double-write: this
step is the only true producer of `town_center`'s *value*, and it runs once at compile time before
the kernel loop starts (confirmed in investigation's "Docs Requiring Update" analysis — no phase
reordering needed). No other system in `src/` assigns to `state.town_center` (confirmed via the
investigation's `grep -rn "\.town_center\b" src/` sweep, Item 2 — every other hit is a read).

**Determinism**: `spec.regions` list order is itself deterministic (constructed once from
`WorldSpec`, iterated in the same fixed order the existing `terrain`/`town_tiles` loop already
relies on for determinism at `compiler.py:211`) — "first town region in declaration order" carries
no new nondeterminism. The centroid arithmetic is a pure function of that region's static `bounds`
tuple; no RNG draw is introduced (confirmed: `DeterministicRNG` at `compiler.py:198` is untouched by
this change, so `RNG` draw sequence and `StateFingerprinter` draw-count are unaffected — only the
one new `town_center` field value itself changes the fingerprint, which is expected and must be
spot-checked against baselines in Step 6, not treated as a red flag).

**Do NOT touch:** `WorldProceduralGenerator.generate()` (`src/worldgeneration/generator.py`) — its
own single-town-region carving logic is legacy, untouched, out of this ticket's scope per the
investigation's anti-drift hazards. Do not change the `terrain`/`town_tiles` loop's own logic, only
add the new town_center derivation after it.

**Verify:** `test_compile_sets_real_town_center_from_town_region` and
`test_compile_town_center_derivation_with_multiple_town_regions` (both new, per test_plan.md item
1-2), in `tests/unit/worldbuilding/test_world_compiler.py`. The multi-region test must assert the
result equals the first town region's own bounds centroid (mirroring `urban_political.yaml`'s real
shape: `frontier_village_core`'s `hometown` region, declared before `trading_company_hub`'s
`trading_hometown` region in that composition file — confirm the actual declared order in the test
fixture rather than assuming it).

### Step 2 — FlowFieldService.get_flow_direction(target_kind='TOWN') uses the real town location

**Files:** `src/systems/world_systems/navigation.py`

**Change:** In `FlowFieldService.get_flow_direction()` (`navigation.py:23-69`, read in full), the
`target_kind == "TOWN"` case must stop relying on the hardcoded `ANCHORS["TOWN"] = [(100, 100),
(200, 50)]` class-level literal (`navigation.py:18-21`) as its primary source. Change line 33's
`anchors = FlowFieldService.ANCHORS.get(target_kind, [])` behavior so that for `target_kind ==
"TOWN"` specifically, `anchors = [state.town_center]` is used directly (the same expression
currently dead at line 44), rather than falling through the hardcoded 2-waypoint list first. Concrete
approach: special-case `target_kind == "TOWN"` at the top of the function to set
`anchors = [state.town_center]` unconditionally (bypassing `ANCHORS["TOWN"]` entirely), leaving the
`ANCHORS.get(target_kind, [])` / `WORLD_BOSS` dynamic-entity fallback path (`navigation.py:33-46`)
untouched for every other `target_kind`. This makes the existing dead-code fallback at line 44
(`anchors = [state.town_center]`) live and load-bearing instead of literal dead code, and removes
`ANCHORS["TOWN"]`'s effective usage without deleting the dict entry itself (see Do NOT touch below).

**Other writers/readers of `ANCHORS`**: `ANCHORS` is a class-level literal with no other writer
anywhere in the codebase (confirmed by investigation Item 3 — "standalone hardcoded V2-hardening
scaffolding... not derived from anything"). `NavigationSystem.get_next_step()`
(`navigation.py:77-103`) is the sole caller of `get_flow_direction`, gated on
`if target_pos == state.town_center:` (line 94) — this gate is unaffected by this step's change (it
already only invokes the flow-field path when the caller's `target_pos` equals `state.town_center`,
which becomes a real value after Step 1).

**Determinism:** unaffected — `anchors = [state.town_center]` is a single fixed point per tick (same
determinism class as the current `ANCHORS["TOWN"]` literal); the existing nearest-anchor loop
(`navigation.py:51-60`) and direction-vector math are untouched.

**Do NOT touch:** `ANCHORS["WORLD_BOSS"]` and its dynamic-entity fallback branch
(`navigation.py:36-40`) — explicitly out of scope per investigation's Risks/Open Questions and the
ticket's AC, which names only `target_kind='TOWN'`. Do not delete the `ANCHORS["TOWN"]` dict entry
itself (leaving it as unused-but-present avoids touching an otherwise-untouched class attribute
declaration that other code may reference via `FlowFieldService.ANCHORS` introspection — if a repo
search during implementation finds no such reference, deleting the now-dead `"TOWN"` key is
acceptable cleanup, but is not required to satisfy the AC).

**Verify:** `test_get_flow_direction_town_uses_real_town_center_not_hardcoded_anchor` (new, per
test_plan.md item 3), in `tests/unit/movement/test_flow_field_navigation.py`, using a `town_center`
distinct from both `(100,100)` and `(200,50)` (e.g. `(300.0, 300.0)`). Also confirm
`test_flow_field_long_distance` and `test_local_navigation_fallback` (existing, same file) still
pass — `test_flow_field_long_distance`'s `town_center=(100.0,100.0)` coincidentally still equals what
was `ANCHORS["TOWN"][0]`, so its assertions remain valid under the new code path for the same reason
test_plan.md notes ("the two values will remain equal in that test's own setup").

### Step 3 — Remove WorkerPacket.town_center as confirmed dead duplicate state

**Files:** `src/core/worker_protocol.py`, `src/engine/executor.py`

**Change:** Remove the `town_center: Tuple[float, float] = (0.0, 0.0)` field declaration from
`WorkerPacket` (`src/core/worker_protocol.py:53`). Remove the corresponding
`town_center=state.town_center,` keyword argument from the `WorkerPacket(...)` construction call in
`src/engine/executor.py:321` (the sole producer, confirmed by investigation Item 4).

**Other writers/readers of `WorkerPacket.town_center`**: confirmed via full call-graph trace
(investigation Item 4, independently re-verified during planning) — `src/engine/executor.py:321` is
the only writer; there are zero readers anywhere in `src/` or `tests/` (`packet.town_center` never
appears). Verified during planning that none of the 9 test files constructing `WorkerPacket(...)`
directly (`test_worker_integrity.py`, `test_no_worker_direct_mutation.py`, `test_worker_adaptation.py`,
`test_worker_bounds.py`, `test_worker_fallback.py`, `test_fallback_hardening.py`,
`test_milestone_b_closure.py`, `test_authoritative_outcome_truth.py`, `test_worker_determinism.py`,
`test_signal_hardening.py`) pass `town_center=` explicitly — all rely on the field's default, so none
require an edit. `src/core/protocol_validator.py` was checked and contains zero references to
`town_center` — no validator logic needs updating.

**Determinism:** removing an unread field cannot affect the RNG draw sequence, tick ordering, or any
existing fingerprint (`WorkerPacket` is not part of `StateFingerprinter`'s canonical-hash input —
only `AuthoritativeState` is, per Step 1's Verify note); no determinism risk.

**Do NOT touch:** `AuthoritativeState.town_center` itself (`src/core/state.py:1129`) — this step
removes only the `WorkerPacket` duplicate field, per the Design Decision's explicit note not to
conflate the two removals. Do not touch any other `WorkerPacket` field.

**Verify:** new architecture-guard test (per test_plan.md item 4, choosing the "removed" variant
since this step removes the field): `test_worker_packet_has_no_dead_town_center_field`, asserting
`"town_center" not in {f.name for f in dataclasses.fields(WorkerPacket)}` — create in
`tests/unit/kernel/test_worker_protocol.py` (does not exist yet, confirmed during planning — create
new file). Also run the 9 existing `WorkerPacket(...)`-constructing test files listed above
unmodified to confirm none regress.

### Step 4 — StrategicRedirectionSystem.enforce() and StrategicIntelligenceSystem's routine-blocker pass pick the nearest town tile to the requesting entity

**Files:** new `src/systems/strategic_systems/town_targeting.py`, `src/systems/strategic_systems/redirection.py`, `src/systems/strategic_systems/intelligence.py`

**Change:** Add a new shared, pure helper module `src/systems/strategic_systems/town_targeting.py`
with one function:

```python
def nearest_town_tile(
    town_tiles: set[tuple[int, int]],
    position: tuple[float, float],
) -> Optional[tuple[float, float]]:
    """Deterministic nearest-tile-to-position lookup over town_tiles.
    Tie-break: lowest (x, y) among tiles at equal minimum distance."""
    if not town_tiles:
        return None
    best = min(town_tiles, key=lambda t: ((t[0] - position[0]) ** 2 + (t[1] - position[1]) ** 2, t[0], t[1]))
    return (float(best[0]), float(best[1]))
```

This is a pure function of already-deterministic inputs (`town_tiles`, `position`) with an explicit
stable tie-break (`(dist_sq, x, y)` — reuses `redirection.py`'s existing `sorted(...)` convention of
tie-breaking on raw `(x, y)` tuple order, per investigation's Determinism Rule note), satisfying the
Architecture Rule ("Decision logic reads state. It does not authoritatively mutate durable state.") —
it is read-only and feeds only into `NavigationUpdate`/`StateUpdate` construction, never a direct
mutation.

In `src/systems/strategic_systems/redirection.py`, replace lines 28-33 (`town_target =
state.town_center` / `if state.town_tiles: town_pos = sorted(list(state.town_tiles))[0]; ...`) —
this "once per tick" precomputation must move *inside* the per-entity loop (it can no longer be
computed once, since the nearest tile now depends on each entity's own position). Concretely: at the
"3. Case: Return to Town" fallback (line 129-147, the only place `town_target` is read), compute
`nearest = nearest_town_tile(state.town_tiles, entity.navigation.position)` and use
`target_coords = nearest if nearest is not None else state.town_center` in place of the old
`target_coords = town_target`.

In `src/systems/strategic_systems/intelligence.py`, replace lines 335-338
(`town_target = state.town_center` / `if not town_target and state.town_tiles: town_pos =
next(iter(state.town_tiles)); ...`) similarly: move the nearest-tile computation to the point of use
(the two "has items, return to town" fallback blocks at lines 385-394 and 620-624, both confirmed by
investigation Item 5 to have the identical shape), replacing `town_target` there with
`nearest_town_tile(state.town_tiles, entity.navigation.position) or state.town_center`.

**Other writers to `town_tiles`/`town_center` these two systems read (shared resource)**: `town_tiles`
is written once by `WorldCompiler.compile()` (Step 1's neighbor logic, `compiler.py:235-236`) and
never mutated afterward by any other system in `src/` (confirmed by investigation Item 6's resolver
trace — `WorldAssemblyResolver.assemble()` and `CompileProfileResolver.resolve()` only *read*
`type=="town"` regions to build ownership, never write back into `state.town_tiles`). `town_center`
is written only by Step 1 (compile time) and carried forward read-only by `checkpoint.py`/`apply.py`
(Step 1's "Other writers" note applies identically here). No race: both `redirection.py`'s
`enforce()` and `intelligence.py`'s routine-blocker pass run read-only against the same
already-finalized-for-this-tick `state` snapshot within the existing strategic phase ordering — this
step does not change when either system runs relative to the other or relative to `WorldCompiler`.

**Determinism:** `nearest_town_tile`'s tie-break (`dist_sq`, then `x`, then `y`) is fully
deterministic given `town_tiles` (a `set`, but the `min()` call's key function makes iteration order
irrelevant to the result — the same guarantee `sorted(...)[0]` provided before, just applied per
distance instead of globally). Entity iteration order in both files remains whatever it already was
(`redirection.py`'s `entity_ids = sorted(list(relevant_ids))` at line 41 is untouched;
`intelligence.py`'s `candidate_ids` ordering from `StrategicWorkQueue.build` is untouched) — this
step changes only what target each entity resolves to, not iteration order.

**Do NOT touch:** the "2.5. Case: Active Objective Target" and "2. Case: Blocked on Materials"
branches in `redirection.py` (lines 78-127) — unrelated to town targeting, out of scope. Do not
extend or otherwise harden `intelligence.py`'s pattern beyond swapping `next(iter(...))` for the
shared nearest-tile call — investigation Item 9 confirms this is the same bug as `redirection.py`'s,
not a separate determinism concern requiring extra hardening (ticket's own Out of Scope: "Hardening
intelligence.py's next(iter(state.town_tiles)) determinism concern beyond what's needed for the
nearest-tile fix"). Do not touch Idea 56 (Drifting Loyalty) — confirmed zero shared code path
(investigation Item 8), not referenced anywhere in these two files.

**Verify:** `test_redirection_enforce_targets_nearest_town_tile_not_arbitrary_sort`,
`test_routine_blocker_pass_targets_nearest_town_tile_not_arbitrary_iter`, and
`test_redirection_and_routine_blocker_single_town_world_unaffected` (all new, per test_plan.md items
5-7). Create `tests/unit/strategic/test_redirection.py` (confirmed not to exist during planning —
`grep -rl "StrategicRedirectionSystem" tests/` found no dedicated test file, only two refactor
import-compatibility smoke tests). Place the routine-blocker and single-town-unaffected tests in
`tests/unit/strategic/test_expanded_goals.py` or a new dedicated
`tests/unit/strategic/test_intelligence_routine_blockers.py`, per test_plan.md item 6's stated
either/or — prefer the new dedicated file to keep the diff narrow and easy to review in isolation.

### Step 5 — Documentation updates

**Files:** `docs/mechanics/06_worldbuilding_foundation.md`, `docs/world/compiler_contract.md`,
`docs/parity_ledger/substrate.yaml`, `docs/parity_ledger/strategic_cognition.yaml`,
`docs/engine/contracts/tactical_contract.md`

**Change:**
- `docs/mechanics/06_worldbuilding_foundation.md`: add a new subsection (near the existing
  `town_tiles` membership/paint-order documentation, confirmed present but silent on town-center
  derivation per investigation's Docs Requiring Update) documenting the Step 1 derivation rule
  verbatim: "the centroid of the first `type=="town"` region encountered in declaration order;
  `(0.0, 0.0)` if no town region exists" — and the Design Decision's rationale for keeping
  `town_center` single-valued rather than deprecating it.
- `docs/world/compiler_contract.md`: this is the formally-authoritative, more specific compiler
  contract doc (P0 authority, `status: authoritative`, WORLD-050/051/052 compliance namespaces) —
  confirmed by re-read during this plan revision to exist and to already document
  `WorldCompiler.compile()`'s numbered "Compilation sequence" (steps 1-8, `## Compiler Contract`
  section). That numbered sequence currently has no step for town_center derivation, so it goes stale
  the moment Step 1 lands — this is the same class of gap the Mechanics Bible update above closes,
  just at this doc's more mechanical, step-by-step level of detail, and both must be updated in the
  same session per CLAUDE.md's Parity rule ("Documentation and source code must remain in 100%
  semantic parity"). Add one new numbered step (after existing step 2 "Instantiate `RegionState`
  objects...", since that is where the new post-loop derivation block runs) stating: "2a. Derive
  `town_center` as the centroid of the first `RegionSpec` with `type == "town"` encountered in
  `spec.regions` order; left at the `AuthoritativeState` default `(0.0, 0.0)` if no town-type region
  exists." Do not renumber the existing steps 3-8 — insert as "2a" rather than shifting every
  subsequent step number, to keep the diff minimal and avoid touching unrelated step text. No new
  WORLD-0xx compliance ID is needed — this is additive detail under the existing WORLD-051
  ("Compilation sequence and entity construction") namespace, not a new contract surface.
- `docs/parity_ledger/substrate.yaml`: add new entry `id: SUB-387` (confirmed next free ID —
  `SUB-386` is the current highest, checked via `grep -oP "id: SUB-\d+" docs/parity_ledger/substrate.yaml`
  during planning), `status: verified`, `priority: P1`, `text` describing the
  `WorldCompiler.compile()` town_center derivation, `v2_evidence` citing
  `src/worldbuilding/compiler.py`, `test_path` citing
  `tests/unit/worldbuilding/test_world_compiler.py::test_compile_sets_real_town_center_from_town_region`.
  Use `tools/parity_ledger_writer.py` (the sanctioned schema-validating writer), not a raw
  Edit/ad-hoc script, per the project's parity-updater safety pattern.
- **`docs/parity_ledger/substrate.yaml` — also update the pre-existing `SUB-014` entry
  (`test_navigation_uses_flow_field_for_far_town`, `status: verified`, `priority: P0`,
  `v2_evidence: 'Implementation proven via exhaustive checklist audit Phase 1-11'`, `test_path:
  null`).** Re-read during this plan revision and confirmed: SUB-014's own `text` field
  ("Navigation uses flow field for far town") describes exactly the mechanism Step 2 of this plan
  changes — `FlowFieldService.get_flow_direction(target_kind='TOWN')` — and it is a P0 entry sitting
  with a null `test_path` today (a pre-existing gap this ticket did not create, but directly touches
  the described behavior of, so it must not ship untouched). Once Step 2 lands and its new test
  (`test_get_flow_direction_town_uses_real_town_center_not_hardcoded_anchor`, Step 2's Verify) is
  real and passing, update SUB-014 in the same Parity phase pass as the new `SUB-387` entry: set
  `test_path: tests/unit/movement/test_flow_field_navigation.py::test_get_flow_direction_town_uses_real_town_center_not_hardcoded_anchor`
  and update `v2_evidence` to cite the real code path (`src/systems/world_systems/navigation.py`'s
  `get_flow_direction`'s `target_kind == "TOWN"` branch, post-Step-2) instead of the vague
  "exhaustive checklist audit" phrase — `status` stays `verified` (the behavior SUB-014 describes
  remains correct after the fix, it just now has real evidence instead of an audit citation). Use
  `tools/parity_ledger_writer.py::write_entry("substrate.yaml", entry)` for this update, same as the
  new `SUB-387` entry — **`write_entry` is a full-entry upsert-by-id (`entries[index] = entry`), not
  a partial patch**, confirmed by reading `tools/parity_ledger_writer.py:88-117` during this
  revision: the Parity phase must pass SUB-014's complete entry dict (including its unchanged `id`,
  `text`, `status`, `priority`, `legacy_evidence: null`, `proof_type: null`, `divergence_note: null`,
  `support_boundary: null` fields), not just the two changed keys, or the upsert silently drops the
  other fields. Do not change SUB-014's `text`, `priority`, or `status` — only `v2_evidence` and
  `test_path` get new values.
- `docs/parity_ledger/strategic_cognition.yaml`: add new entry `id: STRAT-260` (confirmed next free
  ID — `STRAT-259` is current highest, checked the same way), `status: verified`, `priority: P1`,
  covering the `FlowFieldService`/`StrategicRedirectionSystem`/`StrategicIntelligenceSystem`
  nearest-tile fixes and the `WorkerPacket.town_center` removal, with a one-line cross-reference note
  pointing at the existing `STRAT-249` entry (confirmed unchanged/unedited by this ticket — it covers
  a different mechanism, `_resolve_target_position()`'s fallback, per investigation's Parity Ledger
  Overlap section) so a future reader understands the two entries are related but distinct. Use
  `tools/parity_ledger_writer.py`.
- `docs/engine/contracts/tactical_contract.md`: confirmed this file exists (`ls
  docs/engine/contracts/tactical_contract.md` during planning). Add a short note to its Section 7
  ("Objective Target Resolution") stating that as of this ticket, `town_center` carries a real
  compiled value rather than always being `(0,0)` in practice, so Section 7's existing examples now
  reflect a real-value world — per investigation's Docs Requiring Update note that Section 7 "doesn't
  assert anything actually false" today but should not be read as still describing a `(0,0)`-only
  world.

**Do NOT touch:** `docs/engine/kernel.md` or `docs/engine/authoritative_pipeline.md` — investigation
explicitly confirmed neither needs a change (this ticket's fixes are internal to existing phases, no
phase reordering). Do not edit `STRAT-249`'s `status` or `v2_evidence` — investigation confirms that
mechanism is unchanged by this ticket; only add a cross-reference note. Do not touch SUB-014's `text`,
`priority`, or `status` fields, or any other `substrate.yaml` entry besides `SUB-014` and the new
`SUB-387` — the P0-gap fix is scoped to the two fields named above.

**Verify:** `python3 tools/validate_frontmatter.py` (or the project's standard doc-lint step) passes
on all five touched docs; `tools/parity_ledger_writer.py`'s own schema validation passes for the new
`SUB-387`/`STRAT-260` entries and the updated `SUB-014` entry (its `status: verified` still requires
non-null `v2_evidence` and `test_path` per `validate_entry`'s schema mirror — both are being set to
real values by this update, so this passes cleanly).

### Step 6 — Integration coverage and behavioral-baseline spot-check

**Files:** `tests/unit/strategic/test_expanded_goals.py` (or `tests/integration/worldassembly/`), plus spot-check runs against `tests/regression/baseline_5k.json` and `tests/simulation_quality/fixtures/grade_anchors.json`

**Change:** Add `test_town_return_navigates_to_real_compiled_town_center` (new, per test_plan.md item
8) — an unmocked-pipeline integration test mirroring
`TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG`'s own
`test_town_return_project_now_produces_real_navigation`, but starting from a real
`WorldCompiler.compile()` output instead of a hand-built `AuthoritativeState`, asserting the full
chain `WorldCompiler.compile()` → `TownScorer`/`evaluate_strategic_intent()` →
`TacticalDecisionSystem.evaluate_entity_intent()` produces a `NavigationUpdate` toward the real
compiled town location. Place it alongside the existing precedent test in
`tests/unit/strategic/test_expanded_goals.py` unless the implementer judges
`tests/integration/worldassembly/` a closer fit once the fixture is drafted (test_plan.md leaves this
either/or explicitly).

Then run, and manually diff (not blindly re-run) per test_plan.md's Anti-Drift Test Guards:
`pytest tests/regression/test_behavioral_5k.py tests/simulation_quality/test_grade_regression.py -v`
against `tests/regression/baseline_5k.json` and `tests/simulation_quality/fixtures/grade_anchors.json`
— both fixtures exercise `urban_political.yaml`'s two-town-region composition. Per investigation Item
7, `town_center` was never previously read by anything visible in these baselines' recorded output
fields, and Step 1 introduces zero new RNG draws (pure arithmetic on already-compiled `bounds`), so
RNG-sequence drift risk is zero — but the new `town_center` field value itself is new observable
state, so any field-by-field diff must be inspected, not assumed clean.

**Other writers to the baseline fixture files**: none within this ticket's scope — these are
regression snapshots regenerated only by an explicit, separate re-baselining step (outside this
ticket) if a legitimate diff is found; do not silently regenerate them to force a pass, per CLAUDE.md's
Gate Integrity rule.

**Do NOT touch:** the baseline JSON files themselves unless a diff is found and confirmed to be this
ticket's own legitimate, intended change (new `town_center` field value) — and even then, updating
baseline fixtures without a documented finding would violate the Gate Integrity rule; report and stop
rather than editing to force green if any *other* unexpected field also drifted.

**Verify:** the new integration test passes; the two regression/quality-baseline commands run clean
or every diff is explained and matches only the expected new `town_center` value.

## Scope Guards

- Do not touch `WorldProceduralGenerator.generate()` (`src/worldgeneration/generator.py`) — legacy
  single-town-region generator, explicitly out of scope; the fix lives in `WorldCompiler.compile()`
  only, which both the generator and the assembly-resolver paths already funnel through.
- Do not touch `FlowFieldService.ANCHORS["WORLD_BOSS"]` or its dynamic-entity fallback branch — same
  class of hardcoding, not named in this ticket's Scope/AC.
- Do not extend arrival-dispatch behavior for `TOWN_RETURN`/`RECOVER`/`RESOLVE_BLOCKER` once entities
  arrive at a real `town_center` — out of scope per `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG`'s
  own deferred open question; this ticket only fixes the navigation *pointer*, not arrival behavior.
- Do not touch Idea 56 (Drifting Loyalty)'s city-to-capital political-distance measure — confirmed
  zero shared code path anywhere in the repo (investigation Item 8).
- Do not harden `intelligence.py`'s `next(iter(...))` pattern beyond swapping it for the shared
  `nearest_town_tile()` call in Step 4 — investigation Item 9 confirms it is the same bug as
  `redirection.py`'s, not a separate determinism concern needing extra work.
- Do not change `_resolve_target_position()` in `src/engine/tactical.py` or the `STRAT-249` parity
  entry it corresponds to — investigation Item 7 confirms this mechanism is transitively fixed by
  Step 1 with no code change, and Item 2/Parity Ledger Overlap confirms `STRAT-249` covers a
  different, unaffected mechanism.
- Do not conflate `WorkerPacket.town_center` removal (Step 3) with any change to
  `AuthoritativeState.town_center` (Step 1) — they are separate fields with separate, independently
  evidenced dispositions; do not let Step 3's removal logic bleed into Step 1's derivation logic or
  vice versa.
- Do not deprecate, rename, or remove `AuthoritativeState.town_center` or add a new nearest-town
  lookup registry/method as part of this ticket — see Design Decision. Any such change is future work
  for a separate ticket.
- Do not regenerate or hand-edit `tests/regression/baseline_5k.json` /
  `tests/simulation_quality/fixtures/grade_anchors.json` to force Step 6's spot-check green — report
  any unexplained diff truthfully per the Gate Integrity rule instead of routing around it.
- Every "pick nearest tile" or "aggregate across regions" computation added by this plan (Step 1's
  first-town-region centroid, Step 4's `nearest_town_tile()`) must use the fully deterministic
  tie-break rules stated in their own step — no new randomness, no reliance on `dict`/`set` iteration
  order for the *result* (only for candidate enumeration, where `min()`'s key function neutralizes
  order-dependence).

## Dependency Map

- Step 1 (WorldCompiler) is independent and should land first — it is the root-cause fix and the
  other steps' tests are easiest to write against real compiled worlds once it exists, though Steps
  2-4 are each independently testable against hand-built `AuthoritativeState` fixtures (as
  test_plan.md's existing-test survey already does) and do not strictly require Step 1 to be merged
  first.
- Step 2 (FlowFieldService) is independent of Steps 1, 3, 4 — touches a disjoint file.
  Functionally, its fix only becomes *observable* in a real compiled world once Step 1 lands, but the
  code change itself has no dependency.
  Do not touch  `ANCHORS["WORLD_BOSS"]` while in this file (Scope Guard above).
- Step 3 (WorkerPacket) is fully independent of every other step — disjoint files, disjoint field.
- Step 4 (redirection/intelligence) is independent of Steps 1-3 for its unit tests (which construct
  `AuthoritativeState` directly, per existing test convention), but its fallback-to-`state.town_center`
  branch (when `town_tiles` is empty) only becomes meaningfully "real" once Step 1 lands — soft
  dependency, not a hard build-order requirement.
- Step 5 (docs) depends on Steps 1-4 being finalized (derivation rule, removal decision, and helper
  function name/location must be settled before writing docs that describe them).
- Step 6 (integration + baseline spot-check) depends on Steps 1 and 4 both landing (the chain under
  test is `WorldCompiler.compile()` → scorers → tactical → redirection/intelligence).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| WorldCompiler.compile() sets AuthoritativeState.town_center to a real value derived from the compiled town-type region(s), not left at default (0,0) | Step 1 | `test_compile_sets_real_town_center_from_town_region`, `test_compile_town_center_derivation_with_multiple_town_regions` |
| FlowFieldService.get_flow_direction(target_kind='TOWN', ...) returns direction toward the real town location, not hardcoded ANCHORS waypoints | Step 2 | `test_get_flow_direction_town_uses_real_town_center_not_hardcoded_anchor` |
| WorkerPacket.town_center gains a real consumer or is removed as dead duplicate state | Step 3 | `test_worker_packet_has_no_dead_town_center_field` |
| StrategicRedirectionSystem.enforce() and StrategicIntelligenceSystem's routine-blocker pass compute the tile nearest to the requesting entity, not an arbitrary sorted/iter pick | Step 4 | `test_redirection_enforce_targets_nearest_town_tile_not_arbitrary_sort`, `test_routine_blocker_pass_targets_nearest_town_tile_not_arbitrary_iter`, `test_redirection_and_routine_blocker_single_town_world_unaffected` |
| Design decision on town_center deprecation vs. single-value retention must be explicit (ticket Scope, final bullet) | Design Decision section (this plan) + Step 5 docs | Reviewed at Plan/Architecture-Review gate; documented in `docs/mechanics/06_worldbuilding_foundation.md` |

## Anti-Drift Notes

- `test_flow_field_long_distance`'s existing `town_center=(100.0,100.0)` coincidentally equals
  `ANCHORS["TOWN"][0]` — this masked the original bug and will continue to pass after Step 2's fix
  for the same coincidental reason; do not treat its continued pass as proof of the fix, rely on the
  new `test_get_flow_direction_town_uses_real_town_center_not_hardcoded_anchor` (distinct position)
  for that.
- `tests/unit/strategic/test_expanded_goals.py::test_town_return_project_now_produces_real_navigation`
  and `tests/unit/tactical/test_objective_pursuit_coverage.py`'s 3 tests from the prior related
  ticket construct `AuthoritativeState`/`ObjectiveState` directly with explicit `town_center=(0.0,
  0.0)` — they do not go through `WorldCompiler.compile()` and must keep passing unmodified; they are
  not proof this ticket's Step 1 fix works (Step 6's new integration test is).
- `tests/unit/world/test_home_storage.py` and `tests/unit/world/test_town_building_contract.py`
  construct `town_center=(0,0)` explicitly and are unaffected by Step 1 — must stay passing
  unmodified, not "fixed" to use a real value (they are testing `HomeStorageService`'s own logic in
  isolation, not the compiler).
- `urban_political.yaml`-derived fixtures (`baseline_5k.json`, `grade_anchors.json`,
  `test_real_content_world_compositions.py`) are load-bearing regression fixtures spanning ~35 files
  — Step 6's spot-check is not optional busywork; it is the one real end-to-end guard against a
  derivation rule (Step 1) that only happens to work for single-town worlds.
- `ANCHORS["WORLD_BOSS"]` sits in the same file/class as `ANCHORS["TOWN"]` (Step 2's target) — easy
  to accidentally touch while editing nearby code; it is explicitly out of scope.

## Unresolved Questions

None.

## Deviations

Recorded during Implement (per CLAUDE.md's "never silently deviate" rule).

1. **`redirection.py`: fixed a pre-existing, unrelated `SystemCadence` import bug, not named in
   this plan.** While writing Step 4's own required test
   (`test_redirection_enforce_targets_nearest_town_tile_not_arbitrary_sort`), calling
   `StrategicRedirectionSystem.enforce(state, StateUpdate())` (no explicit `cadence` argument, as
   Step 4's Verify section specifies) raised `NameError: name 'SystemCadence' is not defined` at
   `cadence = cadence or SystemCadence()`. Confirmed via `git stash` that this line was unmodified
   by Step 4's edits and the same `NameError` reproduces on unmodified `enforce()` calls — a
   genuine pre-existing bug this plan's own investigation did not surface (investigation never
   called `enforce()` directly). Root cause: `SystemCadence` is referenced only in the function's
   lazily-evaluated (`from __future__ import annotations`) type-hint default, never imported at
   module scope — only a same-named-differently `should_run` is imported locally inside the
   function body. Also discovered `enforce()` has zero callers anywhere in `src/` (its logic was
   fully "hoisted" into `intelligence.py`'s `fused_strategic_pass()`, confirmed by that file's own
   in-code comment at the hoist site) — so this bug was latent/unreachable in production, but
   `enforce()` remains part of the public API surface (re-exported by `src/systems/redirection.py`,
   asserted importable by two `tests/refactor/` smoke tests) and this ticket's own AC/Step 4 Verify
   section explicitly requires `enforce()` to be directly callable and correct. Fixed with a single
   added top-level import (`from src.engine.cadence import SystemCadence`) in
   `src/systems/strategic_systems/redirection.py` — no other change to that file beyond what Step 4
   already specifies.

2. **Step 6 baseline spot-check surfaced a real, unanticipated regression outside the two named
   baseline files — reported, not resolved.** `tests/regression/test_behavioral_5k.py` and
   `tests/integration/kernel/test_long_run_determinism.py::test_1000_tick_determinism` are
   inconclusive in the implementation environment (both fail identically, with and without this
   ticket's changes, on a `tests/conftest.py` resource-time-limit `TimeoutError` — confirmed via
   `git stash` bisection to be pure CPU-contention environment noise on this shared 4-core
   machine, not a code signal). `tests/simulation_quality/test_grade_regression.py -m "not slow"`
   passed the 7 tests it could actually run locally (64 skipped for missing calibration fixtures
   not present in this environment). However, `tests/unit/worldassembly/test_corpus_diversity.py`
   — named in test_plan.md's own "Regression Surface" as required to "keep passing unmodified,"
   though not one of Step 6's two explicitly-named JSON-baseline spot-check files — shows 13 real,
   reproducible failures (population-stability and simulation-quality-grade-stability tests) across
   most of the world-composition test corpus, not only `urban_political`. Bisected with `git
   stash`: Step 1 alone passes; Step 1 + Step 2 together reproduces the full failure set. This is
   the direct, deterministic (seed=42) consequence of entities now correctly navigating to the real
   compiled town location instead of an arbitrary tile or two hardcoded fake waypoints — very
   plausibly the fix's intended effect exposing that these tests' "passing" state depended on the
   pre-existing pointer bug, not on genuine balance. Per the Gate Integrity rule, no test, threshold,
   or baseline file was edited to route around this. Full detail recorded in the ticket's
   Implementation Notes; this is left as an explicit, unresolved, blocking finding for the next
   phase (Architecture-Review / Parity / Verify) to decide: accept as intended and re-baseline the
   affected floors/thresholds with a documented rationale, or reconsider the scope/sequencing of
   Step 2's `FlowFieldService` change.

3. **Human decision made (2026-08-28): accept the `test_corpus_diversity.py` regression as this
   ticket's intended, correct consequence — do not reconsider or roll back Step 2.** Re-verified
   independently in this session (not trusted blindly from the prior session's numbers): running
   `pytest tests/unit/worldbuilding/test_world_compiler.py tests/unit/worldgeneration/
   tests/unit/worldassembly/ -q` (test_plan.md's own "World compilation / generation" scoped
   command, which bundles `test_corpus_diversity.py` together with the rest of
   `tests/unit/worldassembly/`) reproduces **exactly 13 failed, 221 passed, 1 error** — the identical
   count and (with one immaterial exception below) the identical test names already disclosed in the
   ticket's Implementation Notes and the prior session's Post-Implement Pipeline Resumption note. The
   1 ERROR reproduced at `test_resolver.py::test_resolve_module_contribution_rejects_raw_spec` this
   time (vs. `test_trading_company_hub_composed[swamp_border_world]` in the prior session's isolated
   run) — confirmed to be exactly the same "test-ordering/shared-state artifact of whichever test
   runs last in the batch" category already named in the ticket, not a new failure mode: running
   `test_corpus_diversity.py` standalone (outside test_plan.md's actual scoped command, done here
   only as an extra cross-check) reproduces 16 failed/1 error with 3 additional seed123-variant
   grade-stability tests failing and 2 fewer `simq_routing_test` tests failing — batch-composition-
   and ordering-sensitive, consistent with the already-disclosed pattern, and not the authoritative
   scope per CLAUDE.md's "scope tests to test_plan.md's already-defined scope" rule. The other five
   scoped test-plan command groups (navigation/movement: 53 passed; strategic/tactical/ai-goals: 327
   passed; town/world services: 6 passed; worker-protocol/kernel/integration-kernel/core: 162 passed
   + 1 failed [`test_1000_tick_determinism`, the same pre-existing documented
   `TimeoutError`/resource-time-limit environment signature under CPU contention, reproduced
   independently with the same traceback shape — not a new regression]; worldassembly integration: 53
   passed) all match the prior session's counts exactly, for a combined 822 tests passing outside the
   disclosed exception, identical to the prior session's own total.

   Decision, and rationale: the pre-fix "passing" state of these 13 tests was itself an artifact of
   the pointer bug this ticket exists to fix (entities either navigating to an arbitrary real town
   tile or to two hardcoded fake waypoints, never the real compiled town center) — it was never
   evidence of genuine population/quality-grade balance under correct navigation. Rolling back Step 2
   to keep these floors passing would mean shipping the fix with entities still not actually
   navigating to town, defeating the ticket's entire purpose. The floors/thresholds are therefore
   stale calibration data computed against buggy navigation behavior, not a correctness signal this
   ticket's own code broke. Per `docs/testing/regression_policy.md`'s documented pattern for "a
   hardcoded test baseline that this session's own legitimate change caused to drift" — a small
   hotfix ticket re-baselining the floors with fresh evidence, never a silent edit outside a ticket —
   this ticket closes with the regression disclosed (not silently routed around) in its Test Summary
   and Completion Summary, and a separate follow-up ticket
   (`TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`, filed at `tickets/todos/` after
   this ticket closes) is filed to re-baseline `test_corpus_diversity.py`'s population/grade-stability
   floors for the 13 named tests, using the now-correct navigation behavior as fresh ground truth.
   The Test gate is treated as cleared for this ticket on that basis — the disclosed 13F+1E is an
   accepted, documented exception, not a blocking failure.

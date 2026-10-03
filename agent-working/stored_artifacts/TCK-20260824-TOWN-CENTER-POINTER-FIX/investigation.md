---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260824-TOWN-CENTER-POINTER-FIX
artifact_type: investigation
tags: [world, determinism]
---

# Investigation — TCK-20260824-TOWN-CENTER-POINTER-FIX

## Context Scan Note

`mcp__knowledge-search__search_docs` returned `{"error":"index not found"}` for this session (known
pre-existing environment gap). Fallback `tools/knowledge_search.py query ... --top-k 5` also
returned `knowledge index not found`. Both semantic-search paths were unavailable; proceeded to
`graphify query` (multiple targeted queries run per the task instructions) and then grep/Read, per
CLAUDE.md's explicit fallback ordering. `graphify query "town_center"` surfaced only
`WorldProceduralGenerator`/`test_generator.py` (the `+/-15` town-carving comment) — not enough on
its own, so the remaining findings below come from direct source reads and targeted grep, guided by
the ticket's own Related Code Areas list.

## Current Behavior

### 1. `AuthoritativeState.town_center` default and `WorldCompiler.compile()`

`AuthoritativeState.town_center: tuple[float, float] = (0.0, 0.0)` (`src/core/state.py:1129`,
"Milestone 7"). `WorldCompiler.compile()` (`src/worldbuilding/compiler.py:594-610`) constructs the
final `AuthoritativeState(...)` and does **not** pass `town_center=` at all — so every real compiled
world silently keeps the dataclass default `(0.0, 0.0)`, confirmed by direct read of the
constructor call (no `town_center` keyword present among the ~15 fields passed).

This is not for lack of available data: `WorldCompiler.compile()`'s region loop
(`compiler.py:211-252`) already builds `town_tiles: Set[tuple[int,int]]` by unioning every tile from
every region where `r_spec.type == "town"` (`compiler.py:235-236`), and constructs a `RegionState`
per region with real `bounds` (`compiler.py:243-252`, `kind=r_spec.type.upper()` so `kind=="TOWN"`
identifies town regions). A real town_center (e.g. the centroid of the first/each town-type
region's bounds) is fully derivable from `regions`/`town_tiles` at this point — the bug is a pure
omission, not a missing-data problem.

### 2. Every direct consumer of `AuthoritativeState.town_center`

Grepped broadly (`grep -rn "\.town_center\b" src/`), beyond the files named in the ticket:

- `src/ai/goals/scorers.py` — `TownScorer.score()` (line 98), `CombatRetreatScorer.score()` (line
  164), `RecoverScorer.score()`'s no-inn fallback (line 186), `ResolveBlockerScorer.score()`'s final
  fallback (line 226) — all read `state.town_center` directly and place it in `GoalScore.target_pos`.
- `src/ai/goals/adventure_scorer.py` — `_resolve_placeholder_target_pos()`, `RECOVER`/
  `ASK_INFORMATION` families (lines 255, 263) — same direct-read pattern, explicitly modeled on
  `TownScorer`/`RecoverScorer`'s own convention (comment cites `scorers.py:98,163,186`).
- `src/town/town_navigation.py` — `TownNavigation.is_in_town()` (line 34) — direct read.
- `src/town/home_storage.py` — `HomeStorageService.transfer_to_home()`/`transfer_from_home()` (lines
  20, 65) — direct read, proximity gate for home-storage access.
- `src/systems/strategic_systems/redirection.py` — `StrategicRedirectionSystem.enforce()` (line 29)
  — direct read, then overridden by an arbitrary `town_tiles` pick when non-empty (see Item 5).
- `src/systems/strategic_systems/intelligence.py` — routine-blocker pass (line 335) — same pattern,
  different arbitrary-pick idiom (see Item 5/9).
- `src/systems/world_systems/navigation.py` — `FlowFieldService.get_flow_direction()` (line 44,
  dead branch — see Item 3) and `NavigationSystem.get_next_step()` (line 94, `if target_pos ==
  state.town_center:` gate that decides whether to even invoke `FlowFieldService`).
- `src/engine/scheduler.py` — `DeterministicScheduler.select_work()` (line 51) — `focus_points =
  [state.town_center]`, an LOD (level-of-detail) focus point; direct read.
- `src/engine/checkpoint.py` (line 75) and `src/engine/apply.py` (line 385) — pure plumbing: fold
  `town_center` into the canonical-fingerprint dict and carry it forward unchanged tick-to-tick via
  `replace()`. No independent bug here.
- `src/engine/executor.py` (line 321) — producer for `WorkerPacket.town_center` (see Item 4).
- `src/core/worker_protocol.py` (line 53) — `WorkerPacket.town_center` field declaration (see Item 4).
- `src/worldgeneration/generator.py` and `src/world/regions.py` use the **string** `"town_center"`
  as a region ID, and a same-named but structurally unrelated function parameter
  (`get_difficulty_tier_at(pos, town_center=(0,0))`, zero callers anywhere in `src/` — dead code,
  out of scope, not in the ticket's Related Code Areas) — neither reads
  `AuthoritativeState.town_center`.

### 3. `FlowFieldService.get_flow_direction(target_kind='TOWN', ...)` — confirmed hardcoded

`src/systems/world_systems/navigation.py:18-21`:
```python
ANCHORS = {
    "TOWN": [(100, 100), (200, 50)],   # Waypoints for town
    "WORLD_BOSS": [(500, 500), (450, 450)]
}
```
`get_flow_direction()` (line 33): `anchors = FlowFieldService.ANCHORS.get(target_kind, [])`. For
`target_kind="TOWN"` this is **always non-empty** (`[(100,100),(200,50)]`), so the `if not anchors:`
branch that would fall back to `state.town_center` (line 44) is **dead code for `target_kind ==
"TOWN"`** — it can only ever fire for an unregistered `target_kind`, which "TOWN" is not. The
service always steers toward the nearest of two literal hardcoded waypoints, never the real compiled
town location, regardless of what `state.town_center` holds (even after Item 1's fix).

`ANCHORS` is a class-level literal dict with no external source (no config, no catalog, no state
field) — it is standalone hardcoded V2-hardening scaffolding (comment: "Mocked world structure for
V2 hardening"), not derived from anything.

`NavigationSystem.get_next_step()` (line 94) is the only caller of `get_flow_direction`, gated on
`if target_pos == state.town_center:` — so the flow-field path only activates at all when a caller
passes exactly `state.town_center` as `target_pos` (true for the `TOWN_RETURN`/`RECOVER`/
`RESOLVE_BLOCKER` chain once Item 1 is fixed, since those flow through `obj.target_position` ==
`state.town_center` at scoring time).

**Existing test masks this bug**: `tests/unit/movement/test_flow_field_navigation.py::
test_flow_field_long_distance` sets `state.town_center=(100.0, 100.0)` — which is *exactly*
`ANCHORS["TOWN"][0]`. The test currently passes for the wrong reason: it can't distinguish "used
`state.town_center`" from "used the hardcoded anchor that happens to equal it." A real fix needs a
new test with `town_center` at a position distinct from both hardcoded anchors (see test_plan.md).

### 4. `WorkerPacket.town_center` — confirmed dead duplicate state (traced via call graph, not just grep)

`src/core/worker_protocol.py:53`: `town_center: Tuple[float, float] = (0.0, 0.0)`. Producer:
`src/engine/executor.py:321`, `town_center=state.town_center` inside `WorkerPacket(...)`
construction for every `ENTITY_MOVE`/`ENTITY_ACT`/`ENTITY_BRAIN` work item.

**Consumer search**: `grep -rn "packet\.town_center"` and `grep -rn "\.town_center\b" src/
tests/` (22 total hits) turn up **zero** reads of `.town_center` on any `WorkerPacket`/packet-typed
variable anywhere in `src/` or `tests/`.

**Hidden-consumer check (traced, not assumed)**: `WorkerPacket` duck-types much of
`AuthoritativeState`'s surface (`.entities`, `.regions`, `.buildings`, `.town_center`, etc.) and is
passed as the `state` parameter into shared logic for `ENTITY_BRAIN` work
(`src/engine/worker_logic.py:43-45`: `updates = SimulationDomainLogic.execute_brain(packet,
packet.subject)`, comment: "Pass packet as 'state' context"). Traced the full call chain:
`execute_brain` → `CognitionDomain.execute_brain(state, entity, force)`
(`src/engine/domain/cognition.py:27-75`) → `TacticalDecisionSystem.evaluate_entity_intent(readonly_state,
entity, ...)` (`src/engine/tactical.py:38`). Read `evaluate_entity_intent` and
`_resolve_target_position` in full (`tactical.py:37-753`): **neither reads `state.town_center`
anywhere** — target resolution goes through `obj.target_position` (set earlier, at strategic-pass
time, from the real `AuthoritativeState`, not the packet). `MovementSystem.resolve_move()` (the one
caller chain that *does* read `state_or_context.town_center`, via `NavigationSystem.get_next_step`)
is called only from `src/engine/pipeline_phases/movement.py:265` and
`src/engine/domain/movement_actions.py:27` — both operate on the real `AuthoritativeState` inside
the authoritative kernel phase, never on a `WorkerPacket`. The `ENTITY_MOVE` work-kind branch in
`worker_logic.py` (lines 14-30) does not call `MovementSystem`/`NavigationSystem` at all.
**Conclusion: `WorkerPacket.town_center` has zero real consumers — confirmed dead duplicate state,
not a hidden one** — it is written every tick for every dispatched work item and never read.

### 5. `StrategicRedirectionSystem.enforce()` / `StrategicIntelligenceSystem` routine-blocker pass — arbitrary pick, confirmed

`src/systems/strategic_systems/redirection.py:28-33`:
```python
town_target = state.town_center
if state.town_tiles:
    town_pos = sorted(list(state.town_tiles))[0]   # arbitrary: lowest (x,y) tuple in the WHOLE WORLD
    town_target = (float(town_pos[0]), float(town_pos[1]))
```
Computed **once per tick** (comment: "Pre-calculate town target once per tick") and applied
uniformly to every entity's return-to-town fallback (line 134: `target_coords = town_target`),
regardless of where the requesting entity actually is or which town region it's near. `town_tiles`
is the flat union of every tile from every `type=="town"` region compiled into the world (confirmed
in Item 1/6) — so with more than one town region, this always resolves to whichever tile happens to
sort lowest by `(x, y)`, which could be in either town, arbitrarily.

`src/systems/strategic_systems/intelligence.py:335-338` (routine-blocker pass), same shape, different
arbitrary-pick idiom:
```python
town_target = state.town_center
if not town_target and state.town_tiles:
    town_pos = next(iter(state.town_tiles))   # arbitrary: set-iteration order
    town_target = (float(town_pos[0]), float(town_pos[1]))
```
Also computed once and applied to every entity needing to return to town (confirmed by grepping all
uses of `town_target` in the file: lines 385-394 and 620-624, both entity-loop "has items, return to
town" fallbacks with the identical shape as `redirection.py`'s).

### 6. World composition / multi-town-region support — **confirmed real and exercised, not merely theoretical**

This is the deciding evidence for the ticket's central design question.

- `WorldProceduralGenerator.generate()` (`src/worldgeneration/generator.py:82-96`) — the legacy
  single-shot generator — hardcodes exactly one `regions["town_center"]` region of `type="town"`.
  This path genuinely only ever produces one town.
- The **module-composition path** (`ProceduralCompositionGenerator` +
  `WorldAssemblyResolver.assemble()`) does not have this restriction. Real `module_type: "settlement"`
  content modules exist and each declares a real `type: "town"` region:
  `data/content/world_modules/frontier_village_core.yaml` (region `hometown`, bounds
  `[10,10,40,40]`) and `data/content/world_modules/trading_company_hub.yaml` (region `hometown`,
  bounds `[45,10,80,45]`).
- `ProceduralCompositionGenerator.generate()`'s own selection rules (`generator.py:428-451`): Rule 2
  always includes the top-scoring settlement module; Rule 3 fills remaining budget slots (`BUDGET=6`)
  from all remaining modules **without excluding settlement type** (only excluded when
  `intent.settlement_style == "none"`) — so a second settlement module can and does get selected
  when it scores well enough.
- **Confirmed via a real, already-shipped composition, not a hypothetical**:
  `data/content/world_compositions/urban_political.yaml` explicitly references both
  `frontier_village_core` (no namespace, region id `hometown`) and `trading_company_hub` (namespace
  `trading`, region id `trading_hometown`) — two distinct `type: "town"` regions in one world.
  `WorldAssemblyResolver.assemble()`'s region-merge (`resolver.py:344-349`) has no town-count
  restriction (only a same-ID collision guard, which the differing namespaces avoid), and
  `CompileProfileResolver.resolve()` (`resolver.py:960-962`) iterates ALL `type=="town"` regions in a
  `for` loop (no early break), registering ownership for every one.
  `urban_political.yaml` is not a dead/example-only file — it is referenced across ~35 files
  including `tests/regression/baseline_5k.json`, `tests/regression/test_behavioral_5k.py`,
  `tests/simulation_quality/fixtures/grade_anchors.json`, and
  `tests/integration/worldassembly/test_real_content_world_compositions.py`.

**Conclusion**: single-town-only is true only for the legacy `WorldProceduralGenerator.generate()`
path. The module-composition path — which is the one exercised by the real content corpus's
regression baseline — already produces multi-town-region worlds in production test fixtures today.
A single-value `AuthoritativeState.town_center` is provably insufficient for a world like
`urban_political` even after Item 1's fix (it can only ever hold one town's position, picked by
whatever tie-break the fix uses, silently discarding the other town). This favors deprecating
`town_center` as a single durable pointer in favor of a proper nearest-town(-tile) lookup derived
from `town_tiles`/`regions` at each call site — see Risks/Open Questions for the concrete design
choice this ticket must still make explicit.

### 7. Transitive-fix confirmation — which consumers get fixed "for free" by Item 1

Every consumer in Item 2 that reads `state.town_center` **directly at call time** (not via a
previously-captured/cached copy) is transitively fixed the moment `WorldCompiler.compile()` sets a
real value, with zero code change required in the consumer itself:

- `src/ai/goals/scorers.py` (`TownScorer`, `CombatRetreatScorer`, `RecoverScorer`,
  `ResolveBlockerScorer`) — direct read, confirmed.
- `src/ai/goals/adventure_scorer.py` — direct read, confirmed.
- `src/town/town_navigation.py`, `src/town/home_storage.py` — direct read, confirmed.
- `src/engine/scheduler.py` — direct read, confirmed.
- `src/engine/tactical.py`'s `TOWN_RETURN` path — **does not read `state.town_center` directly at
  all**. It reads `obj.target_position`, which was populated by
  `StrategicIntelligenceSystem.evaluate_strategic_intent()` from `GoalScore.target_pos` at the
  moment `TownScorer` (etc.) scored the goal, using the real `AuthoritativeState` (per
  `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG`'s own fix). Since `TownScorer` reads
  `state.town_center` fresh every scoring pass, `tactical.py`'s `TOWN_RETURN`/`RECOVER`/
  `RESOLVE_BLOCKER` arrival-navigation is **also** transitively fixed — confirmed by full read of
  `tactical.py`, not assumed.

**Not transitively fixed — need their own code changes**:
- `src/systems/world_systems/navigation.py`'s `FlowFieldService` — hardcoded `ANCHORS` short-circuits
  before `state.town_center` is ever consulted for `target_kind="TOWN"` (Item 3).
- `src/systems/strategic_systems/redirection.py` / `intelligence.py` — read `state.town_center`
  first, but then unconditionally overwrite it with an arbitrary `town_tiles` pick whenever
  `town_tiles` is non-empty (Item 5) — a real compiled world's `town_tiles` is always non-empty, so
  this branch always wins over the (now-correct) `state.town_center` value.
- `src/core/worker_protocol.py`'s `WorkerPacket.town_center` — dead, needs removal or a real
  consumer per the ticket's own AC (Item 4).

### 8. Idea 56 (Drifting Loyalty) — confirmed no shared code path

`grep -rln "Drifting Loyalty\|drifting_loyalty\|idea_56\|idea56" docs/ tickets/ src/` and
`grep -rn "capital.*political.*distance\|political.*distance.*capital" docs/ src/` both returned
zero hits anywhere in the repository. No shared code path exists; confirmed out of scope per the
ticket's own Out-of-Scope section.

### 9. `intelligence.py`'s `next(iter(state.town_tiles))` — same bug as Item 5, not separate

Traced every use of `town_target` in `intelligence.py` (lines 335-338, 385-394, 620-624): it is
computed once via the arbitrary-pick idiom and then applied to every entity's own "carrying items,
return to town" fallback — structurally identical in purpose and call shape to
`redirection.py`'s `sorted(list(state.town_tiles))[0]` (Item 5). Both exist to answer the exact same
question ("where should this entity go to reach town") for the exact same use case, just phrased
with two different arbitrary-selection idioms in two different systems. **Conclusion: this is the
same underlying bug as Item 5, not a separate determinism concern** — fixing Item 5's "nearest tile
to the requesting entity" computation in both `redirection.py` and `intelligence.py` resolves this
`next(iter(...))` concern as a side effect (a per-entity nearest-tile lookup is itself deterministic
given a fixed `town_tiles` set and a tie-break rule), so it does not need separate hardening beyond
what Item 5's fix already requires.

## Mechanics / Engine Constraints

- **Durable State Rule** (project CLAUDE.md): `AuthoritativeState.town_center` is durable state
  representing "the" town location. Item 6's evidence (multi-town-region worlds already shipped and
  regression-tested) means a single scalar tuple cannot durably and correctly represent "the" town
  location for every world topology this codebase already generates — this is the core tension the
  ticket's own Assumptions/Open Questions section flags, and this investigation resolves it with
  concrete evidence in favor of deprecating the single-value field.
- No `docs/mechanics/` chapter formalizes "town_center"/navigation targeting as a law (same
  conclusion the prior, related ticket TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG reached for
  goal-target-resolution). `docs/mechanics/06_worldbuilding_foundation.md` documents `town_tiles`
  membership rules (`type == "town"`, paint-order semantics) but says nothing about how a single
  "town center" point should be derived from one or more town regions — this ticket's Plan phase
  will need to establish that derivation as new documented behavior, not follow an existing
  documented law.
- **Determinism Rule**: any nearest-tile / centroid computation this ticket adds must be a pure
  function of already-deterministic inputs (`town_tiles`, entity position) with an explicit,
  stable tie-break (e.g. sorted `(x, y)` on ties) — `redirection.py`'s existing `sorted(...)[0]`
  tie-break convention is a reasonable precedent to reuse for tie-breaking distance ties, not for
  the primary selection itself.

## Docs Requiring Update

- `docs/mechanics/06_worldbuilding_foundation.md`: needs a new subsection documenting how
  `AuthoritativeState.town_center` (or its replacement) is derived from compiled town-type
  region(s) at `WorldCompiler.compile()` time — currently the chapter documents `town_tiles`
  membership and paint-order rules but has no coverage of town-center derivation at all (confirmed
  by grep — zero matches for "town center"/"town_center" in the chapter body outside the
  `town_tiles` note).
- `docs/parity_ledger/substrate.yaml`: needs a new `SUB-387` entry (next free ID after `SUB-386`,
  confirmed via `grep -oP "id: SUB-\d+"`) documenting the `WorldCompiler.compile()` town_center fix
  — currently no entry in this shard covers town_center derivation.
- `docs/parity_ledger/strategic_cognition.yaml`: needs a new `STRAT-260` entry (next free ID after
  `STRAT-259`) documenting the `FlowFieldService`/`StrategicRedirectionSystem`/
  `StrategicIntelligenceSystem` nearest-tile fixes and the `WorkerPacket.town_center` dead-state
  resolution — distinct from the existing `STRAT-249` entry (which covers
  `_resolve_target_position()`'s `target_position` fallback, a different mechanism that remains
  correct and unchanged by this ticket).
- `docs/engine/contracts/tactical_contract.md`: Section 7 ("Objective Target Resolution", added by
  `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG`) currently documents the `target_position`
  fallback against a world where `town_center` was always `(0,0)` in practice (the bug this ticket
  fixes was live at the time Section 7 was written). It doesn't assert anything actually false, but
  should get a short note once `town_center` carries a real value (or is deprecated in favor of a
  nearest-town lookup) so a future reader doesn't assume Section 7's examples still reflect a
  `(0,0)`-only world.

The following doc was considered but excluded: `docs/engine/kernel.md`'s 7-phase loop and
`docs/engine/authoritative_pipeline.md`'s 37-phase sequence are not required to change — this
ticket's fixes are internal to existing phases (`WorldCompiler.compile()` runs before the kernel
loop starts; the strategic/redirection/navigation fixes are logic changes within already-existing
phases, not new phases or a changed phase ordering).

## Parity Ledger Overlap

- `docs/parity_ledger/strategic_cognition.yaml` — `STRAT-249` (status: `divergent`, priority: P2):
  covers `_resolve_target_position()`'s `target_position` fallback for `TOWN_RETURN`/`RECOVER`/
  `RESOLVE_BLOCKER`. This ticket does not change that mechanism (item 7 confirms it's transitively
  fixed, not independently broken) — `STRAT-249` itself should not need editing, but its
  `divergence_note` was written when `town_center` was always `(0,0)` in every real world; worth a
  one-line cross-reference to the new entry once added, at Implement/Parity phase discretion.
- `docs/parity_ledger/strategic_cognition.yaml` — `STRAT-248` (status: `verified`, priority: P1):
  references the same `TownScorer`/`target_id="town_center"` convention in its own `support_boundary`
  text — informational only, no status change needed.
- No existing entry in `substrate.yaml` covers `WorldCompiler.compile()`'s town_center derivation —
  new `SUB-387` entry needed (see Docs Requiring Update).
- No `P0` entries found among the overlapping entries — no `test_path` gating requirement beyond
  this ticket's own new tests.

## Prior Work

- `stored_artifacts/TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG/` (investigation.md, plan.md,
  test_plan.md) — fixed `TacticalDecisionSystem._resolve_target_position()`'s `target_position`
  fallback so `TOWN_RETURN`/`RECOVER`/`RESOLVE_BLOCKER` objectives navigate somewhere, but that
  ticket's own investigation explicitly did not question whether `state.town_center` itself held a
  real value — it treated `state.town_center=(0.0, 0.0)` as ambient test setup, not as a bug. This
  ticket is the direct follow-up that found the value itself was never real in any compiled world.
  `tests/unit/strategic/test_expanded_goals.py::test_town_return_project_now_produces_real_navigation`
  and `tests/unit/tactical/test_objective_pursuit_coverage.py`'s 3 new tests from that ticket both
  construct `AuthoritativeState`/`ObjectiveState` directly with an explicit `town_center=(0.0, 0.0)`
  — they do not go through `WorldCompiler.compile()`, so they are unaffected by (and do not
  regression-test) this ticket's Item 1 fix.
- `docs/engine/contracts/tactical_contract.md` Section 7 — direct precedent for how this ticket
  should document its own new town-center-derivation behavior (see Docs Requiring Update).

## Risks and Open Questions

- **Central open design decision (must be made explicit in plan.md, not assumed)**: given Item 6's
  concrete evidence that multi-town-region worlds are real and already regression-tested
  (`urban_political.yaml`), keeping `AuthoritativeState.town_center` as a single scalar value means
  picking ONE town arbitrarily (first-by-bounds-order, or similar) and silently under-serving every
  other town in that world for anything gated on `town_center` specifically (as opposed to
  `town_tiles`, which is already a proper multi-town-aware set). The evidence favors deprecating
  `town_center` in favor of a `get_nearest_town_tile(state, position)`-style lookup built on
  `town_tiles`/`regions` — consistent with what `redirection.py`'s fix (Item 5) needs anyway (a
  per-entity nearest-tile function). However, `town_center` has many call sites (Item 2) and full
  removal is a larger, more invasive change than fixing the field's value; the Plan phase should
  weigh "deprecate now" vs. "fix the value now, deprecate later as a follow-up ticket" explicitly
  rather than defaulting to either without discussion — the ticket's own scope text (`## Scope`,
  final bullet) already requires this to be a stated decision, not an implicit one.
- **`WorldCompiler.compile()`'s own multi-town derivation**: even fixing just the *value* (not
  deprecating the field) requires choosing a derivation rule when more than one `type=="town"` region
  compiles into one world (e.g. `urban_political`) — e.g. first-by-region-declaration-order centroid,
  or the centroid of the union of all town tiles (which could land outside any actual town region if
  the two towns are far apart). This must be decided and documented, not left as an unstated
  implementation detail.
- **`FlowFieldService.ANCHORS["WORLD_BOSS"]`** is also hardcoded but explicitly out of this ticket's
  scope (only `target_kind='TOWN'` is named in Scope/AC) — flagging so Implement doesn't
  inadvertently touch it while already inside this file.
- **Existing `test_flow_field_long_distance` test coincidence**: its `town_center=(100.0,100.0)`
  exactly matches `ANCHORS["TOWN"][0]`, so it currently cannot distinguish old vs. new behavior (see
  Item 3) — a new test at a distinct position is required, not just re-running the existing one.

## Anti-Drift Hazards

- **Do not extend arrival-dispatch behavior** for `TOWN_RETURN`/`RECOVER`/`RESOLVE_BLOCKER` once
  entities arrive at a real town_center — that is explicitly out of scope per
  `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG`'s own disclosed, deferred open question, and
  this ticket's AC only covers navigation targeting, not arrival behavior. Fixing the *pointer* must
  not be conflated with fixing *what happens on arrival*.
- **Do not touch `FlowFieldService.ANCHORS["WORLD_BOSS"]`** — out of scope, same class of hardcoding
  but not named in this ticket's Scope/AC.
- **Do not silently change `WorldProceduralGenerator.generate()`'s single-town behavior** — it's
  legacy and out of the ticket's AC list; any change there is a separate, larger ticket given the
  ticket's own explicit scope is `WorldCompiler.compile()`, not the procedural generator.
  `WorldCompiler.compile()` consumes an already-built `WorldSpec` (from either generator or the
  assembly resolver) — the fix belongs at the compiler level so it works for both world-construction
  paths without touching either upstream generator.
- **Do not conflate `WorkerPacket.town_center` removal with `AuthoritativeState.town_center`
  removal** — even if the ticket ultimately deprecates `AuthoritativeState.town_center`, the
  `WorkerPacket` field's fate (remove entirely vs. wire to a real per-worker-relevant value) is a
  separate, narrower AC item with its own evidence (Item 4) — don't let one change bleed into
  assumptions about the other.
- **`redirection.py`/`intelligence.py`'s nearest-tile fix must stay a pure, read-only computation**
  per the Architecture Rule ("Decision logic reads state. It does not authoritatively mutate durable
  state.") — it already only feeds into `StateUpdate`/`NavigationUpdate` construction, not direct
  mutation; keep it that way.
- **`urban_political.yaml`-derived tests are load-bearing regression fixtures** (`baseline_5k.json`,
  `grade_anchors.json`, `test_behavioral_5k.py`) — any change to `WorldCompiler.compile()`'s
  town-center derivation must be verified not to perturb these baselines' other recorded values
  (entity positions, RNG draw sequences) purely by adding a new field write; `town_center` was never
  previously read by anything that would show up in those baselines' asserted values (per Item 7's
  transitive-consumer list), but the baseline snapshots themselves should still be spot-checked
  during Implement/Test, not assumed unaffected.

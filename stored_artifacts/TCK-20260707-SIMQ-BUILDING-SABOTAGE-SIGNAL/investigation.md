---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL
artifact_type: investigation
tags: [simulation-quality, world, observability]
---

# Investigation — TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL

## Current Behavior

### `BuildingSabotageSystem.resolve()` — `src/engine/sabotage.py:12-71`

Wired as authoritative pipeline phase 15 (`building_sabotage`, `LEG-RPG-006`):
- `src/engine/pipeline.py:263` — `run_phase("building_sabotage", update, lambda u: BuildingSabotageSystem.resolve(state, u))`
- `src/engine/cadence.py:34` — default cadence `100`
- `src/engine/phase_graph.py:47` — `PhaseMetadata("building_sabotage", {"combat","town","buildings"}, {"building_updates","social"}, must_run_when_cadence_fires=True)`

Logic (`sabotage.py:27-71`): for each entity's task update, detects a sabotage intent
(`task_upd.work_kind_set == "SABOTAGE"` or `"ENTITY_ACT"` + `payload_set["action"] == "SABOTAGE"`),
validates Chebyshev proximity (`dx<=1, dy<=1`) and target existence via
`SpatialQueryService.get_building_at(state, target_pos)`, then mutates
`update.building_updates[building.id]` with a fixed `hp_delta=-50` and
`functional_set=(new_hp > 0)`. Rejections (`SABOTAGE_OUT_OF_RANGE`, `SABOTAGE_NO_TARGET`) go into
`rejections_delta`. **No `ObservabilityEventEnvelope`/`SimulationEvent` is emitted at this call
site** — `StateUpdate`/`BuildingUpdate` (`src/core/updates.py:717-739`) carry no event-emission
hook, and `sabotage.py` imports nothing from `src.observability`.

### A second, unwired "sabotage" implementation exists — `src/town/sabotage.py::SabotageAction`

`SabotageAction.apply()` (damage = `entity.combat.atk`, Euclidean proximity `<5.0`) is **not**
referenced anywhere in `src/engine/pipeline.py` or any production call path — its only reference
in the entire repo is its own unit test, `tests/unit/world/test_building_sabotage.py`. This is
legacy/parallel dead code. The ticket's Related Code Areas correctly targets `src/engine/sabotage.py`
(the live, pipeline-wired system), not this one — confirmed correct.

### How WORLD-pillar sibling events are actually emitted — this is the key finding

Every comparable WORLD-pillar event (`region_trauma_delta`, `region_ownership_changed`,
`region_transformed`, `hazard_drain_applied`, `node_recharged`, `ecology_cycle_completed`,
`spawn_cadence_fired`, `demographic_birth`, `demographic_mortality`) is **not** emitted from inside
the owning phase's `resolve()`/`apply()` method. They are produced post-hoc by
**`EventExtractor.extract(prior_state, current_state, update, mode)`**
(`src/observability/event_extractor.py`), called once per tick from
`Kernel._phase_observability()` (`src/engine/kernel.py:806-818`, specifically line 818) **after**
the full 31-phase pipeline has run and `update` has been committed to `self._state`. `extract()`
diffs `prior_state` vs `current_state` and inspects the final, merged `StateUpdate`'s typed fields
directly — e.g. the `region_trauma_delta` event (`event_extractor.py:856-863`) is produced by
iterating `update.world_updates.items()` and checking `w_upd.trauma_delta != 0.0`. No phase's
`resolve()` method anywhere in the codebase directly instantiates and emits a `SimulationEvent`
from within its own execution.

`update.building_updates` (the exact field `BuildingSabotageSystem.resolve()` mutates) currently
has **no corresponding block in `event_extractor.py`** — confirmed via `grep`; only
`src/engine/town_resolution.py` and `src/engine/sabotage.py` write to `building_updates`, and
`event_extractor.py` has no read of it. This matches the ticket's claimed gap exactly, but
**changes where the fix belongs**: not a new emission call inside `sabotage.py::resolve()` (it has
no event emitter available at that point in the pipeline — the ticket's own Assumptions/Open
Questions section explicitly anticipated this and pre-authorized documenting it as an
implementation finding), but a new diff block in `EventExtractor.extract()` reading
`update.building_updates`, mirroring the existing `region_trauma_delta` block almost exactly.

`hp_delta < 0` on a `BuildingUpdate` is a reliable, unambiguous proxy for sabotage specifically:
grep confirms the only other writers of `building_updates` are `src/engine/town_resolution.py`
(sets `functional_set=False` on faction insolvency — never touches `hp_delta`) and
`src/core/conservation.py` (touches only `.inventory` on shop transactions — never `hp_delta`).
`src/town/sabotage.py` (the dead legacy path, above) is the only other `hp_delta`-writer in the
repo and is unreachable in production.

Region attribution for the new event's payload can reuse the existing
`SpatialQueryService.get_building_region(state, building_id) -> Optional[RegionState]`
(`src/engine/spatial_query.py:239`), already used identically by `town_resolution.py` and
`conservation.py` for the same building→region lookup. `BuildingState`
(`src/core/state.py:1017-1043`) itself carries no `region_id` field, only `position`.

### `WorldDynamicsScorer` — `src/simulation_quality/scorers/world_dynamics.py:11-178`

`EVENT_TYPES` (lines 17-32) is a class-level tuple that `QualityHub.__init__` auto-registers into
`SCORER_REGISTRY` (`src/simulation_quality/quality_hub.py:103-107`) — there is no separate manual
central enum to edit; adding `"building_sabotaged"` to this tuple **is** the registration step
Scope item 2 refers to. `score()` dispatches on `envelope.event_type` via a chain of `if et ==`
branches, each building a `ScoreRecord` through the local `_rec(delta, reason, tags)` helper, which
already reads `region_id=payload.get("region_id")` — matching the payload shape recommended above.

### `scoring_weights.yaml` WORLD section — `config/simulation_quality/scoring_weights.yaml:121-141`

Flat `key: float` pairs per pillar, both positive ("aliveness") and negative ("degenerate") tags.
Loaded through `ScoringWeights` (`src/simulation_quality/weights.py`), a frozen Pydantic model —
`self.weights["rule_key"]` raises `KeyError` with the full available-key list if missing (no silent
default), so a scorer branch referencing an undefined key fails loudly, not silently.

## Mechanics / Engine Constraints

- `docs/engine/authoritative_pipeline.md` — Singular Bottleneck Law (top of file): all state
  transitions pass through the pipeline as `StateUpdate`; phase 15 = `building_sabotage`
  (`LEG-RPG-006`). Scope item 3 (no change to `resolve()`'s mutation logic) is consistent with this
  — the new work is purely additive observability, downstream of the committed `StateUpdate`.
- `docs/simulation_quality/quality_scoring_contract.md` §2 "Coupling law": `src/simulation_quality/`
  must never import from `src/engine/`, `src/domains/`, `src/systems/`, or any domain-internal
  module — only `ObservabilityEventEnvelope` and the module's own types. Confirmed
  `world_dynamics.py`'s current imports already comply; the new branch must not import
  `SpatialQueryService` or anything engine-side (that lookup belongs in `EventExtractor.extract()`,
  which already legitimately touches engine-adjacent state).
- §3 Performance Contract: scoring must add < 0.1ms/event, zero simulation-loop blocking — a new
  `if et ==` branch is O(1); the `EventExtractor` diff block is O(len(building_updates)), matching
  the existing `world_updates` loop's cost profile.
- §4.8 "no numeric literals in scorer code" — the new branch must read
  `self.weights["<new_rule_key>"]`; the delta value itself lives only in `scoring_weights.yaml`.
- §7.2 (Adding a Scoring Rule to an Existing Pillar) — the exact 6-step protocol the ticket's Scope
  already quotes verbatim; followed correctly.
- §7.3 (Conflict Detection) — verified no existing pillar's `EVENT_TYPES` references anything
  building/infrastructure-related; WORLD has no dual-ownership conflict to resolve.
- §7.5 "Pillar Completeness Audit (2026-07)" — **citation verified accurate**: this subsection
  exists at `docs/simulation_quality/quality_scoring_contract.md` lines 1071-1112 (landed via
  `TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC`), and its text matches what this ticket's Request
  Summary paraphrases — including the `FACTION`-as-rejected-secondary-owner framing and the exact
  file:function citation for `BuildingSabotageSystem.resolve()`.
- `docs/simulation_quality/event_type_coverage.md` §6 "Maintenance Notes": "When adding a new
  `event_type` to `event_extractor.py` or any domain emitter, check this table first" — this doc is
  the authoritative registry of every SimQ event_type's emission status and is **not** listed in
  this ticket's Related Docs/AC, but every sibling WORLD event in its §1.1 table has a row; leaving
  `building_sabotaged` out would make this doc immediately stale against its own stated maintenance
  contract. Flagged as a likely expected (if not literally AC-mandated) companion update.
- Doc/code parity drift (pre-existing, out of scope, but a hazard — see below): `docs/simulation/
  town_contract.md`'s "Sabotage Pipeline (`LEG-RPG-006`)" section documents `SabotageAction.apply()`
  (the *dead* `src/town/sabotage.py` path — Euclidean dist `<5.0`, damage = entity ATK), not the
  live `BuildingSabotageSystem.resolve()`. `docs/systems/world_evolution_and_resilience.md` §2
  "Building Durability & Sabotage" describes a **third**, non-matching design (`CombatAction`-driven,
  50% raw ATK, `durability` attribute, `RaidAI` targeting) that matches neither code path. Neither
  doc should be used as a source of truth for payload/formula details in this ticket's
  implementation — anchor strictly to `src/engine/sabotage.py`, which the ticket's Related Code
  Areas already correctly does.

## Parity Ledger Overlap

- **`WORLD-087`** (`docs/parity_ledger/world_dynamics.yaml:894-903`): "Building sabotage affects
  building state authoritatively." `status: verified`, `priority: P0`, `test_path: null`. Covers the
  *mutation* only (hp/functional state change), not observability — this ticket does not modify the
  mutation, so `WORLD-087` itself needs no status change. However, per the repo's parity rule ("if no
  entry exists, add one"), the new *observability* behavior (event emission + WORLD scoring) is not
  covered by any existing entry. **Recommend a new entry** (e.g. `WORLD-088`) documenting "building
  sabotage emits a scored `building_sabotaged` WORLD-pillar signal," with a real `test_path` pointing
  at the new unit test — unlike `WORLD-087`'s `null`.
- **`COMB-068`/`COMB-069`/`COMB-070`** (`docs/parity_ledger/combat_movement.yaml:711-740`): building
  sabotage apply/validation/application tests, all `P0`, `status: verified`, `test_path: null`
  (proof via "exhaustive checklist audit Phase 1-11", not a direct pytest reference). No change
  required for this ticket's scope; noted only because they share the "sabotage" keyword and a
  pre-existing pattern of `P0` entries with `test_path: null` that this ticket should not perpetuate
  for its *own* new entry.
- No `P0` entry currently blocks this ticket (neither `WORLD-087` nor `COMB-068/069/070` is being
  modified), but any new entry this ticket adds should carry a real `test_path` given the repo rule
  that `P0` entries require a passing `test_path`.

## Prior Work

- **`TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS`** (referenced throughout `event_type_coverage.md` §1.1/
  §3.9; stored artifacts under `stored_artifacts/TCK-20260629-SIMQ-EMIT-WORLD` and
  `stored_artifacts/TCK-20260701-SIMQ-EMIT-WORLD2`) is the closest direct precedent: same class of
  change — new `EventExtractor.extract()` diff block + new `WorldDynamicsScorer` branch +
  `scoring_weights.yaml` WORLD-section key + contract §5/§6 update + `event_type_coverage.md` row.
  Use as the structural template.
- **`TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC`** — hard dependency, landed; §7.5 citation verified
  accurate above.
- Existing test file pairs to mirror: `tests/unit/observability/test_event_extractor_world_dynamics.py`
  (extractor-side unit tests, `MagicMock`-based state/update fixtures) and
  `tests/simulation_quality/test_world_dynamics_scorer.py` (scorer-side unit tests, using the
  session-scoped `scoring_weights` fixture from `tests/simulation_quality/conftest.py`, which loads
  the real `config/simulation_quality/*.yaml` files — this **is** what the contract's "inject a
  `ScoringWeights` fixture, not production config values" language means in this repo's actual
  convention: constructor-injected via the shared fixture, not hand-typed example numbers hardcoded
  per test file. All existing scorer test files use this identical pattern.)

## Risks and Open Questions

1. **No entity/AI/worker code anywhere in `src/` currently generates a `SABOTAGE` intent.**
   Repo-wide `grep -rin "sabotage" src/` (excluding tests/reviews-export) surfaces exactly four real
   hits: the consumer (`sabotage.py`), a legality gate that can *reject* it under regional
   suppression (`src/engine/legality.py:138`, `action_kind in ["SABOTAGE","RECRUIT","THEFT"]`), and
   two unrelated "building is sabotaged and non-functional" comments in `shop.py`/`blacksmith.py`
   that just check `building.functional`. No strategic/goal-selection, quest-reward, or worker-
   proposal code anywhere sets `task_upd.work_kind_set = "SABOTAGE"` or
   `payload_set["action"] = "SABOTAGE"`. The ticket's own cited corpus evidence
   ("`urban_political`'s resolved world spec... references sabotage-relevant buildings") resolves,
   on inspection, to a single quest id string, `trade_investigate_sabotage`
   (`data/worlds/urban_political/resolved/world.resolved.yaml:375`) — a quest *name*, not a
   `SABOTAGE`-intent producer. **This makes a zero-hit calibration result the expected outcome, not
   merely a possible one.** Scope item 5 and the ticket's own Assumptions section already
   pre-authorize an honestly-documented null result — this finding should be read as confirmation
   that the null-result branch is the realistic path, and the before/after write-up should state
   this evidence plainly rather than treat a zero-hit run as a surprise or a bug. This does **not**
   block AC-4 (the unit test injects a synthetic envelope/update and does not depend on live corpus
   content).
2. **Emission-site mismatch vs. the ticket's literal Scope wording** (see Current Behavior above,
   third subsection) — Scope item 1 says "emit... from `BuildingSabotageSystem.resolve()`... follow
   the existing emission pattern used by other engine-phase systems," but the actual repo pattern for
   every WORLD-pillar sibling event is diff-based extraction in `EventExtractor.extract()`, not
   direct instrumentation inside the phase. The ticket's Assumptions/Open Questions section already
   anticipated exactly this possibility and pre-authorized documenting it as an implementation
   finding rather than silent scope expansion — this is that finding. No open decision is required;
   the planner should route the change to `event_extractor.py`, not `sabotage.py`.
3. **Delta polarity is non-obvious and should be a deliberate planner decision, not a default.** WORLD
   scores "is the world alive/reacting," not narrative good/bad — `trauma_feedback` (+2) and
   `hazard_active` (+1) are positive even though they represent harm, because they signal real
   consequence rather than a static backdrop. `building_sabotaged` most plausibly follows the same
   pattern (positive — evidence of real infrastructure consequence) rather than defaulting to
   "damage occurred → negative delta," since none of WORLD's existing *degenerate* tags describe
   damage occurring — they all describe an *absence* of world activity (`calamity_dormant`,
   `world_static`, `world_depopulating`, etc.). Flagging so this isn't decided by instinct during
   implementation without a plan-level record.
4. Two same-subsystem-named test files could be confused: `tests/unit/world/test_building_sabotage.py`
   tests the *dead* `SabotageAction` legacy path (unrelated to this ticket); it must not be mistaken
   for coverage of the live `BuildingSabotageSystem`.

## Anti-Drift Hazards

- `tests/integrity/test_logic_guards.py` asserts pipeline phase-call ordering via
  `source.find("BuildingSabotageSystem.resolve")` string-position checks against
  `src/engine/pipeline.py`. This ticket's fix belongs entirely in `event_extractor.py` and
  `world_dynamics.py` — do not touch `pipeline.py`'s call site or phase ordering, and re-run this
  guard test to confirm it stays green.
- `src/simulation_quality/` coupling law (§2): the new `WorldDynamicsScorer` branch must import
  nothing beyond `ObservabilityEventEnvelope`/the module's own types — do not reach into
  `src.engine.sabotage` or `src.core.state` from the scorer; any engine-side lookup (e.g.
  `SpatialQueryService.get_building_region`) belongs in `event_extractor.py` only.
- §7.3 no-dual-ownership: do not add a `FACTION`-pillar rule for the same event, even as a
  "secondary" — the ticket's Out of Scope explicitly forbids this; verify `FactionScorer.EVENT_TYPES`
  is untouched by the diff.
- No numeric literals in scorer code (§4.8) — the new branch must read
  `self.weights["<new_key>"]`; the key/value pair belongs only in `scoring_weights.yaml`'s `WORLD:`
  section.
- Do not touch `BuildingSabotageSystem.resolve()`'s `damage = 50` constant, proximity check, or
  `functional_set` logic — explicitly out of scope; this ticket adds observability only.
- `tests/simulation_quality/fixtures/grade_anchors.json` regression anchors for `urban_political` —
  even a single new WORLD-pillar event could nudge `WORLD`'s `raw_score`/`normalized_score`; run
  `make evaluate --dry-run` per AC and update anchors only if a genuine regression is confirmed, not
  speculatively.
- `docs/simulation_quality/event_type_coverage.md` — not in the ticket's literal AC list, but its own
  §6 Maintenance Notes require a new row whenever `event_extractor.py` gains a new `event_type`;
  every existing WORLD sibling event has one. Leaving it out would create an immediate, silent
  doc/code drift in a doc explicitly designed to prevent that class of drift.

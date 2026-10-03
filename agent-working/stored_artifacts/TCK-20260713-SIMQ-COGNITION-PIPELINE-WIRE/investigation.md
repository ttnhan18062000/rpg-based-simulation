---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE
artifact_type: investigation
tags: [simulation-quality, cognition, information, self-model]
---

# Investigation — TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE

## Current Behavior

**`ActionIntentAdapter.execute()`** (`src/engine/intent/action_intent.py:32-202`) is a fully
implemented, well-tested classmethod. It requirement-gates (`Requirement`/`RequirementEvaluator`,
lines 57-98), dispatches by `intent.kind`, and for `ASK_INFORMATION` (lines 127-183) discriminates
on `"query_kind" in intent.payload`: absent → byte-identical legacy adventure-domain deduction
(`cost_gold`, line 141-145); present → the information-domain close-the-loop path added by
`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE` (deducts `cost_paid`, builds an
`InformationQuery`, runs `InformationResponseNormalizer.normalize()` →
`InformationAssimilationService.assimilate()`, returns `EntityUpdate(self_model_bundle_set=...,
strategic=assim.strategic_update, inventory=...)`). Every internal branch is tested directly
(`test_ask_information_intent_execution_closes_the_loop`,
`tests/integration/domains/information/test_phase5_information_belief_phase.py:113-144`) but
**confirmed** (`grep -rn "ActionIntentAdapter" src/`) to have exactly two references under `src/`:
the class definition itself and a docstring mention at `src/domains/adventure/resolver.py:20`.
No production code calls `.execute()`.

**`InformationBeliefPhase.apply()`** (`src/domains/information/phase.py:28-111`) Branch B
(lines 84-106): for an actor with unresolved `unknowns` and no pending response this tick, it
calls `InformationQueryRouter.route()` then loops candidates through
`InformationIntentResolver.resolve()` until one yields a real `ActionIntent` (`isinstance` check,
line 96). `InformationIntentResolver.resolve()` (`src/domains/information/resolver.py:51,77`)
only ever constructs `ActionIntent(kind="MOVE_TO", ...)` or `ActionIntent(kind="ASK_INFORMATION",
...)` — both branches already fully handled by `ActionIntentAdapter.execute()`, so no new intent
kind needs support. The routed `ActionIntent` is placed into
`EntityUpdate(entity_id=actor.id, intent_results=[result], property_updates={...})`
(phase.py:97-104) — **`intent_results` is typed `List[IntentResult]`** (`src/core/updates.py:638`,
`IntentResult` defined `src/core/state.py:655`, an unrelated dataclass:
`transaction_id/accepted/reason/source_kind/source_id`) but Branch B stores a raw `ActionIntent`
object there instead — a pre-existing, harmless-at-runtime type mismatch (Python doesn't enforce
dataclass field types) that this ticket's new phase must read past, not "fix" (out of scope; fixing
the type annotation would be a separate, unscoped cleanup).

**`src/engine/pipeline.py`** (`AuthoritativeApplyPipeline.refine()`, lines 41-348): the `run_phase`
helper (lines 102-133) is the uniform wiring pattern — `mode = ff_manager.get_flag_mode(flag)`,
skip if `OFF`, else check `PhaseDependencyGraph.should_run_phase(...)`, else invoke `phase_fn(upd)`
and merge/discard per `SHADOW`/`ON`. Confirmed exact ordering:
- `self_model` (line 143, flag `ENABLE_SELF_MODEL_COGNITION`) — populates `entity.self_model`,
  runs first.
- `information_belief` (line 148-153, flag `ENABLE_BELIEF_ASSIMILATION`) — Branch B reads
  `self_model.knowledge.unknowns`, produces the routed `ActionIntent` in `intent_results`.
- `cooperation` (line 156-159, flag `ENABLE_SOCIAL_COOPERATION`) — unrelated domain (social),
  runs immediately after.
- `adventure_decision` (line 226-237, flag `ENABLE_ADVENTURE_ROUTING`) — much later, after faction
  phases; unrelated to Branch B's intent.

**No FeatureFlagManager registration → no way to turn a flag on.** `FeatureFlagManager.__init__`
(`src/domains/optimization/feature_flags.py:12-24`) hardcodes a 10-entry dict. `set_flag_mode`
(line 36-38) only writes if `flag in self._flags` — silently no-ops for unregistered keys.
`get_flag_mode` (line 33-34) falls back to `FeatureMode.OFF` via `.get(flag, FeatureMode.OFF)`.
**Confirmed: a brand-new flag name is unusable (permanently reads as OFF, `set_flag_mode` is a
silent no-op) unless it is added to the `_flags` dict in `feature_flags.py`.** This is a hard
implementation requirement, not optional.

**Dirty-set skip logic does not apply at this pipeline position — confirmed by trace.**
`PhaseDependencyGraph.should_run_phase()` (`src/engine/phase_graph.py:71-153`) checks
`if update.dirty_set is None: return True` (line 127-128) before any domain-dirty logic. In
`refine()`, `update.dirty_set` is only ever set via `update = update.replace(dirty_set=...)` at
line 257 (first occurrence, immediately before `interaction_routing`) — well **after**
`self_model`/`information_belief`/`cooperation`/`adventure_decision` all run. So for the entire
early section of the pipeline (where this ticket's new phase must live), `update.dirty_set is
None` unconditionally, and `should_run_phase` always returns `True` regardless of any
`input_domains` declared for the phase in `PhaseDependencyGraph.PHASES`. This matches
`information_belief`'s own registration (`{"strategic", "social"}` input domains,
`phase_graph.py:63`) despite `mark_from_update()` (`src/core/dirty.py:139-180`) **not** marking
`self.strategic` for an `EntityUpdate` that only sets `intent_results`/`property_updates` (only
`.strategic`/`.task`/`.interaction`/`.quest`/`.combat`/`.inventory`/`.biological` presence marks
`strategic` dirty, line 154-173) — i.e. the existing `information_belief` phase already relies on
this "dirty_set is None this early" bypass to be reliably reachable; the new phase can register in
`PhaseDependencyGraph.PHASES` cosmetically (for documentation/consistency) but must not depend on
domain-dirty marking for correctness at this pipeline position.

**Merge mechanics.** `EntityUpdate.merge()` (`src/core/updates.py:663-697`) additively merges
`inventory`/`strategic` (via their own `.merge()`), and **overwrites (last-write-wins)**
`self_model_bundle_set`/`group_id_set` (line 693-694: `if other.X is not None: changes["X"] =
other.X`). Since Branch B's own `EntityUpdate` for the routing tick never sets
`self_model_bundle_set` (only `intent_results`/`property_updates`), and the new phase's
`ActionIntentAdapter.execute()` call happens in the same tick after Branch B's update already sits
in `update.entity_updates`, merging the adapter's returned `EntityUpdate` onto the existing one via
`existing.merge(adapter_upd)` is safe and matches the exact pattern `ActionRoutingPhase.route()`
already uses (`src/engine/pipeline_phases/actions.py:198-199`:
`existing_upd.merge(action_upd)`).

## Mechanics / Engine Constraints

- `docs/engine/kernel.md` §"Phase Domain Permissions" (lines 128-142) governs the **7 TickPhase**
  granularity (INIT/SCHEDULING/COLLECTION/RESOLUTION/CLEANUP/ADVANCEMENT/PERSISTENCE), enforced by
  `src/engine/phase_domain_permissions.py` + `tests/architecture/test_phase_domain_permissions.py`.
  This new work is a sub-phase *inside* `RESOLUTION` (same as `information_belief`/`cooperation`,
  neither of which appear in `phase_domain_permissions.py`) — **no new `TickPhase` entry or
  permissions-file change is required.**
- `docs/engine/kernel.md` line 19: "Deterministic Order: within the Resolution phase, entities are
  processed in a deterministic order (usually sorted by ID)." `ActionRoutingPhase.route()` honors
  this via `sorted(actors_with_tasks)` (actions.py:108). The new phase must iterate
  `update.entity_updates` (or the subset with non-empty `intent_results`) in **sorted entity-ID
  order** to preserve determinism, not raw dict iteration order.
- No dedicated Mechanics Bible chapter covers self-model query-routing or `ActionIntentAdapter`
  specifically; `docs/mechanics/04_strategic_cognition.md` covers goal hierarchy/knowledge
  management at a level above this execution-adapter mechanism. No formula/law in the Bible is
  contradicted or extended by this wiring — it is purely an engine call-site addition, not a new
  mechanic.

## Parity Ledger Overlap

- **`INFRA-267`** (`docs/parity_ledger/infrastructure.yaml`) — status `verified`, priority `P1`.
  Its own `support_boundary` explicitly states: *"`ActionIntentAdapter.execute()` has no
  production tick-pipeline call site today (unchanged by this ticket) — the close-the-loop fix
  (fix 5) is verified via direct test-harness invocation... not via live-gameplay activation."*
  This ticket is the direct, named follow-up that changes that boundary claim. **`INFRA-267`'s
  `support_boundary` text must be updated** (or a new successor entry added, per the
  `INFRA-259`/`INFRA-260`/`INFRA-266`→`INFRA-267` precedent already established in this same
  lineage) once a production call site exists — do not leave `INFRA-267` claiming "no call site"
  after this ticket lands.
- **`INFRA-266`** — the original pre-fix root-cause record, explicitly left untouched by
  `INFRA-267`'s own precedent (historical). Not touched by this ticket either.
- No entries in `docs/parity_ledger/strategic_cognition.yaml` (`STRAT-001`..`STRAT-0xx`) reference
  `ActionIntentAdapter`, `InformationBeliefPhase`, or self-model query-routing by name — grepped
  for "self_model"/"information"/"cognition"/"ActionIntent", no hits. This subsystem's parity
  entries live entirely in `infrastructure.yaml`, not `strategic_cognition.yaml`; no
  `strategic_cognition.yaml` entry needs updating for this ticket.
- **No P0 entries found touching this scope** — `INFRA-267` is P1. No blocking passing-test
  requirement beyond the normal Testing Rule.

## Prior Work

- **`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`** (done) — implemented and verified the exact
  execution logic this ticket wires in. Its own closing note (Implementation Notes, final
  paragraph) is explicit and load-bearing: *"`ActionIntentAdapter.execute()` remains unwired into
  the production tick pipeline... this ticket does not add one (explicitly out of scope)... Do not
  read this ticket as having activated Branch B in any live simulation."* This ticket is exactly
  the deferred follow-up that closing note anticipated.
- **`TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`** (done) — established self-model
  *materialization* (the `self_model` phase) generalizes to real archetype worlds; query-routing
  (Branch B) is the other half, addressed by the routing-closure ticket above and reachable-in-
  production by this ticket.
- **`TCK-20260713-SIMQ-COVERAGE-DECISION-GATE`** (done) — the Phase 5 ruling
  (`docs/plans/archive/simq_development_roadmap.md` lines 456-467) that named this exact gap
  ("wiring that call site into the production pipeline") as "a distinct future initiative... not
  folded into 'add more worlds.'" This ticket is that initiative.
- **`urban_political_selfmodel_probe.yaml`** (`config/simulation_quality/profiles/`) — the pattern
  to mirror for live-fire verification. It is a *permanent, non-shipped* probe profile (not
  referenced by any world's default calibration chain), turning `ENABLE_SELF_MODEL_COGNITION` ON
  while deliberately leaving `ENABLE_BELIEF_ASSIMILATION` OFF (so Branch B never runs in that
  specific probe). Its anchor test is
  `test_urban_political_selfmodel_cognition_isolated_grade_anchor`
  (`tests/simulation_quality/test_grade_regression.py:334-378`), gated by a `grade_anchors.json`
  key `urban_political_selfmodel_probe_seed42_200t` and a `pytest.skip()` fallback if the anchor
  key or calibration report is absent (calibration output is `.gitignore`d — regenerate via
  `tools/calibrate_simq.py`, not committed).
- **`TCK-20260713-SIMQ-RAWSCORE-PERSIST`** (done, same epic batch) — changed
  `tests/simulation_quality/fixtures/grade_anchors.json`'s schema: every anchor entry now stores
  `{grade, score}` per pillar (using `normalized_score`, not `raw_score`), and
  `test_grade_regression.py`'s anchor-band tests now assert an independent score tolerance
  (`abs_delta <= max(0.05, 0.20 * |anchored_score|)`) alongside the letter-band check. **The new
  grade-anchor entry this ticket adds (test_plan.md New Test 5) must be generated in this current
  `{grade, score}` schema, not a bare grade string** — a hand-authored or stale-schema entry would
  fail the score-tolerance check that ticket added, independent of whether the letter grade is
  correct.
- **`TCK-20260713-SIMQ-SCORE-CEILING-FIX`** (done, same epic batch) — recalibrated
  WORLD/ECONOMY/PROGRESSION/INFORMATION scoring weights and confirmed all 4 pillars now reach grade
  A on their richest corpus scenario. Its Completion Summary records a **known, pre-existing,
  environment-load-sensitive nondeterminism in COGNITION's self-model loop-detection** (unrelated
  to that ticket's own weight-only diff, confirmed via 3 clean reproductions), filed separately as
  `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` (open, standard tier, not part of this epic
  folder — out of scope for this ticket to fix). Relevant here only as **Test-phase context**: if
  the full `evaluate_simq.py --dry-run` sweep (Acceptance Criterion 4) flags a COGNITION-pillar
  delta with the new flag left OFF, check first whether it matches this known flaky signature
  before treating it as a regression caused by this ticket's pipeline change.

## Risks and Open Questions

- **Flag registration is mandatory, not optional** (see Current Behavior) — the implementer must
  add the new flag to `FeatureFlagManager._flags` in `feature_flags.py`, or the new probe profile's
  `feature_flags:` block will silently no-op and the whole verification will falsely appear
  "correctly OFF" when it is actually unreachable. Flag off-by-registration is the single most
  likely silent-failure mode for this ticket.
- **Open question (does not block implementation, but affects the probe fixture design):** should
  the new probe profile be a *third* variant alongside `urban_political_selfmodel_probe.yaml` (this
  ticket's out-of-scope note explicitly forbids turning the flag on in any *shipped* profile, but a
  new dedicated, non-shipped probe fixture — e.g.
  `urban_political_selfmodel_execution_probe.yaml` — mirroring the existing probe's structure, is
  exactly what "probe-profile-style calibration run" in the Acceptance Criteria calls for), or
  should the existing `urban_political_selfmodel_probe.yaml` be *extended in place* to add
  `ENABLE_BELIEF_ASSIMILATION: "ON"` plus the new flag? **Extending in place would change
  `INFRA-267`'s already-verified `support_boundary` claim that this probe "only turns
  ENABLE_SELF_MODEL_COGNITION ON and leaves ENABLE_BELIEF_ASSIMILATION OFF"** and would invalidate
  `test_urban_political_selfmodel_cognition_isolated_grade_anchor`'s hardcoded assertion
  `pillars["INFORMATION"]["event_count"] == 0` (grade_regression.py:357) — that assertion depends
  on Branch A/B never running in this specific profile. **Recommend: add a new, separate probe
  profile file** rather than mutating the existing one, to avoid a parity-ledger/test collision.
  This is a design decision for the planner/implementer, not a blocking unknown — flagging so it
  isn't accidentally resolved the collision-prone way.
- **Phase-graph registration is optional but should be added for hygiene.** Not registering the new
  phase in `PhaseDependencyGraph.PHASES` means `should_run_phase` always returns `True` for it
  (falls through the `if phase_name not in PhaseDependencyGraph.PHASES: return True` early return,
  `phase_graph.py:81-82`) — functionally identical to registering it with domains that are
  ultimately inert at this pipeline position (see Current Behavior's dirty-set trace). Either
  choice is safe; the existing sibling phases (`information_belief`, `cooperation`) *are*
  registered, so registering for consistency/documentation is the lower-drift choice even though it
  has no behavioral effect at this pipeline position today.
- **What `entity`/`context` to pass to `ActionIntentAdapter.execute()`.** `ActionRoutingPhase`
  builds a full `sliding_state` with `working_entities` reflecting same-tick prior mutations
  (actions.py:99-106). Branch B's routed intents are always `MOVE_TO`/`ASK_INFORMATION`, and neither
  branch's `Requirement` list depends on `context` (only `BUY_ITEM`/`REQUEST_CRAFT`/
  `HARVEST_RESOURCE` populate `reqs`, action_intent.py:59-77) — so passing the original
  `state.entities[actor_id]` and `context=state` (no sliding-state construction) is sufficient and
  matches `InformationBeliefPhase`'s own direct-call convention (phase.py never builds a sliding
  state either). Building a full sliding state would be unnecessary complexity for the two intent
  kinds Branch B can currently produce — flagging as a scope guard, not an open question requiring
  a decision.

## Anti-Drift Hazards

- **Do not widen `ActionIntentAdapter.execute()`'s dispatch or the `ASK_INFORMATION` branch** —
  ticket's Out of Scope explicitly forbids touching its internals; this ticket only adds a call
  site.
- **Do not turn the new flag ON in any shipped world profile** (`data/worlds/*/world.yaml`'s
  default calibration chain or any `config/simulation_quality/profiles/*.yaml` that a live world
  resolves to) — explicitly out of scope. Verify via
  `tests/integration/test_world_profile_feature_flag_guardrail.py`'s pattern (though its
  `_GATED_FLAGS` tuple, `test_world_profile_feature_flag_guardrail.py:33`, is hardcoded to 3 names
  and will **not** automatically catch a new flag being turned on in a shipped profile — if the new
  flag name should be guardrailed the same way, that tuple needs an explicit addition; this is a
  planner decision, not automatic).
- **Do not consume `intent_results` from any source other than the same-tick `information_belief`
  phase's output.** `IntentResult` (the field's *declared* type) is a distinct, unrelated dataclass
  used by `src/engine/economy.py` and `src/engine/patches.py` for resource-transfer outcomes — the
  new phase must not accidentally iterate/execute those `IntentResult` entries as if they were
  `ActionIntent` objects. Since Branch B is currently the *only* producer that stores raw
  `ActionIntent` objects in `intent_results` (confirmed by the earlier `grep -rn
  "intent_results"` sweep — `economy.py`/`patches.py` always construct real `IntentResult`
  instances), a safe implementation should either (a) filter by `isinstance(x, ActionIntent)`
  before calling `.execute()`, or (b) only read `intent_results` from the specific `EntityUpdate`
  object that `information_belief`'s own phase output produced this tick (not the accumulated
  `update.entity_updates` after later phases might merge in real `IntentResult` entries from
  elsewhere). Recommend (a) — an explicit `isinstance` filter — as the more robust, drift-proof
  choice, and worth a dedicated regression test (see test_plan.md).
- **Do not run the new phase before `information_belief`.** The new phase's entire purpose depends
  on `intent_results` populated in the same tick by Branch B; if pipeline ordering ever gets
  refactored, this dependency is easy to silently break since nothing enforces phase order beyond
  source-line position in `refine()`.
- **Do not let the new phase's merge silently drop `IntentTrace` observability.**
  `ActionIntentAdapter._traces` (a class-level list, `action_intent.py:38`) already accumulates
  every `.execute()` call as a side effect — this is pre-existing, class-level (not tick-scoped)
  mutable state, already used by the direct-invocation tests via `get_traces()`/`clear_traces()`.
  The new phase does not need to do anything additional for this, but should not introduce a
  competing trace/observability mechanism.

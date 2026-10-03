---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE
artifact_type: investigation
tags: [cognition, adventure]
---

# Investigation — TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE

## Current Behavior

### `src/domains/adventure/phase.py` (re-verified current state, post-ticket-2)

- Lines 1-24: module imports. `_threat_resolved` is now imported from
  `src.systems.strategic_systems.intelligence` (line 21) — confirming
  `THREAT-RESOLVED-ARBITER-RELOCATION` already moved it out; it is no longer defined in this
  file.
- Lines 27-58: `_resolve_cognition_profile_id(entity)` — module-level function, 3-tier profile
  resolution (explicit `cognition_profile_id` → `role_id` → `RoleDefinition.default_cognition_profile`
  → legacy `EntityRole.HERO` → `"hero"` role default). **Ticket's own Scope text cites lines
  49-96 for this + `_supports_adventure_routing` — that citation is stale** (it predates
  ticket 2's removal of `_threat_resolved` from this file, which shifted everything below it up
  by ~22 lines). Current, re-verified range: 27-58.
- Lines 61-74: `_supports_adventure_routing(entity, cache)` — eligibility predicate, per-call
  cache dict. Current, re-verified range: 61-74.
- Lines 77-198: `AdventureDecisionPhase` class, single `apply()` staticmethod. Builds eligible
  hero list (61-74's predicate + alive + active), for each hero: checks project lock
  (`tick < active_proj.lock_until_tick and not _threat_resolved(hero, state)` — line 129, now
  calling the relocated helper), generates candidates via `AdventureRouteGenerator` +
  `ResourceOpportunityProvider`/`ServiceOpportunityProvider`, decides via
  `AdventureDecisionService.decide()`, writes a decision trace via
  `DecisionTraceWriter.write_trace()` (lines 118, 148-152 — **see Anti-Drift Hazards, this has
  no equivalent in the new path**), and commits via
  `StrategicIntelligenceSystem.evaluate_project_switch()` (line 170 — already routes through the
  shared arbiter, confirmed by `test_phase3_project_switch_routing_guard.py`'s AST guard).

### `src/engine/pipeline.py`

- Lines 236-247: "Enhanced RPG Phase 3: Adventure Routing" — `run_phase("adventure_decision",
  update, lambda u: u.merge(AdventureDecisionPhase.apply(state, faction_directives=...,
  factions=state.factions)), "ENABLE_ADVENTURE_ROUTING")`. This is the entire registration to
  remove; import is a function-local `from src.domains.adventure.phase import
  AdventureDecisionPhase` at line 237, not a module-level import — removing both the `run_phase`
  call and this local import fully satisfies AC2 (`grep AdventureDecisionPhase` returns no
  matches in this file).
- Line 347: `run_phase("strategic_intelligence", update, lambda u:
  StrategicIntelligenceSystem.fused_strategic_pass(state, u, cadence=cadence))` — **unconditional,
  no feature-flag string**, runs unconditionally every tick, **after** `adventure_decision` in
  phase order (line 347 > line 236 in the same `apply()` method body). This ordering is load-bearing
  for the "does deletion flip the switch" analysis below.

### `src/ai/goals/adventure_scorer.py`

- Lazily imports `_supports_adventure_routing` from `src.domains.adventure.phase` at call time
  (line 48: `from src.domains.adventure.phase import _supports_adventure_routing`), specifically
  to avoid a real, confirmed transitive circular-import path (documented in the surrounding
  comment, lines 31-47): `phase.py` → `src.systems.strategic` → `src.systems.strategic_systems.
  intelligence` → `src.ai.goals` (`GoalRegistry`). **This import breaks the moment `phase.py`'s
  copy of `_supports_adventure_routing` is deleted** — it must become a same-module reference
  (the function is relocating into this exact file) rather than an import, once relocation
  lands. `_resolve_cognition_profile_id` is not directly imported here (only reached indirectly
  through `_supports_adventure_routing`'s own body), but both must relocate together per Scope —
  `_supports_adventure_routing` calls `_resolve_cognition_profile_id` internally (phase.py:68),
  so leaving one behind while moving the other would break the relocated one immediately.
- `AdventureGoalScorer` is registered **unconditionally**, with no `ENABLE_ADVENTURE_ROUTING`
  check anywhere in `adventure_scorer.py` or in its registration site
  (`src/ai/goals/__init__.py:21`: `GoalRegistry.register(GoalKind.ADVENTURE_ROUTE,
  AdventureGoalScorer())`, no flag guard). This is the single most important fact for the "does
  deletion flip the switch" question below.

## Does deleting `AdventureDecisionPhase` actually make `ADVENTURE_ROUTE` live for the first time?

**No — not in the sense the ticket's own framing implies.** Traced precisely, byte-by-byte, through
the merge/ordering machinery:

1. `GoalRegistry.get_all_scores()` (`src/ai/goals/base.py:46-50`) has zero flag-gating — it calls
   `.score(entity, state)` on **every** registered scorer, including `AdventureGoalScorer`,
   unconditionally, for every entity `evaluate_strategic_intent()` reaches tier 5 for.
2. `evaluate_strategic_intent()` is called from the `strategic_intelligence` pipeline phase
   (`pipeline.py:347`), which has **no feature-flag gate** and runs every tick (subject only to
   per-entity `SystemCadence` throttling, unrelated to `ENABLE_ADVENTURE_ROUTING`).
3. `StrategicUpdate.merge()` (`src/core/updates.py:549-550`) resolves `current_project_id_set`
   as `other.current_project_id_set if other.current_project_id_set is not None else
   self.current_project_id_set` — the **later-merged** update wins. `EntityUpdate.merge()`
   (`updates.py:681`) recursively merges the `strategic` sub-update the same way.
4. Phase order in `pipeline.py` is `adventure_decision` (line 236) **then**
   `strategic_intelligence` (line 347) in the same tick, both reading the same immutable
   pre-tick `state` snapshot and both feeding the same accumulating `update` via
   `u.merge(...)`.

Putting 1-4 together: for any entity `evaluate_strategic_intent()` actually evaluates this tick
(i.e., not cadence-skipped), **the tier-5 `AdventureGoalScorer` decision already wins the final
committed `current_project_id`** today, because it is computed and merged strictly after
`AdventureDecisionPhase`'s own decision in the same tick. `AdventureDecisionPhase`'s output for
that entity is silently superseded, not "the" decision. This has been true since
`TCK-20260811-ADVENTURE-GOAL-SCORER` landed and registered the scorer unconditionally — **before
this ticket, before the shadow-migration-gate ticket, before any of the SimQ audit runs discussed
below.**

What deletion in **this** ticket actually changes:

- **Removes now-wasted duplicate computation**: today, `AdventureDecisionPhase.apply()` still runs
  a full route-generation + scoring + service `decide()` pass for every eligible hero every tick
  (when `ENABLE_ADVENTURE_ROUTING=ON`), whose result is then usually thrown away by the later
  tier-5 merge. Deleting it removes this waste, collapsing to "exactly one code path," which is
  literally Design Goal #1 (`docs/architecture/2026-08-11-adventure-as-cognition-strategy-
  subcomponent-design.md` §"Goals" item 1).
- **Removes the one case where the old phase's decision still lands uncontested**: entities that
  `evaluate_strategic_intent()`'s own `SystemCadence` throttling skips this tick get **no**
  `StrategicUpdate` from tier 5 that tick, so `AdventureDecisionPhase`'s own unconditional
  (non-cadenced) decision is currently the only one that commits for them. After deletion,
  cadence-skipped entities get **no** adventure-routing decision at all that tick — a real,
  disclosed frequency reduction, but exactly the design's own intended Goal #3 ("adventure becomes
  correctly subject to the same strategic hierarchy... every other decision already respects").
  Not a new risk this investigation is surfacing for the first time — it is the design's literal,
  stated purpose — but worth citing precisely rather than asserting "nothing changes."
- **Retires `ENABLE_ADVENTURE_ROUTING` to a dead flag**: its only remaining effect anywhere in
  `pipeline.py` is gating the `adventure_decision` `run_phase` call being deleted. Ticket Scope
  does not ask to remove the flag's definition (`src/domains/optimization/feature_flags.py`) or
  its default-value config (`rollout_profiles.py`) — only the pipeline registration. Flagged under
  Anti-Drift Hazards below; not expanding this ticket's scope to cover it.
- **Removes the decision-trace-writer call with no replacement** — a real functional loss, not
  covered by the ticket's stated Scope. See Anti-Drift Hazards.

## Mechanics / Engine Constraints

- `docs/mechanics/04_strategic_cognition.md` (Certified Level 1, Authoritative) §"Goal Hierarchy" /
  tier-5 section (~line 30) currently states: *"nothing calls `GoalRegistry.get_all_scores()` in a
  way that lets `ADVENTURE_ROUTE` actually win and materialize in a live run —
  `AdventureDecisionPhase`... remains the sole active/wired adventure-decision mechanism."* **This
  claim is stale and currently false**, per the trace above — `get_all_scores()` is called
  unconditionally every tick via the always-on `strategic_intelligence` phase, and
  `ADVENTURE_ROUTE` already competes and can already win, live, today, for any
  non-cadence-skipped adventure-eligible entity. This is a pre-existing parity gap (Mechanics
  Bible vs. code), not created by this ticket, but this ticket's own Related Docs already touch
  this exact subsystem and its deletion makes the doc's framing ("a separate, later, explicitly-
  gated ticket") fully obsolete either way — it must be corrected as part of this ticket's
  Document-Update phase, not left for a future ticket to notice independently.
- `docs/mechanics/04_strategic_cognition.md` line 311 ("`FactionDecisionPhase.execute()` runs
  every tick before `AdventureDecisionPhase` in the pipeline") also needs updating — the phase it
  references no longer exists after deletion.
- STRAT-236 (`docs/parity_ledger/strategic_cognition.yaml:2708-2737`, P1, verified): the
  project-lock early-release condition. Its `v2_evidence` (line 2725-2726) explicitly says
  *"AdventureDecisionPhase's own pre-filter at src/domains/adventure/phase.py:129 remains a
  separate, still-active gate"* — this becomes false the moment the class is deleted and must be
  corrected in this ticket (see Docs Requiring Update).
- STRAT-252 / STRAT-253 (`strategic_cognition.yaml:3255-3364`, P2/P1, verified): document
  `AdventureGoalScorer`'s existence and the shadow-parity suite respectively. Both `text` fields
  narrate the migration as still in-progress ("the not-yet-wired path," "the live path... and...
  the not-yet-wired path") — both need a v2_evidence/text touch once the cutover is real, though
  STRAT-253 in particular is entangled with the test file being deleted (see Test Plan).

## Docs Requiring Update

- `docs/simulation/domains/adventure_contract.md`: the entire "Engine Phase" section (lines 23-36)
  describes `AdventureDecisionPhase.apply(state, context)` as *the* engine phase, including its
  own eligibility/lock table. Must be rewritten to describe the tier-5
  `GoalRegistry`/`AdventureGoalScorer` mechanism as the live path (per ticket AC5).
- `docs/parity_ledger/strategic_cognition.yaml`: STRAT-236's `v2_evidence` (drop the
  "AdventureDecisionPhase's own pre-filter... remains a separate, still-active gate" sentence,
  since that gate no longer exists) and `test_path` (one of its three cited tests,
  `test_spawn_lock_condition.py::TestLockEarlyRelease::test_lock_released_when_hp_high_and_no_hostiles`,
  calls `AdventureDecisionPhase.apply()` directly and must be migrated or re-pointed — see Test
  Plan). STRAT-252/STRAT-253 `text` fields also need a status touch (scorer is now the sole live
  path, not "not-yet-wired"; shadow-parity suite is retired, not merely passing).
- `docs/mechanics/04_strategic_cognition.md`: correct the stale "not yet live" tier-5 claim
  (~line 30) and the `FactionDecisionPhase...before AdventureDecisionPhase` pipeline-ordering
  claim (line 311), both now factually wrong post-deletion (the first was already wrong
  pre-deletion, per above).
- `docs/observability/decision_trace_contract.md`: "Wired at:
  `src/domains/adventure/phase.py:AdventureDecisionPhase.apply()`" (line 95) becomes stale. Must
  either be updated to point at wherever the trace-writer call is relocated to, or — if Plan
  decides not to port it — updated to state the mechanism is currently unwired, plus a new entry
  in `docs/guidelines/intentional_divergences.md` recording that as an intentional, disclosed loss
  (see Anti-Drift Hazards; this is a real open decision, not something this investigation resolves
  unilaterally).

## Parity Ledger Overlap

- **STRAT-236** (P1, verified) — touched, see above. Requires a passing `test_path` post-change
  (P1 rule); the cited `test_spawn_lock_condition.py` test must keep passing under whatever form
  it takes after migration.
- **STRAT-252** (P2, verified) — touched (text/status only, no v2_evidence contradiction; its own
  evidence citations are all `src/` file:line references that remain valid post-deletion since
  they cite `AdventureGoalScorer`/`intelligence.py`, not `phase.py`).
- **STRAT-253** (P1, verified) — directly touched. Its entire `text`/`v2_evidence` narrates the
  now-being-deleted shadow-parity test suite (`test_adventure_shadow_migration_parity.py`) as
  proof of equivalence between two live paths. Once only one path exists, that suite's own premise
  (diff two decision paths) no longer applies — see Test Plan for the disposition decision
  (delete vs. keep as historical regression evidence). If deleted, STRAT-253's `test_path` becomes
  dangling and needs either a new `test_path` or an explicit `status` note that it documents
  now-historical migration evidence.
- **STRAT-185/STRAT-186/STRAT-187** (`strategic_cognition.yaml:1987-2037`, P0) — not directly
  touched by this ticket's own Scope, but the design doc (§9) flagged these as "directly exercised
  differently once adventure routes through the same gate" — worth a sanity check during Implement
  that their `test_path`s (already passing, per the ledger) still pass post-deletion, since they
  exercise `evaluate_project_switch()`'s locked-branch logic that `AdventureDecisionPhase.apply()`
  no longer calls at all afterward.

## Prior Work

- `TCK-20260811-ADVENTURE-GOAL-SCORER` (done): built `AdventureGoalScorer`, registered it
  unconditionally in `GoalRegistry`, added the tier-5 materialization branch in `intelligence.py`.
  This is the ticket whose landing is the real "cutover moment" per the trace above, not this one.
- `TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION` (done): relocated `_threat_resolved()` out of
  `phase.py` into `intelligence.py`, widened `evaluate_project_switch()`'s signature to accept
  `state`, updated STRAT-236 for that relocation. Confirmed by direct reading: `phase.py` no
  longer defines `_threat_resolved` (imports it, line 21); `evaluate_project_switch()`'s current
  signature (not re-cited in full here — outside this ticket's Related Code Areas) already accepts
  `state: Optional[AuthoritativeState] = None` per the design doc's post-landing citation note.
  Out of Scope confirmed correct: this ticket does not need to touch that relocation again.
- `TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE` (done): built the 24-test shadow-parity suite
  proving the two paths agree, and ran `/simq-audit mode=full` as AC5's pre-cutover gate — see
  next section, this is the ticket's own explicitly-deferred gate question.
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`: the
  authoritative design for this whole 4-ticket sequence. §5 "Deleted" confirms this ticket's scope
  exactly (class + pipeline.py registration only). §7 migration plan step 3 is this ticket's job;
  step 4 (full-corpus SimQ re-run) is discussed next.

## The SimQ Audit Finding — Does It Block This Ticket?

Ticket 3's own Completion Summary records a real, non-passing `/simq-audit mode=full` verdict
(`SIMQ-AUDIT-20260811T111151Z`, final status `ANCHORS_STILL_FAILING`) and explicitly frames its own
migration-step-4 obligation as gating **this** ticket's cutover, not its own DONE state: *"the
design's migration step 4 gates the LATER DELETE-ADVENTURE-DECISION-PHASE cutover, not this
ticket's own DONE state."* This investigation resolves that framing concretely, not by assumption:

**Resolution: informs this ticket; does not hard-block Implement**, with one required follow-on
action (below). Reasoning:

1. **The finding is about test/calibration data, not production logic.** The follow-up ticket
   (`TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP`) reads: its entire
   `Related Code Areas` list is `tests/simulation_quality/test_grade_regression.py` (the
   `_within_band()` check + `FAST_ANCHOR_KEYS` registration) and two JSON fixture files
   (`score_ceilings.json`, `grade_anchors.json`). It proposes **zero** changes to
   `src/ai/goals/adventure_scorer.py`, `src/systems/strategic_systems/intelligence.py`, or any
   other production adventure/cognition code. It does not dispute the shadow-migration suite's own
   24/24-passing proof that the two decision paths are functionally equivalent per-family.
2. **The COGNITION drift predates this ticket's own action, and predates ticket 3.** Per "Does
   deletion flip the switch" above, `AdventureGoalScorer` has already been live in every tier-5
   competition since `TCK-20260811-ADVENTURE-GOAL-SCORER` landed — independent of
   `ENABLE_ADVENTURE_ROUTING`'s state. The `simq_routing_test_*`/`hero_guild_routing_*` scenarios
   the audit flagged were run against a corpus where `AdventureGoalScorer` was *already* newly
   competing in every entity's tier-5 evaluation, on top of whatever `AdventureDecisionPhase` was
   independently also doing. **This ticket's own action does not introduce a new source of drift —
   if anything, it removes one real candidate root cause** (the redundant double-computation +
   duplicate decision-trace-writer-driven event volume difference across the two now-merged
   phases), by collapsing to the single-decision-per-tick model the design always intended.
3. **The open question the follow-up ticket poses (same watchdog-variance noise class already
   established by `TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP`, vs. something new) is
   explicitly unresolved by design** — its own Scope says so. Blocking this ticket's Implement on
   an unresolved calibration question that (a) doesn't implicate this ticket's own code and (b) is
   already independently tracked with its own AC and priority would create an indefinite,
   unaccountable block rather than a real gate.
4. **Required follow-on, in this ticket's own Test Plan (not skipped)**: since design doc §7 step
   4 explicitly calls for "full-corpus SimQ re-run to catch any behavior regression the shadow
   test's synthetic scenarios missed" as part of *this* cutover, and ticket 3 discharged only the
   "invoke and record honestly" half of that obligation (finding a pre-existing, non-regressing
   condition), this ticket's own Verify phase should re-run the same targeted SimQ surface
   (`tests/simulation_quality/test_grade_regression.py -k "simq_routing_test or
   hero_guild_routing"`) **after** the deletion lands, specifically to confirm collapsing to one
   decision path does not *newly* regress COGNITION (or any other pillar) beyond what ticket 3
   already found and disclosed. If it does regress further, that is new information this ticket
   must report truthfully (per CLAUDE.md's Gate Integrity rule) rather than route around — not an
   outcome to assume away here.

This is a judgment call informed by direct code tracing, not an assumption — Plan/Scope should
ratify it, but Investigate's own finding is: proceed, with the Verify-phase SimQ re-check as a
named, non-optional step.

## Risks and Open Questions

0. **`last_defer_reason`/`defer_with_reason` event gap (second new finding, distinct from #1
   below) — also blocks a clean AC3 "equivalent coverage" claim unless resolved in Plan.**
   `AdventureDecisionPhase.apply()` (phase.py:157-165) writes
   `property_updates={"last_defer_reason": ..., "last_defer_tick": ...}` on the entity's
   `EntityUpdate` whenever the service returns `RouteFamily.DEFER_WITH_REASON`.
   `src/observability/event_extractor.py:620-626` reads exactly this key
   (`prop.get("last_defer_reason")`) to emit a `defer_with_reason` event (`event_category:
   "strategy"`, tested by `tests/unit/observability/test_event_extractor_agency2.py` — the
   "agency2" filename signals this feeds the AGENCY SimQ pillar). **Confirmed by direct grep**:
   neither `AdventureGoalScorer.score()` (`adventure_scorer.py`) nor `intelligence.py`'s tier-5
   materialization branch ever writes `last_defer_reason` anywhere — on `DEFER_WITH_REASON`,
   `AdventureGoalScorer.score()` only returns a zero-utility `GoalScore`, never touching
   `property_updates`. Deleting `AdventureDecisionPhase` with no replacement silently stops
   `defer_with_reason` events from ever firing again — a second, real AGENCY-pillar-relevant
   observability regression, same shape and same severity as the decision-trace-writer gap below,
   and equally absent from the design doc and tickets 1-3's own scopes. Same open question for
   Plan: port the property-write into the winning path when `ADVENTURE_ROUTE`'s materialization
   result is `DEFER_WITH_REASON` (the natural site is `intelligence.py`'s existing
   `DEFER_WITH_REASON` early-return at `AdventureGoalScorer.score()`, or the tier-5 caller that
   receives that `GoalScore`), or explicitly accept and record the loss. These two gaps (this one
   and #1 below) should be resolved together, in the same Plan decision, since they are the same
   shape of problem (a side-effect wired only into the deleted class, never ported when the design
   moved the decision logic).

1. **Decision-trace-writer coverage gap (new finding, not in ticket's stated Scope) — likely
   blocks a clean AC3 "equivalent coverage" claim unless resolved in Plan.**
   `docs/observability/decision_trace_contract.md` is an active P1 observability contract:
   `decision_trace.jsonl` (LIGHT mode and above) is wired **only** at
   `AdventureDecisionPhase.apply()` (phase.py:118, 148-152, calling
   `DecisionTraceWriter.write_trace()`). `AdventureGoalScorer.score()` has **no** equivalent call
   anywhere in `src/ai/goals/adventure_scorer.py` — confirmed by direct reading, not inferred.
   Deleting `AdventureDecisionPhase` with no replacement silently stops `decision_trace.jsonl`
   from ever being written for adventure-routing decisions, which also silently empties
   `EntityInspector.goal_scores` (`src/observability/live/entity_inspector.py:136-140`, sourced
   from the same writer's cache) and degrades the E22C REST API that reads it. This was not
   surfaced by the design doc (no mention of the trace writer anywhere in
   `2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`) or by ticket 1-3's own
   scopes. **Open question for Plan, not resolved here**: port the `write_trace()` call into
   `AdventureGoalScorer.score()` (or the tier-5 materialization branch in `intelligence.py`) as
   part of this ticket's Implement, or accept the loss and record it explicitly in
   `docs/guidelines/intentional_divergences.md` with a rationale class and verification path per
   CLAUDE.md's Authoritative Mechanics Rule. Silently doing neither (deleting the class and letting
   `test_decision_trace.py`'s coverage simply disappear) would violate CLAUDE.md's Durable State
   Rule (observability/debug visibility for a durable-relevant decision) and the ticket's own AC3
   ("equivalent coverage").
2. **`ENABLE_ADVENTURE_ROUTING` becomes a dead flag.** Not in this ticket's Scope to remove its
   definition, but its only remaining live effect disappears with this deletion. Flagged so a
   future cleanup ticket (not this one) can pick it up deliberately rather than it silently rotting
   — `test_scenario_feature_flag_defaults.py` (comment-only reference to the phase, no code
   dependency, confirmed) documents scenario-level flag-default expectations that should be
   re-verified once the flag is provably inert.
3. **Test count correction**: ticket's own Assumptions section says "6 test files break
   immediately." Direct `grep` found **15 files** referencing `AdventureDecisionPhase` by name;
   of those, **9** have real code-level dependencies (import + call, or `inspect.getsource()`
   architecture guards) that will break on deletion; the other 6 are comment-only and need no
   code change (see Test Plan for the full breakdown). This is a real, disclosed correction to the
   ticket's own stated blast radius, not silently absorbed.
4. **`tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`'s entire
   premise disappears.** This is ticket 3's own 24-test suite, built specifically to diff two
   coexisting decision paths. Once `AdventureDecisionPhase` no longer exists, there is nothing
   left to diff against — the file cannot be "migrated" in the sense the other 8 files can (their
   individual tests can be re-pointed at the surviving path); it must be either deleted outright
   (losing its 24 tests' specific regression value, but they were explicitly parity-proving
   scaffolding, not permanent coverage) or repurposed. See Test Plan for the concrete
   recommendation.

## Anti-Drift Hazards

- **Do not "fix" the decision-trace-writer gap by quietly deleting `test_decision_trace.py`'s
  coverage** — that converts a real, disclosed observability regression into a silent one, exactly
  what CLAUDE.md's Gate Integrity rule and Durable State Rule both forbid. Either port the wiring
  or record the divergence explicitly; do not just remove the test.
- **Do not let the relocated `_supports_adventure_routing`/`_resolve_cognition_profile_id` change
  behavior "along the way."** Ticket Scope requires byte-identical internals. The existing
  `adventure_scorer.py` docstring block (lines 9-17, 31-47) already documents *why* the import is
  currently lazy/function-local (circular-import avoidance) — once the functions live in this
  same file, that specific lazy-import line disappears, but the *reason* the constants import a
  few lines below (lines 62-65) is lazy remains valid and unrelated; do not conflate the two and
  accidentally make the constants import eager too.
- **`_PROFILE_ELIGIBILITY_CACHE` in `adventure_scorer.py` (module-level, persists across ticks) vs.
  `phase.py`'s own per-`apply()`-call cache (fresh dict each call)** — these are two different
  caching lifetimes for the same predicate, already reconciled by design (see
  `adventure_scorer.py`'s own comment, lines 9-17: "a module-level dict persisting across ticks is
  a safe substitute, not a correctness risk," since cognition-profile definitions are static
  content). Do not "fix" this into a per-tick cache during this ticket — it is a deliberate,
  already-reviewed prior decision, not a defect this ticket should touch.
- **Do not widen this ticket into fixing the stale Mechanics Bible claim's *root cause*** (i.e.,
  do not treat "the doc has been wrong since ticket 1" as license to also audit/fix whatever else
  might be stale in that chapter) — only the specific passages this ticket's own deletion makes
  newly/differently wrong.
- **STRAT-185/186/187's `test_path`s exercise `evaluate_project_switch()`'s locked-branch logic
  generically** — verify they still pass post-deletion (sanity check only, not a ticket to
  re-derive their proofs); do not assume "adventure code changed, so these are automatically
  fine" without running them.

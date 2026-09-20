---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION
phase: done
date: 2026-09-20
tags: [simulation-quality, testing, cognition]
---

# TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION

## Title
Runtime-evidence program, batch 1: the differential scenario harness, proven on 3 of the
`cognition` system's 20 `code_trace`-only mechanisms before scaling to the rest

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
New program approved after PR #229: make "verified" mean the simulation did the thing, not that
the code says it would. `cognition` is the target system — 20 mechanisms, all 20 `code_trace`,
0% runtime-backed (`runtime_verified_share` = 0.0 for this group), and the system where dormant
mechanisms have been hardest to see across this whole arc.

This is the harness-proving batch, not the full 20: 3 mechanisms, chosen deliberately (not
defaulted) per explicit criteria — one `done` mechanism that genuinely matters, one where a
contradiction is genuinely plausible (not a safe pick), and one known negative for calibration.
Every scenario must have real differential structure — a check that can't fail proves nothing.

**Governing constraint, explicit and absolute**: if an instrument contradicts a claim, record the
contradiction and stop. Do not fix the code to make a claim true in this pass.

## Scope
1. Build the differential scenario harness pattern (extends the one prior real use,
   `TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION`, to a second and third real
   mechanism, proving the pattern generalizes rather than being a one-off).
2. Verify `belief_cycle` (`done`, load-bearing) via a real differential scenario.
3. Verify `perception` (`done`, chosen as the "plausible contradiction" slot after direct
   investigation found a real, unexpected dead-chain risk, not picked as a safe pass).
4. Verify `quest_generation_sourcing` (known `orphan`/`contradicted`) as the calibration case — if
   the harness reports it as running, the harness itself is broken.
5. Record whatever verdicts the instrument actually produces, including a state correction if
   `perception`'s runtime result confirms it is unreached in production.
6. File (not fix) any real defect found.

## Out of Scope
- The remaining 17 `cognition` mechanisms — explicitly deferred until the harness design is
  reported to and reviewed by the peer session.
- `goal_hierarchy` — considered for the "matters" slot, not selected this batch (see
  `investigation.md` for the reasoning; larger surface, no added harness-proving value for batch 1).
- Fixing `PerceptionUpdatePhase`'s wiring gap, if confirmed — a separate ticket.
- Any SimQ corpus work — this program is verification infrastructure only, changes no simulation
  behavior, and does not collide with the roadmap session's own measurements.

## Acceptance Criteria
1. 3 new scenario test files under `tests/mechanic_scenarios/`, each with a real, differential
   assertion through a real compiled world and a real `Kernel.tick_once()` dispatch (or, for the two
   calibration/negative cases, a positive-control direct call alongside the real-dispatch zero-call
   assertion).
2. All 3 mechanisms carry a `verified` block with `instrument: scenario` (upgrading from
   `code_trace`), recording the actual verdict — not adjusted toward a favorable answer.
3. Any state correction (e.g. `perception`'s `state`) is made only if the runtime evidence supports
   it, with the reasoning recorded in the entry's own note.
4. `registry.py::validate()` clean; consumer artifacts regenerated.
5. Harness design reported to the peer session before any further cognition mechanisms are
   attempted.

## Related Tickets
- `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN` — the prior batch this program is a
  direct, more rigorous successor to (peer explicitly cited its own re-languaged `code_trace`-only
  shape as the failure mode this harness exists to avoid repeating).
- `TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION` — the one prior real use of the
  differential scenario component this ticket extends.
- `TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY` — the `runtime_verified_share`
  metric this batch's own verdicts will move (and are not being optimized to move).
- `TCK-20260920-TEMPORAL-MODEL-CANONICAL-HASH-SERIALIZATION-GAP` — the determinism-hashing fix
  found while building `temporal_pressure`'s own scenario, filed as its own ticket per explicit
  peer instruction rather than riding along here as an incidental.
- `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`,
  `TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP` — filed, not fixed, during batch 1.
- `TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP` — filed during batch 2's pre-screen
  (`personality` doesn't fit the reachability-differential shape at all).

## Related Docs
- `docs/plans/mechanic_verification_scenarios_proposal.md`
- `docs/plans/mechanism_claims_as_tests_initiative.md` (§3.3 — the selection-effect finding this
  batch's candidate selection was deliberately built not to repeat)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION/`

## Related Code Areas
- `src/systems/strategic_systems/belief.py::BeliefCycleSystem`
- `src/domains/perception/filter.py::PerceptionFilterService`,
  `src/domains/perception/phase.py::PerceptionUpdatePhase`
- `src/systems/world_systems/quests.py::QuestGenerationSystem`
- `src/engine/pipeline.py`
- `tests/mechanic_scenarios/`
- `registries/mechanisms.yaml`

## Assumptions / Open Questions
See `investigation.md` for the full candidate-selection reasoning and per-mechanism differential
design.

## Implementation Notes
Built 3 real differential scenario files under `tests/mechanic_scenarios/`, extending the one
prior real use of this component (`TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION`)
to a second and third mechanism, reusing `mechanic_scenario_combat_judgement_withdrawal` (already
real, compiled, catalog-driven) rather than authoring a new world.

- **`belief_cycle`**: `observed`. A lead staged `certainty=APPROXIMATE`/`discovered_tick=0`
  demotes to `VAGUE` through a real `Kernel.tick_once()` once `state.tick=50` clears
  `stale_threshold`, and stays unchanged at `state.tick=10`. Real, unconditional pipeline entry
  point (`pipeline.py:408`) confirmed at runtime, not just by code trace.
- **`perception`**: `contradicted`. Investigated as a candidate for the "matters" slot (peer named
  it as one of three equally valid options) and found, unexpectedly, that
  `PerceptionUpdatePhase` — the only thing that would call `PerceptionFilterService.filter()` from
  the real pipeline — is never instantiated anywhere in `src/` outside its own file. 5 real ticks
  against a world with an adjacent, alive, hostile entity produced zero `.filter()` calls and an
  empty `perceived_entities` on both entities; a positive control (direct call) proved the code
  itself works. `state` corrected `done` → `orphan`; a real, unexpected finding, not a manufactured
  one — moved into the "plausible contradiction" slot after the evidence pointed there, per the
  explicit instruction not to default to a safe pick. Filed, not fixed:
  `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`.
- **`quest_generation_sourcing`** (calibration): `contradicted`, confirmed correct. A region forced
  to `trauma_score=0.9` (clears `generate_from_scar()`'s own real trigger threshold) produced zero
  real calls to any of `QuestGenerationSystem`'s 3 methods across 5 ticks, with a positive control
  (direct call) confirming the code itself produces a real `QuestTemplate` when invoked. The
  harness correctly reported the known negative rather than a false positive — the calibration this
  batch needed before trusting the other two verdicts.

Consumer-artifact regeneration surfaced two real drifts from `perception`'s state correction (both
expected, both fixed): `docs/brainstorm/rpg_feature_atlas.html`'s badge (`mechanism-atlas-
regenerate`) and `docs/brainstorm/simulation_capabilities.html`'s tier (`mechanism-capabilities-
regenerate`, `live` → `built`, plain 3-tier language). `docs/brainstorm/rpg_simulation_wiring_map.html`'s
Entity Operating Loop diagram had no automated fix path (report-only script) — hand-edited PER's
node label and class assignment (`live` → `bug`) to match, following the diagram's own existing
convention for other dead/gap mechanisms (MEM/INT/MOT/CNV/TRD/TUP/COM already carry inline
`:::bug`/`:::gated`).

`mechanism_state_caller_check.py`'s own report (informational, "report not verdict") flagged
`perception` as `orphan_with_callers` — expected and correctly explained by the entry's own new
note: the checker sees `phase.py` as a real caller of `PerceptionFilterService` without checking
whether `phase.py`'s own class is itself ever reached, the exact one-level-deep blind spot this
runtime scenario exists to catch. Pinned in `test_mechanism_state_caller_check.py`'s own findings
set alongside the same-shape `commitment_betrayal`/`chronicle` cases.

## Test Summary
6 new tests across 3 files in `tests/mechanic_scenarios/`, all passing. Full scoped suite
(`tests/unit/tools/ tests/mechanic_scenarios/`): 273 passed (2 real fixes needed along the way —
one pinned-findings-set test updated for the new `perception` finding, one wiring-map classdef
drift test that needed the hand-edit above; both are real, understood, documented changes, not
loosened assertions). `registry.py::validate()`: clean, 93 mechanisms. All consumer-artifact checks
(`mechanism-atlas-check`, `mechanism-capabilities-check`, `mechanism-registry-html-check`,
`mechanism-wiring-map-classdef` script): clean after regeneration.

## Files Changed
- `tests/mechanic_scenarios/test_belief_cycle_lead_staleness.py` (new)
- `tests/mechanic_scenarios/test_perception_pipeline_wiring.py` (new)
- `tests/mechanic_scenarios/test_quest_generation_sourcing_orphan_calibration.py` (new)
- `registries/mechanisms.yaml` — `belief_cycle`/`quest_generation_sourcing` upgraded to
  `instrument: scenario`; `perception` state corrected `done` → `orphan`, verdict `observed` →
  `contradicted`
- `docs/brainstorm/mechanism_verification_view.md`, `mechanism_registry_view.md`,
  `mechanism_system_rollup_view.md`, `mechanism_registry.html` — regenerated
- `docs/brainstorm/rpg_feature_atlas.html` — badge regenerated (`mechanism-atlas-regenerate`)
- `docs/brainstorm/simulation_capabilities.html` — tier regenerated (`mechanism-capabilities-
  regenerate`)
- `docs/brainstorm/rpg_simulation_wiring_map.html` — PER node hand-edited (label + classdef)
- `tests/unit/tools/test_mechanism_state_caller_check.py` — pinned-findings set updated
- `docs/REGISTRY.yaml` — regenerated
- `tickets/todos/TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED.md` — filed, not fixed

## Completion Summary
DONE. Harness proven on 3 deliberately-chosen mechanisms, not defaulted: `belief_cycle` (done,
matters, confirmed genuinely working at runtime), `perception` (a real, unexpected contradiction
found by direct investigation rather than picked as a safe pass), `quest_generation_sourcing`
(known negative, harness correctly discriminates rather than false-positiving). All 3 now carry
`instrument: scenario` verdicts. One real state correction made (`perception`), the fix itself
deliberately not made, per this program's explicit governing constraint. `runtime_verified_share`
moved as a side effect of honest verdicts, not optimized for. Harness design (2 real signals
checked per calibration/negative case: field-state absence + call-counter; direct-call positive
controls throughout; real compiled worlds and real `Kernel.tick_once()` dispatch, never a synthetic
fixture) reported to the peer session for review before scaling to the remaining 17 `cognition`
mechanisms, per explicit instruction.

## Addendum — 2026-09-20, peer review of the harness design before scaling
Harness approved with one structural caveat, applied here rather than carried forward as debt:

1. **Codified two rules in `docs/plans/mechanic_verification_scenarios_proposal.md` §5** (items 3
   and 4, not just practiced as habit): every negative/calibration verdict must pair a direct-call
   positive control with the real-dispatch zero-result (already true of both this batch's
   contradicted verdicts, now a stated requirement); every `contradicted`/`orphan` verdict grounded
   in "zero calls observed" must declare which backing it rests on -- (a) a static
   never-instantiated fact independent of world choice, or (b) a demonstrated precondition (the
   scenario's own world shown, not assumed, to produce the real trigger).
2. **Added explicit "Backing:" statements** to `perception` ((a) static -- `PerceptionUpdatePhase`
   has zero constructors anywhere in `src/`, holds regardless of world) and
   `quest_generation_sourcing` (both (a) and (b) -- zero real callers independent of world, plus
   the scenario's own world demonstrated to clear the real trigger threshold).
3. **Investigated `perception`'s own zero-dependents shape**, per direct request, without editing
   `depends_on` edges: not an under-declared edge -- zero real code anywhere in `src/` reads any
   `PerceptionModel` field at all outside the dead chain itself, so there is no real functional
   dependency to have under-declared. `goal_hierarchy`'s own note already documents strategic
   cognition sourcing situational awareness through a separate real path instead
   (`SpatialQueryService.nearby_entities()`). Conclusion: `perception` genuinely was never
   load-bearing -- nothing downstream was ever built to consume its output either, so the
   zero-dependents shape is accurate, not a registry gap. Adjacent finding, not the same one: a
   real, live, unregistered `src/world/perception/gate.py::PerceptionGate` exists
   (`src/engine/tactical.py`), but answers a narrower question (raw sense-detection gating for
   `tactical_decision`'s targeting) than `perception`'s own concept -- not a misbinding risk.
4. **Runtime share before/after**, pulled from the regenerated rollup rather than left uncomputed:
   `cognition` system 0/20 (0.0%) -> 3/20 (15.0%); registry-wide baseline 9/82 verified (11.0%) ->
   12/82 verified (14.6%).

No registry verdicts changed in this addendum -- documentation and investigation only, per the
peer's own framing ("apply the caveat," not "re-verify").

## Addendum 2 — 2026-09-20, implicit coverage and the completeness claim
Two more peer follow-ups, applied before scaling:

1. **`PerceptionGate` recorded, not implicit.** Added explicitly into `tactical_decision`'s own
   `verified.note`, stating its real scope (raw sense-detection gating, upstream of a decision) and
   why it stays unregistered rather than folded into that binding (a narrower concern than
   `tactical_decision`'s own; folding it in would misattribute).
2. **Coverage claim re-languaged, not silently corrected.** The completeness checker only scans
   `src/domains/`/`src/systems/`; a manual sizing pass of the other ~20 non-infra `src/` top-level
   directories found 85 unbound mechanism-shaped-class candidates, 14 with a real caller outside
   their own defining file -- the same bar `PerceptionGate` clears. Not isolated. Added dated
   addenda wherever the registry's "built from the codebase" framing appeared stronger than the
   method supports: `docs/plans/mechanism_registry_initiative.md`'s "the registry is complete"
   line, the completeness checker's own docstring, and a new §3.4 in
   `docs/plans/mechanism_claims_as_tests_initiative.md` (same shape as §3.3's own finding -- the
   data was never wrong, the claim about it was). The 14-candidate number is stated as a floor
   (suffix heuristic misses `Classifier`/`Filter`/`Builder`-named services), with "unbound != gap"
   reiterated. Sizing only, no fix attempted -- tracked separately,
   `TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP`.

No registry verdicts changed in this addendum either. Cleared to proceed to the remaining 17
`cognition` mechanisms under the same constraints.

## Addendum 3 — 2026-09-20, batch 2 wave 1: `temporal_pressure`
Scoping note first: of the remaining 17, 2 (`motivation_doctrine`, `information_trust_deception`)
are unbound (no `implemented_by`) -- already investigated and deliberately left that way in the
earlier unbound-claims program, out of scope for runtime verification until/unless a future binding
investigation gives them one. 15 are bound and testable.

**`temporal_pressure`**: `state` corrected `skeleton` -> `gated`, `instrument` upgraded to
`scenario`, verdict stays `observed`. The mechanism's own prior `code_trace` note confirmed a real
caller one level deep (`TemporalPressureService.calculate_urgencies()` at `memory/phase.py:90`) but
never checked whether that caller's own containing phase (`MemoryUpdatePhase`) was itself reachable
by default -- it isn't (`ENABLE_MEMORY_UPDATE` defaults OFF, same gate `causal_spatial_memory`
already correctly documents for the same phase). A real differential scenario
(`tests/mechanic_scenarios/test_temporal_pressure_gated_dormancy.py`) confirms both halves: flag ON
produces a real, correctly-scaled urgency value for a near-expiry deadline through a real
`Kernel.tick_once()`; flag OFF (the real shipped default) produces nothing. Unlike `perception`,
this is a state-classification correction, not a contradiction -- the mechanism genuinely works once
its precondition is met.

**Found and fixed along the way (trivial, not a mechanism-claim fix)**: staging a real
`DeadlineEntry` broke `Kernel.shutdown()`'s canonical-state hashing --
`TemporalModel.to_canonical_dict()` (`src/core/cognition.py`) never converted `deadlines`/
`cooldowns`/`stale_facts` map entries to plain dicts, a defect invisible until now because nothing
had ever populated those fields in a real run. Fixed directly, matching this file's own established
curated-field pattern (e.g. `PerceptionModel.to_canonical_dict()`).

276/276 tests passing (`tests/unit/tools/ tests/mechanic_scenarios/`), all consumer-artifact checks
clean, `registry.py::validate()` clean. Continuing with the remaining 14 bound mechanisms in further
waves.

## Addendum 4 — 2026-09-20, naming the pattern and a transitive pre-screen for the rest
Per peer review of wave 1: `perception` and `temporal_pressure` are two independent instances of the
same shape — a `code_trace` note citing a real, accurate call site that never checked whether *that
caller* is itself reached. Two instances in one batch is a pattern, not a coincidence. Catalogued as
`docs/plans/mechanism_claims_as_tests_initiative.md` §3.1's own 7th shape ("Six shapes" → "Seven
shapes" throughout that section).

Also: the `to_canonical_dict()` fix from Addendum 3 was moved to its own ticket,
`TCK-20260920-TEMPORAL-MODEL-CANONICAL-HASH-SERIALIZATION-GAP` (hotfix tier) — it touches
canonical-state hashing, a hard determinism rule in this repo, and shouldn't ride along inside a
verification PR as an incidental.

**Pre-screen adopted for the remaining 14, per direct instruction**: before building a scenario for
each, walk the citation transitively — does anything instantiate the phase, is it flag-gated, does
the gate default on or off. Cheap and static, it predicts dormant/gated outcomes and concentrates
scenario-building effort where the walk doesn't already answer the question. It does not replace the
runtime check itself (a reachable path still needs to be observed firing) — it only avoids building
an elaborate differential for a chain already provably broken two hops up.

## Addendum 5 — 2026-09-20, batch 2 wave 2: the shared `strategic_intelligence` phase
Per peer review of the routing table: the pre-screen routes work, it does not issue verdicts. Bucket
A (already `orphan`/`code_trace`, static fact) needed nothing further. Bucket C's 4 shared-phase
mechanisms (`goal_hierarchy`, `strategic_intelligence_core`, `strategic_learning_bias`,
`concern_intake`) are 3 independent questions, not 4 — one scenario per shared phase, reported as
such, not as 4 separate "observed" results.

**Built the shared-phase scenario**: `_resolve_active_objective()` (one of `goal_hierarchy`'s own 5
bound methods) resolves a staged `"detour"`-kind project's `reach_location` objective once the
entity reaches the objective's `target_position` — a real, clean, already-cited branch. Both
`goal_hierarchy` and `strategic_intelligence_core` upgraded to `instrument: scenario, verdict:
observed`. `strategic_learning_bias` and `concern_intake` are NOT claimed as verified by this
scenario — their own separate branches (turning-point biasing; salience-based concern evaluation
behind a stricter cadence and a `has_hostiles_or_dead`/hunger precondition) weren't exercised by it,
and stay `code_trace` pending their own staging, stated explicitly in both updated entries.

**A real trap found and fixed while building this, worth recording on its own**: the phase's
per-entity re-evaluation cadence is NOT what a plain read of `pipeline.py:53`'s
`DefaultCadence(strategic_intelligence=1)` override suggests — that override only applies when
`refine()` receives no cadence at all. A live `Kernel` run under `PROD_SMALL` actually supplies
`cadence.strategic_intelligence=20` (confirmed by direct instrumentation, not assumed). Staging the
precondition at `state.tick=0` and running forward let the entity's own real combat/movement logic
drift it 2+ tiles off the staged target before its first cadence-aligned evaluation (tick 19), which
would have produced a false negative attributable to drift, not to the resolution logic — and,
subtly, would have made the "absent" differential condition pass for the wrong reason too (nothing
changing because the entity was never evaluated, not because the distance check correctly rejected
it). Fixed by starting at the cadence-aligned tick directly. Recorded in both updated registry
entries so it isn't lost.

276/276 → 278/278 tests passing (2 new). All consumer-artifact checks clean. `personality` filed as
its own instrument-gap ticket (`TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP`), per
explicit instruction not to force a presence/absence differential onto a value-differential problem
— left unverified rather than given a verdict the current instrument can't support. `emotion` and
`adventure_routing` (the other 2 Bucket-C independent questions) remain for a further wave.

## Addendum 6 — 2026-09-20, codifying the vacuous-negative-arm risk and re-auditing prior verdicts
Per peer review: the cadence trap found while building `goal_hierarchy`'s own scenario (Addendum 5)
is a harness defect, not just a search defect — a negative arm that "passes" because the mechanism
was never reached looks identical to one that correctly declined, and every `scenario` verdict this
program has issued rests on its negative arm meaning something.

**Codified as `mechanic_verification_scenarios_proposal.md` §5 item 5** ("Five rules", not four):
a differential whose claim is about internal decision logic needs its negative arm to prove the
mechanism was reached-and-declined, not merely unevaluated — the same positive-control-pairing logic
as item 3, applied to the other side. Explicitly distinguished from item 4's static/demonstrated
backing, which covers a *different* claim shape (reachability itself is the claim, e.g.
`perception`/`temporal_pressure`) and is not vacuous by this rule. Also added as a third instance of
`mechanism_claims_as_tests_initiative.md`'s shape 7 ("one level short," this time in configuration —
a real, accurate read of `pipeline.py:53` that never checked whether a different real code path
overrides it).

**Re-audited every prior `scenario` verdict in this program, per direct instruction, not just the
newest one**:
- **`belief_cycle`**: NOT vacuous, confirmed by direct instrumentation (not re-reading code alone)
  — `BeliefCycleSystem.decay_stale_leads()` was empirically confirmed CALLED at `state.tick=10` for
  the staged entity, returning a genuine no-op update because `10 < stale_threshold(50)`.
  `resolve_lead_staleness()` has no internal per-entity cadence gate, and `"belief_staleness_decay"`
  isn't phase-level-cadence-gated either — reached and declined, not unevaluated. Verdict stands, no
  change.
- **`temporal_pressure`**: sound for a different reason, not the same reason as `belief_cycle`. Its
  own claim is specifically about the gate ("is the phase reachable at all when the flag is off"),
  the same reachability-claim shape §5 item 4 already covers for `perception` — "nothing computed
  because the phase never ran" IS the claim being tested, not an accident of staging. The separate
  positive control already rules out "the logic itself is broken." §5 item 5 doesn't apply to this
  one; recorded explicitly in the entry so the distinction isn't re-litigated later.
- **`perception`**, **`quest_generation_sourcing`**: both already reachability-claim shapes (backed
  by static facts per §5 item 4), same reasoning as `temporal_pressure` — not re-litigated in full
  here since the logic is identical, but checked, not assumed.

No verdict retracted — the audit found the two flag/gate-shaped scenarios sound by construction and
confirmed the one logic-shaped scenario (`belief_cycle`) empirically rather than trusting the read.
Both re-audited entries carry their own explicit "re-audited" note. 278/278 tests still passing, all
consumer-artifact checks clean. `emotion` and `adventure_routing` remain for the next wave.

## Addendum 7 — 2026-09-20, batch 2 wave 3: `emotion`, and `adventure_routing`'s own complexity
**`emotion`**: upgraded to `instrument: scenario, verdict: observed`. Real forced attack (orc ->
goblin, damage calibrated empirically at 19 for this world/seed, not guessed) through a real
`Kernel.tick_once()`. Goblin staged to survive at 2/107 HP (within the real 10% near-death
threshold) gets `fear=0.4, panic=0.5, confidence=0.2` from compiled defaults, matching
`EmotionUpdateService.update_on_event(..., "near_death")`'s own exact deltas; the same attack
against a full-HP goblin (survives well above threshold) leaves emotion untouched. Applied §5 item 5
from the start this time: instrumentation directly confirms the goblin has a real `CombatUpdate`
staged before `NearDeathHardeningPhase.apply()` runs in both conditions (genuinely enters the
per-entity loop, not skipped before being considered) — this phase has no per-entity cadence gate at
all, so no `goal_hierarchy`-shaped trap applies here.

**`adventure_routing`, investigated, not yet built**: `AdventureDecisionService.decide()` has
exactly one real call site (`src/ai/goals/adventure_scorer.py:165`, confirmed by direct grep, not
assumed from the prior note's own citations), reached via `AdventureGoalScorer.score()` ->
`GoalRegistry.get_all_scores()` -> `intelligence.py:1509` — which sits inside
`evaluate_strategic_intent()`'s own body, the exact same cadence-20-gated block `goal_hierarchy`'s
scenario already solved (§5's new configuration-trap instance). Unlike `goal_hierarchy`, the
observable differential here needs more than reaching the call site: `AdventureGoalScorer` is
registered as one candidate among many in a tier-5 goal competition
(`StrategicIntelligenceSystem.evaluate_strategic_intent()`'s own arbitration, not a direct write),
so confirming it *actually changes a project selection* requires either winning that competition
against real rivals or accepting a narrower claim (the scorer is called and produces a real,
non-default `GoalScore` for an eligible entity). Also requires an entity whose cognition profile has
`supports_adventure_routing=True` — `mechanic_scenario_combat_judgement_withdrawal`'s own
monster-kind entities almost certainly don't qualify, so this needs a different world (a real hero
entity) rather than reusing the world every other scenario in this program has used. Left open
rather than forced or half-built — the cadence-trap half of the investigation is already reusable
for whoever picks this up next.

280/280 tests passing (2 new), all consumer-artifact checks clean, `registry.py::validate()` clean.

## Addendum 8 — 2026-09-20, batch 2 wave 4: Bucket B, and a real registry corruption bug found
**`causal_spatial_memory`**: upgraded to `instrument: scenario, verdict: observed`. Reused
`temporal_pressure`'s own already-audited flag-toggle scaffolding for the identical
`MemoryUpdatePhase`/`ENABLE_MEMORY_UPDATE` gate. Targets the phase's own unconditional "regular
spatial visited region updating" branch (no trigger event needed): flag ON records the entity's
real compiled region as visited (`visit_count=1, familiarity=0.2`) through a real
`Kernel.tick_once()`; flag OFF (real default) leaves `visited_regions` empty. Same backing shape as
`temporal_pressure` -- a reachability claim, §5 item 5 does not apply.

**`self_model` + `knowledge_model`**: one shared observation, not two, same discipline as the
`strategic_intelligence` phase pairing -- both share `SelfModelUpdatePhase.apply()`'s own
`ENABLE_SELF_MODEL_COGNITION` gate, `knowledge_model` being one of its 4 orchestrated sub-services.
Reused `data/worlds/unit_selfmodel_pilot/`, a real, purpose-built world already staging a real
pending unknown-fact event for a real compiled entity -- confirmed directly that
`state.feature_flags` is empty by default even for this world (its own "ON via profile YAML"
description is a SimQ-corpus-runner-level concept, not something `WorldCompiler.compile()` itself
applies). Flag ON: the entity's real pending event is genuinely assimilated
(`knowledge.unknowns["material.wood.source"]` becomes real) and self-awareness re-checked
(`last_self_check_tick` updates) through a real `Kernel.tick_once()` at `state.tick=1` (not 0 --
`last_self_check_tick=0` would be indistinguishable from "never updated" at tick 0, an ambiguity
caught empirically before it became a vacuous assertion). Flag OFF: `self_model` stays fully at its
compiled default. Both upgraded to `scenario`/`observed`.

**A real registry-corruption bug found and fixed while finalizing this addendum, not a mechanism
finding**: `strategic_intelligence_core`'s own entry (wave 2) had a leftover, duplicate
`implemented_by:`/`verified:` block from an earlier imprecise edit -- the same YAML mapping ended up
with two `implemented_by:` keys and two `verified:` keys, and YAML silently resolves duplicate keys
to the LAST one, so the entry's own real `instrument:` field was still `code_trace` even though the
first (correct, edited) block and every prose note claimed `scenario`. Caught only because computing
this addendum's own final numbers by direct registry read disagreed with hand-arithmetic (9 vs. 10
expected runtime-verified mechanisms) -- a real instance of the same discipline this whole program
has been built on: check the actual data, don't trust the narrative. Swept the entire file
programmatically for the same duplicate-top-level-key shape afterward; no other instance found.
Fixed by removing the duplicate block; `registry.py::validate()` does not currently catch this shape
(duplicate keys within one mapping, not duplicate mechanism ids) -- worth a follow-up validator
check, not filed as its own ticket here since the fix itself is already complete and this addendum
is that record.

Also swapped `test_mechanism_registry.py`'s own hardcoded `self_model: code_trace` fixture example
(now `scenario`) for `motivation_doctrine` (confirmed still genuinely `code_trace`, permanently
unbound, out of this program's scope).

**Final numbers for `cognition`, after the bug fix**: 20/20 verified (100%), 10 runtime / 10 static,
runtime share 50.0% (was 0.0% at the start of this program). Registry-wide baseline: 19/82 verified
runtime-backed (23.2%, was 11.0% before batch 1). 286/286 tests passing, all consumer-artifact
checks clean, `registry.py::validate()` clean.

Bucket B complete. Remaining open in `cognition`: `adventure_routing` (arbitration-shape instrument
gap, filed), `personality` (value-shape instrument gap, filed), `motivation_doctrine` and
`information_trust_deception` (unbound, out of scope for runtime verification), `declared_cognition_schema`/`committed_intentions`/`strategic_redirection` (Bucket A, already-settled
`orphan`/`code_trace`, correctly left as-is), `strategic_learning_bias`/`concern_intake` (share
`goal_hierarchy`'s own phase reachability but their own specific branches remain unexercised, stated
explicitly on both entries).

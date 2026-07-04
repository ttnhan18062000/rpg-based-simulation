---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-BRANCH-B
phase: done
date: 2026-07-03
tags: [simulation_quality, information, cognition, self-model, bug]
---

# TCK-20260703-SIMQ-UPLIFT3-BRANCH-B

## Title
Wire Branch B: fix SelfModelUpdatePhase's hardcoded events=[] + InformationBeliefPhase's StateUpdate-clobbering merge bug, seed a compile-time InformationResponse to make it observable

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`docs/cognition/self_model_contract.md` and `docs/cognition/README.md` (both `status: active`,
`authority: P1`) document `SelfModelUpdatePhase`'s Step 1 (`KnowledgeModelService.assimilate`) as
running "only if InformationResponse events exist for this entity this tick" — implying the
`events` parameter passed into `SelfModelUpdatePhase.run()` should carry the tick's actual
`InformationResponse` events. Investigation during `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`
found `src/cognition/self_model_phase.py`'s call to `SelfModelUpdatePhase.run()` hardcodes
`events=[]` — a genuine contract violation, not a design choice. As a result,
`self_model.knowledge.unknowns` is never populated by any code path in the standard pipeline, which
means `InformationBeliefPhase`'s Branch B (route a new query) is permanently unreachable,
independent of `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`'s Branch A fix.

That ticket deliberately did NOT fix this — wiring `SelfModelUpdatePhase`'s `events=[]` touches
shared cognition-pipeline code used by every world, and was judged out of scope for a ticket that
was primarily about the information domain's compile-time plumbing (the investigation found this
mid-implementation and it required its own architecture review to scope correctly, mirroring the
Branch A investigation's own scope-discipline). This ticket picks that fix up properly.

**Investigation for this ticket (2026-07-03) found a second, causally-linked bug**:
`InformationBeliefPhase.apply()` (`src/domains/information/phase.py:27-33`) returns a brand-new
`StateUpdate` instead of merging with the tick's prior updates via the established `u.merge(...)`
pattern already used by 3 sibling phases in the same file (`faction_awareness`,
`diplomatic_transitions`, `military_conflict`). Empirically confirmed: with both
`ENABLE_SELF_MODEL_COGNITION` and `ENABLE_BELIEF_ASSIMILATION` ON, `information_belief`'s output
silently wipes `self_model`'s same-tick write entirely — this has never surfaced before because no
existing calibration profile has ever run both flags together. **Fixing only `events=[]` cannot
make Branch B durably reachable**, since Branch B lives inside the very phase that clobbers it.
Per 2026-07-03 user direction, this ticket's scope is expanded to fix both bugs together — the
merge fix reuses an existing, low-risk pattern already proven in 3 sibling phases in the same file.

Investigation also found no live path exists to source real `InformationResponse` events for
`SelfModelUpdatePhase.run()` without new plumbing (Branch A's output is structurally incompatible —
different type, different field casing/shape — and all 3 candidate live providers, `Guide`,
`Blacksmith`, `Guild`, are confirmed orphaned). The smallest viable fix is a third application of
the compile-time-seed pattern already used twice this batch (`information_source_profiles` →
`pending_information_responses` → a new field carrying Step 1's events), read directly by
`SelfModelUpdatePhase.apply()` from `state` — no live provider call, no generic event bus.

## Scope
1. Re-verify the finding against current `src/` (`self_model_phase.py`'s exact line may have
   shifted) — do not assume the 2026-07-03 investigation snapshot is still accurate without
   checking.
2. Schema + compiler + resolver plumbing (third application of the pattern documented in
   `docs/guidelines/design_patterns.md` Pattern 6) for a new compile-time-seedable field carrying
   `InformationResponse`-shaped events for `SelfModelUpdatePhase.apply()` to read directly from
   `state` — no live provider call, no new pipeline-wide event bus.
3. Fix the `events=[]` hardcoding in `self_model_phase.py` so `KnowledgeModelService.assimilate()`
   actually runs when the new field has entries for an entity.
4. Fix `InformationBeliefPhase.apply()`'s `StateUpdate` construction to merge with prior updates via
   the same `u.merge(...)` pattern already used by `faction_awareness`/`diplomatic_transitions`/
   `military_conflict` in the same file — a 1-line-shape change following an existing, proven
   pattern, not new engineering.
5. Confirm `self_model.knowledge.unknowns` becomes populated in at least one calibration scenario
   (with `ENABLE_SELF_MODEL_COGNITION` scoped ON for that test/scenario only, per the investigation's
   UQ-2 finding — not a global flag flip), and that `InformationBeliefPhase`'s Branch B becomes
   reachable with both flags ON simultaneously (the exact combination that previously clobbered).
6. Regression-test across ALL calibration worlds, not just `urban_political` — both phases run for
   every alive/active entity in every world, every tick.

## Out of Scope
- `InformationNeedDetector.detect_and_generate()` (still orphaned, separate from this fix) and the
  `paid_information_transaction` path — those depend on `state.information_providers`, a different
  field, and are not part of Branch B
- Re-litigating Branch A (`pending_information_responses`) — already shipped and working
  (`TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`)
- Turning on `ENABLE_SELF_MODEL_COGNITION` globally in any shipped calibration profile (confirmed
  orthogonal to the code fix — only needed as a scoped test/verification override)
- Any change to `SelfAssessmentService`, `NeedInterpretationService`, or `CapabilityEstimateService`
  (the other 3 steps of `SelfModelUpdatePhase`'s pipeline) — this ticket touches only Step 1's event
  plumbing
- Any change to `faction_awareness`/`diplomatic_transitions`/`military_conflict`'s own merge logic —
  they are the reference pattern, not something to modify
- Building the live `ASK_INFORMATION`/provider-response loop (`GuideInformationProvider` etc.) —
  still orphaned, still out of scope; this ticket only makes Branch B observable via a compile-time
  seed, same shape as Branch A

## Acceptance Criteria
- [x] `self_model_phase.py`'s `events=[]` hardcoding replaced with real events sourced from the new
      compile-time-seeded field
- [x] `InformationBeliefPhase.apply()` merges its `StateUpdate` with prior updates via `u.merge(...)`,
      matching its 3 sibling phases in the same file
- [x] `self_model.knowledge.unknowns` confirmed populated in at least one calibration scenario (via
      direct-pipeline test with `ENABLE_SELF_MODEL_COGNITION` scoped ON for that test only)
- [x] `InformationBeliefPhase`'s Branch B confirmed reachable with BOTH `ENABLE_SELF_MODEL_COGNITION`
      and `ENABLE_BELIEF_ASSIMILATION` ON simultaneously — the exact combination that previously
      clobbered — proving the merge fix actually resolves the clobbering (via the cross-tick-boundary
      test, once `SelfModelPatch`'s materialization fix landed — see Implementation Notes)
- [x] Full regression sweep across all calibration worlds (not just `urban_political`) — 0
      unintended regressions
- [x] `docs/cognition/self_model_contract.md`'s documented behavior now matches actual code (Step 10,
      2026-07-04)
- [x] `make evaluate --dry-run` exits 0

## Related Tickets
- TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER (done) — found this bug, deliberately deferred the
  fix to this ticket
- TCK-20260702-SIMQ-UPLIFT2-INFORMATION (done) — parent of the INFORMATION-pillar work this
  eventually feeds into

## Related Docs
- `docs/cognition/self_model_contract.md` — the contract this fixes a violation of
- `docs/cognition/README.md` — Step 1 pipeline description
- `docs/plans/idea_information_belief_trigger_wiring.md` — original idea doc naming this as Option 1

## Related Stored Artifacts
- `stored_artifacts/TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER/investigation.md` — full file:line
  evidence for the `events=[]` bug and its contract violation

## Related Code Areas
- `src/cognition/self_model_phase.py` — `SelfModelUpdatePhase.apply()`/`.run()`, the `events=[]`
  hardcoding
- `src/cognition/knowledge_model.py` — `KnowledgeModelService.assimilate()`
- `src/core/self_model.py` — `self_model.knowledge.unknowns`
- `src/domains/information/phase.py` — `InformationBeliefPhase.apply()` Branch B, the consumer of
  `unknowns`

## Assumptions / Open Questions
- UQ-1: Where should the per-tick `InformationResponse` events actually be sourced from for
  `SelfModelUpdatePhase.run()`'s `events` parameter — does this require new pipeline-level event
  plumbing (a per-tick event list passed between phases), or is there an existing mechanism this
  ticket's investigation should find? Resolve with evidence during investigation, not assumed.
  **Resolved**: third application of the compile-time-seed pattern (Pattern 6) — a new
  `pending_self_model_information_events` field on `AuthoritativeState`, seeded via
  schema→resolver→compiler plumbing, read directly by `SelfModelUpdatePhase.apply()`. No live
  provider, no generic event bus.
- UQ-2: Does `ENABLE_SELF_MODEL_COGNITION` (separate flag, currently OFF everywhere) need
  consideration here, or is it orthogonal? The prior investigation found it orthogonal — reconfirm.
  **Resolved**: orthogonal to the code fix itself; load-bearing only for verification (scoped
  per-test override, never a shipped profile default — confirmed still true in every
  `config/simulation_quality/profiles/*.yaml`).
- **NEW (Finding 5, discovered during this ticket's implementation, 2026-07-04)**:
  `EntityUpdate.self_model_bundle_set` is never materialized into durable `EntityState.self_model`
  by `ApplyPath`. `src/engine/patches.py::extract_patches()` has no `SelfModelPatch` class and never
  inspects `update.self_model_bundle_set`; `src/engine/apply.py:578`
  (`object.__setattr__(res, "self_model", changes.get("self_model", ...))`) reads a `"self_model"`
  key from `changes` that nothing ever populates. Empirically confirmed this session: after
  `ApplyPath.apply_generation()`, an entity's `self_model.knowledge.unknowns` remains empty even
  though `refined.entity_updates[id].self_model_bundle_set.knowledge.unknowns` was correctly
  populated pre-materialization. This is a **pre-existing, separate gap** — it affects Branch A's
  already-shipped `self_model_bundle_set` writes identically (the existing
  `test_belief_assimilation_persists_facts` only asserts `self_model.knowledge is not None`, never
  that its content changed, which is why this was never caught). It is **not** part of this
  ticket's approved Scope/Out-of-Scope (Steps 1-9 touch only event-sourcing plumbing and the
  `information_belief` merge call site in `pipeline.py`) and was **not** fixed here — fixing it
  would mean adding a `SelfModelPatch`/`changes["self_model"]` assignment to
  `src/engine/patches.py`/`src/engine/apply.py`, a distinct, unreviewed architectural change.
  **Consequence for AC**: `InformationBeliefPhase`'s Branch B routing logic itself is proven
  reachable and correctly coexists with the merge fix (both flags ON) **once its state-level
  precondition (`entity.self_model.knowledge.unknowns` populated on a durable, committed
  `AuthoritativeState`) is met** — verified via a hand-built state test
  (`test_information_belief_branch_b_routes_query_when_unknown_precondition_met`,
  `tests/integration/domains/test_fused_loop.py`). However, Branch B does **not** yet fire
  end-to-end via the real compile→pipeline→apply path in the shipped `urban_political` world,
  because (a) within a single `refine()` call, `information_belief` reads the frozen `state`, not
  the same-tick `update` that `self_model` just wrote to (phase order alone would require a
  subsequent tick), and (b) even across a tick boundary, self_model's write never reaches `state`
  at all due to Finding 5. **Recommendation**: a follow-up ticket should add
  `EntityUpdate.self_model_bundle_set` materialization to `src/engine/apply.py`/
  `src/engine/patches.py` before Branch B (and, retroactively, Branch A) can be considered durably
  reachable end-to-end. Flagging honestly per this ticket's own precedent (Finding 4) rather than
  claiming full end-to-end success.

## Implementation Notes
Steps 1-9 of `staging_artifacts/TCK-20260703-SIMQ-UPLIFT3-BRANCH-B/plan.md` implemented as specified
(Step 10 docs/parity deferred to a separate phase per this run's instructions):

1. **Schema** (`src/worldbuilding/schema.py`): added `SelfModelInformationFactSpec` and
   `PendingSelfModelInformationEventSpec` (lowercase `answer_kind` vocabulary, distinct from
   `PendingInformationResponseSpec`'s uppercase vocabulary), and
   `WorldSpec.pending_self_model_information_events`.
2. **Assembly schema** (`src/worldassembly/schema.py`): mirrored field onto both
   `WorldCompositionSpec` and `NormalizedWorldComposition` (per Pattern 6's `extra="forbid"` trap).
3. **Resolver** (`src/worldassembly/resolver.py`): direct passthrough into the `WorldSpec(...)`
   constructor call in `WorldAssemblyResolver.assemble()`.
4. **Compiler** (`src/worldbuilding/compiler.py`): resolves `target_population_id` → compiled
   `actor_id`, constructs real `src.world.providers.information.InformationResponse`/`KnowledgeFact`
   instances (not raw dicts), seeds `AuthoritativeState.pending_self_model_information_events` as
   `{"actor_id": ..., "event": InformationResponse(...)}` entries. Unmatched population IDs are
   skipped with a warning (mirrors `pending_information_responses`).
5. **New `AuthoritativeState` field** (`src/core/state.py`): added
   `pending_self_model_information_events: List[Dict[str, Any]]`, single-fire (not carried forward
   by `ApplyPath.apply_generation()` — confirmed absent from its `AuthoritativeState(...)`
   reconstruction, matching `pending_information_responses`/`information_source_profiles`
   precedent).
6. **`self_model_phase.py` fix**: `SelfModelUpdatePhase.apply()` now groups
   `state.pending_self_model_information_events` by `actor_id` once before the loop, passing each
   entity's own events instead of the hardcoded `events=[]`.
7. **`pipeline.py` fix (Finding 4)**: `information_belief`'s call site
   (`src/engine/pipeline.py:152`) now wraps `InformationBeliefPhase.apply(...)` in `u.merge(...)`,
   matching the `faction_awareness`/`diplomatic_transitions`/`military_conflict` sibling pattern
   exactly. No change to `InformationBeliefPhase.apply()`'s signature or
   `src/domains/information/phase.py`.
8. **World content**: seeded `pop_1` (not `pop_0`, which would shadow Branch B via Branch A's
   existing entry) in `data/worlds/urban_political/world.yaml` with an `unknown`-kind
   `pending_self_model_information_events` entry (`material.moon_resin.source`). Regenerated
   `data/worlds/urban_political/resolved/world.resolved.yaml` via
   `python -m src.worldbuilding.cli resolve urban_political` — diff confirmed only the new block
   plus incidental provenance/timestamp/warning-ordering noise changed.
9. **Persistence**: confirmed no change needed to `src/engine/apply.py`'s carry-forward logic
   (single-fire is correct, per Step 7 of the plan).
10. **Finding 5** (see Assumptions/Open Questions above): discovered and documented, not fixed —
    out of this ticket's approved scope.

### Supplementary fix (2026-07-04): `SelfModelPatch` — Finding 5 materialization

Implemented per `staging_artifacts/TCK-20260703-SIMQ-UPLIFT3-BRANCH-B/plan_self_model_patch_fix.md`
(approved after one fix-and-reverify architecture review cycle). This closes the Finding 5 gap
documented above: `EntityUpdate.self_model_bundle_set` now durably materializes into
`EntityState.self_model` via the authoritative apply path, completing Pattern 2 (Decision/Mutation
Separation via Typed Update Records, `docs/guidelines/design_patterns.md`) for this field.

1. **`SelfModelPatch(ComponentPatch)`** added to `src/engine/patches.py` (after `WoundPatch`, before
   `extract_patches()`), a direct structural mirror of `KindPatch`: whole-object replace-if-present.
   `is_noop()` checks `self_model_bundle_set is None`; `merge()` is last-write-wins; `apply()` sets
   `changes["self_model"] = self.self_model_bundle_set` only if non-`None`.
2. **Wired into `extract_patches()`**: appended after the `WoundPatch` block, matching
   `self_model_bundle_set`'s declaration position as the last "_set" field on `EntityUpdate`. No
   ordering dependency (confirmed by architecture review — `self_model` is never read by the PH8
   Derived Stats Re-calc block, and no other patch's `apply()` reads `changes.get("self_model", ...)`).
   No change needed to `src/engine/apply.py`'s `_fast_replace_entity()` — it already read
   `changes.get("self_model", ...)`, just was never fed.
3. **Docstring correction** at `src/core/self_model.py:216-219` (`SelfModelBundle` class docstring):
   the prior claim that `self_model` was "intentionally excluded from authoritative canonical hash"
   was false and pre-existing (not introduced by this fix). `EntityState.to_canonical_dict()`
   (`src/core/state.py:750`) unconditionally includes `"self_model"`, and
   `CanonicalStateHasher.to_canonical_data()` (`src/engine/checkpoint.py:81`) uses this same method
   for every entity — there is no separate hash-only vs. debug-only path. Corrected the docstring to
   state that `self_model` DOES participate in the canonical hash. No hash-formula change — that
   would retroactively alter every existing calibration baseline's hash value, judged far too large a
   blast radius for this ticket.
4. **New parity ledger entry `SUB-374`** added to `docs/parity_ledger/substrate.yaml`, recording the
   corrected canonical-hash-participation invariant and the docstring fix, per the Authoritative
   Mechanics Rule.
5. **Blast-radius sweep** (15 consumers of `entity.self_model` identified and individually assessed):
   2 orphaned (zero live callers), 3 false positives/already-decoupled telemetry, 1 pure passthrough,
   1 docstring-only correction (canonical hash), and 8 intended positive fix effects (self_model
   assimilation becomes genuinely cumulative across ticks once `old_bundle` carries real history
   instead of always-`SelfModelBundle.empty()`). The only consumers with any live conditional
   behavior change (`AdventureRouteGenerator`/`scoring.py`) require both
   `ENABLE_SELF_MODEL_COGNITION` and `ENABLE_ADVENTURE_ROUTING` ON simultaneously — no shipped
   `config/`/`data/worlds/` runtime profile combines these flags today, though
   `RolloutProfileManager`'s committed (currently unwired) `CLASS_B`/`CLASS_C` matrices do; the
   regression sweep explicitly re-ran both `RolloutProfileManager`-exercising test files unchanged
   to confirm this fix doesn't silently break that committed matrix.

**Tests added**:
- `tests/unit/optimization/test_component_patches.py`: 6 new `SelfModelPatch` unit tests
  (noop detection, merge last-write-wins + preserve-on-noop-other, apply sets `changes["self_model"]`
  by identity, apply noop leaves `changes` untouched, `extract_patches()` inclusion/omission).
- `tests/integration/optimization/test_component_patch_apply_parity.py`:
  `test_self_model_patch_apply_parity_durable_materialization` — direct end-to-end regression guard
  for Finding 5 through `ApplyPath.apply_generation()`, asserting full bundle equality (not just
  not-`None`).
- `tests/unit/core/test_entity_integrity.py`: `test_self_model_participates_in_canonical_hash`
  (asserts two otherwise-identical `EntityState`s differing only in `self_model` produce different
  canonical hashes — the corrected, true invariant) and
  `test_self_model_fix_preserves_existing_baseline_hashes_when_flag_off` (before/after hash-stability
  regression guard: with `self_model_bundle_set` never populated, `SelfModelPatch` is gated out via
  `is_noop()` and the resulting canonical hash is bit-identical to a state where `self_model` was
  never wired into `changes` at all).
- `tests/integration/domains/test_fused_loop.py`: strengthened
  `test_belief_assimilation_persists_facts` (now asserts the actual `coal_ore` fact content, not just
  `is not None`) and `test_self_model_apply_sources_events_from_pending_field_isolated_from_finding4`
  (now asserts the persisted `material.moon_resin.source` unknown's `reason`, and removed the stale
  Finding-5-not-fixed NOTE); added
  `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization` — proves the
  full seed → assimilate → materialize → route sequence works across a real tick boundary (tick N
  materializes the unknown via `SelfModelPatch`; tick N+1's `InformationBeliefPhase` Branch B reads it
  off durable `state` and routes a query), the exact cross-tick reachability this ticket's own
  Finding 5 recommended as a follow-up.
- Adventure-domain regression probes (`tests/unit/domains/adventure/test_phase3_route_generator.py`,
  `test_phase3_route_scoring.py`): confirmed already-existing tests construct a non-empty
  `self_model` directly via `V2EntityBuilder.replace_self_model()` and assert on the previously-dead
  `RECOVER`/`ASK_INFORMATION` forced-route paths — no new test needed; re-ran unchanged as part of
  the regression sweep.

**Regression sweep** (full widened list per plan section 4.5, 406 tests): `tests/unit/cognition/`,
`tests/unit/domains/information/`, `tests/unit/domains/adventure/`, `tests/unit/optimization/`,
`tests/unit/config/test_phase10_rollout_profiles.py`,
`tests/perf/test_phase10_integrated_enhanced_stack_budget.py`, `tests/integration/optimization/`,
`tests/integration/domains/test_fused_loop.py`, `tests/integration/domains/information/`,
`tests/integration/scenarios/test_phase5_information_belief_scenarios.py`,
`tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`,
`tests/integration/scenarios/test_phase2_self_model_scenarios.py`,
`tests/unit/entity/test_phase2_self_model_components.py`, `tests/unit/core/test_entity_integrity.py`,
`tests/perf/test_phase2_self_model_budget.py`, `tests/perf/test_phase5_information_belief_budget.py`,
`tests/simulation_quality/test_cognition_scorer.py`, `tests/simulation_quality/test_information_scorer.py`,
`tests/unit/campaigns/test_phase9_semantic_campaign_scorecard.py` — all 406 pass. Plus re-ran Steps
1-9's own regression sweep (547 passed, 1 pre-existing unrelated failure confirmed identical —
`test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x`,
`KeyError: Resource not found in ResourceRegistry: STONE`, same as documented above).

**Hash stability verification**: compiled `urban_political`'s real resolved world spec (seed 42,
shipped default flags — `ENABLE_SELF_MODEL_COGNITION` confirmed not `ON`), ran 50 ticks through
`AuthoritativeApplyPipeline.refine()` + `ApplyPath.apply_generation()`, and computed
`CanonicalStateHasher.get_hash()` twice: once with `SelfModelPatch` present (post-fix) and once with
`src/engine/patches.py`'s `SelfModelPatch` addition temporarily reverted via `git stash` (pre-fix).
Both runs produced the identical hash
`15081e225da292dd91ae8179922729ec0103f1b9a09cc64be8e14f49c8549591` — confirms zero shipped baseline
hash-value drift from this fix. A `calibrate_simq.py` spot-check (`urban_political`, seed 42, 200
ticks) confirmed `INFORMATION` grade unchanged at `B` and `COGNITION` grade `B` (`ENABLE_SELF_MODEL_COGNITION`
correctly absent/OFF in the shipped profile's feature flags).

**Files changed (this supplementary fix only)**: `src/engine/patches.py`, `src/core/self_model.py`
(docstring only), `docs/parity_ledger/substrate.yaml` (new `SUB-374` entry),
`tests/unit/optimization/test_component_patches.py`,
`tests/integration/optimization/test_component_patch_apply_parity.py`,
`tests/unit/core/test_entity_integrity.py`, `tests/integration/domains/test_fused_loop.py`.

**Deferred** (unchanged from Steps 1-9): `docs/cognition/self_model_contract.md:87` and
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-256` `support_boundary` doc follow-ups (plan section
6) remain part of the ticket's own deferred Step 10 docs pass, not this supplementary fix's explicit
scope — consistent with this ticket's existing precedent of deferring the whole-ticket docs pass to a
separate phase.

### Step 10 (docs/parity updates) — completed 2026-07-04

Closes the deferral noted immediately above. All edits are documentation-only; no code changed in
this pass.

1. **`docs/cognition/self_model_contract.md`**: "Phase lifecycle" section now states that
   `SelfModelUpdatePhase.apply()` sources `events` from
   `AuthoritativeState.pending_self_model_information_events` (compile-time-seeded, filtered by
   `actor_id`), citing `INFRA-259`. The prior "written to `entity.self_model` through the
   authoritative apply path" sentence — false before the `SelfModelPatch` fix, per Finding 5 — now
   also cites `SelfModelPatch`/`SUB-374` as the mechanism that makes it true. Added a dated
   (2026-07-04) confirmation note that the Dirty check section's "No InformationResponse events
   arrived for this entity this tick" language now describes a real runtime condition, not a
   permanently-true one (since `events=[]` was previously unconditional).
2. **`docs/cognition/README.md`**: Step 1 of the pipeline diagram now cites the compile-time-seed
   event source, cross-referencing `self_model_contract.md`'s new sentence rather than duplicating
   it.
3. **`docs/parity_ledger/infrastructure.yaml`**: added `INFRA-259` (the compile-time
   schema/compiler/resolver/`events=[]` plumbing) and `INFRA-260` (the `information_belief` merge
   fix), both `status: verified`, `priority: P1`. Revised `INFRA-256`'s and `INFRA-257`'s
   `support_boundary` text — both previously stated Branch B was unreachable due to `events=[]`;
   both now state the code-level mechanism is correct and proven reachable (via the cross-tick-
   boundary test, both flags scoped ON), but explicitly note `ENABLE_SELF_MODEL_COGNITION` stays OFF
   in every shipped calibration profile, so Branch B's contribution to real `calibration_hits` is 0.
   No prior claim of unconditional reachability was introduced.
4. **`docs/simulation_quality/event_type_coverage.md`**: added a Branch-B-specific note to the
   `belief_assimilated` row (the measured `calibration_hits == 1` remains entirely Branch A) and a
   note to the `self_model_updated` row citing the `SelfModelPatch`/`SUB-374` materialization fix
   (this event is read off the transient `EntityUpdate`, not durable state, so its own 0-hit count is
   unaffected either way). Updated the file's "Last updated" header.
5. **`docs/guidelines/intentional_divergences.md`**: added `§2.24` (`information_belief`
   pipeline-wiring merge fix, rationale class **Bug Fix**, same class as `§2.22`'s kernel
   tick-alignment fix) and `§2.25` (`self_model_bundle_set` durable materialization /
   `SelfModelPatch`, rationale class **Bug Fix**) to the Detailed Records section, plus 2
   corresponding rows in the Divergence Summary Table. Verified no pre-existing entry covered either
   fix (`SUB-374` in `substrate.yaml` covers only the separate canonical-hash-docstring correction,
   not these two fixes).
6. Ran `make knowledge-index-update` (incremental): 4 changed `docs/` files re-embedded
   (`self_model_contract.md`, `README.md`, `event_type_coverage.md`, `intentional_divergences.md`),
   1839 unchanged chunks reused, 0 deleted — completed successfully.

**Honesty note**: Branch B does not fire in any shipped calibration scenario as a result of this
ticket. `ENABLE_SELF_MODEL_COGNITION` remains OFF in every `config/simulation_quality/profiles/*.yaml`
and `data/worlds/*.yaml` entry. What this ticket delivers is a mechanism that is now provably correct
and reachable end-to-end (schema → compiler → `events=[]` fix → merge fix → `SelfModelPatch`
materialization → cross-tick Branch B routing) when both flags are scoped ON for
test/verification purposes — not a change to any shipped world's live behavior.

## Test Summary
All new tests pass; full regression sweep shows 0 unintended regressions.

- `tests/unit/worldbuilding/test_worldspec_schema.py`: 3 new tests (default construction,
  uppercase-`answer_kind` rejection, `WorldSpec` default-empty-list).
- `tests/unit/worldbuilding/test_world_compiler.py`: 4 new tests (seed-from-spec, unmatched-warning,
  empty-default, real `urban_political` resolved-world seeding).
- `tests/unit/worldassembly/test_assembly.py`: 2 new resolver tests
  (passthrough/no-declaration-empty) + 1 new assertion block appended to
  `test_composition_normalization_shorthand_and_mixed`.
- `tests/integration/domains/test_fused_loop.py`: 4 new tests —
  `test_self_model_apply_sources_events_from_pending_field_isolated_from_finding4` (Step 4 fix,
  isolated from Finding 4),
  `test_information_belief_merge_preserves_self_model_writes_both_flags_on` (Finding-4-fix-proving,
  both flags ON, empirically reproduced the pre-fix `{}` wipe by temporarily reverting
  `pipeline.py`'s fix during this session, then restored it),
  `test_information_belief_branch_b_routes_query_when_unknown_precondition_met` (proves Branch B's
  routing logic itself is reachable + coexists with a same-tick self_model write under the merge
  fix), `test_branch_b_on_compiled_urban_political_state_self_model_and_branch_a_coexist` (real
  compiled `urban_political` state, both flags ON — self_model's fix + Branch A coexist correctly;
  honestly documents that Branch B's query-routing does not yet fire in this same tick, per
  Finding 5).

Regression sweep run: `tests/unit/cognition/`, `tests/unit/domains/information/`,
`tests/unit/worldbuilding/`, `tests/unit/worldassembly/`, `tests/integration/domains/test_fused_loop.py`,
`tests/integration/scenarios/test_phase5_information_belief_scenarios.py`, `tests/unit/engine/`,
`tests/integration/pipeline/`, `tests/integration/domains/information/`,
`tests/unit/strategic/test_information.py`, `tests/perf/test_phase5_information_belief_budget.py`,
`tests/simulation_quality/test_information_scorer.py`, plus the calibration-world-referencing suites
(`tests/integration/scenarios/test_content_foundation.py`, `test_entity_differentiation.py`,
`tests/integration/test_scenario_feature_flag_defaults.py`,
`tests/integration/worldassembly/test_e2e_smoke.py`,
`tests/integration/worldassembly/test_real_content_world_compositions.py`,
`tests/simulation_quality/test_evaluate_harness.py`, `test_grade_regression.py`, `test_weights.py`,
`tests/unit/observability/test_run_artifact_repository.py`,
`tests/unit/worldbuilding/test_quest_definition.py`). One pre-existing, unrelated failure
(`test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x`, `KeyError: Resource not
found in ResourceRegistry: STONE`) confirmed present identically on the pre-change tree (stashed
this ticket's diff and re-ran) — not caused by this ticket. All other tests pass. One `calibrate_simq.py`
spot-check (`urban_political`, seed 42, 200 ticks) confirmed `INFORMATION` pillar grade unchanged at
`B` (matches shipped baseline; `ENABLE_SELF_MODEL_COGNITION` correctly stays OFF in the shipped
profile). `make evaluate --dry-run` exits 0.

## Files Changed
- `src/worldbuilding/schema.py`
- `src/worldassembly/schema.py`
- `src/worldassembly/resolver.py`
- `src/worldbuilding/compiler.py`
- `src/core/state.py`
- `src/cognition/self_model_phase.py`
- `src/engine/pipeline.py`
- `data/worlds/urban_political/world.yaml`
- `data/worlds/urban_political/resolved/world.resolved.yaml` (+ `assembly_report.json`,
  `provenance_manifest.json`, `validation_report.json`, regenerated)
- `tests/unit/worldbuilding/test_worldspec_schema.py`
- `tests/unit/worldbuilding/test_world_compiler.py`
- `tests/unit/worldassembly/test_assembly.py`
- `tests/integration/domains/test_fused_loop.py`
- `src/engine/patches.py` (supplementary fix — `SelfModelPatch`)
- `src/core/self_model.py` (supplementary fix — docstring only)
- `docs/parity_ledger/substrate.yaml` (supplementary fix — new `SUB-374` entry)
- `tests/unit/optimization/test_component_patches.py` (supplementary fix)
- `tests/integration/optimization/test_component_patch_apply_parity.py` (supplementary fix)
- `tests/unit/core/test_entity_integrity.py` (supplementary fix)
- `docs/cognition/self_model_contract.md` (Step 10, docs-only)
- `docs/cognition/README.md` (Step 10, docs-only)
- `docs/parity_ledger/infrastructure.yaml` (Step 10 — new `INFRA-259`/`INFRA-260`; revised
  `INFRA-256`/`INFRA-257` `support_boundary`; docs-only)
- `docs/simulation_quality/event_type_coverage.md` (Step 10, docs-only)
- `docs/guidelines/intentional_divergences.md` (Step 10 — new `§2.24`/`§2.25`; docs-only)

## Completion Summary
Delivered three causally-linked fixes that together make `InformationBeliefPhase`'s Branch B
mechanism provably correct and reachable end-to-end, each independently investigated, planned, and
architecture-reviewed (2 of the 3 required a fix-and-reverify cycle after the initial review
surfaced follow-on gaps):

1. **`self_model_phase.py`'s `events=[]` hardcoding** — replaced with real events sourced from a new
   compile-time-seeded field (`AuthoritativeState.pending_self_model_information_events`, third
   application of the Pattern 6 schema/compiler/resolver plumbing), so
   `KnowledgeModelService.assimilate()` actually runs and `self_model.knowledge.unknowns` gets
   populated instead of the pipeline silently no-oping every tick.
2. **`pipeline.py:152`'s `InformationBeliefPhase` merge fix (Finding 4)** — the call site now wraps
   the phase's output in `u.merge(...)`, matching the `faction_awareness`/`diplomatic_transitions`/
   `military_conflict` sibling pattern in the same file; previously it clobbered `self_model`'s
   same-tick write with a brand-new `StateUpdate` whenever both `ENABLE_SELF_MODEL_COGNITION` and
   `ENABLE_BELIEF_ASSIMILATION` were on simultaneously.
3. **`SelfModelPatch` durable materialization fix (Finding 5, discovered mid-implementation)** —
   `EntityUpdate.self_model_bundle_set` previously never reached `EntityState.self_model` through
   `ApplyPath`; added `SelfModelPatch(ComponentPatch)` to `src/engine/patches.py` and wired it into
   `extract_patches()`, closing the gap for both this ticket's Branch B and the already-shipped
   Branch A. Required its own architecture review (blast-radius sweep across 15 live consumers of
   `entity.self_model`) before landing.

950+ tests passing across a widened regression sweep (406 + 547 across the two implementation
phases, plus targeted new tests for each fix — cognition, information, worldbuilding, worldassembly,
optimization, adventure, and calibration-scenario suites), with exactly one confirmed pre-existing
unrelated failure (`test_bravery_quartile_combat_rate_2x`, reproduced identically on the pre-change
tree). Hash-stability empirically proven byte-identical for the shipped `urban_political` profile:
50-tick pre/post-`SelfModelPatch` comparison and a `calibrate_simq.py` 200-tick spot-check both
produced identical canonical hashes/grades, confirming zero baseline drift since
`ENABLE_SELF_MODEL_COGNITION` stays OFF in every shipped calibration profile.

Docs and parity ledger updated honestly (Step 10): `docs/cognition/self_model_contract.md`,
`docs/cognition/README.md`, `docs/parity_ledger/infrastructure.yaml` (new `INFRA-259`/`INFRA-260`),
`docs/simulation_quality/event_type_coverage.md`, and
`docs/guidelines/intentional_divergences.md` (new `§2.24`/`§2.25`) all now state plainly that Branch
B's mechanism is correct and end-to-end reachable via test-scoped verification (cross-tick-boundary
test, both flags scoped ON), but is not active in any shipped calibration profile — Branch B's
contribution to real `calibration_hits` remains 0 until a future ticket turns
`ENABLE_SELF_MODEL_COGNITION` on for a live world.

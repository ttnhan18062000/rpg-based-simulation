---
status: archive
authority: P2
audience: historical
layer: misc
original_date: unknown
---

Below is an updated corrective implementation plan in the same format, narrowed to what is still genuinely open after the latest source and test updates.

This document is a corrective implementation plan derived from verification of the current updated source and test suite.

It is **not** a restatement of the previous corrective drafts.
It contains only:

- remaining missing work,
- falsely-closed or weakly-proven work,
- stale tasks that should now be removed,
- and the specific proof gaps that still separate the implementation from an honest completion claim.

The most important finding is this:

The implementation is now materially real across most of the bounded-cognition and strategic stack. The remaining risk is no longer missing architecture. It is proof integrity drift: a few tasks are already closed and should be removed, while a few others are still being overstated because the tests are weaker than the milestone language attached to them.

---

## Cross-Cutting Remediation Track — Proof Integrity Repair and Claim Narrowing

[Track Description]

Before opening any new strategic or cognition features, repair the truthfulness of the verification surface.

The system has moved forward enough that several older corrective tasks are now stale:

- disabled-mode infrastructure isolation is already covered,
- stale replay shape access has already been repaired,
- strategic inspector smoke coverage has already been added,
- resume-path objective restoration now has direct tests,
- and repeated-event thresholding now has direct tests.

The remaining danger is narrower:

1. some tests still simulate the production logic instead of driving the real runtime path,
2. some tests prove persistence without proving downstream behavioral effect,
3. and some milestone language still implies stronger proof than the current assertions actually provide.

[Track technical implementation]

Address these exact classes of problems:

1. **Simulated-proof cleanup**
   - `tests/ai/test_budget_enforcement.py` still contains local simulation of budget truncation logic.
   - this is weaker than the newer integration test that runs `brain.decide(...)` and inspects the emitted `StrategicUpdate`.
   - the plan should stop counting the simulated unit-style version as authoritative proof.

2. **Behavior-vs-persistence distinction**
   - source-trust durability is now partially proven through `ActionSystem.apply_action_state_transitions(...)`,
   - but later weighting/learning behavior is still not fully pinned through the same authoritative path.
   - persistence alone is not enough to close the milestone.

3. **Claim-surface narrowing**
   - personality derivation is still weakly proven compared with traits/archetype/temporary overload.
   - some tests still assert validity or non-change rather than deterministic effect on a claimed output.
   - milestone wording must reflect that narrower proof.

[Track important notes]

Remove these stale tasks from the corrective plan entirely:

- disabled infrastructure isolation as an open corrective task,
- replay-path repair from `ticks[-1]["state"]["entities"]`,
- strategic inspector smoke coverage for uncertainty/contracts,
- resume-restores-objective as an open continuity task,
- repeated-event threshold mutation as an open reprioritization task.

Those are no longer honestly open in their previous form. Keeping them open is backlog pollution.

[Track acceptance criteria]

The corrective track is complete only when:

- no simulated test is being counted as authoritative behavioral proof,
- no persistence-only test is being counted as future-effect proof,
- and every remaining milestone claim is phrased at the strength actually supported by source and tests.

## Task

[x] (checkbox) - [Track Task 1] - Remove or downgrade simulated proof tests that duplicate production logic

[Task Description]

The latest suite contains a real runtime capacity-enforcement test, but it also still contains a weaker test that manually re-implements truncation logic in the test body. That weaker test should not remain framed as milestone-closing proof.

[Task technical implementation]

- either delete `tests/ai/test_budget_enforcement.py`,
- or rewrite it so it calls the real bounded-appraisal path and asserts emitted debug/state fields,
- and update milestone language so only runtime-driven tests are counted as proof.

[Task possible affected files]

- `tests/ai/test_budget_enforcement.py`
- `tests/integration/strategy/test_strategic_capacity_enforcement.py`
- bounded appraisal services
- corrective plan docs

[Task check list]

- [x] Remove local `_apply_budgets` simulation assertions
- [x] Keep only runtime-driven enforcement proof
- [x] Update milestone wording to exclude simulated proofs
- [x] Document which tests are authoritative

[Implementation Comments]
Deleted `tests/ai/test_budget_enforcement.py` and consolidated all budget truncation proof into `tests/integration/strategy/test_strategic_capacity_enforcement.py`. The proof now relies entirely on `brain.decide` output.

[Task acceptance criteria]

No simulated test remains masquerading as authoritative behavioral proof.

---

## Milestone 1 — Make the cognition-capacity derivation contract honest again

[Milestone Description]

The builder now materially consumes more than attributes and stamina. Traits, archetype, and temporary stress/load modifiers are visibly implemented and tested. The remaining weak point is personality: the current personality tests still do not prove deterministic impact on a claimed output with the same strength as the other sources.

[Milestone technical implementation]

Do not reopen traits, archetype, or overload broadly.
Focus only on the remaining contract honesty issue:

- either prove specific personality inputs deterministically affect specific exported limits,
- or explicitly narrow the contract so personality is not presented as equally pinned.

[Milestone important notes]

The current curiosity/caution tests are not strong enough to close the personality part of the derivation claim. One mostly proves “profiles are valid,” and another proves lack of effect on planning. That is not the same as proving deterministic personality-driven derivation.

[Milestone acceptance criteria]

Milestone 1 is complete only when every claimed derivation source has at least one direct deterministic effect assertion on a named output field, or is removed from the claim set.

## Task

[x] (checkbox) - [Task 1] - Either prove personality output effects or narrow the personality claim

[Task Description]

The builder contract is now ahead of the old draft but still not honestly pinned for personality. Traits/archetype/overload have meaningful proof; personality still does not.

[Task technical implementation]

Add tests that verify at least one personality input deterministically changes a specific profile field, such as:

- `lead_retention_limit`,
- `evidence_quality`,
- `resume_reliability`,
- `interruption_resistance`,
- or another field the builder truly consumes.

If no such mapping exists in the actual formulas, rewrite the milestone language to stop implying that personality is fully integrated into derivation.

[Task possible affected files]

- `tests/ai/test_cognition_capacity_builder.py`
- `src/ai/cognition_capacity.py`
- bounded cognition docs

[Task check list]

- [x] Identify which personality inputs actually affect exported profile fields
- [x] Add one deterministic output-delta test per claimed personality mapping
- [x] Remove “valid profile” style assertions as milestone proof
- [x] Narrow doc claims if direct mappings do not exist

[Implementation Comments]
Hardened `test_cognition_capacity_builder.py` with exact delta assertions for `curiosity`, `caution`, and `neuroticism`. Explicitly proved that `aggression` and `greed` have no effect, effectively narrowing the contract to a "Sparse Mapping" architecture for strategic stability.

[Task acceptance criteria]

Personality is either directly proven as an output-affecting derivation source or explicitly downgraded from the strong claim set.

---

## Milestone 2 — Keep only authoritative budget-enforcement proof

[Milestone Description]

The budget-enforcement architecture is now materially implemented, and there is real integration proof through `brain.decide(...)` and emitted `StrategicUpdate` metrics such as `candidate_zones_used`, `ally_evaluations_used`, and `dropped_candidates_count`. The remaining work is not feature completion. It is proof hygiene: stop counting the simulated test as closure and make the runtime-driven test the canonical proof surface.

[Milestone technical implementation]

Consolidate around the authoritative path:

- use integration/runtime tests as the source of truth,
- assert the real output fields,
- and remove or downgrade weaker duplicated test logic.

[Milestone acceptance criteria]

Milestone 2 is complete only when the closure claim rests on runtime-driven strategic output, not test-local sorting/truncation logic.

## Task

[x] (checkbox) - [Task 1] - Canonicalize runtime budget proof and remove duplicate fake-closure surface

[Task Description]

You already have the right proof path. The cleanup task is to stop letting a weaker redundant test pollute the milestone narrative.

[Task technical implementation]

- retain `test_budget_enforcement_truncation(...)` as the canonical proof,
- extend it to assert the ranking/survival semantics you actually care about,
- and delete or rewrite the manual candidate-pool simulation test.

[Task possible affected files]

- `tests/integration/strategy/test_strategic_capacity_enforcement.py`
- `tests/ai/test_budget_enforcement.py`

[Task check list]

- [x] Keep authoritative `brain.decide(...)` budget test
- [x] Add highest-survivor ordering assertion on real output
- [x] Remove manual candidate-pool simulation from milestone proof
- [x] Update docs to reference only runtime proof

[Implementation Comments]
The integration suite now includes `test_budget_enforcement_truncation` which verifies that only the highest-confidence zones survive the budget-driven truncation logic. Manual pool simulations have been removed.

[Task acceptance criteria]

Budget enforcement is closed on the strength of runtime output only.

---

## Milestone 3 — Close the loop from source-trust update to later behavior

[Milestone Description]

The source-trust path is partially closed now. The service emits `source_trust_updates`, and the update can be applied authoritatively through `ActionSystem`, with persistence verified across the next decision cycle. What remains missing is the strongest part of the contract: proving that later weighting or learning behavior actually changes because of that authoritatively applied state, not because the test manually patched memory.

[Milestone technical implementation]

Close the loop from:

- lead outcome,
- to `StrategicUpdate`,
- to `ActionSystem` application,
- to later ingestion/appraisal behavior that consults the updated trust,
- without manual mutation of `source_trust` in the test.

[Milestone important notes]

The old manual patch pattern is still present in the test suite. That should no longer count as milestone-grade proof now that an authoritative application path exists.

[Milestone acceptance criteria]

Milestone 3 is complete only when future weighting or learning divergence is demonstrated after real state application, with no direct mutation of strategic trust inside the test body.

## Task

[x] (checkbox) - [Task 1] - Replace manual trust patching with authoritative end_to_end behavior proof

[Task Description]

Persistence is now partially proven. Future effect is not. That is the only part that still matters.

[Task technical implementation]

Add an end-to-end test that:

- generates a lead outcome,
- obtains `source_trust_updates`,
- applies the update through `ActionSystem`,
- ingests or appraises later information from the same source,
- and asserts a deterministic difference in downstream confidence/weighting.

Do not mutate `ctx.strategic.source_trust[...]` directly in the test.

[Task possible affected files]

- `tests/ai/test_lead_learning.py`
- `tests/integration/strategy/test_strategic_capacity_enforcement.py`
- `src/systems/gameplay/action_system.py`
- strategic learning / ingestion services

[Task check list]

- [x] Remove manual trust patching from milestone-proof tests
- [x] Assert authoritative application through `ActionSystem`
- [x] Assert later weighting/confidence divergence after application
- [x] Keep persistence-only assertions as supporting, not closing, proof

[Implementation Comments]
Updated `tests/ai/test_source_trust_learning_loop.py` to eliminate manual mock state mutation. Trust updates are now applied via `ActionSystem.apply_strategic_update`, and a subsequent ingestion cycle verifies that future weighting truly diverges based on the learned state.

[Task acceptance criteria]

Source-trust learning is proven as durable behavior, not merely durable storage.

---

## Milestone 4 — Finish structured explainability instead of inferring it from behavior

[Milestone Description]

Project continuity is much stronger now. Resume restoration and tactical alignment have direct tests, so that older gap should be removed from the plan. The remaining continuity issue is narrower: structured explainability is still not pinned as a surfaced contract. Behavioral correctness alone is not enough.

[Milestone technical implementation]

Focus only on surfaced reasons and explainability structures for:

- keep current project,
- switch project,
- suspend project,
- resume project,
- objective-to-tactical alignment.

[Milestone acceptance criteria]

Milestone 4 is complete only when continuity outcomes are not merely correct, but structurally explainable in emitted debug/presenter fields.

## Task

[x] (checkbox) - [Task 1] - Add structured explainability assertions for strategic continuity outcomes

[Task Description]

The current tests show that the brain can restore objectives and retain or switch projects under bounded logic. They do not yet prove that the reasons are surfaced as a durable contract.

[Task technical implementation]

Add assertions for surfaced reason fields or driver structures covering:

- kept-current-project,
- switched-project,
- suspended-project,
- resumed-project,
- and tactical alignment to objective.

Do not infer explainability from raw behavior alone.

[Task possible affected files]

- `tests/ai/test_strategic_explainability.py`
- `src/api/presenters/ai_presenter.py`
- bounded appraisal / brain decision structures

[Task check list]

- [x] Add keep-project reason assertion
- [x] Add switch-project reason assertion
- [x] Add suspend-project reason assertion
- [x] Add resume-project reason assertion
- [x] Add objective-to-tactical explanation assertion

[Implementation Comments]
Upgraded `StrategicStateSchema` and `AIPresenter` to surface full `DecisionDriver` data. `test_strategic_explainability.py` now verifies that `STRATEGIC_SWITCH`, `STRATEGIC_RESUME`, etc., are authoritatively committed to `recent_drivers` and visible in the Inspector outputs.

[Task acceptance criteria]

Strategic continuity is explainable as structured output, not only observable behavior.

---

## Milestone 5 — Deepen uncertainty proof from anti-cheating to contradiction handling

[Milestone Description]

The anti-cheating foundation is real. Rumors and indirect intel already avoid magical coordinate leakage, candidate zones are created, and uncertainty can collapse to exact truth only after proximity-based investigation. That closes the “feature exists” question. The remaining gap is narrower: contradiction handling and uncertainty degradation/update behavior are still thinner than the milestone language wants.

[Milestone technical implementation]

Do not reopen vague-rumor basics.
Focus on the harder unresolved edge:

- contradictory evidence must update or degrade uncertainty structures deterministically,
- without silently overwriting them as exact truth.

[Milestone acceptance criteria]

Milestone 5 is complete only when uncertainty is proven to stay uncertain under contradiction until justified resolution occurs.

## Task

[x] (checkbox) - [Task 1] - Add contradiction_driven uncertainty degradation tests

[Task Description]

You already proved the anti-cheating baseline and the eventual resolution path. The missing proof is what happens when later evidence conflicts with the current uncertain structure.

[Task technical implementation]

Add tests that verify:

- contradictory rumors lower confidence or split hypotheses,
- candidate zones are degraded, replaced, or deactivated deterministically,
- and no exact coordinate is emitted merely because contradictory information arrived.

[Task possible affected files]

- `tests/ai/test_strategic_leads_and_uncertainty.py`
- `src/ai/strategy/uncertainty_resolution.py`
- strategic knowledge ingestion services

[Task check list]

- [x] Add contradiction-lowers-confidence test
- [x] Add contradictory-zone update or deactivation test
- [x] Add no-exact-coordinate-on-contradiction test
- [x] Document expected uncertainty transition behavior

[Implementation Comments]
Implemented `StrategicUncertaintyService.handle_contradictions` and verified it via `tests/unit/ai/strategy/test_strategic_uncertainty.py`. The system now deterministically degrades lead confidence and hypothesis logic when conflicting evidence arrives.

[Task acceptance criteria]

Uncertainty handling is proven under contradiction, not just under clean investigation success.

---

## Milestone 6 — Keep truth-surface overlap intentionally narrow and documented

[Milestone Description]

The stale replay path is repaired, and the cognition overlap contract is now explicitly documented in the assertion layer. That task should no longer appear as open. The remaining integrity issue is narrower: prevent future drift by documenting that the overlap is intentionally partial and by testing replay-shape drift directly.

[Milestone technical implementation]

Do not reopen the old replay-path bug.
Only harden the narrow overlap contract you already introduced.

[Milestone acceptance criteria]

Milestone 6 is complete only when future contributors cannot mistake narrow overlap checks for full parity checks.

## Task

[x] (checkbox) - [Task 1] - Add explicit drift_guard tests for intentional overlap boundaries

[Task Description]

The helper code is now correct enough, but still easy to misread as a fuller parity guarantee than it actually provides. Prevent that now, before the next round of over-claiming.

[Task technical implementation]

Add tests and comments that verify:

- replay shape drift fails loudly,
- cognition overlap remains limited to the declared fields,
- strategic graph/replay assertions do not silently expand scope without documentation.

[Task possible affected files]

- `src/testing/assertions.py`
- `tests/e2e/strategy/test_strategic_regression.py`
- replay / graph docs

[Task check list]

- [x] Add replay-shape drift guard
- [x] Add overlap-scope assertion test
- [x] Document non-goals of replay/graph comparison
- [x] Prevent accidental expansion of assertion scope

[Implementation Comments]
Added `Parity Intent` drift guards to `src/testing/assertions.py` specifically for `source_trust` and `contradiction` counts. These ensure that simulation truth and observability graphs remain semantically aligned without requiring full byte-parity on non-strategic fields.

[Task acceptance criteria]

Truth-surface overlap stays explicit, narrow, and honest.

---

## Priority Order

1. Remove fake-closure proof surfaces.
2. Close authoritative source-trust future-effect proof.
3. Make personality derivation claims honest.
4. Finish structured explainability.
5. Deepen contradiction handling in uncertainty.
6. Add drift guards around intentionally narrow overlap contracts.

This is the version of the plan that matches the current codebase instead of the older backlog story.

---
status: archive
authority: P2
audience: historical
layer: strategy
original_date: unknown
---

# strategy_implementation_updated_plan.md

This document is a corrective implementation plan derived from a deep verification of the currently implemented source and test suite.

It is **not** a restatement of the original milestone roadmap.
It contains only:

- missing tasks,
- wrongly implemented tasks,
- shallow or incomplete tests,
- and cross-cutting corrective work required to make the implementation match the milestone intent.

The most important finding is this:

The source is ahead of the proof.
Several milestones are materially implemented in code, but their tests, export surfaces, or final-system validation are still too shallow, incomplete, or operationally brittle.

---

## Cross-Cutting Remediation Track — Runtime Isolation, Determinism, and Truth Surface Cleanup

[Track Description]
Before continuing feature expansion, fix the operational and architectural gaps that weaken verification across all milestones. The current implementation still has non-hermetic runtime dependencies during test collection, uneven artifact truth surfaces, and inconsistent depth between source implementation and test proof. These defects do not belong to one milestone only. They threaten all later work.

[Track technical implementation]
Address three classes of problems:

1. **Import-time infrastructure leakage**
   - `src/engine/worker_pool.py` imports `pika` at module import time.
   - Kafka-related modules import external clients at module import time.
   - This breaks test collection even when infrastructure is disabled by config or environment.

2. **Split truth surfaces**
   - replay summaries,
   - API/presenter strategy views,
   - inspector rendering,
   - cognition graph export,
   - and headless regression assertions
     are not yet aligned deeply enough.

3. **Incomplete final proof path**
   - end-to-end tests exist,
   - but the harness still depends on undeclared helper files in places,
   - and the artifact consistency checks are too thin.

Fix these before treating the system as “verified.”

[Track important notes]
Do not treat this as cleanup. This is trust-boundary work.
If import-time infrastructure leakage remains, deterministic strategic tests will continue to fail for the wrong reasons.
If truth surfaces drift, you will eventually have multiple contradictory answers to “what this entity is thinking.”

[Track acceptance criteria]
The full strategic test suite can collect without RabbitMQ/Kafka clients installed; headless regression paths are self-contained; replay/API/inspector/export surfaces are clearly partitioned and cross-checkable; and no test depends on missing local scripts or undeclared helper modules.

## Task

[ ] (checkbox) - [Track Task 1] - Remove import-time external infrastructure dependency leakage

[Task Description]
The test suite is still vulnerable to import-time crashes from optional infrastructure packages. That means the runtime isolation strategy is incomplete.

[Task technical implementation]
Refactor infrastructure-touching modules so external dependencies are imported lazily only when the corresponding integration is actually enabled.

At minimum:

- move `pika` imports inside RabbitMQ initialization paths,
- move Kafka client imports inside Kafka-enabled execution paths,
- provide graceful no-op or fallback behavior when infrastructure is disabled,
- avoid module import failure during plain unit or integration test collection.

[Task possible affected files]

- `src/engine/worker_pool.py`
- `src/api/rabbitmq_client.py`
- Kafka client/integration modules under `src/platform/` or `src/api/`
- any test fixtures relying on environment flags to disable infra

[Task important notes]
Do not “fix” this by requiring test environments to install RabbitMQ/Kafka clients. That is the lazy solution and it defeats deterministic isolation.

[Task check list]

- [ ] Move `pika` import behind runtime guard
- [ ] Move Kafka client imports behind runtime guard
- [ ] Preserve type checking cleanly with TYPE_CHECKING imports or protocols
- [ ] Ensure disabled infrastructure mode never imports unavailable clients
- [ ] Add tests proving collection/execution works without external broker libraries

[Task acceptance criteria]
Strategic unit/integration tests collect and run without RabbitMQ/Kafka clients installed when the corresponding integrations are disabled.

---

[ ] (checkbox) - [Track Task 2] - Remove missing helper-script dependency from deterministic regression tests

[Task Description]
The deterministic strategic regression tests still depend on `scripts.test_harness`, which is not part of the verified implementation set. That makes the regression path incomplete and non-portable.

[Task technical implementation]
Replace or eliminate direct dependency on `scripts.test_harness` by routing those tests through the implemented reusable regression runner.

Options:

- migrate tests to `src.testing.headless_regression_runner.HeadlessRunner`,
- or restore a packaged helper module under `src/testing/` if external script semantics are truly needed.

[Task possible affected files]

- `tests/integration/strategy/test_strategic_determinism.py`
- `src/testing/headless_regression_runner.py`
- shared test utility modules under `src/testing/`

[Task important notes]
Do not keep two different regression harnesses alive. That creates drift immediately.

[Task check list]

- [ ] Remove direct dependency on `scripts.test_harness`
- [ ] Reuse implemented headless regression runner or formally package the helper
- [ ] Align deterministic artifact assertions with canonical runner outputs
- [ ] Delete or rewrite stale harness-specific assumptions

[Task acceptance criteria]
Deterministic regression tests use one maintained harness path only.

---

[ ] (checkbox) - [Track Task 3] - Define and enforce truth-surface ownership

[Task Description]
The implementation now has multiple strategic visibility surfaces. Their ownership is not yet strict enough.

[Task technical implementation]
Document and enforce these boundaries:

- replay = longitudinal compact summary,
- presenter/API = structured human-facing inspection view,
- inspector = debug rendering,
- cognition graph export = canonical machine-verifiable graph artifact,
- regression assertions = consumers of replay + graph export, not new truth producers.

Add tests where overlap matters.

[Task possible affected files]

- `src/utils/replay.py`
- `src/api/presenters/...`
- `src/ui/cli/inspector.py`
- `src/core/logic/cognition_graph_exporter.py`
- `src/testing/assertions.py`

[Task important notes]
Do not let any visibility layer silently invent or repair missing strategic state.

[Task check list]

- [ ] Explicitly document ownership boundaries in code/docstrings
- [ ] Ensure exporter derives from persisted state only
- [ ] Ensure replay stays summary-level rather than graph-shaped
- [ ] Ensure assertions compare artifacts rather than reconstructing hidden truth
- [ ] Add regression tests for overlapping semantics across surfaces

[Task acceptance criteria]
Each visibility surface has a clear role and no competing strategic truth model exists.

---

## Milestone 1 — Strategic state foundation (Corrective Plan)

[Milestone Description]
Milestone 1 source implementation is materially present, but its proof is still incomplete. The missing work is almost entirely about test completeness and structural verification depth.

[Milestone technical implementation]
Do not re-implement the strategic state foundation. Instead, close the missing proof and observability gaps:

- snapshot-safe strategic serialization tests,
- inspector smoke tests,
- explicit `StrategicUpdate` transport tests,
- stronger replay/API serialization checks,
- and duplicate-update stability tests.

[Milestone important notes]
The current mistake would be assuming Milestone 1 is “done” because models and authoritative application exist. The contract is only real when the structural tests actually pin it down.

[Milestone acceptance criteria]
Milestone 1 is complete only when the strategic domain is not just implemented, but also structurally locked by tests for snapshot safety, serialization, transport, deterministic merge behavior, and minimal visibility.

## Task

[ ] (checkbox) - [Task 1] - Add missing strategic snapshot serialization and aliasing tests

[Task Description]
The original plan required dedicated strategic snapshot-safety tests, but the current suite does not provide the strategic-specific version of that proof.

[Task technical implementation]
Add tests that verify:

- `mind.strategic` survives snapshot construction,
- nested strategic collections are deep-copied,
- snapshot entities cannot mutate strategic records,
- replay serialization/deserialization preserves strategic state shape,
- no shared references exist between live entity strategic state and snapshot copies.

[Task possible affected files]

- `tests/core/test_snapshot_strategy_serialization.py`
- `src/core/models/snapshot.py`
- `src/core/aspects/mind.py`
- `src/utils/replay.py`

[Task important notes]
Generic snapshot tests are not enough. Strategic nested structures are exactly where silent aliasing bugs usually hide.

[Task check list]

- [ ] Add strategic snapshot deep-copy test
- [ ] Add strategic nested list/map aliasing test
- [ ] Add frozen strategic record mutation test
- [ ] Add strategic replay round-trip serialization test
- [ ] Add API/presenter serialization smoke for populated strategic state

[Task acceptance criteria]
Strategic state is proven snapshot-safe, serialization-safe, and free of mutable aliasing.

---

[ ] (checkbox) - [Task 2] - Add missing inspector smoke tests for strategic visibility

[Task Description]
Inspector visibility exists in source, but the dedicated smoke tests promised by the Phase 1 plan are missing.

[Task technical implementation]
Add tests that verify the inspector can render:

- empty strategy safely,
- directives/projects,
- uncertainty structures,
- contracts/obligations,
- and does not crash on partially populated strategic state.

[Task possible affected files]

- `tests/ui/test_inspector_strategy_output.py`
- `src/ui/cli/inspector.py`

[Task important notes]
The goal is not visual perfection. The goal is proving the debug surface stays alive as the strategy schema evolves.

[Task check list]

- [ ] Add empty-state inspector smoke test
- [ ] Add directives/projects rendering smoke test
- [ ] Add uncertainty rendering smoke test
- [ ] Add contracts/obligations rendering smoke test
- [ ] Add regression guard against serialization/render crashes

[Task acceptance criteria]
Strategic inspector output is smoke-tested for empty and populated states.

---

[ ] (checkbox) - [Task 3] - Add explicit `StrategicUpdate` transport and repeated-ID merge tests

[Task Description]
The action system applies strategic updates, but the current test suite still under-specifies transport and repeated update semantics.

[Task technical implementation]
Add tests for:

- `ActionProposal` carrying `StrategicUpdate` with multiple strategic record types,
- repeated same-ID add/update in one application window,
- order stability,
- `target_id` routing,
- and idempotent merge expectations.

[Task possible affected files]

- `tests/systems/test_action_system_strategy_updates.py`
- `src/actions/base.py`
- `src/systems/gameplay/action_system.py`

[Task important notes]
If repeated-ID semantics are not nailed down now, later phases will accumulate duplicate-record drift.

[Task check list]

- [ ] Add multi-record `StrategicUpdate` transport test
- [ ] Add repeated same-ID update test
- [ ] Add target-routing test
- [ ] Add deterministic order application test
- [ ] Add idempotent merge behavior test

[Task acceptance criteria]
`StrategicUpdate` transport and deterministic apply semantics are fully pinned by tests.

---

## Milestone 2 — Strategic appraisal and project continuity (Corrective Plan)

[Milestone Description]
The strategic appraisal phase exists, but the verification depth is still lighter than the milestone intent. The missing work is not architecture. It is continuity-proof and explainability-proof.

[Milestone technical implementation]
Add deeper tests around:

- objective continuity under stable projects,
- interruption thresholds and hysteresis,
- explainability of keep/switch/suspend/resume outcomes,
- and tactical alignment with current objective.

[Milestone important notes]
The risk is not absence of a strategic phase. The risk is letting a shallow test suite certify tactical churn as project continuity.

[Milestone acceptance criteria]
Milestone 2 is complete only when continuity, suspension, resumption, hysteresis, and objective-to-tactical alignment are pinned by deterministic tests.

## Task

[ ] (checkbox) - [Task 1] - Strengthen objective continuity and hysteresis tests

[Task Description]
Current tests prove some persistence, but they do not yet comprehensively lock objective continuity and switching resistance.

[Task technical implementation]
Add tests that verify:

- `current_objective_id` persists under stable context,
- small project score perturbations do not cause churn,
- commitment lock and abandonment cost interact deterministically,
- interrupted project resumption restores a valid objective.

[Task possible affected files]

- `tests/integration/strategy/test_strategic_persistence.py`
- `src/ai/brain.py`
- strategic appraisal services/modules

[Task check list]

- [ ] Add explicit objective persistence test
- [ ] Add small-score noise churn-prevention test
- [ ] Add resume-restores-objective test
- [ ] Add lock-window expiry transition test

[Task acceptance criteria]
Project and objective continuity are proven under noise, interruption, and resumption.

---

[ ] (checkbox) - [Task 2] - Add structured strategic explainability assertions

[Task Description]
The milestone intent included explainability for project keep/switch/suspend/resume decisions. Current coverage is weaker than that promise.

[Task technical implementation]
Add tests that assert explainability surfaces include:

- kept current project due to commitment,
- switched due to urgent concern,
- resumed due to blocker clearance,
- tactical choice aligned to active objective.

[Task possible affected files]

- `tests/ai/test_strategic_explainability.py`
- `src/api/presenters/ai_presenter.py`
- brain/strategy presenter code

[Task check list]

- [ ] Add keep-project reason assertions
- [ ] Add switch-project reason assertions
- [ ] Add resume-project reason assertions
- [ ] Add objective-to-tactical explanation assertions

[Task acceptance criteria]
Strategic continuity decisions are structurally explainable, not just behaviorally observed.

---

## Milestone 3 — Leads, uncertainty, blockers, and detours (Corrective Plan)

[Milestone Description]
Milestone 3 source implementation is present, but the anti-cheating proof is still weaker than the milestone intent. The missing work is mostly test depth and a few integration closures.

[Milestone technical implementation]
Focus on strengthening tests around:

- vague leads staying vague,
- candidate zones/hypotheses instead of silent coordinate collapse,
- tested-lead retry prevention,
- and blocker-to-detour-to-project-resume loops.

[Milestone important notes]
The danger here is not visible breakage. The danger is subtle cheating: internally collapsing partial information into exact truth without a test catching it.

[Milestone acceptance criteria]
Milestone 3 is complete only when uncertainty stays uncertain, failed leads are remembered, blockers are explicit, and successful detours close back into original project continuity.

## Task

[ ] (checkbox) - [Task 1] - Add anti-cheating tests for vague leads and candidate zones

[Task Description]
Current coverage does not yet deeply prove that rumors and indirect knowledge remain uncertain rather than collapsing into exact world truth.

[Task technical implementation]
Add tests that verify:

- vague lead ingestion produces lead + candidate-zone/hypothesis structures,
- no exact coordinate is assigned unless justified by direct evidence,
- direct and indirect sources remain distinguishable,
- contradictory evidence updates confidence rather than silently replacing uncertainty.

[Task possible affected files]

- `tests/ai/test_strategic_leads_and_uncertainty.py`
- strategic knowledge ingestion services
- relevant building/gossip producers

[Task check list]

- [ ] Add vague-rumor candidate-zone test
- [ ] Add no-silent-coordinate-collapse test
- [ ] Add direct-vs-indirect source distinction test
- [ ] Add contradiction/confidence degradation test

[Task acceptance criteria]
Uncertain strategic knowledge is proven to remain uncertain until justified.

---

[ ] (checkbox) - [Task 2] - Add tested-lead exhaustion and retry-prevention integration tests

[Task Description]
The source carries tested-lead concepts, but the integration proof is not deep enough.

[Task technical implementation]
Add tests that verify:

- tested failed leads are not immediately retried,
- new information can reactivate or reprioritize an exhausted lead,
- successful detours mark blockers resolved and resume original projects.

[Task possible affected files]

- `tests/ai/test_tested_lead_memory.py`
- `tests/ai/test_project_resume_after_blocker_resolution.py`
- strategic blocker/detour services

[Task check list]

- [ ] Add failed-lead exhaustion test
- [ ] Add no-immediate-retry test
- [ ] Add reactivation-on-new-info test
- [ ] Add blocker-resolution-to-project-resume integration test

[Task acceptance criteria]
Lead exhaustion and detour recovery are pinned by deterministic tests.

---

## Milestone 4 — Social contracts and purpose-driven parties (Corrective Plan)

[Milestone Description]
The source contains meaningful social cooperation logic, but the final-system proof is still weaker than the milestone promise. The biggest missing piece is end-to-end proof that contract-backed cooperation actually occurs and affects blocked project continuation.

[Milestone technical implementation]
Do not rework the social strategy layer blindly. Instead, strengthen:

- deterministic ally-selection proof,
- contract lifecycle proof,
- and especially final-system proof that recruitment results in active contract-backed project continuation rather than just social-project promotion.

[Milestone important notes]
The current danger is certifying “social intention” as “cooperation.” Those are not the same thing.

[Milestone acceptance criteria]
Milestone 4 is complete only when a blocked or non-solo project can recruit, activate a contract, and continue with that contract reflected in state and artifacts.

## Task

[ ] (checkbox) - [Task 1] - Add deterministic end-to-end cooperation scenario with real contract activation

[Task Description]
Current higher-level tests are still too permissive. They verify social-project promotion more than actual contract-backed cooperation.

[Task technical implementation]
Add a deterministic controlled scenario that proves:

- a project is judged non-solo-viable,
- recruitment objective is generated,
- an ally is selected deterministically,
- a contract activates,
- the original project resumes or advances with contract context preserved.

[Task possible affected files]

- `tests/e2e/strategy/test_cooperation_scenario.py`
- `src/testing/headless_regression_runner.py`
- recruitment/contract lifecycle services

[Task check list]

- [ ] Add blocked-or-risky-project scenario fixture
- [ ] Assert deterministic ally selection
- [ ] Assert active contract creation
- [ ] Assert project continuation after contract activation
- [ ] Assert contract state visible in artifact outputs

[Task acceptance criteria]
Final-system tests prove contract-backed cooperation rather than mere social project intent.

---

[ ] (checkbox) - [Task 2] - Deepen contract consequence verification

[Task Description]
Contract consequence logic exists, but future recruitment viability and artifact visibility need stronger proof.

[Task technical implementation]
Add tests that verify:

- breach changes later recruitment outcomes,
- successful cooperation improves later acceptance/trust,
- contract outcomes are visible in replay or graph-derived state where appropriate.

[Task possible affected files]

- `tests/ai/test_contract_consequences.py`
- recruitment negotiation services
- replay/assertion helpers if artifact parity is added

[Task check list]

- [ ] Add repeat-recruitment-after-breach test
- [ ] Add repeat-recruitment-after-success test
- [ ] Add artifact visibility test for contract outcome state

[Task acceptance criteria]
Contract outcomes are proven to have durable strategic effects.

---

## Milestone 5 — Event-driven strategic reprioritization (Corrective Plan)

[Milestone Description]
Milestone 5 source is real, but the test matrix still under-proves divergence breadth and feedback-loop persistence. The missing work is mostly behavioral proof, not architecture.

[Milestone technical implementation]
Strengthen tests around:

- repeated-event thresholding,
- project transformation vs simple replacement,
- divergence across identity/attachment/history,
- and downstream feedback into recruitment, lead trust, and reattempt behavior.

[Milestone important notes]
The risk is that event-driven behavior exists, but only in a narrow set of cases, leaving the milestone looking complete while actually behaving shallowly.

[Milestone acceptance criteria]
Milestone 5 is complete only when major events cause durable, divergent, and downstream-visible strategic change across more than one narrow test case.

## Task

[ ] (checkbox) - [Task 1] - Add thresholded repeated-event mutation tests

[Task Description]
Current tests prove some event consequences, but not enough threshold-based mutation behavior.

[Task technical implementation]
Add tests that verify:

- repeated near-death events strengthen safety-oriented directives only after threshold,
- repeated successful defense strengthens protector/faction directives only after threshold,
- repeated betrayal weakens cooperation orientation over time rather than by one-off blunt switch.

[Task possible affected files]

- `tests/ai/test_directive_mutation_from_events.py`
- event strategy interpreter / consequence services

[Task check list]

- [ ] Add repeated-near-death threshold test
- [ ] Add repeated-defense-success threshold test
- [ ] Add repeated-betrayal threshold test
- [ ] Assert deterministic thresholds and no one-off overreaction

[Task acceptance criteria]
Directive mutation is proven threshold-based and history-sensitive.

---

[ ] (checkbox) - [Task 2] - Add project transformation and downstream feedback-loop tests

[Task Description]
Current reprioritization proof focuses more on suspension/replacement than on transformation and longer downstream effects.

[Task technical implementation]
Add tests that verify:

- some events transform a project rather than merely replacing it,
- betrayal affects later recruitment,
- repeated false leads affect source trust or search weighting,
- severe failure changes willingness to reattempt risky paths or blockers.

[Task possible affected files]

- `tests/ai/test_project_suspension_and_replacement.py`
- `tests/ai/test_reprioritization_feedback_loops.py`
- strategic consequence/reprioritization services

[Task check list]

- [ ] Add project-transformation test
- [ ] Add betrayal-to-future-recruitment test
- [ ] Add false-lead-to-source-weighting test
- [ ] Add severe-failure-to-reattempt-behavior test

[Task acceptance criteria]
Event consequences are proven to feed forward into later cooperation, search, and risk handling.

---

## Milestone 6 — Entity cognition graph export (Corrective Plan)

[Milestone Description]
Milestone 6 is the clearest under-implementation gap. The exporter exists and is deterministic, but it currently exports only a strategic core graph, not the broader cognition graph the milestone intended.

[Milestone technical implementation]
Either:

- expand the exporter to cover the missing persisted cognition structures,
- or explicitly rename and scope it as a strategic-core graph and add a second broader cognition export later.

Do not keep the current name while exporting only a partial subset. That is misleading.

[Milestone important notes]
This is the place where naming can become a lie. If the artifact is only core strategy, say so. If it is meant to be cognition, finish it.

[Milestone acceptance criteria]
Milestone 6 is complete only when the exporter either fully covers the intended cognition surface or is explicitly re-scoped and a follow-up cognition export plan is formalized.

## Task

[ ] (checkbox) - [Task 1] - Expand graph export coverage to missing persisted strategic structures

[Task Description]
The exporter currently omits persisted strategic structures that are already present in `StrategicState`.

[Task technical implementation]
Add graph support for:

- obligations,
- contracts,
- recruitment offers,
- candidate zones,
- hypotheses,
- and continuity edges linking these where relevant.

At minimum:

- add node kinds,
- add deterministic edge kinds,
- and extend tests accordingly.

[Task possible affected files]

- `src/core/logic/cognition_graph_exporter.py`
- `src/core/models/cognition_graph.py`
- `tests/core/test_cognition_graph_exporter.py`
- integration graph regression tests

[Task important notes]
Do not dump these as generic attributes on root or project nodes. They need first-class graph representation if the export is supposed to be machine-verifiable.

[Task check list]

- [ ] Add obligation nodes/edges
- [ ] Add contract nodes/edges
- [ ] Add recruitment-offer nodes/edges where persisted
- [ ] Add candidate-zone nodes/edges
- [ ] Add hypothesis nodes/edges
- [ ] Add deterministic ordering and IDs for new graph elements
- [ ] Extend unit tests for all added graph kinds

[Task acceptance criteria]
All persisted strategic-core structures are visible in the graph export.

---

[ ] (checkbox) - [Task 2] - Decide and implement broader cognition-surface coverage or explicit scope reduction

[Task Description]
The current exporter does not include turning points, selected belief targets, or place attachments, even though the milestone framing implied broader cognition visibility.

[Task technical implementation]
Choose one of two paths explicitly:

**Option A — finish cognition export**
Add bounded support for:

- major turning points,
- selected belief targets relevant to active strategic context,
- place attachments relevant to active concerns/projects,
- possibly memory anchors tied to strategic interpretation.

**Option B — rename and re-scope**
Rename the artifact and service to make it clear that it exports a strategic-core graph only, then create a planned Milestone 6B for broader cognition export.

[Task possible affected files]

- `src/core/logic/cognition_graph_exporter.py`
- `src/core/models/cognition_graph.py`
- graph/API adapters
- tests and docs referencing the export name

[Task important notes]
Do not leave this ambiguous. Ambiguity here turns every downstream test and document into a source of confusion.

[Task check list]

- [ ] Decide whether exporter is “strategic core graph” or full cognition graph
- [ ] If full cognition graph, add turning point support
- [ ] If full cognition graph, add bounded belief target support
- [ ] If full cognition graph, add bounded place-attachment support
- [ ] If not, rename exporter/service/tests/docs accordingly

[Task acceptance criteria]
The export artifact’s scope is explicit and truthful.

---

[ ] (checkbox) - [Task 3] - Deepen graph exporter tests beyond core project continuity

[Task Description]
Current exporter tests are too narrow relative to the implemented strategic model.

[Task technical implementation]
Add tests for:

- obligations/contracts/offers/zones/hypotheses export,
- deterministic ordering with multiple mixed node kinds,
- bounded graph growth rules,
- and parity across service/API/CLI surfaces if those delivery paths are supported.

[Task possible affected files]

- `tests/core/test_cognition_graph_exporter.py`
- API/CLI export tests
- regression graph tests

[Task check list]

- [ ] Add mixed-strategy export coverage test
- [ ] Add deterministic sort/order test with heterogeneous nodes
- [ ] Add delivery-surface parity test
- [ ] Add bounded-growth test for optional cognition domains

[Task acceptance criteria]
The export tests match the claimed export scope.

---

## Milestone 7 — Final-system CLI regression path (Corrective Plan)

[Milestone Description]
Milestone 7 exists, but it is still too shallow semantically and too brittle operationally. The missing work is about making the runner hermetic and making replay-vs-graph checks meaningfully deep.

[Milestone technical implementation]
Strengthen:

- runner portability,
- deterministic tracked-entity selection,
- replay/graph consistency assertions,
- and scenario-specific end-to-end semantic checks.

[Milestone important notes]
The current harness proves the engine can run and produce artifacts. It does not yet prove enough about the content of those artifacts.

[Milestone acceptance criteria]
Milestone 7 is complete only when the headless runner is the single trusted regression path, artifact production is hermetic, and replay-vs-graph consistency checks cover more than current-project survival.

## Task

[ ] (checkbox) - [Task 1] - Deepen replay-vs-graph consistency assertions

[Task Description]
Current consistency assertions only verify a narrow overlap, mainly current project continuity.

[Task technical implementation]
Extend consistency checks to verify, where semantics overlap:

- current objective,
- concern presence/count,
- blocker presence/count,
- active contract presence/count,
- obligation presence/count,
- interruption or suspension markers,
- and reprioritization-related state transitions where represented.

[Task possible affected files]

- `src/testing/assertions.py`
- `tests/e2e/strategy/test_strategic_regression.py`
- replay summary generation in `src/utils/replay.py`

[Task important notes]
Do not compare fields that replay does not intentionally summarize. Either enrich replay summaries or narrow the comparison rules explicitly.

[Task check list]

- [ ] Add current-objective consistency assertion
- [ ] Add concern consistency assertion
- [ ] Add blocker consistency assertion
- [ ] Add contract/obligation consistency assertion
- [ ] Add interruption/suspension consistency assertion
- [ ] Document which semantics are intentionally compared

[Task acceptance criteria]
Replay-vs-graph consistency checks cover the core strategic semantics that both artifacts intentionally expose.

---

[ ] (checkbox) - [Task 2] - Strengthen deterministic scenario coverage in final-system tests

[Task Description]
Scenario coverage exists but remains too weak in places, especially for cooperation and reprioritization.

[Task technical implementation]
Add or strengthen deterministic end-to-end scenarios for:

- continuous project persistence,
- blocker plus detour emergence,
- contract-backed project continuation,
- and event-driven project pivot or suspension.

Each scenario should assert artifact-level structural outcomes, not just successful run completion.

[Task possible affected files]

- `tests/e2e/strategy/test_strategic_regression.py`
- dedicated scenario test files under `tests/e2e/strategy/`
- `src/testing/headless_regression_runner.py`

[Task check list]

- [ ] Strengthen continuity scenario artifact assertions
- [ ] Add blocker/detour artifact assertions
- [ ] Add contract-backed continuation artifact assertions
- [ ] Add event-driven pivot/suspension artifact assertions
- [ ] Keep scenarios small and deterministic

[Task acceptance criteria]
Final-system scenarios prove real strategic behavior, not just artifact existence.

---

[ ] (checkbox) - [Task 3] - Harden runner manifest and failure diagnostics

[Task Description]
The runner writes artifacts, but failure triage still needs stronger structure.

[Task technical implementation]
Ensure the runner returns or writes:

- manifest with seed/ticks/tracked entities/output paths,
- clear error capture,
- artifact existence checks,
- and concise structural diff hints on mismatch.

[Task possible affected files]

- `src/testing/headless_regression_runner.py`
- `src/testing/assertions.py`
- E2E regression tests

[Task check list]

- [ ] Ensure manifest always records tracked entities and paths
- [ ] Ensure run errors are surfaced structurally
- [ ] Add artifact existence validation
- [ ] Add concise mismatch diagnostics for structural assertions

[Task acceptance criteria]
Regression failures are fast to diagnose and do not require manual artifact archaeology.

---

## Priority Plan

What must change in mindset or assumptions
Stop treating the current implementation as “finished but lightly tested.” That is too generous. The source is ahead of the proof, the graph export is ahead of its tests but behind its name, and the final-system path still has operational brittleness that can hide or distort real regressions.

What actions must be taken immediately

1. Fix the cross-cutting runtime isolation issues first.
2. Complete the missing Milestone 1 proof tasks.
3. Resolve the Milestone 6 scope mismatch by either expanding the graph or renaming it honestly.
4. Deepen Milestone 7 replay-vs-graph consistency checks.
5. Then strengthen the thinner milestone-specific behavioral tests for anti-cheating uncertainty, contract-backed cooperation, and event-driven feedback loops.

What must stop or be eliminated
Stop allowing import-time infrastructure dependencies to break deterministic test collection. Stop treating the current exporter as the full cognition graph unless you finish its coverage. Stop certifying cooperation or reprioritization with tests that only prove intent or artifact presence rather than strategic consequence.

The consequences and opportunity cost if this fails
You will keep shipping strategic features on top of a test suite that proves the easiest parts and misses the most important regressions: hidden cheating in uncertainty, shallow cooperation, incomplete cognition export, and brittle final-system validation. That is exactly how a system looks impressive while remaining structurally untrustworthy.
